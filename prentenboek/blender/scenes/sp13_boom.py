"""p. 13-14: Joep klimt in de boom. Hup, hup, hup! Kikvorsperspectief langs de stam omhoog; Joep halverwege,
Daan onderaan wijst omhoog; zon door het bladerdak."""
import math
from lib import core as K, cast, stage, sets, world as Wd
from lib.daan import Daan
from lib.joep import Joep, joep_mats


def main(out, opts):
    Q = stage.setup(opts, 'spread')
    dm = cast.char_mats()
    jm = joep_mats(dm)
    stage.sky('#4d8fdb', '#cfe6f3', '#8f9a7a', 1.1)
    stage.sun(110, 62, 4.5)
    sets.park(None, Q, grass_region=(-1.5, 1.5, -1.5, 1.0), trees=[(4, 6, 5.5, 1.8), (-5, 5, 6, 2.0)],
              bushes=[(-1.8, 1.8, 0.9)], path=False, flowers_n=12, houses=False)
    Wd.tree('Klimboom', (0, 0, 0), height=6.5, crown=2.4, seed=33, density=int(800 * Q['leaves']),
            trunk_r=0.2, leaf_size=0.09)
    j = Joep('Joep', pose=dict(
        root=(0, 0, 0), head=(-0.5, 0.5, 0.1),
        arm_r=[(-0.05, -0.04, 0.05), (-0.08, -0.1, 0.1), (-0.07, -0.15, 0.15)],
        arm_l=[(0.05, -0.04, 0.02), (0.08, -0.1, 0.03), (0.07, -0.15, 0.04)],
        leg_r=[(-0.03, -0.04, -0.03), (-0.06, -0.08, -0.03), (-0.06, -0.13, -0.02)],
        leg_l=[(0.03, -0.05, -0.06), (0.06, -0.1, -0.09), (0.06, -0.15, -0.12)],
        tail=[(0.0, 0.04, -0.03), (0.02, 0.07, -0.07), (0.05, 0.08, -0.1)]),
        mats=jm, fur=Q['fur'], )
    jr = j.build()
    jr.scale = (1.0,) * 3
    jr.location = (0.06, -0.27, 0.95)
    jr.rotation_euler = (0.1, 0, math.pi - 0.25)
    cam = (0.38, -0.58, 0.12)
    d = Daan('Daan', pose=dict(
        root=(-0.28, -0.66, 0.0), yaw=96, head=(-30, -10, 0), lean=(-0.12, 0.0),
        hand_r=(-0.06, -0.15, 0.95), palm_r=(1, 0, 0), fdir_r=(0.15, -0.2, 1), fingers_r='point', elbow_r=(-1, 0, -0.3),
        hand_l=(0.17, -0.02, 0.36), fingers_l='relaxed'),
        expr=dict(smile=1.0, mouth='grin', open=0.6, squint=0.1, look_at=(0.38, -0.58, 0.12)), cap=True, mats=dm,
        hair_density=Q['hair'])
    d.build()
    K.camera(cam, (0.0, -0.1, 2.4), lens=14, fstop=5.6, focus=(0.06, -0.27, 1.05), roll=0.5)
    K.light('AREA', (1.5, -2.5, 1.0), (0, 0, 1.2), energy=300, size=3.0, color=(0.9, 0.95, 1.0))
    K.render(out)
