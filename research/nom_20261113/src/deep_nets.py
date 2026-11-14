"""Derin model yardımcıları (LSTM, TCN) — lightgbm/catboost İÇERMEZ (macOS OpenMP kilitlenmesini önlemek için ayrı modül)."""
from __future__ import annotations

import numpy as np
import pandas as pd

SEQ = 120
EPOCHS = 6


def seq_tensor(rows_i1: np.ndarray, b: pd.DataFrame, atr: np.ndarray) -> np.ndarray:
    """Son SEQ kapanmış 1m bar: [log getiri, (h−l), (c−o)] / (ATR/fiyat) — yalnız geçmiş barlar (i1 dahil)."""
    c, h, l, o = (b[k].to_numpy() for k in ('close', 'high', 'low', 'open'))
    J = rows_i1[:, None] - np.arange(SEQ)[::-1][None, :]
    J = np.clip(J, 1, None)
    a = (atr / c[rows_i1])[:, None]
    r = np.log(c[J] / c[J - 1]) / a
    rg = (h[J] - l[J]) / c[J] / a
    bd = (c[J] - o[J]) / c[J] / a
    X = np.stack([r, rg, bd], axis=1).astype(np.float32)
    return np.nan_to_num(np.clip(X, -20, 20))


def deep_model(kind: str, n_tab: int):
    import torch
    import torch.nn as nn

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            if kind == 'lstm':
                self.rnn = nn.LSTM(3, 32, batch_first=True)
                seq_out = 32
            elif kind == 'transformer':   # 2 katmanlı kodlayıcı, 120 adımı 10'luk yamalara böler (12 jeton) + konum gömmesi
                self.proj = nn.Linear(3 * 10, 32)
                self.pos = nn.Parameter(torch.zeros(1, 12, 32))
                enc = nn.TransformerEncoderLayer(32, 4, 64, dropout=0.1, batch_first=True)
                self.enc = nn.TransformerEncoder(enc, 2)
                seq_out = 32
            else:   # TCN: genişleyen (dilated) nedensel evrişimler
                layers, ch = [], 3
                for d in (1, 2, 4, 8, 16):
                    layers += [nn.ConstantPad1d((2 * d, 0), 0.0), nn.Conv1d(ch, 32, 3, dilation=d), nn.ReLU()]
                    ch = 32
                self.tcn = nn.Sequential(*layers)
                seq_out = 32
            self.tab = nn.Sequential(nn.Linear(n_tab, 64), nn.ReLU())
            self.head = nn.Sequential(nn.Linear(seq_out + 64, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, 3))

        def forward(self, xs, xt):
            if kind == 'lstm':
                _, (hn, _) = self.rnn(xs.transpose(1, 2))
                s = hn[-1]
            elif kind == 'transformer':
                x = xs.transpose(1, 2).reshape(xs.shape[0], 12, 30)
                s = self.enc(self.proj(x) + self.pos).mean(1)
            else:
                s = self.tcn(xs)[:, :, -1]
            return self.head(torch.cat([s, self.tab(xt)], 1))
    return Net()


def train_deep(kind, Xs_tr, Xt_tr, y_tr, Xs_va, Xt_va, y_va, Xs_te, Xt_te):
    import torch
    torch.manual_seed(7)
    net = deep_model(kind, Xt_tr.shape[1])
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
    lossf = torch.nn.CrossEntropyLoss()
    t = lambda a: torch.tensor(a)
    Xs_tr, Xt_tr, y_tr = t(Xs_tr), t(Xt_tr), torch.tensor(y_tr, dtype=torch.long)
    best, best_state = 9e9, None
    for ep in range(EPOCHS):
        net.train()
        perm = torch.randperm(len(y_tr))
        for s in range(0, len(perm), 512):
            ix = perm[s:s + 512]
            opt.zero_grad()
            loss = lossf(net(Xs_tr[ix], Xt_tr[ix]), y_tr[ix])
            loss.backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            pv = torch.softmax(net(t(Xs_va), t(Xt_va)), 1).numpy()
        vl = -np.log(np.clip(pv[np.arange(len(y_va)), y_va], 1e-6, 1)).mean()
        if vl < best:
            best, best_state = vl, {k: v.clone() for k, v in net.state_dict().items()}
    net.load_state_dict(best_state)
    net.eval()
    with torch.no_grad():
        return torch.softmax(net(t(Xs_va), t(Xt_va)), 1).numpy(), torch.softmax(net(t(Xs_te), t(Xt_te)), 1).numpy()
