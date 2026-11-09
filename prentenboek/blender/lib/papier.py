"""Papieren kijkdoos: uitgeknipte figuurtjes en decors van gekleurd karton, in laagjes achter elkaar.

- Elk knipsel is een vlakke vorm (in centimeters ontworpen) van 0,3 mm dik karton, met een licht
  onregelmatige knipkant, een lichtere snijrand en een heel klein beetje kromming.
- Figuurtjes bestaan uit laagjes (zoals met foamtape opgeplakt): elk laagje ligt 1,2 mm dichter bij de
  camera, zodat er echte kleine schaduwen ontstaan.
- Eén papiermateriaal: kleur per hoekpunt ('col'), papiervezels en -nerf, een vleugje doorschijnendheid.

Figuren staan in het xz-vlak en kijken naar -y (naar de camera). Maten in meters, vormen in centimeters.
"""
import math
import bpy
import numpy as np
from mathutils import Vector, geometry
from . import core as K, mats as M

CM = 0.01
LAYER = 0.0012
THICK = 0.0003


def c(h):
    return np.array(K.srgb(h)[:3], dtype=np.float32)


# ------------------------------------------------------------------ materiaal
_MAT = {}


def _alive(m):
    try:
        m.name
        return True
    except ReferenceError:
        return False


PAPERS = ('mat', 'karton', 'linnen', 'kraft', 'aquarel', 'crepe', 'zijde', 'golf', 'glans', 'folie',
          'strepen', 'stippen', 'ruit', 'brei', 'raam')


def paper_mat(kind='karton'):
    """Papiersoorten: karton, linnen (reliëf), kraft (vezels en spikkels), aquarel (gewassen kleur, korrel),
    crepe (fijne plooitjes), zijde (doorschijnend), golf (golfkarton), glans (gecoat), folie (goud/zilver),
    en bedrukt papier: strepen, stippen, ruit (boerenbont), brei (gebreid motief). Kleur uit 'col' (en 'col2')."""
    key = 'papier_' + kind
    m = _MAT.get(key)
    if m is not None and _alive(m):
        return m
    g = M.NT('Papier ' + kind)
    pos = g._out(g.n('ShaderNodeNewGeometry'), 'Position')
    obj = g.coord('Object')
    ox, oy, oz = g.sep(obj)
    col = g.attr('col')
    col2 = g.attr('col2')
    # gemeenschappelijke basis: vezels, wolkjes, nerf
    f1 = g.noise(g.mapping(pos, scale=(1, 1, 9)), 2600, 2, 0.6, distortion=1.0)
    f2 = g.noise(g.mapping(pos, scale=(9, 1, 1)), 2600, 2, 0.6, distortion=1.0)
    fib = g.math('MAXIMUM', f1, f2)
    cloud = g.noise(pos, 70, 4, 0.55)
    tooth = g.noise(pos, 9000, 2, 0.5)
    var, bump, bump_d = 0.06, 0.18, 0.00006
    rough, spec, sheen, metal, coat, trans = 0.82, 0.25, 0.15, 0.0, 0.0, 0.07
    base = col
    h = g.math('ADD', g.math('MULTIPLY', fib, 0.6), g.math('MULTIPLY', tooth, 0.4))
    if kind == 'linnen':
        wx = g.math('SINE', g.math('MULTIPLY', ox, 2 * 3.14159 / 0.0008))
        wz = g.math('SINE', g.math('MULTIPLY', g.math('ADD', oz, oy), 2 * 3.14159 / 0.0008))
        h = g.math('ADD', g.math('MULTIPLY', g.math('ADD', wx, wz), 0.35), g.math('MULTIPLY', tooth, 0.3))
        bump, var = 0.22, 0.04
    elif kind == 'kraft':
        long_ = g.noise(g.mapping(pos, scale=(1, 1, 16)), 900, 3, 0.65, distortion=2.0)
        specks = g.math('LESS_THAN', g.voronoi(pos, 1400, out='Distance'), 0.09)
        base = g.mix(g.maprange(long_, 0.35, 0.75, 0.0, 0.25), col, g.mix(1.0, col, (0.7, 0.62, 0.5, 1), 'MULTIPLY'))
        base = g.mix(g.math('MULTIPLY', specks, 0.7), base, (0.18, 0.12, 0.07, 1))
        h = g.math('ADD', g.math('MULTIPLY', long_, 0.8), g.math('MULTIPLY', tooth, 0.4))
        bump, var, rough = 0.3, 0.08, 0.9
    elif kind == 'aquarel':
        wash = g.noise(pos, 22, 4, 0.6, distortion=0.6)
        gran = g.voronoi(pos, 1600, out='Distance')
        base = g.mix(g.maprange(wash, 0.3, 0.7, 0.0, 1.0), g.mix(1.0, col, (1.08, 1.08, 1.08, 1), 'MULTIPLY'),
                     g.mix(1.0, col, (0.88, 0.88, 0.9, 1), 'MULTIPLY'))
        base = g.mix(g.maprange(gran, 0.0, 0.4, 0.12, 0.0), base, g.mix(1.0, col, (0.75, 0.75, 0.8, 1), 'MULTIPLY'))
        cold = g.noise(pos, 1100, 4, 0.6)
        h = g.math('ADD', g.math('MULTIPLY', cold, 0.8), g.math('MULTIPLY', tooth, 0.3))
        bump, var, rough = 0.35, 0.02, 0.9
    elif kind == 'crepe':
        dist = g.noise(pos, 300, 2, 0.5)
        cr = g.math('SINE', g.math('MULTIPLY', g.math('ADD', oz, g.math('MULTIPLY', dist, 0.0012)),
                                   2 * 3.14159 / 0.0011))
        cr2 = g.noise(g.mapping(pos, scale=(1, 1, 14)), 1500, 2, 0.6)
        h = g.math('ADD', g.math('MULTIPLY', cr, 0.5), g.math('MULTIPLY', cr2, 0.5))
        base = g.mix(g.maprange(cr, -1, 1, 0.0, 0.12), col, (1, 1, 1, 1))
        bump, var, rough, sheen = 0.55, 0.04, 0.7, 0.35
    elif kind == 'zijde':
        wr = g.noise(pos, 240, 3, 0.6, distortion=1.5)
        h = g.math('MULTIPLY', wr, 1.0)
        bump, var, rough, trans = 0.12, 0.03, 0.6, 0.45
    elif kind == 'golf':
        ridge = g.math('SINE', g.math('MULTIPLY', g.math('ADD', ox, oy), 2 * 3.14159 / 0.0035))
        base = g.mix(g.maprange(ridge, -1, 1, 0.0, 0.18), col, (0.1, 0.07, 0.05, 1))
        h = g.math('ADD', g.math('MULTIPLY', ridge, 1.0), g.math('MULTIPLY', fib, 0.15))
        bump, bump_d, var, rough = 0.8, 0.0004, 0.05, 0.88
    elif kind == 'mat':
        bump, var, rough, spec, sheen = 0.25, 0.08, 0.95, 0.12, 0.0
    elif kind == 'glans':
        bump, var, rough, spec, coat = 0.05, 0.02, 0.3, 0.5, 0.35
    elif kind == 'folie':
        cr = g.noise(pos, 900, 4, 0.65, distortion=1.2)
        h = cr
        bump, var, rough, metal, spec, trans = 0.35, 0.0, 0.28, 1.0, 0.5, 0.0
    elif kind in ('strepen', 'stippen', 'ruit', 'brei'):
        if kind == 'strepen':
            pat = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', g.math('ADD', oz, oy), 2 * 3.14159 / 0.0075)),
                         0.15)
        elif kind == 'stippen':
            d = g.voronoi(g.mapping(obj, scale=(1, 1, 1)), 160, out='Distance', rand=0.0)
            pat = g.math('LESS_THAN', d, 0.22)
        elif kind == 'ruit':
            a = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', ox, 2 * 3.14159 / 0.008)), 0.0)
            b = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', g.math('ADD', oz, oy), 2 * 3.14159 / 0.008)),
                       0.0)
            pat = g.math('MULTIPLY', g.math('ADD', a, b), 0.5)
        else:
            px = g.math('ABSOLUTE', g.math('SUBTRACT', g.math('FRACT', g.math('MULTIPLY', ox, 1 / 0.0032)), 0.5))
            v = g.math('FRACT', g.math('ADD', g.math('MULTIPLY', g.math('ADD', oz, oy), 1 / 0.0026),
                                       g.math('MULTIPLY', px, 1.2)))
            pat = g.math('GREATER_THAN', v, 0.5)
            h = g.math('ADD', g.math('MULTIPLY', v, 0.6), g.math('MULTIPLY', tooth, 0.3))
            bump = 0.35
        base = g.mix(pat, col, col2)
    shade = g.maprange(g.math('ADD', g.math('MULTIPLY', cloud, 0.6), g.math('MULTIPLY', fib, 0.4)), 0.3, 0.7,
                       1 - var, 1 + var * 0.8)
    colv = g.mix(1.0, base, g.comb(shade, shade, shade), 'MULTIPLY')
    p = g.principled(color=colv, rough=rough, spec=spec, sheen=sheen, sheen_rough=0.5, sss=0.04 if not metal else 0.0,
                     sss_radius=(1.0, 0.8, 0.6), sss_scale=0.0005, metal=metal, coat=coat, coat_rough=0.1)
    g.set(p, 'Normal', g.bump(h, bump, bump_d))
    if kind == 'raam':
        gl = g.principled(color=col, rough=0.15, spec=0.6)
        tp = g.n('ShaderNodeBsdfTransparent')
        g.set(tp, 'Color', g.mix(0.35, (1, 1, 1, 1), col))
        mx = g.n('ShaderNodeMixShader')
        g.set(mx, 0, 0.62)
        g.set(mx, 1, gl)
        g.set(mx, 2, tp)
        m = g.done(mx)
        _MAT[key] = m
        return m
    if trans > 0:
        tr = g.n('ShaderNodeBsdfTranslucent')
        g.set(tr, 'Color', colv)
        mx = g.n('ShaderNodeMixShader')
        g.set(mx, 0, trans)
        g.set(mx, 1, p)
        g.set(mx, 2, tr)
        m = g.done(mx)
    else:
        m = g.done(p)
    _MAT[key] = m
    return m


def plain_mat(name, color, rough=0.4, emit=None, trans=0.0):
    key = 'p_' + name
    m = _MAT.get(key)
    if m is not None and _alive(m):
        return m
    if emit:
        m = M.emission(name, color, emit)
    else:
        g = M.NT(name)
        p = g.principled(color=M.C(color), rough=rough, trans=trans)
        m = g.done(p)
    _MAT[key] = m
    return m


# ------------------------------------------------------------------ vormen (in cm)
def circle(cx, cy, r, n=48, ry=None):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([cx + r * np.cos(t), cy + (ry if ry else r) * np.sin(t)], 1)


def ellipse(cx, cy, rx, ry, n=48, rot=0.0):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    P = np.stack([rx * np.cos(t), ry * np.sin(t)], 1)
    return rotate(P, rot) + np.array([cx, cy])


def rrect(cx, cy, w, h, r, n=8):
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4)
    pts = []
    for qx, qy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for t in np.linspace(a0, a0 + 90, n):
            pts.append((cx + qx + r * math.cos(math.radians(t)), cy + qy + r * math.sin(math.radians(t))))
    return np.array(pts)


def star(cx, cy, ro, ri, n=5, rot=90):
    pts = []
    for i in range(2 * n):
        a = math.radians(rot + i * 180 / n)
        r = ro if i % 2 == 0 else ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return round_corners(np.array(pts), 0.06)


def rotate(P, deg, about=(0, 0)):
    a = math.radians(deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return (np.asarray(P, float) - about) @ R.T + about


def chaikin(P, it=3, closed=True):
    P = np.asarray(P, float)
    for _ in range(it):
        Q = np.roll(P, -1, 0) if closed else P[1:]
        A = P if closed else P[:-1]
        new = np.empty((len(A) * 2, 2))
        new[0::2] = 0.75 * A + 0.25 * Q
        new[1::2] = 0.25 * A + 0.75 * Q
        P = new if closed else np.vstack([P[:1], new, P[-1:]])
    return P


def round_corners(P, r, it=2):
    return chaikin(P, it)


def strip(pts, w, cap=True, n=6):
    """Strookje papier langs een lijn (mond, wenkbrauw, kraagrand)."""
    P = np.asarray(pts, float)
    if len(P) > 2:
        P = chaikin(P, 2, closed=False)
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    N = np.stack([-T[:, 1], T[:, 0]], 1)
    L = P + N * w / 2
    R = P - N * w / 2
    out = list(L)
    if cap:
        a0 = math.atan2(N[-1, 1], N[-1, 0])
        out += [P[-1] + w / 2 * np.array([math.cos(a0 - t), math.sin(a0 - t)]) for t in np.linspace(0, math.pi, n)[1:-1]]
    out += list(R[::-1])
    if cap:
        a0 = math.atan2(-N[0, 1], -N[0, 0])
        out += [P[0] + w / 2 * np.array([math.cos(a0 - t), math.sin(a0 - t)]) for t in np.linspace(0, math.pi, n)[1:-1]]
    return np.array(out)


def arc_pts(cx, cy, r, a0, a1, n=24, ry=None):
    t = np.radians(np.linspace(a0, a1, n))
    return np.stack([cx + r * np.cos(t), cy + (ry if ry else r) * np.sin(t)], 1)


def radial_union(center, shapes, n=120):
    """Omtrek van de vereniging van cirkels/ellipsen [(cx, cy, rx, ry)] gezien vanuit een binnenpunt."""
    cx0, cy0 = center
    out = []
    for t in np.linspace(0, 2 * math.pi, n, endpoint=False):
        d = np.array([math.cos(t), math.sin(t)])
        best = 0.0
        for cx, cy, rx, ry in shapes:
            o = (np.array([cx0, cy0]) - np.array([cx, cy])) / np.array([rx, ry])
            dd = d / np.array([rx, ry])
            a = dd @ dd
            b = 2 * o @ dd
            cc = o @ o - 1
            disc = b * b - 4 * a * cc
            if disc > 0:
                best = max(best, (-b + math.sqrt(disc)) / (2 * a))
        out.append((cx0 + d[0] * best, cy0 + d[1] * best))
    return np.array(out)


def scallop(x0, x1, y, depth, n, up=True):
    """Golvende rand (pony, gras, wolkrand) als puntenrij van x0 naar x1."""
    pts = []
    for i in range(n):
        a, b = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
        for t in np.linspace(0, 1, 7)[:-1]:
            x = a + (b - a) * t
            pts.append((x, y + (depth if up else -depth) * math.sin(math.pi * t)))
    pts.append((x1, y))
    return np.array(pts)


# ------------------------------------------------------------------ knipsels maken
def _resample(P, step):
    P = np.asarray(P, float)
    out = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        L = np.linalg.norm(b - a)
        k = max(1, int(L / step))
        for t in np.arange(k) / k:
            out.append(a + (b - a) * t)
    return np.array(out)


def piece(name, poly, color, parent=None, layer=0.0, edge=None, thick=THICK, bend=0.02, jitter=0.012, seed=0,
          plane='xz', z=0.0, paper='karton', col2=None):
    """Knipsel: vlakke vorm (cm) als dun stuk karton. layer: laagje (x 1,2 mm naar de camera).
    plane 'xz' = rechtop (kijkt naar -y), 'xy' = plat op de grond."""
    rng = np.random.default_rng(abs(hash(name)) % (2 ** 31) + seed)
    P = np.asarray(poly, float)
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if area < 0:
        P = P[::-1]
    P = _resample(P, 0.12)
    if jitter:
        nrm = np.roll(P, -1, 0) - np.roll(P, 1, 0)
        nrm = np.stack([nrm[:, 1], -nrm[:, 0]], 1)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        wob = np.convolve(rng.normal(0, 1, len(P) + 6), np.ones(5) / 5, 'same')[3:3 + len(P)]
        P = P + nrm * (wob * jitter)[:, None]
    tris = geometry.tessellate_polygon([[Vector((x, y, 0)) for x, y in P]])
    n = len(P)
    P3 = P * CM
    cx, cy = P3.mean(0)
    w = max(np.ptp(P3[:, 0]), 1e-4)
    curl = bend * CM * ((P3[:, 0] - cx) / w) ** 2 * 2
    front = -layer * LAYER - thick
    back = -layer * LAYER

    def to3(xy, depth):
        x, y = xy[:, 0], xy[:, 1]
        dpt = depth + curl
        if plane == 'xz':
            return np.stack([x, dpt, y], 1)
        return np.stack([x, y, z - dpt], 1)
    Vf = to3(P3, front)
    Vb = to3(P3, back)
    # rand: eigen hoekpunten (andere kleur)
    V = np.concatenate([Vf, Vb, Vf, Vb])
    F = []
    for a, b, cc in tris:
        F.append((a, b, cc))
        F.append((n + cc, n + b, n + a))
    for i in range(n):
        j = (i + 1) % n
        F.append((2 * n + i, 3 * n + i, 3 * n + j, 2 * n + j))
    col = c(color) if isinstance(color, str) else np.asarray(color, np.float32)
    ecol = c(edge) if edge else np.clip(col * 0.55 + 0.45, 0, 1)
    C = np.concatenate([np.repeat(col[None], 2 * n, 0), np.repeat(ecol[None], 2 * n, 0)])
    c2 = c(col2) if col2 else col
    C2 = np.concatenate([np.repeat(c2[None], 2 * n, 0), np.repeat(ecol[None], 2 * n, 0)])
    ob = K.mesh_obj(name, V, F, paper_mat(paper), parent, smooth=False, attrs={'col': ('POINT', C),
                                                                                'col2': ('POINT', C2)})
    return ob


def group(name, parent=None, pivot=(0, 0), angle=0.0, layer=0.0, loc3=None):
    """Draaipunt (cm) voor een deel van een figuur; angle in graden, met de klok mee (vooraanzicht)."""
    e = K.empty(name, loc3 if loc3 is not None else (pivot[0] * CM, -layer * LAYER, pivot[1] * CM), (0, 0, 0), 1.0,
                parent)
    e.rotation_euler = (0, math.radians(angle), 0)
    return e


def local(pts, pivot):
    return np.asarray(pts, float) - np.asarray(pivot, float)


def tiles(name, polys, colors, paper='karton', plane='xy', z=0.0, y=0.0, thick=0.0008, parent=None, edge_mix=0.35,
          col2=None):
    """Veel kleine (bolle) knipsels in één mesh: klinkers, tegels, dakpannen, behangmotief.
    polys in cm (lijst van (n,2)-arrays), colors: één hex per vorm. plane 'xy' plat op hoogte z (m),
    'xz' rechtop op diepte y (m), kijkend naar -y."""
    V, F, C, C2 = [], [], [], []
    off = 0
    for P, col in zip(polys, colors):
        P = np.asarray(P, float) * CM
        n = len(P)
        cc = c(col) if isinstance(col, str) else np.asarray(col, np.float32)
        ec = np.clip(cc * (1 - edge_mix) + edge_mix, 0, 1)
        c2 = c(col2) if col2 else cc
        if plane == 'xy':
            top = np.stack([P[:, 0], P[:, 1], np.full(n, z + thick)], 1)
            bot = np.stack([P[:, 0], P[:, 1], np.full(n, z)], 1)
        else:
            top = np.stack([P[:, 0], np.full(n, y - thick), P[:, 1]], 1)
            bot = np.stack([P[:, 0], np.full(n, y), P[:, 1]], 1)
        V += [top, bot, top, bot]
        for i in range(1, n - 1):
            F.append((off, off + i, off + i + 1))
            F.append((off + n, off + n + i + 1, off + n + i))
        for i in range(n):
            j = (i + 1) % n
            F.append((off + 2 * n + i, off + 3 * n + i, off + 3 * n + j, off + 2 * n + j))
        C += [np.repeat(cc[None], 2 * n, 0), np.repeat(ec[None], 2 * n, 0)]
        C2 += [np.repeat(c2[None], 2 * n, 0), np.repeat(ec[None], 2 * n, 0)]
        off += 4 * n
    V = np.concatenate(V)
    if plane == 'xz':
        # vlakken naar de camera (-y) laten wijzen
        F = [f[::-1] for f in F]
    return K.mesh_obj(name, V, F, paper_mat(paper), parent, smooth=False,
                      attrs={'col': ('POINT', np.concatenate(C)), 'col2': ('POINT', np.concatenate(C2))})
