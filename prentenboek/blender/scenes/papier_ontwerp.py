"""Ontwerpblad papieren kijkdoos: alle figuurtjes op een rij voor een kartonnen achtergrond."""
import math
from lib import core as K, stage, papier as P
from lib.papierpop import Daan, Joep, Mens


def main(out, opts):
    stage.setup(opts, 'spread', look='Medium Contrast')
    K.world_color('#d9cfc2', 0.25)
    P.piece('Achterkarton', P.rrect(0, 15, 140, 60, 2), '#e7dccb', None, 0, thick=0.002, bend=0, jitter=0,
            ).location = (0, 0.09, -0.12)
    P.piece('Grondkarton', P.rrect(0, 0, 140, 40, 2), '#d9c9b1', None, 0, thick=0.002, bend=0, jitter=0, plane='xy',
            z=0.0).location = (0, 0.0, -0.002)
    Mens('Lange', 'lang', pose=dict(loc=(-0.24, 0.02, 0), arm_l='hip', arm_r='down'),
         expr=dict(mouth='smile', brows='cross')).build()
    Mens('Dikkie', 'dik', pose=dict(loc=(-0.13, 0.0, 0), arm_l='hold', arm_r='hold'),
         expr=dict(mouth='o', brows='worried')).build()
    Daan('Daan', pose=dict(loc=(-0.03, -0.02, 0), arm_r='salute', arm_l='down'),
         expr=dict(mouth='smile'), cap=True).build()
    Daan('DaanKuif', pose=dict(loc=(0.05, -0.01, 0), arm_l='wave', arm_r='hip', head=-6),
         expr=dict(mouth='grin', brows='up'), cap=False).build()
    Joep('Joep', pose=dict(loc=(0.115, -0.03, 0), arm_r='salute', arm_l='down', legs='sit'), cap=True).build()
    Mens('Bakker', 'bakker', pose=dict(loc=(0.21, 0.01, 0), arm_l='wave', arm_r='hip'),
         expr=dict(mouth='grin')).build()
    K.camera((0.0, -0.75, 0.13), (0.0, 0.0, 0.1), lens=50, fstop=8.0, focus=(0.0, -0.02, 0.1), clip=(0.01, 10))
    K.light('AREA', (-0.5, -0.55, 0.55), (0, 0, 0.08), energy=22, size=0.3, color=(1.0, 0.94, 0.85))
    K.light('AREA', (0.6, -0.5, 0.3), (0, 0, 0.08), energy=4, size=0.8, color=(0.85, 0.92, 1.0))
    K.render(out)
