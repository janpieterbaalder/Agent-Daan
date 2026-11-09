from lib import core as K, cast, hair
from lib.head import Head


def main(out, opts):
    K.reset()
    K.render_setup(1000, 600, samples=32)
    K.world_color('#8c8178', 0.6)
    m = cast.char_mats()
    base = K.empty('b', (0, 0, 0), (0, 0, 0))
    h = Head('H')
    h.build(base, m, scale=0.13)
    K.camera((0.03, -0.5, 0.05), (0.03, 0, 0.0), lens=90)
    K.light('AREA', (-0.9, -1.2, 0.9), (0, 0, 0), energy=120, size=1.0, color=(1, 0.95, 0.9))
    K.light('AREA', (1.1, -0.9, 0.2), (0, 0, 0), energy=40, size=1.5, color=(0.9, 0.95, 1))
    K.render(out)
