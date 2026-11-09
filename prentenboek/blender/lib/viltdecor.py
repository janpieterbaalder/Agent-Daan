"""Vilten decors in diorama-stijl: luchtdoek met wolken, straat met keitjes, huisjes, bakkerij, bomen met
bolle kruinen, struiken, bloemetjes, politieautootje, slaapkamer, bakkerij van binnen en rekwisieten.

Alles bestaat uit eenvoudige, zachte vormen (afgeronde blokken, bollen, platte lapjes met steekjes);
de wol, vezels en pluis komen uit felt.py bij het renderen. Grond op z = 0, camera kijkt meestal naar +y.
"""
import math
import numpy as np
from mathutils import Matrix
from . import core as K, sdf as S, mats as M
from .viltpop import wol, garen, kraal, piece, fbounds, Lump, applique, stitches, rrect, star, ellipse, _n, \
    wol_streep, F32, _MC, _cached

PAL = dict(
    sky='#a8d5f2', sky_top='#78b8e6', night='#1c2856', night_top='#121a3d', cloud='#fdfcf8', sun='#ffd24a',
    grass='#7ab648', grass2='#5f9a3a', road='#9a9ca3', walk='#ddd5c7', curb='#c4bcb0',
    trunk='#8a5a36', leaf=('#5aa04a', '#6db458', '#4c8f3e', '#7cc06a'), bush='#4f9a48',
    frame='#fbf7ef', pane='#bfe3f5', pane_night='#ffd98a', roof=('#8a3d2e', '#4b5d7a', '#6b4a3a'),
    house=('#c8553d', '#e9b44c', '#8fb8a8', '#e88a7d', '#f2e3c6', '#9fb3d9'),
    door=('#2f6b8f', '#a83b3b', '#4f7a3a', '#7a4f8f'),
)


def colmat(name, attr='col', fuzz=1.0, sheet=False):
    """Viltmateriaal waarvan de kleur uit een kleurattribuut komt (per steentje, blaadje, lapje)."""
    m = _cached(name)
    if m:
        return m
    g = M.NT(name)
    g.principled(color=g.attr(attr), rough=1.0)
    m = g.done([n for n in g.t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0])
    m['fuzz'] = fuzz
    if sheet:
        m['sheet'] = 1
    _MC[name] = m
    return m


def hexc(h):
    return np.array(K.srgb(h)[:3])


# ------------------------------------------------------------------ bouwstenen
_TPL = {}


def _template(n=4.0, res=(14, 7)):
    key = (n, res)
    if key not in _TPL:
        D, F = K.sph(*res)
        P = K.superdir(D, n)
        tris = []
        for f in F:
            if len(f) == 3:
                tris.append(f)
            else:
                tris.append((f[0], f[1], f[2]))
                tris.append((f[0], f[2], f[3]))
        _TPL[key] = (P, np.array(tris, np.int64))
    return _TPL[key]


def instances(name, locs, sizes, cols, mat, parent=None, n=4.0, res=(14, 7), rotz=None, rng=None, jitter=0.0):
    """Veel zachte blokjes/bolletjes als één mesh (keitjes, blaadjes, bloemblaadjes)."""
    P, T = _template(n, res)
    locs = np.asarray(locs, float)
    sizes = np.broadcast_to(np.asarray(sizes, float), locs.shape)
    m = len(locs)
    V = P[None] * sizes[:, None, :]
    if jitter and rng is not None:
        V = V * (1 + rng.normal(0, jitter, (m, 1, 3)))
    if rotz is not None:
        c, s = np.cos(rotz)[:, None], np.sin(rotz)[:, None]
        x, y = V[..., 0].copy(), V[..., 1].copy()
        V[..., 0], V[..., 1] = x * c - y * s, x * s + y * c
    V = V + locs[:, None, :]
    F = T[None] + (np.arange(m) * len(P))[:, None, None]
    C = np.repeat(np.asarray(cols, float)[:, None, :], len(P), 1)
    return K.mesh_obj(name, V.reshape(-1, 3), F.reshape(-1, 3), mat, parent,
                      attrs={'col': ('POINT', C.reshape(-1, 3))})


def box(name, center, half, mat, parent=None, n=6.0, rot=(0, 0, 0), res=(32, 16)):
    return K.blob(name, tuple(half), n, res, mat=mat, parent=parent, loc=tuple(center), rot=rot)


def slab(name, outline, thick, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), bevel=True, plane='xz'):
    """Plat vilten lapje: omtrek in het xz-vlak (x rechts, z omhoog), dikte naar -y (naar de camera)."""
    O = np.asarray(outline, float)
    if 0.5 * np.sum(O[:, 0] * np.roll(O[:, 1], -1) - np.roll(O[:, 0], -1) * O[:, 1]) < 0:
        O = O[::-1]
    n = len(O)
    c = O.mean(0)
    if plane == 'xz':
        to3 = lambda p, y: (p[0], y, p[1])
        back, front = 0.0, -thick
    else:  # xy: plat op de grond, dikte omhoog
        to3 = lambda p, z: (p[0], p[1], z)
        back, front = 0.0, thick
    V = [to3(p, back) for p in O] + [to3(p, front) for p in O] + [to3(c, back), to3(c, front)]
    F = []
    ib, it = 2 * n, 2 * n + 1
    for i in range(n):
        j = (i + 1) % n
        if plane == 'xz':
            F.append((it, n + j, n + i))
            F.append((ib, i, j))
            F.append((i, n + i, n + j, j))
        else:
            F.append((it, n + i, n + j))
            F.append((ib, j, i))
            F.append((i, j, n + j, n + i))
    ob = K.mesh_obj(name, np.array(V), F, mat, parent, loc=loc, rot=rot)
    if bevel:
        K.modifier(ob, 'BEVEL', width=thick * 0.4, segments=2, limit_method='ANGLE')
    return ob


def puff(cx, n=60, lobes=((0, 0, 1.0),)):
    """Omtrek van een wolkje: vereniging van cirkels (x, z, r), radiaal bemonsterd vanuit het midden."""
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    rr = []
    for t in th:
        d = np.array([math.cos(t), math.sin(t)])
        best = 0.0
        for x, z, r in lobes:
            c = np.array([x, z]) - cx
            b = -2 * c @ d
            cc = c @ c - r * r
            disc = b * b - 4 * cc
            if disc > 0:
                best = max(best, (-b + math.sqrt(disc)) / 2)
        rr.append(best)
    return np.stack([cx[0] + np.cos(th) * rr, cx[1] + np.sin(th) * rr], 1)


def cloud(name, loc, scale=1.0, parent=None, seed=0):
    rng = np.random.default_rng(seed)
    lobes = [(0, 0, 0.55), (-0.6, -0.12, 0.42), (0.62, -0.1, 0.45), (-0.25, 0.32, 0.45), (0.28, 0.3, 0.5)]
    lobes = [(x * scale, z * scale, r * scale * (0.9 + 0.2 * rng.random())) for x, z, r in lobes]
    O = puff(np.array([0.0, 0.05 * scale]), 72, lobes)
    O[:, 1] = np.maximum(O[:, 1], -0.38 * scale)
    return slab(name, O, 0.06 * scale, wol('Vilt wolk', PAL['cloud'], fuzz=1.6), parent, loc=loc)


# ------------------------------------------------------------------ lucht en grond
def backdrop(y=8.0, width=34.0, height=11.0, night=False, sun=(4.5, 6.2), clouds=None, parent=None, fillet=2.5,
             x0=0.0, seed=1):
    """Achterdoek van vilt met een zachte bocht naar de grond, met wolken en zon (of maan en sterren)."""
    g = M.NT('Vilt luchtdoek nacht' if night else 'Vilt luchtdoek')
    co = g.coord('Object')
    x, yy, z = g.sep(co)
    f = g.maprange(z, 0.5, height * 0.9, 0.0, 1.0)
    top, bot = (PAL['night_top'], PAL['night']) if night else (PAL['sky_top'], PAL['sky'])
    col = g.mix(f, K.srgb(bot), K.srgb(top))
    g.principled(color=col, rough=1.0)
    mat = g.done([n for n in g.t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0])
    mat['sheet'] = 1
    mat['fuzz'] = 0.4
    nu, nv = 60, 40
    U = np.linspace(-width / 2, width / 2, nu) + x0
    ts = np.linspace(0, 1, nv)
    pts = []
    L1 = fillet * math.pi / 2
    L2 = height - fillet
    for t in ts:
        s = t * (L1 + L2)
        if s < L1:
            a = s / fillet
            pts.append((y - fillet + math.sin(a) * fillet, fillet - math.cos(a) * fillet))
        else:
            pts.append((y, fillet + (s - L1)))
    V = np.array([(u, py, pz) for py, pz in pts for u in U])
    F = [(i * nu + j, i * nu + j + 1, (i + 1) * nu + j + 1, (i + 1) * nu + j) for i in range(nv - 1)
         for j in range(nu - 1)]
    ob = K.mesh_obj('Achterdoek', V, F, mat, parent)
    root = K.empty('Lucht', (0, 0, 0), (0, 0, 0), 1.0, parent)
    rng = np.random.default_rng(seed)
    if night:
        mm = wol('Vilt maan', '#f7e6a3', sheet=True)
        moon = puff(np.array([0.0, 0.0]), 64, [(0, 0, 0.8)])
        th = np.linspace(0, 2 * math.pi, 64, endpoint=False)
        cres = []
        for t in th:
            p = np.array([math.cos(t), math.sin(t)]) * 0.8
            if np.linalg.norm(p - np.array([0.38, 0.22])) < 0.68:
                p = np.array([0.38, 0.22]) + (p - np.array([0.38, 0.22])) / np.linalg.norm(p - np.array([0.38, 0.22])) * 0.68
            cres.append(p)
        slab('Maan', np.array(cres), 0.07, mm, root, loc=(sun[0], y - 0.08, sun[1]))
        ym = wol('Vilt ster', '#ffe17a', sheet=True)
        for i in range(26):
            sx = x0 + rng.uniform(-width * 0.42, width * 0.42)
            sz = rng.uniform(fillet + 1.0, height - 0.6)
            slab(f'Ster{i}', star(rng.uniform(0.12, 0.22), 0.06), 0.04, ym, root, loc=(sx, y - 0.06, sz),
                 rot=(0, rng.uniform(-0.4, 0.4), 0))
    else:
        if sun:
            sm = wol('Vilt zon', PAL['sun'], sheet=True)
            slab('Zon', ellipse(0.85, 0.85, 64), 0.07, sm, root, loc=(sun[0], y - 0.08, sun[1]))
            rays = []
            for i in range(12):
                a = i * math.pi / 6
                pts = np.array([(math.cos(a - 0.1) * 1.0, math.sin(a - 0.1) * 1.0), (math.cos(a) * 1.45, math.sin(a) * 1.45),
                                (math.cos(a + 0.1) * 1.0, math.sin(a + 0.1) * 1.0)])
                slab(f'Zonnestraal{i}', pts, 0.05, sm, root, loc=(sun[0], y - 0.07, sun[1]))
        for i, (cx, cz, sc) in enumerate(clouds or [(-6, 7.5, 1.6), (1.0, 8.2, 1.2), (8, 7.0, 1.8), (-12, 6.5, 1.4),
                                                   (13, 8.0, 1.3)]):
            cloud(f'Wolk{i}', (cx + x0, y - 0.12 - 0.02 * i, cz), sc, root, seed=i)
    return ob


def ground(name, x0, x1, y0, y1, color, parent=None, z=0.0, n=8.0):
    return box(name, ((x0 + x1) / 2, (y0 + y1) / 2, z - 0.05), ((x1 - x0) / 2, (y1 - y0) / 2, 0.05), wol(name, color),
               parent, n=n, res=(48, 12))


def cobbles(name, x0, x1, y0, y1, parent=None, size=(0.11, 0.075, 0.03), seed=2, colors=None, tile=False):
    rng = np.random.default_rng(seed)
    colors = colors or ['#7b7c80', '#8a8a8c', '#727378', '#8b857c', '#7f8288']
    w, d, h = size
    locs, cols, sz = [], [], []
    row = 0
    yy = y0 + d
    while yy < y1:
        off = (w if row % 2 else 0.0)
        xx = x0 + off
        while xx < x1:
            locs.append((xx + rng.normal(0, 0.006), yy + rng.normal(0, 0.005), h * 0.4))
            cols.append(hexc(colors[rng.integers(len(colors))]) * rng.uniform(0.94, 1.06))
            sz.append((w * rng.uniform(0.86, 0.95), d * rng.uniform(0.84, 0.94), h * rng.uniform(0.85, 1.1)))
            xx += 2 * w
        yy += 2 * d
        row += 1
    ground(name + '_voeg', x0, x1, y0, y1, '#4f5056' if not tile else '#b0a696', parent)
    return instances(name, locs, sz, cols, colmat('Vilt keitjes'), parent, n=4.5 if not tile else 6.0, rng=rng,
                     rotz=rng.normal(0, 0.04, len(locs)))


def grass_tufts(name, region, n, parent=None, seed=3, h=(0.04, 0.09), colors=('#6aa83f', '#83c25a', '#5b9636')):
    """Wollen grasplukjes (Hair Curves)."""
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = region
    cx = rng.uniform(x0, x1, n)
    cy = rng.uniform(y0, y1, n)
    per = 9
    strands, cols = [], []
    for i in range(n):
        base = np.array([cx[i], cy[i], 0.0])
        c = hexc(colors[rng.integers(len(colors))])
        for k in range(per):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(0, 0.012)
            p0 = base + np.array([math.cos(a) * r, math.sin(a) * r, -0.005])
            d = _n(np.array([math.cos(a) * 0.35, math.sin(a) * 0.35, 1.0]))
            L = rng.uniform(*h)
            t = np.linspace(0, 1, 4)[:, None]
            strands.append(p0 + d * L * t + np.array([math.cos(a), math.sin(a), 0]) * (L * 0.25 * t ** 2))
            cols.append(c * rng.uniform(0.9, 1.1))
    mat = _cached('Wol gras') or M.hair_color_mat('Wol gras', rough=0.55, radial=0.9, attr='col')
    _MC['Wol gras'] = mat
    return K.hair(name, np.array(strands), (0.0022, 0.0008), mat, parent, col=np.array(cols))


def flowers(name, region, n, parent=None, seed=7, kinds=('#f27c9b', '#ffd34d', '#ffffff', '#b47ae0', '#ff9a52'),
            size=0.045):
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = region
    P, Sz, C, Rz = [], [], [], []
    cen, cc = [], []
    stems = []
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        hgt = rng.uniform(0.06, 0.16)
        col = hexc(kinds[rng.integers(len(kinds))])
        s = size * rng.uniform(0.8, 1.2)
        top = np.array([x, y, hgt])
        for k in range(5):
            a = k * 2 * math.pi / 5 + rng.uniform(0, 0.3)
            P.append(top + np.array([math.cos(a) * s * 0.6, math.sin(a) * s * 0.6, 0]))
            Sz.append((s * 0.55, s * 0.32, s * 0.12))
            C.append(col)
            Rz.append(a)
        cen.append(top + np.array([0, 0, s * 0.08]))
        cc.append(hexc('#f5c242'))
        stems.append(np.array([[x, y, -0.01], [x, y, hgt * 0.5], [x, y, hgt]]))
    instances(name + '_blad', P, Sz, C, colmat('Vilt bloemblad', sheet=True), parent, n=2.2, res=(10, 6),
              rotz=np.array(Rz))
    instances(name + '_hart', cen, (s * 0.3, s * 0.3, s * 0.18), cc, colmat('Vilt bloemhart'), parent, n=2.0,
              res=(10, 6))
    mat = _cached('Wol steel') or M.hair_color_mat('Wol steel', color='#4f8a35', rough=0.6, radial=0.9)
    _MC['Wol steel'] = mat
    K.hair(name + '_stelen', np.array(stems), (0.0035, 0.0028), mat, parent)


# ------------------------------------------------------------------ planten
def tree(name, loc=(0, 0, 0), h=2.4, crown=0.85, parent=None, seed=11, apples=0, branch=None):
    rng = np.random.default_rng(seed)
    root = K.empty(name, loc, (0, 0, 0), 1.0, parent)
    F = S.Field()
    F.add(*S.Cone((0, 0, -0.05), (0.02, 0.0, h * 0.62), 0.16, 0.09))
    for s in (-1, 1):
        F.add(*S.Cone((0.0, 0, h * 0.42), (s * 0.28, 0.02, h * 0.62), 0.06, 0.045), k=0.05)
    if branch is not None:
        bs, bz, bl = branch
        F.add(*S.Cone((0.0, 0.0, bz - 0.06), (bs * bl, -0.04, bz + 0.05), 0.075, 0.05), k=0.05)
    lump = Lump(seed, 0.006, 6)
    piece(name + '_stam', lambda P: F(P) + lump(P), *fbounds(F, 0.03), wol('Vilt stam', PAL['trunk']), root, h=0.012)
    Fc = S.Field()
    cz = h * 0.62 + crown * 0.55
    Fc.add(*S.Sph((0, 0, cz), crown))
    for i in range(7):
        a = i * 2 * math.pi / 7 + rng.uniform(0, 0.5)
        r = crown * rng.uniform(0.55, 0.7)
        Fc.add(*S.Sph((math.cos(a) * crown * 0.72, math.sin(a) * crown * 0.5, cz + rng.uniform(-0.25, 0.35) * crown), r),
               k=0.12)
    Fc.add(*S.Sph((0, 0, cz + crown * 0.62), crown * 0.68), k=0.14)
    lump2 = Lump(seed + 1, 0.012, 5)
    col = PAL['leaf'][seed % len(PAL['leaf'])]
    fcr = lambda P: Fc(P) + lump2(P)
    piece(name + '_kruin', fcr, *fbounds(Fc, 0.05), wol('Vilt blad ' + col, col, fuzz=1.3), root, h=0.016)
    if apples:
        from .viltpop import surf
        am = wol('Vilt appel', '#d9443a')
        for i in range(apples):
            a = rng.uniform(-1.2, 1.2) - math.pi / 2
            z = cz + rng.uniform(-0.5, 0.5) * crown
            q, nq = surf(fcr, (math.cos(a) * crown * 2.5, math.sin(a) * crown * 2.5, z), (-math.cos(a), -math.sin(a), 0))
            K.blob(f'{name}_appel{i}', (0.075, 0.075, 0.07), 2.0, (16, 10), mat=am, parent=root, loc=tuple(q + nq * 0.05))
    return root


def bush(name, loc=(0, 0, 0), size=0.6, parent=None, seed=13, color=None, berries=0):
    rng = np.random.default_rng(seed)
    root = K.empty(name, loc, (0, 0, 0), 1.0, parent)
    F = S.Field()
    F.add(*S.Ell((0, 0, size * 0.45), (size, size * 0.75, size * 0.55)))
    for i in range(6):
        a = i * math.pi / 3 + rng.uniform(0, 0.4)
        F.add(*S.Sph((math.cos(a) * size * 0.65, math.sin(a) * size * 0.4, size * rng.uniform(0.35, 0.75)),
                     size * rng.uniform(0.4, 0.55)), k=0.08)
    lump = Lump(seed, 0.008, 7)
    f = lambda P: S.smax(F(P) + lump(P), -P[:, 2], 0.02)
    col = color or PAL['bush']
    piece(name + '_bol', f, *fbounds(F, 0.04), wol('Vilt struik ' + col, col, fuzz=1.3), root, h=0.011)
    if berries:
        from .viltpop import surf
        bm = wol('Vilt bes', '#e2425b')
        for i in range(berries):
            a = rng.uniform(-1.3, 1.3) - math.pi / 2
            z = size * rng.uniform(0.3, 0.9)
            q, nq = surf(f, (math.cos(a) * 3, math.sin(a) * 3, z), (-math.cos(a), -math.sin(a), 0))
            K.blob(f'{name}_bes{i}', (0.03, 0.03, 0.03), 2.0, (12, 8), mat=bm, parent=root, loc=tuple(q + nq * 0.02))
    return root


# ------------------------------------------------------------------ gebouwen
def window(name, parent, x, z, w, h, y, night=False, cross=True, shutters=None):
    fr = wol('Vilt kozijn', PAL['frame'], sheet=True)
    pane = wol('Vilt ruit nacht', PAL['pane_night']) if night else wol('Vilt ruit', PAL['pane'], sheet=True, fuzz=0.4)
    box(name + '_kozijn', (x, y - 0.03, z), (w / 2 + 0.05, 0.035, h / 2 + 0.05), fr, parent, n=6)
    box(name + '_ruit', (x, y - 0.055, z), (w / 2, 0.03, h / 2), pane, parent, n=8)
    if cross:
        box(name + '_roede1', (x, y - 0.09, z), (0.018, 0.012, h / 2), fr, parent, n=4)
        box(name + '_roede2', (x, y - 0.09, z), (w / 2, 0.012, 0.018), fr, parent, n=4)
    box(name + '_bank', (x, y - 0.08, z - h / 2 - 0.06), (w / 2 + 0.08, 0.07, 0.025), fr, parent, n=5)
    if shutters:
        sm = wol('Vilt luik ' + shutters, shutters)
        for s in (-1, 1):
            box(f'{name}_luik{s}', (x + s * (w / 2 + 0.05 + w * 0.26), y - 0.04, z), (w * 0.24, 0.025, h / 2 + 0.03),
                sm, parent, n=5)
    if night:
        e = M.emission(name + '_licht', '#ffcf7a', 2.5)
        box(name + '_gloed', (x, y + 0.01, z), (w / 2 - 0.01, 0.01, h / 2 - 0.01), e, parent, n=4)


def house(name, x, width, height, parent=None, y=3.0, depth=1.4, color=None, roof=None, door=None, seed=0,
          night=False, roof_kind='gable', windows=True, ground_window=True):
    rng = np.random.default_rng(seed)
    root = K.empty(name, (x, 0, 0), (0, 0, 0), 1.0, parent)
    col = color or PAL['house'][seed % len(PAL['house'])]
    wm = wol('Vilt gevel ' + col, col)
    box(name + '_romp', (0, y + depth / 2, height / 2), (width / 2, depth / 2, height / 2), wm, root, n=7)
    rc = roof or PAL['roof'][seed % len(PAL['roof'])]
    rm = wol('Vilt dak ' + rc, rc)
    if roof_kind == 'gable':
        # puntdak: driehoek vooraan met een rij schubdakpannen
        rh = width * 0.5
        tri = np.array([(-width / 2 - 0.12, 0.0), (width / 2 + 0.12, 0.0), (0.0, rh)])
        slab(name + '_dakgevel', _dens(tri), depth, rm, root, loc=(0, y + depth - 0.02, height), bevel=True)
        sc = []
        for r in range(5):
            zz = height + 0.12 + r * rh / 5.3
            half = (width / 2 + 0.1) * (1 - (zz - height) / rh)
            nsc = max(1, int(2 * half / 0.32))
            for k in range(nsc):
                xx = -half + (k + 0.5) * 2 * half / nsc
                sc.append((xx, zz))
        cols = [hexc(rc) * rng.uniform(0.9, 1.1) for _ in sc]
        instances(name + '_pannen', [(sx, y - 0.04, sz) for sx, sz in sc], (0.16, 0.05, 0.11), cols,
                  colmat('Vilt dakpannen'), root, n=2.2, res=(12, 6))
        box(name + '_schoorsteen', (width * 0.25, y + depth * 0.6, height + rh * 0.62), (0.13, 0.13, 0.32),
            wol('Vilt baksteen', '#a9493a'), root, n=6)
    else:
        box(name + '_dakrand', (0, y + depth / 2, height + 0.06), (width / 2 + 0.08, depth / 2 + 0.06, 0.07), rm, root,
            n=6)
    if windows:
        nx = max(1, int(width / 1.2))
        for i in range(nx):
            wx = -width / 2 + (i + 0.5) * width / nx
            window(f'{name}_raam_b{i}', root, wx, height * 0.72, 0.55, 0.7, y, night=night,
                   shutters=None if rng.random() < 0.5 else PAL['door'][rng.integers(4)])
    dc = door or PAL['door'][seed % len(PAL['door'])]
    dx = width * (0.25 if seed % 2 else -0.25)
    dm = wol('Vilt deur ' + dc, dc)
    arch = np.concatenate([np.array([(0.34, 0.0), (0.34, 1.05)]),
                           np.array([(0.34 * math.cos(t), 1.05 + 0.34 * math.sin(t)) for t in np.linspace(0, math.pi, 12)]),
                           np.array([(-0.34, 1.05), (-0.34, 0.0)])])
    slab(name + '_deur', arch, 0.06, dm, root, loc=(dx, y - 0.01, 0.0))
    K.blob(name + '_klink', (0.035, 0.035, 0.035), 2.0, (12, 8), mat=kraal('Knop goud', '#d9a93a'), parent=root,
           loc=(dx + 0.22, y - 0.09, 0.6))
    box(name + '_stoep', (dx, y - 0.15, 0.04), (0.45, 0.16, 0.04), wol('Vilt stoepje', '#c9c0b2'), root, n=5)
    if ground_window:
        wx = -dx
        window(f'{name}_raam_o', root, wx, 1.05, 0.6, 0.7, y, night=night)
    return root


def _dens(P, per=4):
    P = np.asarray(P, float)
    out = []
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        for t in np.linspace(0, 1, per, endpoint=False):
            out.append(a * (1 - t) + b * t)
    return np.array(out)


def bakery(name, x, parent=None, y=3.0, width=3.0, height=2.75, night=False, cookies=True):
    """Bakkerij: crème gevel, rood-wit gestreepte luifel, grote etalage, uithangbord met letters."""
    root = house(name, x, width, height, parent, y=y, color='#f4e4c4', roof='#8a3d2e', door='#a83b3b', seed=1,
                 night=night, windows=False, ground_window=False)
    # etalage
    fr = wol('Vilt kozijn groen', '#2f5d4a', sheet=True)
    ex, ew, eh, ez = -0.35, 1.5, 1.05, 1.05
    box(name + '_etalagekozijn', (ex, y - 0.04, ez), (ew / 2 + 0.07, 0.04, eh / 2 + 0.07), fr, root, n=6)
    box(name + '_etalage', (ex, y - 0.07, ez), (ew / 2, 0.03, eh / 2), wol('Vilt etalage', '#fff3d6', sheet=True),
        root, n=8)
    box(name + '_plank', (ex, y - 0.22, ez - 0.25), (ew / 2, 0.14, 0.025), fr, root, n=5)
    if cookies:
        for i, xx in enumerate(np.linspace(ex - ew / 2 + 0.2, ex + ew / 2 - 0.2, 4)):
            cookie(f'{name}_etalagekoek{i}', root, (xx, y - 0.22, ez - 0.2), r=0.09, rot=(math.radians(70), 0, 0),
                   seed=i)
    # luifel: gestreept, schuin naar voren
    aw = wol_streep_x('Vilt luifel', '#d9443a', '#fbf7ef', 0.36)
    box(name + '_luifel', (0, y - 0.42, height * 0.72), (width / 2 + 0.05, 0.45, 0.04), aw, root, n=6,
        rot=(math.radians(-22), 0, 0))
    n = int(width / 0.36)
    for i in range(n):
        xx = -width / 2 + (i + 0.5) * width / n
        K.blob(f'{name}_schulp{i}', (width / n / 2, 0.035, 0.09), 2.2, (14, 8),
               mat=wol('Vilt luifelrand ' + ('r' if i % 2 == 0 else 'w'), '#d9443a' if i % 2 == 0 else '#fbf7ef'),
               parent=root, loc=(xx, y - 0.84, height * 0.72 - 0.38))
    # uithangbord met letters
    bm = wol('Vilt bord', '#5b3b2a')
    box(name + '_bord', (0, y - 0.06, height * 0.9), (width * 0.36, 0.05, 0.22), bm, root, n=6)
    tm = wol('Vilt letters', '#f7e2a6', sheet=True)
    K.text_obj(name + '_tekst', 'BAKKER', size=0.3, extrude=0.02, bevel=0.006, mat=tm, parent=root,
               loc=(0, y - 0.13, height * 0.9 - 0.11), rot=(math.radians(90), 0, 0))
    return root


def wol_streep_x(name, c1, c2, period):
    m = _cached(name)
    if m:
        return m
    g = M.NT(name)
    co = g.coord('Object')
    x, y, z = g.sep(co)
    st = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', x, 2 * math.pi / period)), 0.0)
    g.principled(color=g.mix(st, M.C(c1), M.C(c2)), rough=1.0)
    m = g.done([n for n in g.t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0])
    _MC[name] = m
    return m


def lamp_post(name, loc, parent=None, h=2.6, night=False):
    root = K.empty(name, loc, (0, 0, 0), 1.0, parent)
    pm = wol('Vilt lantaarn', '#2f4a3e')
    F = S.Field()
    F.add(*S.Cone((0, 0, 0), (0, 0, h), 0.07, 0.045))
    F.add(*S.Cyl((0, 0, 0), (0, 0, 0.12), 0.13) if hasattr(S, 'Cyl') else S.Sph((0, 0, 0.04), 0.12), k=0.03)
    piece(name + '_paal', F, *fbounds(F, 0.03), pm, root, h=0.008)
    box(name + '_kap', (0, 0, h + 0.22), (0.17, 0.17, 0.05), pm, root, n=4)
    lm = M.emission('Lantaarnlicht', '#ffd27a', 4.0 if night else 0.6)
    box(name + '_glas', (0, 0, h + 0.07), (0.12, 0.12, 0.13), lm, root, n=6)
    if night:
        K.light('POINT', (loc[0], loc[1], h + 0.05), (0, 0, 0), energy=60, size=0.2, color=(1.0, 0.82, 0.5))
    return root


def bunting(name, a, b, n=12, parent=None, sag=0.35, colors=('#d9443a', '#ffd34d', '#4f9ad9', '#7ab648', '#f27c9b')):
    """Vlaggenlijn: driehoekjes vilt aan een koord."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    t = np.linspace(0, 1, 40)
    P = a[None] * (1 - t[:, None]) + b[None] * t[:, None]
    P[:, 2] -= sag * 4 * t * (1 - t)
    K.curve_tube(name + '_koord', [tuple(p) for p in P], 0.008, garen('Garen koord', '#f3ead8'), parent)
    for i in range(n):
        u = (i + 0.5) / n
        p = a * (1 - u) + b * u
        p[2] -= sag * 4 * u * (1 - u)
        tri = np.array([(-0.13, 0.0), (0.13, 0.0), (0.0, -0.26)])
        c = colors[i % len(colors)]
        slab(f'{name}_vlag{i}', _dens(tri, 3), 0.02, wol('Vilt vlag ' + c, c, sheet=True), parent, loc=tuple(p),
             rot=(0, 0, math.atan2(b[1] - a[1], b[0] - a[0])))


# ------------------------------------------------------------------ straat en park
def street(parent=None, x0=-9.0, x1=9.0, bakery_x=0.0, night=False, houses=True, y_house=3.0, trees=True, seed=1,
           backdrop_y=9.5, flowers_n=30):
    """Straat: keitjesweg (y -2.6..0.9), stoep (0.9..y_house), huisjes en bakkerij, achterdoek."""
    backdrop(y=backdrop_y, night=night, x0=(x0 + x1) / 2, sun=((x0 + x1) / 2 + 5, 7.2))
    cobbles('Weg', x0, x1, -2.8, 0.85, parent, seed=seed)
    cobbles('Stoep', x0, x1, 0.95, y_house + 0.1, parent, size=(0.22, 0.22, 0.03), seed=seed + 1,
            colors=['#ddd5c7', '#d2cabb', '#e4ddd0'], tile=True)
    box('Stoeprand', ((x0 + x1) / 2, 0.9, 0.05), ((x1 - x0) / 2, 0.07, 0.06), wol('Vilt stoeprand', PAL['curb']),
        parent, n=6, res=(64, 12))
    ground('Achtergrond', x0 - 4, x1 + 4, y_house, backdrop_y, PAL['grass'], parent)
    if houses:
        i = 0
        if bakery_x is not None:
            bakery('Bakkerij', bakery_x, parent, y=y_house, night=night)
            left, right = bakery_x - 1.62, bakery_x + 1.62
        else:
            left = right = (x0 + x1) / 2 + 0.06
        xx = left
        while xx > x0 - 1.5:
            w = 2.4 + 0.4 * (i % 2)
            house(f'Huis{i}', xx - w / 2, w, 2.25 + (i % 3) * 0.3, parent, y=y_house, seed=i + seed, night=night)
            xx -= w + 0.12
            i += 1
        xx = right
        while xx < x1 + 1.5:
            w = 2.4 + 0.4 * (i % 2)
            house(f'Huis{i}', xx + w / 2, w, 2.25 + (i % 3) * 0.3, parent, y=y_house, seed=i + seed, night=night)
            xx += w + 0.12
            i += 1
    if trees:
        for i, tx in enumerate(np.arange(x0 + 2.0, x1, 5.2)):
            if bakery_x is not None and abs(tx - bakery_x) < 2.0:
                continue
            tree(f'Straatboom{i}', (tx, 1.8, 0), h=2.2, crown=0.6, parent=parent, seed=i)
    flowers('Bloemen', (x0, x1, y_house - 0.35, y_house - 0.08), flowers_n, parent, seed=seed)


def park(parent=None, x0=-9.0, x1=9.0, y0=-3.5, y1=9.0, path=True, seed=3, night=False, trees=None, bushes=None,
         tufts=600, flowers_n=80, backdrop_y=10.0):
    backdrop(y=backdrop_y, night=night, x0=(x0 + x1) / 2, sun=((x0 + x1) / 2 - 5, 7.4))
    # zacht glooiend grasveld
    nu, nv = 70, 40
    U = np.linspace(x0, x1, nu)
    Vv = np.linspace(y0, backdrop_y - 1.0, nv)
    X, Y = np.meshgrid(U, Vv)
    Z = 0.0 + np.clip((Y - 3.0) / 6.0, 0, 1) ** 2 * (0.5 + 0.35 * np.sin(X * 0.5 + seed))
    P = np.stack([X, Y, Z], -1).reshape(-1, 3)
    F = [(i * nu + j, i * nu + j + 1, (i + 1) * nu + j + 1, (i + 1) * nu + j) for i in range(nv - 1)
         for j in range(nu - 1)]
    K.mesh_obj('Grasveld', P, F, wol('Vilt gras', PAL['grass']), parent)
    if path:
        cobbles('Pad', x0, x1, -1.3, -0.2, parent, size=(0.16, 0.12, 0.025), seed=seed,
                colors=['#d8c49a', '#cdb88c', '#e2d0aa'], tile=True)
    for i, (tx, ty, th, cr) in enumerate(trees if trees is not None else
                                         [(-6.5, 4.5, 2.6, 0.95), (6.8, 5.5, 2.8, 1.0), (-2.5, 7.5, 2.2, 0.8),
                                          (3.0, 8.0, 2.4, 0.85)]):
        tree(f'Boom{i}', (tx, ty, 0), h=th, crown=cr, parent=parent, seed=i + seed, apples=5 if i == 0 else 0)
    for i, (bx, by, bs) in enumerate(bushes if bushes is not None else [(-4.0, 3.0, 0.6), (4.5, 3.5, 0.7)]):
        bush(f'Struik{i}', (bx, by, 0), bs, parent, seed=i + 20, berries=6)
    grass_tufts('Grasplukjes', (x0 * 0.6, x1 * 0.6, y0 + 0.2, 3.5), tufts, parent, seed=seed)
    flowers('Bloemen', (x0 * 0.7, x1 * 0.7, 0.4, 4.0), flowers_n, parent, seed=seed + 1)


# ------------------------------------------------------------------ binnen
def bedroom(night=False, parent=None, bed=True, wall_y=2.0, wall_x=None, bed_x=-0.9, sleeper=False, window_x=1.3,
            bed_y=None, bed_rot=0.0, stand=None):
    """Kamer: achterwand met sterrenbehang en raam, vloer met rond kleed, bed met lappendeken."""
    root = K.empty('Kamer', (0, 0, 0), (0, 0, 0), 1.0, parent)
    wall = wol('Vilt behang', '#cfe4f2' if not night else '#8fa6c9')
    box('Achterwand', (0, wall_y + 0.1, 1.6), (4.0, 0.1, 1.7), wall, root, n=10, res=(48, 24))
    if wall_x is not None:
        box('Zijwand', (wall_x - 0.1, 0.0, 1.6), (0.1, 2.2, 1.7), wall, root, n=10, res=(48, 24))
    floor = wol('Vilt vloer', '#cf9f6f')
    box('Vloer', (0, -0.5, -0.05), (4.0, 3.0, 0.05), floor, root, n=10)
    rng = np.random.default_rng(5)
    ym = wol('Vilt behangster', '#f4d36b' if not night else '#ffe9a0', sheet=True)
    for i in range(40):
        x, z = rng.uniform(-3.8, 3.8), rng.uniform(0.5, 3.2)
        if abs(x - window_x) < 0.75 and 0.9 < z < 2.4:
            continue
        slab(f'Behangster{i}', star(0.07, 0.03), 0.012, ym, root, loc=(x, wall_y - 0.005, z))
    # raam met gordijntjes
    wx, wz = window_x, 1.65
    fr = wol('Vilt kozijn', PAL['frame'], sheet=True)
    box('Raamkozijn', (wx, wall_y - 0.03, wz), (0.6, 0.05, 0.62), fr, root, n=6)
    if night:
        box('Raamlucht', (wx, wall_y - 0.06, wz), (0.52, 0.03, 0.54), wol('Vilt nachtlucht', PAL['night'], sheet=True),
            root, n=8)
        slab('Raammaan', puff(np.array([0.0, 0.0]), 48, [(0, 0, 0.13)]), 0.02,
             wol('Vilt maan', '#f7e6a3', sheet=True), root, loc=(wx + 0.22, wall_y - 0.09, wz + 0.25))
        for i in range(6):
            slab(f'Raamster{i}', star(0.04, 0.016), 0.012, wol('Vilt ster', '#ffe17a', sheet=True), root,
                 loc=(wx + rng.uniform(-0.42, 0.3), wall_y - 0.09, wz + rng.uniform(-0.4, 0.42)))
    else:
        box('Raamlucht', (wx, wall_y - 0.06, wz), (0.52, 0.03, 0.54), wol('Vilt ruit', PAL['pane'], sheet=True, fuzz=0.4),
            root, n=8)
        cloud('Raamwolk', (wx - 0.1, wall_y - 0.1, wz + 0.15), 0.25, root)
    box('Raamroede1', (wx, wall_y - 0.1, wz), (0.02, 0.015, 0.54), fr, root, n=4)
    box('Raamroede2', (wx, wall_y - 0.1, wz), (0.52, 0.015, 0.02), fr, root, n=4)
    cm = wol('Vilt gordijn', '#f2a7b6')
    for s in (-1, 1):
        Fg = S.Field()
        for k in range(4):
            xx = wx + s * (0.62 + k * 0.07)
            Fg.add(*S.Cap((xx, wall_y - 0.14, 0.85), (xx, wall_y - 0.14, 2.42), 0.05), k=0.04)
        piece(f'Gordijn{s}', Fg, *fbounds(Fg, 0.02), cm, root, h=0.012)
    box('Gordijnroede', (wx, wall_y - 0.16, 2.45), (1.05, 0.025, 0.025), wol('Vilt hout', '#9a6a40'), root, n=4)
    # rond kleed: ringen
    for i, (r, c) in enumerate([(1.1, '#7ab3d9'), (0.85, '#f4d36b'), (0.6, '#f2a7b6'), (0.35, '#7ab648')]):
        K.blob(f'Kleed{i}', (r, r * 0.8, 0.012 + i * 0.004), 2.0, (64, 8), mat=wol('Vilt kleed ' + c, c, sheet=True),
               parent=root, loc=(-0.2, -0.4, 0.006 + i * 0.004))
    # speelgoedkast
    wood = wol('Vilt hout licht', '#d9a874')
    sx = -2.4
    box('Kast', (sx, wall_y - 0.3, 0.55), (0.55, 0.28, 0.55), wood, root, n=6)
    box('Kastvak', (sx, wall_y - 0.56, 0.62), (0.47, 0.05, 0.2), wol('Vilt kastvak', '#a4774c'), root, n=5)
    for i, (c, lt) in enumerate([('#d9443a', 'A'), ('#4f9ad9', 'B'), ('#ffd34d', 'C')]):
        box(f'Blok{i}', (sx - 0.3 + i * 0.3, wall_y - 0.3, 1.2), (0.12, 0.12, 0.12), wol('Vilt blok ' + c, c), root,
            n=5)
    K.blob('Bal', (0.16, 0.16, 0.16), 2.0, (24, 12), mat=wol('Vilt bal', '#f27c9b'), parent=root,
           loc=(sx + 0.75, wall_y - 0.6, 0.16))
    if bed:
        bed_(root, (bed_x, wall_y - 0.75 if bed_y is None else bed_y, 0), night, sleeper, bed_rot)
    if night:
        lampje = M.emission('Nachtlampje', '#ffcf7a', 6.0)
        nx, ny = stand if stand is not None else (bed_x + 0.85, wall_y - 0.35)
        box('Nachtkastje', (nx, ny, 0.28), (0.24, 0.22, 0.28), wood, root, n=6)
        K.blob('Lampvoet', (0.06, 0.06, 0.12), 2.0, (16, 8), mat=wol('Vilt lampvoet', '#7ab3d9'), parent=root,
               loc=(nx, ny, 0.68))
        K.blob('Lampkap', (0.15, 0.15, 0.12), 3.0, (24, 12), mat=lampje, parent=root, loc=(nx, ny, 0.86))
        K.light('POINT', (nx, ny - 0.15, 0.86), (0, 0, 0), energy=80, size=0.25, color=(1.0, 0.78, 0.45))
    return root


def bed_(parent, loc, night=False, sleeper=False, rot=0.0):
    root = K.empty('Bed', loc, (0, 0, rot), 1.0, parent)
    wood = wol('Vilt bedhout', '#b98652')
    box('Hoofdeind', (0, 0.62, 0.5), (0.5, 0.06, 0.5), wood, root, n=6)
    box('Voeteind', (0, -0.72, 0.3), (0.5, 0.06, 0.3), wood, root, n=6)
    box('Bedbak', (0, -0.05, 0.2), (0.48, 0.66, 0.12), wood, root, n=6)
    box('Matras', (0, -0.05, 0.36), (0.46, 0.64, 0.07), wol('Vilt matras', '#fbf7ef'), root, n=6)
    K.blob('Kussen', (0.3, 0.14, 0.08), 3.0, (24, 12), mat=wol('Vilt kussen', '#fbf7ef'), parent=root,
           loc=(0, 0.45, 0.48))
    # lappendeken: blokjes in kleuren met steekjes
    cols = ['#7ab3d9', '#f4d36b', '#f2a7b6', '#7ab648', '#fbf7ef', '#b47ae0']
    th = garen('Garen wit', '#ffffff')
    k = 0
    for i in range(4):
        for j in range(5):
            x = -0.36 + i * 0.24
            y = 0.2 - j * 0.2
            c = cols[(i + 2 * j) % len(cols)]
            zl = 0.45
            if sleeper:
                # deken bolt over het slapende lijfje
                zl += 0.2 * math.exp(-((x - 0.0) / 0.32) ** 2) * (1 if y < 0.28 else 0.4)
            ob = box(f'Lap{i}{j}', (x, y, zl), (0.122, 0.104, 0.035), wol('Vilt lap ' + c, c, sheet=True), root, n=6,
                     res=(16, 8))
            k += 1
    return root


def bakery_inside(parent=None, empty=True):
    """Bakkerij binnen: tegelwand, schappen met broden, toonbank met vitrine."""
    root = K.empty('Winkel', (0, 0, 0), (0, 0, 0), 1.0, parent)
    g = M.NT('Vilt tegelwand')
    co = g.coord('Object')
    x, y, z = g.sep(co)
    a = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', x, 2 * math.pi / 0.5)), 0.0)
    b = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', z, 2 * math.pi / 0.5)), 0.0)
    chk = g.math('ABSOLUTE', g.math('SUBTRACT', a, b))
    g.principled(color=g.mix(chk, K.srgb('#f6efe0'), K.srgb('#f2d2c4')), rough=1.0)
    wm = g.done([n for n in g.t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0])
    box('Wand', (0, 2.6, 1.7), (4.5, 0.1, 1.8), wm, root, n=10, res=(48, 24))
    box('Vloer', (0, 0, -0.05), (4.5, 3.0, 0.05), wol('Vilt winkelvloer', '#c9b08a'), root, n=10)
    wood = wol('Vilt hout', '#9a6a40')
    for z in (1.2, 1.75, 2.3):
        box(f'Schap{z}', (0, 2.35, z), (2.0, 0.2, 0.03), wood, root, n=5)
    rng = np.random.default_rng(3)
    bread = wol('Vilt brood', '#d99a55')
    for z in (1.2, 1.75, 2.3):
        for i, x in enumerate(np.linspace(-1.75, 1.75, 6)):
            if empty and z < 2.0:
                # lege schaaltjes
                K.blob(f'Schaal{z}{i}', (0.16, 0.12, 0.03), 2.5, (20, 8), mat=wol('Vilt schaal', '#fbf7ef'), parent=root,
                       loc=(x, 2.3, z + 0.05))
                continue
            K.blob(f'Brood{z}{i}', (0.2, 0.11, 0.1), 2.2, (20, 10), mat=bread, parent=root, loc=(x, 2.3, z + 0.12),
                   rot=(0, 0, rng.uniform(-0.2, 0.2)))
    # toonbank
    box('Toonbank', (0, 0.9, 0.25), (1.8, 0.34, 0.25), wol('Vilt toonbank', '#f4e4c4'), root, n=6)
    box('Toonbankblad', (0, 0.9, 0.52), (1.9, 0.4, 0.035), wood, root, n=5)
    st = wol_streep_x('Vilt toonbankstreep', '#d9443a', '#fbf7ef', 0.4)
    box('Toonbankband', (0, 0.55, 0.33), (1.8, 0.03, 0.1), st, root, n=6)
    # koekjespot (leeg)
    K.blob('Pot', (0.15, 0.15, 0.19), 2.5, (24, 12), mat=M.thin_glass('Potglas'), parent=root, loc=(1.4, 0.9, 0.745))
    K.blob('Potdeksel', (0.16, 0.16, 0.04), 2.5, (24, 8), mat=wol('Vilt deksel', '#d9443a'), parent=root,
           loc=(1.4, 0.9, 0.955))
    return root


# ------------------------------------------------------------------ rekwisieten
def cookie(name, parent=None, loc=(0, 0, 0), r=0.05, rot=(0, 0, 0), seed=0, bite=False):
    rng = np.random.default_rng(seed)
    root = K.empty(name, loc, rot, 1.0, parent)
    F = S.Field()
    F.add(*S.Ell((0, 0, 0), (r, r, r * 0.28)))
    if bite:
        F.cut(*S.Sph((r * 0.95, r * 0.3, 0), r * 0.35), k=0.004)
    piece(name + '_deeg', F, *fbounds(F, 0.01), wol('Vilt koek', '#d9a35e'), root, h=max(0.002, r / 22))
    chips = []
    for i in range(6):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 0.7) * r
        chips.append((math.cos(a) * d, math.sin(a) * d, r * 0.24))
    instances(name + '_chips', chips, (r * 0.12, r * 0.12, r * 0.09), [hexc('#4a2a17')] * len(chips),
              colmat('Vilt chocolade'), root, n=2.0, res=(10, 6))
    return root


def plate(name, parent=None, loc=(0, 0, 0), r=0.16):
    return K.blob(name, (r, r, 0.02), 2.6, (32, 8), mat=wol('Vilt bord', '#fbf7ef'), parent=parent, loc=loc)


def crumbs(name, pts, parent=None, seed=1, size=0.012):
    rng = np.random.default_rng(seed)
    pts = np.asarray(pts, float)
    sz = np.stack([size * rng.uniform(0.6, 1.3, len(pts))] * 2 + [size * rng.uniform(0.4, 0.7, len(pts))], 1)
    cols = [hexc(['#b8742f', '#c98a40', '#a5652a'][i % 3]) * rng.uniform(0.85, 1.1) for i in range(len(pts))]
    return instances(name, pts, sz, cols, colmat('Vilt kruimels'), parent, n=2.4, res=(8, 5))


def sack(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), size=0.32, cookies=4):
    root = K.empty(name, loc, rot, 1.0, parent)
    F = S.Field()
    F.add(*S.Ell((0, 0, size * 0.55), (size * 0.62, size * 0.55, size * 0.58)))
    F.add(*S.Cone((0, 0, size * 0.9), (0, 0, size * 1.12), size * 0.2, size * 0.24), k=0.04)
    lump = Lump(9, 0.006, 12)
    f = lambda P: S.smax(F(P) + lump(P), -P[:, 2], 0.01)
    piece(name + '_zak', f, *fbounds(F, 0.03), wol('Vilt jute', '#b48c58'), root, h=0.006)
    K.curve_tube(name + '_touw', [(size * 0.21 * math.cos(t), size * 0.21 * math.sin(t), size * 0.98)
                                  for t in np.linspace(0, 2 * math.pi, 24)], 0.012, garen('Garen touw', '#e8d8a8'), root)
    for i in range(cookies):
        a = i * 2 * math.pi / max(cookies, 1)
        cookie(f'{name}_koek{i}', root, (math.cos(a) * size * 0.1, math.sin(a) * size * 0.1, size * 1.16),
               r=size * 0.18, rot=(0.6 * math.cos(a), 0.6 * math.sin(a), 0), seed=i)
    return root


def magnifier(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), r=0.07):
    root = K.empty(name, loc, rot, 1.0, parent)
    F = S.Field()
    F.add(*S.Tor((0, 0, 0), r, r * 0.16, S.rot(math.pi / 2, 0, 0)))
    piece(name + '_ring', F, *fbounds(F, 0.01), wol('Vilt goudgeel', '#e8b33c'), root, h=0.0025)
    K.blob(name + '_lens', (r * 0.95, r * 0.12, r * 0.95), 2.0, (32, 12), mat=M.thin_glass('Lensglas', refl=0.3),
           parent=root)
    Fh = S.Field()
    Fh.add(*S.Cap((0, 0, -r * 1.1), (0, 0, -r * 3.0), r * 0.17))
    piece(name + '_steel', Fh, *fbounds(Fh, 0.01), wol('Vilt steel rood', '#c63b33'), root, h=0.0025)
    return root


def medal(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), r=0.04, ribbon=0.09):
    root = K.empty(name, loc, rot, 1.0, parent)
    rib = np.array([(-r * 0.45, 0.0), (r * 0.45, 0.0), (r * 0.25, -ribbon), (-r * 0.25, -ribbon)])
    slab(name + '_lint', _dens(rib, 3), 0.004, wol('Vilt lint', '#3a6fd1', sheet=True), root, loc=(0, 0, ribbon))
    slab(name + '_munt', ellipse(r, r, 40), 0.008, wol('Vilt medaille', '#f0bd3c'), root, loc=(0, -0.004, -r * 0.8))
    slab(name + '_ster', star(r * 0.55, r * 0.24), 0.004, wol('Vilt medaillester', '#fff2b0', sheet=True), root,
         loc=(0, -0.013, -r * 0.8))
    return root


def confetti(name, n, region, parent=None, seed=4, size=0.025):
    rng = np.random.default_rng(seed)
    (x0, y0, z0), (x1, y1, z1) = region
    locs = np.stack([rng.uniform(x0, x1, n), rng.uniform(y0, y1, n), rng.uniform(z0, z1, n)], 1)
    cols = [hexc(c) for c in rng.choice(['#d9443a', '#ffd34d', '#4f9ad9', '#7ab648', '#f27c9b', '#b47ae0'], n)]
    return instances(name, locs, (size, size, size * 0.18), cols, colmat('Vilt confetti', sheet=True), parent, n=2.0,
                     res=(10, 5), rotz=rng.uniform(0, 6.28, n))


def crate(name, parent=None, loc=(0, 0, 0), size=(0.7, 0.5, 0.3)):
    root = K.empty(name, loc, (0, 0, 0), 1.0, parent)
    w, d, h = size
    box(name + '_kist', (0, 0, h / 2), (w / 2, d / 2, h / 2), wol('Vilt kist', '#c08a58'), root, n=7)
    for z in (h * 0.3, h * 0.7):
        box(name + f'_lat{z:.2f}', (0, -d / 2 - 0.01, z), (w / 2 - 0.02, 0.012, 0.04), wol('Vilt lat', '#9a6a40'), root,
            n=5)
    return root


def table(name, parent=None, loc=(0, 0, 0), size=(1.6, 0.8, 0.5)):
    root = K.empty(name, loc, (0, 0, 0), 1.0, parent)
    w, d, h = size
    g = M.NT('Vilt ruitjeskleed')
    co = g.coord('Object')
    x, y, z = g.sep(co)
    a = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', x, 2 * math.pi / 0.2)), 0.0)
    b = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', g.math('ADD', y, z), 2 * math.pi / 0.2)), 0.0)
    chk = g.math('MULTIPLY', a, b)
    g.principled(color=g.mix(chk, K.srgb('#fbf7ef'), K.srgb('#d9443a')), rough=1.0)
    cm = g.done([n for n in g.t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0])
    wood = wol('Vilt tafelhout', '#9a6a40')
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f'{name}_poot{sx}{sy}', (sx * (w / 2 - 0.08), sy * (d / 2 - 0.08), h / 2), (0.045, 0.045, h / 2), wood,
                root, n=4)
    # kleed met zachte overhang
    F = S.Field()
    F.add(*S.Box((0, 0, h - 0.06), (w / 2 + 0.06, d / 2 + 0.06, 0.07), 0.04))
    piece(name + '_kleed', F, *fbounds(F, 0.03), cm, root, h=0.008)
    return root


def police_car(name, parent=None, loc=(0, 0, 0), yaw=0.0, lights=True, scale=1.0):
    """Open politieautootje van vilt (kinderformaat): wit met blauwe band, wieltjes met knoopjes,
    rolbeugel met blauw zwaailicht. Kijkt naar -y."""
    root = K.empty(name, loc, (0, 0, yaw), scale, parent)
    white = wol('Vilt autowit', '#f7f6f2')
    blue = wol('Vilt autoblauw', '#2f5fc4')
    F = S.Field()
    F.add(*S.Box((0, 0, 0.32), (0.4, 0.74, 0.16), 0.1))
    F.add(*S.Ell((0, -0.5, 0.36), (0.38, 0.32, 0.16)), k=0.08)
    F.cut(*S.Box((0, 0.12, 0.5), (0.31, 0.36, 0.2), 0.08), k=0.03)
    lump = Lump(5, 0.003, 9)
    fc = lambda P: F(P) + lump(P)
    piece(name + '_carrosserie', fc, (-0.6, -1.0, 0.0), (0.6, 0.95, 0.65), white, root, h=0.008)
    # blauwe band rondom
    fb = lambda P: S.smax(fc(P) - 0.008, np.abs(P[:, 2] - 0.3) - 0.045, 0.006)
    piece(name + '_band', fb, (-0.6, -1.0, 0.2), (0.6, 0.95, 0.4), blue, root, h=0.006)
    fo = lambda P: S.smax(fc(P) - 0.01, np.abs(P[:, 2] - 0.365) - 0.012, 0.004)
    piece(name + '_oranje', fo, (-0.6, -1.0, 0.3), (0.6, 0.95, 0.42), wol('Vilt autooranje', '#f08a1c'), root,
          h=0.005)
    # stoeltjes
    seat = wol('Vilt stoel', '#2a3550')
    box(name + '_stoel', (0, 0.32, 0.36), (0.26, 0.12, 0.1), seat, root, n=5)
    box(name + '_leuning', (0, 0.44, 0.55), (0.26, 0.06, 0.2), seat, root, n=5)
    # stuurtje en ruitje
    Fs = S.Field()
    Fs.add(*S.Tor((0, 0, 0), 0.09, 0.016, S.rot(math.radians(60), 0, 0)))
    piece(name + '_stuur', lambda P: Fs(P - np.array([-0.12, 0.12, 0.6], np.float32)), (-0.24, -0.02, 0.48),
          (0.0, 0.26, 0.72), wol('Vilt zwart', '#1d1d22'), root, h=0.003)
    box(name + '_ruitrand', (0, -0.36, 0.66), (0.3, 0.02, 0.1), blue, root, n=5, rot=(math.radians(-20), 0, 0))
    box(name + '_ruit', (0, -0.375, 0.665), (0.26, 0.012, 0.075), wol('Vilt autoruit', '#cfe9f7', sheet=True), root,
        n=6, rot=(math.radians(-20), 0, 0))
    # wielen met knoopjes
    for sx in (-1, 1):
        for sy in (-0.48, 0.5):
            Fw = S.Field()
            Fw.add(*S.Tor((sx * 0.5, sy, 0.16), 0.11, 0.06, S.rot(0, math.pi / 2, 0)))
            piece(f'{name}_wiel{sx}{sy}', Fw, *fbounds(Fw, 0.02), wol('Vilt zwart', '#1d1d22'), root, h=0.006)
            hub = K.blob(f'{name}_naaf{sx}{sy}', (0.075, 0.075, 0.02), 2.4, (20, 8),
                         mat=wol('Vilt naaf', '#e8eaee'), parent=root, loc=(sx * 0.565, sy, 0.16),
                         rot=(0, math.pi / 2, 0))
            for k in range(4):
                a = k * math.pi / 2 + math.pi / 4
                K.blob(f'{name}_gaatje{sx}{sy}{k}', (0.012, 0.012, 0.006), 2.0, (8, 6), mat=wol('Vilt zwart', '#1d1d22'),
                       parent=root, loc=(sx * 0.586, sy + math.cos(a) * 0.025, 0.16 + math.sin(a) * 0.025),
                       rot=(0, math.pi / 2, 0))
    # koplampen en achterlichten
    for sx in (-1, 1):
        K.blob(f'{name}_koplamp{sx}', (0.06, 0.02, 0.05), 2.0, (16, 8), mat=wol('Vilt koplamp', '#ffe48a'),
               parent=root, loc=(sx * 0.24, -0.84, 0.36))
        K.blob(f'{name}_achterlicht{sx}', (0.05, 0.02, 0.035), 2.0, (16, 8), mat=wol('Vilt achterlicht', '#d9443a'),
               parent=root, loc=(sx * 0.28, 0.83, 0.36))
    # rolbeugel met zwaailicht
    Fr = S.Field()
    Fr.add(*S.Chain([(-0.3, 0.6, 0.4), (-0.28, 0.6, 0.85), (0.0, 0.6, 0.92), (0.28, 0.6, 0.85), (0.3, 0.6, 0.4)],
                    [0.025] * 5))
    piece(name + '_beugel', Fr, *fbounds(Fr, 0.02), blue, root, h=0.005)
    box(name + '_lichtbak', (0, 0.6, 0.97), (0.12, 0.06, 0.04), wol('Vilt zwart', '#1d1d22'), root, n=5)
    lm = M.emission('Zwaailicht', '#4aa3ff', 9.0 if lights else 0.5)
    K.blob(name + '_zwaailicht', (0.07, 0.05, 0.06), 2.0, (16, 10), mat=lm, parent=root, loc=(0, 0.6, 1.04))
    if lights:
        K.light('POINT', (0, 0.6, 1.1), (0, 0, 0), energy=30, size=0.1, color=(0.3, 0.6, 1.0)).parent = root
    # POLITIE op beide zijkanten
    tm = wol('Vilt autoletters', '#1e3f8f', sheet=True)
    for sx in (-1, 1):
        X = np.array([0, 1.0 if sx > 0 else -1.0, 0])
        Y = np.array([0, 0, 1.0])
        Z = np.cross(X, Y)
        Rm = Matrix((tuple(X), tuple(Y), tuple(Z))).transposed()
        K.text_obj(f'{name}_politie{sx}', 'POLITIE', size=0.11, extrude=0.006, bevel=0.002, mat=tm, parent=root,
                   loc=(sx * 0.505, 0.02, 0.215), rot=tuple(Rm.to_euler()))
    return root
