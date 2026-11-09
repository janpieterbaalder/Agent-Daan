"""p. 26-27: Nu is het bedtijd. Welterusten, agent Daan. Welterusten, Joep.

Nacht in de kinderkamer. Links in bed ligt Daan te slapen onder de lappendeken, Joep in zijn arm; de pet
hangt aan het bed, het nachtlampje gloeit. Rechts het raam met maan en sterren en een rustige, donkere
wand voor de tekst."""
import math
from lib import core as K, papierset as PS, papierscene as V
from lib.papierpop import Daan, Joep, daan_cap

CM = 0.01


def main(out, opts):
    V.setup(opts, night=True)
    info = PS.bedroom(night=True, bed_x=-0.16, window_x=0.0, y_wall=0.16)
    yb = info['bed_y']
    bx = -0.16
    # Daan ligt (hoofd links op het kussen), deken eroverheen
    d = Daan('Daan', pose=dict(loc=(bx + 0.017, yb - 0.017, 0.115), arm_l='down', arm_r='hug', head=0),
             expr=dict(mouth='smile', eyes='closed'), cap=False, outfit='pyjama')
    V.lie(d.build(), -90)
    j = Joep('Joep', pose=dict(loc=(bx - 0.01, yb - 0.0185, 0.146), legs='stand', head=0),
             expr=dict(mouth='smile', eyes='closed'), cap=False)
    V.lie(j.build(), -90)
    kinds = [('stippen', '#4f6aa8', '#7f95c8'), ('ruit', '#8a5a8a', '#b48ab4'), ('linnen', '#a89a6a', None),
             ('strepen', '#4f7a5a', '#7fa08a'), ('brei', '#6a4f98', '#56407e')]
    deken = PS.chaikin(PS.np.array([(-5.5, 0.0), (13.5, 0.0), (13.5, 6.4), (-5.5, 6.8)]), 2)
    PS.card('Deken', deken + PS.np.array([bx * 100, 8.0]), '#4f6aa8', yb - 0.02, paper='stippen', col2='#7f95c8')
    for i in range(6):
        for k, zz in enumerate((9.7, 12.7)):
            pk, col, c2 = kinds[(i + 2 * k) % len(kinds)]
            PS.card(f'Dekenlap{i}{k}', PS.rrect(bx * 100 - 3.2 + i * 2.95, zz, 2.8, 2.8, 0.3), col, yb - 0.0215,
                    paper=pk, col2=c2)
    PS.card('Dekenrand', PS.rrect(bx * 100 + 4.0, 14.4, 19.2, 0.8, 0.3), '#c9cde0', yb - 0.022, paper='crepe')
    # pet aan het hoofdeind
    px, py, pz = info['post']
    hook = K.empty('Pethaak', (px + 0.004, py - 0.006, pz - 0.012))
    daan_cap('Pet', hook, (0, 0), angle=-14, layer=0)
    V.cam((0.0, -0.8, 0.14), (0.0, 0.0, 0.135), lens=38, fstop=8.0, focus=(bx, yb - 0.02, 0.11))
    K.render(out)
