import math
from lib import core as K, cast, mats as MM
from lib.joep import Joep, joep_mats


def main(out, opts):
    K.reset()
    w = int(opts.get('w') or 1600)
    K.render_setup(w, int(w * 0.6), samples=int(opts.get('samples') or 48))
    K.world_color('#8c8178', 0.7)
    dm = cast.char_mats()
    m = joep_mats(dm)
    j1 = Joep('JoepA', pose=dict(root=(-0.12, 0, 0)), mats=m, fur=float(opts.get('fur') or 1.0))
    j1.build()
    j2 = Joep('JoepB', pose=dict(root=(0.14, 0, 0), rot=(0, 0, -0.9), cap=True, head=(0.1, 0.3, 0.15),
                                 arm_l=[(0.03, -0.01, 0.03), (0.04, -0.03, 0.08), (0.03, -0.05, 0.12)]),
              mats=m, fur=float(opts.get('fur') or 1.0))
    j2.build()
    K.camera((0, -1.15, 0.24), (0, 0, 0.19), lens=60, fstop=4.0)
    K.light('AREA', (-0.8, -0.9, 1.0), (0, 0, 0.2), energy=60, size=1.0, color=(1, 0.95, 0.9))
    K.light('AREA', (1.0, -0.6, 0.4), (0, 0, 0.2), energy=20, size=1.2, color=(0.9, 0.95, 1))
    K.light('AREA', (0.3, 1.0, 0.8), (0, 0, 0.25), energy=50, size=0.6)
    K.blob('vloer', (3, 3, 0.01), 6, (8, 4), mat=MM.simple('vloer', '#b8aea2', 0.7), loc=(0, 0, -0.01))
    K.render(out)
