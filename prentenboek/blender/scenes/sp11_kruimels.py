"""p. 10-11: Kijk eens, kruimels! Wie heeft dat gedaan?

Kikvorsperspectief op de stoep voor de bakkerij. Vlak voor de camera (onscherp) ligt een koekmannetje met
een hap eruit en grote kruimels. Daan buigt zich met zijn vergrootglas over het spoor, Joep wijst waar het
heen gaat: schuin naar rechts achter, de straat uit."""
import numpy as np
from lib import core as K, papier as P, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep

CM = 0.01


def main(out, opts):
    V.setup(opts)
    PS.sky(y=0.6, w=180, h=80, sun=(56, 48), clouds=((-30, 50, 0.8), (30, 56, 0.6)))
    yh = 0.26
    with PS.scaled((-0.12, yh, 0), 1.35):
        PS.bakery('Bakkerij', -0.12, yh)
    for i, (hx, w, h, col, rf, dr) in enumerate(((-0.42, 14, 16, '#9fb3d9', '#b8503e', '#7a4f8f'),
                                                (0.18, 14, 15, '#e88a7d', '#4b5d7a', '#4f7a3a'),
                                                (0.44, 13, 17, '#8fb8a8', '#6b4a3a', '#a83b3b'))):
        with PS.scaled((hx, yh + 0.004 * i, 0), 1.35):
            PS.house(f'Huis{i}', hx, yh + 0.004 * i, w, h, col, rf, dr, seed=i + 3)
    PS.lamppost('Lantaarn', 0.07, yh - 0.05, h=30)
    PS.pavement('Stoep', -1.0, 1.0, -0.7, yh + 0.005, kind='tegel', seed=6)
    # kruimelspoor: van de bakkerijdeur schuin naar rechts achter
    rng = np.random.default_rng(2)
    pts = []
    for t in np.linspace(0, 1, 60):
        x = 0.12 + 0.28 * t + 0.03 * np.sin(t * 7)
        y = -0.17 + 0.4 * t
        pts.append((x + rng.normal(0, 0.008), y + rng.normal(0, 0.006)))
    PS.crumbs('Kruimel', pts, seed=5, z=0.0007, size=1.9)
    # voorgrond: groot koekmannetje met hap en dikke kruimels
    PS.cookie('Voorkoek', 0.12, -0.21, 0.0012, r=2.2, seed=3, bite=True, flat_=True, rot=-25)
    PS.crumbs('Grote_kruimel', [(0.07, -0.19), (0.16, -0.18), (0.18, -0.23), (0.09, -0.24), (0.14, -0.15)],
              seed=9, z=0.0007, size=2.4)
    # Daan met vergrootglas, Joep wijst
    d = Daan('Daan', pose=dict(loc=(-0.1, -0.13, 0.0), arm_r=(70, 80), arm_l='hip', head=8),
             expr=dict(mouth='o', brows='up', look=(0.3, -0.15)), cap=True)
    d.build()

    def held(par, loc):
        # handvat in de vuist (hand vóór het steeltje), lens voorbij de hand, iets naar de kruimels gekanteld
        grip = P.group('Vergrootglas_greep', par, (0.0, 0.0), angle=12)
        return PS.magnifier('Vergrootglas', grip, (0.0, -3.0), 3.0, rot=180, s=1.0)
    V.in_hand(d, 1, held)
    Joep('Joep', pose=dict(loc=(0.095, -0.16, 0.0), arm_r='point', arm_l='down', head=-6),
         expr=dict(mouth='grin', look=(0.25, 0.0)), cap=True).build()
    V.cam((0.02, -0.6, 0.13), (0.02, 0.0, 0.06), lens=34, fstop=5.6, focus=(-0.12, -0.14, 0.06))
    K.render(out)
