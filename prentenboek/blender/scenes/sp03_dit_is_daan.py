"""p. 2-3: Dit is Daan. En dit is Joep, het aapje van Daan.

In de tuin achter een wit hekje. Links staat Daan (gewone kleren: rood shirt met een banaan, spijkerbroek)
en zwaait. Rechts schommelt Joep op een houten schommel. Bovenin blijft lucht vrij voor de tekst."""
import math
import bpy
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep

CM = 0.01


def main(out, opts):
    V.setup(opts)
    clouds = ((-40, 38, 0.8), (6, 44, 0.65), (44, 36, 0.7))
    PS.sky(y=0.55, w=180, h=75, sun=(-62, 40), clouds=clouds)
    for i, (cx, cz, s) in enumerate(clouds):
        PS.thread(f'Wolkdraad{i}', cx * CM, 0.55 - 0.009 - 0.002 * i, cz * CM + 0.045 * s)
    PS.thread('Zondraad', -0.62, 0.544, 0.40 + 0.115)
    PS.hills(y0=0.47, w=180, seed=3)
    PS.tree('Boom0', -0.48, 0.3, 16, 7.5, apples=4, seed=1)
    PS.tree('Boom1', 0.5, 0.32, 18, 8, seed=2)
    PS.grassland(y0=-0.6, y1=0.5)
    PS.fence('Hek', -0.9, 0.9, 0.16, h=9.0)
    PS.bush('Struik0', -0.3, 0.14, 16, 6, berries=5, seed=1)
    PS.bush('Struik1', 0.36, 0.14, 14, 5, seed=2)
    PS.flowers('Bloem', -0.6, 0.6, 0.12, 22, seed=3)
    # schommel rechts
    sx, sy, top = 0.2, 0.03, 0.2
    for k, dx in enumerate((-0.085, 0.085)):
        for j, lean in enumerate((-1, 1)):
            PS.card(f'Schommelpoot{k}{j}', PS.strip([(0, 0), (-lean * 3.2, top * 100)], 1.2, cap=False), '#9a6a40',
                    sy + 0.004 + 0.002 * j, x=sx + dx + lean * 0.032, paper='kraft')
    PS.card('Schommelbalk', PS.rrect(0, top * 100, 22, 1.6, 0.4), '#8a5a36', sy + 0.001, x=sx, paper='kraft')
    piv = K.empty('Schommelas', (sx, sy, top), (0, 0, 0))
    for k, dx in enumerate((-3.6, 3.6)):
        ob = PS.piece(f'Touw{k}', PS.rrect(dx, -6.5, 0.28, 13.0, 0.1), '#efe6cf', piv, 0, paper='crepe', jitter=0.0)
    PS.piece('Zitje', PS.rrect(0, -13.2, 9.5, 1.1, 0.3), '#c0392b', piv, 1.0, paper='glans')
    j = Joep('Joep', pose=dict(loc=(sx, sy - 0.003, top - 0.128), arm_r='wave', arm_l=(160, 170), legs='sit',
                               head=-8), expr=dict(mouth='grin'), cap=False)
    jr = j.build()
    bpy.context.view_layer.update()
    jr.parent = piv
    jr.matrix_parent_inverse = piv.matrix_world.inverted()
    piv.rotation_euler[1] = math.radians(-14)
    # Daan links
    Daan('Daan', pose=dict(loc=(-0.2, -0.27, 0.0), arm_r='wave', arm_l='down', head=-5),
         expr=dict(mouth='grin', brows='up', look=(0.1, 0.0)), cap=False, outfit='casual').build()
    PS.card('Bal', PS.circle(0, 2.4, 2.4, 48), '#4f9ad9', -0.22, x=-0.1, paper='glans')
    PS.card('Balstreep', PS.rrect(0, 2.4, 4.8, 0.8, 0.3), '#ffd34d', -0.2212, x=-0.1, paper='glans')
    for i, (x, y) in enumerate(((-0.42, -0.3), (-0.05, -0.33), (0.36, -0.3), (0.12, -0.36))):
        PS.tuft(f'Pol{i}', x, y, h=3.5, w=6, color='#5f9a3f', seed=i)
    V.cam((0.0, -0.82, 0.1), (0.0, 0.0, 0.105), lens=38, fstop=8.0, focus=(-0.2, -0.27, 0.07))
    K.render(out)
