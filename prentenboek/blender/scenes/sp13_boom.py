"""p. 12-13: Joep klimt in de boom. Hup, hup, hup!

In het park staat een grote boom met een stam van kraftpapier. Joep klimt halverwege omhoog; Daan staat
onderaan en wijst naar boven. Het 'hup, hup, hup!' loopt rechts van de stam omhoog; linksonder ruimte
voor de zin."""
import numpy as np
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep

CM = 0.01


def main(out, opts):
    V.setup(opts)
    PS.sky(y=0.6, w=180, h=85, sun=(-60, 52), clouds=((-34, 56, 0.7), (40, 64, 0.6)))
    PS.thread('Zondraad', -0.6, 0.594, 0.52 + 0.115)
    PS.hills(y0=0.52, w=180, seed=7)
    PS.tree('Boom1', -0.44, 0.4, 15, 7, seed=4)
    PS.tree('Boom2', 0.46, 0.42, 13, 6, seed=5)
    PS.grassland(y0=-0.6, y1=0.55)
    PS.bench('Bank', -0.34, 0.22, w=16)
    PS.lamppost('Lantaarn', 0.36, 0.24, h=26)
    PS.flowers('Bloem', -0.6, 0.6, 0.18, 18, seed=6)
    PS.big_tree('Grote_boom', 0.07, 0.06, h=34)
    Joep('Joep', pose=dict(loc=(0.075, 0.035, 0.16), arm_l=(165, 175), arm_r=(150, 160), legs='hang', head=6),
         expr=dict(mouth='grin', look=(0.0, 0.2)), cap=True).build()
    Daan('Daan', pose=dict(loc=(-0.08, -0.08, 0.0), arm_r='up', arm_l='down', head=12),
         expr=dict(mouth='grin', brows='up', look=(0.2, 0.35)), cap=True).build()
    for i, (x, y) in enumerate(((-0.45, -0.32), (-0.12, -0.35), (0.25, -0.33), (0.5, -0.3))):
        PS.tuft(f'Pol{i}', x, y, h=4.0, w=7, color='#5f9a3f', seed=i)
    V.cam((0.0, -0.68, 0.08), (0.0, 0.0, 0.14), lens=36, fstop=8.0, focus=(0.0, -0.02, 0.12))
    K.render(out)
