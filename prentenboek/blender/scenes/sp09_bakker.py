"""p. 9-10: Oh nee! Bij de bakker zijn alle koekjes weg.
Camera in de lege vitrine: lege bakjes met kruimels vooraan, door het glas kijken Daan en Joep geschrokken
naar binnen; de bakker erachter met zijn handen tegen zijn wangen."""
import math
import numpy as np
from lib import core as K, cast, stage, sets, props as P, world as Wd, mats as M
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
    sm = sets.set_mats()
    K.world_color('#fff1dc', 0.3)
    sets._box('Vloer', (12, 12, 0.04), (0, 0, -0.02), sm['planks'], None, n=10)
    # vitrine: bodem, kast, glas voor en boven
    sets._box('Vitrinebodem', (3.0, 0.9, 0.06), (0, 0.0, 0.5), wm['counter'], None, n=6)
    sets._box('Vitrinekast', (3.0, 0.9, 0.5), (0, 0.0, 0.25), wm['counter'], None, n=6)
    sets._box('Glas_voor', (3.0, 0.012, 0.62), (0, -0.46, 0.84), pr['thin_glass'], None, n=10)
    sets._box('Glas_boven', (3.0, 0.9, 0.012), (0, 0.0, 1.16), pr['thin_glass'], None, n=10)
    for x in (-1.5, 1.5):
        sets._box(f'Stijl{x}', (0.04, 0.92, 0.66), (x, 0, 0.84), wm['frame_green'], None, n=8)
    sets._box('Lijst_boven', (3.04, 0.04, 0.04), (0, -0.46, 1.16), wm['frame_green'], None, n=8)
    # lege bakjes met kleedjes en kruimels
    rng = np.random.default_rng(2)
    for i, x in enumerate((-0.95, -0.3, 0.35, 1.0)):
        sets._box(f'Bakje{i}', (0.5, 0.36, 0.025), (x, 0.0, 0.545), pr['chrome'], None, n=5)
        K.blob(f'Kleedje{i}', (0.2, 0.15, 0.002), 2.0, (32, 4), mat=pr['white'], loc=(x, 0.0, 0.56))
        pts = np.stack([x + rng.normal(0, 0.12, 14), rng.normal(0, 0.08, 14), np.full(14, 0.565)], 1)
        P.crumbs(f'Kruimels{i}', pts, rng.uniform(0.004, 0.009, 14), seed=i)
    K.text_obj('Bordje', 'OP!', size=0.07, extrude=0.004, bevel=0.001, mat=wm['sign'], loc=(0.65, -0.125, 0.6),
               rot=(math.radians(80), 0, math.radians(-10)))
    sets._box('Bordjekaart', (0.17, 0.006, 0.09), (0.65, -0.11, 0.6), pr['white'], None, n=8,
              rot=(math.radians(-10), 0, math.radians(-10)))
    # winkelpui achter de figuren, met de letters op de ruit (van binnen gespiegeld)
    sets._box('Pui_l', (2.0, 0.12, 3.0), (-2.6, -3.4, 1.5), wm['frame_green'], None, n=8)
    sets._box('Pui_r', (2.0, 0.12, 3.0), (2.6, -3.4, 1.5), wm['frame_green'], None, n=8)
    sets._box('Pui_o', (3.4, 0.12, 0.5), (0, -3.4, 0.25), wm['frame_green'], None, n=8)
    sets._box('Pui_b', (3.4, 0.12, 0.6), (0, -3.4, 2.8), wm['frame_green'], None, n=8)
    sets._box('Etalageruit', (3.4, 0.01, 2.0), (0, -3.38, 1.5), pr['thin_glass'], None, n=10)
    K.text_obj('Ruitletters', 'BAKKER', size=0.32, extrude=0.002, bevel=0.0, mat=wm['gold_letter'],
               loc=(0, -3.36, 2.15), rot=(math.pi / 2, 0, math.pi))
    buiten = K.blob('Straat_buiten', (6, 0.05, 3), 8, (8, 4), mat=M.emission('Daglicht', '#e9f2f7', 2.2),
                    loc=(0, -6.5, 1.5))
    buiten.visible_shadow = False
    for i in range(6):
        o = K.blob(f'Vaag{i}', (0.5, 0.05, 0.8), 2, (16, 8),
                   mat=M.emission(f'Vaag{i}', ('#a8c48a', '#c98e6c', '#8fb0d6')[i % 3], 1.4),
                   loc=(-2.5 + i, -6.3, 1.1 + 0.3 * (i % 2)))
        o.visible_shadow = False
    K.light('AREA', (0, -5.0, 2.0), (0, -1.0, 1.0), energy=600, size=3.0, color=(0.9, 0.95, 1.0))
    # figuren (gezicht naar +y)
    cam = (-0.02, 0.12, 0.64)
    tray = (0.1, 0.0, 0.57)
    d = Daan('Daan', pose=dict(
        root=(0.3, -0.72, 0.0), yaw=180, lean=(0.12, 0.0), head=(-6, -6, 4),
        hand_r=(-0.2, -0.28, 0.54), palm_r=(0, -1, 0), fdir_r=(-0.25, 0, 1), fingers_r='spread', elbow_r=(-1, 0.4, -0.3),
        hand_l=(0.27, -0.2, 0.5), palm_l=(-1, -0.3, 0), fdir_l=(0.2, -0.3, 1), fingers_l='hold', elbow_l=(1, 0.4, -0.3)),
        expr=dict(mouth='o', open=0.85, smile=0.0, lids=1.0, brow_up=1.0, look_at=tray), cap=True, mats=dm,
        hair_density=Q['hair'])
    d.build()
    j = Joep('Joep', pose=dict(
        root=(0.02, -0.56, 0.42), rot=(0, 0, math.pi + 0.25), cap=True, head=(0.12, -0.2, -0.12),
        arm_r=[(-0.04, -0.03, 0.04), (-0.06, -0.06, 0.09), (-0.06, -0.08, 0.13)],
        arm_l=[(0.04, -0.03, 0.04), (0.06, -0.06, 0.09), (0.06, -0.08, 0.13)],
        leg_r=[(-0.005, -0.04, -0.02), (-0.01, -0.06, -0.08), (-0.01, -0.06, -0.14)],
        leg_l=[(0.005, -0.04, -0.02), (0.015, -0.06, -0.08), (0.02, -0.06, -0.14)]),
        mats=jm, fur=Q['fur'])
    j.build()
    b = Person('Bakker', 'bakker', pose=dict(
        root=(-0.62, -1.4, 0.0), yaw=192, head=(6, 8, -6),
        hand_r=(-0.17, -0.2, 1.32), palm_r=(1, 0, 0), fdir_r=(0.3, 0, 1), fingers_r='flat', elbow_r=(-1, 0, -0.5),
        hand_l=(0.17, -0.2, 1.32), palm_l=(-1, 0, 0), fdir_l=(-0.3, 0, 1), fingers_l='flat', elbow_l=(1, 0, -0.5)),
        expr=dict(mouth='o', open=0.7, smile=-0.3, brow_up=0.6, brow_tilt=0.9, look_at=tray), mats=pm)
    b.build()
    K.camera(cam, (0.0, -1.2, 1.05), lens=24, fstop=3.5, focus=(0.3, -0.6, 0.78))
    K.light('AREA', (0.0, 1.5, 2.6), (-0.2, -0.8, 0.8), energy=350, size=2.0, color=(1.0, 0.85, 0.65))
    K.light('AREA', (1.5, 0.5, 1.5), (-0.2, -0.8, 0.8), energy=120, size=1.0, color=(1.0, 0.9, 0.75))
    K.render(out)
