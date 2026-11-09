"""Proefplaat: Daan (uniform, pet) houdt Joep (petje) vast en zwaait."""
import math
from lib import core as K, cast, mats as MM
from lib.daan import Daan
from lib.joep import Joep, joep_mats


def main(out, opts):
    K.reset()
    w = int(opts.get('w') or 1600)
    K.render_setup(w, int(w * 1.25), samples=int(opts.get('samples') or 128), look='Medium High Contrast')
    K.world_color('#9a8f86', 0.2)
    dm = cast.char_mats()
    jm = joep_mats(dm)
    d = Daan('Daan', pose=dict(
        yaw=18, lean=(0.04, -0.02), head=(-4, -14, 4),
        hand_l=(0.0, -0.16, 0.36), elbow_l=(0.5, 0.2, -0.6), palm_l=(0, 0, 1), fdir_l=(-0.9, -0.2, 0.1),
        fingers_l='hold',
        hand_r=(-0.23, -0.05, 0.6), elbow_r=(-0.6, 0.3, -0.6), palm_r=(0, -1, 0), fdir_r=(-0.25, -0.1, 1),
        fingers_r='spread',
        foot_r=(-0.07, 0.01, 0.058), foot_l=(0.07, -0.02, 0.058), toe_r=(-0.25, -1, 0), toe_l=(0.2, -1, 0)),
        expr=dict(smile=1.0, squint=0.18, look_at=(-0.55, -2.2, 0.6)), cap=True, mats=dm)
    d.build()
    j = Joep('Joep', pose=dict(
        root=(0.03, -0.185, 0.24), rot=(0.05, 0, 0.3), cap=True, head=(-0.12, -0.3, 0.12),
        leg_r=[(-0.01, -0.03, -0.02), (-0.015, -0.08, -0.04), (-0.015, -0.1, -0.1)],
        leg_l=[(0.01, -0.03, -0.02), (0.02, -0.08, -0.05), (0.025, -0.09, -0.12)],
        arm_r=[(-0.03, -0.02, -0.02), (-0.06, -0.04, 0.0), (-0.08, -0.06, 0.03)],
        arm_l=[(0.02, -0.01, -0.04), (0.035, -0.02, -0.08), (0.04, -0.03, -0.11)]),
        mats=jm)
    jr = j.build()
    jr.parent = d.root
    # studio: holle achtergrond in dezelfde warme grijstint
    import numpy as np
    bg = MM.simple('Studio', '#a69a90', rough=0.9)
    def cyc(U, V):
        x = (U - 0.5) * 8
        y = V * 6 - 1
        z = np.where(y > 2.2, (y - 2.2) ** 2 * 0.8, 0)
        y2 = np.where(y > 2.2, 2.2 + (y - 2.2) * 0.3, y)
        return np.stack([x, y2, z], 1)
    K.grid_mesh('Studio', 20, 60, cyc, bg)
    K.camera((-0.55, -2.2, 0.6), (0.02, 0.0, 0.5), lens=70, fstop=2.8, focus=(0.0, -0.15, 0.68))
    K.light('AREA', (-1.6, -1.8, 1.9), (0, 0, 0.55), energy=170, size=2.2, color=(1.0, 0.93, 0.85))
    K.light('AREA', (1.8, -1.6, 0.9), (0, 0, 0.5), energy=40, size=2.5, color=(0.85, 0.92, 1.0))
    K.light('AREA', (1.2, 1.6, 1.6), (0, 0, 0.7), energy=170, size=1.0, color=(1.0, 0.95, 0.9))
    K.light('AREA', (-1.0, 1.4, 1.2), (0, 0, 0.6), energy=90, size=1.0, color=(0.9, 0.95, 1.0))
    K.render(out)
