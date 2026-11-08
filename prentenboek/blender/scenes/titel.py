"""Titelpagina-vignet: Joep zit met zijn petje op en houdt een groot koekje vast (vrijstaand, met schaduw)."""
import math
import bpy
from lib import core as K, cast, stage, props as P, mats as M
from lib.joep import Joep, joep_mats


def main(out, opts):
    Q = stage.setup(opts, 'page', transparent=True)
    dm = cast.char_mats()
    jm = joep_mats(dm)
    K.world_color('#fff8ec', 0.9)
    j = Joep('Joep', pose=dict(
        root=(0, 0, -0.12), cap=True, head=(-0.12, 0.25, 0.12), body_tilt=(-0.15, 0.0),
        leg_r=[(-0.02, -0.06, -0.12), (-0.05, -0.12, -0.14), (-0.08, -0.17, -0.14)],
        leg_l=[(0.02, -0.06, -0.12), (0.05, -0.12, -0.14), (0.08, -0.17, -0.14)],
        arm_r=[(-0.02, -0.04, 0.0), (-0.0, -0.075, 0.02), (0.02, -0.09, 0.04)],
        arm_l=[(0.02, -0.04, 0.0), (0.0, -0.075, 0.02), (-0.02, -0.09, 0.04)],
        tail=[(0.0, 0.05, -0.12), (0.05, 0.09, -0.135), (0.1, 0.1, -0.14)]),
        mats=jm, fur=Q['fur'])
    jr = j.build()
    jr.scale = (1.0,) * 3
    P.cookie('Grote_koek', 'choc', 0.05, j.body, (0.0, -0.085, 0.115), (1.2, 0, 0.2), seed=3, bite=0.55)
    vl = K.blob('Schaduwvanger', (2, 2, 0.001), 8, (8, 4), mat=M.simple('sv', '#ffffff'), loc=(0, 0, -0.001))
    vl.is_shadow_catcher = True
    K.camera((0.12, -0.95, 0.24), (0.0, 0.0, 0.14), lens=70, fstop=4.0, focus=(0, -0.1, 0.16))
    K.light('AREA', (-0.8, -0.8, 1.2), (0, 0, 0.15), energy=60, size=1.2, color=(1.0, 0.95, 0.88))
    K.light('AREA', (0.9, -0.5, 0.5), (0, 0, 0.15), energy=18, size=1.0, color=(0.88, 0.93, 1.0))
    K.light('AREA', (0.3, 0.9, 0.7), (0, 0, 0.2), energy=40, size=0.6)
    K.render(out)
