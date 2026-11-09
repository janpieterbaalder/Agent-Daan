"""Gedeelde opzet voor de viltplaten: rustige diorama-belichting, camera op ooghoogte, hulpjes om Joep
of een voorwerp in een hand of op een plek te zetten."""
import math
import numpy as np
from . import core as K, stage
from .viltpop import Daan, Joep, Mens


def setup(opts, kind='spread', night=False, inside=False, transparent=False):
    Q = stage.setup(opts, kind, transparent=transparent)
    if night:
        stage.sky('#1a2350', '#2c3a6e', '#1d2233', 0.22)
        stage.sun(200, 35, 0.25, color=(0.7, 0.8, 1.0), angle=6)
    elif inside:
        K.world_color('#f3e8da', 0.55)
    else:
        stage.sky('#78b8e6', '#cfe8f6', '#9a9c8f', 0.85)
        stage.sun(215, 42, 2.8, color=(1.0, 0.94, 0.84), angle=8)
    return Q


def key(loc=(-3.0, -4.5, 4.2), target=(0, 0, 0.6), energy=950, size=4.5, color=(1.0, 0.96, 0.9)):
    return K.light('AREA', loc, target, energy=energy, size=size, color=color)


def fill(loc=(3.5, -3.5, 2.0), target=(0, 0, 0.6), energy=260, size=4.0, color=(0.9, 0.95, 1.0)):
    return K.light('AREA', loc, target, energy=energy, size=size, color=color)


def cam(loc, target, lens=35, focus=None, fstop=4.0, shift=(0, 0)):
    return K.camera(loc, target, lens=lens, fstop=fstop, focus=focus if focus is not None else target, shift=shift)


def attach(obj, parent, loc, rot=(0, 0, 0)):
    obj.parent = parent
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def in_hand(pop, key, builder, offset=0.03, rot=(0, 0, 0)):
    """Zet een voorwerp (builder(parent, loc, rot) -> object) in de hand van een pop."""
    W, d = pop.hands[key]
    loc = tuple(np.asarray(W) + np.asarray(d) * offset)
    return builder(pop.root, loc, rot)


def joep_on(parent, loc, yaw=0.0, expr=None, cap=True, name='Joep', **pose):
    """Joep als kind van een ander object (op de arm van Daan, op de motorkap, op een tak)."""
    p = dict(root=(0, 0, 0), yaw=yaw)
    p.update(pose)
    j = Joep(name, pose=p, expr=expr, cap=cap)
    r = j.build()
    if parent is not None:
        r.parent = parent
    r.location = loc
    r.rotation_euler = (0, 0, math.radians(yaw))
    return j


def ortho(loc, target, scale, name='Cam'):
    c = K.camera(loc, target, lens=50)
    c.data.type = 'ORTHO'
    c.data.ortho_scale = scale
    return c
