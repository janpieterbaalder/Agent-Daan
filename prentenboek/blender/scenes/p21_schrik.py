"""p. 20: De boeven schrikken.

Dichtbij: de twee boeven springen op van schrik, armen omhoog, ogen wijd open; de zak valt om en de
koekmannetjes vliegen door de lucht. Onderaan rustig gras voor de tekst."""
import math
import numpy as np
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Mens

CM = 0.01


def main(out, opts):
    V.setup(opts, 'page')
    PS.sky(y=0.4, w=120, h=70, sun=None, clouds=((-20, 40, 0.6), (24, 46, 0.5)))
    PS.hills(y0=0.33, w=120, seed=12)
    PS.grassland(y0=-0.5, y1=0.4)
    PS.bush('Struik', 0.0, 0.16, 50, 12, berries=6, seed=16)
    Mens('Lange', 'lang', pose=dict(loc=(-0.055, 0.0, 0.02), arm_l='up', arm_r='up', legs='walk', head=-8),
         expr=dict(mouth='o', brows='worried', look=(0.0, 0.25))).build()
    Mens('Dikkie', 'dik', pose=dict(loc=(0.065, -0.02, 0.03), arm_l='cheer', arm_r='cheer', legs='walk', head=8),
         expr=dict(mouth='o', brows='worried', look=(0.0, 0.25))).build()
    zak = PS.sack('Zak', 0.0, -0.05, 0.0, s=1.0, cookies_out=0)
    rng = np.random.default_rng(8)
    for i in range(8):
        a = i / 8 * math.pi
        PS.cookie(f'Vliegkoek{i}', 0.005 + 0.11 * math.cos(a), -0.06 - 0.004 * i, 0.12 + 0.08 * math.sin(a),
                  r=1.0, seed=50 + i, rot=rng.uniform(-80, 80))
    for i, (x, y) in enumerate(((-0.14, -0.2), (0.12, -0.22))):
        PS.tuft(f'Pol{i}', x, y, h=3.5, w=6, color='#5f9a3f', seed=i + 5)
    V.cam((0.0, -0.5, 0.11), (0.0, 0.0, 0.12), lens=40, fstop=7.0, focus=(0.0, -0.02, 0.12))
    K.render(out)
