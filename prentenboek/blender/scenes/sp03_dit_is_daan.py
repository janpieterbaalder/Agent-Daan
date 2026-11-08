"""p. 3-4: Dit is Daan. En dit is Joep, het aapje van Daan.
Van bovenaf op het ronde kleed in de slaapkamer; ochtendzon valt door het raam in lange vlekken over de vloer.
Daan zit links en zwaait omhoog, met zijn andere hand wijst hij naar Joep rechts."""
import math
from lib import core as K, cast, stage, sets
from lib.daan import Daan
from lib.joep import Joep, joep_mats


def main(out, opts):
    Q = stage.setup(opts, 'spread')
    dm = cast.char_mats()
    jm = joep_mats(dm)
    K.world_color('#fff3e0', 0.15)
    sets.bedroom(night=False, window_x=0.4)
    cam = (0.1, -1.9, 1.6)
    d = Daan('Daan', pose=dict(
        root=(-0.42, 0.1, 0.0), yaw=14, hip=(0, 0.04, 0.1), lean=(-0.05, 0.03), head=(-20, 6, -6),
        foot_r=(0.07, -0.17, 0.045), foot_l=(-0.05, -0.2, 0.06), knee_r=(-1, -0.25, 0.25), knee_l=(1, -0.25, 0.25),
        toe_r=(0.95, -0.3, 0), toe_l=(-0.95, -0.3, 0),
        hand_r=(-0.2, -0.12, 0.62), palm_r=(0, -0.6, 0.6), fdir_r=(-0.1, -0.2, 1), fingers_r='spread',
        elbow_r=(-0.8, 0.2, -0.4),
        hand_l=(0.32, -0.2, 0.32), palm_l=(0.2, -0.2, 1), fdir_l=(1, -0.3, 0.1), fingers_l='open',
        elbow_l=(0.5, 0.4, -0.6)),
        expr=dict(smile=1.0, mouth='grin', open=0.45, squint=0.2, look_at=cam), cap=False, mats=dm,
        hair_density=Q['hair'])
    d.build()
    j = Joep('Joep', pose=dict(
        root=(0.55, -0.18, 0.0), rot=(0, 0, -0.3), body_tilt=(-0.25, 0.0), head=(-0.55, 0.15, 0.18), scale=1.0,
        leg_r=[(-0.02, -0.06, -0.12), (-0.05, -0.12, -0.14), (-0.08, -0.17, -0.14)],
        leg_l=[(0.02, -0.06, -0.12), (0.05, -0.12, -0.14), (0.08, -0.17, -0.14)],
        arm_r=[(-0.02, -0.01, -0.05), (-0.04, -0.03, -0.09), (-0.05, -0.06, -0.12)],
        arm_l=[(0.03, -0.02, -0.04), (0.06, -0.04, -0.06), (0.09, -0.06, -0.06)],
        tail=[(0.0, 0.05, -0.12), (0.03, 0.09, -0.135), (0.07, 0.11, -0.14)]),
        mats=jm, fur=Q['fur'])
    jr = j.build()
    jr.location.z = -0.115
    jr.scale = (1.0, 1.0, 1.0)
    K.camera(cam, (0.0, 0.0, 0.3), lens=36, fstop=3.5, focus=(-0.25, -0.05, 0.45))
    stage.sun(95, 32, 6.5, color=(1.0, 0.88, 0.7), angle=1.5)
    K.light('AREA', (0.0, -2.5, 2.6), (0, 0, 0.3), energy=260, size=3.0, color=(0.88, 0.93, 1.0))
    K.light('AREA', (1.8, 1.0, 2.6), (0, 0, 0.3), energy=60, size=1.0, color=(1.0, 0.9, 0.8))
    K.render(out)
