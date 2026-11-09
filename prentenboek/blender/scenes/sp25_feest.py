"""p. 24-25: Goed gedaan, agent Daan! Goed gedaan, agent Joep!

Feest op het pleintje: Daan en Joep staan op een kist met een medaille, iedereen juicht. De boeven dragen
nu een koksmuts (ze helpen de bakker), vlaggetjes en confetti, de politieauto met zwaailicht erbij."""
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, Mens


def main(out, opts):
    V.setup(opts)
    PS.sky(y=0.6, w=180, h=80, sun=None, clouds=((-50, 44, 0.6), (50, 46, 0.6)))
    yh = 0.27
    for i, (hx, w, h, col, rf, dr) in enumerate(((-0.42, 14, 16, '#9fb3d9', '#b8503e', '#7a4f8f'),
                                                (0.16, 14, 15, '#e88a7d', '#4b5d7a', '#4f7a3a'),
                                                (0.42, 13, 17, '#8fb8a8', '#6b4a3a', '#a83b3b'))):
        with PS.scaled((hx, yh, 0), 1.35):
            PS.house(f'Huis{i}', hx, yh, w, h, col, rf, dr, seed=i + 8)
    with PS.scaled((-0.14, yh, 0), 1.35):
        PS.bakery('Bakkerij', -0.14, yh)
    PS.pavement('Plein', -1.0, 1.0, -0.6, yh + 0.005, kind='klinker', seed=9)
    PS.bunting('Vlag1', -0.6, 0.0, 0.2, 0.12, n=12, sag=3.0)
    PS.bunting('Vlag2', 0.0, 0.6, 0.2, 0.12, n=12, sag=3.0)
    PS.police_car('Auto', 0.38, 0.16, facing=-1, scale=0.8)
    # podium
    PS.crate('Podium', 0.0, -0.08, w=22, h=6)
    d = Daan('Daan', pose=dict(loc=(-0.04, -0.085, 0.06), arm_r='salute', arm_l='down', head=-4),
             expr=dict(mouth='grin', brows='up'), cap=True)
    d.build()
    PS.medal('Medaille_Daan', d.root, (0.0, 6.1), 4.5)
    j = Joep('Joep', pose=dict(loc=(0.05, -0.088, 0.06), arm_l='cheer', arm_r='cheer', head=6),
             expr=dict(mouth='grin', eyes='happy'), cap=True)
    j.build()
    PS.medal('Medaille_Joep', j.root, (0.0, 3.0), 4.5, s=0.8)
    Mens('Bakker', 'bakker', pose=dict(loc=(-0.22, -0.02, 0.0), arm_l='cheer', arm_r='cheer', head=-4),
         expr=dict(mouth='grin', eyes='happy')).build()
    Mens('Lange', 'lang', pose=dict(loc=(0.2, 0.0, 0.0), arm_l='cheer', arm_r='wave', head=5),
         expr=dict(mouth='grin'), mask_up=True, chef=True).build()
    Mens('Dikkie', 'dik', pose=dict(loc=(0.29, -0.03, 0.0), arm_l='cheer', arm_r='cheer', head=-5),
         expr=dict(mouth='grin', eyes='happy'), mask_up=True, chef=True).build()
    PS.confetti('Confetti', 90, -0.4, 0.4, 0.04, 0.3, -0.2, 0.05, seed=7)
    V.cam((0.0, -0.84, 0.12), (0.0, 0.0, 0.12), lens=38, fstop=8.0, focus=(0.0, -0.08, 0.1))
    K.render(out)
