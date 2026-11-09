"""Proefvel: politieauto met Daan achter het stuur en Joep achterin, koekjes, zak, en de figuren naast elkaar."""
from lib import core as K, papier as P, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, Mens


def main(out, opts):
    V.setup(opts)
    P.piece('Achterkarton', P.rrect(0, 15, 160, 70, 2), '#e7dccb', None, 0, thick=0.002, bend=0, jitter=0,
            ).location = (0, 0.12, -0.12)
    P.piece('Grondkarton', P.rrect(0, 0, 160, 50, 2), '#d9c9b1', None, 0, thick=0.002, bend=0, jitter=0, plane='xy',
            z=0.0).location = (0, 0.0, -0.002)
    car = PS.police_car('Auto', -0.12, 0.02, facing=1)
    Daan('Daan', pose=dict(loc=car['driver'], arm_r='wave', arm_l='hold', legs='sit', head=-4),
         expr=dict(mouth='grin'), cap=True).build()
    Joep('Joep', pose=dict(loc=car['back'], arm_r='wave', arm_l='down', legs='sit'), cap=True).build()
    for i, (x, b) in enumerate(((0.13, False), (0.165, True), (0.20, False))):
        PS.cookie(f'Koek{i}', x, -0.04, 0.012, r=1.0, seed=i, bite=b)
    PS.sack('Zak', 0.26, 0.0, 0.0, s=1.0, cookies_out=3)
    Daan('DaanKuif', pose=dict(loc=(0.12, 0.03, 0), arm_l='wave', arm_r='hip', head=-6),
         expr=dict(mouth='grin', brows='up'), cap=False).build()
    Mens('Lange', 'lang', pose=dict(loc=(0.33, 0.04, 0), arm_l='hip', arm_r='down'),
         expr=dict(mouth='smile', brows='cross')).build()
    V.cam((0.04, -0.85, 0.12), (0.04, 0.0, 0.1), lens=45, fstop=11.0, focus=(0.0, 0.0, 0.1))
    K.render(out)
