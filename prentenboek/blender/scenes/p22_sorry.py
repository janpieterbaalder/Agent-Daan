"""p. 21: 'Sorry,' zeggen ze. 'We hadden zo'n honger.'

De boeven hebben hun masker omhooggeschoven en kijken beteuterd; de lange houdt de zak voor zich uit om
terug te geven. Rechts vooraan staat Daan met zijn handen in zijn zij, Joep naast hem. Boven rust voor
de tekst."""
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, Mens


def main(out, opts):
    V.setup(opts, 'page')
    PS.sky(y=0.4, w=120, h=70, sun=None, clouds=((-26, 44, 0.5),))
    PS.hills(y0=0.33, w=120, seed=13)
    PS.grassland(y0=-0.5, y1=0.4)
    PS.bush('Struik', -0.02, 0.18, 54, 11, berries=4, seed=17)
    Mens('Lange', 'lang', pose=dict(loc=(-0.1, 0.02, 0.0), arm_l='hold', arm_r='hold', head=10),
         expr=dict(mouth='sad', brows='worried', look=(0.15, -0.2)), mask_up=True).build()
    PS.sack('Zak', -0.095, 0.004, 0.045, s=1.0, cookies_out=3)
    Mens('Dikkie', 'dik', pose=dict(loc=(0.01, 0.0, 0.0), arm_l='hug', arm_r='hug', head=-8),
         expr=dict(mouth='sad', brows='worried', look=(0.15, -0.2)), mask_up=True).build()
    Daan('Daan', pose=dict(loc=(0.1, -0.1, 0.0), arm_l='hip', arm_r='hip', head=-4),
         expr=dict(mouth='flat', brows='cross', look=(-0.25, 0.1)), cap=True).build()
    Joep('Joep', pose=dict(loc=(0.165, -0.12, 0.0), arm_l='hip', arm_r='hip', head=-6),
         expr=dict(mouth='flat', look=(-0.25, 0.1)), cap=True).build()
    for i, (x, y) in enumerate(((-0.16, -0.2), (0.05, -0.24))):
        PS.tuft(f'Pol{i}', x, y, h=3.5, w=6, color='#5f9a3f', seed=i + 7)
    V.cam((0.03, -0.5, 0.1), (0.03, 0.0, 0.1), lens=40, fstop=7.0, focus=(0.0, -0.04, 0.1))
    K.render(out)
