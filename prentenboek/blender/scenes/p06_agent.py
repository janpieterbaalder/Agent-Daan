"""p. 6: Joep krijgt ook een pet. Nu zijn ze agent! Lage heldenhoek buiten bij de voordeur: Daan met de
handen in de zij, Joep salueert op zijn schouder; de politieauto staat klaar, tegenlicht van de zon."""
import math
from lib import core as K, cast, stage, sets, props as P, world as Wd
from lib.daan import Daan
from lib.joep import Joep, joep_mats


def main(out, opts):
    Q = stage.setup(opts, 'page')
    dm = cast.char_mats()
    jm = joep_mats(dm)
    stage.sky('#4f93df', '#d6ebf6', '#8f9a7a', 1.0)
    stage.sun(60, 42, 4.5)
    stage.clouds('Wolk', [(-6, 14, 9), (5, 18, 12), (-14, 22, 13)], scale=1.8)
    Wd.sidewalk('Stoep', -4, 4, -2, 1.6, z=0.0)
    Wd.gable_house('Huis', 0.2, 4.4, 9.5, None, brick='brick', gable='trap', door='door', y=1.65, door_side=0.0)
    car, wheels = P.police_car('Politieauto', None, (-1.35, 0.55, 0.0), math.radians(-35), scale=0.62)
    Wd.tree('Boom', (2.6, 1.0, 0), height=5, crown=1.6, seed=3, density=int(500 * Q['leaves']))
    cam = (0.2, -0.7, 0.12)
    d = Daan('Daan', pose=dict(
        root=(0, 0, 0), yaw=-8, head=(-10, 6, 4), lean=(-0.06, 0.0),
        hand_r=(-0.145, 0.01, 0.33), palm_r=(1, 0, 0), fdir_r=(0.2, 0.3, -1), fingers_r='fist', elbow_r=(-1, 0.35, 0.1),
        hand_l=(0.0, -0.16, 0.36), palm_l=(0, 0, 1), fdir_l=(-0.9, -0.2, 0.1), fingers_l='hold', elbow_l=(0.5, 0.2, -0.6),
        foot_r=(-0.1, 0.0, 0.058), foot_l=(0.1, 0.0, 0.058), toe_r=(-0.3, -1, 0), toe_l=(0.3, -1, 0)),
        expr=dict(smile=1.0, squint=0.3, look_at=cam), cap=True, mats=dm, hair_density=Q['hair'])
    d.build()
    j = Joep('Joep', pose=dict(
        root=(0.03, -0.185, 0.24), rot=(0.05, 0, 0.3), cap=True, head=(-0.15, 0.25, 0.1), cap_tilt=(-0.2, 0.15, 0.05),
        arm_r=[(-0.035, -0.035, 0.04), (-0.035, -0.07, 0.085), (-0.004, -0.07, 0.118)],
        arm_l=[(0.03, -0.02, -0.04), (0.05, -0.04, -0.08), (0.06, -0.05, -0.12)],
        leg_r=[(-0.01, -0.03, -0.02), (-0.015, -0.08, -0.04), (-0.015, -0.1, -0.1)],
        leg_l=[(0.005, -0.04, -0.02), (0.015, -0.06, -0.08), (0.02, -0.06, -0.14)]),
        mats=jm, fur=Q['fur'])
    j.build()
    K.camera(cam, (-0.03, 0.0, 0.72), lens=17, fstop=4.0, focus=(-0.05, -0.08, 0.7))
    K.light('AREA', (0.8, -2.0, 1.2), (0, 0, 0.7), energy=200, size=2.5, color=(0.9, 0.95, 1.0))
    K.light('AREA', (-1.2, 1.5, 1.8), (0, 0, 0.8), energy=220, size=1.0, color=(1.0, 0.9, 0.75))
    K.render(out)
