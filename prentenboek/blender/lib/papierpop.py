"""Papieren figuurtjes voor de kijkdoos: Daan, Joep, de bakker en de twee boeven.

Elke figuur is een stapel uitgeknipte stukjes papier (ontworpen in cm, vooraanzicht), elk van een eigen
papiersoort: huid van aquarelpapier, blosjes van zijdepapier, haar van crêpepapier, kleding met
linnenreliëf of bedrukt papier (strepen, breisel, boerenbont), ster en schildje van goudfolie.

Pose: loc (m), yaw (graden), arm_l / arm_r (naam uit POSES of (bovenarm, onderarm) als richting in
graden: 0 = omlaag, 90 = opzij, 180 = omhoog, negatief = naar binnen), legs ('stand', 'walk', 'sit',
'hang'), head (kanteling). Gezicht: mouth ('smile', 'grin', 'o', 'sad', 'flat'), eyes ('open', 'closed',
'happy'), brows ('none', 'up', 'worried', 'cross'), look (dx, dy) in cm.
"""
import math
import numpy as np
from . import core as K
from .papier import (piece, group, circle, ellipse, rrect, star, rotate, chaikin, strip, arc_pts, radial_union,
                     scallop, CM)

SKIN = '#f6cfb4'
BLACK = '#26262b'
WHITE = '#fbf8f1'
CHEEK = '#f49a9a'
LIP = '#b8323c'
BLOND = '#f0c040'
BLOND2 = '#c98e22'
GOLD = '#e9b23a'

POSES = {
    'down': (8, 4), 'wave': (115, 170), 'up': (150, 165), 'cheer': (135, 160), 'hip': (40, -55),
    'point': (82, 86), 'forward': (35, -25), 'hold': (25, -75), 'salute': (162, 292), 'stop': (95, 150),
    'out': (55, 58), 'hug': (20, -95),
}


def _arm_angles(a):
    return POSES[a] if isinstance(a, str) else a


def irregular(cx, cy, r, n, rng, k=0.35):
    """Grillig vormpje (chocoladestukje, kruimel)."""
    t = np.sort(rng.uniform(0, 2 * math.pi, n))
    rr = r * (1 + rng.uniform(-k, k, n))
    return chaikin(np.stack([cx + rr * np.cos(t), cy + rr * np.sin(t)], 1), 1)


class Figuur:
    def __init__(self, name, pose=None, expr=None):
        self.name = name
        self.p = dict(loc=(0, 0, 0), yaw=0.0, arm_l='down', arm_r='down', legs='stand', head=0.0, scale=1.0)
        self.p.update(pose or {})
        self.e = dict(mouth='smile', eyes='open', brows='none', look=(0.0, 0.0))
        self.e.update(expr or {})

    def _root(self):
        p = self.p
        r = K.empty(self.name, tuple(p['loc']), (0, 0, math.radians(p['yaw'])), p['scale'])
        self.root = r
        self.hands = {}
        return r

    def arm(self, side, pivot, L1, L2, w, sleeve, cuff, hand, layer, hand_r=0.62, paper='linnen', col2=None):
        a, f = _arm_angles(self.p['arm_l' if side < 0 else 'arm_r'])
        b = f - a
        sh = group(f'{self.name}_schouder{side}', self.root, pivot, angle=a if side < 0 else -a)
        n = self.name + f'_arm{side}'
        piece(n + '_boven', rrect(0, -L1 / 2 + 0.25, w, L1 + 0.7, w / 2), sleeve, sh, layer, paper=paper, col2=col2)
        el = group(f'{self.name}_elleboog{side}', sh, (0, -L1), angle=b if side < 0 else -b)
        piece(n + '_onder', rrect(0, -L2 / 2 + 0.1, w * 0.95, L2 + 0.55, w / 2), sleeve, el, layer + 0.3, paper=paper,
              col2=col2)
        if cuff:
            piece(n + '_manchet', rrect(0, -L2 + 0.05, w * 1.02, 0.42, 0.15), cuff, el, layer + 0.6, paper='linnen')
        hg = group(f'{self.name}_hand{side}', el, (0, -L2 - hand_r * 0.55))
        piece(n + '_hand', circle(0, 0, hand_r), hand, hg, layer + 0.8, paper='aquarel')
        self.hands[side] = hg
        return el

    def face(self, parent, cx, cy, s, layer, eye_dx=1.05, eye_dy=0.15, eye=(0.36, 0.46), cheek=0.55,
             nose=(0.32, 0.27), nose_col='#eaa98e', mouth_dy=-1.05, mouth_w=0.6, brow_col='#c49a5c', cheeks=True,
             eye_col=BLACK):
        e = self.e
        lx, ly = e['look']
        n = self.name
        ex, ey = eye_dx * s, eye_dy * s
        for k, sx in enumerate((-1, 1)):
            if e['eyes'] == 'open':
                piece(f'{n}_oog{k}', ellipse(cx + sx * ex + lx, cy + ey + ly, eye[0] * s, eye[1] * s), eye_col, parent,
                      layer, edge=eye_col, paper='glans')
                piece(f'{n}_glim{k}', circle(cx + sx * ex + lx + 0.1 * s, cy + ey + ly + 0.15 * s, 0.11 * s, 16), WHITE,
                      parent, layer + 0.6, edge=WHITE, paper='glans')
            else:
                k2 = -1 if e['eyes'] == 'closed' else 1
                pts = [(cx + sx * ex + t * 0.38 * s, cy + ey + k2 * 0.18 * s * (1 - t * t)) for t in np.linspace(-1, 1, 7)]
                piece(f'{n}_ooglijn{k}', strip(pts, 0.14 * s), BLACK, parent, layer, edge=BLACK, paper='glans')
            if cheeks:
                piece(f'{n}_wang{k}', circle(cx + sx * (ex + 0.62 * s), cy + ey - 0.75 * s, cheek * s), CHEEK, parent,
                      layer - 0.4, paper='zijde')
            if e['brows'] != 'none':
                tilt = {'up': 0, 'worried': 0.22, 'cross': -0.22}[e['brows']] * sx
                yb = cy + ey + (0.75 if e['brows'] in ('up', 'worried') else 0.64) * s
                pts = [(cx + sx * ex + t * 0.36 * s, yb + 0.08 * s * (1 - t * t) - tilt * t * s) for t in
                       np.linspace(-1, 1, 7)]
                piece(f'{n}_wenkbrauw{k}', strip(pts, 0.13 * s), brow_col, parent, layer, edge=brow_col, paper='crepe')
        if nose:
            piece(f'{n}_neus', ellipse(cx, cy + ey - 0.5 * s, nose[0] * s, nose[1] * s), nose_col, parent, layer,
                  paper='aquarel')
        my = cy + mouth_dy * s
        m = e['mouth']
        mw = mouth_w * s
        if m in ('smile', 'sad', 'flat'):
            k = {'smile': 1, 'sad': -1, 'flat': 0}[m]
            pts = [(cx + t * mw, my - k * 0.28 * s * (1 - t * t)) for t in np.linspace(-1, 1, 9)]
            piece(f'{n}_mond', strip(pts, 0.15 * s), LIP, parent, layer, edge=LIP, paper='glans')
        elif m in ('grin', 'open'):
            hh = (0.55 if m == 'grin' else 0.7) * s
            ww = mw * (1.0 if m == 'grin' else 0.75)
            top = [(cx + x, my + 0.1 * s - 0.08 * s * (x / ww) ** 2) for x in np.linspace(ww, -ww, 9)]
            bot = [(cx - ww * math.cos(t), my + 0.1 * s - hh * math.sin(t)) for t in np.linspace(0, math.pi, 13)[1:-1]]
            piece(f'{n}_mond', np.array(top + bot), '#7a1f2b', parent, layer, edge='#7a1f2b', paper='glans')
            piece(f'{n}_tong', ellipse(cx, my + 0.1 * s - hh * 0.72, ww * 0.5, hh * 0.25), '#f08a98', parent,
                  layer + 0.3, paper='aquarel')
        elif m == 'o':
            piece(f'{n}_mond', ellipse(cx, my, 0.24 * s, 0.32 * s), '#7a1f2b', parent, layer, edge='#7a1f2b',
                  paper='glans')


# ------------------------------------------------------------------ Daan
def daan_cap(n, parent, pivot=(0, 0), angle=0.0, layer=7.5):
    """Politiepet van Daan (linnen bol, glanzende klep, goudfolie schildje); ook los te gebruiken."""
    cg = group(n, parent, pivot, angle=angle)
    crown = chaikin(np.array([(-3.0, 0.0), (-3.55, 1.0), (-2.6, 1.75), (0, 2.0), (2.6, 1.75), (3.55, 1.0),
                              (3.0, 0.0)]), 3)
    piece(f'{n}bol', crown, '#1d2858', cg, layer, paper='linnen')
    piece(f'{n}band', rrect(0, 0.0, 6.2, 0.8, 0.3), BLACK, cg, layer + 0.5, paper='glans')
    visor = chaikin(np.array([(-3.0, -0.3), (3.0, -0.3), (2.4, -0.85), (0, -1.05), (-2.4, -0.85)]), 3)
    piece(f'{n}klep', visor, '#151519', cg, layer + 0.9, paper='glans')
    sh = chaikin(np.array([(-0.45, 1.45), (0.45, 1.45), (0.45, 0.85), (0, 0.45), (-0.45, 0.85)]), 2)
    piece(f'{n}schild', sh, GOLD, cg, layer + 1.0, paper='folie')
    return cg


class Daan(Figuur):
    """Daan (ca. 14 cm met pet): blond crêpehaar, donkerblauw linnen pakje, goudfolie ster, pet met schildje."""

    def __init__(self, name='Daan', pose=None, expr=None, cap=True, pyjama=False, outfit=None):
        Figuur.__init__(self, name, pose, expr)
        self.cap = cap
        self.outfit = outfit or ('pyjama' if pyjama else 'uniform')
        self.pyjama = self.outfit == 'pyjama'

    def build(self):
        r = self._root()
        n, p = self.name, self.p
        NAVY, NAVY2, NAVY_D = '#1c2a66', '#2f4596', '#15204f'
        of = self.outfit
        shirt = {'pyjama': '#9cc8e8', 'casual': '#d8443b'}.get(of, NAVY)
        pants = {'pyjama': '#9cc8e8', 'casual': '#3f63a0'}.get(of, NAVY_D)
        light = {'pyjama': '#e3f1fa', 'casual': '#f3e6cf'}.get(of, NAVY2)
        cloth = 'stippen' if self.pyjama else 'linnen'
        shoe = {'pyjama': SKIN, 'casual': '#f4f1ea'}.get(of, BLACK)
        shoe_p = {'pyjama': 'aquarel', 'casual': 'linnen'}.get(of, 'glans')
        legs = p['legs']
        for k, sx in enumerate((-1, 1)):
            hp = group(f'{n}_heup{k}', r, (sx * 0.85, 3.4), angle={'walk': sx * 9}.get(legs, 0))
            if legs == 'sit':
                piece(f'{n}_been{k}', rrect(0, -0.9, 1.6, 2.0, 0.55), pants, hp, 1, paper=cloth, col2='#ffffff')
                piece(f'{n}_zool{k}', ellipse(0.0, -2.0, 0.8, 0.95), shoe, hp, 2, paper=shoe_p)
                piece(f'{n}_zoolrand{k}', ellipse(0.0, -2.0, 0.55, 0.7), '#6b6b70' if not self.pyjama else '#f0b9a0',
                      hp, 2.3, paper='kraft')
            else:
                piece(f'{n}_been{k}', rrect(0, -1.45, 1.6, 3.4, 0.55), pants, hp, 1, paper=cloth, col2='#ffffff')
                piece(f'{n}_schoen{k}', ellipse(sx * 0.18, -2.95, 1.05, 0.58), shoe, hp, 2, paper=shoe_p)
                if of == 'casual':
                    piece(f'{n}_schoenzool{k}', rrect(sx * 0.18, -3.42, 2.0, 0.32, 0.12), '#d8443b', hp, 2.3,
                          paper='karton')
                    piece(f'{n}_omslag{k}', rrect(0, -2.25, 1.75, 0.5, 0.2), '#6f8fc4', hp, 1.6, paper='linnen')
        body = chaikin(np.array([(-2.5, 3.0), (2.5, 3.0), (2.25, 7.45), (-2.25, 7.45)]), 3)
        piece(f'{n}_romp', body, shirt, r, 2, paper=cloth, col2='#ffffff')
        if of == 'uniform':
            piece(f'{n}_riem', rrect(0, 3.75, 5.0, 0.58, 0.2), BLACK, r, 3, paper='glans')
            piece(f'{n}_gesp', rrect(0, 3.75, 0.95, 0.68, 0.15), '#c9ccd3', r, 3.6, paper='folie')
            piece(f'{n}_gespgat', rrect(0, 3.75, 0.5, 0.3, 0.08), BLACK, r, 4.0, paper='glans')
            piece(f'{n}_beleg', rrect(0, 5.7, 0.32, 3.2, 0.1), NAVY_D, r, 3, paper='linnen')
            for i, y in enumerate((4.6, 5.6, 6.6)):
                piece(f'{n}_knoop{i}', circle(0, y, 0.17, 16), '#e8eaee', r, 3.6, paper='glans')
            for k, sx in enumerate((-1, 1)):
                piece(f'{n}_zak{k}', rrect(sx * 1.2, 5.95, 1.3, 1.1, 0.2), light, r, 3, paper='linnen')
                piece(f'{n}_klep{k}', rrect(sx * 1.2, 6.5, 1.45, 0.42, 0.15), light, r, 3.5, paper='linnen')
            piece(f'{n}_ster', star(1.3, 7.05, 0.45, 0.19), GOLD, r, 3.8, paper='folie')
            for k, sx in enumerate((-1, 1)):
                piece(f'{n}_kraag{k}', chaikin(np.array([(sx * 0.15, 7.5), (sx * 1.15, 7.55), (sx * 0.4, 6.75)]), 2),
                      light, r, 3.2, paper='linnen')
        elif of == 'casual':
            piece(f'{n}_kraag', strip([(-1.2, 7.45), (0, 7.05), (1.2, 7.45)], 0.42), light, r, 3.2, paper='linnen')
            ban = [(-1.25, 5.6), (-0.6, 4.95), (0.35, 4.95), (1.1, 5.5)]
            piece(f'{n}_banaan', strip(ban, 0.62), '#f6d34a', r, 3.2, paper='aquarel')
            piece(f'{n}_banaantip', circle(1.18, 5.62, 0.16, 12), '#6b4a2a', r, 3.5, paper='kraft')
        else:
            piece(f'{n}_kraag', rrect(0, 7.35, 2.6, 0.5, 0.2), '#e3f1fa', r, 3.2, paper='linnen')
        for sx in (-1, 1):
            self.arm(sx, (sx * 2.15, 7.0), 1.75, 1.6, 1.25, shirt, None if of == 'casual' else light, SKIN, 3.2,
                     paper=cloth, col2='#ffffff')
        hg = group(f'{n}_hoofd', r, (0, 7.4), angle=-p['head'])
        piece(f'{n}_nek', rrect(0, 0.2, 1.1, 1.2, 0.3), SKIN, hg, 1.5, paper='aquarel')
        for k, sx in enumerate((-1, 1)):
            piece(f'{n}_oor{k}', circle(sx * 2.85, 2.5, 0.68), SKIN, hg, 4, paper='aquarel')
            piece(f'{n}_oorbinnen{k}', circle(sx * 2.92, 2.5, 0.36), '#f0b39e', hg, 4.2, paper='aquarel')
        piece(f'{n}_kop', circle(0, 2.8, 2.9, 64), SKIN, hg, 5, paper='aquarel')
        self.face(hg, 0, 2.75, 1.0, 6.4)
        self._hair(hg)
        if self.cap:
            daan_cap(f'{n}_pet', hg, (0, 4.45 + p.get('cap_lift', 0.0)), p.get('cap_tilt', -4))
        return r

    def _hair(self, hg):
        n = self.name
        if self.cap:
            for k, sx in enumerate((-1, 1)):
                tuft = np.array([(sx * 2.15, 4.15), (sx * 3.05, 3.75), (sx * 3.3, 3.05), (sx * 3.0, 3.3),
                                 (sx * 2.95, 2.8), (sx * 2.62, 3.35), (sx * 2.35, 3.6)])
                piece(f'{n}_pluk{k}', chaikin(tuft, 2), BLOND, hg, 5.6, paper='crepe')
            return
        # haar met volume: achterlaag rond het hoofd tot boven de oren, voorlaag met een pony van drie
        # ronde lokken die naar rechts vallen; de pony eindigt net boven de wenkbrauwen
        back = list(arc_pts(0, 3.0, 3.45, -14, 194, 48))
        piece(f'{n}_haarachter', chaikin(np.array(back), 1), BLOND2, hg, 4.6, paper='crepe')
        top = list(arc_pts(0, 2.95, 3.3, -6, 186, 44))
        fr = [(-3.28, 2.6), (-2.75, 2.75), (-2.45, 3.5)]
        for (a, b, tip) in ((-2.45, -0.75, 3.75), (-0.75, 1.05, 3.95), (1.05, 2.75, 3.9)):
            fr += [(a + 0.45 * (b - a), tip + 0.05), (a + 0.8 * (b - a), tip - 0.05), (b, tip + 0.55)]
        fr += [(3.0, 3.2), (3.28, 2.6)]
        piece(f'{n}_haar', chaikin(np.array(top + fr), 2), BLOND, hg, 5.8, paper='crepe', edge='#fbe6a6')
        piece(f'{n}_kuifje', strip([(0.2, 6.15), (0.65, 6.75), (1.25, 6.85)], 0.55), BLOND, hg, 5.7, paper='crepe')


# ------------------------------------------------------------------ Joep
class Joep(Figuur):
    """Joep (ca. 8 cm): aapje van kraftpapier met een crème gezichtje van aquarelpapier, krulstaart, petje."""

    def __init__(self, name='Joep', pose=None, expr=None, cap=True):
        Figuur.__init__(self, name, pose, expr)
        self.cap = cap
        if 'scale' not in (pose or {}):
            self.p['scale'] = 0.72      # knuffelformaat naast Daan

    def build(self):
        r = self._root()
        n, p = self.name, self.p
        BR, BR2, CR = '#a3632f', '#7e4722', '#f1d6a8'
        tail = [(1.1, 1.6), (2.4, 1.3), (3.1, 2.1), (2.9, 3.0), (2.2, 3.1), (2.0, 2.5), (2.5, 2.3)]
        piece(f'{n}_staart', strip(tail, 0.42), BR2, r, 0.5, paper='kraft')
        legs = p['legs']
        for k, sx in enumerate((-1, 1)):
            if legs == 'sit':
                L = [(sx * 0.7, 1.0), (sx * 1.5, 0.35), (sx * 2.2, 0.2)]
                piece(f'{n}_been{k}', strip(L, 0.62), BR, r, 1.5, paper='kraft')
                piece(f'{n}_voet{k}', ellipse(sx * 2.45, 0.25, 0.6, 0.45), CR, r, 2.2, paper='aquarel')
            else:
                ang = {'walk': sx * 10, 'hang': sx * 6}.get(legs, 0)
                L = 2.8 if legs == 'hang' else 1.9
                hp = group(f'{n}_heup{k}', r, (sx * 0.65, 1.1), angle=ang)
                piece(f'{n}_been{k}', rrect(0, -L / 2 + 0.45, 0.62, L, 0.3), BR, hp, 1.5, paper='kraft')
                piece(f'{n}_voet{k}', ellipse(sx * 0.12, -L + 0.45, 0.6, 0.42), CR, hp, 2.2, paper='aquarel')
        piece(f'{n}_lijf', ellipse(0, 2.35, 1.55, 1.9), BR, r, 2, paper='kraft')
        piece(f'{n}_buik', ellipse(0, 2.15, 0.95, 1.2), CR, r, 2.6, paper='aquarel')
        for sx in (-1, 1):
            self.arm(sx, (sx * 1.2, 3.55), 1.45, 1.45, 0.55, BR, None, CR, 3.0, hand_r=0.42, paper='kraft')
        hg = group(f'{n}_hoofd', r, (0, 3.9), angle=-p['head'])
        for k, sx in enumerate((-1, 1)):
            piece(f'{n}_oor{k}', circle(sx * 1.95, 2.0, 0.78), BR, hg, 3.6, paper='kraft')
            piece(f'{n}_oorbinnen{k}', circle(sx * 2.0, 2.0, 0.45), CR, hg, 3.8, paper='aquarel')
        piece(f'{n}_kop', circle(0, 1.85, 1.95, 56), BR, hg, 4, paper='kraft')
        face = radial_union((0, 1.55), [(-0.6, 2.05, 0.82, 0.82), (0.6, 2.05, 0.82, 0.82), (0, 1.05, 1.15, 0.78)])
        piece(f'{n}_gezicht', chaikin(face, 1), CR, hg, 4.6, paper='aquarel')
        piece(f'{n}_snuit', ellipse(0, 0.95, 0.85, 0.55), '#f7e2bd', hg, 5.0, paper='aquarel')
        self.face(hg, 0, 1.75, 0.55, 5.6, eye_dx=1.1, eye_dy=0.5, eye=(0.42, 0.5), cheeks=False,
                  nose=(0.32, 0.2), nose_col='#4a2a1a', mouth_dy=-1.55, mouth_w=0.75)
        if self.cap:
            cg = group(f'{n}_pet', hg, (0.15, 3.45), angle=p.get('cap_tilt', 12))
            crown = chaikin(np.array([(-1.6, 0.0), (-1.9, 0.55), (-1.4, 0.95), (0, 1.1), (1.4, 0.95), (1.9, 0.55),
                                      (1.6, 0.0)]), 3)
            piece(f'{n}_petbol', crown, '#1d2858', cg, 6.5, paper='linnen')
            piece(f'{n}_petband', rrect(0, 0.0, 3.3, 0.45, 0.18), BLACK, cg, 7, paper='glans')
            visor = chaikin(np.array([(-1.6, -0.18), (1.6, -0.18), (1.3, -0.48), (0, -0.6), (-1.3, -0.48)]), 3)
            piece(f'{n}_klep', visor, '#151519', cg, 7.3, paper='glans')
            piece(f'{n}_schild', star(0, 0.62, 0.3, 0.13), GOLD, cg, 7.5, paper='folie')
        return r


# ------------------------------------------------------------------ bijrollen
class Mens(Figuur):
    """'bakker', 'lang' (lange boef) of 'dik' (dikke boef). mask_up: masker op het voorhoofd;
    chef: koksmuts (ook voor de boeven op het feest)."""

    SPEC = dict(
        bakker=dict(leg=(0.95, 5.2, 1.85), shoe='#4a3426', pants='#6a6c78', body=('round', 4.3, 4.6, 9.6),
                    shirt=WHITE, head=(15.6, 2.65), arm=(3.2, 2.6, 1.5), skin='#f2c6a6', hair='#7a5232'),
        lang=dict(leg=(0.8, 8.6, 1.4), shoe='#5a3b24', pants='#2c2c33', body=('slim', 1.95, 3.6, 11.9),
                  shirt='#efe9dc', head=(17.9, 2.35), arm=(3.3, 3.1, 1.15), skin='#f0c5a5', hair='#3b2a20',
                  beanie=('#3a3d48', '#2a2c34', '#3f7a4a'), scarf='#3f7a4a'),
        dik=dict(leg=(1.05, 4.0, 2.0), shoe='#5a3b24', pants='#2c2c33', body=('round', 4.0, 3.9, 7.7),
                 shirt='#efe9dc', head=(12.85, 2.7), arm=(2.5, 2.3, 1.45), skin='#f2c2a0', hair='#7a3f22',
                 beanie=('#c24242', '#a53434', '#efe3c0'), scarf='#c63b33'),
    )

    def __init__(self, name, kind='bakker', pose=None, expr=None, mask_up=False, chef=False):
        Figuur.__init__(self, name, pose, expr)
        self.kind = kind
        self.mask_up = mask_up
        self.chef = chef or kind == 'bakker'

    def build(self):
        r = self._root()
        n, p = self.name, self.p
        sp = self.SPEC[self.kind]
        thief = self.kind != 'bakker'
        lx, lh, lw = sp['leg']
        legs = p['legs']
        for k, sx in enumerate((-1, 1)):
            hp = group(f'{n}_heup{k}', r, (sx * lx, lh), angle={'walk': sx * 9}.get(legs, 0))
            if legs == 'sit':
                # zittend in het gras: knieën en schoenzolen naar de camera, onder de buik
                kind_, bw_, bh_, by_ = sp['body']
                yb_ = by_ - bh_ + 0.7 - lh
                piece(f'{n}_knie{k}', ellipse(sx * 0.5, yb_ + 0.4, lw * 0.75, lw * 0.62), sp['pants'], hp, 3.6,
                      paper='linnen')
                piece(f'{n}_zool{k}', ellipse(sx * 0.9, yb_ - 0.3, lw * 0.55, lw * 0.68), sp['shoe'], hp, 3.9,
                      paper='kraft')
            else:
                piece(f'{n}_been{k}', rrect(0, -lh / 2 + 0.3, lw, lh + 0.4, 0.6), sp['pants'], hp, 1, paper='linnen')
                piece(f'{n}_schoen{k}', ellipse(sx * 0.25, -lh + 0.45, lw * 0.75, 0.62), sp['shoe'], hp, 2,
                      paper='kraft')
        kind, bw, bh, by = sp['body']
        if kind == 'round':
            body = ellipse(0, by, bw, bh, 64)
        else:
            body = chaikin(np.array([(-bw, by - bh), (bw, by - bh), (bw * 1.08, by + bh), (-bw * 1.08, by + bh)]), 3)
        top = by + bh
        if thief:
            piece(f'{n}_romp', body, sp['shirt'], r, 2, paper='strepen', col2='#2a2b31')
            piece(f'{n}_riem', rrect(0, by - bh + 0.35, 2 * bw * (0.55 if kind == 'round' else 1.0), 0.45, 0.15),
                  '#5a3b24', r, 2.6, paper='kraft')
            piece(f'{n}_sjaal', rrect(0, top - 0.1, 2.6, 0.7, 0.3), sp['scarf'], r, 3.2, paper='crepe')
        else:
            piece(f'{n}_romp', body, sp['shirt'], r, 2, paper='linnen')
            apron = chaikin(np.array([(-2.4, by - 3.6), (2.4, by - 3.6), (2.6, by + 2.2), (-2.6, by + 2.2)]), 3)
            piece(f'{n}_schort', apron, '#d9443a', r, 2.6, paper='ruit', col2='#fbf8f1')
            piece(f'{n}_schortzak', rrect(0, by - 1.6, 2.2, 1.2, 0.3), '#fbf8f1', r, 3.0, paper='linnen')
            piece(f'{n}_sjaal', rrect(0, top - 0.25, 2.8, 0.75, 0.3), '#c63b33', r, 3.2, paper='crepe')
            piece(f'{n}_sjaalpunt', chaikin(np.array([(-0.6, top - 0.5), (0.6, top - 0.5), (0, top - 1.6)]), 2),
                  '#c63b33', r, 3.3, paper='crepe')
        L1, L2, aw = sp['arm']
        for sx in (-1, 1):
            shx = (bw * (0.62 if kind == 'round' else 1.0) + aw * 0.35)
            self.arm(sx, (sx * shx, top - 0.6), L1, L2, aw, sp['shirt'], None, sp['skin'], 3.4, hand_r=0.68,
                     paper='strepen' if thief else 'linnen', col2='#2a2b31' if thief else None)
        hy, hr = sp['head']
        hg = group(f'{n}_hoofd', r, (0, top), angle=-p['head'])
        rel = hy - top
        piece(f'{n}_nek', rrect(0, 0.3, 1.2, 1.4, 0.3), sp['skin'], hg, 1.5, paper='aquarel')
        for k, sx in enumerate((-1, 1)):
            piece(f'{n}_oor{k}', circle(sx * hr * 0.98, rel - 0.2, 0.62), sp['skin'], hg, 4, paper='aquarel')
        if self.kind == 'lang':
            piece(f'{n}_kop', ellipse(0, rel, hr * 0.95, hr * 1.12, 64), sp['skin'], hg, 5, paper='aquarel')
        else:
            piece(f'{n}_kop', circle(0, rel, hr, 64), sp['skin'], hg, 5, paper='aquarel')
        for k, sx in enumerate((-1, 1)):
            tuft = np.array([(sx * hr * 0.75, rel + 0.9), (sx * hr * 1.05, rel + 0.5), (sx * hr * 1.08, rel - 0.4),
                             (sx * hr * 0.92, rel - 0.1), (sx * hr * 0.8, rel + 0.3)])
            piece(f'{n}_haar{k}', chaikin(tuft, 2), sp['hair'], hg, 5.6, paper='crepe')
        mask_y = rel + 0.3 + (1.15 if self.mask_up else 0.0)
        if thief:
            piece(f'{n}_masker', rrect(0, mask_y, hr * 2.05, 0.95, 0.4), BLACK, hg, 6.0, paper='glans')
            if not self.mask_up:
                for k, sx in enumerate((-1, 1)):
                    piece(f'{n}_maskeroog{k}', ellipse(sx * 0.85, mask_y, 0.42, 0.32), WHITE, hg, 6.3, paper='glans')
        nose = (0.42, 0.36) if self.kind != 'lang' else (0.36, 0.7)
        ncol = '#e89a86' if self.kind != 'dik' else '#e2786c'
        self.face(hg, 0, rel - 0.05, 0.92, 6.6, eye_dx=0.92, eye_dy=0.35, eye=(0.3, 0.36), cheek=0.5, nose=nose,
                  nose_col=ncol, mouth_dy=-1.3 if self.kind != 'lang' else -1.6, mouth_w=0.62, brow_col=sp['hair'])
        if self.kind == 'bakker':
            for k, sx in enumerate((-1, 1)):
                st = chaikin(np.array([(sx * 0.1, rel - 0.75), (sx * 1.3, rel - 0.85), (sx * 1.55, rel - 1.25),
                                       (sx * 0.9, rel - 1.15), (sx * 0.1, rel - 1.0)]), 2)
                piece(f'{n}_snor{k}', st, sp['hair'], hg, 7.2, paper='crepe')
        if self.chef:
            cg = group(f'{n}_muts', hg, (0, rel + hr * 0.62))
            puff = radial_union((0, 1.6), [(-1.5, 1.4, 1.3, 1.2), (1.5, 1.4, 1.3, 1.2), (0, 2.1, 1.5, 1.4),
                                           (-0.8, 2.6, 1.1, 1.0), (0.8, 2.6, 1.1, 1.0)])
            piece(f'{n}_mutsbol', chaikin(puff, 1), '#ffffff', cg, 7.5, paper='crepe')
            piece(f'{n}_mutsband', rrect(0, 0.3, hr * 1.9, 1.1, 0.3), '#f3eee4', cg, 7.8, paper='linnen')
        elif thief:
            c1, c2, rim = sp['beanie']
            cg = group(f'{n}_muts', hg, (0, rel + hr * 0.45))
            dome = np.array(list(arc_pts(0, 0.0, hr * 1.04, 0, 180, 32, ry=hr * 0.95)))
            piece(f'{n}_mutsbol', dome, c1, cg, 7.0, paper='brei', col2=c2)
            piece(f'{n}_mutsrand', rrect(0, 0.0, hr * 2.15, 0.85, 0.35), rim, cg, 7.4, paper='brei',
                  col2=rim if rim != '#efe3c0' else '#dccfa8')
            piece(f'{n}_bolletje', circle(0, hr * 0.95 + 0.35, 0.6), rim, cg, 7.2, paper='crepe')
        return r
