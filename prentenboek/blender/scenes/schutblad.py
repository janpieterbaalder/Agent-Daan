"""Schutblad: patroon van koekjes, gouden sterren, petjes en vergrootglazen op donkerblauwe stof (recht van boven)."""
import math
import numpy as np
import bpy
from lib import core as K, cast, stage, props as P, body as B, mats as M


def main(out, opts):
    Q = stage.setup(opts, 'page')
    dm = cast.char_mats()
    pr = P.prop_mats()
    K.world_color('#20284d', 0.4)
    stof = M.fabric('Ondergrond', '#1b2550', rough=0.85, sheen=0.5, weave=600, strength=0.3)
    K.blob('Stof', (1.2, 1.2, 0.01), 8, (8, 4), mat=stof, loc=(0, 0, -0.01))
    rng = np.random.default_rng(21)
    # verdeling op een verschoven raster met jitter
    pts = []
    for i in range(7):
        for k in range(7):
            x = -0.84 + i * 0.28 + (0.14 if k % 2 else 0) + rng.normal(0, 0.025)
            y = -0.84 + k * 0.28 + rng.normal(0, 0.025)
            pts.append((x, y))
    kinds = ['choc', 'roze', 'ster', 'ster_goud', 'pet', 'choc', 'roze', 'loep']
    for n, (x, y) in enumerate(pts):
        kind = kinds[(n * 5 + n // 7) % len(kinds)]
        rot = rng.random() * 6.28
        if kind in ('choc', 'roze', 'ster'):
            P.cookie(f'K{n}', kind, 0.07, None, (x, y, 0.0), (0, 0, rot), seed=n, bite=0.5 if n % 9 == 0 else 0.0)
        elif kind == 'ster_goud':
            K.poly_obj(f'S{n}', K.round_star_pts(0.06, 0.5), depth=0.006, bevel=0.006, mat=pr['gold'],
                       loc=(x, y, 0.008), rot=(0, 0, rot))
        elif kind == 'pet':
            B.police_cap(f'P{n}', None, dm, loc=(x, y, 0.0), rot=(0.5, 0, rot), scale=0.075)
        else:
            mg = P.magnifier(f'L{n}', None, (x, y, 0.016), (math.pi / 2, 0, rot), r=0.055)
    cd = bpy.data.cameras.new('Cam')
    cd.type = 'ORTHO'
    cd.ortho_scale = 1.55
    cam = bpy.data.objects.new('Cam', cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, 0, 3)
    bpy.context.scene.camera = cam
    K.light('AREA', (-1.5, -1.0, 2.5), (0, 0, 0), energy=500, size=2.0, color=(1.0, 0.95, 0.88))
    K.light('AREA', (1.5, 1.2, 2.0), (0, 0, 0), energy=150, size=2.0, color=(0.85, 0.9, 1.0))
    K.render(out)
