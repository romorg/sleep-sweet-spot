"""Generate charts ONLY from the approved-candidate public aggregate tables.

Nothing in this program accesses personal Health or diary files.
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
FIG=ROOT/'figures'
FIG.mkdir(exist_ok=True)

onset=pd.read_csv(DATA/'public_onset_counts.csv')
assert int(onset.n.sum())==2058
p5=100*onset.n_sleep_at_least_5h/onset.n
p7=100*onset.n_sleep_at_least_7h/onset.n
fig,ax=plt.subplots(figsize=(10.5,4.6))
x=range(len(onset));width=.35
ax.bar([i-width/2 for i in x],p5,width,label='At least 5 hours')
ax.bar([i+width/2 for i in x],p7,width,label='At least 7 hours')
ax.set_xticks(list(x),[f'{b}\n(n={n:,})' for b,n in zip(onset.start_band,onset.n)])
ax.set_ylim(0,110);ax.set_ylabel('Share of eligible windows (%)')
ax.set_xlabel('First recorded sleep start (local time)')
ax.set_title('Later recorded sleep start, fewer windows reach longer durations')
ax.legend(loc='upper right',frameon=False)
fig.tight_layout()
fig.savefig(FIG/'onset_thresholds.png',dpi=155)
plt.close(fig)

matrix=pd.read_csv(DATA/'public_next_night_matrix.csv')
cols=[c for c in matrix if c!='initial_duration_band']
a=matrix[cols].to_numpy(int)
assert int(a.sum())==1933
r=a/a.sum(axis=1,keepdims=True)*100
fig,ax=plt.subplots(figsize=(8.5,5.5))
img=ax.imshow(r,aspect='auto',vmin=0,vmax=35)
labels=['3–<5h','5–<6h','6–<7h','7–<8h','8h+']
ax.set_xticks(range(5),labels);ax.set_yticks(range(5),labels)
ax.set_xlabel('Following window duration')
ax.set_ylabel('Initial window duration')
ax.set_title('How recorded sleep duration transitions across adjacent windows')
for row in range(5):
    for col in range(5):
        ax.text(col,row,str(a[row,col]),ha='center',va='center',fontsize=10,color='black')
fig.colorbar(img,ax=ax,label='Row share (%)')
fig.tight_layout();fig.savefig(FIG/'consecutive_nights.png',dpi=155)
plt.close(fig)
print('Wrote two aggregate-only figures; no private data accessed.')
