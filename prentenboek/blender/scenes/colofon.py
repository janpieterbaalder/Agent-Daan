"""Einde-vignet: Joep is in slaap gevallen tegen een groot koekmannetje, zijn petje naast zich."""
from lib import core as K, papier as P, papierset as PS, papierscene as V
from lib.papierpop import Joep, daan_cap


def main(out, opts):
    V.setup(opts, 'page', transparent=True)
    PS.cookie('Grote_koek', 0.018, 0.004, 0.045, r=2.4, seed=4, bite=True, rot=-12)
    Joep('Joep', pose=dict(loc=(-0.012, -0.004, 0.0), arm_l='hug', arm_r='down', legs='sit', head=-16),
         expr=dict(mouth='smile', eyes='closed'), cap=False).build()
    hook = K.empty('Pethaak', (-0.045, -0.012, 0.012))
    daan_cap('Petje', hook, (0, 0), angle=-20, layer=0)
    hook.scale = (0.5, 0.5, 0.5)
    sv = P.piece('Schaduwvanger', P.rrect(0, 0, 40, 40, 1), '#ffffff', None, 0, plane='xy', z=0.0, jitter=0.0, bend=0)
    sv.is_shadow_catcher = True
    V.cam((0.0, -0.3, 0.05), (0.0, 0.0, 0.035), lens=55, fstop=8.0, focus=(0.0, -0.004, 0.035))
    K.render(out)
