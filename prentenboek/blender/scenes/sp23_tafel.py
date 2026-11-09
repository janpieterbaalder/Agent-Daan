"""p. 22-23: Samen brengen ze de koekjes terug. Iedereen krijgt er één. Joep krijgt er twee!

Voor de bakkerij staat een lange tafel met een boerenbont kleed en een schaal koekmannetjes. Erachter: de
boeven (masker omhoog, blij), de bakker, Daan. Rechts staat Joep op een kistje met in elke hand een koek."""
import numpy as np
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, Mens

CM = 0.01


def main(out, opts):
    V.setup(opts)
    PS.sky(y=0.6, w=180, h=80, sun=(60, 50), clouds=((-44, 52, 0.7), (10, 58, 0.6)))
    PS.thread('Zondraad', 0.6, 0.594, 0.5 + 0.115)
    yh = 0.26
    with PS.scaled((-0.04, yh, 0), 1.35):
        PS.bakery('Bakkerij', -0.04, yh)
    for i, (hx, w, h, col, rf, dr) in enumerate(((-0.36, 14, 16, '#8fb8a8', '#4b5d7a', '#a83b3b'),
                                                (0.3, 14, 15, '#e9b44c', '#b8503e', '#2f6b8f'))):
        with PS.scaled((hx, yh, 0), 1.35):
            PS.house(f'Huis{i}', hx, yh, w, h, col, rf, dr, seed=i + 5)
    PS.pavement('Stoep', -1.0, 1.0, yh - 0.11, yh + 0.005, kind='tegel', seed=7)
    PS.card('Stoeprand', PS.rrect(0, 0.45, 200, 0.9, 0.3), '#b9b2a6', yh - 0.111, x=0.0)
    PS.pavement('Weg', -1.0, 1.0, -0.6, yh - 0.111, kind='klinker', seed=8)
    PS.bunting('Vlaggetjes', -0.45, 0.45, 0.25, yh - 0.02, n=16, sag=3.5)
    # figuren achter de tafel
    yt = 0.0
    Mens('Lange', 'lang', pose=dict(loc=(-0.27, yt + 0.045, 0.0), arm_l='down', arm_r='hold', head=-5),
         expr=dict(mouth='grin', look=(0.1, 0.0)), mask_up=True).build()
    Mens('Dikkie', 'dik', pose=dict(loc=(-0.15, yt + 0.042, 0.0), arm_l='hold', arm_r='down', head=5),
         expr=dict(mouth='grin', eyes='happy'), mask_up=True).build()
    Mens('Bakker', 'bakker', pose=dict(loc=(-0.02, yt + 0.046, 0.0), arm_l='hip', arm_r='wave', head=-4),
         expr=dict(mouth='grin', look=(0.15, 0.0))).build()
    d = Daan('Daan', pose=dict(loc=(0.11, yt + 0.04, 0.0), arm_l='down', arm_r='hold', head=4),
             expr=dict(mouth='grin', look=(0.15, 0.0)), cap=True)
    d.build()
    V.in_hand(d, 1, lambda par, loc: PS.cookie('Daankoek', 0, loc[1], 0.004, r=0.9, seed=31, parent=par, rot=10))
    tb = PS.table('Tafel', -0.08, yt + 0.008, w=46, h=7.5, depth=2.6)
    top, fy = tb['top'], tb['front']
    # schaal van opzij met koekmannetjes erop, een glas melk, losse koekjes bij de boeven
    PS.card('Schaal', PS.np.array([(-6.0, 0.0), (6.0, 0.0), (7.2, 1.1), (-7.2, 1.1)]), '#fbf7ef', fy + 0.008,
            x=0.0, z=top + 0.0008, paper='glans')
    PS.card('Schaalvoet', PS.rrect(0, 0, 4.0, 0.5, 0.2), '#e9e2d2', fy + 0.0084, x=0.0, z=top + 0.0006,
            paper='glans')
    for i, x in enumerate((-0.045, -0.022, 0.0, 0.022, 0.045)):
        PS.cookie(f'Schaalkoek{i}', x, fy + 0.0095, top + 0.0105 + 0.002 * (i % 2), r=0.95, seed=70 + i,
                  rot=(-12 + 6 * i))
    for i, (x, rot) in enumerate(((-0.215, 0), (-0.185, 10), (-0.155, -8))):
        PS.cookie(f'Tafelkoek{i}', x, fy + 0.006, top + 0.0095, r=0.9, seed=60 + i, rot=rot)
    PS.card('Melk', PS.rrect(0, 1.3, 1.5, 2.6, 0.35), '#fbf7ef', fy + 0.007, x=0.075, z=top + 0.0008, paper='glans')
    PS.card('Melkglas', PS.rrect(0, 1.5, 1.8, 3.0, 0.4), '#d8ecf6', fy + 0.0062, x=0.075, z=top + 0.0006,
            paper='raam')
    # Joep op een kistje rechts, met twee koeken
    PS.crate('Kistje', 0.25, -0.06, w=7, h=5)
    j = Joep('Joep', pose=dict(loc=(0.25, -0.065, 0.05), arm_l='cheer', arm_r='cheer', head=6),
             expr=dict(mouth='grin', eyes='happy'), cap=True)
    j.build()
    for side in (-1, 1):
        V.in_hand(j, side, lambda par, loc, side=side: PS.cookie(f'Joepkoek{side}', 0, loc[1], 0.006, r=1.3,
                                                                  seed=80 + side, parent=par, rot=side * 15))
    V.cam((0.0, -0.84, 0.13), (0.0, 0.0, 0.12), lens=38, fstop=8.0, focus=(0.0, 0.0, 0.1))
    K.render(out)
