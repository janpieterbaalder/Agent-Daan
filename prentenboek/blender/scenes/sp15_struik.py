"""p. 14-15: Joep ziet iets. Daar, achter de struik!

Dezelfde grote boom als op de vorige bladzijde, links. Joep zit op een tak en wijst; Daan staat onder de
boom en kijkt naar hem op. Rechts in het park staat een struik: daarachter zitten de twee boeven, hun
mutsen en maskers steken er duidelijk bovenuit. Naast de struik de zak met koekmannetjes, en een spoor
van kruimels loopt erheen."""
import numpy as np
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, Mens

CM = 0.01


def main(out, opts):
    V.setup(opts)
    PS.sky(y=0.6, w=180, h=85, sun=(60, 52), clouds=((-10, 56, 0.7), (36, 62, 0.6)))
    PS.thread('Zondraad', 0.6, 0.594, 0.52 + 0.115)
    PS.hills(y0=0.52, w=180, seed=7)
    PS.tree('Boom1', 0.48, 0.42, 13, 6, seed=5)
    PS.grassland(y0=-0.6, y1=0.55)
    PS.flowers('Bloem', -0.6, 0.6, 0.2, 16, seed=6)
    # de grote boom links met Joep op de rechtertak
    tx, ty, h = -0.3, 0.06, 26
    PS.big_tree('Grote_boom', tx, ty, h=h, apples=5)
    Joep('Joep', pose=dict(loc=(tx + 0.085, ty - 0.004, (h - 1.6) * CM), arm_l='salute', arm_r='point', legs='sit',
                           head=-6), expr=dict(mouth='o', brows='up', look=(0.3, -0.1)), cap=True).build()
    Daan('Daan', pose=dict(loc=(tx + 0.1, -0.06, 0.0), arm_r='point', arm_l='down', head=10),
         expr=dict(mouth='o', brows='up', look=(-0.1, 0.35)), cap=True).build()
    # de boeven achter de struik: mutsen en maskers erboven
    bx, by = 0.2, 0.08
    Mens('Lange', 'lang', pose=dict(loc=(bx - 0.055, by + 0.025, -0.044), arm_l='down', arm_r='down', legs='sit',
                                    head=-5), expr=dict(mouth='grin', look=(-0.2, 0.0))).build()
    Mens('Dikkie', 'dik', pose=dict(loc=(bx + 0.06, by + 0.022, -0.012), arm_l='down', arm_r='down', legs='sit',
                                    head=6), expr=dict(mouth='grin', look=(-0.2, 0.0))).build()
    PS.bush('Struik', bx, by, 36, 11, berries=6, seed=11)
    PS.sack('Zak', bx + 0.19, by - 0.01, 0.0, s=1.0, cookies_out=3)
    rng = np.random.default_rng(6)
    pts = [(-0.05 + 0.25 * t + rng.normal(0, 0.006), -0.12 + 0.18 * t + rng.normal(0, 0.005))
           for t in np.linspace(0, 1, 40)]
    PS.crumbs('Kruimel', pts, seed=6, z=0.0012, size=1.6)
    for i, (x, y) in enumerate(((-0.46, -0.3), (-0.1, -0.34), (0.2, -0.32), (0.48, -0.3))):
        PS.tuft(f'Pol{i}', x, y, h=4.0, w=7, color='#5f9a3f', seed=i + 2)
    V.cam((0.0, -0.84, 0.1), (0.0, 0.0, 0.135), lens=36, fstop=8.0, focus=(0.0, 0.0, 0.12))
    K.render(out)
