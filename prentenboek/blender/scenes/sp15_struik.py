"""p. 15-16: Joep ziet iets. Daar, achter de struik! Over Joeps schouder vanuit de boom omlaag: het kruimelspoor
loopt naar een struik; daarachter een gestreepte rug, een rode muts en de zak. Daan klein onder aan de boom."""
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
    sm = sets.set_mats()
    stage.sky('#4d8fdb', '#cfe6f3', '#8f9a7a', 1.0)
    stage.sun(200, 48, 4.3)
    sets.park(None, Q, grass_region=(-1.0, 4.5, 0.5, 7.5), trees=[(-3.5, 9, 6, 2.0), (5.5, 10, 5.5, 1.8)],
              bushes=[(1.6, 4.3, 1.05), (-0.8, 6.8, 0.8), (3.9, 6.2, 0.9)], path=True, flowers_n=30, houses=True,
              grass_density=1800)
    # boom met een lange tak naar de struik toe; het blad staat achter en boven de camera
    bark = Wd.world_mats()['bark']
    K.tube('Stam', [(0, -0.3, -0.05), (0.02, -0.28, 1.2), (0.0, -0.25, 2.4), (-0.1, -0.3, 3.6)],
           [0.26, 0.21, 0.18, 0.13], bark, None, ring=28, per=8)
    K.tube('Tak', [(0.0, -0.27, 2.25), (0.15, 0.25, 2.38), (0.35, 0.9, 2.45), (0.55, 1.5, 2.55), (0.7, 1.9, 2.62)],
           [0.12, 0.095, 0.075, 0.055, 0.04], bark, None, ring=16, per=6)
    Wd.foliage('Takblad', [((0.85, 2.15, 2.85), 0.42), ((0.5, 1.6, 3.05), 0.32), ((-0.6, -0.8, 4.0), 0.9),
                           ((0.6, -0.9, 4.2), 0.8)], None, leaf_size=0.08, density=int(700 * Q['leaves']), seed=7)
    # kruimelspoor over het pad naar de struik
    rng = np.random.default_rng(3)
    t = np.linspace(0, 1, 60)
    xs = -0.2 + 1.8 * t + rng.normal(0, 0.05, 60)
    ys = 1.4 + 2.6 * t + rng.normal(0, 0.05, 60)
    P.crumbs('Spoor', np.stack([xs, ys, np.full(60, 0.01)], 1), rng.uniform(0.008, 0.016, 60), seed=2)
    # boeven achter de struik (zittend, van boven zichtbaar)
    Person('Lange', 'lang', pose=dict(root=(1.3, 4.95, 0), yaw=150, hip=(0, 0, 0.14), lean=(0.3, 0),
                                      foot_r=(-0.12, -0.5, 0.075), foot_l=(0.12, -0.48, 0.075),
                                      knee_r=(0, -0.3, 1), knee_l=(0, -0.3, 1),
                                      hand_r=(-0.05, -0.32, 0.6), hand_l=(0.1, -0.3, 0.45)),
           expr=dict(smile=1.0, squint=0.5), mats=pm).build()
    Person('Dikkie', 'dik', pose=dict(root=(2.2, 4.85, 0), yaw=200, hip=(0, 0, 0.16), lean=(0.2, 0),
                                      foot_r=(-0.18, -0.45, 0.075), foot_l=(0.18, -0.45, 0.075),
                                      knee_r=(0, -0.3, 1), knee_l=(0, -0.3, 1),
                                      hand_r=(-0.1, -0.35, 0.55), hand_l=(0.1, -0.35, 0.55)),
           expr=dict(smile=1.0, squint=0.5), mats=pm, puff=0.1).build()
    P.sack('Zak', None, (1.75, 5.25, 0), (0, 0, 0.5), size=0.45, open_=True)
    # Joep op de tak, van achteren, wijst naar de struik
    j = Joep('Joep', pose=dict(
        root=(0, 0, 0), cap=True, head=(0.35, -0.2, 0.0), body_tilt=(0.15, 0.0),
        arm_r=[(-0.03, -0.05, -0.02), (-0.05, -0.1, -0.05), (-0.06, -0.15, -0.08)],
        arm_l=[(0.04, -0.01, -0.04), (0.06, 0.0, -0.08), (0.07, 0.02, -0.12)],
        leg_r=[(-0.01, -0.04, -0.05), (-0.015, -0.03, -0.1), (-0.02, -0.02, -0.15)],
        leg_l=[(0.01, -0.04, -0.05), (0.02, -0.02, -0.1), (0.03, 0.0, -0.15)],
        tail=[(0.0, 0.04, -0.05), (0.0, 0.05, -0.1), (0.01, 0.04, -0.15)]),
        mats=jm, fur=Q['fur'])
    jr = j.build()
    jr.location = (0.3, 0.72, 2.38)
    jr.rotation_euler = (0, 0, math.pi + 0.35)
    d = Daan('Daan', pose=dict(root=(0.45, 0.25, 0), yaw=200, head=(-40, 0, 0),
                               hand_r=(-0.1, -0.12, 0.88), fdir_r=(0, -0.2, 1), fingers_r='spread', palm_r=(0, -1, 0)),
             expr=dict(smile=0.5, mouth='o', open=0.4, look_at=(0.3, 0.72, 2.7)), cap=True, mats=dm,
             hair_density=Q['hair'] * 0.6)
    d.build()
    K.camera((-0.12, 0.05, 2.92), (1.5, 4.2, 0.4), lens=24, fstop=8.0, focus=(1.4, 4.4, 0.4), roll=-0.05)
    K.light('AREA', (-2.0, -1.0, 4.0), (1.0, 3.0, 0.5), energy=400, size=4.0, color=(0.9, 0.95, 1.0))
    K.render(out)
