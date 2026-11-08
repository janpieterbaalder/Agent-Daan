"""p. 19-20: Stop! Politie! roept Daan. Oe-oe-aa-aa! roept Joep.
Vanuit de boeven gezien, laag: Daan stapt door de struik met zijn hand omhoog; Joep springt in de lucht,
zijn petje vliegt eraf; blaadjes dwarrelen."""
import math
import numpy as np
from lib import core as K, cast, stage, sets, props as P, world as Wd, body as B
from lib.daan import Daan
from lib.joep import Joep, joep_mats


def main(out, opts):
    Q = stage.setup(opts, 'spread')
    dm = cast.char_mats()
    jm = joep_mats(dm)
    stage.sky('#4d8fdb', '#cfe6f3', '#8f9a7a', 1.1)
    stage.sun(120, 50, 4.2)
    sets.park(None, Q, grass_region=(-2.0, 2.0, -1.2, 1.8), trees=[(-2.8, 5.0, 6, 2.1), (3.5, 6.0, 5.5, 1.8)],
              bushes=[(-1.15, 0.95, 1.05), (1.25, 1.05, 1.0)], path=False, flowers_n=20, houses=True,
              grass_density=2400)
    cam = (0.05, -1.05, 0.22)
    d = Daan('Daan', pose=dict(
        root=(-0.12, 0.42, 0.0), yaw=6, lean=(-0.04, 0.03), head=(-10, -4, -6),
        hand_r=(-0.17, -0.22, 0.66), palm_r=(0, -1, 0), fdir_r=(-0.1, 0, 1), fingers_r='flat', elbow_r=(-1, 0.4, -0.5),
        hand_l=(0.145, 0.01, 0.33), palm_l=(-1, 0, 0), fdir_l=(-0.2, 0.3, -1), fingers_l='fist', elbow_l=(1, 0.35, 0.1),
        foot_r=(-0.08, 0.05, 0.058), foot_l=(0.09, -0.12, 0.09), toe_r=(-0.2, -1, 0), toe_l=(0.1, -1, 0)),
        expr=dict(mouth='shout', open=0.95, smile=0.0, brow_tilt=-0.8, lids=1.0, look_at=cam), cap=True, mats=dm,
        hair_density=Q['hair'])
    d.build()
    j = Joep('Joep', pose=dict(
        root=(0, 0, 0), cap=False, head=(-0.3, -0.3, 0.2), body_tilt=(-0.2, 0.25),
        arm_r=[(-0.05, -0.01, 0.04), (-0.09, -0.02, 0.09), (-0.12, -0.02, 0.14)],
        arm_l=[(0.05, -0.01, 0.04), (0.09, -0.02, 0.09), (0.12, -0.02, 0.14)],
        leg_r=[(-0.03, -0.01, -0.05), (-0.07, -0.02, -0.09), (-0.11, -0.03, -0.12)],
        leg_l=[(0.03, -0.01, -0.05), (0.07, -0.03, -0.09), (0.11, -0.05, -0.12)],
        tail=[(0.02, 0.04, -0.02), (0.06, 0.07, 0.0), (0.1, 0.07, 0.04)]),
        mats=jm, fur=Q['fur'])
    jr = j.build()
    jr.location = (0.52, 0.32, 0.5)
    jr.rotation_euler = (0.15, 0.25, -0.35)
    jr.scale = (0.9,) * 3
    B.police_cap('Vliegend_petje', None, dm, loc=(0.6, 0.3, 0.98), rot=(0.8, 0.6, 0.3), scale=0.034)
    # dwarrelende blaadjes en de zak van de boeven op de voorgrond
    rng = np.random.default_rng(4)
    n = int(140 * Q['leaves']) + 30
    c = np.stack([rng.uniform(-1.2, 1.4, n), rng.uniform(-0.2, 1.2, n), rng.uniform(0.1, 1.4, n)], 1)
    nrm = rng.normal(size=(n, 3))
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    V, F, C = Wd._leaf_mesh(n, c, nrm, 0.06, rng, ['#4f9233', '#6db544', '#3f7d2b', '#8cc14f'])
    K.mesh_obj('Dwarrelblad', V, F, Wd.world_mats()['leaf'], None, attrs={'col': ('POINT', C)})
    P.sack('Zak_voor', None, (-0.62, -0.55, 0), (0.3, 0, 0.9), size=0.38, open_=True, cookies_in=5)
    P.cookie('Koek_voor', 'roze', 0.045, None, (0.42, -0.7, 0.015), (0.1, 0.0, 0.4), seed=2)
    K.camera(cam, (0.15, 0.5, 0.78), lens=18, fstop=3.5, focus=(-0.1, 0.35, 0.72))
    K.light('AREA', (0.3, -1.6, 0.6), (0, 0.4, 0.7), energy=220, size=2.5, color=(0.95, 0.97, 1.0))
    K.light('AREA', (-1.0, 2.0, 2.2), (0, 0.4, 0.8), energy=300, size=1.0, color=(1.0, 0.9, 0.75))
    K.render(out)
