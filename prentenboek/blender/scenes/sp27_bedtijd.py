"""p. 27-28: Nu is het bedtijd. Daan slaapt met Joep in zijn arm; maanlicht door het raam, nachtlampje,
de politiepet aan de bedknop."""
import math
from lib import core as K, cast, stage, sets, body as B, world as Wd, mats as M
from lib.daan import Daan
from lib.joep import Joep, joep_mats


def main(out, opts):
    Q = stage.setup(opts, 'spread', exposure=-0.2)
    dm = cast.char_mats()
    jm = joep_mats(dm)
    wm = Wd.world_mats()
    K.world_color('#0d1430', 0.25)
    sets.bedroom(night=True, window_x=-0.2, rug=True, sleeper=True)
    bx, by = -1.35, 0.85
    # Daan op zijn rug onder het dekbed, hoofd op het kussen, iets naar de camera gedraaid
    d = Daan('Daan', pose=dict(
        root=(0, 0, 0), head=(-4, 0, 0), lean=(0.0, 0.0),
        hand_l=(0.2, -0.16, 0.46), palm_l=(-0.6, 0.6, 0), fdir_l=(0.1, -0.2, 1), fingers_l='hold',
        elbow_l=(0.8, 0.2, -0.5),
        hand_r=(0.1, -0.19, 0.4), palm_r=(0.6, 0.6, 0), fdir_r=(1, -0.1, 0.4), fingers_r='hold',
        elbow_r=(-0.6, 0.2, -0.4)),
        expr=dict(smile=0.7, lids=0.0, squint=0.0), cap=False, outfit='pajama', mats=dm, hair_density=Q['hair'])
    dr = d.build()
    dr.location = (bx + 0.05, by - 0.05, 0.775)
    dr.rotation_mode = 'XYZ'
    dr.rotation_euler = (-math.pi / 2 + 0.02, 0.5, 0.0)
    j = Joep('Joep', pose=dict(
        root=(0, 0, 0), head=(0.1, -0.5, 0.3),
        arm_r=[(-0.03, -0.03, 0.01), (-0.05, -0.07, 0.02), (-0.06, -0.1, 0.05)],
        arm_l=[(0.03, -0.02, -0.04), (0.05, -0.04, -0.08), (0.07, -0.05, -0.12)]),
        mats=jm, fur=Q['fur'])
    jr = j.build()
    import bpy
    bpy.context.view_layer.update()
    hl = bpy.data.objects['Daan_handl_palm'].matrix_world.translation
    jr.rotation_mode = 'XYZ'
    jr.rotation_euler = (-math.pi / 2, 0.75, 0.15)
    jr.location = (hl.x + 0.05, hl.y - 0.36, hl.z - 0.01)
    # pet aan de bedknop
    knob = (bx + 0.48, by - 0.92, 0.47)
    B.police_cap('Pet_bedknop', None, dm, loc=(knob[0], knob[1], knob[2] - 0.035), rot=(0.25, 0.15, 0.6),
                 scale=0.152)
    # nachtkastje met maanlampje
    sets._box('Nachtkastje', (0.4, 0.38, 0.5), (bx + 0.85, by + 0.75, 0.25), wm['bed_wood'], None, n=5)
    lamp = M.emission('Maanlampje', '#ffcf7a', 14.0)
    K.blob('Lampje', (0.05, 0.04, 0.05), 2, (24, 16), mat=lamp, loc=(bx + 0.85, by + 0.85, 0.56))
    K.light('POINT', (bx + 0.85, by + 0.72, 0.64), energy=9, color=(1.0, 0.72, 0.4), size=0.08)
    # maanlicht door het raam
    K.light('AREA', (-0.2, 3.0, 1.8), (bx, by, 0.6), energy=260, size=1.2, color=(0.55, 0.68, 1.0))
    K.light('AREA', (1.5, -1.5, 2.0), (bx, by, 0.6), energy=18, size=3.0, color=(0.45, 0.55, 0.95))
    cam = (bx + 0.85, by - 0.25, 0.98)
    K.camera(cam, (bx + 0.4, by + 1.0, 0.85), lens=30, fstop=2.2, focus=(bx + 0.1, by + 0.62, 0.8),
             shift=(-0.05, 0.02))
    K.render(out)
