"""Titelpagina-vignet: Daan in zijn politiepakje houdt Joep in zijn armen, vrijstaand met zachte schaduw."""
import bpy
from lib import core as K, papier as P, papierscene as V
from lib.papierpop import Daan, Joep


def main(out, opts):
    V.setup(opts, 'page', transparent=True)
    Daan('Daan', pose=dict(loc=(0.0, 0.0, 0.0), arm_l='hug', arm_r='hug', head=-5),
         expr=dict(mouth='grin', brows='up', look=(0.1, 0.0)), cap=True).build()
    Joep('Joep', pose=dict(loc=(0.004, -0.009, 0.016), arm_l='down', arm_r='wave', legs='hang', head=8),
         expr=dict(mouth='grin'), cap=False).build()
    sv = P.piece('Schaduwvanger', P.rrect(0, 0, 60, 60, 1), '#ffffff', None, 0, plane='xy', z=0.0, jitter=0.0, bend=0)
    sv.is_shadow_catcher = True
    V.cam((0.0, -0.42, 0.09), (0.0, 0.0, 0.075), lens=50, fstop=8.0, focus=(0.0, -0.01, 0.08))
    K.render(out)
