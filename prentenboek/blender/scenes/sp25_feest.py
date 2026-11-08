"""p. 25-26: Goed gedaan, agent Daan! Goed gedaan, agent Joep!
Feest voor de bakkerij: Daan en Joep staan op een kistje met een gouden medaille, confetti dwarrelt; de bakker
klapt en de boeven, nu met een koksmuts op, juichen mee."""
import math
import numpy as np
from lib import core as K, cast, stage, sets, props as P, world as Wd
from lib.daan import Daan
from lib.joep import Joep, joep_mats
from lib.people import Person, people_mats


def main(out, opts):
    Q = stage.setup(opts, 'spread')
    dm = cast.char_mats()
    jm = joep_mats(dm)
    pm = people_mats(dm)
    pr = P.prop_mats()
    wm = Wd.world_mats()
    stage.sky('#4f93df', '#d6ebf6', '#8f9a7a', 1.0)
    stage.sun(250, 40, 4.5)
    stage.clouds('Wolk', [(-8, 20, 10), (10, 22, 12)], scale=2.0)
    sets.street(None, bakery_x=0.0, quality=Q, cob=(-6, 6, -3.2, 2.6), y_fac=5.0)
    # kistje als podium
    sets._box('Kistje', (0.7, 0.5, 0.32), (0.0, 3.55, 0.16), wm['bed_wood'], None, n=6)
    cam = (0.35, 1.35, 0.42)
    d = Daan('Daan', pose=dict(
        root=(0.0, 3.55, 0.32), yaw=-8, head=(-14, 4, -4), lean=(-0.08, 0),
        hand_r=(-0.3, -0.02, 0.98), palm_r=(0, -1, 0), fdir_r=(-0.3, 0, 1), fingers_r='fist', elbow_r=(-1, 0.3, -0.5),
        hand_l=(0.3, -0.02, 0.98), palm_l=(0, -1, 0), fdir_l=(0.3, 0, 1), fingers_l='fist', elbow_l=(1, 0.3, -0.5)),
        expr=dict(smile=1.0, mouth='grin', open=0.7, squint=0.35, look_at=cam), cap=True, mats=dm,
        hair_density=Q['hair'])
    d.build()
    P.medal('Medaille_daan', d.root, (0.0, -0.13, 0.45), (0.08, 0, 0), r=0.032, ribbon_len=0.1)
    j = Joep('Joep', pose=dict(
        root=(0.24, -0.02, 0.0), rot=(0, 0, -0.2), cap=True, head=(-0.3, 0.2, 0.15), scale=0.9,
        arm_r=[(-0.04, -0.01, 0.05), (-0.07, -0.02, 0.1), (-0.09, -0.02, 0.15)],
        arm_l=[(0.04, -0.01, 0.05), (0.07, -0.02, 0.1), (0.09, -0.02, 0.15)]),
        mats=jm, fur=Q['fur'])
    jr = j.build()
    jr.parent = d.root
    P.medal('Medaille_joep', j.body, (0.0, -0.045, 0.03), (0.1, 0, 0), r=0.018, ribbon_len=0.06)
    Person('Bakker', 'bakker', pose=dict(
        root=(1.15, 3.25, 0.12), yaw=-30, head=(-6, -10, 0),
        hand_r=(-0.02, -0.4, 1.12), palm_r=(1, 0, 0), fdir_r=(0.2, 0, 1), fingers_r='flat',
        hand_l=(0.05, -0.4, 1.12), palm_l=(-1, 0, 0), fdir_l=(-0.2, 0, 1), fingers_l='flat'),
        expr=dict(smile=1.0, mouth='grin', open=0.5, squint=0.4, look_at=cam), mats=pm).build()
    Person('Lange', 'lang', pose=dict(
        root=(-1.2, 3.35, 0.12), yaw=25, head=(-8, 10, 0),
        hand_r=(-0.35, -0.05, 1.75), palm_r=(0, -1, 0), fdir_r=(-0.2, 0, 1), fingers_r='spread',
        hand_l=(0.35, -0.05, 1.75), palm_l=(0, -1, 0), fdir_l=(0.2, 0, 1), fingers_l='spread'),
        expr=dict(smile=1.0, mouth='grin', open=0.6, squint=0.3, look_at=cam), mats=pm, mask_up=0.38,
        baker_hat=True).build()
    Person('Dikkie', 'dik', pose=dict(
        root=(-1.95, 2.95, 0.12), yaw=35, head=(-8, 8, 0),
        hand_r=(-0.3, -0.1, 1.25), palm_r=(0, -1, 0), fdir_r=(-0.2, 0, 1), fingers_r='spread',
        hand_l=(0.3, -0.25, 0.9), palm_l=(0, -1, 0), fingers_l='spread'),
        expr=dict(smile=1.0, mouth='grin', open=0.6, squint=0.5, look_at=cam), mats=pm, mask_up=0.38,
        baker_hat=True).build()
    P.confetti('Confetti', int(900 * (0.5 if Q['q'] == 'preview' else 1.0)), ((-3, 1.8, 0.3), (3, 5.0, 3.2)), size=0.014)
    K.camera(cam, (-0.2, 3.6, 1.05), lens=22, fstop=4.0, focus=(0.0, 3.4, 0.95))
    K.light('AREA', (1.5, 0.5, 1.8), (0, 3.5, 0.9), energy=380, size=3.0, color=(1.0, 0.95, 0.9))
    K.render(out)
