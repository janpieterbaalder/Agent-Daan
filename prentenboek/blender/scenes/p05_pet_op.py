"""p. 5: Daan zet zijn politiepet op. Close-up: de pet net boven zijn kuif, ogen omhoog naar de pet."""
import math
from lib import core as K, cast, stage, sets, body as B
from lib.daan import Daan


def main(out, opts):
    Q = stage.setup(opts, 'page')
    dm = cast.char_mats()
    K.world_color('#fff3e0', 0.15)
    sets.bedroom(night=False, window_x=-0.6, rug=False)
    cam = (0.22, -0.95, 0.68)
    d = Daan('Daan', pose=dict(
        root=(0.0, 0.0, 0.0), yaw=8, head=(-12, 4, -4), lean=(-0.04, 0.0),
        hand_r=(-0.165, -0.07, 0.99), palm_r=(1, 0.1, -0.2), fdir_r=(0.2, 0, 1), fingers_r='grip',
        elbow_r=(-1, 0.1, -0.2),
        hand_l=(0.165, -0.08, 0.99), palm_l=(-1, 0.1, -0.2), fdir_l=(-0.2, 0, 1), fingers_l='grip',
        elbow_l=(1, 0.1, -0.2)),
        expr=dict(smile=1.0, squint=0.2, look=(0.05, -1.0, 0.42), brow_up=0.7), cap=False, mats=dm,
        hair_density=Q['hair'])
    d.build()
    B.police_cap('Pet_in_handen', d.head.root, dm, loc=(0, -0.06, 1.32), rot=(0.25, 0.08, 0.06), scale=1.0)
    K.camera(cam, (0.0, -0.01, 0.86), lens=50, fstop=2.2, focus=(0.0, -0.12, 0.82))
    stage.sun(120, 30, 5.0, color=(1.0, 0.88, 0.7), angle=1.5)
    K.light('AREA', (0.9, -1.4, 1.2), (0, 0, 0.8), energy=130, size=1.6, color=(1.0, 0.95, 0.88))
    K.light('AREA', (-1.2, -0.6, 0.9), (0, 0, 0.8), energy=45, size=1.5, color=(0.85, 0.92, 1.0))
    K.light('AREA', (-0.4, 1.0, 1.4), (0, 0, 0.85), energy=90, size=0.8, color=(1.0, 0.9, 0.75))
    K.render(out)
