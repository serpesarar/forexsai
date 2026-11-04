"""Static export charts; CSV/JSON inputs, no network or new computations of edge."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
HERE=Path(__file__).resolve().parent
OUT=HERE/'results'
SYMS=['NDX.INDX','GDAXI.INDX','XAUUSD','USOIL.FOREX']
NAMES=['technical-basic','candlestick','ichimoku','volatility','seasonal','harmonic','elliott-wave']
LABELS=['Teknik temel','Mum desenleri','Ichimoku','Volatilite','Mevsimsellik','Harmonik','Elliott']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})

def heatmap():
 rows=list(csv.DictReader((OUT/'summary.csv').open()))
 fig,axs=plt.subplots(1,2,figsize=(14,7),layout='constrained')
 for ax,dataset,title in zip(axs,['recent_5m','long_1h'],['5 dakika | 1 Eylül–20/21 Ekim 2026','1 saat | 2024–2026']):
  vals=np.full((7,4),np.nan);counts={}
  for r in rows:
   if r['epoch']!='test' or r['dataset']!=dataset:continue
   i=NAMES.index(r['strategy']);j=SYMS.index(r['symbol']);counts[(i,j)]=int(r['n'])
   try:vals[i,j]=float(r['mean_R'])
   except ValueError:pass
  cmap=plt.get_cmap('RdYlGn').copy();cmap.set_bad('#e7e9ed')
  ax.imshow(vals,cmap=cmap,vmin=-.15,vmax=.15,aspect='auto')
  ax.set_xticks(range(4),['NDX','DAX','XAU','OIL']);ax.set_yticks(range(7),LABELS)
  for i in range(7):
   for j in range(4):
    v=vals[i,j];n=counts.get((i,j))
    txt=(f'{v:+.3f}R\nn={n:,}' if math.isfinite(v) else ('İşlem yok' if n==0 else 'Hacim yok'))
    ax.text(j,i,txt,ha='center',va='center',fontsize=10,color='#131722')
  ax.set_title(title,loc='left',pad=16,fontweight='bold')
 fig.suptitle('Vibe-Trading hazır örnekleri — dönem dışı net işlem ortalaması',fontsize=17,fontweight='bold')
 fig.supxlabel('Hiçbir hücre tüm araştırma koşullarını geçmedi. R = 2×ATR14 referansı; stop değildir.\nSpread + kayma tahmini; swap hariç. Renk ±0,15R’de doyar; hücrede gerçek değer yazılıdır.',fontsize=10)
 fig.savefig(OUT/'oos_heatmap.png',dpi=160);plt.close(fig)

def trade_examples():
 rows=json.loads((OUT/'chart_examples.json').read_text())
 fig,axs=plt.subplots(4,2,figsize=(16,15),layout='constrained')
 for r,ax in zip(rows,axs.flat):
  bars=list(csv.DictReader((OUT/r['bars_csv']).open()));times=[datetime.fromisoformat(b['ts']) for b in bars]
  entry=datetime.fromisoformat(r['entry_ts']);exit=datetime.fromisoformat(r['exit_ts'])
  # Minutes relative to decision; context before zero is observable at entry.
  xs=np.array([(t-entry).total_seconds()/60 for t in times])
  for right_edge,b in zip(xs,bars):
   x=right_edge-2.5  # Render each right-labelled 5m candle inside its known interval.
   o,h,l,c=[float(b[k]) for k in ['open','high','low','close']];col='#15836b' if c>=o else '#d2564f'
   ax.vlines(x,l,h,color=col,lw=.7)
   ax.add_patch(Rectangle((x-1.8,min(o,c)),3.6,max(abs(c-o),max(1e-7,abs(c)*.000002)),facecolor=col,edgecolor=col))
  ax.axvspan(0,max(xs[-1],1),color='#aab4c0',alpha=.12)
  ax.axvline(0,color='#4259b7',ls='--',lw=1,label='Karar / giriş')
  exmin=(exit-entry).total_seconds()/60
  ax.scatter([0],[r['entry']],color='#4259b7',marker='>',s=70,zorder=5)
  ax.scatter([exmin],[r['exit']],color='#1a1e29',marker='x',s=60,zorder=5)
  ax.plot([0,exmin],[r['entry'],r['exit']],ls=':',color='#1a1e29',lw=1)
  side='BUY' if r['side']==1 else 'SELL';out='İlk kazanç' if r['outcome']=='win' else 'İlk kayıp'
  ax.set_title(f"{r['symbol']} · {out} · {side} · {r['net_R']:+.2f}R\n{entry:%Y-%m-%d %H:%M} UTC",loc='left',fontsize=11,fontweight='bold')
  ax.set_xlabel('Karar anından dakika');ax.set_ylabel('Fiyat');ax.grid(alpha=.12)
 fig.suptitle('Betimsel işlem örnekleri | technical-basic, 5m sınama dönemi',fontsize=17,fontweight='bold')
 fig.supxlabel('Her sembolde kronolojik ilk kazanç ve ilk kayıp seçildi. Gri alan karar sonrası: sinyal girdisi değildir.\nTP/SL yok; çıkış hedef pozisyonun değişmesidir. İşaretler M1 açılış dolumunu gösterir; maliyet net R’de düşülür.',fontsize=10)
 fig.savefig(OUT/'trade_examples.png',dpi=150);plt.close(fig)
if __name__=='__main__':heatmap();trade_examples()
