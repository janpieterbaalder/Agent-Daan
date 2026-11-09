"""p. 5: Joep krijgt ook een pet. Nu zijn ze agent!

Daan en Joep staan naast elkaar op het kleedje en salueren, allebei met een pet; Joep staat op de
verkleedkist zodat hij er ook bij is. Rechtsboven en rechtsonder ruimte voor de tekst."""
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep


def main(out, opts):
    V.setup(opts, 'page')
    PS.bedroom(night=False, bed_x=-0.2, window_x=0.05, y_wall=0.16, toys=False, w=120)
    PS.crate('Verkleedkist', 0.0, -0.05, w=10, h=6)
    Daan('Daan', pose=dict(loc=(-0.075, -0.07, 0.0), arm_r='salute', arm_l='down', head=-3),
         expr=dict(mouth='grin', brows='up', look=(0.1, 0.05)), cap=True).build()
    Joep('Joep', pose=dict(loc=(0.0, -0.055, 0.06), arm_r='salute', arm_l='down', head=6),
         expr=dict(mouth='grin', look=(-0.1, 0.05)), cap=True).build()
    V.cam((-0.02, -0.5, 0.1), (-0.02, 0.0, 0.1), lens=40, fstop=6.0, focus=(-0.04, -0.06, 0.1))
    K.render(out)
