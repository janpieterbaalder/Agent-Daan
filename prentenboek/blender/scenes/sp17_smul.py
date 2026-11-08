"""p. 17-18: Twee boeven met een zak vol koekjes. Smik, smak, smul!
Laag, door de bladeren van de struik heen: de boeven zitten in het gras en smullen; de zak ligt open."""
import math
import numpy as np
from lib import core as K, cast, stage, sets, props as P, world as Wd
from lib.people import Person, people_mats


def main(out, opts):
    Q = stage.setup(opts, 'spread')
    dm = cast.char_mats()
    pm = people_mats(dm)
    stage.sky('#4d8fdb', '#cfe6f3', '#8f9a7a', 1.0)
    stage.sun(140, 40, 4.0)
    sets.park(None, Q, grass_region=(-2.2, 2.2, -1.0, 2.0), trees=[(-2.5, 4.5, 5.5, 2.0), (3.0, 5.0, 5.0, 1.7)],
              bushes=[(-2.0, 1.8, 1.0), (2.3, 1.6, 0.9)], path=False, flowers_n=25, houses=True,
              grass_density=2600)
    # voorgrond: bladeren van de struik waar de camera doorheen kijkt
    Wd.foliage('VoorBlad_l', [((-0.95, -1.05, 0.5), 0.45), ((-0.75, -1.0, 0.95), 0.3)], None, leaf_size=0.07,
               density=int(1600 * Q['leaves']), seed=31, inner_mat=False)
    Wd.foliage('VoorBlad_r', [((0.95, -1.0, 0.45), 0.4), ((0.8, -1.1, 0.0), 0.35)], None, leaf_size=0.07,
               density=int(1600 * Q['leaves']), seed=32, inner_mat=False)
    cam = (0.0, -1.55, 0.42)
    L = Person('Lange', 'lang', pose=dict(
        root=(-0.5, 0.3, 0), yaw=18, hip=(0, 0, 0.13), lean=(0.05, 0.0), head=(-6, 10, 6),
        foot_r=(-0.16, -0.52, 0.075), foot_l=(0.14, -0.5, 0.075), knee_r=(-0.3, -0.3, 1), knee_l=(0.3, -0.3, 1),
        hand_r=(-0.02, -0.27, 0.77), palm_r=(0, 1, 0), fdir_r=(0.2, -0.2, 1), fingers_r='grip', elbow_r=(-1, 0, -0.4),
        hand_l=(0.2, -0.3, 0.42), palm_l=(0, 0, 1), fdir_l=(0, -1, 0.3), fingers_l='hold'),
        expr=dict(smile=1.0, squint=0.7, look_at=cam), mats=pm, puff=0.06)
    L.build()
    Dk = Person('Dikkie', 'dik', pose=dict(
        root=(0.55, 0.2, 0), yaw=-22, hip=(0, 0, 0.16), lean=(-0.05, 0.0), head=(-4, -8, -4),
        foot_r=(-0.2, -0.45, 0.075), foot_l=(0.2, -0.45, 0.075), knee_r=(-0.3, -0.3, 1), knee_l=(0.3, -0.3, 1),
        hand_r=(-0.14, -0.36, 0.62), palm_r=(0.3, 1, 0), fdir_r=(0.3, 0, 1), fingers_r='grip', elbow_r=(-1, 0, -0.4),
        hand_l=(0.14, -0.36, 0.62), palm_l=(-0.3, 1, 0), fdir_l=(-0.3, 0, 1), fingers_l='grip', elbow_l=(1, 0, -0.4)),
        expr=dict(smile=1.0, squint=0.8), mats=pm, puff=0.14)
    Dk.build()
    # koekjes in de handen (in de lokale ruimte van de figuren)
    P.cookie('Koek_lang', 'choc', 0.045, L.root, (-0.02, -0.33, 0.83), (1.3, 0.2, 0.3), seed=1, bite=0.5)
    P.cookie('Koek_dik_r', 'roze', 0.045, Dk.root, (-0.12, -0.44, 0.7), (1.2, 0.3, 0.0), seed=2)
    P.cookie('Koek_dik_l', 'choc', 0.045, Dk.root, (0.12, -0.44, 0.7), (1.2, -0.3, 0.0), seed=3, bite=0.6)
    P.sack('Zak', None, (0.05, 0.62, 0), (0.25, 0, 0.4), size=0.42, open_=True, cookies_in=8)
    rng = np.random.default_rng(6)
    kinds = ['choc', 'roze', 'ster']
    for i in range(9):
        P.cookie(f'Los{i}', kinds[i % 3], 0.04, None,
                 (rng.uniform(-0.5, 0.6), rng.uniform(-0.1, 0.5), 0.012), (rng.normal(0, 0.15), rng.normal(0, 0.15), rng.random() * 6),
                 seed=10 + i)
    P.crumbs('Kruimels', np.stack([rng.uniform(-0.8, 0.9, 120), rng.uniform(-0.4, 0.7, 120), np.full(120, 0.01)], 1),
             rng.uniform(0.004, 0.01, 120), seed=5)
    K.camera(cam, (0.02, 0.35, 0.6), lens=26, fstop=2.8, focus=(0.0, 0.3, 0.6))
    K.light('AREA', (0.5, -2.0, 1.5), (0, 0.3, 0.5), energy=250, size=2.5, color=(0.95, 0.95, 1.0))
    K.light('AREA', (-1.5, 2.0, 2.0), (0, 0.3, 0.6), energy=200, size=1.0, color=(1.0, 0.9, 0.75))
    K.render(out)
