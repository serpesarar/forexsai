"""Pine `strategy.*` broker emülatörü (TradingView varsayılanlarıyla).

- Piyasa emirleri bir sonraki barın açılışında dolar (`process_orders_on_close=true` ise aynı barın kapanışında).
- Limit/stop emirleri ve `strategy.exit` braketleri bar içinde OHLC yolu varsayımıyla denetlenir: açılış yükseğe
  daha yakınsa açılış → yüksek → düşük → kapanış, değilse açılış → düşük → yüksek → kapanış.
- Piramitleme: aynı yönde en çok `pyramiding` (0 → 1) giriş; ters yönde giriş pozisyonu çevirir.
- `strategy.exit`: profit/loss (tik), limit/stop (fiyat), trail_points/trail_price + trail_offset (yaklaşık iz süren stop).
  Çıkış emri bağlı olduğu işlem kapanınca düşer.
Bar b'nin dolumları, script b barında çalışmadan önce işlenir (RT.commit → process(b+1)); script o barın kapanışında
güncel pozisyonu görür.
"""
from __future__ import annotations

NA = float("nan")


def _na(x) -> bool:
    return x is None or (isinstance(x, float) and x != x)


def _num(x, default=NA):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return default if v != v else v


def _dir(direction) -> int:
    if direction is True:
        return 1
    if direction is False:
        return -1
    s = str(direction)
    return 1 if s.endswith("long") else (-1 if s.endswith("short") else 0)


class Trade:
    __slots__ = ("id", "size", "price", "bar", "time", "exit_price", "exit_bar", "exit_time", "exit_id", "hi", "lo")

    def __init__(self, id_, size, price, bar, time_):
        self.id, self.size, self.price, self.bar, self.time = id_, size, price, bar, time_
        self.exit_price = self.exit_bar = self.exit_time = NA
        self.exit_id = ""
        self.hi = self.lo = price

    def profit(self, px):
        return (px - self.price) * self.size


class Broker:
    def __init__(self, rt):
        self.rt = rt
        self.pyramiding = 1
        self.on_close = False
        self.default_qty = 1.0
        self.open: list[Trade] = []
        self.closed: list[Trade] = []
        self.market: list[dict] = []          # bir sonraki dolumda işlenecek piyasa emirleri
        self.resting: dict = {}               # id → limit/stop giriş emri (iptal/dolum'a kadar)
        self.exits: dict = {}                 # çıkış id → braket
        self.netprofit = 0.0
        self.active = False

    # ── yapılandırma / durum ──
    def config(self, pyramiding=0, process_orders_on_close=False, default_qty_value=1.0, **_):
        self.pyramiding = max(1, int(_num(pyramiding, 0)))
        self.on_close = bool(process_orders_on_close)
        self.default_qty = _num(default_qty_value, 1.0) or 1.0

    @property
    def size(self) -> float:
        return sum(t.size for t in self.open)

    def avg(self) -> float:
        s = self.size
        if not self.open or s == 0:
            return NA
        return sum(t.price * t.size for t in self.open) / s

    def openprofit(self) -> float:
        if not self.open:
            return 0.0
        return sum(t.profit(self.rt.C[self.rt.bar]) for t in self.open)

    def _sync(self):
        rt = self.rt
        rt.pos = self.size
        rt.pos_price = self.avg()

    # ── emir girişleri (script çağrıları) ──
    def entry(self, id_, direction, qty=None, limit=None, stop=None, kind="entry"):
        d = _dir(direction)
        if d == 0:
            return
        q = abs(_num(qty, self.default_qty)) or self.default_qty
        o = dict(kind=kind, id=str(id_), dir=d, qty=q, limit=_num(limit), stop=_num(stop), bar=self.rt.bar)
        self.active = True
        if _na(o["limit"]) and _na(o["stop"]):
            self.market = [m for m in self.market if not (m["kind"] in ("entry", "order") and m["id"] == o["id"])]
            self.market.append(o)
            if self.on_close:
                self._fill_market(self.rt.bar, self.rt.C[self.rt.bar])
        else:
            self.resting[o["id"]] = o

    def close(self, id_=None, qty=None, all_=False):
        if not self.open and not self.market:
            return
        self.active = True
        self.market.append(dict(kind="close", id=None if all_ else str(id_), qty=_num(qty)))
        if self.on_close:
            self._fill_market(self.rt.bar, self.rt.C[self.rt.bar])

    def exit(self, id_, from_entry="", qty=None, qty_percent=None, profit=None, limit=None, loss=None, stop=None,
             trail_price=None, trail_points=None, trail_offset=None):
        self.active = True
        prev = self.exits.get(str(id_))
        self.exits[str(id_)] = dict(id=str(id_), from_entry="" if _na(from_entry) else str(from_entry or ""),
                                    profit=_num(profit), limit=_num(limit), loss=_num(loss), stop=_num(stop),
                                    trail_price=_num(trail_price), trail_points=_num(trail_points),
                                    trail_offset=_num(trail_offset), armed=prev["armed"] if prev else False,
                                    trail_on=prev["trail_on"] if prev else False, best=prev["best"] if prev else NA)

    def cancel(self, id_=None):
        if id_ is None:
            self.resting.clear()
            self.market = [m for m in self.market if m["kind"] == "close"]
            return
        self.resting.pop(str(id_), None)
        self.exits.pop(str(id_), None)
        self.market = [m for m in self.market if m.get("id") != str(id_)]

    # ── dolum mekaniği ──
    def _open_trade(self, o, px, b):
        d, q = o["dir"], o["qty"]
        cur = self.size
        if o["kind"] == "entry":
            if cur * d < 0:                              # ters yön: çevir
                self._close_trades(list(self.open), px, b, "reverse")
            elif cur * d > 0 and sum(1 for t in self.open if t.size * d > 0) >= self.pyramiding:
                return                                   # piramitleme sınırı
        elif o["kind"] == "order" and cur * d < 0:       # ham emir: önce karşı pozisyonu azalt
            left = q
            for t in list(self.open):
                if left <= 0:
                    break
                take = min(abs(t.size), left)
                self._close_part(t, take, px, b, o["id"])
                left -= take
            q = left
            if q <= 0:
                return
        self.open.append(Trade(o["id"], q * d, px, b, self.rt.TM[b]))

    def _close_part(self, t, q, px, b, exit_id):
        if q >= abs(t.size) - 1e-12:
            self._close_trades([t], px, b, exit_id)
            return
        sgn = 1 if t.size > 0 else -1
        part = Trade(t.id, q * sgn, t.price, t.bar, t.time)
        t.size -= q * sgn
        self._finish(part, px, b, exit_id)

    def _close_trades(self, trades, px, b, exit_id):
        for t in trades:
            if t in self.open:
                self.open.remove(t)
                self._finish(t, px, b, exit_id)

    def _finish(self, t, px, b, exit_id):
        t.exit_price, t.exit_bar, t.exit_time, t.exit_id = px, b, self.rt.TM[b], exit_id
        self.netprofit += t.profit(px)
        self.closed.append(t)

    def _fill_market(self, b, px):
        orders, self.market = self.market, []
        for o in orders:
            if o["kind"] == "close":
                trades = [t for t in self.open if o["id"] is None or t.id == o["id"]]
                q = o.get("qty")
                if _na(q):
                    self._close_trades(trades, px, b, "close")
                else:
                    left = abs(q)
                    for t in trades:
                        if left <= 0:
                            break
                        take = min(abs(t.size), left)
                        self._close_part(t, take, px, b, "close")
                        left -= take
            else:
                self._open_trade(o, px, b)
        self._sync()

    def _path(self, o, h, l, c):
        return (o, h, l, c) if abs(h - o) <= abs(o - l) else (o, l, h, c)

    def _resting_hits(self, b, o_, h, l):
        """Limit/stop giriş emirleri: dolan emir → fiyat."""
        for oid, o in list(self.resting.items()):
            d, lim, stp = o["dir"], o["limit"], o["stop"]
            px = None
            if not _na(stp) and not _na(lim):            # stop-limit: önce stop tetiklenir
                if (d > 0 and h >= stp) or (d < 0 and l <= stp):
                    px = lim if (d > 0 and l <= lim) or (d < 0 and h >= lim) else None
            elif not _na(lim):
                if d > 0 and l <= lim:
                    px = min(o_, lim)
                elif d < 0 and h >= lim:
                    px = max(o_, lim)
            elif not _na(stp):
                if d > 0 and h >= stp:
                    px = max(o_, stp)
                elif d < 0 and l <= stp:
                    px = min(o_, stp)
            if px is not None:
                del self.resting[oid]
                self._open_trade(o, px, b)

    def _levels(self, ex, t):
        mt = self.rt.mintick or 0.01
        sgn = 1 if t.size > 0 else -1
        tp = ex["limit"] if not _na(ex["limit"]) else (t.price + sgn * ex["profit"] * mt if not _na(ex["profit"]) else NA)
        sl = ex["stop"] if not _na(ex["stop"]) else (t.price - sgn * ex["loss"] * mt if not _na(ex["loss"]) else NA)
        if ex["trail_on"] and not _na(ex["best"]) and not _na(ex["trail_offset"]):
            ts = ex["best"] - sgn * ex["trail_offset"] * mt
            sl = ts if _na(sl) else (max(sl, ts) if sgn > 0 else min(sl, ts))
        return tp, sl

    def _trail_update(self, ex, t, h, l):
        if _na(ex["trail_offset"]):
            return
        mt = self.rt.mintick or 0.01
        sgn = 1 if t.size > 0 else -1
        act = ex["trail_price"] if not _na(ex["trail_price"]) else (
            t.price + sgn * ex["trail_points"] * mt if not _na(ex["trail_points"]) else NA)
        fav = h if sgn > 0 else l
        if not ex["trail_on"] and not _na(act) and ((sgn > 0 and h >= act) or (sgn < 0 and l <= act)):
            ex["trail_on"], ex["best"] = True, fav
        elif ex["trail_on"]:
            ex["best"] = max(ex["best"], fav) if sgn > 0 else min(ex["best"], fav)

    def _exit_hits(self, b, o_, h, l, c):
        if not self.exits or not self.open:
            return
        path = self._path(o_, h, l, c)
        for ex in list(self.exits.values()):
            trades = [t for t in self.open if not ex["from_entry"] or t.id == ex["from_entry"]]
            if trades:
                ex["armed"] = True
            for t in trades:
                tp, sl = self._levels(ex, t)
                sgn = 1 if t.size > 0 else -1
                px = None
                if not _na(sl) and ((sgn > 0 and o_ <= sl) or (sgn < 0 and o_ >= sl)):
                    px = o_                               # açılış boşluğu stop'un ötesinde
                elif not _na(tp) and ((sgn > 0 and o_ >= tp) or (sgn < 0 and o_ <= tp)):
                    px = o_
                else:
                    for a, z in zip(path[:-1], path[1:]):
                        lo, hi = min(a, z), max(a, z)
                        hit_sl = not _na(sl) and lo <= sl <= hi
                        hit_tp = not _na(tp) and lo <= tp <= hi
                        if hit_sl and hit_tp:            # aynı segmentte: önce yaklaşılan
                            px = sl if abs(sl - a) <= abs(tp - a) else tp
                        elif hit_sl:
                            px = sl
                        elif hit_tp:
                            px = tp
                        if px is not None:
                            break
                if px is not None:
                    self._close_trades([t], px, b, ex["id"])
                else:
                    self._trail_update(ex, t, h, l)
            if ex["armed"] and not any(not ex["from_entry"] or t.id == ex["from_entry"] for t in self.open):
                del self.exits[ex["id"]]

    def process(self, b):
        """Bar b açılmadan önce bekleyen emirler, bar b içinde limit/stop/çıkışlar."""
        rt = self.rt
        o_, h, l, c = rt.O[b], rt.H[b], rt.L[b], rt.C[b]
        if self.market:
            self._fill_market(b, o_)
        if self.resting:
            self._resting_hits(b, o_, h, l)
        self._exit_hits(b, o_, h, l, c)
        self._sync()
        if not (self.market or self.resting or self.exits or self.open):
            self.active = False

    # ── strategy.opentrades.* / closedtrades.* ──
    def trade_fn(self, path: str, i=0, *a, **k):
        group, field = path.split(".")[1], path.split(".")[2]
        lst = self.open if group == "opentrades" else self.closed
        try:
            t = lst[int(i)]
        except (TypeError, ValueError, IndexError):
            return NA
        rt = self.rt
        if field == "entry_price":
            return t.price
        if field == "entry_bar_index":
            return t.bar
        if field == "entry_time":
            return t.time
        if field == "entry_id":
            return t.id
        if field == "size":
            return t.size
        if field == "profit":
            return t.profit(t.exit_price if group == "closedtrades" else rt.C[rt.bar])
        if field == "profit_percent":
            px = t.exit_price if group == "closedtrades" else rt.C[rt.bar]
            return (px / t.price - 1) * 100 * (1 if t.size > 0 else -1) if t.price else NA
        if field == "exit_price":
            return t.exit_price
        if field == "exit_bar_index":
            return t.exit_bar
        if field == "exit_time":
            return t.exit_time
        if field == "exit_id":
            return t.exit_id
        if field in ("commission",):
            return 0.0
        if field in ("max_runup", "max_drawdown", "max_runup_percent", "max_drawdown_percent"):
            return 0.0
        return NA

    def stat(self, name: str):
        if name == "wintrades":
            return sum(1 for t in self.closed if t.profit(t.exit_price) > 0)
        if name == "losstrades":
            return sum(1 for t in self.closed if t.profit(t.exit_price) < 0)
        if name == "eventrades":
            return sum(1 for t in self.closed if t.profit(t.exit_price) == 0)
        if name == "grossprofit":
            return sum(max(0.0, t.profit(t.exit_price)) for t in self.closed)
        if name == "grossloss":
            return -sum(min(0.0, t.profit(t.exit_price)) for t in self.closed)
        if name == "position_entry_name":
            return self.open[-1].id if self.open else ""
        return NA
