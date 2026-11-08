"""Omslag (doorlopend, links achterkant en rechts voorkant).
Voorkant: Daan als held met de handen in de zij, Joep salueert op zijn schouder, de politieauto met zwaailicht
erachter. Achterkant: verderop in de straat sluipen de boeven weg met de zak koekjes."""
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
    stage.sky('#3f86d8', '#d2e8f4', '#8f9a7a', 1.05)
    stage.sun(235, 30, 4.6, color=(1.0, 0.88, 0.72))
    stage.clouds('Wolk', [(-14, 26, 11), (-2, 30, 14), (12, 24, 10), (24, 34, 15)], scale=2.4)
    sets.street(None, bakery_x=-1.5, quality=Q, cob=(-7, 6, -3.2, 2.6), y_fac=5.0)
    cam = (1.0, -2.6, 0.32)
    # held rechts op de voorkant
    d = Daan('Daan', pose=dict(
        root=(1.31, -1.03, 0.0), yaw=-12, head=(-8, 8, 4), lean=(-0.06, 0.0),
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
    jr = j.build()
    jr.parent = d.root
    car, wheels = P.police_car('Politieauto', None, (2.25, 0.05, 0.0), math.radians(-55), scale=0.62)
    # boeven sluipen weg (achterkant)
    Person('Lange', 'lang', pose=dict(
        root=(-1.65, 1.64, 0), yaw=-75, lean=(0.25, 0), head=(-4, 40, 0),
        foot_r=(-0.12, -0.25, 0.14), foot_l=(0.12, 0.2, 0.075), knee_r=(0, -1, 0.3), knee_l=(0, -1, 0.3),
        hand_r=(-0.25, 0.1, 1.45), palm_r=(0, 1, 0), fingers_r='grip',
        hand_l=(0.3, -0.25, 1.0), fingers_l='flat', palm_l=(0, 0, -1)),
        expr=dict(smile=0.6, lids=0.75, look_at=cam), mats=pm).build()
    P.sack('Zak', None, (-1.7, 2.0, 1.15), (0.3, 0.5, 0.2), size=0.42, open_=False)
    Person('Dikkie', 'dik', pose=dict(
        root=(-0.95, 1.25, 0), yaw=-80, lean=(0.2, 0), head=(-4, 50, 0),
        foot_r=(-0.15, -0.2, 0.12), foot_l=(0.15, 0.15, 0.075),
        hand_r=(-0.25, -0.35, 0.95), fingers_r='point', palm_r=(0, 0, -1), fdir_r=(0, 0, 1),
        hand_l=(0.3, -0.2, 0.8), fingers_l='flat'),
        expr=dict(smile=0.8, lids=0.75, look_at=cam), mats=pm).build()
    K.camera(cam, (0.48, 0.35, 1.0), lens=22, fstop=5.0, focus=(1.31, -1.03, 0.7))
    K.light('AREA', (3.0, -2.5, 1.5), (1.7, -1.0, 0.7), energy=320, size=2.5, color=(0.9, 0.95, 1.0))
    K.light('AREA', (0.5, 1.0, 2.0), (1.7, -1.0, 0.8), energy=260, size=1.0, color=(1.0, 0.85, 0.65))
    K.render(out)
