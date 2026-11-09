"""p. 18-19: Stop! Politie! roept Daan. Oe-oe-aa-aa! roept Joep.

De boeven zitten klem: links springt Daan tevoorschijn met zijn hand omhoog, rechts springt Joep uit de
struik. De boeven in het midden schrikken zich een hoedje, koekmannetjes vliegen in het rond. Achteraan op
het pad staat de politieauto met zwaailicht."""
import numpy as np
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, Mens

CM = 0.01


def main(out, opts):
    V.setup(opts)
    PS.sky(y=0.6, w=180, h=80, sun=None, clouds=((-48, 46, 0.7), (48, 50, 0.7)))
    PS.hills(y0=0.52, w=180, seed=10)
    PS.tree('Boom0', -0.42, 0.42, 16, 7.5, seed=8)
    PS.grassland(y0=-0.6, y1=0.55)
    PS.road('Pad', -1.0, 1.0, 0.24, 0.32, dash=False)
    PS.police_car('Auto', 0.03, 0.3, facing=1, scale=0.6)
    PS.bush('Struik_rechts', 0.32, -0.02, 26, 10, berries=5, seed=15)
    PS.flowers('Bloem', -0.6, 0.6, 0.18, 14, seed=11)
    # boeven schrikken
    Mens('Lange', 'lang', pose=dict(loc=(-0.03, 0.02, 0.012), arm_l='up', arm_r='cheer', legs='walk', head=-6),
         expr=dict(mouth='o', brows='worried', look=(-0.25, 0.1))).build()
    Mens('Dikkie', 'dik', pose=dict(loc=(0.1, 0.0, 0.018), arm_l='cheer', arm_r='up', legs='walk', head=6),
         expr=dict(mouth='o', brows='worried', look=(0.25, 0.1))).build()
    sack = PS.sack('Zak', 0.03, -0.02, 0.0, s=1.0, cookies_out=0)
    rng = np.random.default_rng(5)
    for i, (x, z) in enumerate(((-0.05, 0.25), (0.03, 0.28), (0.11, 0.26), (0.0, 0.21), (0.08, 0.22), (0.16, 0.2))):
        PS.cookie(f'Vliegkoek{i}', x, -0.03, z, r=0.9, seed=30 + i, rot=rng.uniform(-60, 60))
    for i, (x, z, s) in enumerate(((-0.07, 0.02, 0.9), (0.16, 0.025, 0.8))):
        PS.puff(f'Sprong{i}', x, 0.0, z, s=s, col='#f3ede0')
    # Daan links, Joep rechts
    Daan('Daan', pose=dict(loc=(-0.27, -0.14, 0.0), arm_r='stop', arm_l='hip', head=-4),
         expr=dict(mouth='open', brows='cross', look=(0.2, 0.0)), cap=True).build()
    Joep('Joep', pose=dict(loc=(0.25, -0.1, 0.055), arm_l='up', arm_r='up', legs='walk', head=8),
         expr=dict(mouth='open', brows='cross', look=(-0.2, 0.0)), cap=True).build()
    PS.speedlines('Joepvaart', 0.3, -0.095, 0.075, n=3, L=5, gap=1.6)
    for i, (x, y) in enumerate(((-0.48, -0.3), (-0.08, -0.34), (0.22, -0.32), (0.5, -0.3))):
        PS.tuft(f'Pol{i}', x, y, h=4.0, w=7, color='#5f9a3f', seed=i + 3)
    V.cam((0.0, -0.84, 0.1), (0.0, 0.0, 0.12), lens=38, fstop=8.0, focus=(-0.05, -0.05, 0.1))
    K.render(out)
