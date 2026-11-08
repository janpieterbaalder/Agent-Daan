"""Gemeenschappelijke scène-instellingen: formaat, kwaliteit, lucht, wolken, zon."""
import math
import bpy
import numpy as np
from . import core as K, mats as M

SPREAD = (5040, 2520)   # 42 x 21 cm + afloop, 300 dpi
PAGE = (2520, 2520)


def setup(opts, kind='spread', transparent=False, exposure=0.0, look='Medium High Contrast', seed=1):
    K.reset(seed)
    q = opts.get('q', 'preview')
    W, H = SPREAD if kind == 'spread' else PAGE
    if opts.get('w'):
        f = int(opts['w']) / W
        W, H = int(W * f), int(H * f)
    elif q == 'preview':
        W, H = W // 4, H // 4
    elif q == 'mid':
        W, H = W // 2, H // 2
    samples = int(opts.get('samples') or (40 if q == 'preview' else 160 if q == 'mid' else 320))
    K.render_setup(W, H, samples=samples, transparent=transparent, exposure=exposure, look=look)
    Q = dict(q=q, hair=0.45 if q == 'preview' else 1.0, fur=0.4 if q == 'preview' else 1.0,
             grass=0.35 if q == 'preview' else 1.0, leaves=0.5 if q == 'preview' else 1.0, W=W, H=H)
    return Q


def sky(zenith='#5b9be0', horizon='#d9ecf5', ground='#8f9a7a', strength=1.0):
    return K.world_sky(zenith, horizon, ground, strength)


def clouds(name, centers, scale=1.0, seed=3):
    """Dikke stripwolken: groepjes bollen, zacht wit, geen schaduw."""
    mat = M.simple('Wolk', '#ffffff', rough=1.0, sss=0.6)
    rng = np.random.default_rng(seed)
    root = K.empty(name)
    for ci, c in enumerate(centers):
        c = np.array(c, dtype=float)
        s = scale * (0.8 + 0.4 * rng.random())
        for k in range(7):
            off = np.array([rng.normal(0, 1.4), rng.normal(0, 0.4), abs(rng.normal(0, 0.5))]) * s
            r = s * (0.9 + 0.8 * rng.random()) * (1.3 if k == 0 else 1.0)
            ob = K.blob(f'{name}{ci}_{k}', (r, r * 0.8, r * 0.75), 2.0, (24, 16), mat=mat, parent=root,
                        loc=tuple(c + off))
            ob.visible_shadow = False
    return root


def sun(az, el, energy=3.5, color=(1.0, 0.93, 0.82), angle=2.5):
    return K.sun_dir(az, el, energy, color, angle)
