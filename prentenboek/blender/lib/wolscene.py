"""Gedeelde opzet voor de viltanimatie-platen (ware grootte: Daan ca. 12 cm)."""
import math
import numpy as np
from . import core as K, stage, wol as W
from .wolpop import Daan, Joep, Mens

GROUND_Z = 0.0045     # bovenkant van de keitjes


def setup(opts, kind='spread', night=False, inside=False, transparent=False):
    Q = stage.setup(opts, kind, transparent=transparent, look='Medium Contrast')
    if night:
        W.studio(key=(-0.35, -0.4, 0.45), energy=3.0, size=0.5, warm=(0.62, 0.7, 1.0), fill_energy=0.8,
                 rim_energy=1.5, world='#1c2450', world_strength=0.12)
    elif inside:
        W.studio(key=(-0.3, -0.42, 0.42), energy=15.0, size=0.5, fill_energy=4.0, rim_energy=5.0,
                 world='#efe6da', world_strength=0.45)
    else:
        W.studio(key=(-0.32, -0.42, 0.48), energy=16.0, size=0.55, fill_energy=4.0, rim_energy=7.0,
                 world='#e8e2da', world_strength=0.45)
    return Q


def cam(loc, target, lens=42, fstop=4.0, focus=None):
    return W.camera(loc, target, lens=lens, fstop=fstop, focus=focus)


def in_hand(pop, key, builder, offset=0.003):
    Wp, d = pop.hands[key]
    return builder(pop.root, tuple(np.asarray(Wp) + np.asarray(d) * offset))


def joep(parent, loc, yaw=0.0, name='Joep', expr=None, cap=True, rot=None, **pose):
    p = dict(root=(0, 0, 0), yaw=yaw)
    p.update(pose)
    j = Joep(name, pose=p, expr=expr, cap=cap)
    r = j.build()
    if parent is not None:
        r.parent = parent
    r.location = loc
    r.rotation_euler = rot if rot is not None else (0, 0, math.radians(yaw))
    return j
