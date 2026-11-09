"""p. 16-17: Twee boeven met een zak vol koekjes. Smik, smak, smul!

Achter de struik zitten de boeven in het gras met de open zak tussen zich in en eten koekmannetjes; overal
kruimels. Links vooraan, achter een struik, kijken Daan en Joep stiekem over de rand."""
import numpy as np
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, Mens

CM = 0.01


def main(out, opts):
    V.setup(opts)
    PS.sky(y=0.6, w=180, h=80, sun=(58, 46), clouds=((-20, 48, 0.8), (36, 54, 0.6)))
    PS.thread('Zondraad', 0.58, 0.594, 0.46 + 0.115)
    PS.hills(y0=0.52, w=180, seed=9)
    PS.tree('Boom0', -0.05, 0.42, 16, 7.5, apples=3, seed=3)
    PS.tree('Boom1', 0.48, 0.44, 15, 7, seed=6)
    PS.grassland(y0=-0.6, y1=0.55)
    PS.bush('Achterstruik', 0.2, 0.2, 40, 10, seed=12)
    PS.flowers('Bloem', -0.5, 0.6, 0.12, 14, seed=10)
    # boeven in het gras
    yb = 0.04
    lange = Mens('Lange', 'lang', pose=dict(loc=(0.06, yb, -0.076), arm_l='down', arm_r=(25, -110), legs='sit', head=-6),
                 expr=dict(mouth='grin', eyes='happy'))
    lange.build()
    dik = Mens('Dikkie', 'dik', pose=dict(loc=(0.27, yb + 0.004, -0.031), arm_l=(30, -115), arm_r='down', legs='sit',
                                           head=6), expr=dict(mouth='open'))
    dik.build()
    V.in_hand(lange, 1, lambda par, loc: PS.cookie('Koek_lang', 0, loc[1], 0.004, r=1.0, seed=1, bite=True,
                                                   parent=par, rot=20))
    V.in_hand(dik, -1, lambda par, loc: PS.cookie('Koek_dik', 0, loc[1], 0.004, r=1.0, seed=2, bite=True,
                                                  parent=par, rot=-20))
    PS.sack('Zak', 0.165, yb - 0.01, 0.0, s=1.0, cookies_out=3)
    for i, (x, rot) in enumerate(((0.12, 70), (0.21, -60), (0.33, 30))):
        PS.cookie(f'Grondkoek{i}', x, yb - 0.03 - 0.01 * i, 0.0013, r=1.0, seed=20 + i, flat_=True, rot=rot,
                  bite=i == 1)
    rng = np.random.default_rng(3)
    PS.crumbs('Kruimel', [(rng.uniform(0.0, 0.36), rng.uniform(-0.07, 0.03)) for _ in range(40)], seed=4, z=0.0012,
              size=1.4)
    # Daan en Joep gluren over de struik vooraan links
    Daan('Daan', pose=dict(loc=(-0.25, -0.2, 0.0), arm_l='down', arm_r='down', head=-6),
         expr=dict(mouth='o', brows='up', look=(0.3, -0.05)), cap=True).build()
    Joep('Joep', pose=dict(loc=(-0.165, -0.205, 0.072), arm_l='down', arm_r='down', head=8),
         expr=dict(mouth='o', look=(0.3, -0.05)), cap=True).build()
    PS.bush('Gluurstruik', -0.21, -0.23, 26, 9.0, berries=4, seed=14)
    V.cam((0.0, -0.84, 0.11), (0.03, 0.0, 0.08), lens=38, fstop=8.0, focus=(0.15, 0.04, 0.06))
    K.render(out)
