"""Viltpoppen, opgebouwd zoals een naaldviltpop: losse eenvoudige delen (bolle kop, eivormig lijfje,
worstarmpjes met wanthandjes, stevige beentjes), opgenaaide vilten lapjes (ogen, zakken, ster, kraag),
geborduurde details (mond, wimperlijn, stiksels) en een wollen kuif.

Alles wordt als vorm-veld (SDF) gemaakt en daarna als mesh opgebouwd; lapjes worden over het oppervlak
gelegd. De wol zelf (vezels, putjes, pluis) komt uit felt.py bij het renderen.

Lokaal: pop kijkt naar -y, x = linkerkant van de pop (rechts in beeld), z omhoog, maten in meters.
"""
import math
import numpy as np
from mathutils import Euler
from . import core as K, sdf as S, mats as M
from .body import ik2

F32 = np.float32


def _n(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


# ------------------------------------------------------------------ materialen
_MC = {}


def _cached(name):
    m = _MC.get(name)
    if m is None:
        return None
    try:
        m.name
        return m
    except ReferenceError:
        return None


def wol(name, color, attr=None, sheet=False, fuzz=1.0):
    m = _cached(name)
    if m:
        return m
    g = M.NT(name)
    col = M.C(color) if isinstance(color, str) else color
    if attr:
        col = g.mix(1.0, col, g.attr(attr), 'MULTIPLY')
    g.principled(color=col, rough=1.0)
    m = g.done([n for n in g.t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0])
    if sheet:
        m['sheet'] = 1
    m['fuzz'] = fuzz
    _MC[name] = m
    return m


def kraal(name, color='#121216'):
    m = _cached(name)
    if m:
        return m
    g = M.NT(name)
    p = g.principled(color=M.C(color), rough=0.1, coat=1.0, coat_rough=0.03, spec=0.6)
    m = g.done(p)
    m['nofelt'] = 1
    _MC[name] = m
    return m


def garen(name, color):
    m = _cached(name)
    if m:
        return m
    m = M.thread(name, color, scale=2600)
    _MC[name] = m
    return m


# ------------------------------------------------------------------ vormgereedschap
class Lump:
    """Handgevilte onregelmatigheid: een paar lage sinusgolven in willekeurige richtingen."""

    def __init__(self, seed, amp=0.0015, freq=22.0, n=7):
        rng = np.random.default_rng(seed)
        k = _n(rng.normal(size=(n, 3)))
        self.k = (k * freq * (0.7 + 0.6 * rng.random((n, 1)))).astype(F32)
        self.ph = (rng.random(n) * 6.283).astype(F32)
        self.amp = F32(amp)

    def __call__(self, P):
        return self.amp * np.sin(P @ self.k.T + self.ph).mean(1) * F32(1.7)


def fbounds(F, pad=0.02):
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for kind, fn, k, b in F.ops:
        if kind != 'add' or b is None:
            continue
        c, r = np.asarray(b[0], float), float(b[1])
        lo, hi = np.minimum(lo, c - r), np.maximum(hi, c + r)
    return lo - pad, hi + pad


def piece(name, f, lo, hi, mat, parent, h=0.0035, attrs_fn=None):
    V, Q = S.mesh(f, lo, hi, h, relax=1)
    attrs = attrs_fn(V) if attrs_fn else None
    return K.mesh_obj(name, V, Q, mat, parent, attrs=attrs)


def to_surf(f, P, it=6, eps=5e-4):
    Q = np.asarray(P, F32).reshape(-1, 3).copy()
    for _ in range(it):
        d = f(Q)
        g = S.gradient(f, Q, eps)
        Q = Q - g * d[:, None]
    return Q.astype(float), S.gradient(f, Q, eps).astype(float)


def hit(f, P0, d=(0, 1, 0), it=80):
    """Loop vanaf P0 langs richting d naar het oppervlak (sphere tracing)."""
    p = np.asarray(P0, float).reshape(3)
    d = _n(d)
    t = 0.0
    for _ in range(it):
        v = float(f((p + d * t)[None].astype(F32))[0])
        if abs(v) < 2e-5:
            break
        t += v * 0.9
        if t > 3.0 or t < -3.0:
            return p
    return p + d * t


def surf(f, P0, d=(0, 1, 0)):
    q, n = to_surf(f, [hit(f, P0, d)])
    return q[0], n[0]


def frame(n, up=(0, 0, 1)):
    n = _n(n)
    u = np.cross(up, n)
    if np.linalg.norm(u) < 1e-5:
        u = np.cross((0, 1, 0), n)
    u = _n(u)
    return u, np.cross(n, u)


def applique(name, f, anchor, outline, thick, mat, parent, lift=0.0, up=(0, 0, 1), rings=4, bevel=True,
             stitch=None, inset=0.0045, ray=(0, 1, 0)):
    """Vilten lapje met omtrek `outline` (n,2) in het raakvlak bij `anchor`, over het oppervlak gelegd.
    Geeft het object en een functie top(P2) -> (punten, normalen) op de bovenkant."""
    c, n0 = surf(f, anchor, ray)
    u, v = frame(n0, up)
    O = np.asarray(outline, float)
    if 0.5 * np.sum(O[:, 0] * np.roll(O[:, 1], -1) - np.roll(O[:, 0], -1) * O[:, 1]) < 0:
        O = O[::-1]
    n = len(O)

    def place(P2, h):
        P = c + P2[:, :1] * u + P2[:, 1:2] * v
        q, nq = to_surf(f, P)
        return q + nq * h, nq

    Vb, Vt = [], []
    for k in range(rings, 0, -1):
        s = k / rings
        Vb.append(place(O * s, lift)[0])
        Vt.append(place(O * s, lift + thick)[0])
    cb = c + n0 * lift
    ct = c + n0 * (lift + thick)
    V = np.concatenate(Vb + Vt + [cb[None], ct[None]])
    F = []
    nb = rings * n
    icb, ict = 2 * nb, 2 * nb + 1
    for r in range(rings - 1):
        for i in range(n):
            j = (i + 1) % n
            a0, a1, b0, b1 = r * n + i, r * n + j, (r + 1) * n + i, (r + 1) * n + j
            F.append((nb + a0, nb + b0, nb + b1, nb + a1)[::-1])
            F.append((a0, a1, b1, b0)[::-1])
    last = (rings - 1) * n
    for i in range(n):
        j = (i + 1) % n
        F.append((ict, nb + last + i, nb + last + j))
        F.append((icb, last + j, last + i))
        F.append((i, j, nb + j, nb + i))
    ob = K.mesh_obj(name, V, F, mat, parent)
    if bevel:
        K.modifier(ob, 'BEVEL', width=thick * 0.42, segments=2, limit_method='ANGLE')
    if stitch is not None:
        r_ = np.linalg.norm(O, axis=1, keepdims=True) + 1e-9
        Oi = O * np.maximum(1 - inset / r_, 0.2)
        Oi = np.concatenate([Oi, Oi[:1]])
        fine = _densify(Oi, 6)
        P, N = place(fine, lift + thick)
        stitches(name + '_stiksel', P, N, stitch, parent)
    return ob


def _densify(P2, per):
    out = []
    for i in range(len(P2) - 1):
        for t in np.linspace(0, 1, per, endpoint=False):
            out.append(P2[i] * (1 - t) + P2[i + 1] * t)
    out.append(P2[-1])
    return np.array(out)


def stitches(name, P, N, mat, parent, dash=0.0048, gap=0.0032, r=0.00075):
    """Rijgsteek: korte stukjes garen die in en uit de stof duiken."""
    P, N = np.asarray(P, float), np.asarray(N, float)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    strands = []
    x = gap * 0.5
    lift = np.array([-0.0007, 0.00035, 0.00035, -0.0007])
    while x + dash < s[-1]:
        ts = np.linspace(x, x + dash, 4)
        q = np.stack([np.interp(ts, s, P[:, i]) for i in range(3)], 1)
        nn = _n(np.stack([np.interp(ts, s, N[:, i]) for i in range(3)], 1))
        strands.append(q + nn * lift[:, None])
        x += dash + gap
    if strands:
        return K.hair(name, strands, (r, r * 0.9), mat, parent)


def thread_line(name, f, anchor, pts2d, mat, parent, r=0.0016, lift=0.0, up=(0, 0, 1), ray=(0, 1, 0)):
    """Geborduurde lijn (mond, wimperlijn, gesloten oog) over het oppervlak."""
    c, n0 = surf(f, anchor, ray)
    u, v = frame(n0, up)
    P2 = _densify(np.asarray(pts2d, float), 6)
    P = c + P2[:, :1] * u + P2[:, 1:2] * v
    q, nq = to_surf(f, P)
    q = q + nq * (lift + r * 0.55)
    return K.curve_tube(name, [tuple(x) for x in q], r, mat, parent)


def ellipse(a, b, n=40, c=(0, 0)):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([c[0] + a * np.cos(t), c[1] + b * np.sin(t)], 1)


def rrect(w, h, r, n=8):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for t in np.linspace(a0, a0 + 90, n):
            pts.append((cx + r * math.cos(math.radians(t)), cy + r * math.sin(math.radians(t))))
    return np.array(pts)


def star(ro, ri, n=5, rot=90):
    pts = []
    for i in range(2 * n):
        a = math.radians(rot + i * 180 / n)
        r = ro if i % 2 == 0 else ri
        pts.append((r * math.cos(a), r * math.sin(a)))
    P = np.array(pts)
    return _densify(np.concatenate([P, P[:1]]), 3)[:-1]


def shield(w, h):
    pts = [(x, h / 2 + 0.08 * h * (1 - (2 * x / w) ** 2)) for x in np.linspace(-w / 2, w / 2, 9)]
    pts += [(w / 2, y) for y in np.linspace(h / 2, 0, 5)[1:]]
    pts += [(w / 2 * math.cos(t), -h / 2 * math.sin(t)) for t in np.linspace(0, math.pi, 13)[1:]]
    pts += [(-w / 2, y) for y in np.linspace(0, h / 2, 5)[1:-1]]
    return np.array(pts)


# ------------------------------------------------------------------ pet
def police_cap(name, parent, s=1.0, hair_t=0.011, loc=(0, 0, 0), rot=(0, 0, 0), stitch=True):
    """Vilten politiepet in de maat van Daans hoofd (schaal s), in hoofd-coördinaten."""
    root = K.empty(name, loc, rot, s, parent)
    navy = wol('Vilt politieblauw', '#111836')
    black = wol('Vilt zwart', '#1d1d22')
    gold = wol('Vilt goud', '#f0bd3c', sheet=True)
    zb, hb = 0.094, 0.024
    ax, ay = 0.127 + hair_t * 0.4, 0.121 + hair_t * 0.4

    def band(P, ax=ax, ay=ay, zc=zb, hh=hb, r=0.006):
        q = np.sqrt((P[:, 0] / ax) ** 2 + (P[:, 1] / ay) ** 2)
        d2 = (q - 1) * min(ax, ay)
        dz = np.abs(P[:, 2] - zc) - hh
        return np.minimum(np.maximum(d2, dz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz, 0) ** 2) - r
    F = S.Field()
    F.add(band, bound=((0, 0, zb), 0.2))
    F.add(*S.Ell((0, -0.014, zb + hb + 0.024), (0.168, 0.176, 0.042), S.rot(0.1, 0, 0)), k=0.018)
    lump = Lump(31, 0.0012, 26)
    fcap = lambda P: F(P) + lump(P)
    piece(name + '_bol', fcap, (-0.2, -0.22, 0.04), (0.2, 0.2, 0.2), navy, root, h=0.0028)
    # zwarte band onderaan
    fb = lambda P: band(P, ax + 0.0035, ay + 0.0035, zb - hb + 0.007, 0.0075, 0.003)
    piece(name + '_band', fb, (-0.16, -0.16, 0.05), (0.16, 0.16, 0.1), black, root, h=0.0022)
    # klep: platte halve ellips naar voren, iets omlaag
    Rv = S.rot(-0.32, 0, 0)

    def visor(P):
        e = S.ellipsoid(P, (0, -0.108, zb - hb + 0.004), (0.112, 0.082, 0.0075), Rv)
        return S.smax(e, P[:, 1] + 0.096, 0.004)
    piece(name + '_klep', visor, (-0.14, -0.21, 0.02), (0.14, -0.06, 0.12), black, root, h=0.0022)
    # schildje voorop de bol
    applique(name + '_schild', fcap, (0, -0.2, zb + hb + 0.03), shield(0.03, 0.034), 0.0032, gold, root,
             stitch=garen('Garen goud', '#9a6d12') if stitch else None, inset=0.0035)
    return root


# ------------------------------------------------------------------ Daan
DAAN = dict(
    skin='#f3c4a3', hair='#eccb72', navy='#111836', navy2='#1b2550', black='#1d1d22', star='#f2b21a',
    head_c=(0, -0.006, 0.6), head_r=(0.152, 0.142, 0.148),
    torso=[((0, 0.0, 0.298), (0.146, 0.13, 0.128)), ((0, 0.002, 0.388), (0.123, 0.105, 0.094))],
    shoulder=(0.108, 0.004, 0.43), arm=(0.086, 0.086), arm_r=(0.047, 0.041), hand_r=0.039,
    hip=(0.062, 0.0, 0.2), leg=(0.072, 0.074), leg_r=(0.06, 0.055), belt_z=0.232,
)


FACE = dict(eye_x=0.056, eye_z=0.012, eye_a=0.025, eye_b=0.029, iris=0.018, pupil=0.0102, brow_x=0.058,
            brow_z=0.064, brow_w=0.02, mouth_z=-0.066, mouth_w=0.032, iris_col='#6c90c2', brow_col='#c99a58',
            lash=True)

ARMS = {
    'down': ((0.04, -0.012, -0.145), (1, 0.4, 0.0)),
    'hip': ((0.035, 0.01, -0.12), (1, 0.6, 0.1)),
    'wave': ((0.1, -0.03, 0.12), (1, 0.4, -0.7)),
    'up': ((0.055, -0.03, 0.155), (1, 0.3, 0.0)),
    'forward': ((0.0, -0.15, -0.02), (1, 0.0, -0.6)),
    'hold': ((-0.045, -0.1, -0.075), (1, 0.3, -0.6)),
    'point': ((0.02, -0.16, 0.02), (1, 0.0, -0.4)),
    'reach': ((0.05, -0.13, 0.08), (1, 0.1, -0.6)),
    'cheer': ((0.085, -0.02, 0.14), (1, 0.4, -0.3)),
    'clap': ((-0.03, -0.13, -0.0), (1, 0.0, -0.7)),
}
LEGS = {
    'stand': [(0.066, 0.0, 0.064), (0.066, 0.0, 0.064)],
    'step': [(0.064, -0.055, 0.064), (0.068, 0.04, 0.064)],
    'sit': [(0.07, -0.15, 0.1), (0.07, -0.15, 0.1)],
    'tiptoe': [(0.064, 0.02, 0.085), (0.068, 0.0, 0.066)],
    'floor': [(0.075, -0.13, 0.19), (0.075, -0.13, 0.19)],
}


class Daan:
    """Viltpop Daan. pose: root, yaw, lean (graden voorover), head (pitch, yaw, roll in graden),
    arm_r/arm_l (naam uit ARMS of (dx, dy, dz) t.o.v. de schouder), legs (naam uit LEGS).
    expr: mouth ('smile', 'grin', 'open', 'o', 'sad', 'flat'), eyes ('open', 'closed', 'happy'),
    look (dx, dz) in -1..1, brows ('neutral', 'up', 'worried', 'cross'), blush (0..1).
    outfit 'uniform' of 'pyjama'."""

    def __init__(self, name='Daan', pose=None, expr=None, cap=True, outfit='uniform', mats=None,
                 hair_density=1.0, **kw):
        self.name = name
        self.p = dict(root=(0, 0, 0), yaw=0.0, lean=0.0, head=(0, 0, 0), arm_r='down', arm_l='down',
                      legs='stand')
        self.p.update(pose or {})
        self.e = dict(mouth='smile', eyes='open', look=(0, 0), brows='neutral', blush=1.0)
        self.e.update(expr or {})
        self.cap = cap
        self.outfit = outfit
        self.spec = dict(DAAN)
        self.fp = dict(FACE)

    # -- hulp
    def _arm(self, s, key):
        sp = self.spec
        Sh = np.array(self.tilt((s * sp['shoulder'][0], sp['shoulder'][1], sp['shoulder'][2])))
        a = self.p['arm_' + key]
        if isinstance(a, str) and a == 'salute':
            hc = np.array(self.hc)
            W = hc + np.array([s * 0.128, -0.075, 0.012])
            pole = np.array([s * 1.0, 0.2, -0.4])
        else:
            off, pole = ARMS[a] if isinstance(a, str) else (a, (1, 0.3, -0.3))
            k = (sp['arm'][0] + sp['arm'][1]) / 0.172 if isinstance(a, str) else 1.0
            W = Sh + np.array([s * off[0], off[1], off[2]]) * k
            pole = np.array([s * pole[0], pole[1], pole[2]])
        E, W = ik2(Sh, W, sp['arm'][0], sp['arm'][1], pole, stretch=1.25)
        return Sh, E, W

    def build(self):
        sp, p, e = self.spec, self.p, self.e
        root = K.empty(self.name)
        self.root = root
        pj = self.outfit == 'pyjama'
        skin, cloth, cloth2, black, thread, pants, shoe_m = self._materials()
        lean = math.radians(p['lean'])
        # hoofdmidden (ook nodig voor saluut)
        hc = np.array(sp['head_c'], float)
        zp = sp.get('lean_z', 0.27)
        hc = np.array([hc[0], hc[1] - math.sin(lean) * (hc[2] - zp), zp + (hc[2] - zp) * math.cos(lean)])
        self.hc = hc
        # ---- lijf: romp, armen, benen als één gevilt stuk
        F = S.Field()
        tilt = lambda c: (c[0], c[1] - math.sin(lean) * (c[2] - zp), zp + (c[2] - zp) * math.cos(lean))
        self.tilt = tilt
        for i, (c, r) in enumerate(sp['torso']):
            F.add(*S.Ell(tilt(c), r, S.rot(-lean, 0, 0)), k=0.08)
        torso_only = S.Field()
        for c, r in sp['torso']:
            torso_only.add(*S.Ell(tilt(c), r, S.rot(-lean, 0, 0)), k=0.08)
        arms = {}
        for s, key in ((-1, 'r'), (1, 'l')):
            Sh, E, W = self._arm(s, key)
            arms[key] = (Sh, E, W)
            r0, r1 = sp['arm_r']
            F.add(*S.Cone(tuple(Sh), tuple(E), r0, (r0 + r1) / 2), k=0.03)
            F.add(*S.Cone(tuple(E), tuple(W), (r0 + r1) / 2, r1), k=0.02)
        legs = {}
        lp = LEGS[p['legs']] if isinstance(p['legs'], str) else p['legs']
        lk = (sp['leg'][0] + sp['leg'][1]) / 0.146
        fk = sp.get('foot_k', 1.0)
        armF = S.Field()
        for key in ('r', 'l'):
            Sh, E, W = arms[key]
            armF.add(*S.Cone(tuple(Sh), tuple(E), sp['arm_r'][0], sp['arm_r'][1]))
            armF.add(*S.Cone(tuple(E), tuple(W), sp['arm_r'][0], sp['arm_r'][1]))
        for s, key, (fx, fy, fz) in ((-1, 'r', lp[0]), (1, 'l', lp[1])):
            Hh = np.array([s * sp['hip'][0], sp['hip'][1], sp['hip'][2]])
            A = np.array([s * fx * sp['hip'][0] / 0.062, fy * lk, 0.064 * fk + (fz - 0.064) * lk])
            pole = np.array([0, -1.0, 0.3]) if p['legs'] not in ('sit', 'floor') else np.array([0, -0.2, 1.0])
            Kn, A = ik2(Hh, A, sp['leg'][0], sp['leg'][1], pole, stretch=1.2)
            legs[key] = (Hh, Kn, A)
            r0, r1 = sp['leg_r']
            F.add(*S.Cone(tuple(Hh + np.array([0, 0, 0.03])), tuple(Kn), r0, (r0 + r1) / 2), k=0.04)
            F.add(*S.Cone(tuple(Kn), tuple(A), (r0 + r1) / 2, r1), k=0.02)
        lump = Lump(3, 0.0016, 18)
        fbody = lambda P: F(P) + lump(P)
        lo, hi = fbounds(F, 0.03)
        ob = piece(self.name + '_lijf', fbody, lo, hi, cloth, root, h=0.0036 * sp.get('res_k', 1.0))
        if pants is not None:
            # broek: alles onder de riem dat niet bij een arm hoort
            me = ob.data
            me.materials.append(pants)
            V = np.empty(len(me.vertices) * 3, np.float32)
            me.vertices.foreach_get('co', V)
            V = V.reshape(-1, 3)
            low = (V[:, 2] < sp['belt_z']) & (armF(V.astype(F32)) > 0.012)
            fi = np.empty(len(me.loops), np.int32)
            me.loops.foreach_get('vertex_index', fi)
            fi = fi.reshape(-1, 4)
            me.polygons.foreach_set('material_index', low[fi[:, 0]].astype(np.int32))
        self.fbody = fbody
        # ---- handen (wanten met duimpje)
        self.hands = {k: (arms[k][2], _n(arms[k][2] - arms[k][1])) for k in arms}
        for s, key in ((-1, 'r'), (1, 'l')):
            Sh, E, W = arms[key]
            d = _n(W - E)
            hcen = W + d * (sp['hand_r'] * 0.75)
            thumb_dir = _n(np.array([0, -1.0, 0.4]) - d * np.dot(np.array([0, -1.0, 0.4]), d))
            if np.linalg.norm(thumb_dir) < 1e-3:
                thumb_dir = np.array([0, 0, 1.0])
            Fh = S.Field()
            hk = sp['hand_r'] / 0.039
            Fh.add(*S.Cone(tuple(W - d * 0.005), tuple(hcen + d * 0.012 * hk), sp['hand_r'] * 0.82, sp['hand_r']))
            Fh.add(*S.Sph(tuple(hcen + thumb_dir * 0.026 * hk - d * 0.006), 0.0135 * hk), k=0.012)
            piece(self.name + f'_hand{key}', Fh, *fbounds(Fh, 0.02), skin, root, h=0.0026,
                  attrs_fn=lambda V: {'paint': ('POINT', np.ones((len(V), 3), F32))})
            # manchet
            Fc = S.Field()
            Fc.add(*S.Cone(tuple(W - d * 0.024), tuple(W - d * 0.006), sp['arm_r'][1] + 0.004, sp['arm_r'][1] + 0.005))
            piece(self.name + f'_manchet{key}', Fc, *fbounds(Fc, 0.01), cloth2 if not pj else cloth2, root, h=0.0024)
        # ---- schoenen of blote voetjes
        for s, key in ((-1, 'r'), (1, 'l')):
            Hh, Kn, A = legs[key]
            fwd = np.array([s * 0.12, -1.0, 0.0])
            fwd = _n(fwd)
            Fs = S.Field()
            c = A + fwd * 0.026 * fk + np.array([0, 0, -0.03 * fk])
            Fs.add(*S.Ell(tuple(c), (0.047 * fk, 0.074 * fk, 0.038 * fk), S.rot(0, 0, math.atan2(fwd[0], -fwd[1]))))
            Fs.add(*S.Sph(tuple(A + np.array([0, 0.004, -0.004])), 0.044 * fk), k=0.03)
            zcut = c[2] - 0.03 * fk
            fs = lambda P, Fs=Fs, zcut=zcut: S.smax(Fs(P), zcut - P[:, 2], 0.004)
            lo, hi = fbounds(Fs, 0.02)
            piece(self.name + f'_schoen{key}', fs, lo, hi, shoe_m, root, h=0.003,
                  attrs_fn=(lambda V: {'paint': ('POINT', np.ones((len(V), 3), F32))}) if pj else None)
            if not pj:
                # zool: lichtere rand
                fz = lambda P, fs=fs, zcut=zcut: S.smax(fs(P) - 0.003, P[:, 2] - zcut - 0.008, 0.002)
                piece(self.name + f'_zool{key}', fz, lo, hi, wol('Vilt grijs', '#8b8d94'), root, h=0.0024)
        # ---- kleding-details
        self._details(torso_only, cloth2, black, thread)
        # ---- hoofd
        self._head(skin)
        rl = list(p['root'])
        if p['legs'] == 'floor':
            rl[2] -= sp['hip'][2] - sp['leg_r'][0] * 0.85
        root.location = rl
        root.rotation_euler = (0, 0, math.radians(p['yaw']))
        return root

    def _materials(self):
        sp = self.spec
        pj = self.outfit == 'pyjama'
        skin = wol('Vilt huid', sp['skin'], attr='paint')
        cloth = wol('Vilt pyjama', '#8fc1e3') if pj else wol('Vilt politieblauw', sp['navy'])
        cloth2 = wol('Vilt pyjama licht', '#d9ecf7', sheet=True) if pj else wol('Vilt blauw licht', sp['navy2'],
                                                                                  sheet=True)
        black = wol('Vilt zwart', sp['black'])
        thread = garen('Garen lichtblauw', '#cbd6f0') if not pj else garen('Garen wit', '#ffffff')
        return skin, cloth, cloth2, black, thread, None, (skin if pj else black)

    def _details(self, T, cloth2, black, thread):
        if self.outfit == 'pyjama':
            self._pyjama(T, cloth2, thread)
        else:
            self._uniform(T, cloth2, black, thread)

    def _uniform(self, T, cloth2, black, thread):
        sp, root = self.spec, self.root
        fb = self.fbody
        star_m = wol('Vilt geel', sp['star'], sheet=True)
        beads = kraal('Knoopje grijs', '#aeb3bd')
        # kraag: zachte rol om de hals met twee punten voor
        hc = self.hc
        zc = hc[2] - 0.135
        self._collar(T, zc, cloth2)
        zb = sp['belt_z']
        for s in (-1, 1):
            tri = np.array([(s * 0.004, 0.0), (s * 0.05, 0.004), (s * 0.016, -0.036)])
            tri = _densify(np.concatenate([tri, tri[:1]]), 5)[:-1]
            applique(self.name + f'_kraagpunt{s}', fb, (0, -0.2, zc - 0.012), tri, 0.0035, cloth2, root,
                     stitch=thread, inset=0.004)
        # knoopsluiting: stiksel en knoopjes
        P2 = np.array([(0.0, 0.0), (0.0, -((zc - 0.045) - (zb + 0.02)))])
        c, n0 = surf(fb, (0, -0.2, zc - 0.045))
        u, v = frame(n0)
        line = c + _densify(P2, 40)[:, :1] * u + _densify(P2, 40)[:, 1:2] * v
        q, nq = to_surf(fb, line)
        stitches(self.name + '_beleg', q + nq * 0.0008 + u * 0.01, nq, thread, root)
        for z in np.linspace(zc - 0.06, zb + 0.04, 3):
            q, nq = surf(fb, (0, -0.2, z))
            K.blob(self.name + f'_knoop{z:.2f}', (0.0065, 0.0065, 0.003), 2.2, (16, 10), mat=beads, parent=root,
                   loc=tuple(q + nq * 0.002), rot=tuple(_rot_to(nq)))
        # borstzakken met klep, knoopje; ster links op de borst
        for s in (-1, 1):
            anc = (s * 0.058, -0.2, zc - 0.095)
            applique(self.name + f'_zak{s}', fb, anc, rrect(0.05, 0.044, 0.01), 0.003, cloth2, root, stitch=thread)
            anc2 = (s * 0.058, -0.2, zc - 0.07)
            applique(self.name + f'_klep{s}', fb, anc2, rrect(0.056, 0.017, 0.006), 0.003, cloth2, root, lift=0.003,
                     stitch=thread, inset=0.003)
            q, nq = surf(fb, anc2)
            K.blob(self.name + f'_zakknoop{s}', (0.005, 0.005, 0.0025), 2.2, (14, 8), mat=beads, parent=root,
                   loc=tuple(q + nq * 0.0072), rot=tuple(_rot_to(nq)))
        applique(self.name + '_ster', fb, (0.062, -0.2, zc - 0.037), star(0.02, 0.0085), 0.0034, star_m, root,
                 lift=0.0005, stitch=garen('Garen goud', '#9a6d12'), inset=0.0032)
        # schouderlusjes
        for s in (-1, 1):
            a = np.array([s * 0.085, 0.0, zc + 0.03])
            applique(self.name + f'_epaulet{s}', fb, a + np.array([0, 0, 0.08]), rrect(0.05, 0.02, 0.008), 0.003,
                     cloth2, root, up=(0, -1, 0), stitch=thread, inset=0.0035, ray=(0, 0, -1))
        # riem met gesp
        fr = lambda P: S.smax(T(P) - 0.0075 + self._lump_b(P), np.abs(P[:, 2] - zb) - 0.017, 0.003)
        piece(self.name + '_riem', fr, (-0.2, -0.2, zb - 0.04), (0.2, 0.2, zb + 0.04), black, root, h=0.0026)
        applique(self.name + '_gesp', fr, (0, -0.2, zb), rrect(0.036, 0.028, 0.005), 0.0028,
                 wol('Vilt zilvergrijs', '#b7bcc6', sheet=True), root)
        applique(self.name + '_gespgat', fr, (0, -0.2, zb), rrect(0.022, 0.014, 0.003), 0.0012, black, root,
                 lift=0.0028, bevel=False)
        # portofoon op de rechterheup
        Fr = S.Field()
        Fr.add(*S.Box((-0.135, -0.035, zb - 0.025), (0.013, 0.021, 0.034), 0.008, S.rot(0, 0, 0.5)))
        Fr.add(*S.Cap((-0.137, -0.03, zb + 0.005), (-0.137, -0.03, zb + 0.055), 0.0048), k=0.004)
        piece(self.name + '_portofoon', Fr, *fbounds(Fr, 0.02), black, root, h=0.0022)
        K.blob(self.name + '_led', (0.003, 0.003, 0.003), 2, (8, 6), mat=M.emission('Lampje', '#ff4040', 6),
               parent=root, loc=(-0.137, -0.045, zb + 0.02))

    def _lump_b(self, P):
        return 0.0

    def _collar(self, T, zc, mat):
        hc = self.hc
        rx = abs(hit(T, (0.4, hc[1], zc), (-1, 0, 0))[0])
        ry = abs(hit(T, (0.0, -0.4, zc), (0, 1, 0))[1] - hc[1])
        Rr = (rx + ry) / 2 + 0.004
        Fk = S.Field()
        Fk.add(*S.Tor((hc[0], hc[1] + 0.004, zc), Rr, 0.015))
        piece(self.name + '_kraag', Fk, *fbounds(Fk, 0.01), mat, self.root, h=0.0026)

    def _pyjama(self, T, cloth2, thread):
        sp, root = self.spec, self.root
        fb = self.fbody
        hc = self.hc
        zc = hc[2] - 0.135
        self._collar(T, zc, cloth2)
        # stippen/sterretjes op de pyjama
        rng = np.random.default_rng(4)
        ym = wol('Vilt geel', sp['star'], sheet=True)
        for i in range(14):
            z = rng.uniform(0.2, zc - 0.03)
            a = rng.uniform(-1.1, 1.1)
            anc = (math.sin(a) * 0.2, -math.cos(a) * 0.2, z)
            applique(self.name + f'_pjster{i}', fb, anc, star(0.011, 0.005), 0.002, ym, root, bevel=False)

    # ------------------------------------------------------------------ hoofd
    def _head(self, skin):
        sp, p, e = self.spec, self.p, self.e
        pitch, yaw, roll = [math.radians(v) for v in p['head']]
        piv = K.empty(self.name + '_hoofd', tuple(self.hc), (0, 0, 0), 1.0, self.root)
        piv.rotation_mode = 'YXZ'
        piv.rotation_euler = (math.radians(p['lean']) - pitch, roll, yaw)
        self.head_root = piv
        hr = sp['head_r']
        F = S.Field()
        F.add(*S.Ell((0, 0, 0), hr))
        for s in (-1, 1):
            F.add(*S.Sph((s * 0.066, -0.088, -0.062), 0.07), k=0.05)
        F.add(*S.Sph((0, -0.07, -0.098), 0.06), k=0.05)
        # oren
        for s in (-1, 1):
            F.add(*S.Ell((s * 0.146, 0.006, -0.012), (0.02, 0.034, 0.043), S.rot(0, 0, -s * 0.35)), k=0.012)
            F.cut(*S.Sph((s * 0.167, -0.004, -0.012), 0.02), k=0.008)
        base = F
        # neusje: bolletje op het oppervlak
        qn, nn_ = surf(base, (0, -0.2, -0.022))
        q = [qn]
        F.add(*S.Sph(tuple(qn + nn_ * 0.007), 0.019), k=0.008)
        lump = Lump(11, 0.0011, 24)
        fh = lambda P: F(P) + lump(P)
        self.fhead = fh

        def paint(V):
            col = np.ones((len(V), 3), F32)
            g = lambda c, s: np.exp(-((V - np.asarray(c, F32)) ** 2).sum(1) / (2 * s * s))
            b = 0.8 * e['blush']
            for s in (-1, 1):
                w = (b * g((s * 0.076, -0.13, -0.045), 0.026))[:, None]
                col = col * (1 - w) + col * np.array([1.0, 0.6, 0.58], F32) * w
                w = (0.5 * g((s * 0.16, -0.0, -0.012), 0.03))[:, None]
                col = col * (1 - w) + col * np.array([1.0, 0.72, 0.68], F32) * w
            w = (0.45 * g(q[0], 0.022))[:, None]
            col = col * (1 - w) + col * np.array([1.0, 0.74, 0.7], F32) * w
            return {'paint': ('POINT', col)}
        piece(self.name + '_kop', fh, (-0.2, -0.2, -0.19), (0.2, 0.19, 0.17), skin, piv, h=0.0028, attrs_fn=paint)
        self._face(fh, piv)
        self._hair(fh, piv)
        if self.cap:
            lift = p.get('cap_lift', 0.0)
            police_cap(self.name + '_pet', piv, 1.0, loc=(0, 0.004, 0.006 + lift),
                       rot=tuple(p.get('cap_rot', (-0.12, 0, 0))))

    def _face(self, fh, piv):
        e, fp = self.e, self.fp
        white = wol('Vilt oogwit', '#faf6ee', sheet=True, fuzz=0.3)
        iris = wol('Vilt iris ' + fp['iris_col'], fp['iris_col'], sheet=True, fuzz=0.2)
        pupil = kraal('Oogkraal')
        brow_m = wol('Vilt wenkbrauw ' + fp['brow_col'], fp['brow_col'], sheet=True)
        dark = garen('Garen bruin', '#3b2a22')
        lx, lz = e['look']
        ea, eb, ir = fp['eye_a'], fp['eye_b'], fp['iris']
        for s in (-1, 1):
            anc = (s * fp['eye_x'], -0.3, fp['eye_z'])
            if e['eyes'] == 'closed':
                arc = [(x, -0.006 * (1 - (x / (ea * 0.88)) ** 2)) for x in np.linspace(-ea * 0.88, ea * 0.88, 9)]
                thread_line(self.name + f'_slaapoog{s}', fh, anc, arc, dark, piv, r=0.0018)
                continue
            if e['eyes'] == 'happy':
                arc = [(x, 0.009 * (1 - (x / (ea * 0.88)) ** 2)) for x in np.linspace(-ea * 0.88, ea * 0.88, 9)]
                thread_line(self.name + f'_lachoog{s}', fh, anc, arc, dark, piv, r=0.0019)
                continue
            applique(self.name + f'_oogwit{s}', fh, anc, ellipse(ea, eb), 0.0026, white, piv)
            ic = (lx * (ea - ir) * 0.95, -0.002 + lz * (eb - ir) * 0.6)
            applique(self.name + f'_iris{s}', fh, anc, ellipse(ir, ir * 1.05, c=ic), 0.0012, iris, piv, lift=0.0026,
                     bevel=False)
            # pupil: glanzende kraal (vangt echte lichtjes)
            c, nq = surf(fh, anc)
            u, v = frame(nq)
            pc = c + u * ic[0] + v * ic[1]
            pc, pn = to_surf(fh, [pc])
            pr = fp['pupil']
            K.blob(self.name + f'_pupil{s}', (pr, pr, pr * 0.57), 2.0, (20, 12), mat=pupil, parent=piv,
                   loc=tuple(pc[0] + pn[0] * 0.0036), rot=tuple(_rot_to(pn[0])))
            # wimperlijn boven het oogwit
            t = np.linspace(math.radians(15), math.radians(165), 12)
            arc = np.stack([(ea + 0.0015) * np.cos(t), (eb + 0.0015) * np.sin(t) - 0.001], 1)
            if s < 0:
                arc = arc[::-1]
            if fp['lash']:
                thread_line(self.name + f'_wimper{s}', fh, anc, arc, dark, piv, r=0.0014, lift=0.0026)
        # wenkbrauwen: vilten boogjes
        tilt = {'neutral': 0.0, 'up': 0.0, 'worried': 0.35, 'cross': -0.35}.get(e['brows'], 0.0)
        bz = fp['brow_z'] + (0.01 if e['brows'] in ('up', 'worried') else 0.0)
        bw = fp['brow_w']
        for s in (-1, 1):
            t = np.linspace(math.radians(20), math.radians(160), 10)
            outer = np.stack([bw * np.cos(t), 0.3 * bw * np.sin(t)], 1)
            inner = np.stack([0.9 * bw * np.cos(t[::-1]), 0.125 * bw * np.sin(t[::-1]) - 0.1 * bw], 1)
            cr = np.concatenate([outer, inner])
            a = -s * tilt
            R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
            applique(self.name + f'_wenkbrauw{s}', fh, (s * fp['brow_x'], -0.3, bz), cr @ R.T, 0.0022, brow_m, piv,
                     bevel=False)
        # mond
        mouth = e['mouth']
        mz, mw0 = fp['mouth_z'], fp['mouth_w']
        anc = (0, -0.3, mz)
        red = garen('Garen roze', '#b0484f')
        dm = wol('Vilt mond', '#7c2230', sheet=True, fuzz=0.3)
        if mouth in ('smile', 'sad', 'flat'):
            k = {'smile': 1.0, 'sad': -0.8, 'flat': 0.0}[mouth]
            pts = [(x, 0.011 * k * (x / mw0) ** 2) for x in np.linspace(-mw0, mw0, 11)]
            thread_line(self.name + '_mond', fh, anc, pts, red, piv, r=0.0019)
        elif mouth in ('grin', 'open'):
            w = mw0 if mouth == 'grin' else mw0 * 0.8
            hgt = mw0 * 0.7 if mouth == 'grin' else mw0 * 0.8
            t = np.linspace(0, math.pi, 16)
            top = [(x, 0.006 * (x / w) ** 2 * (1 if mouth == 'grin' else 0.3)) for x in np.linspace(w, -w, 12)]
            bot = [(-w * math.cos(a), -hgt * math.sin(a)) for a in t[1:-1]]
            out = np.array(top + bot)[::-1]
            applique(self.name + '_mondopen', fh, anc, out, 0.0016, dm, piv, bevel=False)
            applique(self.name + '_tong', fh, (0, -0.3, mz - hgt * 0.62), ellipse(w * 0.5, hgt * 0.28), 0.001,
                     wol('Vilt tong', '#e07a86', sheet=True, fuzz=0.2), piv, lift=0.0016, bevel=False)
            thread_line(self.name + '_mondrand', fh, anc, np.concatenate([out, out[:1]]), red, piv, r=0.0013,
                        lift=0.0012)
        elif mouth == 'o':
            applique(self.name + '_mondo', fh, (0, -0.3, mz - 0.004), ellipse(mw0 * 0.34, mw0 * 0.44), 0.0016, dm, piv,
                     bevel=False)

    def _hair(self, fh, piv):
        hr = self.spec['head_r']
        hair = wol('Vilt blond', self.spec['hair'], fuzz=1.8)
        base = lambda P: S.ellipsoid(P, (0, 0, 0), hr)
        xs = [0, 35, 70, 100, 140, 180]
        zs = [0.084, 0.075, 0.05, 0.026, -0.03, -0.055]

        def region(P):
            az = np.degrees(np.abs(np.arctan2(P[:, 0], -P[:, 1])))
            return np.interp(az, xs, zs).astype(F32) - P[:, 2]
        def grooves(P):
            w = np.clip((P[:, 2] - 0.06) / 0.07, 0, 1).astype(F32)
            top = np.sin(P[:, 0] * 120 + 6 * np.sin(P[:, 1] * 25))
            side = np.sin(np.arctan2(P[:, 0], -P[:, 1]) * 26 + P[:, 2] * 40)
            return F32(0.0016) * (w * top + (1 - w) * side)
        F = S.Field()
        def thick(P):
            az = np.degrees(np.abs(np.arctan2(P[:, 0], -P[:, 1])))
            hl = np.interp(az, xs, zs).astype(F32)
            return F32(0.0035) + F32(0.011) * np.clip((P[:, 2] - hl) / 0.035, 0, 1).astype(F32)
        F.add(lambda P: S.smax(base(P) - thick(P) + grooves(P), region(P), 0.004), bound=((0, 0, 0), 0.25))
        if not self.cap:
            # kuif: dikke wollen lokken die vooraan omhoog en naar achter krullen
            # onderlaag van de kuif; de lokken zelf zijn losse wol (zie onder)
            F.add(*S.Ell((0, -0.045, 0.112), (0.108, 0.09, 0.05)), k=0.03)
            for s in (-1, 1):
                F.add(*S.Chain([(s * 0.1, -0.06, 0.11), (s * 0.13, -0.02, 0.13), (s * 0.12, 0.03, 0.15)],
                               [0.02, 0.02, 0.014]), k=0.02)
        else:
            # plukjes onder de pet uit: boven de oren en in de nek
            for s in (-1, 1):
                for j, (y, z) in enumerate(((-0.07, 0.07), (-0.035, 0.06), (0.0, 0.055), (0.04, 0.05))):
                    a = np.array([s * 0.13, y, z + 0.02])
                    b = np.array([s * 0.158, y - 0.012, z - 0.022])
                    F.add(*S.Cone(tuple(a), tuple(b), 0.014, 0.006), k=0.01)
            for x in (-0.03, 0.0, 0.03):
                F.add(*S.Cone((x, -0.12, 0.096), (x * 1.3, -0.142, 0.072), 0.014, 0.006), k=0.01)
        lump = Lump(17, 0.0012, 30)
        f = lambda P: F(P) + lump(P)
        piece(self.name + '_haar', f, (-0.21, -0.22, -0.12), (0.21, 0.21, 0.24), hair, piv, h=0.0027)
        if not self.cap:
            self._wool_locks(f, piv)

    def _wool_locks(self, f, piv):
        """Kuif van losse lokjes wol (roving), op de vilten onderlaag gezet."""
        from . import hair as H
        k = 0.15
        unit = K.empty(self.name + '_wolruimte', (0, 0, 0), (0, 0, 0), k, piv)

        class _U:
            name = self.name + '_wol'
            root = unit

            def shape(_, D):
                D = np.asarray(D, F32)
                lo = np.full(len(D), 0.05, F32)
                hi = np.full(len(D), 0.32, F32)
                for _i in range(22):
                    mid = (lo + hi) / 2
                    inside = f(D * mid[:, None]) < 0
                    lo = np.where(inside, mid, lo)
                    hi = np.where(inside, hi, mid)
                return (D * ((lo + hi) / 2)[:, None] / k).astype(float)
        H._HL = [0.5, 0.48, 0.38, 0.22, 0.08, -0.1, -0.3, -0.4]
        rng = np.random.default_rng(5)
        D = _n(rng.normal(size=(90000, 3)))
        w = H.scalp_mask(D) * H.top_weight(D)
        D = D[rng.random(len(D)) < w][:30000]
        mat = _cached('Wol blond')
        if mat is None:
            mat = M.hair_color_mat('Wol blond', color='#e8c262', rough=0.5, radial=0.9)
            _MC['Wol blond'] = mat
        H._locks(_U(), D, {'hair': mat}, rng, kind='kuif', mess=1.2)


def _rot_to(n):
    """Euler-rotatie die de lokale z-as op n zet."""
    from mathutils import Vector
    q = Vector((0, 0, 1)).rotation_difference(Vector(tuple(n)))
    return q.to_euler()


# ------------------------------------------------------------------ Joep
JARMS = {
    'down': ((0.03, -0.01, -0.11), (1, 0.3, 0)),
    'up': ((0.05, -0.02, 0.12), (1, 0.3, 0)),
    'wave': ((0.08, -0.02, 0.08), (1, 0.3, -0.6)),
    'hug': ((-0.035, -0.07, -0.02), (1, 0.2, -0.5)),
    'forward': ((0.0, -0.11, 0.0), (1, 0.0, -0.6)),
    'hold': ((-0.03, -0.085, -0.05), (1, 0.2, -0.5)),
    'side': ((0.12, -0.02, -0.03), (0.3, 0.2, -1)),
}
JLEGS = {
    'sit': [(0.04, -0.13, 0.015), (0.04, -0.13, 0.015)],
    'hang': [(0.035, -0.02, -0.11), (0.04, -0.03, -0.1)],
    'stand': [(0.032, -0.0, -0.065), (0.032, 0.0, -0.065)],
    'dangle': [(0.04, -0.08, -0.08), (0.045, -0.1, -0.05)],
}


class Joep:
    """Viltpop Joep: bruin wollen aapje met crème gezichtje, kraaloogjes, lange slungelarmen en -benen.
    Oorsprong = onderkant van het lijfje. pose: root, rot (rx, ry, rz radialen) of yaw (graden),
    arm_r/arm_l (JARMS of (dx,dy,dz)), legs (JLEGS), head (pitch, yaw, roll graden), cap, scale."""

    def __init__(self, name='Joep', pose=None, expr=None, cap=True, mats=None, **kw):
        self.name = name
        self.p = dict(root=(0, 0, 0), rot=None, yaw=0.0, arm_r='down', arm_l='down', legs='sit', head=(0, 0, 0),
                      scale=1.0, salute=None)
        self.p.update(pose or {})
        self.e = dict(mouth='smile')
        self.e.update(expr or {})
        self.cap = self.p.get('cap', cap)

    def build(self):
        p = self.p
        root = K.empty(self.name, p['root'], (0, 0, 0), p['scale'])
        if p['rot'] is not None:
            root.rotation_euler = p['rot']
        else:
            root.rotation_euler = (0, 0, math.radians(p['yaw']))
        self.root = root
        brown = wol('Vilt aapbruin', '#9a5a2c', fuzz=1.6)
        cream = wol('Vilt crème', '#efd5aa', attr='paint')
        cream_s = wol('Vilt crème plat', '#efd5aa', sheet=True)
        ones = lambda V: {'paint': ('POINT', np.ones((len(V), 3), F32))}
        F = S.Field()
        F.add(*S.Ell((0, 0, 0.066), (0.053, 0.047, 0.066)))
        F.add(*S.Ell((0, -0.004, 0.035), (0.058, 0.052, 0.04)), k=0.03)
        sh = {}
        for s, key in ((-1, 'r'), (1, 'l')):
            Sh = np.array([s * 0.042, 0.0, 0.112])
            a = p['arm_' + key]
            if a == 'salute':
                W = np.array([s * 0.062, -0.045, 0.24])
                pole = np.array([s, 0.2, -0.5])
            else:
                off, pole = JARMS[a] if isinstance(a, str) else (a, (1, 0.3, -0.3))
                W = Sh + np.array([s * off[0], off[1], off[2]])
                pole = np.array([s * pole[0], pole[1], pole[2]])
            E, W = ik2(Sh, W, 0.075, 0.075, pole, stretch=1.3)
            F.add(*S.Cone(tuple(Sh), tuple(E), 0.017, 0.015), k=0.012)
            F.add(*S.Cone(tuple(E), tuple(W), 0.015, 0.014), k=0.006)
            sh[key] = (Sh, E, W)
        legs = {}
        for s, key, (fx, fy, fz) in ((-1, 'r', JLEGS[p['legs']][0]), (1, 'l', JLEGS[p['legs']][1])):
            Hh = np.array([s * 0.03, -0.012, 0.03])
            A = np.array([s * fx, fy, fz])
            Kn, A = ik2(Hh, A, 0.065, 0.065, np.array([0, -0.3, 1.0]) if p['legs'] == 'sit' else np.array([0, -1, 0.2]),
                        stretch=1.3)
            F.add(*S.Cone(tuple(Hh), tuple(Kn), 0.019, 0.016), k=0.014)
            F.add(*S.Cone(tuple(Kn), tuple(A), 0.016, 0.015), k=0.006)
            legs[key] = (Hh, Kn, A)
        # staart: krulletje achter
        F.add(*S.Chain([(0, 0.045, 0.03), (0.0, 0.08, 0.03), (0.01, 0.1, 0.06), (0.0, 0.095, 0.095),
                        (-0.012, 0.075, 0.1)], [0.011, 0.01, 0.009, 0.009, 0.008]), k=0.01)
        lump = Lump(41, 0.0009, 40)
        fb = lambda P: F(P) + lump(P)
        piece(self.name + '_lijf', fb, *fbounds(F, 0.02), brown, root, h=0.0021)
        # buikje
        applique(self.name + '_buik', fb, (0, -0.1, 0.06), ellipse(0.03, 0.036), 0.0022, cream_s, root, bevel=True)
        # handjes en voetjes
        self.hands = {k: (v[2], _n(v[2] - v[1])) for k, v in sh.items()}
        for key, (Sh, E, W) in sh.items():
            d = _n(W - E)
            Fh = S.Field()
            Fh.add(*S.Ell(tuple(W + d * 0.012), (0.019, 0.019, 0.021)))
            piece(self.name + f'_hand{key}', Fh, *fbounds(Fh, 0.01), cream, root, h=0.0018, attrs_fn=ones)
        for key, (Hh, Kn, A) in legs.items():
            d = _n(A - Kn)
            Ff = S.Field()
            fwd = np.array([0, -1.0, 0]) if p['legs'] != 'sit' else _n(np.array([0, -0.3, 1.0]))
            Ff.add(*S.Ell(tuple(A + d * 0.008 + fwd * 0.008), (0.02, 0.026, 0.018)))
            piece(self.name + f'_voet{key}', Ff, *fbounds(Ff, 0.01), cream, root, h=0.0018, attrs_fn=ones)
        # hoofd
        pitch, yaw, roll = [math.radians(v) for v in p['head']]
        piv = K.empty(self.name + '_hoofd', (0, -0.004, 0.198), (-pitch, roll, yaw), 1.0, root)
        piv.rotation_mode = 'YXZ'
        piv.rotation_euler = (-pitch, roll, yaw)
        Fh = S.Field()
        Fh.add(*S.Ell((0, 0, 0), (0.07, 0.064, 0.066)))
        for s in (-1, 1):
            Fh.add(*S.Ell((s * 0.072, 0.004, 0.01), (0.012, 0.03, 0.031), S.rot(0, 0, -s * 0.25)), k=0.01)
        lump2 = Lump(43, 0.0008, 40)
        fh = lambda P: Fh(P) + lump2(P)
        piece(self.name + '_kop', fh, (-0.1, -0.09, -0.09), (0.1, 0.09, 0.09), brown, piv, h=0.0019)
        for s in (-1, 1):
            q, nq = surf(fh, (s * 0.12, -0.01, 0.01), (-s, 0, 0))
            applique(self.name + f'_oorbinnen{s}', fh, q, ellipse(0.017, 0.02), 0.0018, cream_s, piv,
                     up=(0, 0, 1), bevel=False, ray=(-s, 0, 0))
        # gezichtje: crème snuit (bol) en 'pinda' rond de ogen
        Fm = S.Field()
        Fm.add(*S.Ell((0, -0.05, -0.022), (0.042, 0.026, 0.03)))
        fm = Fm
        piece(self.name + '_snuit', fm, (-0.06, -0.09, -0.06), (0.06, -0.01, 0.02), cream, piv, h=0.0016,
              attrs_fn=lambda V: {'paint': ('POINT', np.ones((len(V), 3), F32))})
        th = np.linspace(0, 2 * math.pi, 48, endpoint=False)
        rr = []
        for t in th:
            dvec = np.array([math.cos(t), math.sin(t)])
            best = 0
            for cx in (-0.018, 0.018):
                c = np.array([cx, 0.0])
                b = -2 * c @ dvec
                cc = c @ c - 0.022 ** 2
                disc = b * b - 4 * cc
                if disc > 0:
                    best = max(best, (-b + math.sqrt(disc)) / 2)
            rr.append(best)
        pea = np.stack([np.cos(th) * rr, np.sin(th) * rr], 1)
        applique(self.name + '_gezicht', fh, (0, -0.1, 0.018), pea, 0.0022, cream_s, piv)
        bead = kraal('Oogkraal')
        dark0 = garen('Garen donkerbruin', '#3a2117')
        for s in (-1, 1):
            if self.e.get('eyes') == 'closed':
                arc = [(x, -0.004 * (1 - (x / 0.009) ** 2)) for x in np.linspace(-0.009, 0.009, 7)]
                thread_line(self.name + f'_slaapoog{s}', fh, (s * 0.019, -0.1, 0.02), arc, dark0, piv, r=0.0013,
                            lift=0.0022)
                continue
            q, nq = surf(fh, (s * 0.019, -0.1, 0.02))
            K.blob(self.name + f'_oog{s}', (0.0078, 0.0078, 0.0055), 2.0, (16, 10), mat=bead, parent=piv,
                   loc=tuple(q + nq * 0.0034), rot=tuple(_rot_to(nq)))
        # neusje en glimlach geborduurd op de snuit
        dark = garen('Garen donkerbruin', '#3a2117')
        nose = np.array([(-0.007, 0.0), (0.007, 0.0), (0.0, -0.006)])
        applique(self.name + '_neus', fm, (0, -0.1, -0.008), _densify(np.concatenate([nose, nose[:1]]), 4)[:-1],
                 0.0018, wol('Vilt donkerbruin', '#3a2117', sheet=True, fuzz=0.2), piv, bevel=False)
        if self.e.get('mouth') == 'open':
            applique(self.name + '_mondopen', fm, (0, -0.1, -0.032), ellipse(0.011, 0.009), 0.0015,
                     wol('Vilt mond', '#7c2230', sheet=True, fuzz=0.3), piv, bevel=False)
        else:
            sm = [(x, 0.006 * (x / 0.018) ** 2) for x in np.linspace(-0.018, 0.018, 9)]
            thread_line(self.name + '_mond', fm, (0, -0.1, -0.03), sm, dark, piv, r=0.0012)
        if self.cap:
            police_cap(self.name + '_pet', piv, 0.47, loc=(0.004, 0.006, 0.006), rot=(-0.18, 0.12, 0.0),
                       stitch=False)
        self.body = root
        self.head = piv
        return root


# ------------------------------------------------------------------ bijrollen
def wol_streep(name, c1, c2, period=0.05):
    """Gestreepte wol (boevenshirt): horizontale banen in de objectruimte."""
    m = _cached(name)
    if m:
        return m
    g = M.NT(name)
    co = g.coord('Object')
    x, y, z = g.sep(co)
    st = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', z, 2 * math.pi / period)), 0.0)
    col = g.mix(st, M.C(c1), M.C(c2))
    g.principled(color=col, rough=1.0)
    m = g.done([n for n in g.t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0])
    m['fuzz'] = 1.0
    _MC[name] = m
    return m


AFACE = dict(eye_x=0.043, eye_z=0.024, eye_a=0.0185, eye_b=0.0215, iris=0.0125, pupil=0.0076, brow_x=0.046,
             brow_z=0.064, brow_w=0.019, mouth_z=-0.064, mouth_w=0.03, iris_col='#6b5a44', brow_col='#5a3d26',
             lash=False)

ADULTS = dict(
    bakker=dict(skin='#f0bf9c', head_c=(0, -0.004, 1.0), head_r=(0.126, 0.12, 0.132),
                torso=[((0, 0.0, 0.6), (0.2, 0.18, 0.22)), ((0, 0.004, 0.79), (0.158, 0.13, 0.12))],
                shoulder=(0.142, 0.004, 0.845), arm=(0.165, 0.165), arm_r=(0.052, 0.046), hand_r=0.046,
                hip=(0.078, 0.0, 0.4), leg=(0.18, 0.18), leg_r=(0.07, 0.062), belt_z=0.45, foot_k=1.3,
                lean_z=0.5, res_k=1.3, nose=('bol', 0.03), hair_c='#6e4a2c', chin=0.06,
                face=dict(iris_col='#5d7fa8')),
    lang=dict(skin='#eec3a2', head_c=(0, -0.004, 1.158), head_r=(0.112, 0.11, 0.132),
              torso=[((0, 0.0, 0.74), (0.13, 0.11, 0.2)), ((0, 0.004, 0.93), (0.146, 0.115, 0.11))],
              shoulder=(0.136, 0.004, 0.99), arm=(0.205, 0.205), arm_r=(0.042, 0.037), hand_r=0.043,
              hip=(0.066, 0.0, 0.55), leg=(0.25, 0.25), leg_r=(0.056, 0.05), belt_z=0.6, foot_k=1.3,
              lean_z=0.62, res_k=1.3, nose=('lang', 0.026), hair_c='#3b2a20', chin=0.045, beanie='#1d1d22'),
    dik=dict(skin='#f2c3a0', head_c=(0, -0.006, 0.9), head_r=(0.13, 0.126, 0.128),
             torso=[((0, 0.0, 0.5), (0.23, 0.21, 0.24)), ((0, 0.004, 0.68), (0.18, 0.16, 0.12))],
             shoulder=(0.152, 0.004, 0.735), arm=(0.14, 0.14), arm_r=(0.052, 0.046), hand_r=0.046,
             hip=(0.088, 0.0, 0.28), leg=(0.12, 0.12), leg_r=(0.072, 0.065), belt_z=0.33, foot_k=1.3,
             lean_z=0.36, res_k=1.3, nose=('bol', 0.031), hair_c='#7a3f22', chin=0.07, beanie='#9a2c2c'),
)


class Mens(Daan):
    """Volwassen viltpop: 'bakker', 'lang' (lange boef) of 'dik' (dikke boef).
    mask_up: boevenmasker op het voorhoofd; baker_hat: koksmuts (ook voor de boeven op het feest)."""

    def __init__(self, name, kind='bakker', pose=None, expr=None, mask_up=False, baker_hat=False, mats=None,
                 **kw):
        Daan.__init__(self, name, pose, expr, cap=False, outfit=kind)
        self.kind = kind
        self.spec = dict(DAAN)
        self.spec.update(ADULTS[kind])
        self.fp = dict(AFACE)
        self.fp.update(ADULTS[kind].get('face', {}))
        self.mask_up = mask_up
        self.baker_hat = baker_hat or kind == 'bakker'

    def _materials(self):
        sp = self.spec
        skin = wol('Vilt huid ' + self.kind, sp['skin'], attr='paint')
        black = wol('Vilt zwart', '#1d1d22')
        if self.kind == 'bakker':
            cloth = wol('Vilt bakkerwit', '#eee6d6')
            pants = wol('Vilt bakkerbroek', '#4b4e5c')
        else:
            cloth = wol_streep('Vilt boevenstreep', '#f0ece3', '#202128', 0.05)
            pants = black
        cloth2 = wol('Vilt wit plat', '#fbf8f2', sheet=True)
        return skin, cloth, cloth2, black, garen('Garen wit', '#ffffff'), pants, wol('Vilt schoenbruin', '#4a3426')

    def _details(self, T, cloth2, black, thread):
        sp, root, fb = self.spec, self.root, self.fbody
        hc = self.hc
        red = wol('Vilt rood', '#c63b33')
        # sjaaltje om de hals
        ztop = max(c[2] + r[2] for c, r in sp['torso'])
        zc = min(hc[2] - sp['head_r'][2] * 0.95, ztop - 0.03)
        rx = abs(hit(T, (0.6, hc[1], zc), (-1, 0, 0))[0])
        ry = abs(hit(T, (0.0, -0.6, zc), (0, 1, 0))[1] - hc[1])
        Fk = S.Field()
        Fk.add(*S.Tor((hc[0], hc[1] + 0.004, zc), (rx + ry) / 2 + 0.002, 0.017))
        piece(self.name + '_sjaal', Fk, *fbounds(Fk, 0.01), red if self.kind != 'lang' else
              wol('Vilt sjaalgroen', '#3f7a4a'), root, h=0.003)
        if self.kind == 'bakker':
            # schort met zak en stiksels
            zt, zb = sp['belt_z'] + 0.3, sp['hip'][2] + 0.0
            zm_, hh = (zt + zb) / 2, (zt - zb) / 2
            fa = lambda P: S.smax(S.smax(S.smax(T(P) - 0.007, P[:, 1] + 0.04, 0.01), np.abs(P[:, 2] - zm_) - hh, 0.006),
                                  np.abs(P[:, 0]) - 0.15, 0.006)
            piece(self.name + '_schort', fa, (-0.3, -0.35, zb - 0.03), (0.3, 0.05, zt + 0.03), cloth2, root, h=0.003)
            applique(self.name + '_schortzak', fa, (0.0, -0.4, zb + hh * 0.6), rrect(0.11, 0.07, 0.015), 0.003,
                     cloth2, root, stitch=garen('Garen rood', '#c63b33'), inset=0.006)
        else:
            # riem
            zb = sp['belt_z']
            fr = lambda P: S.smax(T(P) - 0.0075, np.abs(P[:, 2] - zb) - 0.018, 0.003)
            piece(self.name + '_riem', fr, (-0.3, -0.3, zb - 0.04), (0.3, 0.3, zb + 0.04),
                  wol('Vilt riembruin', '#5a3b24'), root, h=0.003)

    def _head(self, skin):
        sp, p, e = self.spec, self.p, self.e
        pitch, yaw, roll = [math.radians(v) for v in p['head']]
        piv = K.empty(self.name + '_hoofd', tuple(self.hc), (0, 0, 0), 1.0, self.root)
        piv.rotation_mode = 'YXZ'
        piv.rotation_euler = (math.radians(p['lean']) - pitch, roll, yaw)
        self.head_root = piv
        hr = sp['head_r']
        F = S.Field()
        F.add(*S.Ell((0, 0, 0), hr))
        for s_ in (-1, 1):
            F.add(*S.Sph((s_ * 0.058, -0.068, -0.05), 0.052), k=0.04)
        F.add(*S.Sph((0, -0.06, -0.09), sp['chin']), k=0.05)
        for s_ in (-1, 1):
            F.add(*S.Ell((s_ * hr[0] * 0.96, 0.006, -0.01), (0.018, 0.032, 0.04), S.rot(0, 0, -s_ * 0.3)), k=0.012)
            F.cut(*S.Sph((s_ * (hr[0] * 0.96 + 0.019), -0.004, -0.01), 0.018), k=0.008)
        qn, nn_ = surf(F, (0, -0.3, -0.018))
        kind, nr = sp['nose']
        if kind == 'lang':
            F.add(*S.Ell(tuple(qn + nn_ * 0.012 + np.array([0, -0.006, -0.004])), (nr * 0.75, nr * 1.4, nr * 0.85)),
                  k=0.01)
        else:
            F.add(*S.Sph(tuple(qn + nn_ * 0.01), nr), k=0.01)
        lump = Lump(13, 0.0011, 22)
        fh = lambda P: F(P) + lump(P)
        self.fhead = fh

        def paint(V):
            col = np.ones((len(V), 3), F32)
            g = lambda c, s: np.exp(-((V - np.asarray(c, F32)) ** 2).sum(1) / (2 * s * s))
            for s_ in (-1, 1):
                w = (0.6 * g((s_ * 0.066, -0.1, -0.04), 0.024))[:, None]
                col = col * (1 - w) + col * np.array([1.0, 0.62, 0.6], F32) * w
            w = (0.55 * g(qn + nn_ * 0.03, 0.03))[:, None]
            col = col * (1 - w) + col * np.array([1.0, 0.7, 0.66], F32) * w
            return {'paint': ('POINT', col)}
        piece(self.name + '_kop', fh, (-0.2, -0.22, -0.19), (0.2, 0.19, 0.2), skin, piv, h=0.0028, attrs_fn=paint)
        face_f = fh
        black = wol('Vilt zwart', '#1d1d22')
        if self.kind != 'bakker':
            # boevenmasker: zwarte band over de ogen (of omhoog op het voorhoofd)
            zm = self.fp['eye_z'] + (0.062 if self.mask_up else 0.0)
            fm = lambda P, zm=zm: S.smax(S.smax(fh(P) - 0.004, np.abs(P[:, 2] - zm) - 0.024, 0.006), P[:, 1] - 0.03,
                                          0.01)
            piece(self.name + '_masker', fm, (-0.2, -0.22, zm - 0.05), (0.2, 0.1, zm + 0.05), black, piv, h=0.0024)
            if not self.mask_up:
                face_f = lambda P, fm=fm: np.minimum(fh(P), fm(P))
            # zwarte stoppels-plukjes haar opzij
            hairm = wol('Vilt haar ' + self.kind, sp['hair_c'], fuzz=1.6)
            Fhh = S.Field()
            for s_ in (-1, 1):
                for y, z in ((-0.02, 0.05), (0.02, 0.045), (0.06, 0.035)):
                    Fhh.add(*S.Cone((s_ * hr[0] * 0.92, y, z + 0.02), (s_ * hr[0] * 1.05, y - 0.006, z - 0.02), 0.014,
                                    0.006), k=0.008)
            piece(self.name + '_plukjes', Fhh, *fbounds(Fhh, 0.01), hairm, piv, h=0.0024)
        self._face(face_f, piv)
        if self.kind == 'bakker':
            # snor
            snor = wol('Vilt snor', sp['hair_c'], fuzz=1.5)
            Fs = S.Field()
            for s_ in (-1, 1):
                a = qn + np.array([s_ * 0.008, -0.004, -0.03])
                Fs.add(*S.Cone(tuple(a), tuple(a + np.array([s_ * 0.055, 0.022, -0.004])), 0.019, 0.008), k=0.012)
            piece(self.name + '_snor', Fs, *fbounds(Fs, 0.01), snor, piv, h=0.0018)
            # haar opzij en achter
            hairm = wol('Vilt haar bakker', sp['hair_c'], fuzz=1.6)
            base = lambda P: S.ellipsoid(P, (0, 0, 0), hr)

            def region(P):
                az = np.degrees(np.abs(np.arctan2(P[:, 0], -P[:, 1])))
                return np.maximum(np.maximum(-0.04 - P[:, 2], P[:, 2] - 0.07), (55 - az) * 0.004).astype(F32)
            fhb = lambda P: S.smax(base(P) - 0.01, region(P), 0.006)
            piece(self.name + '_haar', fhb, (-0.2, -0.2, -0.08), (0.2, 0.2, 0.12), hairm, piv, h=0.0026)
        if self.baker_hat:
            chef_hat(self.name + '_koksmuts', piv, hr)
        elif self.kind != 'bakker':
            beanie(self.name + '_muts', piv, hr, sp['beanie'])


def chef_hat(name, parent, hr):
    white = wol('Vilt koksmuts', '#fbfaf6')
    F = S.Field()
    zb = hr[2] * 0.45
    F.add(*S.Cap((0, 0, zb), (0, 0, zb + 0.07), hr[0] * 0.98))
    for i in range(6):
        a = i * math.pi / 3
        F.add(*S.Sph((math.cos(a) * 0.075, math.sin(a) * 0.07, zb + 0.15), 0.07), k=0.03)
    F.add(*S.Sph((0, 0, zb + 0.175), 0.08), k=0.03)
    lump = Lump(51, 0.0018, 20)
    f = lambda P: S.smax(F(P) + lump(P), zb - 0.01 - P[:, 2], 0.004)
    piece(name, f, (-0.2, -0.2, zb - 0.03), (0.2, 0.2, zb + 0.3), white, parent, h=0.0035)


def beanie(name, parent, hr, color):
    m = wol('Vilt muts ' + color, color, fuzz=1.4)
    zb = hr[2] * 0.18
    base = lambda P: S.ellipsoid(P, (0, 0.004, 0.008), (hr[0] + 0.012, hr[1] + 0.012, hr[2] + 0.016))
    rib = lambda P: F32(0.0016) * np.sin(np.arctan2(P[:, 0], -P[:, 1]) * 30)
    dome = lambda P: S.smax(base(P) + rib(P), zb - P[:, 2], 0.004)
    Fb = S.Field()
    Fb.add(dome, bound=((0, 0, 0.05), 0.25))
    Fb.add(*S.Tor((0, 0.004, zb + 0.01), hr[0] * 0.97 + 0.01, 0.018), k=0.01)
    piece(name, Fb, (-0.2, -0.2, zb - 0.05), (0.2, 0.2, hr[2] + 0.06), m, parent, h=0.003)
    Fp = S.Field()
    Fp.add(*S.Sph((0, 0.01, hr[2] + 0.03), 0.03))
    piece(name + '_bol', lambda P: Fp(P) + F32(0.002) * np.sin(P[:, 0] * 300) * np.sin(P[:, 1] * 300),
          (-0.05, -0.05, hr[2] - 0.01), (0.05, 0.06, hr[2] + 0.08), m, parent, h=0.0022)
