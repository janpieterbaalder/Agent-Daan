"""Gedeelde opzet voor de kijkdoosplaten: licht als bij een papieren maquette op tafel, camera, hulpjes."""
import math
from . import core as K, stage


def setup(opts, kind='spread', night=False, transparent=False):
    Q = stage.setup(opts, kind, transparent=transparent, look='Medium High Contrast', exposure=-0.05)
    if night:
        K.world_color('#1a2147', 0.12)
        K.light('AREA', (-0.45, -0.55, 0.55), (0, 0, 0.08), energy=6, size=0.4, color=(0.6, 0.68, 1.0))
        K.light('AREA', (0.5, -0.5, 0.25), (0, 0, 0.08), energy=1.2, size=0.8, color=(0.7, 0.75, 1.0))
    else:
        K.world_color('#d9cfc2', 0.22)
        K.light('AREA', (-0.5, -0.55, 0.6), (0, 0, 0.08), energy=24, size=0.32, color=(1.0, 0.94, 0.85))
        K.light('AREA', (0.6, -0.5, 0.3), (0, 0, 0.08), energy=5, size=0.8, color=(0.85, 0.92, 1.0))
        K.light('AREA', (0.1, 0.4, 0.5), (0, 0.1, 0.1), energy=4, size=0.5, color=(1.0, 0.9, 0.8))
        # lamp op het luchtdoek, zoals bij een kijkdoos op tafel
        K.light('AREA', (0.0, -0.1, 0.95), (0, 0.5, 0.25), energy=12, size=1.4, color=(1.0, 0.97, 0.92))
    return Q


def cam(loc, target, lens=45, fstop=8.0, focus=None):
    return K.camera(loc, target, lens=lens, fstop=fstop, focus=focus if focus is not None else target, clip=(0.01, 20))


def in_hand(fig, side, fn, dz=0.0, layer=4.6):
    """Zet een voorwerp in de hand van een figuur (side -1 = linker, 1 = rechter, gezien vanaf de figuur
    in beeld: -1 links in beeld). fn(parent, loc) maakt het voorwerp; loc in m, lokaal in de hand."""
    hg = fig.hands[side]
    return fn(hg, (0.0, -layer * 0.0012, dz))


def lie(root, deg=-90.0):
    """Leg een figuur neer (draai om de kijkas); -90 = hoofd naar links."""
    import math
    root.rotation_euler[1] = math.radians(deg)
    return root
