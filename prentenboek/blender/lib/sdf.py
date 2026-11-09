"""Boetseren met signed distance fields (SDF) en een surface-nets-mesher.

Vormen worden opgebouwd uit primitieven (bol, ellipsoïde, capsule, ronde kegel, torus, afgeronde doos)
die met zachte overgangen (smooth min/max) worden samengevoegd of weggesneden. Zo ontstaan
geboetseerde vormen met natuurlijke plooien en overgangen. De mesher evalueert het veld alleen
in een smalle band rond het oppervlak en projecteert de hoekpunten daarna exact op het oppervlak.

Alle functies werken op numpy-arrays P van vorm (N, 3) en geven (N,) afstanden terug.
"""
import math
import numpy as np

F32 = np.float32


def _v(x):
    return np.asarray(x, dtype=F32)


def norm(A):
    return np.sqrt((A * A).sum(-1))


def rot(rx=0.0, ry=0.0, rz=0.0):
    """Rotatiematrix (kolommen = lokale assen in wereld), volgorde X dan Y dan Z."""
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return (Rz @ Ry @ Rx).astype(F32)


def local(P, c, R=None):
    Q = P - _v(c)
    if R is not None:
        Q = Q @ _v(R)
    return Q


# ------------------------------------------------------------------ primitieven
def sphere(P, c, r):
    return norm(P - _v(c)) - r


def ellipsoid(P, c, r, R=None):
    Q = local(P, c, R)
    r = _v(r)
    k0 = norm(Q / r)
    k1 = norm(Q / (r * r))
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def capsule(P, a, b, r):
    a, b = _v(a), _v(b)
    pa, ba = P - a, b - a
    h = np.clip((pa @ ba) / float(ba @ ba), 0, 1)
    return norm(pa - h[:, None] * ba) - r


def round_cone(P, a, b, r1, r2):
    """Kegel met afgeronde uiteinden van a (straal r1) naar b (straal r2) (Inigo Quilez)."""
    a, b = _v(a), _v(b)
    ba = b - a
    l2 = float(ba @ ba)
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = P - a
    y = pa @ ba
    z = y - l2
    xv = pa * l2 - y[:, None] * ba
    x2 = (xv * xv).sum(-1)
    y2 = y * y * l2
    z2 = z * z * l2
    k = math.copysign(1.0, rr) * rr * rr * x2
    out = np.empty(len(P), dtype=F32)
    m1 = np.sign(z) * a2 * z2 > k
    m2 = (~m1) & (np.sign(y) * a2 * y2 < k)
    m3 = ~(m1 | m2)
    out[m1] = np.sqrt(x2[m1] + z2[m1]) * il2 - r2
    out[m2] = np.sqrt(x2[m2] + y2[m2]) * il2 - r1
    out[m3] = (np.sqrt(x2[m3] * a2 * il2) + y[m3] * rr) * il2 - r1
    return out


def chain(P, pts, radii):
    """Buis langs een polylijn met per punt een straal (unie van ronde kegels)."""
    d = None
    for i in range(len(pts) - 1):
        di = round_cone(P, pts[i], pts[i + 1], radii[i], radii[i + 1])
        d = di if d is None else np.minimum(d, di)
    return d


def torus(P, c, R_, r, R=None):
    Q = local(P, c, R)
    q = np.sqrt(Q[:, 0] ** 2 + Q[:, 1] ** 2) - R_
    return np.sqrt(q * q + Q[:, 2] ** 2) - r


def rbox(P, c, b, rr, R=None):
    Q = np.abs(local(P, c, R)) - (_v(b) - rr)
    return norm(np.maximum(Q, 0)) + np.minimum(Q.max(-1), 0) - rr


def plane(P, c, n):
    n = _v(n) / np.linalg.norm(n)
    return (P - _v(c)) @ n


def cylinder(P, a, b, r):
    """Afgeronde cilinder zonder bolle uiteinden (vlak afgesneden)."""
    a, b = _v(a), _v(b)
    ba = b - a
    L = float(np.linalg.norm(ba))
    axis = ba / L
    pa = P - a
    t = pa @ axis
    radial = norm(pa - t[:, None] * axis) - r
    cap = np.maximum(-t, t - L)
    return np.minimum(np.maximum(radial, cap), 0) + norm(np.stack([np.maximum(radial, 0), np.maximum(cap, 0)], -1))


# ------------------------------------------------------------------ bewerkingen
def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


def sub(a, b, k=0.0):
    """a min b (wegsnijden), zacht met k."""
    return smax(a, -b, k)


def onion(d, t):
    return np.abs(d) - t


# ------------------------------------------------------------------ mesher
def _eval_chunks(f, P, chunk=600000):
    out = np.empty(len(P), dtype=F32)
    for i in range(0, len(P), chunk):
        out[i:i + chunk] = f(P[i:i + chunk])
    return out


def mesh(f, lo, hi, h, block=8, band=3.0, relax=1, project=2, verbose=False):
    """Polygoniseer het veld f binnen [lo, hi] met celgrootte h. Geeft (V, F) met vierhoeken."""
    lo, hi = _v(lo), _v(hi)
    nb = np.ceil((hi - lo) / (h * block)).astype(int)
    n = nb * block + 1
    # grof raster
    gi = [np.arange(nb[a] + 1) for a in range(3)]
    G = np.stack(np.meshgrid(*gi, indexing='ij'), -1).reshape(-1, 3)
    dc = _eval_chunks(f, lo + G.astype(F32) * (h * block)).reshape(nb + 1)
    near = np.abs(dc) < band * block * h
    act = np.zeros(nb, bool)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                act |= near[dx:dx + nb[0], dy:dy + nb[1], dz:dz + nb[2]]
    # fijn raster: buiten de band het teken van het grove raster
    Fv = np.repeat(np.repeat(np.repeat(dc[:-1, :-1, :-1], block, 0), block, 1), block, 2)
    Fv = np.pad(Fv, ((0, 1), (0, 1), (0, 1)), mode='edge').astype(F32)
    Fv = np.where(Fv < 0, F32(-1e3), F32(1e3))
    ab = np.argwhere(act)
    off = np.stack(np.meshgrid(*[np.arange(block + 1)] * 3, indexing='ij'), -1).reshape(-1, 3)
    off = off[(off < block).all(1)]  # elk blok eigen punten; de laatste rand komt van het buurblok
    for i in range(0, len(ab), 3000):
        idx = (ab[i:i + 3000, None, :] * block + off[None, :, :]).reshape(-1, 3)
        vals = _eval_chunks(f, lo + idx.astype(F32) * h)
        Fv[idx[:, 0], idx[:, 1], idx[:, 2]] = vals
    # randvlakken van actieve blokken waarvan het buurblok niet actief is
    edge_blocks = ab
    rim = np.stack(np.meshgrid(*[np.arange(block + 1)] * 3, indexing='ij'), -1).reshape(-1, 3)
    rim = rim[(rim == block).any(1)]
    for i in range(0, len(edge_blocks), 3000):
        idx = (edge_blocks[i:i + 3000, None, :] * block + rim[None, :, :]).reshape(-1, 3)
        vals = _eval_chunks(f, lo + idx.astype(F32) * h)
        Fv[idx[:, 0], idx[:, 1], idx[:, 2]] = vals
    if verbose:
        print('mesher: raster', n, 'actieve blokken', len(ab))
    S = Fv < 0
    nc = n - 1
    anyin = np.zeros(nc, bool)
    allin = np.ones(nc, bool)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                s = S[dx:dx + nc[0], dy:dy + nc[1], dz:dz + nc[2]]
                anyin |= s
                allin &= s
    cells = anyin & ~allin
    ci = np.argwhere(cells)
    nv = len(ci)
    VI = np.full(nc, -1, np.int64)
    VI[ci[:, 0], ci[:, 1], ci[:, 2]] = np.arange(nv)
    # hoekpunt per cel: gemiddelde van de kruisingen op de 12 ribben
    corners = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]])
    edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
    acc = np.zeros((nv, 3), F32)
    cnt = np.zeros(nv, F32)
    Fc = [Fv[ci[:, 0] + c[0], ci[:, 1] + c[1], ci[:, 2] + c[2]] for c in corners]
    for a, b in edges:
        fa, fb = Fc[a], Fc[b]
        m = (fa < 0) != (fb < 0)
        t = np.clip(fa / np.where(m, fa - fb, 1), 0, 1)
        p = corners[a][None, :] + (corners[b] - corners[a])[None, :] * t[:, None]
        acc += p * m[:, None]
        cnt += m
    V = lo + (ci + acc / np.maximum(cnt, 1)[:, None]) * h
    # vlakken: één vierhoek per rib met tekenwissel
    quads, outw = [], []
    for ax in range(3):
        a1, a2 = [(1, 2), (0, 2), (0, 1)][ax]
        sl0 = [slice(None)] * 3
        sl1 = [slice(None)] * 3
        sl0[ax] = slice(0, n[ax] - 1)
        sl1[ax] = slice(1, n[ax])
        ch = S[tuple(sl0)] != S[tuple(sl1)]
        # alleen ribben met vier buurcellen
        sub_ = [slice(None)] * 3
        sub_[a1] = slice(1, n[a1] - 1)
        sub_[a2] = slice(1, n[a2] - 1)
        sub_[ax] = slice(0, n[ax] - 1)
        chs = ch[tuple(sub_)]
        e = np.argwhere(chs)
        e[:, a1] += 1
        e[:, a2] += 1
        inside_low = S[e[:, 0], e[:, 1], e[:, 2]]
        def cell(d1, d2):
            c = e.copy()
            c[:, a1] -= d1
            c[:, a2] -= d2
            return VI[c[:, 0], c[:, 1], c[:, 2]]
        q = np.stack([cell(1, 1), cell(0, 1), cell(0, 0), cell(1, 0)], 1)
        o = np.zeros((len(e), 3), F32)
        o[:, ax] = np.where(inside_low, 1, -1)
        quads.append(q)
        outw.append(o)
    Q = np.concatenate(quads)
    O = np.concatenate(outw)
    ok = (Q >= 0).all(1)
    Q, O = Q[ok], O[ok]
    nrm = np.cross(V[Q[:, 2]] - V[Q[:, 0]], V[Q[:, 3]] - V[Q[:, 1]])
    flip = (nrm * O).sum(1) < 0
    Q[flip] = Q[flip][:, ::-1]
    V = V.astype(F32)
    # ontspannen en terugleggen op het oppervlak
    eps = h * 0.5
    def proj(V):
        for _ in range(project):
            d = f(V)
            g = np.stack([(f(V + _v([eps, 0, 0])) - f(V - _v([eps, 0, 0]))),
                          (f(V + _v([0, eps, 0])) - f(V - _v([0, eps, 0]))),
                          (f(V + _v([0, 0, eps])) - f(V - _v([0, 0, eps])))], 1) / (2 * eps)
            g2 = np.maximum((g * g).sum(1), 1e-8)
            V = V - (d / g2)[:, None] * g
        return V
    if relax:
        A = np.concatenate([Q[:, i] for i in range(4)] + [Q[:, (i + 1) % 4] for i in range(4)])
        B = np.concatenate([Q[:, (i + 1) % 4] for i in range(4)] + [Q[:, i] for i in range(4)])
        cnt = np.bincount(A, minlength=len(V)).astype(F32)
        for _ in range(relax):
            avg = np.stack([np.bincount(A, weights=V[B, k], minlength=len(V)) for k in range(3)], 1) /                 np.maximum(cnt, 1)[:, None]
            V = (V * 0.5 + avg * 0.5).astype(F32)
            V = proj(V)
    else:
        V = proj(V)
    if verbose:
        print('mesher: hoekpunten', len(V), 'vlakken', len(Q))
    return V, Q


def gradient(f, P, eps=1e-3):
    g = np.stack([(f(P + _v([eps, 0, 0])) - f(P - _v([eps, 0, 0]))),
                  (f(P + _v([0, eps, 0])) - f(P - _v([0, eps, 0]))),
                  (f(P + _v([0, 0, eps])) - f(P - _v([0, 0, eps])))], 1)
    return g / np.maximum(norm(g), 1e-9)[:, None]


# ------------------------------------------------------------------ veldbouwer met lokale evaluatie
class Field:
    """Rij bewerkingen (toevoegen, wegsnijden, doorsnede), elk met een begrenzende bol. Punten ver
    buiten die bol slaan de dure evaluatie over; dat houdt hoofden met tientallen vormen snel."""

    def __init__(self):
        self.ops = []

    def _op(self, kind, fn, k, bound):
        self.ops.append((kind, fn, float(k), bound))
        return self

    def add(self, fn, bound=None, k=0.0):
        return self._op('add', fn, k, bound)

    def cut(self, fn, bound=None, k=0.0):
        return self._op('cut', fn, k, bound)

    def inter(self, fn, bound=None, k=0.0):
        return self._op('inter', fn, k, bound)

    def __call__(self, P):
        """Exacte evaluatie; een bewerking wordt alleen uitgerekend op punten waar ze het resultaat kan
        veranderen (de begrenzende bol geeft een ondergrens voor de afstand)."""
        P = np.asarray(P, dtype=F32)
        d = None
        for kind, fn, k, bound in self.ops:
            if d is None or bound is None or kind == 'inter':
                v = fn(P)
                if d is None:
                    d = v.astype(F32)
                elif kind == 'add':
                    d = smin(d, v, k)
                elif kind == 'cut':
                    d = smax(d, -v, k)
                else:
                    d = smax(d, v, k)
                continue
            bc, br = bound
            dist = norm(P - _v(bc)) - br
            if kind == 'add':
                m = dist < d + k + 0.01        # anders is v >= d + k: geen invloed
                if m.any():
                    d[m] = smin(d[m], fn(P[m]), k)
            else:
                m = dist < k - d + 0.01        # anders is -v <= d - k: geen invloed
                if m.any():
                    d[m] = smax(d[m], -fn(P[m]), k)
        return d


# constructors die (functie, begrenzing) teruggeven
def Sph(c, r):
    return (lambda P: sphere(P, c, r)), (c, r)


def Ell(c, r, R=None):
    return (lambda P: ellipsoid(P, c, r, R)), (c, float(max(r)))


def Cap(a, b, r):
    a_, b_ = np.asarray(a, float), np.asarray(b, float)
    return (lambda P: capsule(P, a, b, r)), (tuple((a_ + b_) / 2), float(np.linalg.norm(b_ - a_) / 2 + r))


def Cone(a, b, r1, r2):
    a_, b_ = np.asarray(a, float), np.asarray(b, float)
    return (lambda P: round_cone(P, a, b, r1, r2)), (tuple((a_ + b_) / 2), float(np.linalg.norm(b_ - a_) / 2 + max(r1, r2)))


def Chain(pts, radii):
    pts = [tuple(map(float, p)) for p in pts]
    A = np.asarray(pts)
    c = (A.min(0) + A.max(0)) / 2
    br = float(np.linalg.norm(A - c, axis=1).max() + max(radii))
    return (lambda P: chain(P, pts, radii)), (tuple(c), br)


def Tor(c, R_, r, R=None):
    return (lambda P: torus(P, c, R_, r, R)), (c, R_ + r)


def Box(c, b, rr, R=None):
    return (lambda P: rbox(P, c, b, rr, R)), (c, float(np.linalg.norm(b)) + float(rr))


def Cyl(a, b, r):
    a_, b_ = np.asarray(a, float), np.asarray(b, float)
    return (lambda P: cylinder(P, a, b, r)), (tuple((a_ + b_) / 2), float(np.linalg.norm(b_ - a_) / 2 + r))
