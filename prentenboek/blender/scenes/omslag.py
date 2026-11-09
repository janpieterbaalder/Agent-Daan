"""Omslag (doorlopend), papieren kijkdoos.

Voorkant (rechts): agent Daan staat groot vooraan en salueert; achter hem de politieauto met zwaailicht,
Joep zit op de motorkap en salueert mee. Boven open lucht voor de titel; zon en wolken hangen aan draadjes.
Achterkant (links): verder weg sluipen de twee boeven bij de bakkerij weg met de zak. Een spoor van
kruimels loopt schuin door de diepte van de boeven naar Daans voeten."""
import numpy as np
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, Mens

CM = 0.01


def main(out, opts):
    V.setup(opts)
    clouds = ((-46, 36, 0.9), (-6, 41, 0.7), (30, 37, 0.65))
    PS.sky(y=0.55, w=180, h=75, sun=(52, 42), clouds=clouds)
    for i, (cx, cz, s) in enumerate(clouds):
        PS.thread(f'Wolkdraad{i}', cx * CM, 0.55 - 0.009 - 0.002 * i, cz * CM + 0.045 * s)
    PS.thread('Zondraad', 0.52, 0.544, 0.42 + 0.115)
    PS.hills(y0=0.47, w=180)
    # achterkant: huizen en bakkerij; voorkant: laag park, zodat de lucht vrij blijft voor de titel
    yh = 0.24
    for i, (hx, w, h, col, rf, dr) in enumerate(((-0.56, 14, 15, '#8fb8a8', '#4b5d7a', '#a83b3b'),
                                                (-0.1, 13, 13, '#e9b44c', '#b8503e', '#2f6b8f'))):
        with PS.scaled((hx, yh, 0), 1.3):
            PS.house(f'Huis{i}', hx, yh, w, h, col, rf, dr, seed=i + 1)
    with PS.scaled((-0.33, yh, 0), 1.3):
        PS.bakery('Bakkerij', -0.33, yh)
    for i, (tx, ty, th, tr) in enumerate(((0.12, 0.36, 15, 7), (0.3, 0.4, 17, 8), (0.5, 0.37, 14, 6.5))):
        PS.tree(f'Boom{i}', tx, ty, th, tr, apples=3 if i == 1 else 0, seed=i + 2)
    PS.bush('Haag0', 0.18, yh + 0.03, 28, 5, seed=3)
    PS.bush('Haag1', 0.42, yh + 0.025, 26, 5.5, berries=4, seed=4)
    PS.flowers('Bloem', 0.05, 0.6, yh + 0.012, 14, seed=5)
    # straat: grijze stoeptegels, stoeprand, rode klinkers in visgraat
    PS.pavement('Stoep', -0.9, 0.9, yh - 0.085, yh + 0.01, kind='tegel', seed=2)
    PS.card('Stoeprand', PS.rrect(0, 0.45, 180, 0.9, 0.3), '#b9b2a6', yh - 0.086, x=0.0)
    PS.pavement('Weg', -0.9, 0.9, -0.5, yh - 0.086, kind='klinker', seed=3)
    # politieauto, Joep op de motorkap
    PS.police_car('Auto', 0.17, 0.03, facing=-1, scale=0.9)
    Joep('Joep', pose=dict(loc=(0.06, 0.016, 0.073), arm_r='salute', arm_l='down', legs='sit', head=-5),
         expr=dict(mouth='grin'), cap=True).build()
    # Daan vooraan
    Daan('Daan', pose=dict(loc=(0.15, -0.25, 0.0), arm_r='salute', arm_l='down', head=4),
         expr=dict(mouth='grin', look=(-0.1, 0.05)), cap=True).build()
    # boeven verder weg bij de bakkerij, sluipend met de zak
    Mens('Lange', 'lang', pose=dict(loc=(-0.335, 0.13, 0.0), arm_l='hold', arm_r='hold', legs='walk', head=-6),
         expr=dict(mouth='smile', brows='cross', look=(-0.2, 0))).build()
    PS.sack('Zak', -0.34, 0.115, 0.035, s=1.0, cookies_out=3)
    Mens('Dikkie', 'dik', pose=dict(loc=(-0.215, 0.11, 0.0), arm_l='point', arm_r='down', legs='walk', head=5),
         expr=dict(mouth='o', brows='worried', look=(-0.25, 0))).build()
    # kruimelspoor van de zak naar Daan
    rng = np.random.default_rng(4)
    pts = []
    for t in np.linspace(0, 1, 46):
        x = -0.32 + 0.45 * t + 0.02 * np.sin(t * 9)
        y = 0.09 - 0.32 * t + 0.01 * np.cos(t * 7)
        pts.append((x + rng.normal(0, 0.006), y + rng.normal(0, 0.004)))
    PS.crumbs('Kruimel', pts, seed=3, z=0.0016, size=1.5)
    for i, (x, y, r) in enumerate(((-0.15, 0.0, 0.8), (0.02, -0.13, 0.9))):
        PS.cookie(f'Kruimelkoek{i}', x, y, 0.0017, r=r, seed=12 + i, bite=True, flat_=True, rot=20 + 60 * i)
    V.cam((0.0, -0.84, 0.085), (0.0, 0.0, 0.118), lens=38, fstop=8.0, focus=(0.15, -0.25, 0.08))
    K.render(out)
