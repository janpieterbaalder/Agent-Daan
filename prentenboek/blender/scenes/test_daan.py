import math
from lib import core as K, cast
from lib.daan import Daan


def main(out, opts):
    K.reset()
    w = int(opts.get('w') or 1600)
    K.render_setup(w, int(w * 0.62), samples=int(opts.get('samples') or 48))
    K.world_color('#8c8178', 0.7)
    m = cast.char_mats()
    d1 = Daan('DaanPet', pose=dict(root=(-0.33, 0, 0)), cap=True, mats=m, hair_density=0.6)
    d1.build()
    d2 = Daan('DaanKuif', pose=dict(root=(0.33, 0, 0), yaw=-25, head=(0, 10, 0)), cap=False, mats=m,
              hair_density=0.6)
    d2.build()
    K.camera((0, -2.9, 0.6), (0, 0, 0.47), lens=55)
    K.light('AREA', (-1.5, -2.0, 2.0), (0, 0, 0.5), energy=500, size=2.0, color=(1, 0.95, 0.9))
    K.light('AREA', (2.0, -1.5, 0.8), (0, 0, 0.5), energy=150, size=2.5, color=(0.9, 0.95, 1))
    K.light('AREA', (0.5, 2.0, 1.6), (0, 0, 0.6), energy=300, size=1.0)
    from lib import mats as MM
    g = K.blob('vloer', (4, 4, 0.01), 6, (8, 4), mat=MM.simple('vloer', '#b8aea2', 0.7), loc=(0, 0, -0.01))
    K.render(out)
