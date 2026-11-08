"""p. 11-12: Kijk eens, kruimels! Wie heeft dat gedaan?
Op stoeptegelhoogte: een spoor kruimels loopt het beeld in naar het park. Joep ligt op zijn buik en snuffelt aan
een kruimel; Daan zit gehurkt met een vergrootglas, zijn oog groot achter de lens."""
import math
import bpy
import numpy as np
from mathutils import Vector
from lib import core as K, cast, stage, sets, props as P, world as Wd
from lib.daan import Daan
from lib.joep import Joep, joep_mats


def main(out, opts):
    Q = stage.setup(opts, 'spread')
    dm = cast.char_mats()
    jm = joep_mats(dm)
    stage.sky('#5b9be0', '#dcedf5', '#8f9a7a', 1.0)
    stage.sun(150, 35, 2.8)
    Wd.sidewalk('Stoep', -3, 3, -1.2, 5.0, z=0.0)
    Wd.curb('Rand', -6, 6, 5.08, z=0.0)
    Wd.ground('Gras', (40, 30), sets.set_mats()['lawn'], None, (0, 20, 0))
    Wd.grass('Gras_p', (-3, 3, 5.2, 9), density=int(1500 * Q['grass']), seed=4)
    for i, (x, y) in enumerate(((-1.6, 8.5), (2.2, 9.5), (0.2, 12.5), (-4.0, 11.0), (4.5, 13.0))):
        Wd.tree(f'Boom{i}', (x, y, 0), height=5.5, crown=1.8, seed=60 + i, density=int(400 * Q['leaves']))
    Wd.bush('Struik', (0.6, 7.0, 0), size=1.0, seed=8, density=int(900 * Q['leaves']))
    fm = Wd.world_mats()['fence']
    for i in range(7):
        K.tube(f'Hek{i}', [(-3 + i, 5.25, 0), (-3 + i, 5.25, 0.8)], [0.025, 0.02], fm, None, ring=8, per=2)
    K.tube('Hekligger', [(-3.2, 5.25, 0.7), (3.2, 5.25, 0.7)], [0.02, 0.02], fm, None, ring=8, per=2)
    # kruimelspoor
    rng = np.random.default_rng(5)
    ys = np.concatenate([np.linspace(-0.45, 0.2, 18), np.linspace(0.2, 6.8, 80)])
    xs = 0.05 + 0.25 * np.sin(ys * 0.7) + rng.normal(0, 0.03, len(ys))
    pts = np.stack([xs, ys, np.full(len(ys), 0.004)], 1)
    sizes = np.clip(0.012 - ys * 0.0012, 0.004, 0.014) * rng.uniform(0.6, 1.3, len(ys))
    P.crumbs('Kruimelspoor', pts, sizes, seed=3)
    P.crumbs('Grote_kruimel', np.array([[0.13, -0.32, 0.01]]), np.array([0.022]), seed=9)
    cam = Vector((0.2, -0.78, 0.055))
    j = Joep('Joep', pose=dict(
        root=(0, 0, 0), head=(-1.15, 0.2, 0.1),
        arm_r=[(-0.02, -0.04, 0.02), (-0.03, -0.08, 0.035), (-0.03, -0.12, 0.04)],
        arm_l=[(0.02, -0.04, 0.02), (0.035, -0.08, 0.035), (0.04, -0.12, 0.03)],
        leg_r=[(-0.01, 0.0, -0.06), (-0.02, 0.01, -0.11), (-0.03, 0.04, -0.14)],
        leg_l=[(0.01, 0.0, -0.06), (0.025, 0.01, -0.11), (0.04, 0.05, -0.14)]),
        mats=jm, fur=Q['fur'])
    jr = j.build()
    jr.rotation_euler = (math.pi / 2 - 0.08, 0, 0.35)
    jr.location = (0.3, 0.02, 0.04)
    # Daan ligt op zijn buik (root draait 90 graden om x): lokaal z -> wereld -y, lokaal y -> wereld z
    R = (-0.38, 0.95, 0.115)
    to_l = lambda X, Y, Z: (X - R[0], Z - R[2], -(Y - R[1]))
    lens_w = (-0.36, 0.06, 0.2)
    d = Daan('Daan', pose=dict(
        root=(0, 0, 0), head=(-72, 6, 4), lean=(0.0, 0.0),
        foot_r=(-0.07, 0.24, 0.16), foot_l=(0.07, 0.2, 0.2), knee_r=(0, -1, 0), knee_l=(0, -1, 0),
        hand_r=to_l(-0.43, 0.1, 0.07), palm_r=(1, 0, 0), fdir_r=(0.1, 1, 0.2), fingers_r='grip', elbow_r=(-1, -0.5, 0),
        hand_l=to_l(-0.18, 0.18, 0.05), palm_l=(0, -1, 0), fdir_l=(-0.2, 0.2, 1), fingers_l='relaxed', elbow_l=(1, -0.5, 0)),
        expr=dict(smile=0.8, brow_up=0.9, look_at=to_l(*tuple(cam))), cap=True, mats=dm, hair_density=Q['hair'])
    dr = d.build()
    dr.rotation_euler = (math.pi / 2, 0, 0)
    dr.location = R
    bpy.context.view_layer.update()
    eye = d.head.eyes[0].matrix_world.translation
    lens_c = eye + (cam - eye).normalized() * 0.075
    mg = P.magnifier('Vergrootglas', None, tuple(lens_c), (0, 0, 0), r=0.06)
    dirv = (cam - lens_c).normalized()
    mg.rotation_euler = Vector((0, -1, 0)).rotation_difference(dirv).to_euler()
    K.camera(tuple(cam), (-0.08, 0.6, 0.16), lens=20, fstop=2.0, focus=(0.18, -0.25, 0.04), roll=0.04)
    K.light('AREA', (0.6, -1.5, 0.8), (0, 0, 0.2), energy=150, size=2.0, color=(0.9, 0.95, 1.0))
    K.render(out)
