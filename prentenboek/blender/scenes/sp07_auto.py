"""p. 6-7: Nie-nu, nie-nu! Daar gaat de politieauto.

Door de polder: een weggetje langs de sloot, een molen op de dijk, koeien-groen. De politieauto rijdt
naar rechts met Daan achter het stuur en Joep achterin; zwaailicht aan, stofwolkjes en snelheidsstreepjes
erachter. Links boven en links onder blijft ruimte voor de tekst."""
import math
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep

CM = 0.01


def main(out, opts):
    V.setup(opts)
    clouds = ((-46, 42, 0.8), (-10, 50, 0.6), (40, 44, 0.75))
    PS.sky(y=0.55, w=180, h=75, sun=(60, 46), clouds=clouds)
    for i, (cx, cz, s) in enumerate(clouds):
        PS.thread(f'Wolkdraad{i}', cx * CM, 0.55 - 0.009 - 0.002 * i, cz * CM + 0.045 * s)
    PS.thread('Zondraad', 0.6, 0.544, 0.46 + 0.115)
    PS.hills(y0=0.48, w=180, colors=('#a8d07a', '#93c264', '#7fb352'), seed=5)
    PS.windmill('Molen', -0.34, 0.4, s=1.25, rot=20)
    for i, (tx, ty, th, tr) in enumerate(((-0.05, 0.36, 13, 6), (0.04, 0.37, 11, 5), (0.44, 0.34, 14, 6.5))):
        PS.tree(f'Boom{i}', tx, ty, th, tr, seed=i + 4)
    # sloot met riet achter de weg
    PS.flat('Sloot', PS.rrect(0, 22, 200, 5, 0.5), '#5f9fcf', z=0.0008, thick=0.0006, paper='zijde')
    for i, x in enumerate((-0.6, -0.42, 0.28, 0.52)):
        PS.tuft(f'Riet{i}', x, 0.19, h=6.5, w=4, color='#6f9a3a', seed=10 + i, n=5)
    PS.grassland(y0=-0.6, y1=0.5, color='#8cc35e')
    PS.road('Weg', -1.0, 1.0, -0.04, 0.12)
    # auto
    car = PS.police_car('Auto', 0.17, 0.04, facing=1, scale=1.0, back_open=True)
    car['root'].rotation_euler[1] = math.radians(-2.5)
    Daan('Daan', pose=dict(loc=car['driver'], arm_r='forward', arm_l='forward', legs='sit', head=-3),
         expr=dict(mouth='grin', look=(0.2, 0.0)), cap=True).build()
    Joep('Joep', pose=dict(loc=car['back'], arm_r='wave', arm_l='down', legs='sit', head=6),
         expr=dict(mouth='grin'), cap=True).build()
    for i, (x, z, s) in enumerate(((-0.05, 0.02, 1.4), (-0.1, 0.035, 1.1), (-0.145, 0.05, 0.8), (-0.185, 0.06, 0.55))):
        PS.puff(f'Stof{i}', x, 0.035 - 0.002 * i, z, s=s, col='#f3ede0')
    PS.speedlines('Vaart', -0.03, 0.03, 0.09, n=3, L=9, gap=2.2)
    # voorgrond: gras en bloemen
    for i, (x, y) in enumerate(((-0.5, -0.28), (-0.2, -0.32), (0.1, -0.3), (0.42, -0.31))):
        PS.tuft(f'Pol{i}', x, y, h=4.0, w=7, color='#5f9a3f', seed=i)
    PS.flowers('Bloem', -0.55, 0.55, -0.22, 16, seed=8)
    V.cam((0.0, -0.84, 0.1), (0.0, 0.0, 0.11), lens=38, fstop=8.0, focus=(0.17, 0.04, 0.08))
    K.render(out)
