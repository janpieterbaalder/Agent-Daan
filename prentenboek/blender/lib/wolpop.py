"""Naaldviltpoppen op ware grootte (Daan ca. 12 cm, Joep ca. 6 cm zittend), ontworpen vanuit viltanimatie:

- Weinig, bolle, iets scheve vormen; kleur zit ín de wol (gevilte vlakjes met rafelige randen) in plaats
  van opgeplakte lapjes.
- Kraaloogjes, een bolletje als neus, blosjes van roze wol, mondjes en wenkbrauwen als dunne gevilte lijntjes.
- Haar als gevilte laag met losse plukjes wol erop.

Lokaal: pop kijkt naar -y, x = linkerkant van de pop, z omhoog, maten in meters.
"""
import math
import numpy as np
from . import core as K, sdf as S
from .body import ik2
from .wol import (vlak, edge, decal, star_poly, circle_poly, rrect_poly, poly_dist, surf_hit, bead, plukwol, c,
                  _n, Noise, smooth, F32, bead_mat)

ARMS = {   # handdoel t.o.v. de schouder, in armlengtes; poolrichting voor de elleboog
    'down': ((0.2, -0.05, -0.97), (1, 0.4, 0.0)),
    'hip': ((0.25, 0.05, -0.75), (1, 0.6, 0.2)),
    'wave': ((0.6, -0.15, 0.7), (1, 0.4, -0.7)),
    'up': ((0.3, -0.15, 0.92), (1, 0.3, 0.0)),
    'cheer': ((0.5, -0.12, 0.82), (1, 0.4, -0.3)),
    'forward': ((0.0, -0.95, -0.12), (1, 0.0, -0.6)),
    'point': ((0.12, -0.96, 0.12), (1, 0.0, -0.4)),
    'reach': ((0.3, -0.75, 0.5), (1, 0.1, -0.6)),
    'hold': ((-0.3, -0.62, -0.45), (1, 0.3, -0.6)),
    'hug': ((-0.45, -0.5, -0.2), (1, 0.2, -0.5)),
    'clap': ((-0.2, -0.8, 0.0), (1, 0.0, -0.7)),
    'side': ((0.9, -0.1, -0.2), (0.3, 0.2, -1)),
}


def _rotto(n):
    from .viltpop import _rot_to
    return _rot_to(n)


def _cols(d, fwd=(0, -1, 0)):
    z = _n(d)
    y = np.asarray(fwd, float) - z * np.dot(fwd, z)
    if np.linalg.norm(y) < 1e-6:
        y = np.array([0, 0, 1.0])
    y = _n(y)
    return np.stack([np.cross(y, z), y, z], 1).astype(F32)


def mouth_line(kind, w, curve):
    """2D-lijn of -vorm voor de mond (in het raakvlak, meters)."""
    if kind in ('smile', 'sad', 'flat'):
        k = {'smile': 1.0, 'sad': -1.0, 'flat': 0.0}[kind]
        return 'line', np.array([(x, curve * k * (x / w) ** 2) for x in np.linspace(-w, w, 11)])
    if kind in ('grin', 'open'):
        ww = w * (1.15 if kind == 'grin' else 0.85)
        hh = w * (0.95 if kind == 'grin' else 1.25)
        top = [(x, 0.15 * hh * (x / ww) ** 2) for x in np.linspace(ww, -ww, 9)]
        bot = [(-ww * math.cos(a), -hh * math.sin(a)) for a in np.linspace(0, math.pi, 13)[1:-1]]
        return 'shape', np.array(top + bot)
    if kind == 'o':
        return 'shape', circle_poly(w * 0.42, 24, ry=w * 0.55)
    return None, None


def line_dist(pts2):
    """Afstand tot een 2D-polylijn (voor gevilte lijntjes)."""
    pts2 = np.asarray(pts2, float)

    def d(P2):
        best = np.full(len(P2), 1e9)
        for i in range(len(pts2) - 1):
            a, b = pts2[i], pts2[i + 1]
            ab = b - a
            t = np.clip(((P2 - a) @ ab) / (ab @ ab + 1e-15), 0, 1)
            best = np.minimum(best, np.linalg.norm(P2 - (a + t[:, None] * ab), axis=1))
        return best
    return d


def surface_mark(center, normal, shape2d=None, line2d=None, thick=0.0006, depth=0.004, up=(0, 0, 1)):
    """Afstandsfunctie (in 3D) voor een gevilt vlakje of lijntje rond een punt op het oppervlak."""
    n = _n(normal)
    u = np.cross(up, n)
    u = _n(u) if np.linalg.norm(u) > 1e-6 else _n(np.cross((0, 1, 0), n))
    v = np.cross(n, u)
    cc = np.asarray(center, float)
    ld = line_dist(line2d) if line2d is not None else None

    def dist(V):
        Q = np.asarray(V, float) - cc
        P2 = np.stack([Q @ u, Q @ v], 1)
        dn = np.abs(Q @ n)
        if ld is not None:
            dd = ld(P2) - thick
        else:
            dd = poly_dist(P2, shape2d)
        return np.where(dn < depth, dd, 1.0)
    return dist


# ------------------------------------------------------------------ pet
def felt_cap(name, parent, s=1.0, loc=(0, 0, 0), rot=(0, 0, 0), seed=5):
    """Gevilte politiepet: bolle bovenkant, zwarte band, platte zwarte klep, goudgeel schildje."""
    root = K.empty(name, loc, rot, s, parent)
    zb, hb = 0.0158, 0.0042
    ax, ay = 0.0222, 0.0208

    def band(P):
        q = np.sqrt((P[:, 0] / ax) ** 2 + ((P[:, 1] - 0.0006) / ay) ** 2)
        d2 = (q - 1) * min(ax, ay)
        dz = np.abs(P[:, 2] - zb) - hb
        return np.minimum(np.maximum(d2, dz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz, 0) ** 2) - 0.0008
    F = S.Field()
    F.add(band, bound=((0, 0, zb), 0.04))
    F.add(*S.Ell((0, -0.0015, zb + hb + 0.0028), (ax * 1.22, ay * 1.28, 0.0058), S.rot(0.12, 0, 0)), k=0.002)
    fcap = lambda P: F(P)
    regions = [
        (edge(lambda V: np.abs(V[:, 2] - (zb - hb + 0.0014)) - 0.0016, 0.00025, seed), '#1f1f24'),
        (edge(surface_mark((0, -ay * 1.05, zb + hb + 0.0035), (0, -1, 0.35),
                           shape2d=np.array([(x * 0.0042, y * 0.0048) for x, y in
                                             [(-1, 1), (1, 1), (1, 0.1), (0, -1), (-1, 0.1)]]), depth=0.006),
              0.0002, seed + 1), '#e9b02a'),
    ]
    vlak(name + '_bol', fcap, '#1d2858', root, h=0.00038, lo=(-0.035, -0.035, zb - hb - 0.003),
         hi=(0.035, 0.035, zb + 0.016), regions=regions, seed=seed)
    Rv = S.rot(-0.32, 0, 0)

    def visor(P):
        e = S.ellipsoid(P, (0, -ay - 0.0006, zb - hb + 0.0006), (ax * 0.82, ay * 0.62, 0.0011), Rv)
        return S.smax(e, P[:, 1] + ay * 0.9, 0.0006)
    vlak(name + '_klep', visor, '#1f1f24', root, h=0.00028, lo=(-0.03, -0.045, zb - 0.012), hi=(0.03, -0.01, zb + 0.004),
         lump=0.00012, seed=seed + 2)
    return root


# ------------------------------------------------------------------ Daan
DAAN = dict(
    skin='#f3cdb3', blush='#ef9a9a', hair='#f0d48c', hair2='#e6c472', navy='#1f2a5a', navy2='#2d3b7a',
    pants='#19224c', boot='#26262b', sole='#8c867c', star='#f2b52a', eye='#1b2540', lip='#b5585f',
    brow='#c49a5c',
    head_c=(0, -0.0005, 0.0885), head_r=(0.0255, 0.0235, 0.0245),
    torso=((0, 0.0, 0.0445), (0.0165, 0.0145, 0.0205)), pelvis=((0, 0.0, 0.0305), (0.0158, 0.0138, 0.0115)),
    shoulder=(0.0128, 0.0, 0.0585), arm=(0.0122, 0.0112), arm_r=(0.0049, 0.0044), hand=0.0053,
    hip=(0.0074, 0.0, 0.0265), leg=(0.0098, 0.0092), leg_r=(0.0063, 0.0058), ankle_z=0.0098,
    belt=0.0302,
)


class Daan:
    """Naaldviltpop Daan. pose: root, yaw, lean, head (pitch, yaw, roll in graden), arm_r/arm_l (naam uit ARMS,
    'salute' of (dx,dy,dz) in armlengtes), legs ('stand', 'step', 'sit', 'floor').
    expr: mouth ('smile', 'grin', 'open', 'o', 'sad', 'flat'), eyes ('open', 'closed', 'happy'),
    brows ('none', 'up', 'worried', 'cross'), look (dx, dz)."""

    def __init__(self, name='Daan', pose=None, expr=None, cap=True, outfit='uniform', **kw):
        self.name = name
        self.sp = dict(DAAN)
        self.p = dict(root=(0, 0, 0), yaw=0.0, lean=0.0, head=(0, 0, 0), arm_r='down', arm_l='down', legs='stand',
                      cap_rot=(-0.14, 0, 0), cap_lift=0.0)
        self.p.update(pose or {})
        self.e = dict(mouth='smile', eyes='open', brows='none', look=(0, 0))
        self.e.update(expr or {})
        self.cap = cap
        self.outfit = outfit

    def _tilt(self, cc):
        lean = math.radians(self.p['lean'])
        zp = self.sp['hip'][2]
        return np.array([cc[0], cc[1] - math.sin(lean) * (cc[2] - zp), zp + (cc[2] - zp) * math.cos(lean)])

    def _arm(self, s, key):
        sp = self.sp
        Sh = self._tilt((s * sp['shoulder'][0], sp['shoulder'][1], sp['shoulder'][2]))
        L = sp['arm'][0] + sp['arm'][1]
        a = self.p['arm_' + key]
        if isinstance(a, str) and a == 'salute':
            hr = sp['head_r']
            W = self.hc + np.array([s * hr[0] * 1.05, -hr[1] * 0.55, hr[2] * 0.05])
            pole = np.array([s, 0.2, -0.5])
        else:
            off, pole = ARMS[a] if isinstance(a, str) else (a, (1, 0.3, -0.3))
            W = Sh + np.array([s * off[0], off[1], off[2]]) * L
            pole = np.array([s * pole[0], pole[1], pole[2]])
        E, W = ik2(Sh, W, sp['arm'][0], sp['arm'][1], pole, stretch=1.12)
        return Sh, E, W

    def _legs(self):
        sp, kind = self.sp, self.p['legs']
        hx, hy, hz = sp['hip']
        L0, L1 = sp['leg']
        az = sp['ankle_z']
        ax = hx + 0.0006
        pres = {'stand': [(ax, 0, az), (ax, 0, az)],
                'step': [(ax, -0.006, az), (ax, 0.004, az + 0.001)],
                'sit': [(ax, -L0 * 0.98, hz - L1 * 0.96), (ax, -L0 * 0.98, hz - L1 * 0.96)],
                'floor': [(ax + 0.001, -(L0 + L1) * 0.95, hz - 0.001), (ax + 0.001, -(L0 + L1) * 0.95, hz - 0.001)]}
        pts = pres[kind] if isinstance(kind, str) else kind
        out = {}
        for s, key, (fx, fy, fz) in ((-1, 'r', pts[0]), (1, 'l', pts[1])):
            Hh = np.array([s * hx, hy, hz])
            A = np.array([s * fx, fy, fz])
            pole = np.array([0, -0.15, 1.0]) if kind in ('sit', 'floor') else np.array([0, -1.0, 0.25])
            Kn, A = ik2(Hh, A, L0, L1, pole, stretch=1.08)
            out[key] = (Hh, Kn, A)
        return out

    def build(self):
        sp, p, e = self.sp, self.p, self.e
        root = K.empty(self.name)
        self.root = root
        self.hc = self._tilt(sp['head_c'])
        arms = {k: self._arm(s, k) for s, k in ((-1, 'r'), (1, 'l'))}
        legs = self._legs()
        self.hands = {k: (v[2], _n(v[2] - v[1])) for k, v in arms.items()}
        pj = self.outfit == 'pyjama'
        # ---- lijf in één stuk: romp, armen, benen
        F = S.Field()
        F.add(*S.Ell(tuple(self._tilt(sp['torso'][0])), sp['torso'][1]))
        F.add(*S.Ell(tuple(self._tilt(sp['pelvis'][0])), sp['pelvis'][1]), k=0.006)
        armF = S.Field()
        for key, (Sh, E, W) in arms.items():
            r0, r1 = sp['arm_r']
            for G in (F, armF):
                G.add(*S.Cone(tuple(Sh), tuple(E), r0, (r0 + r1) / 2), k=0.0035)
                G.add(*S.Cone(tuple(E), tuple(W), (r0 + r1) / 2, r1), k=0.002)
        for key, (Hh, Kn, A) in legs.items():
            r0, r1 = sp['leg_r']
            F.add(*S.Cone(tuple(Hh + np.array([0, 0, 0.003])), tuple(Kn), r0, (r0 + r1) / 2), k=0.004)
            F.add(*S.Cone(tuple(Kn), tuple(A), (r0 + r1) / 2, r1), k=0.002)
        self.fbody = F
        zb = sp['belt']
        top = sp['shoulder'][2]
        shirt, regions = self._body_regions(F, armF, zb, top)
        body, fb = vlak(self.name + '_lijf', None, shirt, root, h=0.00042, F=F, regions=regions, seed=2)
        self.fb = fb
        if self.outfit == 'uniform':
            # knoopjes: wit/grijze kraaltjes
            for i, z in enumerate(np.linspace(top - 0.006, zb + 0.004, 3)):
                q, n = self._front(F, z, 0.0)
                K.blob(self.name + f'_knoop{i}', (0.0009, 0.0009, 0.0005), 2.0, (12, 8),
                       mat=bead_mat('#d9dce2'), parent=root,
                       loc=tuple(q + n * 0.0004), rot=tuple(_rotto(n)))
        # ---- handjes
        for key, (Sh, E, W) in arms.items():
            d = _n(W - E)
            Fh = S.Field()
            Fh.add(*S.Ell(tuple(W + d * sp['hand'] * 0.75), (sp['hand'], sp['hand'] * 0.88, sp['hand'] * 1.08),
                          _cols(d)))
            vlak(self.name + f'_hand{key}', None, sp['skin'], root, h=0.0003, F=Fh, seed=30 + (key == 'l'), fuzz=0.5)
        # ---- laarsjes (of blote voetjes bij de pyjama)
        for s, key in ((-1, 'r'), (1, 'l')):
            Hh, Kn, A = legs[key]
            d = _n(A - Kn)
            fwd = np.array([s * 0.12, -1.0, 0.0]) if p['legs'] not in ('sit', 'floor') else \
                np.array([s * 0.1, -0.5, 0.0]) + (np.array([0, 0, 1.0]) if p['legs'] == 'floor' else 0)
            fwd = _n(fwd)
            Fb = S.Field()
            fk = sp.get('foot_k', 1.0)
            fc = A + d * 0.0042 * fk + fwd * 0.0022 * fk
            Fb.add(*S.Ell(tuple(fc), (0.0056 * fk, 0.0088 * fk, 0.0049 * fk), _boot(d, fwd)))
            Fb.add(*S.Sph(tuple(A), sp['leg_r'][1] * 0.95), k=0.002)
            bot = fc + d * 0.0038 * fk
            fbt = lambda P, Fb=Fb, bot=bot, d=d: S.smax(Fb(P), (P - bot.astype(F32)) @ d.astype(F32), 0.0008)
            lo = np.minimum(A, fc) - 0.014 * fk
            hi = np.maximum(A, fc) + 0.014 * fk
            regs = [] if pj else [(lambda V, bot=bot, d=d: smooth(-0.0018, -0.0010, (V - bot) @ d), sp['sole'])]
            vlak(self.name + f'_laars{key}', fbt, sp['skin'] if pj else sp['boot'], root, h=0.0003, lo=lo, hi=hi,
                 regions=regs, seed=40 + (key == 'l'))
        self._head()
        rl = list(p['root'])
        if p['legs'] == 'floor':
            rl[2] -= sp['hip'][2] - sp['leg_r'][0] * 0.9
        root.location = rl
        root.rotation_euler = (0, 0, math.radians(p['yaw']))
        return root

    def _body_regions(self, F, armF, zb, top):
        sp = self.sp
        pj = self.outfit == 'pyjama'
        shirt = '#8fc0e2' if pj else sp['navy']
        pants = '#8fc0e2' if pj else sp['pants']
        regions = []
        # broek: alles onder de riem dat niet bij de armen hoort
        regions.append((lambda V: smooth(0.0005, -0.0005, V[:, 2] - zb) * (armF(V.astype(F32)) > 0.0012), pants))
        if not pj:
            regions.append((edge(lambda V: np.where(armF(V.astype(F32)) > 0.001, np.abs(V[:, 2] - zb) - 0.0021, 1.0),
                                 0.0002, 4), '#1d1d22'))
            # gesp, zakken, ster, kraag
            fr = self._front(F, zb)
            regions.append((edge(surface_mark(fr[0], fr[1], shape2d=rrect_poly(0.0058, 0.0042, 0.0008)), 0.00018, 5),
                            '#c9ccd3'))
            regions.append((edge(surface_mark(fr[0], fr[1], shape2d=rrect_poly(0.0032, 0.0018, 0.0005)), 0.00015, 6),
                            '#1d1d22'))
            for s in (-1, 1):
                q, n = self._front(F, top - 0.012, s * 0.0068)
                regions.append((edge(surface_mark(q, n, shape2d=rrect_poly(0.0062, 0.0058, 0.0012)), 0.0002, 7 + s),
                                sp['navy2']))
                regions.append((edge(surface_mark(q + np.array([0, 0, 0.0031]), n, line2d=[(-0.0032, 0), (0.0032, 0)],
                                                  thick=0.00035), 0.00012, 9 + s), '#121a3a'))
            q, n = self._front(F, top - 0.0035, 0.0072)
            regions.append((edge(surface_mark(q, n, shape2d=star_poly(0.0033, 0.0014)), 0.00016, 12), sp['star']))
            q, n = self._front(F, top + 0.0005, 0.0)
            vshape = np.array([(-0.0058, 0.0012), (0.0058, 0.0012), (0.0, -0.0062)])
            regions.append((edge(surface_mark(q, n, shape2d=vshape), 0.0002, 13), sp['navy2']))
            # knoopsluiting: een donkerder lijntje
            q, n = self._front(F, (top + zb) / 2 - 0.002, 0.0)
            regions.append((edge(surface_mark(q, n, line2d=[(0.0, 0.009), (0.0, -0.009)], thick=0.0003), 0.0001, 14),
                            '#121a3a'))
        else:
            rng = np.random.default_rng(3)
            for i in range(9):
                a = rng.uniform(-1.2, 1.2)
                z = rng.uniform(zb - 0.006, top - 0.004)
                q, n = surf_hit(F, (math.sin(a) * 0.06, -math.cos(a) * 0.06, z), (-math.sin(a), math.cos(a), 0))
                regions.append((edge(surface_mark(q, n, shape2d=star_poly(0.0018, 0.0008)), 0.00012, 20 + i), '#f4d36b'))
        return shirt, regions

    def _front(self, F, z, x=0.0):
        q, n = surf_hit(F, (x, -0.08, z), (0, 1, 0))
        return q, n

    # ------------------------------------------------------------------ hoofd
    def _head(self):
        sp, p, e = self.sp, self.p, self.e
        pitch, yaw, roll = [math.radians(v) for v in p['head']]
        piv = K.empty(self.name + '_hoofd', tuple(self.hc), (0, 0, 0), 1.0, self.root)
        piv.rotation_mode = 'YXZ'
        piv.rotation_euler = (math.radians(p['lean']) - pitch, roll, yaw)
        self.head_root = piv
        hr = sp['head_r']
        F = S.Field()
        F.add(*S.Ell((0, 0, 0), hr))
        for s in (-1, 1):
            F.add(*S.Sph((s * hr[0] * 0.43, -hr[1] * 0.62, -hr[2] * 0.3), hr[0] * 0.36), k=0.006)
            F.add(*S.Ell((s * hr[0] * 0.98, 0.001, -0.0015), (0.0023, 0.0043, 0.0053), S.rot(0, 0, -s * 0.3)),
                  k=0.0015)
        qn, nn = surf_hit(F, (0, -0.08, -hr[2] * 0.16), (0, 1, 0))
        nkind, nr = sp.get('nose', ('bol', 0.0025))
        if nkind == 'lang':
            F.add(*S.Ell(tuple(qn + nn * nr * 0.9), (nr * 0.8, nr * 1.6, nr * 0.9)), k=0.0008)
        else:
            F.add(*S.Sph(tuple(qn + nn * nr * 0.36), nr), k=0.0008)
        regions = []
        for s in (-1, 1):
            q, n = surf_hit(F, (s * hr[0] * 0.5, -0.08, -hr[2] * 0.3), (0, 1, 0))
            regions.append((edge(surface_mark(q, n, shape2d=circle_poly(sp.get('cheek_r', 0.0046), 28)), 0.0013,
                                 50 + s, 0.0004), sp['blush']))
        regions.append((edge(lambda V, q=qn: np.linalg.norm(V - q, axis=1) - nr * 1.05, 0.0007, 52),
                        sp.get('nose_col', '#f2b0a4')))
        regions += self._face_regions(F)
        # mond
        kind, shape = mouth_line(e['mouth'], sp.get('mouth_w', 0.0034), sp.get('mouth_c', 0.0016))
        if kind:
            q, n = surf_hit(F, (0, -0.08, -hr[2] * 0.42), (0, 1, 0))
            if kind == 'line':
                regions.append((edge(surface_mark(q, n, line2d=shape, thick=0.00042), 0.00012, 53), sp['lip']))
            else:
                regions.append((edge(surface_mark(q, n, shape2d=shape), 0.00014, 54), '#7a2632'))
        # wenkbrauwen
        if e['brows'] != 'none':
            tilt = {'up': 0.0, 'worried': 0.35, 'cross': -0.35}.get(e['brows'], 0.0)
            bz = hr[2] * (0.27 if e['brows'] in ('up', 'worried') else 0.22)
            for s in (-1, 1):
                q, n = surf_hit(F, (s * hr[0] * 0.37, -0.08, bz), (0, 1, 0))
                pts = [(x, 0.0007 * (1 - (x / 0.0026) ** 2) - s * tilt * x) for x in np.linspace(-0.0026, 0.0026, 7)]
                regions.append((edge(surface_mark(q, n, line2d=pts, thick=0.00038), 0.0001, 55 + s), sp['brow']))
        # gesloten of lachende oogjes als gevilte boogjes
        ex, ez = hr[0] * sp.get('eye_x', 0.37), hr[2] * sp.get('eye_z', 0.04)
        if e['eyes'] in ('closed', 'happy'):
            k = -1.0 if e['eyes'] == 'closed' else 1.0
            for s in (-1, 1):
                q, n = surf_hit(F, (s * ex, -0.08, ez), (0, 1, 0))
                pts = [(x, k * 0.0011 * (1 - (x / 0.0026) ** 2)) for x in np.linspace(-0.0026, 0.0026, 7)]
                regions.append((edge(surface_mark(q, n, line2d=pts, thick=0.00045), 0.0001, 57 + s), '#3a2a26'))
        _, fh = vlak(self.name + '_kop', None, sp['skin'], piv, h=0.00034, F=F, regions=regions, seed=60, fuzz=0.45)
        self.fhead = fh
        if e['eyes'] == 'open':
            lx, lz = e['look']
            for s in (-1, 1):
                bead(self.name + f'_oog{s}', fh, (s * ex + lx * 0.0008, -0.08, ez + lz * 0.0008),
                     sp.get('eye_r', 0.0027), sp['eye'], piv, sink=0.42)
        self._hair(F, piv)
        self._headwear(piv, fh)

    def _face_regions(self, F):
        return []

    def _headwear(self, piv, fh):
        p = self.p
        if self.cap:
            felt_cap(self.name + '_pet', piv, 1.0, loc=(0, 0.0004, p['cap_lift']), rot=tuple(p['cap_rot']))

    def _hair(self, F, piv):
        sp = self.sp
        hr = sp['head_r']
        xs = [0, 30, 60, 95, 130, 180]
        zs = np.array([0.5, 0.45, 0.25, 0.1, -0.2, -0.38]) * hr[2]
        nz = Noise(71, 1400.0, 9)

        def region(P):
            az = np.degrees(np.abs(np.arctan2(P[:, 0], -P[:, 1])))
            return np.interp(az, xs, zs).astype(F32) + F32(0.0012) * nz(P) - P[:, 2]
        base = lambda P: S.ellipsoid(P, (0, 0, 0), hr)
        fhb = lambda P: S.smax(base(P) - 0.0013, region(P), 0.0007)
        vlak(self.name + '_haar', fhb, sp['hair'], piv, h=0.0003, lo=(-0.03, -0.03, -0.03), hi=(0.03, 0.03, 0.032),
             lump=0.0003, seed=72, regions=[(lambda V: 0.35 * (0.5 + 0.5 * nz(V * 0.7)), sp['hair2'])])
        # losse plukjes wol: onder de pet uit, of een kuif
        rng = np.random.default_rng(73)
        guides = []
        if self.cap:
            for az in np.radians(np.concatenate([np.linspace(-150, -40, 8), np.linspace(40, 150, 8),
                                                 np.linspace(-28, 28, 6)])):
                dvec = np.array([math.sin(az), -math.cos(az), 0.0])
                front = abs(math.degrees(az)) < 35
                z0 = hr[2] * (0.42 if front else 0.36)
                q, n = surf_hit(fhb, dvec * 0.06 + np.array([0, 0, z0]), -dvec)
                down = np.array([0, 0, -1.0])
                d0 = _n(n * 0.55 + down * (0.7 if not front else 0.45) + np.array([0, -0.25, 0]) * front)
                L = rng.uniform(0.006, 0.01) * (0.8 if front else 1.0)
                pts = [q - n * 0.0005]
                dd = d0.copy()
                for i in range(1, 6):
                    dd = _n(dd + down * 0.15 + n * 0.08 + rng.normal(0, 0.15, 3))
                    pts.append(pts[-1] + dd * L / 5)
                guides.append(pts)
        else:
            for i in range(26):
                az = rng.uniform(-math.pi, math.pi)
                el = rng.uniform(0.35, 0.95)
                dvec = _n(np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el) * 0.8, math.sin(el)]))
                q, n = surf_hit(fhb, dvec * 0.06, -dvec)
                front = -dvec[1]
                up = np.array([0, 0, 1.0])
                d0 = _n(n * 0.8 + up * 0.5 + np.array([0, -0.6, 0]) * max(front, 0) + rng.normal(0, 0.2, 3))
                L = rng.uniform(0.007, 0.012) * (1.25 if front > 0.3 else 1.0)
                pts = [q - n * 0.0005]
                dd = d0.copy()
                curl = _n(np.cross(n, dd))
                for k in range(1, 6):
                    dd = _n(dd + curl * 0.2 + np.array([0, 0.12, -0.05]) + rng.normal(0, 0.12, 3))
                    pts.append(pts[-1] + dd * L / 5)
                guides.append(pts)
        plukwol(self.name + '_plukjes', np.array(guides), 0.0013, sp['hair'], piv, per=70, radius=0.000028, seed=74,
                colors=[sp['hair'], sp['hair2'], '#f6e1a8'])


def _boot(d, fwd):
    z = _n(-np.asarray(d, float))
    y = np.asarray(fwd, float) - z * np.dot(fwd, z)
    y = _n(y) if np.linalg.norm(y) > 1e-6 else np.array([0, -1.0, 0])
    return np.stack([np.cross(y, z), y, z], 1).astype(F32)


# ------------------------------------------------------------------ Joep
JARMS = {
    'down': ((0.2, -0.1, -0.95), (1, 0.3, 0)),
    'up': ((0.35, -0.15, 0.9), (1, 0.3, 0)),
    'wave': ((0.7, -0.15, 0.6), (1, 0.3, -0.6)),
    'hug': ((-0.4, -0.6, -0.1), (1, 0.2, -0.5)),
    'forward': ((0.05, -0.95, 0.05), (1, 0.0, -0.6)),
    'hold': ((-0.25, -0.75, -0.35), (1, 0.2, -0.5)),
    'side': ((0.95, -0.1, -0.25), (0.3, 0.2, -1)),
    'point': ((0.15, -0.95, 0.15), (1, 0.0, -0.4)),
}
JOEP = dict(brown='#9b5b2e', brown2='#865026', cream='#efd5aa', dark='#3a2117', eye='#141418')


class Joep:
    """Naaldvilt-aapje Joep (oorsprong = onderkant van het lijfje). pose: root, yaw, rot, arm_r/arm_l, legs
    ('sit', 'hang', 'stand', 'dangle'), head (pitch, yaw, roll), scale. expr: mouth ('smile', 'open'), eyes."""

    def __init__(self, name='Joep', pose=None, expr=None, cap=True, **kw):
        self.name = name
        self.p = dict(root=(0, 0, 0), yaw=0.0, rot=None, arm_r='down', arm_l='down', legs='sit', head=(0, 0, 0),
                      scale=1.0)
        self.p.update(pose or {})
        self.e = dict(mouth='smile', eyes='open')
        self.e.update(expr or {})
        self.cap = cap

    def build(self):
        p, sp = self.p, JOEP
        root = K.empty(self.name, p['root'], (0, 0, 0), p['scale'])
        root.rotation_euler = p['rot'] if p['rot'] is not None else (0, 0, math.radians(p['yaw']))
        self.root = self.body = root
        F = S.Field()
        F.add(*S.Ell((0, 0, 0.0125), (0.0102, 0.0094, 0.0132)))
        F.add(*S.Ell((0, -0.0008, 0.0068), (0.0112, 0.0102, 0.0078)), k=0.004)
        arms, legs = {}, {}
        for s, key in ((-1, 'r'), (1, 'l')):
            Sh = np.array([s * 0.0078, 0.0, 0.0205])
            a = p['arm_' + key]
            L = 0.031
            if a == 'salute':
                W = np.array([s * 0.0135, -0.0075, 0.0385])
                pole = np.array([s, 0.2, -0.5])
            else:
                off, pole = JARMS[a] if isinstance(a, str) else (a, (1, 0.3, -0.3))
                W = Sh + np.array([s * off[0], off[1], off[2]]) * L
                pole = np.array([s * pole[0], pole[1], pole[2]])
            E, W = ik2(Sh, W, 0.016, 0.0155, pole, stretch=1.2)
            F.add(*S.Cone(tuple(Sh), tuple(E), 0.0031, 0.0028), k=0.0018)
            F.add(*S.Cone(tuple(E), tuple(W), 0.0028, 0.0026), k=0.0012)
            arms[key] = (Sh, E, W)
        jl = {'sit': [(0.0075, -0.026, 0.003), (0.0075, -0.026, 0.003)],
              'hang': [(0.0065, -0.004, -0.024), (0.0075, -0.006, -0.022)],
              'stand': [(0.006, 0.0, -0.014), (0.006, 0.0, -0.014)],
              'dangle': [(0.008, -0.016, -0.017), (0.009, -0.02, -0.011)]}[p['legs']]
        for s, key, (fx, fy, fz) in ((-1, 'r', jl[0]), (1, 'l', jl[1])):
            Hh = np.array([s * 0.0058, -0.002, 0.0055])
            A = np.array([s * fx, fy, fz])
            pole = np.array([0, -0.3, 1.0]) if p['legs'] == 'sit' else np.array([0, -1, 0.2])
            Kn, A = ik2(Hh, A, 0.0142, 0.0138, pole, stretch=1.2)
            F.add(*S.Cone(tuple(Hh), tuple(Kn), 0.0034, 0.003), k=0.0022)
            F.add(*S.Cone(tuple(Kn), tuple(A), 0.003, 0.0028), k=0.0012)
            legs[key] = (Hh, Kn, A)
        F.add(*S.Chain([(0, 0.0085, 0.006), (0.0, 0.0145, 0.005), (0.002, 0.0185, 0.0105), (0.0, 0.0172, 0.0168),
                        (-0.0024, 0.0135, 0.018)], [0.0019, 0.0018, 0.0017, 0.0016, 0.0015]), k=0.0015)
        self.hands = {k: (v[2], _n(v[2] - v[1])) for k, v in arms.items()}
        q, n = surf_hit(F, (0, -0.05, 0.011), (0, 1, 0))
        regions = [(edge(surface_mark(q, n, shape2d=circle_poly(0.0058, 28, ry=0.0072)), 0.0003, 81), sp['cream'])]
        nz = Noise(82, 600.0, 7)
        regions.append((lambda V: 0.25 * (0.5 + 0.5 * nz(V)), sp['brown2']))
        vlak(self.name + '_lijf', None, sp['brown'], root, h=0.00028, F=F, regions=regions, seed=83, fuzz=1.3)
        for key, (Sh, E, W) in arms.items():
            d = _n(W - E)
            Fh = S.Field()
            Fh.add(*S.Ell(tuple(W + d * 0.0024), (0.0036, 0.0033, 0.0039), _cols(d)))
            vlak(self.name + f'_hand{key}', None, sp['cream'], root, h=0.00024, F=Fh, seed=84)
        for key, (Hh, Kn, A) in legs.items():
            d = _n(A - Kn)
            fwd = np.array([0, -1.0, 0]) if p['legs'] != 'sit' else _n(np.array([0, -0.25, 1.0]))
            Ff = S.Field()
            Ff.add(*S.Ell(tuple(A + d * 0.0016 + fwd * 0.0018), (0.0036, 0.0048, 0.0031), _boot(d, fwd)))
            vlak(self.name + f'_voet{key}', None, sp['cream'], root, h=0.00024, F=Ff, seed=85)
        # hoofd
        pitch, yaw, roll = [math.radians(v) for v in p['head']]
        piv = K.empty(self.name + '_hoofd', (0, -0.0004, 0.0365), (0, 0, 0), 1.0, root)
        piv.rotation_mode = 'YXZ'
        piv.rotation_euler = (-pitch, roll, yaw)
        self.head = piv
        H = S.Field()
        H.add(*S.Ell((0, 0, 0), (0.0146, 0.0136, 0.0138)))
        for s in (-1, 1):
            H.add(*S.Ell((s * 0.0148, 0.0008, 0.0016), (0.0028, 0.0056, 0.0061), S.rot(0, 0, -s * 0.25)), k=0.0012)
        H.add(*S.Ell((0, -0.0108, -0.0046), (0.0082, 0.0052, 0.0058)), k=0.0018)
        regs = []
        # crème gezicht: pinda rond de ogen + snuit
        cen = [(-0.0042, 0.0016), (0.0042, 0.0016)]
        q, n = surf_hit(H, (0, -0.05, 0.0012), (0, 1, 0))

        def face_d(V, q=q, n=n):
            m1 = surface_mark(q, n, shape2d=circle_poly(0.0058, 28, cx=cen[0][0], cy=cen[0][1]), depth=0.01)(V)
            m2 = surface_mark(q, n, shape2d=circle_poly(0.0058, 28, cx=cen[1][0], cy=cen[1][1]), depth=0.01)(V)
            muz = np.linalg.norm((V - np.array([0, -0.0108, -0.0046])) / np.array([0.0088, 0.0062, 0.0064]), axis=1) - 1
            return np.minimum(np.minimum(m1, m2), muz * 0.006)
        regs.append((edge(face_d, 0.0003, 86), sp['cream']))
        for s in (-1, 1):
            qe, ne = surf_hit(H, (s * 0.04, 0.0, 0.0016), (-s, 0, 0))
            regs.append((edge(surface_mark(qe, ne, shape2d=circle_poly(0.0032, 24, ry=0.0038)), 0.00025, 87 + s),
                         sp['cream']))
        qm, nm = surf_hit(H, (0, -0.05, -0.0035), (0, 1, 0))
        nose = np.array([(-0.0016, 0.0006), (0.0016, 0.0006), (0.0, -0.0011)])
        regs.append((edge(surface_mark(qm, nm, shape2d=nose), 0.0001, 89), sp['dark']))
        mk, sh = mouth_line('smile' if self.e['mouth'] != 'open' else 'o', 0.0026, 0.0011)
        qm2, nm2 = surf_hit(H, (0, -0.05, -0.0068), (0, 1, 0))
        if mk == 'line':
            regs.append((edge(surface_mark(qm2, nm2, line2d=sh, thick=0.00032), 0.0001, 90), sp['dark']))
        else:
            regs.append((edge(surface_mark(qm2, nm2, shape2d=sh * 1.4), 0.0001, 90), '#6e1f2a'))
        if self.e['eyes'] != 'open':
            for s in (-1, 1):
                qe, ne = surf_hit(H, (s * 0.0042, -0.05, 0.0016), (0, 1, 0))
                pts = [(x, -0.0007 * (1 - (x / 0.0019) ** 2)) for x in np.linspace(-0.0019, 0.0019, 7)]
                regs.append((edge(surface_mark(qe, ne, line2d=pts, thick=0.00032), 0.0001, 91 + s), sp['dark']))
        _, fh = vlak(self.name + '_kop', None, sp['brown'], piv, h=0.00026, F=H, regions=regs, seed=92, fuzz=1.3)
        if self.e['eyes'] == 'open':
            for s in (-1, 1):
                bead(self.name + f'_oog{s}', fh, (s * 0.0042, -0.05, 0.0018), 0.0019, sp['eye'], piv, sink=0.4)
        if self.cap:
            felt_cap(self.name + '_pet', piv, 0.56, loc=(0.0004, 0.0006, 0.0006), rot=(-0.2, 0.12, 0.0))
        return root


# ------------------------------------------------------------------ bijrollen
ADULT = dict(
    bakker=dict(skin='#f1c4a6', head_c=(0, -0.0005, 0.158), head_r=(0.0222, 0.021, 0.0238),
                torso=((0, 0.0, 0.105), (0.0262, 0.0232, 0.034)), pelvis=((0, 0.0, 0.075), (0.0225, 0.0195, 0.016)),
                shoulder=(0.019, 0.0, 0.1335), arm=(0.0225, 0.0215), arm_r=(0.0059, 0.0053), hand=0.0063,
                hip=(0.0095, 0.0, 0.0685), leg=(0.03, 0.0285), leg_r=(0.0076, 0.0071), ankle_z=0.0108, belt=0.078,
                foot_k=1.22, boot='#4a3426', sole='#2a1d14', eye='#2a211c', eye_r=0.0023, nose=('bol', 0.0036),
                cheek_r=0.0042, mouth_w=0.0034, blush='#ec9a96', hair='#7a5232', hair2='#5e3e25', brow='#5a3a22',
                shirt='#f1ece2', pants='#686b78', apron='#fbf8f2', scarf='#c63b33', eye_x=0.38, eye_z=0.08),
    lang=dict(skin='#eec3a3', head_c=(0, -0.0005, 0.1865), head_r=(0.0195, 0.019, 0.0225),
              torso=((0, 0.0, 0.13), (0.0168, 0.0142, 0.036)), pelvis=((0, 0.0, 0.0965), (0.016, 0.0135, 0.0135)),
              shoulder=(0.0152, 0.0, 0.1625), arm=(0.0285, 0.0272), arm_r=(0.0049, 0.0044), hand=0.0056,
              hip=(0.0074, 0.0, 0.0905), leg=(0.0412, 0.0392), leg_r=(0.0059, 0.0055), ankle_z=0.0106, belt=0.099,
              foot_k=1.15, boot='#5a3b24', sole='#2a1d14', eye='#141418', eye_r=0.0021, nose=('lang', 0.0032),
              cheek_r=0.0036, mouth_w=0.003, blush='#e8a59c', hair='#3b2a20', hair2='#2a1d16', brow='#2a1d16',
              shirt='#efebe2', stripe='#25262c', pants='#26262c', beanie='#26262c', beanie2='#3f7a4a', scarf='#3f7a4a',
              eye_x=0.36, eye_z=0.08),
    dik=dict(skin='#f0c19f', head_c=(0, -0.0006, 0.1345), head_r=(0.0232, 0.0222, 0.0228),
             torso=((0, 0.0, 0.083), (0.0305, 0.0275, 0.034)), pelvis=((0, 0.0, 0.059), (0.0272, 0.024, 0.018)),
             shoulder=(0.0215, 0.0, 0.1095), arm=(0.0205, 0.0195), arm_r=(0.0063, 0.0057), hand=0.0065,
             hip=(0.011, 0.0, 0.0505), leg=(0.0212, 0.0202), leg_r=(0.0083, 0.0077), ankle_z=0.0108, belt=0.061,
             foot_k=1.25, boot='#5a3b24', sole='#2a1d14', eye='#141418', eye_r=0.0022, nose=('bol', 0.004),
             nose_col='#e88f86', cheek_r=0.0045, mouth_w=0.0036, blush='#ec9a96', hair='#7a3f22', hair2='#5a2e18',
             brow='#5a2e18', shirt='#efebe2', stripe='#25262c', pants='#26262c', beanie='#a52f2f', beanie2='#efe3c0',
             scarf='#c63b33', eye_x=0.38, eye_z=0.08),
)


class Mens(Daan):
    """Volwassen naaldviltpop: 'bakker', 'lang' (lange boef), 'dik' (dikke boef).
    mask_up: boevenmasker op het voorhoofd; baker_hat: koksmuts in plaats van muts."""

    def __init__(self, name, kind='bakker', pose=None, expr=None, mask_up=False, baker_hat=False, **kw):
        Daan.__init__(self, name, pose, expr, cap=False, outfit=kind)
        self.kind = kind
        self.sp = dict(DAAN)
        self.sp.update(ADULT[kind])
        self.mask_up = mask_up
        self.baker_hat = baker_hat or kind == 'bakker'

    def _body_regions(self, F, armF, zb, top):
        sp = self.sp
        regions = []
        not_arm = lambda V: (armF(V.astype(F32)) > 0.0015)
        regions.append((lambda V: smooth(0.0006, -0.0006, V[:, 2] - zb) * not_arm(V), sp['pants']))
        if self.kind == 'bakker':
            q, n = self._front(F, (top + zb) / 2 - 0.012, 0.0)
            zc = (top + zb) / 2 - 0.014

            def apron(V, q=q, zc=zc):
                inside = np.maximum(np.abs(V[:, 0]) - 0.019, np.abs(V[:, 2] - zc) - 0.033)
                return np.where((V[:, 1] < q[1] + 0.012) & not_arm(V), inside, 1.0)
            regions.append((edge(apron, 0.0003, 101), sp['apron']))
            q2, n2 = self._front(F, zb - 0.003, 0.0)
            regions.append((edge(surface_mark(q2, n2, shape2d=rrect_poly(0.013, 0.008, 0.0015)), 0.0002, 102),
                            '#ece6da'))
        else:
            stripes = lambda V: (np.sin(V[:, 2] * 2 * math.pi / 0.0072) > 0.15) * \
                (1 - smooth(0.0006, -0.0006, V[:, 2] - zb) * not_arm(V))
            regions.append((stripes, sp['stripe']))
            regions.append((edge(lambda V: np.where(not_arm(V), np.abs(V[:, 2] - zb) - 0.0022, 1.0), 0.0002, 103),
                            '#5a3b24'))
        regions.append((edge(lambda V: np.abs(V[:, 2] - (top + 0.001)) - 0.0028, 0.0003, 104), sp['scarf']))
        return sp['shirt'], regions

    def _face_regions(self, F):
        sp = self.sp
        hr = sp['head_r']
        if self.kind == 'bakker':
            return []
        ez = hr[2] * sp.get('eye_z', 0.04) + (hr[2] * 0.42 if self.mask_up else 0.0)
        band = lambda V, ez=ez: np.where(V[:, 1] < 0.004, np.abs(V[:, 2] - ez) - hr[2] * 0.17, 1.0)
        regs = [(edge(band, 0.0003, 105), '#1d1d22')]
        if not self.mask_up:
            for s in (-1, 1):
                q, n = surf_hit(F, (s * hr[0] * sp['eye_x'], -0.08, ez), (0, 1, 0))
                regs.append((edge(surface_mark(q, n, shape2d=circle_poly(sp['eye_r'] * 1.55, 24)), 0.0002, 106 + s),
                             '#f4f1ea'))
        return regs

    def _hair(self, F, piv):
        sp = self.sp
        hr = sp['head_r']
        rng = np.random.default_rng(len(self.name) + 7)
        if self.kind == 'bakker':
            qn, nn = surf_hit(F, (0, -0.08, -hr[2] * 0.16), (0, 1, 0))
            guides = []
            for s in (-1, 1):
                for j in range(5):
                    a = qn + np.array([s * 0.0012 * j, -0.001, -0.0045 - 0.0004 * j])
                    guides.append([a + np.array([s * 0.0016 * t, -0.0006 * t, -0.0012 * t * t])
                                   for t in np.linspace(0, 4, 5)])
            plukwol(self.name + '_snor', np.array(guides), 0.0011, sp['hair'], piv, per=60, radius=0.000035, seed=110,
                    colors=[sp['hair'], sp['hair2']])
        guides = []
        zline = hr[2] * 0.3
        for az in np.radians(np.linspace(55, 305, 26)):
            dvec = np.array([math.sin(az), -math.cos(az), 0.0])
            q, n = surf_hit(F, dvec * 0.06 + np.array([0, 0, zline * rng.uniform(0.6, 1.0)]), -dvec)
            dd = _n(n * 0.4 + np.array([0, 0, -1.0]))
            L = rng.uniform(0.004, 0.008)
            pts = [q - n * 0.0004]
            for k in range(1, 5):
                dd = _n(dd + rng.normal(0, 0.2, 3) + n * 0.1)
                pts.append(pts[-1] + dd * L / 4)
            guides.append(pts)
        plukwol(self.name + '_haarplukjes', np.array(guides), 0.0012, sp['hair'], piv, per=55, radius=0.00003,
                seed=111, colors=[sp['hair'], sp['hair2']])

    def _headwear(self, piv, fh):
        sp = self.sp
        hr = sp['head_r']
        if self.baker_hat:
            F = S.Field()
            zb = hr[2] * 0.42
            F.add(*S.Cyl((0, 0, zb), (0, 0, zb + 0.009), hr[0] * 1.0))
            for i in range(6):
                a = i * math.pi / 3
                F.add(*S.Sph((math.cos(a) * hr[0] * 0.55, math.sin(a) * hr[0] * 0.5, zb + 0.019), hr[0] * 0.55),
                      k=0.004)
            F.add(*S.Sph((0, 0, zb + 0.022), hr[0] * 0.62), k=0.004)
            vlak(self.name + '_koksmuts', None, '#fbfaf6', piv, h=0.0004, F=F, seed=112, lump=0.0004, fuzz=1.3)
            return
        zb = hr[2] * 0.15
        base = lambda P: S.ellipsoid(P, (0, 0.0006, 0.0012), (hr[0] + 0.0018, hr[1] + 0.0018, hr[2] + 0.0028))
        dome = lambda P: S.smax(base(P), zb - P[:, 2], 0.0006)
        rib = lambda V: 0.25 * (np.sin(np.arctan2(V[:, 0], -V[:, 1]) * 22) > 0.6)
        vlak(self.name + '_muts', dome, sp['beanie'], piv, h=0.00035, lo=(-0.04, -0.04, zb - 0.004),
             hi=(0.04, 0.04, hr[2] + 0.01), seed=113, lump=0.0003, fuzz=1.6, regions=[(rib, '#000000')])
        R = S.Field()
        R.add(*S.Tor((0, 0.0006, zb + 0.0018), (hr[0] + hr[1]) / 2 + 0.0016, 0.0028))
        vlak(self.name + '_mutsrand', None, sp['beanie2'], piv, h=0.0003, F=R, seed=114, lump=0.0003, fuzz=1.6)
        B = S.Field()
        B.add(*S.Sph((0, 0.002, hr[2] + 0.0055), 0.0048))
        vlak(self.name + '_mutsbol', None, sp['beanie2'], piv, h=0.0003, F=B, seed=115, lump=0.0006, fuzz=2.5)
