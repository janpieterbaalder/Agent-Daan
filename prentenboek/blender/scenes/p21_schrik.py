"""p. 21: De boeven schrikken. Beide boeven vallen achterover met de armen omhoog; koekjes vliegen door de lucht
en de muts van de lange boef springt van zijn hoofd."""
import math
import numpy as np
from lib import core as K, cast, stage, sets, props as P
from lib.people import Person, people_mats


def main(out, opts):
    Q = stage.setup(opts, 'page')
    dm = cast.char_mats()
    pm = people_mats(dm)
    stage.sky('#4d8fdb', '#cfe6f3', '#8f9a7a', 1.0)
    stage.sun(160, 45, 4.0)
    sets.park(None, Q, grass_region=(-1.5, 1.5, -1.0, 1.5), trees=[(-2.0, 5, 5.5, 1.9), (2.6, 5.5, 5.2, 1.7)],
              bushes=[(0.2, 2.4, 1.1)], path=False, flowers_n=15, houses=False, grass_density=2400)
    cam = (0.1, -2.05, 0.62)
    L = Person('Lange', 'lang', pose=dict(
        root=(-0.42, 0.15, 0), yaw=12, hip=(0, 0.05, 0.14), lean=(-0.38, -0.08), head=(-12, 6, -8),
        foot_r=(-0.16, -0.5, 0.2), foot_l=(0.15, -0.55, 0.12), knee_r=(-0.3, -0.3, 1), knee_l=(0.3, -0.3, 1),
        hand_r=(-0.32, 0.0, 1.15), palm_r=(0, -1, 0), fdir_r=(-0.3, 0, 1), fingers_r='spread', elbow_r=(-1, 0, -0.2),
        hand_l=(0.32, 0.0, 1.15), palm_l=(0, -1, 0), fdir_l=(0.3, 0, 1), fingers_l='spread', elbow_l=(1, 0, -0.2)),
        expr=dict(mouth='o', open=1.0, smile=0.0, lids=1.0, brow_up=1.0, look_at=cam), mats=pm, hat_pop=0.35)
    L.build()
    Dk = Person('Dikkie', 'dik', pose=dict(
        root=(0.45, 0.0, 0), yaw=-15, hip=(0, 0.06, 0.16), lean=(-0.45, 0.1), head=(-10, -6, 8),
        foot_r=(-0.2, -0.42, 0.25), foot_l=(0.22, -0.45, 0.15), knee_r=(-0.3, -0.3, 1), knee_l=(0.3, -0.3, 1),
        hand_r=(-0.38, -0.02, 0.98), palm_r=(0, -1, 0), fdir_r=(-0.4, 0, 1), fingers_r='spread', elbow_r=(-1, 0, -0.2),
        hand_l=(0.38, -0.02, 0.98), palm_l=(0, -1, 0), fdir_l=(0.4, 0, 1), fingers_l='spread', elbow_l=(1, 0, -0.2)),
        expr=dict(mouth='o', open=1.0, smile=0.0, lids=1.0, brow_up=1.0, look_at=cam), mats=pm)
    Dk.build()
    rng = np.random.default_rng(12)
    kinds = ['choc', 'roze', 'ster']
    for i, (x, y, z) in enumerate(((-0.1, -0.3, 1.25), (0.25, -0.2, 1.45), (0.65, -0.35, 1.2), (-0.65, -0.2, 1.35),
                                   (0.05, -0.5, 0.95), (0.9, 0.1, 1.5), (-0.95, 0.0, 1.05))):
        P.cookie(f'Vlieg{i}', kinds[i % 3], 0.045, None, (x, y, z), tuple(rng.random(3) * 6), seed=20 + i)
    P.crumbs('Kruimelwolk', np.stack([rng.normal(0.0, 0.5, 80), rng.normal(-0.2, 0.25, 80), rng.uniform(0.6, 1.6, 80)], 1),
             rng.uniform(0.004, 0.009, 80), seed=8)
    P.sack('Zak', None, (0.02, 0.45, 0), (0.6, 0, 0.3), size=0.4, open_=True, cookies_in=3)
    K.camera(cam, (0.02, 0.1, 0.78), lens=30, fstop=4.0, focus=(0.0, 0.05, 0.85))
    K.light('AREA', (0.5, -2.5, 1.5), (0, 0, 0.7), energy=320, size=3.0, color=(0.95, 0.97, 1.0))
    K.light('AREA', (-1.2, 2.0, 2.4), (0, 0, 0.8), energy=260, size=1.0, color=(1.0, 0.9, 0.75))
    K.render(out)
