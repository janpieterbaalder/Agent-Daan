"""Slotvignet: de grote pet met het kleine petje van Joep erop, een half koekje en kruimels (vrijstaand)."""
import math
import numpy as np
from lib import core as K, cast, stage, props as P, body as B, mats as M


def main(out, opts):
    Q = stage.setup(opts, 'page', transparent=True)
    dm = cast.char_mats()
    K.world_color('#fff8ec', 0.9)
    B.police_cap('Pet', None, dm, loc=(0, 0, 0.0), rot=(0.0, 0.0, 0.5), scale=0.152)
    B.police_cap('Petje', None, dm, loc=(0.02, 0.01, 0.0875), rot=(0.12, -0.1, -0.4), scale=0.05)
    P.cookie('Halve_koek', 'choc', 0.045, None, (0.24, -0.12, 0.0), (0, 0, 0.8), seed=4, bite=0.9)
    rng = np.random.default_rng(3)
    P.crumbs('Kruimels', np.stack([rng.normal(0.18, 0.08, 24), rng.normal(-0.12, 0.06, 24), np.full(24, 0.004)], 1),
             rng.uniform(0.003, 0.007, 24), seed=1)
    vl = K.blob('Schaduwvanger', (2, 2, 0.001), 8, (8, 4), mat=M.simple('sv', '#ffffff'), loc=(0, 0, -0.001))
    vl.is_shadow_catcher = True
    K.camera((0.25, -0.95, 0.62), (0.05, 0.0, 0.05), lens=55, fstop=5.6, focus=(0.05, -0.05, 0.06))
    K.light('AREA', (-0.8, -0.8, 1.2), (0, 0, 0.0), energy=70, size=1.2, color=(1.0, 0.95, 0.88))
    K.light('AREA', (0.9, -0.5, 0.6), (0, 0, 0.0), energy=20, size=1.0, color=(0.88, 0.93, 1.0))
    K.render(out)
