"""Schutblad: patroon van papieren knipsels op donkerblauw karton: koekmannetjes, petjes, sterren van
goudfolie, vergrootglazen en bananen. Recht van voren, orthografisch."""
import math
import numpy as np
from lib import core as K, papier as P, papierset as PS, papierscene as V
from lib.papierpop import daan_cap


def main(out, opts):
    V.setup(opts, 'page')
    P.piece('Ondergrond', P.rrect(0, 0, 40, 40, 0.5), '#1f2b5e', None, 0, thick=0.001, jitter=0.0, bend=0,
            paper='linnen').location = (0, 0.004, 0)
    rng = np.random.default_rng(21)
    kinds = ['koek', 'pet', 'ster', 'glas', 'koek', 'banaan', 'ster', 'pet']
    n = 0
    for row in range(7):
        for col in range(7):
            x = -0.105 + col * 0.035 + (0.0175 if row % 2 else 0) + rng.normal(0, 0.0015)
            z = -0.105 + row * 0.035 + rng.normal(0, 0.0015)
            kind = kinds[(n * 5 + row) % len(kinds)]
            rot = rng.uniform(-25, 25)
            hook = K.empty(f'Haak{n}', (x, 0.0, z), (0, math.radians(rot), 0))
            if kind == 'koek':
                PS.cookie(f'K{n}', 0, 0, 0, r=0.95, seed=n, bite=(n % 4 == 0), parent=hook)
            elif kind == 'pet':
                hook.scale = (0.42, 0.42, 0.42)
                daan_cap(f'Pet{n}', hook, (0, -0.8), layer=0)
            elif kind == 'ster':
                P.piece(f'Ster{n}', P.star(0, 0, 0.9, 0.4), '#e9b23a', hook, 0, paper='folie')
            elif kind == 'glas':
                hook.scale = (0.55, 0.55, 0.55)
                PS.magnifier(f'Glas{n}', hook, (0, 0.8), 0)
            else:
                P.piece(f'Banaan{n}', P.strip([(-0.9, 0.4), (-0.4, -0.2), (0.4, -0.25), (0.95, 0.3)], 0.55),
                        '#f6d34a', hook, 0, paper='aquarel')
                P.piece(f'Banaantip{n}', P.circle(0.98, 0.33, 0.13, 12), '#6b4a2a', hook, 0.5, paper='kraft')
            n += 1
    cam = K.camera((0, -0.5, 0), (0, 0.0, 0.0), lens=50)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 0.245
    K.render(out)
