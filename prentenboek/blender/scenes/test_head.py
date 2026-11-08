import math
from lib import core as K, cast, hair
from lib.head import Head


def main(out, opts):
    K.reset()
    w = int(opts.get('w') or 1500)
    K.render_setup(w, int(w * 0.55), samples=int(opts.get('samples') or 48))
    K.world_color('#8c8178', 0.6)
    m = cast.char_mats()
    for i, (x, rz) in enumerate([(-0.2, 0), (0.2, 0.7)]):
        base = K.empty(f'b{i}', (x, 0, 0), (0, 0, rz))
        h = Head(f'H{i}')
        h.build(base, m, scale=0.13)
        h.brows(m, m['brow'])
        hair.build(h, m, 'kuif')
    K.camera((0, -2.0, 0.06), (0, 0, 0.03), lens=90)
    K.light('AREA', (-0.9, -1.2, 0.9), (0, 0, 0), energy=120, size=1.0, color=(1, 0.95, 0.9))
    K.light('AREA', (1.1, -0.9, 0.2), (0, 0, 0), energy=40, size=1.5, color=(0.9, 0.95, 1))
    K.light('AREA', (0.4, 1.2, 0.8), (0, 0, 0), energy=90, size=0.8)
    K.render(out)
