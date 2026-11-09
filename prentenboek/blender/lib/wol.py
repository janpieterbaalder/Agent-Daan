"""Basis voor viltanimatie (naaldvilt-stop-motion) op echte miniatuurschaal: poppen van ca. 13 cm,
decors als tafelmaquette, gefotografeerd met een macrolens.

- Eén wolmateriaal: kleur per hoekpunt (attribuut 'col'): kleur zit ín het vilt, zoals bij naaldvilten,
  waar details met gekleurde wol in het oppervlak worden geprikt. Vezelstructuur en naaldputjes op
  echte grootte (vezels van enkele tienden van een millimeter).
- vlak(): een gevilt stuk uit een vormveld (SDF), met gekleurde vlakjes (regio's) met rafelige randen.
- Vezels: bij het renderen groeit over alle wol een laag losse vezels (Hair Curves): liggend over het
  oppervlak, met pluis aan de silhouetranden; dichtheid per beeldpixel, minder buiten de scherpte.
- plukwol(): bundels lange dunne vezels voor haar, wolken, gras en rook.
"""
import math
import bpy
import numpy as np
from . import core as K, sdf as S, mats as M

F32 = np.float32

# ------------------------------------------------------------------ kleur en ruis
def c(h):
    return np.array(K.srgb(h)[:3], dtype=F32)


def _n(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


class Noise:
    """Goedkope 3D-ruis (som van sinussen in willekeurige richtingen) voor rafelranden en hobbels."""

    def __init__(self, seed=1, freq=900.0, n=9):
        rng = np.random.default_rng(seed)
        k = _n(rng.normal(size=(n, 3)))
        self.k = (k * freq * (0.6 + 0.8 * rng.random((n, 1)))).astype(F32)
        self.ph = (rng.random(n) * 6.283).astype(F32)

    def __call__(self, P):
        return (np.sin(np.asarray(P, F32) @ self.k.T + self.ph).sum(1) / math.sqrt(len(self.ph))).astype(F32)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ materialen
_MAT = {}


def _alive(m):
    try:
        m.name
        return True
    except ReferenceError:
        return False


def wool_mat():
    """Het wolmateriaal (kleur uit 'col'): mat, iets doorschijnend, vezelig reliëf op ware grootte."""
    m = _MAT.get('wol')
    if m is not None and _alive(m):
        return m
    g = M.NT('Wol')
    geo = g._out(g.n('ShaderNodeNewGeometry'), 'Position')
    col = g.attr('col')
    # vezelstreepjes in drie richtingen (uitgerekte ruis), fijne pluis, naaldputjes
    streak = []
    for sc in ((1, 1, 7), (7, 1, 1), (1, 7, 1)):
        mp = g.mapping(geo, scale=tuple(v * 1.0 for v in sc))
        streak.append(g.noise(mp, 700, 3, 0.6, distortion=1.5))
    fib = g.math('MAXIMUM', g.math('MAXIMUM', streak[0], streak[1]), streak[2])
    fine = g.noise(geo, 4200, 2, 0.6, distortion=2.0)
    mott = g.noise(geo, 90, 3, 0.6)
    pits = g.voronoi(geo, 520, out='Distance')
    pit = g.maprange(pits, 0.0, 0.25, 1.0, 0.0)
    shade = g.math('ADD', g.math('MULTIPLY', fib, 0.5), g.math('MULTIPLY', mott, 0.5))
    shade = g.maprange(shade, 0.3, 0.75, 0.84, 1.12)
    shade = g.math('SUBTRACT', shade, g.math('MULTIPLY', pit, 0.07))
    colv = g.mix(1.0, col, g.comb(shade, shade, shade), 'MULTIPLY')
    p = g.principled(color=colv, rough=1.0, spec=0.18, sheen=0.5, sheen_rough=0.4, sss=0.22,
                     sss_radius=(1.0, 0.75, 0.55), sss_scale=0.0012)
    g.set(p, 'Sheen Tint', g.mix(0.4, col, (1, 1, 1, 1)))
    h = g.math('SUBTRACT', g.math('ADD', g.math('MULTIPLY', fib, 0.7), g.math('MULTIPLY', fine, 0.5)),
               g.math('MULTIPLY', pit, 0.35))
    g.set(p, 'Normal', g.bump(h, 0.55, 0.00025))
    m = g.done(p)
    m['wol'] = 1
    m['nofelt'] = 1
    _MAT['wol'] = m
    return m


def fiber_mat():
    m = _MAT.get('vezel')
    if m is not None and _alive(m):
        return m
    m = M.hair_color_mat('Wolvezels', rough=0.55, radial=0.85, attr='col')
    m['nofelt'] = 1
    _MAT['vezel'] = m
    return m


def bead_mat(color='#141418', name=None):
    key = 'kraal' + color
    m = _MAT.get(key)
    if m is not None and _alive(m):
        return m
    g = M.NT(name or ('Kraal ' + color))
    p = g.principled(color=M.C(color), rough=0.06, coat=1.0, coat_rough=0.02, spec=0.7)
    m = g.done(p)
    m['nofelt'] = 1
    _MAT[key] = m
    return m


def plain_mat(name, color, rough=0.5, metal=0.0, coat=0.0, trans=0.0, emit=None):
    key = 'plain' + name
    m = _MAT.get(key)
    if m is not None and _alive(m):
        return m
    if emit:
        m = M.emission(name, color, emit)
    else:
        g = M.NT(name)
        p = g.principled(color=M.C(color), rough=rough, metal=metal, coat=coat, trans=trans)
        m = g.done(p)
    m['nofelt'] = 1
    _MAT[key] = m
    return m


# ------------------------------------------------------------------ gevilte stukken
def bounds(F, pad):
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for kind, fn, k, b in F.ops:
        if kind != 'add' or b is None:
            continue
        cc, r = np.asarray(b[0], float), float(b[1])
        lo, hi = np.minimum(lo, cc - r), np.maximum(hi, cc + r)
    return lo - pad, hi + pad


def vlak(name, f, color, parent=None, h=0.0006, lo=None, hi=None, regions=(), lump=0.00025, seed=1, F=None,
         fuzz=1.0):
    """Gevilt stuk: veld f (of Field F), basiskleur, regio's [(maskfn(V)->0..1, kleur)], kleine hobbels."""
    fld = f if f is not None else F
    if lo is None:
        lo, hi = bounds(F, 0.004)
    nz = Noise(seed, 380.0, 7)
    ff = (lambda P: fld(P) + F32(lump) * nz(P)) if lump else fld
    V, Q = S.mesh(ff, lo, hi, h, relax=1)
    col = np.repeat(c(color)[None], len(V), 0) if isinstance(color, str) else np.asarray(color(V), F32)
    for mask, rc in regions:
        w = np.clip(mask(V), 0, 1)[:, None].astype(F32)
        col = col * (1 - w) + c(rc)[None] * w
    ob = K.mesh_obj(name, V, Q, wool_mat(), parent, attrs={'col': ('POINT', col)})
    ob['fuzz'] = fuzz
    return ob, ff


def edge(dist, width=0.00035, seed=3, rough=0.00028):
    """Rafelige rand: masker uit een afstand (negatief = binnen), met vezelige ruis langs de rand."""
    nz = Noise(seed, 2600.0, 9)
    return lambda V: smooth(width, -width, dist(V) + F32(rough) * nz(V))


def poly_in(P2, poly):
    """Punt-in-veelhoek (even-oneven), gevectoriseerd. P2 (n,2), poly (m,2)."""
    x, y = P2[:, 0], P2[:, 1]
    inside = np.zeros(len(P2), bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        cond = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
        inside ^= cond
    return inside


def poly_dist(P2, poly):
    """Getekende afstand tot een veelhoek (negatief binnen)."""
    d = np.full(len(P2), 1e9)
    n = len(poly)
    for i in range(n):
        a, b = np.asarray(poly[i]), np.asarray(poly[(i + 1) % n])
        ab = b - a
        t = np.clip(((P2 - a) @ ab) / (ab @ ab + 1e-12), 0, 1)
        d = np.minimum(d, np.linalg.norm(P2 - (a + t[:, None] * ab), axis=1))
    return np.where(poly_in(P2, poly), -d, d)


def decal(center, normal, poly, depth=0.003, up=(0, 0, 1)):
    """Afstandsfunctie voor een vlakje (veelhoek in het raakvlak) dat in het oppervlak is gevilt."""
    n = _n(normal)
    u = _n(np.cross(up, n)) if np.linalg.norm(np.cross(up, n)) > 1e-5 else _n(np.cross((0, 1, 0), n))
    v = np.cross(n, u)
    cc = np.asarray(center, float)
    poly = np.asarray(poly, float)

    def dist(V):
        Q = np.asarray(V, float) - cc
        P2 = np.stack([Q @ u, Q @ v], 1)
        dn = np.abs(Q @ n)
        d = poly_dist(P2, poly)
        return np.where(dn < depth, d, 1.0)
    return dist


def star_poly(ro, ri, n=5, rot=90):
    pts = []
    for i in range(2 * n):
        a = math.radians(rot + i * 180 / n)
        r = ro if i % 2 == 0 else ri
        pts.append((r * math.cos(a), r * math.sin(a)))
    return np.array(pts)


def circle_poly(r, n=32, cx=0.0, cy=0.0, ry=None):
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    return np.stack([cx + r * np.cos(t), cy + (ry or r) * np.sin(t)], 1)


def rrect_poly(w, h, r, n=6):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                       (w / 2 - r, -h / 2 + r, 270)):
        for t in np.linspace(a0, a0 + 90, n):
            pts.append((cx + r * math.cos(math.radians(t)), cy + r * math.sin(math.radians(t))))
    return np.array(pts)


def surf_hit(f, P0, d=(0, 1, 0), it=120):
    """Sphere tracing van P0 langs d naar het oppervlak; geeft punt en normaal."""
    p = np.asarray(P0, float).reshape(3)
    d = _n(d)
    t = 0.0
    for _ in range(it):
        v = float(f((p + d * t)[None].astype(F32))[0])
        if abs(v) < 2e-6:
            break
        t += v * 0.9
        if abs(t) > 1.0:
            break
    q = p + d * t
    g = S.gradient(f, q[None].astype(F32), 1e-4)[0]
    return q, np.asarray(g, float)


def bead(name, f, anchor, r, color='#141418', parent=None, ray=(0, 1, 0), sink=0.35):
    q, n = surf_hit(f, anchor, ray)
    from .viltpop import _rot_to
    return K.blob(name, (r, r, r * 0.85), 2.0, (20, 12), mat=bead_mat(color), parent=parent,
                  loc=tuple(q + n * r * (1 - sink)), rot=tuple(_rot_to(n)))


# ------------------------------------------------------------------ plukwol (haar, wolken, gras)
def plukwol(name, guides, width, color, parent=None, per=60, radius=0.00003, seed=5, spread_tip=1.6, jitter=0.25,
            colors=None):
    """Bundels lange, dunne vezels langs gidscurven (n,k,3): voor haar, wolken, gras, rook."""
    rng = np.random.default_rng(seed)
    G = np.asarray(guides, float)
    if G.ndim == 2:
        G = G[None]
    n, k, _ = G.shape
    T = _n(np.gradient(G, axis=1))
    ref = np.where(np.abs(T[..., 2:3]) < 0.9, np.array([0, 0, 1.0]), np.array([1.0, 0, 0]))
    U = _n(np.cross(T, ref))
    V = np.cross(T, U)
    t = np.linspace(0, 1, k)[None, :]
    strands, cols = [], []
    base = c(color) if isinstance(color, str) else None
    for i in range(n):
        w = width[i] if np.ndim(width) else width
        a = rng.uniform(0, 2 * math.pi, per)
        rr = np.sqrt(rng.random(per)) * w
        sp = (1 + (spread_tip - 1) * t ** 1.5)
        wig = rng.normal(0, jitter * w, (per, k, 2)) * t[..., None]
        ox = (np.cos(a)[:, None] * rr[:, None] * sp + wig[..., 0])
        oy = (np.sin(a)[:, None] * rr[:, None] * sp + wig[..., 1])
        S_ = G[i][None] + U[i][None] * ox[..., None] + V[i][None] * oy[..., None]
        lf = rng.uniform(0.75, 1.0, per)
        idx = np.clip((np.linspace(0, 1, k)[None, :] * lf[:, None] * (k - 1)), 0, k - 1)
        i0 = np.floor(idx).astype(int)
        i1 = np.minimum(i0 + 1, k - 1)
        fr = (idx - i0)[..., None]
        rows = np.arange(per)[:, None]
        S_ = S_[rows, i0] * (1 - fr) + S_[rows, i1] * fr
        strands.append(S_)
        cb = c(colors[i % len(colors)]) if colors else base
        cols.append(np.clip(cb[None] * rng.uniform(0.82, 1.15, (per, 1)), 0, 1))
    S_ = np.concatenate(strands)
    C_ = np.concatenate(cols)
    return K.hair(name, S_.astype(F32), (radius, radius * 0.6), fiber_mat(), parent, col=C_)


# ------------------------------------------------------------------ vezels groeien
DENS = 1.6e7          # vezels per m2 (ca. 16 per mm2) waar het beeld scherp en dichtbij is
PX_DENS = 0.5         # maximaal aantal vezels per beeldpixel-oppervlak
BUDGET = 5_500_000


def _cam():
    sc = bpy.context.scene
    cam = sc.camera
    cd = cam.data
    W, H = sc.render.resolution_x, sc.render.resolution_y
    Mi = np.array(cam.matrix_world.inverted())
    pos = np.array(cam.matrix_world.translation)
    tx = (cd.sensor_width / 2) / cd.lens
    ty = tx * H / W
    f = cd.lens / 1000.0
    if cd.dof.use_dof:
        df = cd.dof.focus_distance
        if cd.dof.focus_object is not None:
            df = (cd.dof.focus_object.matrix_world.translation - cam.matrix_world.translation).length
        N = cd.dof.aperture_fstop
    else:
        df, N = 1.0, 1e9
    return dict(Mi=Mi, pos=pos, tx=tx * (1 + 2 * abs(cd.shift_x)), ty=ty * (1 + 2 * abs(cd.shift_y)), W=W,
                f=f, df=df, N=N, sw=cd.sensor_width / 1000.0)


def grow_fibers(seed=11):
    bpy.context.view_layer.update()
    if bpy.context.scene.camera is None:
        return None
    cm = _cam()
    rng = np.random.default_rng(seed)
    dg = bpy.context.evaluated_depsgraph_get()
    wm = wool_mat()
    chunks = []
    total = 0.0
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH' or ob.hide_render or not ob.visible_camera:
            continue
        if not any(s.material is wm for s in ob.material_slots):
            continue
        oe = ob.evaluated_get(dg)
        me = oe.to_mesh()
        me.calc_loop_triangles()
        nt = len(me.loop_triangles)
        if nt == 0 or 'col' not in me.attributes:
            oe.to_mesh_clear()
            continue
        V = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get('co', V)
        V = V.reshape(-1, 3).astype(float)
        Tr = np.empty(nt * 3, np.int32)
        me.loop_triangles.foreach_get('vertices', Tr)
        Tr = Tr.reshape(-1, 3)
        ca = me.attributes['col']
        buf = np.empty(len(ca.data) * 4, np.float32)
        ca.data.foreach_get('color', buf)
        CV = buf.reshape(-1, 4)[:, :3]
        Mw = np.array(oe.matrix_world)
        Vw = V @ Mw[:3, :3].T + Mw[:3, 3]
        A, B, C = Vw[Tr[:, 0]], Vw[Tr[:, 1]], Vw[Tr[:, 2]]
        cr = np.cross(B - A, C - A)
        area = np.linalg.norm(cr, axis=1) * 0.5
        nrm = cr / (2 * area[:, None] + 1e-15)
        cen = (A + B + C) / 3
        pc = cen @ cm['Mi'][:3, :3].T + cm['Mi'][:3, 3]
        z = -pc[:, 2]
        vis = (z > 1e-3) & (np.abs(pc[:, 0]) < z * cm['tx'] * 1.06 + 0.002) & \
              (np.abs(pc[:, 1]) < z * cm['ty'] * 1.06 + 0.002)
        z = np.maximum(z, 1e-4)
        px = z * 2 * cm['tx'] / cm['W']                     # pixelgrootte op die afstand
        dens = np.minimum(DENS, PX_DENS / (px * px))
        view = _n(cen - cm['pos'])
        sil = 0.3 + 1.7 * (1 - np.abs((nrm * view).sum(1))) ** 2
        f, N, df = cm['f'], cm['N'], cm['df']
        coc = (f / N) * f * np.abs(z - df) / (z * max(df - f, 1e-4))
        coc_px = coc / cm['sw'] * cm['W']
        blur = 1.0 / (1.0 + (coc_px / 3.0) ** 2)
        w = area * dens * sil * blur * vis * float(ob.get('fuzz', 1.0))
        col = CV[Tr].mean(1)
        if w.sum() >= 1:
            chunks.append((A, B, C, nrm, w, col))
            total += w.sum()
        oe.to_mesh_clear()
    if not chunks:
        return None
    scale = min(1.0, BUDGET / max(total, 1.0))
    P_, N_, C_ = [], [], []
    for A, B, C, nrm, w, col in chunks:
        cnt = np.floor(w * scale + rng.random(len(w))).astype(np.int64)
        idx = np.repeat(np.arange(len(w)), cnt)
        if len(idx) == 0:
            continue
        r1, r2 = rng.random(len(idx)), rng.random(len(idx))
        s = np.sqrt(r1)
        P_.append(A[idx] * (1 - s)[:, None] + B[idx] * (s * (1 - r2))[:, None] + C[idx] * (s * r2)[:, None])
        N_.append(nrm[idx])
        C_.append(col[idx])
    P = np.concatenate(P_)
    Nn = np.concatenate(N_)
    Cc = np.concatenate(C_)
    n = len(P)
    r = rng.normal(size=(n, 3))
    tng = _n(r - Nn * (r * Nn).sum(1, keepdims=True))
    halo = rng.random(n) < 0.18
    elev = np.where(halo, rng.uniform(0.3, 0.85, n), rng.uniform(0.02, 0.22, n))[:, None]
    dirv = _n(Nn * elev + tng * (1 - elev))
    L = np.exp(rng.normal(math.log(0.0022), 0.45, n)) * np.where(halo, 1.6, 1.0)
    L = L[:, None]
    side = np.cross(Nn, tng)
    k = 5
    t = np.linspace(0, 1, k)[None, :, None]
    bend = rng.normal(0, 0.5, (n, 1, 1))
    S_ = (P - Nn * 0.00012)[:, None, :] + dirv[:, None, :] * (L[:, None, :] * t) \
        - Nn[:, None, :] * (L[:, None, :] * np.where(halo, 0.1, 0.35)[:, None, None] * t ** 2) \
        + side[:, None, :] * (L[:, None, :] * bend * np.sin(t * math.pi) * 0.4)
    rad = np.linspace(0.000016, 0.000009, k)[None, :].repeat(n, 0)
    col = np.clip(Cc * rng.uniform(0.82, 1.06, (n, 1)), 0, 1)
    ob = K.hair('Wolvezels', S_.astype(F32), rad, fiber_mat(), None, col=col)
    print(f'wol: {n} vezels (schaal {scale:.2f})')
    return ob


def finalize():
    grow_fibers()


# ------------------------------------------------------------------ camera en licht
def camera(loc, target, lens=60, fstop=4.0, focus=None, shift=(0, 0)):
    cam = K.camera(loc, target, lens=lens, fstop=fstop, focus=focus if focus is not None else target, shift=shift,
                   clip=(0.002, 40))
    return cam


def studio(key=(-0.35, -0.45, 0.5), target=(0, 0, 0.05), energy=28.0, size=0.45, warm=(1.0, 0.92, 0.82),
           fill_energy=6.0, rim_energy=10.0, world='#e9e2d8', world_strength=0.35):
    """Zacht daglicht van een groot raam (key), wat invul en een warm randlicht."""
    K.world_color(world, world_strength)
    K.light('AREA', key, target, energy=energy, size=size, color=warm)
    K.light('AREA', (abs(key[0]) * 1.2, key[1] * 0.8, key[2] * 0.5), target, energy=fill_energy, size=size * 1.2,
            color=(0.9, 0.94, 1.0))
    K.light('AREA', (key[0] * -0.4, abs(key[1]) * 1.1, key[2] * 0.9), target, energy=rim_energy, size=size * 0.5,
            color=(1.0, 0.88, 0.72))
