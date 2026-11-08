"""p. 7-8: Nie-nu, nie-nu! Daar gaat de politieauto.
Lage camera op straathoogte, groothoek, scheve horizon; de camera rijdt mee met de auto (achtergrond
bewogen, auto scherp). Daan stuurt, Joep hangt juichend uit de auto."""
import math
import numpy as np
from mathutils import Vector, Matrix, Euler
from lib import core as K, cast, stage, props as P, world as Wd, sets
from lib.daan import Daan
from lib.joep import Joep, joep_mats


def main(out, opts):
    Q = stage.setup(opts, 'spread')
    dm = cast.char_mats()
    jm = joep_mats(dm)
    P.prop_mats()
    wm = Wd.world_mats()
    stage.sky('#4f93df', '#d6ebf6', '#8f9a7a', 1.0)
    stage.sun(205, 38, 4.0)
    stage.clouds('Wolk', [(-14, 32, 9), (6, 40, 12), (22, 30, 8), (-30, 45, 14)], scale=2.2)

    sets.street(None, bakery_x=-6.0, quality=Q, cob=(-9, 7, -3.2, 2.6), y_fac=5.0)
    stage.clouds('Wolk2', [(-40, 18, 12), (-48, 2, 15), (-36, 34, 17)], scale=2.2)

    # auto-rig: rijdt naar links-voor
    hd = np.array([-0.6, -0.8])
    heading = math.atan2(hd[0], -hd[1])
    rig = K.empty('AutoRig', (-0.55, -0.6, 0.0), (0, 0, heading))
    car, wheels = P.police_car('Politieauto', rig, (0, 0, 0), 0.0, wheel_spin=0.0, scale=0.62)
    sl = np.array(car['seat_l'])
    sr = np.array(car['seat_r'])
    wh = np.array(car['wheel_hand'])
    z0 = sl[2] - 0.29 + 0.02
    cam_world = Vector((0.05, -2.45, 0.26))
    d = Daan('Daan', pose=dict(
        root=(0, 0, 0), lean=(0.12, 0.0), head=(-4, -22, 8),
        hand_l=(wh[0] - sl[0] + 0.075, wh[1] - sl[1] + 0.02, wh[2] - z0 + 0.03), palm_l=(-0.4, 0.3, -0.6),
        fdir_l=(0.2, -0.6, 0.6), fingers_l='grip', elbow_l=(0.6, 0.5, -0.4),
        hand_r=(wh[0] - sl[0] - 0.075, wh[1] - sl[1] + 0.02, wh[2] - z0 + 0.03), palm_r=(0.4, 0.3, -0.6),
        fdir_r=(-0.2, -0.6, 0.6), fingers_r='grip', elbow_r=(-0.6, 0.5, -0.4),
        foot_r=(-0.07, -0.26, 0.12), foot_l=(0.07, -0.26, 0.12), knee_r=(0, -1, 0.8), knee_l=(0, -1, 0.8)),
        expr=dict(smile=1.0, mouth='grin', open=0.55, squint=0.25, look_at=(0.05, -2.45, 0.26)), cap=True, mats=dm,
        hair_density=Q['hair'])
    dr = d.build()
    dr.parent = rig
    dr.location = (sl[0], sl[1], z0)
    j = Joep('Joep', pose=dict(
        root=(0, 0, 0), rot=(0, 0, 0), cap=True, head=(-0.25, 0.2, 0.25), cap_tilt=(-0.8, 0.5, 0.4),
        body_tilt=(0.25, -0.1),
        arm_r=[(-0.04, 0.03, 0.03), (-0.06, 0.08, 0.04), (-0.07, 0.13, 0.05)],
        arm_l=[(0.04, -0.02, 0.06), (0.07, -0.03, 0.12), (0.09, -0.02, 0.17)],
        leg_r=[(-0.01, -0.05, -0.0), (-0.02, -0.1, -0.02), (-0.025, -0.13, -0.07)],
        leg_l=[(0.01, -0.05, 0.0), (0.03, -0.1, -0.01), (0.04, -0.12, -0.06)],
        tail=[(0.0, 0.04, -0.01), (0.03, 0.08, 0.01), (0.06, 0.1, 0.0)]),
        mats=jm, fur=Q['fur'])
    jr = j.build()
    jr.parent = rig
    jr.location = (0.1, -0.36, 0.39)
    jr.rotation_euler = (0, 0, 0.75)
    jr.scale = (0.82,) * 3

    # camera rijdt mee
    target = Vector((-0.9, -0.5, 0.75))
    cam = K.camera(tuple(cam_world), tuple(target), lens=17, fstop=5.0, focus=(-0.5, -0.7, 0.75), roll=-0.14,
                   shift=(-0.12, -0.02))
    sc = K.bpy.context.scene if hasattr(K, 'bpy') else None
    import bpy
    sc = bpy.context.scene
    speed = Vector((math.sin(heading) * -1, math.cos(heading), 0))  # lokale -y naar wereld
    fwd = Vector((-math.sin(-heading), -math.cos(-heading), 0))
    move = Vector((hd[0], hd[1], 0)).normalized() * 0.3
    K.keyframe_move(rig, move)
    K.keyframe_move(cam, move)
    for w in wheels:
        K.keyframe_rot(w, 'x', -1.6)
    sc.frame_set(1)
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 1.0
    sc.frame_current = 1

    # licht: koele invul van links, warme zon, lichte rim voor de figuren
    K.light('AREA', (-2.5, -4.5, 2.5), (-0.3, -0.8, 0.6), energy=600, size=4.0, color=(0.85, 0.92, 1.0))
    K.light('AREA', (1.5, 1.8, 2.4), (-0.3, -0.8, 0.7), energy=300, size=1.5, color=(1.0, 0.92, 0.8))
    K.render(out)
