"""p. 8-9: Oh nee! Bij de bakker zijn alle koekjes weg.

Binnen in de bakkerij. Broden liggen nog op het bovenste schap, maar de bakplaten zijn leeg en de glazen
koekjespot ook; alleen kruimels. De bakker achter de toonbank slaat zijn handen omhoog. Daan en Joep
komen net binnen door de deur met het belletje (links)."""
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, Mens

CM = 0.01


def main(out, opts):
    V.setup(opts)
    yw = 0.16
    info = PS.shop(empty=True, y_wall=yw)
    # deur met ruitje en belletje, links
    PS.card('Deur', PS.rrect(0, 15, 15, 30, 0.8), '#2f5d4a', yw - 0.002, x=-0.3, paper='linnen')
    PS.card('Deurraam', PS.rrect(0, 20, 10, 12, 0.6), '#a6cfea', yw - 0.0032, x=-0.3, paper='glans')
    PS.card('Deurklink', PS.circle(5.0, 13, 0.7, 20), '#e3b23c', yw - 0.0034, x=-0.3, paper='folie')
    PS.card('Belbeugel', PS.rrect(0, 31.5, 0.4, 2.0, 0.1), '#3a2a20', yw - 0.004, x=-0.24, paper='kraft')
    PS.card('Bel', PS.chaikin(PS.np.array([(-1.4, 0), (1.4, 0), (0.9, 2.0), (-0.9, 2.0)]), 2), '#e3b23c', yw - 0.005,
            x=-0.24, z=0.288, paper='folie')
    PS.flat('Vloer', PS.rrect(0, -20, 200, 80, 1), '#d8c7a8', z=0.0, thick=0.001, paper='mat')
    PS.pavement('Vloertegels', -1.0, 1.0, -0.6, yw, kind='tegel', seed=4)
    # bakker achter de toonbank
    Mens('Bakker', 'bakker', pose=dict(loc=(0.05, info['counter_y'] + 0.03, 0.0), arm_l='up', arm_r='up', head=4),
         expr=dict(mouth='o', brows='worried', look=(-0.2, 0.0))).build()
    # Daan en Joep komen binnen
    Daan('Daan', pose=dict(loc=(-0.15, -0.04, 0.0), arm_l='out', arm_r='out', head=-4),
         expr=dict(mouth='o', brows='up', look=(0.25, 0.1)), cap=True).build()
    Joep('Joep', pose=dict(loc=(-0.075, -0.06, 0.0), arm_l='up', arm_r='up', head=6),
         expr=dict(mouth='o'), cap=True).build()
    V.cam((0.0, -0.74, 0.16), (0.0, 0.0, 0.18), lens=28, fstop=8.0, focus=(-0.05, -0.05, 0.12))
    K.render(out)
