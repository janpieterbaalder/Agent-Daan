"""p. 4: Daan zet zijn politiepet op.

In zijn kamer: Daan in zijn politiepakje zet met twee handen zijn pet op, de pet nog net boven zijn hoofd.
Naast hem de verkleedkist; op het bed zit Joep te kijken. Linksonder rust voor de zin."""
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep


def main(out, opts):
    V.setup(opts, 'page')
    info = PS.bedroom(night=False, bed_x=0.13, window_x=-0.06, y_wall=0.16, toys=False, w=120)
    PS.crate('Verkleedkist', -0.12, -0.02, w=12, h=6)
    PS.card('Kistdeksel', PS.rrect(0, 0, 12.5, 1.0, 0.3), '#8a5a36', -0.024, x=-0.12, z=0.062, paper='kraft')
    PS.card('Sjaal', PS.strip([(-4, 6.5), (-2, 7.4), (0, 6.8), (1, 4.5)], 1.0), '#d9443a', -0.027, x=-0.12,
            paper='crepe')
    Daan('Daan', pose=dict(loc=(0.0, -0.06, 0.0), arm_l=(168, 186), arm_r=(168, 186), head=-3, cap_lift=0.9,
                           cap_tilt=-12), expr=dict(mouth='grin', brows='up', look=(0.0, 0.3)), cap=True).build()
    Joep('Joep', pose=dict(loc=(0.105, info['bed_y'] - 0.02, 0.093), arm_l='down', arm_r='wave', legs='sit',
                           head=-8), expr=dict(mouth='grin', look=(-0.25, 0.1)), cap=False).build()
    V.cam((0.0, -0.5, 0.1), (0.0, 0.0, 0.1), lens=40, fstop=6.0, focus=(0.0, -0.06, 0.1))
    K.render(out)
