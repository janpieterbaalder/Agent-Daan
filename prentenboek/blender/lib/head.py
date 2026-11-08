"""Gestileerd kinderhoofd (Daan) en volwassen variant (bakker, boeven).

Eenheidscoördinaten: x naar rechts (linkerkant van het personage), -y is de voorkant van het gezicht,
z omhoog. Het hoofd-empty krijgt de schaal (meters per eenheid).
"""
import math
import numpy as np
from mathutils import Vector, Matrix
from . import core as K
from .core import gauss, smoothstep


def _n(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


DEFAULT = dict(
    scale=(1.0, 0.98, 1.06),
    cheek=0.19, cheek_pos=(0.66, -0.55, -0.45), cheek_sigma=0.44,
    eye_dir=(0.36, -0.9, 0.0), eye_r=0.255, eye_depth=0.6, socket=-0.05,
    nose=0.10, nose_pos=(0, -1, -0.225), nose_sigma=0.072,
    mouth_z=-0.455, mouth_w=0.2, mouth_curve=1.6, chin=0.04,
    brow=0.03, jaw=0.05, ear_size=1.5, ear_out=0.5, flat=0.035,
    adult=False,
)


class Head:
    def __init__(self, name='Hoofd', p=None, expr=None, res=(256, 140)):
        self.name = name
        self.p = dict(DEFAULT)
        self.p.update(p or {})
        self.e = dict(mouth='smile', smile=1.0, open=0.0, lids=1.0, lower=0.0, look=(0, -1, 0), brow_up=0.0,
                      squint=0.12)
        self.e.update(expr or {})
        self.res = res

    # ------------------------------------------------------------ vorm
    def mouth_field(self, D):
        """Afstand tot de mondlijn (in richtingsruimte) en eindvervaging."""
        p, e = self.p, self.e
        x, z = D[:, 0], D[:, 2]
        curve = p['mouth_curve'] * e['smile'] - 0.6 * max(0.0, -e['smile'])
        zm = p['mouth_z'] + curve * x * x
        w = p['mouth_w'] * (1 + 0.15 * e['smile'])
        fade = 1 - smoothstep(w * 0.7, w * 1.05, np.abs(x))
        d = np.abs(z - zm)
        front = smoothstep(-0.55, -0.8, D[:, 1])
        return d, fade * front, zm

    def shape(self, D):
        p, e = self.p, self.e
        P = D * np.asarray(p['scale'])
        add = np.zeros(len(D))
        add += 0.05 * gauss(D, (0, 0.45, 0.8), 0.6)
        for s in (-1, 1):
            cp = np.array(p['cheek_pos']) * (s, 1, 1)
            add += p['cheek'] * gauss(D, cp, p['cheek_sigma'])
            add -= p['jaw'] * gauss(D, (0.6 * s, -0.2, -0.95), 0.32)
            ed = np.array(p['eye_dir']) * (s, 1, 1)
            add -= p['socket'] * gauss(D, ed, 0.2)
            add += p['brow'] * gauss(D, ed + np.array([0, 0.02, 0.3]), 0.17)
            add -= 0.05 * gauss(D, (1.0 * s, 0.05, -0.05), 0.22)
            # mondhoekjes
            add += 0.028 * e['smile'] * gauss(D, (0.24 * s, -0.92, p['mouth_z'] + 0.06), 0.06)
        # gezicht iets platter van voren
        add -= p['flat'] * gauss(D, (0, -1, 0.1), 0.42)
        add -= 0.07 * gauss(D, (0, -0.3, -1), 0.38)
        add -= 0.05 * gauss(D, (0, 0.75, -0.6), 0.3)
        add += p['chin'] * gauss(D, (0, -0.85, -0.66), 0.13)
        # neus
        add += p['nose'] * gauss(D, p['nose_pos'], p['nose_sigma'])
        add += 0.012 * gauss(D, (0, -1, p['nose_pos'][2] + 0.12), 0.06)
        for s in (-1, 1):
            add += 0.018 * gauss(D, (0.075 * s, -0.97, p['nose_pos'][2] - 0.03), 0.04)
        add += 0.022 * gauss(D, (0, -1, -0.36), 0.075)
        # mond
        d, fade, zm = self.mouth_field(D)
        add -= 0.04 * np.exp(-d * d / (2 * 0.010 ** 2)) * fade
        below = np.exp(-((D[:, 2] - (zm - 0.05)) ** 2) / (2 * 0.028 ** 2)) * fade
        add += 0.009 * below
        # open mond: holte
        op = e['open']
        if op > 0:
            cx, cz = 0.0, p['mouth_z'] - 0.02 - 0.03 * op
            kind = e['mouth']
            if kind == 'grin':
                ax, az = 0.1 + 0.06 * op, 0.022 + 0.07 * op
                cz = p['mouth_z'] - 0.015 - 0.035 * op
            elif kind == 'shout':
                ax, az = 0.085 + 0.05 * op, 0.05 + 0.1 * op
            else:
                ax, az = 0.05 + 0.03 * op, 0.05 + 0.065 * op
            zz = D[:, 2] - (p['mouth_curve'] * 0.5 * D[:, 0] ** 2 if kind == 'grin' else 0)
            r = np.sqrt(((D[:, 0] - cx) / ax) ** 2 + ((zz - cz) / az) ** 2)
            front = smoothstep(-0.6, -0.85, D[:, 1])
            hole = (1 - smoothstep(0.75, 1.0, r)) * front
            rim = np.exp(-((r - 1.05) ** 2) / (2 * 0.12 ** 2)) * front
            add -= 0.32 * hole
            add += 0.02 * rim
        P = P + D * add[:, None]
        self.add = add
        return P

    def surface(self, d):
        """Oppervlaktepunt en normaal in richting d (eenheidsruimte)."""
        d = _n(d)
        eps = 0.004
        a = np.cross(d, [0, 0, 1])
        if np.linalg.norm(a) < 1e-3:
            a = np.cross(d, [1, 0, 0])
        a = _n(a)
        b = _n(np.cross(d, a))
        D = np.array([d, _n(d + a * eps), _n(d + b * eps)])
        P = self.shape(D)
        nrm = _n(np.cross(P[1] - P[0], P[2] - P[0]))
        if np.dot(nrm, d) < 0:
            nrm = -nrm
        return P[0], nrm

    # ------------------------------------------------------------ kleur
    def paint(self, D):
        p, e = self.p, self.e
        col = np.ones((len(D), 3))

        def tint(w, c):
            c = np.asarray(c)
            col[:] = col * (1 - w[:, None]) + col * c[None, :] * w[:, None]

        for s in (-1, 1):
            tint(0.95 * gauss(D, (0.56 * s, -0.72, -0.3), 0.21), (1.0, 0.66, 0.62))
            ed = np.array(p['eye_dir']) * (s, 1, 1)
            tint(0.35 * gauss(D, ed + np.array([0, 0, -0.18]), 0.12), (0.97, 0.84, 0.84))
        tint(0.45 * gauss(D, p['nose_pos'], 0.07), (1.0, 0.8, 0.76))
        d, fade, zm = self.mouth_field(D)
        lip = np.exp(-d * d / (2 * 0.02 ** 2)) * fade
        lower = np.exp(-((D[:, 2] - (zm - 0.04)) ** 2) / (2 * 0.026 ** 2)) * fade
        tint(np.clip(0.55 * lip + 0.55 * lower, 0, 0.75), (0.93, 0.6, 0.58))
        if e['open'] > 0:
            depth = np.clip(-self.add / 0.32, 0, 1)
            tint(smoothstep(0.15, 0.6, depth), (0.36, 0.1, 0.12))
        if not p['adult'] and p.get('scalp', True):
            from .hair import scalp_mask
            tint(0.8 * scalp_mask(D), (1.0, 0.93, 0.78))
        # sproetjes
        rng = np.random.default_rng(7)
        if not p['adult']:
            for _ in range(26):
                s = rng.choice([-1, 1])
                c = np.array([s * rng.uniform(0.25, 0.62), -0.85, rng.uniform(-0.3, -0.05)])
                tint(0.28 * gauss(D, c, 0.012), (0.85, 0.62, 0.5))
        return col

    # ------------------------------------------------------------ opbouw
    def build(self, parent, mats, scale=0.13, loc=(0, 0, 0), rot=(0, 0, 0)):
        p, e = self.p, self.e
        root = K.empty(self.name, loc, rot, scale, parent)
        D, F = K.sph(*self.res)
        # bol met de polen op de z-as; dat is prima (boven onder het haar, onder in de hals)
        P = self.shape(D)
        col = self.paint(D)
        self.D, self.P, self.F = D, P, F
        self.skin = K.mesh_obj(self.name + '_huid', P, F, mats['face'], root,
                               attrs={'paint': ('POINT', col)})
        self.root = root
        self.eyes = []
        for s in (-1, 1):
            self._eye(s, mats)
        for s in (-1, 1):
            self._ear(s, mats)
        if e['open'] > 0:
            self._mouth_inside(mats)
        return root

    def _eye_frame(self, s):
        p = self.p
        ed = np.array(p['eye_dir']) * (s, 1, 1)
        sp, nrm = self.surface(ed)
        re = p['eye_r']
        c = sp - _n(ed) * re * p['eye_depth']
        fwd = _n(_n(ed) * 0.55 + np.array([0, -1, 0]) * 0.45)
        return c, fwd, re

    def _eye(self, s, mats):
        p, e = self.p, self.e
        c, fwd, re = self._eye_frame(s)
        look = _n(e['look'])
        # beide ogen kijken naar hetzelfde punt als look een punt is (len 4: x,y,z,1)
        if len(e['look']) == 4:
            tgt = np.array(e['look'][:3])
            look = _n(tgt - c)
        q = Vector((0, -1, 0)).rotation_difference(Vector(look))
        eb = K.blob(self.name + f'_oog{s}', (re, re, re), 2.0, (48, 32), mat=mats['eye'], parent=self.root,
                    loc=tuple(c))
        eb.rotation_mode = 'QUATERNION'
        eb.rotation_quaternion = q
        # oogbol in eenheidsmaat voor de iris-shader: schaal in het object
        me = eb.data
        V = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get('co', V)
        me.vertices.foreach_set('co', (V / re).astype(np.float32))
        eb.scale = (re, re, re)
        self.eyes.append(eb)
        # oogleden: bolschil om het oog
        up = np.array([0, 0, 1.0])
        right = _n(np.cross(fwd, up))
        up2 = _n(np.cross(right, fwd))
        M = np.stack([right, fwd, up2], 1)  # kolommen: x=rechts, y=voor, z=boven

        lid = e['lids']
        sq = e.get('squint', 0.0)
        AZ = 1.75
        # randen van de ooglidopening (amandel): boven daalt naar de hoeken, onder stijgt
        top0 = -0.8 + (1.44 - 0.2 * sq) * lid
        low0 = -0.72 + 0.3 * e.get('lower', 0) + 0.25 * sq
        e_top = lambda A: top0 - 0.42 * (A / 1.15) ** 2
        e_low = lambda A: low0 + 0.6 * (A / 1.15) ** 2

        def shell(upper, rr=1.03, nm='lid', thick=0.06):
            na, ne = 56, 18
            A = np.linspace(-AZ, AZ, na)
            T = np.linspace(0, 1, ne)
            AA, TT = np.meshgrid(A, T, indexing='ij')
            edge = e_top(AA) if upper else e_low(AA)
            end = 1.5 if upper else -1.5
            edge = np.clip(edge, -1.45, 1.45)
            EE = edge + (end - edge) * TT ** 1.3
            loc = np.stack([np.sin(AA) * np.cos(EE), np.cos(AA) * np.cos(EE), np.sin(EE)], -1).reshape(-1, 3)
            Pw = c + (loc * re * rr) @ M.T
            Ff = []
            for i in range(na - 1):
                for j in range(ne - 1):
                    q = (i * ne + j, (i + 1) * ne + j, (i + 1) * ne + j + 1, i * ne + j + 1)
                    Ff.append(q if upper else q[::-1])
            ob = K.mesh_obj(self.name + f'_{nm}{s}', Pw, Ff, mats['lid'], self.root)
            K.solidify(ob, thick * re, offset=1.0)
            K.subsurf(ob, 1)
            return ob

        shell(True, nm='bovenlid')
        shell(False, nm='onderlid', thick=0.045)
        # wimperlijn op de voorrand van het bovenlid
        A = np.linspace(-1.0, 1.0, 26)
        ed = e_top(A)
        pts = np.stack([np.sin(A) * np.cos(ed), np.cos(A) * np.cos(ed), np.sin(ed)], -1) * re * 1.06
        pts = c + pts @ M.T
        self.lash_pts = pts
        K.curve_tube(self.name + f'_wimperlijn{s}', pts, 0.006 * re / 0.2, mats['lash'], self.root)

    def _ear(self, s, mats):
        p = self.p
        sp, nrm = self.surface((1.0 * s, 0.02, -0.08))
        sz = p['ear_size']

        def deform(D, P):
            x = D[:, 0]
            # komvormig aan de buitenkant
            cav = gauss(D, (1, -0.15, 0.05), 0.5)
            P = P.copy()
            P[:, 0] -= 0.75 * cav * P[:, 0].clip(0, None)
            P[:, 0] += 0.03 * gauss(D, (0.6, -0.4, -0.3), 0.3)
            return P

        ear = K.blob(self.name + f'_oor{s}', (0.065 * sz, 0.14 * sz, 0.2 * sz), 2.2, (40, 28), deform=deform,
                     mat=mats['ear'], parent=self.root)
        # oor-lokaal: x naar buiten; links gespiegeld in de mesh zelf
        if s < 0:
            ear.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
            ear.data.flip_normals()
        ear.location = tuple(sp - nrm * 0.03 + np.array([0, 0.02, 0]))
        ear.rotation_euler = (0.12, 0, -s * p['ear_out'])
        self.ears = getattr(self, 'ears', []) + [ear]

    def _mouth_inside(self, mats):
        p, e = self.p, self.e
        cz = p['mouth_z'] - 0.02 - 0.03 * e['open']
        sp, nrm = self.surface((0, -1, cz))
        # tong
        tg = K.blob(self.name + '_tong', (0.07, 0.07, 0.035), 2.0, (32, 16), mat=mats['tongue'],
                    parent=self.root, loc=tuple(sp + np.array([0, 0.2, -0.06 * e['open'] - 0.02])))
        # boventandjes
        if e['mouth'] in ('grin', 'shout'):
            K.blob(self.name + '_tanden', (0.07, 0.03, 0.022), 3.0, (32, 16), mat=mats['teeth'], parent=self.root,
                   loc=tuple(sp + np.array([0, 0.1, 0.035 + 0.02 * e['open']])))

    # ------------------------------------------------------------ wenkbrauwen en wimpers (haar)
    def brows(self, mats, color_mat, density=1.0, length=0.07, rng=None):
        rng = rng or np.random.default_rng(3)
        strands = []
        for s in (-1, 1):
            ed = np.array(self.p['eye_dir']) * (s, 1, 1)
            tilt = self.e.get('brow_tilt', 0.0)  # + = sip (binnenkant omhoog), - = boos
            for i in range(int(70 * density)):
                t = rng.uniform(-1, 1)
                d = ed + np.array([s * t * 0.17, 0, 0.31 + 0.05 * (1 - t * t) + self.e['brow_up'] * 0.08 -
                                   tilt * 0.06 * t + rng.normal(0, 0.012)])
                sp, nrm = self.surface(d)
                along = _n(np.array([s, 0, 0.15 - 0.25 * t * s * s]))
                L = length * (0.7 + 0.5 * rng.random()) * (1 - 0.35 * abs(t))
                pts = [sp - nrm * 0.004]
                for k in range(1, 4):
                    f = k / 3
                    pts.append(sp + nrm * (0.012 * f) + along * L * f)
                strands.append(np.array(pts))
        return K.hair(self.name + '_wenkbrauw', strands, (0.0022, 0.0008), color_mat, self.root)

    def lashes(self, mats, color_mat, length=0.07, rng=None):
        rng = rng or np.random.default_rng(4)
        strands = []
        for s_i, s in enumerate((-1, 1)):
            c, fwd, re = self._eye_frame(s)
            pts_line = None
        # wimpers langs de opgeslagen wimperlijnen
        return None
