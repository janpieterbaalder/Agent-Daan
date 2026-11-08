"""p. 22: 'Sorry,' zeggen ze. 'We hadden zo'n honger.' Van bovenaf, zoals Daan het ziet: de boeven zitten sip
naast elkaar, maskers omhoog geschoven; de lange houdt de zak omhoog, de dikke wrijft over zijn buik."""
import math
import numpy as np
from lib import core as K, cast, stage, sets, props as P
from lib.people import Person, people_mats


def main(out, opts):
    Q = stage.setup(opts, 'page')
    dm = cast.char_mats()
    pm = people_mats(dm)
    stage.sky('#4d8fdb', '#cfe6f3', '#8f9a7a', 1.0)
    stage.sun(200, 50, 3.8)
    sets.park(None, Q, grass_region=(-1.4, 1.4, -1.0, 1.2), trees=None, bushes=[(-0.9, 1.4, 0.9), (1.1, 1.5, 0.8)],
              path=False, flowers_n=18, houses=False, grass_density=2600)
    cam = (0.15, -1.7, 1.35)
    L = Person('Lange', 'lang', pose=dict(
        root=(-0.38, 0.12, 0), yaw=8, hip=(0, 0, 0.13), lean=(0.18, 0.04), head=(-14, 6, 10),
        foot_r=(-0.14, -0.5, 0.075), foot_l=(0.12, -0.52, 0.075), knee_r=(-0.2, -0.3, 1), knee_l=(0.2, -0.3, 1),
        hand_r=(0.02, -0.5, 0.42), palm_r=(1, 0, 0), fdir_r=(0.2, -0.6, 0.3), fingers_r='grip',
        hand_l=(0.2, -0.48, 0.42), palm_l=(-1, 0, 0), fdir_l=(-0.2, -0.6, 0.3), fingers_l='grip'),
        expr=dict(smile=-0.7, brow_tilt=1.0, lids=0.8, look_at=cam), mats=pm, mask_up=0.38, hat=True)
    L.build()
    Dk = Person('Dikkie', 'dik', pose=dict(
        root=(0.42, 0.05, 0), yaw=-10, hip=(0, 0, 0.16), lean=(0.1, -0.05), head=(-12, -8, -10),
        foot_r=(-0.2, -0.42, 0.075), foot_l=(0.2, -0.44, 0.075), knee_r=(-0.3, -0.3, 1), knee_l=(0.3, -0.3, 1),
        hand_r=(-0.05, -0.3, 0.55), palm_r=(0, 1, 0), fdir_r=(1, 0, 0.1), fingers_r='flat',
        hand_l=(0.25, -0.2, 0.4), fingers_l='relaxed'),
        expr=dict(smile=-0.6, brow_tilt=1.0, lids=0.85, look_at=cam), mats=pm, mask_up=0.38)
    Dk.build()
    P.sack('Zak', L.root, (0.1, -0.62, 0.18), (0.35, 0, 0), size=0.36, open_=True, cookies_in=6)
    K.camera(cam, (0.0, 0.05, 0.55), lens=34, fstop=4.0, focus=(0.0, 0.05, 0.75))
    K.light('AREA', (0.2, -2.5, 2.2), (0, 0, 0.6), energy=300, size=3.0, color=(0.97, 0.97, 1.0))
    K.light('AREA', (1.6, 1.6, 2.0), (0, 0, 0.7), energy=200, size=1.0, color=(1.0, 0.9, 0.75))
    K.render(out)
