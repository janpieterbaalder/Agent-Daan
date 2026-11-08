"""p. 23-24: Samen brengen ze de koekjes terug. Iedereen krijgt er een. Joep krijgt er twee!
Recht van boven op een ronde tafel voor de bakkerij: een bord vol koekjes, iedereen kijkt omhoog. Joep zit op de
tafel met in elke hand een koekje."""
import math
import numpy as np
from lib import core as K, cast, stage, sets, props as P, world as Wd
from lib.daan import Daan
from lib.joep import Joep, joep_mats
from lib.people import Person, people_mats


def main(out, opts):
    Q = stage.setup(opts, 'spread')
    dm = cast.char_mats()
    jm = joep_mats(dm)
    pm = people_mats(dm)
    pr = P.prop_mats()
    wm = Wd.world_mats()
    stage.sky('#5b9be0', '#dcedf5', '#8f9a7a', 1.0)
    stage.sun(230, 55, 4.0)
    Wd.sidewalk('Terras', -4.5, 4.5, -3, 3, z=0.0)
    # tafel
    T = 0.52
    K.lathe('Tafelpoot', [(0.28, 0.0), (0.06, 0.04), (0.05, T - 0.03), (0.0, T - 0.02)], 32, wm['metal_dark'], None)
    cloth = K.lathe('Tafelkleed', [(0.0, T + 0.02), (0.78, T + 0.02), (0.82, T), (0.84, T - 0.12), (0.86, T - 0.2)], 96,
                    pr['cloth_check'], None, close_bot=False)
    P._plate('Schaal', None, (0, 0.05, T + 0.02), 0.26)
    rng = np.random.default_rng(1)
    kinds = ['choc', 'roze', 'ster']
    for i in range(14):
        a = i / 14 * 6.28 * 2.3 + rng.random() * 0.3
        r = 0.04 + 0.16 * math.sqrt(i / 14)
        P.cookie(f'Schaalkoek{i}', kinds[i % 3], 0.042, None,
                 (math.cos(a) * r, 0.05 + math.sin(a) * r, T + 0.05 + 0.02 * (i % 3)),
                 (rng.normal(0, 0.2), rng.normal(0, 0.2), rng.random() * 6), seed=40 + i)
    for i, (x, y) in enumerate(((-0.45, -0.25), (0.48, -0.15), (-0.3, 0.45), (0.38, 0.42))):
        K.lathe(f'Beker{i}', [(0.0, T + 0.02), (0.035, T + 0.02), (0.04, T + 0.12), (0.037, T + 0.125), (0.0, T + 0.1)],
                32, pr['white'], None).location = (x, y, 0)
    cam = (0.0, -2.25, 3.05)
    look = (0.0, -2.25, 3.05)
    # personen rond de tafel, iedereen kijkt omhoog
    d = Daan('Daan', pose=dict(
        root=(-0.86, -0.5, 0), yaw=-50, head=(-35, 18, 0), lean=(-0.1, 0),
        hand_r=(-0.12, -0.25, 0.62), palm_r=(0.3, 0, 1), fdir_r=(0, -1, 0.2), fingers_r='grip', elbow_r=(-1, 0.3, -0.3),
        hand_l=(0.17, -0.12, 0.6), palm_l=(0, -1, 0), fdir_l=(0.2, 0, 1), fingers_l='spread'),
        expr=dict(smile=1.0, mouth='grin', open=0.5, squint=0.3, look_at=look), cap=True, mats=dm,
        hair_density=Q['hair'])
    d.build()
    P.cookie('Koek_daan', 'choc', 0.042, d.root, (-0.12, -0.3, 0.64), (1.4, 0, 0), seed=5)
    j = Joep('Joep', pose=dict(
        root=(0, 0, 0), cap=True, head=(-0.75, 0.1, 0.1), body_tilt=(-0.35, 0),
        arm_r=[(-0.04, -0.02, 0.04), (-0.07, -0.03, 0.08), (-0.09, -0.04, 0.12)],
        arm_l=[(0.04, -0.02, 0.04), (0.07, -0.03, 0.08), (0.09, -0.04, 0.12)],
        leg_r=[(-0.01, -0.05, -0.12), (-0.02, -0.1, -0.14), (-0.03, -0.16, -0.14)],
        leg_l=[(0.01, -0.05, -0.12), (0.02, -0.1, -0.14), (0.03, -0.16, -0.14)]),
        mats=jm, fur=Q['fur'])
    jr = j.build()
    jr.location = (0.05, -0.5, T - 0.08)
    jr.rotation_euler = (0, 0, 0.0)
    jr.scale = (0.9,) * 3
    # twee koekjes in Joeps handen (in Joep-ruimte, armen eindigen bij schouder + laatste punt)
    P.cookie('Joepkoek_r', 'roze', 0.04, j.body, (-0.033 - 0.09, -0.002 - 0.04, 0.075 + 0.14), (1.2, 0, 0.2), seed=6)
    P.cookie('Joepkoek_l', 'ster', 0.04, j.body, (0.033 + 0.09, -0.002 - 0.04, 0.075 + 0.14), (1.2, 0, -0.2), seed=7)
    b = Person('Bakker', 'bakker', pose=dict(
        root=(0.95, -0.35, 0), yaw=60, head=(-25, -15, 0), lean=(-0.1, 0),
        hand_r=(-0.12, -0.42, 0.95), palm_r=(0.3, 0, 1), fdir_r=(0, -1, 0.2), fingers_r='grip'),
        expr=dict(smile=1.0, squint=0.4, look_at=look), mats=pm)
    b.build()
    P.cookie('Koek_bakker', 'ster', 0.045, b.root, (-0.12, -0.48, 0.98), (1.4, 0, 0), seed=8)
    L = Person('Lange', 'lang', pose=dict(
        root=(-0.72, 0.62, 0), yaw=25, head=(-20, 5, 0), lean=(-0.05, 0),
        hand_l=(0.14, -0.42, 1.05), palm_l=(-0.3, 0, 1), fdir_l=(0, -1, 0.2), fingers_l='grip'),
        expr=dict(smile=1.0, squint=0.3, look_at=look), mats=pm, mask_up=0.38)
    L.build()
    P.cookie('Koek_lang', 'roze', 0.045, L.root, (0.14, -0.48, 1.08), (1.4, 0, 0), seed=9)
    Dk = Person('Dikkie', 'dik', pose=dict(
        root=(0.65, 0.72, 0), yaw=-25, head=(-20, -5, 0), lean=(-0.05, 0),
        hand_r=(-0.25, -0.35, 0.82), palm_r=(0.3, 0, 1), fdir_r=(0, -1, 0.2), fingers_r='grip'),
        expr=dict(smile=1.0, squint=0.5, look_at=look), mats=pm, mask_up=0.38)
    Dk.build()
    P.cookie('Koek_dik', 'choc', 0.045, Dk.root, (-0.25, -0.41, 0.86), (1.4, 0, 0), seed=10)
    K.camera(cam, (0.0, 0.15, 0.75), lens=27, fstop=5.6, focus=(0, -0.3, 0.7))
    K.light('AREA', (1.5, -2.5, 4.0), (0, 0, 0.6), energy=900, size=4.0, color=(1.0, 0.97, 0.93))
    K.render(out)
