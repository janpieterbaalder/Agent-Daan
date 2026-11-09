"""Geboetseerd hoofd (signed distance fields): kind (Daan) of volwassene (bakker, boeven).

Eenheidsruimte: x = linkerkant van het personage, -y = voorkant van het gezicht, z omhoog. Het hoofd-empty
krijgt de schaal (meters per eenheid). Vormen: schedel, gezichtsmassa, appelwangen, wenkbrauwboog,
oogkassen met oogleden die om de oogbol vouwen, neus met vleugels en neusgaten, filtrum, lippen met
cupidoboog, kin, kaak, hals en oren met helix, antihelix, concha, tragus en lel.
"""
import math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from . import core as K, sdf as S
from .core import smoothstep

F32 = np.float32


def _n(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


CHILD = dict(
    adult=False,
    cranium=((0, 0.1, 0.27), (0.99, 1.04, 1.09)),
    face=((0, -0.2, -0.27), (0.84, 0.68, 0.58)),
    cheek=((0.46, -0.55, -0.3), (0.37, 0.31, 0.3)), cheek_k=0.24,
    chin=((0, -0.66, -0.57), 0.15), jaw_k=0.33,
    eye=(0.4, -0.68, 0.0), re=0.235, open_w=1.06, open_h=0.7,
    brow=0.12,
    nose_tip=((0, -0.905, -0.21), 0.095), nose_bridge=0.05, nose_scale=1.0,
    mouth_z=-0.45, mouth_w=0.16, mouth_y=-0.888, lip_up=0.019, lip_low=0.03, muzzle=((0, -0.66, -0.44), (0.25, 0.2, 0.16)),
    ear=(0.97, 0.08, -0.17), ear_s=1.18, ear_out=0.45,
    neck=0.42, scalp=True,
)

ADULT = dict(CHILD)
ADULT.update(
    adult=True,
    cranium=((0, 0.05, 0.22), (0.93, 0.98, 1.02)),
    face=((0, -0.22, -0.42), (0.84, 0.7, 0.74)),
    cheek=((0.46, -0.6, -0.34), (0.3, 0.26, 0.26)), cheek_k=0.18,
    chin=((0, -0.7, -0.84), 0.2), jaw_k=0.3,
    eye=(0.33, -0.74, 0.06), re=0.19, open_w=1.0, open_h=0.7,
    brow=0.16,
    nose_tip=((0, -1.0, -0.22), 0.17), nose_bridge=0.09, nose_scale=1.6,
    mouth_z=-0.56, mouth_w=0.24, mouth_y=-0.9, lip_up=0.028, lip_low=0.036, muzzle=((0, -0.68, -0.55), (0.33, 0.22, 0.2)),
    ear=(0.92, 0.06, -0.08), ear_s=1.15, ear_out=0.3,
    neck=0.5, scalp=False,
)


def onsurf(pts, depth, F_):
    """Zet punten (x, _, z) op het voorste oppervlak van veld F_; depth > 0 = naar binnen."""
    pts = np.array(pts, F32)
    lo = np.full(len(pts), -1.5, F32)
    hi = np.full(len(pts), -0.3, F32)
    for _ in range(26):
        mid = (lo + hi) / 2
        Q = pts.copy()
        Q[:, 1] = mid
        inside = F_(Q) < 0
        hi = np.where(inside, mid, hi)
        lo = np.where(inside, lo, mid)
    pts[:, 1] = (lo + hi) / 2 + np.asarray(depth, F32)
    return [tuple(map(float, q)) for q in pts]


class Head:
    def __init__(self, name='Hoofd', p=None, expr=None, res=0.009):
        self.name = name
        self.p = dict(ADULT if (p or {}).get('adult') else CHILD)
        self.p.update(p or {})
        self.e = dict(mouth='smile', smile=1.0, open=0.0, lids=1.0, lower=0.0, look=(0, -1, 0), brow_up=0.0,
                      squint=0.12, puff=0.0)
        self.e.update(expr or {})
        self.h = res
        self.felt = getattr(K, 'STYLE', '') == 'vilt'
        p = self.p
        if self.felt:
            # vilt: zachtere lippen (de mond wordt geborduurd), iets grovere mesh
            p['lip_up'] = p['lip_up'] * 0.6
            p['lip_low'] = p['lip_low'] * 0.7
            self.h = max(res, 0.0105)
        # compatibiliteit met haar, wenkbrauwen, maskers
        ex, ey, ez = p['eye']
        p['eye_dir'] = tuple(_n((ex, ey - 0.35, ez)))
        p['eye_r'] = p['re']
        p['nose_pos'] = (0, -1, p['nose_tip'][0][2])
        self._scalp = None
        self._lip_up = self._lip_low = None

    def bounds(self):
        cc, cr = self.p['cranium']
        top = cc[2] + cr[2] + 0.12
        return (-1.45, -1.4, -1.3), (1.45, 1.3, max(1.35, top))

    # haargrens (richting-z) per azimut, voor hair.py: voorkant, opzij, achter
    hair_zs = [0.66, 0.63, 0.55, 0.42, 0.3, 0.08, -0.3, -0.45]

    # ------------------------------------------------------------------ geometrie
    def _eye_c(self, s):
        ex, ey, ez = self.p['eye']
        return np.array([s * ex, ey, ez], F32)

    def _opening(self, s):
        """Ellips (in xz) van de ooglidopening: centrum, halve breedte, halve hoogte."""
        p, e = self.p, self.e
        c = self._eye_c(s)
        re = p['re']
        lid = e['lids']
        sq = e.get('squint', 0.0)
        ax = re * p['open_w'] * (1 - 0.08 * sq)
        az = re * p['open_h'] * max(0.02, lid) * (1 - 0.3 * sq)
        cz = c[2] - 0.03 * re + 0.25 * re * sq * 0.5 - (1 - lid) * re * 0.25
        return np.array([c[0] + s * 0.02 * re, c[1], cz]), ax, az

    def _mouth(self):
        """Controlepunten voor boven- en onderlip en de mondspleet, afhankelijk van de uitdrukking."""
        p, e = self.p, self.e
        zm, w, y0 = p['mouth_z'], p['mouth_w'], p['mouth_y']
        sm = e['smile']
        op = e['open']
        kind = e['mouth']
        if kind == 'o':
            w = w * (0.55 + 0.1 * op)
        elif kind == 'shout':
            w = w * (0.85 + 0.1 * op)
        elif kind == 'grin':
            w = w * (1.1 + 0.15 * op)
        wy = lambda x: y0 + 1.25 * x * x
        corner = sm * 0.05 - max(0.0, -sm) * 0.03
        up_open = op * (0.03 if kind != 'grin' else 0.015)
        low_open = op * {'o': 0.09, 'shout': 0.12, 'grin': 0.07}.get(kind, 0.06)
        if kind in ('o', 'shout'):
            corner = corner * 0.3
        xs = np.array([-1.0, -0.6, -0.22, 0.0, 0.22, 0.6, 1.0]) * w
        upz = zm + 0.012 + up_open + corner * np.abs(xs / w) ** 2 + np.array([0, 0.008, 0.015, 0.006, 0.015, 0.008, 0])
        if kind in ('o', 'shout'):
            upz = upz + up_open * (1 - (xs / w) ** 2) * 0.8
        up = [(x, wy(x) + 0.004, z) for x, z in zip(xs, upz)]
        upr = np.array([0.016, 0.026, 0.032, 0.03, 0.032, 0.026, 0.016]) * (p['lip_up'] / 0.019)
        xl = np.array([-0.8, -0.4, 0.0, 0.4, 0.8]) * w
        lowz = zm - 0.03 - low_open * (1 - 0.6 * (xl / w) ** 2) + corner * 0.8 * np.abs(xl / w) ** 2
        low = [(x, wy(x) - 0.004 * (1 - (x / w) ** 2), z) for x, z in zip(xl, lowz)]
        lowr = np.array([0.026, 0.044, 0.05, 0.044, 0.026]) * (p['lip_low'] / 0.03)
        slit = [(x, wy(x) - 0.012, zm + corner * (x / w) ** 2 - low_open * 0.45 * (1 - (x / w) ** 2))
                for x in np.linspace(-1.0, 1.0, 11) * w]
        return up, upr, low, lowr, slit, w, corner

    def field(self, scalp_only=False):
        p, e = self.p, self.e
        F = S.Field()
        cc, cr = p['cranium']
        F.add(*S.Ell(cc, cr))
        fc, fr = p['face']
        F.add(*S.Ell(fc, fr), k=0.4)
        F.add(*S.Cap((0, 0.02, -0.55), (0, 0.12, -1.55), p['neck']), k=0.32)
        if scalp_only:
            return F
        sm = e['smile']
        puff = e.get('puff', 0.0)
        ckc, ckr = p['cheek']
        for s in (-1, 1):
            c = (s * ckc[0], ckc[1] - 0.02 * puff, ckc[2] + 0.035 * max(0.0, sm) + 0.02 * puff)
            r = tuple(np.array(ckr) * (1 + 0.25 * puff))
            F.add(*S.Ell(c, r, S.rot(0, 0, s * 0.35)), k=p['cheek_k'])
        cpos, crad = p['chin']
        F.add(*S.Sph(cpos, crad), k=0.15)
        # wenkbrauwboog
        for s in (-1, 1):
            ec = self._eye_c(s)
            ts = np.linspace(-1, 1, 6)
            pts = [(ec[0] + s * 0.2 * t, 0, ec[2] + 0.34 + 0.035 * (1 - t * t) + 0.04 * e['brow_up']) for t in ts]
            rr = 0.075
            bp = onsurf(pts, rr - p['brow'] * 0.17 * (1 - 0.4 * ts ** 2), F)
            F.add(*S.Chain(bp, [rr] * len(bp)), k=0.12)
        # oogkassen en oogleden
        re = p['re']
        for s in (-1, 1):
            ec = self._eye_c(s)
            F.cut(*S.Sph(tuple(ec), re + 0.008), k=0.03)
            oc, ax, az = self._opening(s)
            def shell_fn(P, c=tuple(ec), oc=tuple(oc), ax=ax, az=az):
                r = S.norm(P - S._v(c))
                up_ = P[:, 2] > c[2]
                t = np.where(up_, 0.024, 0.013).astype(F32)
                sh = np.abs(r - (re + t)) - t
                return S.smax(sh, -S.ellipsoid(P, (oc[0], oc[1] - 0.4, oc[2]), (ax, 0.7, az)), 0.012)
            shell = shell_fn
            F.add(shell, k=0.03, bound=(tuple(ec), re + 0.1))
        # neus
        ns = p['nose_scale']
        tip, tr = p['nose_tip']
        F.add(*S.Cap((0, tip[1] + 0.15, tip[2] + 0.22), (0, tip[1] + 0.03, tip[2] + 0.04), p['nose_bridge']), k=0.12)
        F.add(*S.Ell(tip, (tr * 1.05, tr * 0.95, tr * 0.9)), k=0.07)
        for s in (-1, 1):
            F.add(*S.Ell((s * 0.088 * ns, tip[1] + 0.08 * ns, tip[2] - 0.045 * ns), (0.06 * ns, 0.06 * ns, 0.05 * ns),
                         S.rot(0, 0, s * 0.4)), k=0.045)
            F.cut(*S.Ell((s * 0.058 * ns, tip[1] + 0.05 * ns, tip[2] - 0.07 * ns), (0.022 * ns, 0.03 * ns, 0.013 * ns),
                         S.rot(0.45, 0, s * 0.45)), k=0.01)
        # mondbol en filtrum
        zm = p['mouth_z']
        mc, mr = p['muzzle']
        F.add(*S.Ell(mc, mr), k=0.12)
        for s in (-1, 1):
            F.add(*S.Cap((s * 0.024, p['mouth_y'] - 0.012, tip[2] - 0.11 * ns), (s * 0.03, p['mouth_y'] - 0.016, zm + 0.035),
                         0.006), k=0.016)
        # mond: lippen en mondplooi op het werkelijke oppervlak gelegd
        up, upr, low, lowr, slit, mw, corner = self._mouth()
        op = e['open']
        self._lip_up = onsurf(up, np.array(upr) - p['lip_up'] * 0.36, F)
        F.add(*S.Chain(self._lip_up, list(upr)), k=0.03)
        self._lip_low = onsurf(low, np.array(lowr) - p['lip_low'] * 0.45, F)
        F.add(*S.Chain(self._lip_low, list(lowr)), k=0.036)
        if op > 0:
            zc = zm - op * 0.04
            F.cut(*S.Ell((0, p['mouth_y'] + 0.12, zc), (mw * 0.92, 0.22, 0.012 + op * 0.075)), k=0.025)
        else:
            self._slit = onsurf(slit, 0.0062, F)
            sr = 0.0076 * np.sqrt(np.clip(1 - np.linspace(-1, 1, len(slit)) ** 4, 0, 1)) + 0.0035
            F.cut(*S.Chain(self._slit, list(np.minimum(sr, 0.0078))), k=0.009)
        for s in (-1, 1):
            cpt = onsurf([(s * mw * 1.04, 0, zm + corner)], 0.017, F)[0]
            F.cut(*S.Sph(cpt, 0.019), k=0.022)
            F.add(*S.Sph((s * (mw + 0.06), p['mouth_y'] + 0.09, zm + 0.035 + corner), 0.075), k=0.06)
        # oren
        for s in (-1, 1):
            self._ear(F, s)
        return F

    def _ear(self, F, s):
        p = self.p
        es = p['ear_s']
        base = np.array([s * p['ear'][0], p['ear'][1], p['ear'][2]])
        # oorvlak: u = naar achteren (+y), v = omhoog, w = naar buiten; schuin uitstaand
        a = p['ear_out']
        Rz = S.rot(0.12, 0, -s * a)
        U, Vv, W = Rz @ np.array([0, 1, 0.0]), Rz @ np.array([0, 0, 1.0]), Rz @ np.array([s * 1.0, 0, 0])
        L = lambda u, v, w=0.0: tuple(base + (U * u + Vv * v + W * w) * es)
        F.add(*S.Ell(L(0.02, 0.0, 0.03), (0.07 * es, 0.15 * es, 0.24 * es), Rz), k=0.07)
        # helix: rand langs de achter- en bovenkant
        arc = [L(-0.08, 0.15, 0.06), L(0.0, 0.23, 0.07), L(0.1, 0.2, 0.075), L(0.16, 0.08, 0.075), L(0.15, -0.06, 0.07),
               L(0.08, -0.17, 0.06)]
        F.add(*S.Chain(arc, [0.032 * es, 0.04 * es, 0.042 * es, 0.04 * es, 0.036 * es, 0.03 * es]), k=0.02)
        # lel
        F.add(*S.Sph(L(0.02, -0.2, 0.05), 0.065 * es), k=0.04)
        # concha (kom) en antihelix (rug)
        F.cut(*S.Ell(L(0.02, -0.01, 0.13), (0.07 * es, 0.1 * es, 0.13 * es), Rz), k=0.035)
        F.add(*S.Chain([L(-0.02, 0.12, 0.08), L(0.07, 0.08, 0.085), L(0.09, -0.04, 0.08)],
                       [0.018 * es, 0.022 * es, 0.018 * es]), k=0.02)
        # tragus
        F.add(*S.Sph(L(-0.09, -0.05, 0.05), 0.035 * es), k=0.02)

    # ------------------------------------------------------------------ oppervlak (voor haar en details)
    def scalp(self):
        if self._scalp is None:
            self._scalp = self.field(scalp_only=True)
        return self._scalp

    def shape(self, D):
        """Oppervlaktepunten van schedel+gezicht in richtingen D (vanuit het midden), via bisectie."""
        D = np.asarray(D, dtype=F32)
        f = self.scalp()
        lo = np.full(len(D), 0.2, F32)
        hi = np.full(len(D), 2.2, F32)
        for _ in range(22):
            mid = (lo + hi) / 2
            inside = f(D * mid[:, None]) < 0
            lo = np.where(inside, mid, lo)
            hi = np.where(inside, hi, mid)
        return (D * ((lo + hi) / 2)[:, None]).astype(float)

    def surface(self, d):
        d = _n(d)
        P = self.shape(d[None, :])[0]
        g = S.gradient(self.full, P[None, :].astype(F32), eps=0.004)[0] if hasattr(self, 'full') else _n(P)
        return P, np.asarray(g, float)

    # ------------------------------------------------------------------ kleur
    def paint(self, V, Fld):
        p, e = self.p, self.e
        col = np.ones((len(V), 3), F32)

        def tint(w, c):
            w = np.clip(w, 0, 1)[:, None]
            col[:] = col * (1 - w) + col * np.asarray(c, F32)[None, :] * w

        g3 = lambda c, s: np.exp(-((V - np.asarray(c, F32)) ** 2).sum(1) / (2 * s * s))
        ckc = p['cheek'][0]
        for s in (-1, 1):
            blush = (1.0, 0.56, 0.54) if self.felt else (1.0, 0.66, 0.62)
            tint((1.0 if self.felt else 0.85) * g3((s * ckc[0] * 1.05, ckc[1] - 0.25, ckc[2] + 0.04), 0.2), blush)
            tint(0.6 * g3((s * p['ear'][0], p['ear'][1], p['ear'][2]), 0.22), (1.0, 0.72, 0.66))
            ec = self._eye_c(s)
            dd = np.abs(S.norm(V - ec) - p['re'])
            tint(0.35 * np.exp(-(dd / 0.07) ** 2) * (V[:, 2] > ec[2] - 0.05), (0.97, 0.82, 0.8))
        tip = p['nose_tip'][0]
        tint(0.45 * g3(tip, 0.09), (1.0, 0.78, 0.74))
        # lippen: afstand tot de lipvormen
        up, upr, low, lowr, slit, mw, corner = self._mouth()
        up, low = (self._lip_up or up), (self._lip_low or low)
        dl = np.minimum(S.chain(V, up, list(upr)), S.chain(V, low, list(lowr)))
        lipm = 1 - smoothstep(0.004, 0.02, dl)
        tint((0.4 if self.felt else 0.78) * lipm, (0.9, 0.55, 0.53) if not p['adult'] else (0.86, 0.58, 0.54))
        if e['open'] > 0:
            depth = -S.ellipsoid(V, (0, p['mouth_y'] + 0.12, p['mouth_z'] - e['open'] * 0.04),
                                 (mw * 0.92, 0.22, 0.012 + e['open'] * 0.075))
            tint(smoothstep(-0.01, 0.03, depth), (0.33, 0.09, 0.11))
        if not p['adult']:
            rng = np.random.default_rng(7)
            for _ in range(30):
                s = rng.choice([-1, 1])
                c = (s * rng.uniform(0.12, 0.55), -0.88, rng.uniform(-0.32, -0.08))
                tint(0.3 * g3(c, 0.012), (0.86, 0.62, 0.5))
            if p.get('scalp', True):
                from .hair import scalp_mask
                D = V / np.linalg.norm(V, axis=1, keepdims=True)
                tint(0.8 * scalp_mask(D), (1.0, 0.93, 0.78))
        return col

    # ------------------------------------------------------------------ opbouw
    def build(self, parent, mats, scale=0.152, loc=(0, 0, 0), rot=(0, 0, 0)):
        p, e = self.p, self.e
        root = K.empty(self.name, loc, rot, scale, parent)
        self.root = root
        Fld = self.field()
        self.full = Fld
        V, Q = S.mesh(Fld, *self.bounds(), self.h, relax=2)
        # hals onderaan afknippen (onder de kraag niet nodig)
        col = self.paint(V, Fld)
        self.V, self.Q = V, Q
        self.skin = K.mesh_obj(self.name + '_huid', V, Q, mats['face'], root, attrs={'paint': ('POINT', col)})
        self.eyes = []
        for s in (-1, 1):
            self._eye(s, mats)
        if e['open'] > 0:
            self._mouth_inside(mats)
        elif self.felt and getattr(self, '_slit', None):
            # geborduurde mond: garen in de mondlijn, met steekjes
            sl = np.array(self._slit, float)
            sl[:, 1] -= 0.004
            t = np.linspace(0, 1, len(sl))
            fine = np.stack([np.interp(np.linspace(0, 1, 40), t, sl[:, i]) for i in range(3)], 1)
            if 'mouth_thread' not in mats:
                from . import mats as MM
                mats['mouth_thread'] = MM.thread('Mondgaren', '#8a3a3c', scale=2200)
            K.curve_tube(self.name + '_mondgaren', [tuple(q) for q in fine], 0.0085, mats['mouth_thread'], root)
        self.ears = []
        return root

    def _look(self, c):
        e = self.e
        if len(e['look']) == 4:
            return _n(np.array(e['look'][:3]) - c)
        return _n(e['look'])

    def _eye(self, s, mats):
        p = self.p
        c = self._eye_c(s)
        re = p['re']
        look = self._look(c)
        q = Vector((0, -1, 0)).rotation_difference(Vector(look))
        piv = K.empty(self.name + f'_oogpivot{s}', tuple(c), (0, 0, 0), re, self.root)
        piv.rotation_mode = 'QUATERNION'
        piv.rotation_quaternion = q
        # oogbol met holle iris (eenheidsbol, kijkt naar -y)
        D, Fc = K.sph(96, 64)
        th = np.arccos(np.clip(-D[:, 1], -1, 1))
        ti = math.asin(0.6)
        dent = 0.05 * (1 - np.clip(th / ti, 0, 1) ** 2)
        P = D * (1 - dent)[:, None]
        eb = K.mesh_obj(self.name + f'_oog{s}', P, Fc, mats['eye'], piv)
        self.eyes.append(eb)
        # hoornvlies: bolle kap voor de iris, glas met echte breking
        tc = math.radians(42)
        bulge = 0.085 * (1 - np.clip(th / tc, 0, 1) ** 2) ** 1.5
        Pc = D * (1.012 + bulge)[:, None]
        K.mesh_obj(self.name + f'_hoornvlies{s}', Pc, Fc, mats['cornea'], piv)
        if not self.felt:
            self._lashes(s, mats)

    def _lashes(self, s, mats):
        p = self.p
        c = self._eye_c(s)
        re = p['re']
        oc, ax, az = self._opening(s)
        rl = re + 0.046
        strands = []
        rng = np.random.default_rng(10 + s)
        for upper, n, L in ((True, 64, 0.052 if not p['adult'] else 0.045), (False, 18, 0.024)):
            for i in range(n):
                t = (i + rng.random() * 0.6) / n
                ang = math.pi * (0.1 + 0.8 * t)
                x = oc[0] + ax * math.cos(ang) * 1.0
                z = oc[2] + (az if upper else -az) * math.sin(ang) * 1.02
                dx, dz = x - c[0], z - c[2]
                yy = c[1] - math.sqrt(max(rl * rl - dx * dx - dz * dz, 1e-6))
                root = np.array([x, yy, z])
                out = _n(root - c)
                up = np.array([0, -0.25, 1.0 if upper else -1.0])
                d0 = _n(out * 0.9 + up * 0.32 + np.array([s * (x - oc[0]) / ax * 0.25, 0, 0]))
                Ls = L * (0.65 + 0.35 * math.sin(ang)) * (0.85 + 0.3 * rng.random())
                pts = [root - out * 0.005]
                for k in range(1, 5):
                    f = k / 4
                    curl = np.array([0, 0.25, 1.0 if upper else -1.0]) * f * f * 0.5
                    pts.append(root + (d0 + curl) * Ls * f)
                strands.append(np.array(pts))
        K.hair(self.name + f'_wimpers{s}', strands, (0.0042, 0.0014), mats['lashes'], self.root)

    def _mouth_inside(self, mats):
        p, e = self.p, self.e
        zm, y0 = p['mouth_z'], p['mouth_y']
        op = e['open']
        up, upr, low, lowr, slit, mw, corner = self._mouth()
        K.blob(self.name + '_tong', (mw * 0.6, 0.12, 0.04), 2.0, (32, 16), mat=mats['tongue'], parent=self.root,
               loc=(0, y0 + 0.12, zm - 0.03 - op * 0.07))
        if e['mouth'] in ('grin', 'shout'):
            K.blob(self.name + '_tanden', (mw * 0.62, 0.05, 0.022), 3.0, (32, 16), mat=mats['teeth'], parent=self.root,
                   loc=(0, y0 + 0.07, zm + 0.0))
        K.blob(self.name + '_mondholte', (mw * 0.95, 0.16, 0.012 + op * 0.08), 2.0, (32, 16), mat=mats['mouth_in'],
               parent=self.root, loc=(0, y0 + 0.22, zm - op * 0.04))

    # ------------------------------------------------------------------ wenkbrauwen
    def brows(self, mats, color_mat, density=1.0, length=0.07, rng=None):
        rng = rng or np.random.default_rng(3)
        strands = []
        f = self.full
        tilt = self.e.get('brow_tilt', 0.0)
        for s in (-1, 1):
            ec = self._eye_c(s)
            for i in range(int(170 * density)):
                t = rng.uniform(-1, 1)
                x = ec[0] + s * t * 0.19
                z = ec[2] + 0.36 + 0.05 * (1 - t * t) + self.e['brow_up'] * 0.06 - tilt * 0.06 * t + rng.normal(0, 0.012)
                # straal vanaf ver voor het gezicht naar achteren tot het oppervlak
                y0, y1 = -1.6, ec[1]
                for _ in range(24):
                    ym = (y0 + y1) / 2
                    if f(np.array([[x, ym, z]], F32))[0] > 0:
                        y0 = ym
                    else:
                        y1 = ym
                sp = np.array([x, (y0 + y1) / 2, z])
                nrm = S.gradient(f, sp[None, :].astype(F32), eps=0.004)[0]
                along = _n(np.array([s, 0, 0.12 - 0.25 * t]))
                L = length * (0.7 + 0.5 * rng.random()) * (1 - 0.35 * abs(t))
                pts = [sp - nrm * 0.004]
                for k in range(1, 4):
                    ff = k / 3
                    pts.append(sp + nrm * (0.01 * ff) + along * L * ff)
                strands.append(np.array(pts))
        return K.hair(self.name + '_wenkbrauw', strands, (0.0022, 0.0008), color_mat, self.root)
