"""Tafelmaquettes van wol en vilt (ware grootte, een scène is ca. 30-50 cm breed): heuvels en grond van
gevilte wol, grasplukjes en wolken van plukwol, een luchtdoek, lollybomen, struikjes, bloemetjes."""
import math
import numpy as np
from . import core as K, sdf as S
from .wol import vlak, plukwol, edge, smooth, Noise, c, _n, F32, surf_hit, circle_poly, star_poly, bead


def sky(y=0.22, width=0.9, height=0.42, x0=0.0, night=False, bend=0.12, top='#7fb8e4', bottom='#bfe0f2', seed=1):
    """Luchtdoek van vilt dat met een bocht in de grond overgaat (gevilt verloop van boven naar beneden)."""
    if night:
        top, bottom = '#16204a', '#2a3a74'

    def f(P):
        # gebogen plaat: afstand tot het oppervlak y = y + buiging, dikte 4 mm
        yy = y - bend * np.clip(1 - P[:, 2] / (height * 0.35), 0, 1) ** 2
        return np.abs(P[:, 1] - yy) - 0.004
    nz = Noise(seed, 60.0, 7)
    colfn = lambda V: (c(bottom)[None] * (1 - smooth(0.02, height * 0.9, V[:, 2])[:, None]) +
                       c(top)[None] * smooth(0.02, height * 0.9, V[:, 2])[:, None]) * \
                      (1 + 0.05 * nz(V))[:, None]
    lo = (x0 - width / 2, y - bend - 0.01, -0.01)
    hi = (x0 + width / 2, y + 0.01, height)
    ob, ff = vlak('Luchtdoek', f, colfn, None, h=0.002, lo=lo, hi=hi, lump=0.0008, seed=seed, fuzz=0.6)
    return ob


def cloud(name, center, size=0.05, seed=2, color='#fbfaf6'):
    """Wolk van plukwol: veel korte, gekrulde bundels in een bolle wolkvorm."""
    rng = np.random.default_rng(seed)
    cc = np.asarray(center, float)
    lobes = [(0, 0, 0, 1.0), (-0.9, 0, -0.15, 0.75), (0.9, 0, -0.12, 0.8), (-0.4, 0, 0.35, 0.75),
             (0.45, 0, 0.3, 0.8)]
    guides = []
    for _ in range(120):
        lx, ly, lz, lr = lobes[rng.integers(len(lobes))]
        dvec = _n(rng.normal(size=3) * np.array([1, 0.4, 1]))
        p0 = cc + np.array([lx, ly, lz]) * size * 0.55 + dvec * size * 0.45 * lr * rng.uniform(0.2, 1.0)
        dd = _n(rng.normal(size=3) * np.array([1, 0.3, 0.6]))
        pts = [p0]
        L = size * rng.uniform(0.25, 0.5)
        for k in range(1, 6):
            dd = _n(dd + rng.normal(0, 0.45, 3))
            pts.append(pts[-1] + dd * L / 5)
        guides.append(pts)
    return plukwol(name, np.array(guides), size * 0.06, color, None, per=55, radius=0.00005, seed=seed,
                   spread_tip=2.2, jitter=0.6, colors=[color, '#ffffff', '#eef2f6'])


def sun(name, center, r=0.03, color='#f6c445'):
    F = S.Field()
    F.add(*S.Ell(tuple(center), (r, 0.006, r)))
    ob, _ = vlak(name, None, color, None, h=0.0012, F=F, lump=0.0008, seed=7)
    return ob


def ground(name='Grond', x0=-0.45, x1=0.45, y0=-0.3, y1=0.25, color='#7fae4a', hills=(), seed=3, patches=()):
    """Vilten grondplaat met zachte heuveltjes [(x, y, rx, ry, h)] en gekleurde vlakken [(maskfn, kleur)]."""
    nz = Noise(seed, 40.0, 7)
    nz2 = Noise(seed + 1, 300.0, 7)

    def f(P):
        z = 0.002 * nz(P[:, :2].repeat(2, 1)[:, :3] if False else np.stack([P[:, 0], P[:, 1], np.zeros(len(P))], 1))
        for hx, hy, rx, ry, hh in hills:
            z = z + hh * np.exp(-(((P[:, 0] - hx) / rx) ** 2 + ((P[:, 1] - hy) / ry) ** 2))
        return P[:, 2] - z
    slab = lambda P: S.smax(S.smax(f(P), -P[:, 2] - 0.02, 0.002),
                            np.maximum(np.maximum(x0 - P[:, 0], P[:, 0] - x1), np.maximum(y0 - P[:, 1], P[:, 1] - y1)),
                            0.01)
    hmax = max([0.01] + [h for *_, h in hills]) + 0.01
    colfn = lambda V: c(color)[None] * (1 + 0.07 * nz2(V))[:, None]
    ob, ff = vlak(name, slab, colfn, None, h=0.0018, lo=(x0 - 0.01, y0 - 0.01, -0.03), hi=(x1 + 0.01, y1 + 0.01, hmax),
                  regions=list(patches), lump=0.0005, seed=seed, fuzz=0.9)
    return ob, f


def height_at(f, x, y):
    lo, hi = -0.05, 0.2
    for _ in range(40):
        mid = (lo + hi) / 2
        if f(np.array([[x, y, mid]], F32))[0] < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def tufts(name, fground, region, n, color=('#6aa83f', '#88c25a', '#5b9636'), h=(0.004, 0.009), seed=4, mask=None):
    """Grasplukjes van groene plukwol."""
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = region
    guides = []
    cols = []
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if mask is not None and not mask(x, y):
            continue
        z = height_at(fground, x, y)
        d = _n(np.array([rng.normal(0, 0.35), rng.normal(0, 0.35), 1.0]))
        L = rng.uniform(*h)
        pts = [np.array([x, y, z - 0.0006])]
        for k in range(1, 5):
            d = _n(d + np.array([rng.normal(0, 0.1), rng.normal(0, 0.1), -0.05]))
            pts.append(pts[-1] + d * L / 4)
        guides.append(pts)
    return plukwol(name, np.array(guides), 0.0016, color[0], None, per=40, radius=0.00006, seed=seed, spread_tip=2.2,
                   jitter=0.35, colors=list(color))


def lolly_tree(name, base, h=0.12, r=0.035, color='#5e9e46', trunk='#8a5a36', apples=0, seed=5):
    """Lollyboom: gevilte stam en een bolle kruin van wol (soms met appeltjes)."""
    rng = np.random.default_rng(seed)
    bx, by, bz = base
    T = S.Field()
    T.add(*S.Cone((bx, by, bz - 0.003), (bx + 0.002, by, bz + h * 0.7), 0.0065, 0.0042))
    vlak(name + '_stam', None, trunk, None, h=0.0007, F=T, seed=seed, lump=0.0004,
         regions=[(lambda V: 0.3 * (0.5 + 0.5 * Noise(seed, 900.0, 5)(V)), '#6b4428')])
    Cr = S.Field()
    cz = bz + h * 0.7 + r * 0.75
    Cr.add(*S.Sph((bx, by, cz), r))
    for i in range(6):
        a = i * math.pi / 3 + rng.uniform(0, 0.4)
        Cr.add(*S.Sph((bx + math.cos(a) * r * 0.62, by + math.sin(a) * r * 0.4, cz + rng.uniform(-0.3, 0.4) * r),
                      r * rng.uniform(0.5, 0.62)), k=r * 0.25)
    nz = Noise(seed + 3, 200.0, 7)
    ob, fc = vlak(name + '_kruin', None, color, None, h=0.0009, F=Cr, seed=seed + 1, lump=0.0012,
                  regions=[(lambda V: 0.35 * (0.5 + 0.5 * nz(V)), '#4a8338')], fuzz=1.3)
    for i in range(apples):
        a = rng.uniform(-1.3, 1.3) - math.pi / 2
        z = cz + rng.uniform(-0.5, 0.6) * r
        q, n = surf_hit(fc, (bx + math.cos(a) * 0.2, by + math.sin(a) * 0.2, z), (-math.cos(a), -math.sin(a), 0))
        A = S.Field()
        A.add(*S.Sph(tuple(q + n * 0.0035), 0.0048))
        vlak(f'{name}_appel{i}', None, '#d9443a', None, h=0.0004, F=A, seed=seed + 10 + i)
    return fc


def bush(name, base, r=0.025, color='#4f9a48', berries=0, seed=6):
    rng = np.random.default_rng(seed)
    bx, by, bz = base
    F = S.Field()
    F.add(*S.Ell((bx, by, bz + r * 0.5), (r * 1.3, r, r * 0.8)))
    for i in range(5):
        a = i * 2 * math.pi / 5 + rng.uniform(0, 0.5)
        F.add(*S.Sph((bx + math.cos(a) * r * 0.75, by + math.sin(a) * r * 0.45, bz + r * rng.uniform(0.4, 0.85)),
                     r * rng.uniform(0.5, 0.65)), k=r * 0.3)
    f = lambda P: S.smax(F(P), bz - 0.002 - P[:, 2], 0.002)
    nz = Noise(seed + 3, 220.0, 7)
    lo = (bx - r * 2.2, by - r * 2.2, bz - 0.005)
    hi = (bx + r * 2.2, by + r * 2.2, bz + r * 2.0)
    ob, fb = vlak(name, f, color, None, h=0.0008, lo=lo, hi=hi, seed=seed, lump=0.001,
                  regions=[(lambda V: 0.35 * (0.5 + 0.5 * nz(V)), '#3d7d38')], fuzz=1.3)
    for i in range(berries):
        a = rng.uniform(-1.4, 1.4) - math.pi / 2
        q, n = surf_hit(fb, (bx + math.cos(a) * 0.2, by + math.sin(a) * 0.2, bz + r * rng.uniform(0.3, 1.1)),
                        (-math.cos(a), -math.sin(a), 0))
        A = S.Field()
        A.add(*S.Sph(tuple(q + n * 0.002), 0.0028))
        vlak(f'{name}_bes{i}', None, '#e2425b', None, h=0.00035, F=A, seed=seed + 20 + i)
    return fb


def flowers(name, fground, region, n, seed=7, colors=('#f27c9b', '#ffd34d', '#ffffff', '#b47ae0', '#ff9a52')):
    """Bloemetjes: een gevilt balletje met vijf bolletjes eromheen op een groen steeltje van wol."""
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = region
    F = S.Field()
    stems = []
    cols = []
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        z = height_at(fground, x, y)
        hh = rng.uniform(0.008, 0.016)
        top = np.array([x, y, z + hh])
        cols.append((top, rng.integers(len(colors))))
        stems.append([np.array([x, y, z - 0.001]) + np.array([0, 0, hh]) * t for t in np.linspace(0, 1, 4)])
    plukwol(name + '_steel', np.array(stems), 0.0004, '#4f8a35', None, per=6, radius=0.00006, seed=seed,
            spread_tip=1.0, jitter=0.05)
    for i, (top, ci) in enumerate(cols):
        Fi = S.Field()
        r = rng.uniform(0.0022, 0.003)
        for k in range(5):
            a = k * 2 * math.pi / 5
            Fi.add(*S.Sph(tuple(top + np.array([math.cos(a) * r * 1.05, math.sin(a) * r * 1.05, 0])), r * 0.75),
                   k=0.0004)
        vlak(f'{name}{i}_blad', None, colors[ci], None, h=0.00028, F=Fi, seed=seed + i, lump=0.00015)
        Fc = S.Field()
        Fc.add(*S.Sph(tuple(top + np.array([0, 0, 0.0009])), r * 0.6))
        vlak(f'{name}{i}_hart', None, '#f5c242', None, h=0.00025, F=Fc, seed=seed + 50 + i, lump=0.0001)


# ------------------------------------------------------------------ bouwstenen
from .wol import wool_mat, bead_mat, plain_mat, rrect_poly, poly_dist, star_poly as _star


def box(name, center, half, r=0.004, color='#cccccc', regions=(), parent=None, h=0.0012, seed=1, lump=0.0005,
        fuzz=1.0, rot=None):
    F = S.Field()
    F.add(*S.Box(tuple(center), tuple(np.array(half) - r), r, rot))
    ob, f = vlak(name, None, color, parent, h=h, F=F, regions=list(regions), seed=seed, lump=lump, fuzz=fuzz)
    return ob, f


def front_rect(cx, cz, w, hh, y, depth=0.006):
    """Afstand tot een rechthoek op een voorvlak (vlak y = y, kijkend naar -y)."""
    return lambda V: np.where(np.abs(V[:, 1] - y) < depth,
                              np.maximum(np.abs(V[:, 0] - cx) - w / 2, np.abs(V[:, 2] - cz) - hh / 2), 1.0)


def front_poly(cx, cz, poly, y, depth=0.006):
    poly = np.asarray(poly, float)
    return lambda V: np.where(np.abs(V[:, 1] - y) < depth,
                              poly_dist(np.stack([V[:, 0] - cx, V[:, 2] - cz], 1), poly), 1.0)


def instances(name, locs, sizes, cols, parent=None, n=2.2, res=(12, 6), rotz=None, fuzz=1.0):
    """Veel balletjes/blokjes wol als één mesh (keitjes, kruimels, confetti)."""
    D, Fc = K.sph(*res)
    P = K.superdir(D, n)
    tris = []
    for f in Fc:
        tris += [f] if len(f) == 3 else [(f[0], f[1], f[2]), (f[0], f[2], f[3])]
    T = np.array(tris)
    locs = np.asarray(locs, float)
    sizes = np.broadcast_to(np.asarray(sizes, float), locs.shape)
    m = len(locs)
    V = P[None] * sizes[:, None, :]
    if rotz is not None:
        cz, sz = np.cos(rotz)[:, None], np.sin(rotz)[:, None]
        x, y = V[..., 0].copy(), V[..., 1].copy()
        V[..., 0], V[..., 1] = x * cz - y * sz, x * sz + y * cz
    V = V + locs[:, None, :]
    F = T[None] + (np.arange(m) * len(P))[:, None, None]
    C = np.repeat(np.asarray(cols, float)[:, None, :], len(P), 1)
    ob = K.mesh_obj(name, V.reshape(-1, 3), F.reshape(-1, 3), wool_mat(), parent,
                    attrs={'col': ('POINT', C.reshape(-1, 3).astype(F32))})
    ob['fuzz'] = fuzz
    return ob


def window_regions(cx, cz, w, hh, y, night=False, cross=True):
    pane = '#ffd98a' if night else '#bfe3f5'
    regs = [(edge(front_rect(cx, cz, w + 0.004, hh + 0.004, y), 0.0002, 201), '#fbf7ef'),
            (edge(front_rect(cx, cz, w, hh, y), 0.0002, 202), pane)]
    if cross:
        regs.append((edge(front_rect(cx, cz, 0.0014, hh, y), 0.00012, 203), '#fbf7ef'))
        regs.append((edge(front_rect(cx, cz, w, 0.0014, y), 0.00012, 204), '#fbf7ef'))
    return regs



def prism(name, poly, cx, cz, yf, thick, color, parent=None, h=0.00045, seed=1, round_=0.0008, fuzz=0.8, lump=0.0002):
    """Opgezet viltvormpje: 2D-omtrek (x, z) als plaatje van dikte thick vóór het vlak y = yf."""
    poly = np.asarray(poly, float)

    def f(P):
        d2 = poly_dist(np.stack([P[:, 0] - cx, P[:, 2] - cz], 1), poly)
        dy = np.abs(P[:, 1] - (yf - thick / 2)) - thick / 2
        return (np.minimum(np.maximum(d2, dy), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dy, 0) ** 2)
                ).astype(F32) - round_
    ext = np.abs(poly).max() + 0.004
    return vlak(name, f, color, parent, h=h, lo=(cx - ext, yf - thick - 0.003, cz - ext),
                hi=(cx + ext, yf + 0.002, cz + ext), seed=seed, lump=lump, fuzz=fuzz)


def felt_window(name, cx, cz, w, hh, yf, night=False, cross=True, frame='#fbf7ef'):
    pane = '#ffd98a' if night else '#bfe3f5'
    prism(name + '_ruit', rrect_poly(w, hh, 0.003), cx, cz, yf, 0.0012, pane, seed=5, fuzz=0.4)
    ring = np.concatenate([rrect_poly(w + 0.007, hh + 0.007, 0.004)])
    fo = rrect_poly(w + 0.007, hh + 0.007, 0.004)
    fi = rrect_poly(w, hh, 0.003)

    def f(P):
        q = np.stack([P[:, 0] - cx, P[:, 2] - cz], 1)
        d2 = np.maximum(poly_dist(q, fo), -poly_dist(q, fi))
        dy = np.abs(P[:, 1] - (yf - 0.0012 - 0.0011)) - 0.0011
        return (np.minimum(np.maximum(d2, dy), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dy, 0) ** 2)
                ).astype(F32) - 0.0006
    ext = max(w, hh) / 2 + 0.008
    vlak(name + '_kozijn', f, frame, None, h=0.00045, lo=(cx - ext, yf - 0.006, cz - ext), hi=(cx + ext, yf + 0.002, cz + ext),
         seed=6, lump=0.00015, fuzz=0.7)
    if cross:
        prism(name + '_roede1', rrect_poly(0.0018, hh, 0.0008), cx, cz, yf - 0.0012, 0.0016, frame, seed=7, fuzz=0.5)
        prism(name + '_roede2', rrect_poly(w, 0.0018, 0.0008), cx, cz, yf - 0.0012, 0.0016, frame, seed=8, fuzz=0.5)
    prism(name + '_bank', rrect_poly(w + 0.012, 0.004, 0.0015), cx, cz - hh / 2 - 0.005, yf, 0.006, frame, seed=9)
    if night:
        lt = K.light('POINT', (cx, yf + 0.01, cz), None, energy=0.05, size=0.01, color=(1.0, 0.8, 0.5))


def felt_door(name, cx, yf, color, w=0.026, hh=0.045):
    arch = [(w / 2 * math.cos(t), hh - w / 2 + w / 2 * math.sin(t)) for t in np.linspace(0, math.pi, 12)]
    poly = np.array([(w / 2, 0.0)] + arch + [(-w / 2, 0.0)])
    poly[:, 1] -= hh / 2
    ob, f = prism(name, poly, cx, hh / 2 + 0.001, yf, 0.0025, color, seed=10, h=0.0005)
    bead(name + '_klink', f, (cx + w * 0.32, yf - 0.05, hh * 0.48), 0.0016, '#d9a93a')
    return f


def house(name, x, w=0.14, hh=0.15, y=0.1, d=0.08, color='#e9b44c', roof='#8a3d2e', door='#2f6b8f', seed=0,
          night=False, windows=2, ground_window=True, door_x=None):
    """Huisje van vilt: zacht blok met opgezette raampjes en een deurtje, een puntdak van wol."""
    yf = y
    ob, f = box(name, (x, yf + d / 2, hh / 2), (w / 2, d / 2, hh / 2), 0.006, color, (), h=0.0016, seed=seed,
                lump=0.0007)
    for i in range(windows):
        cx = x - w / 2 + (i + 0.5) * w / windows
        felt_window(f'{name}_raam{i}', cx, hh * 0.7, 0.028, 0.032, yf, night)
    dx = x + (door_x if door_x is not None else (w * 0.22 if seed % 2 else -w * 0.22))
    felt_door(name + '_deur', dx, yf, door)
    if ground_window:
        felt_window(name + '_raamonder', x - (dx - x), hh * 0.3, 0.03, 0.028, yf, night)
    rh = w * 0.5

    def roof_f(P):
        q = P - np.array([x, yf + d / 2, hh], F32)
        tri = np.maximum(np.abs(q[:, 0]) * (rh / (w / 2 + 0.008)) + q[:, 2] - rh, -q[:, 2])
        return np.maximum(tri, np.abs(q[:, 1]) - d / 2 - 0.006) - 0.002
    nz = Noise(seed + 9, 500.0, 7)
    vlak(name + '_dak', roof_f, roof, None, h=0.0012, lo=(x - w / 2 - 0.02, yf - 0.02, hh - 0.01),
         hi=(x + w / 2 + 0.02, yf + d + 0.02, hh + rh + 0.01), lump=0.0006, seed=seed + 3,
         regions=[(lambda V: 0.3 * (np.sin(V[:, 2] * 2 * math.pi / 0.012 + 3 * nz(V) * 0.2) > 0.6), '#5a2a1e')])
    return f


def bakery(name, x, y=0.1, w=0.18, hh=0.165, d=0.09, night=False):
    """Bakkerij: crème gevel, grote etalage met koekjes, rood-wit gestreepte luifel, uithangbord met koekje."""
    yf = y
    ob, f = box(name, (x, yf + d / 2, hh / 2), (w / 2, d / 2, hh / 2), 0.006, '#f4e4c4', (), h=0.0016, seed=21,
                lump=0.0007)
    felt_window(name + '_etalage', x - 0.025, 0.055, 0.092, 0.052, yf, night, cross=False, frame='#2f5d4a')
    felt_door(name + '_deur', x + 0.055, yf, '#a83b3b', w=0.028, hh=0.052)
    felt_window(name + '_raam1', x - 0.045, hh * 0.8, 0.028, 0.028, yf, night)
    felt_window(name + '_raam2', x + 0.045, hh * 0.8, 0.028, 0.028, yf, night)
    # plankje met koekjes in de etalage
    box(name + '_plank', (x - 0.025, yf - 0.009, 0.034), (0.048, 0.008, 0.0025), 0.0018, '#8a5a36', seed=22)
    for i, xx in enumerate(np.linspace(x - 0.06, x + 0.01, 4)):
        cookie(f'{name}_etalagekoek{i}', (xx, yf - 0.01, 0.0445), r=0.008, rot=(1.25, 0, 0), seed=i)
    # luifel: schuin, rood-wit gestreept, met schulprand
    aw = lambda V: (np.sin((V[:, 0] - x) * 2 * math.pi / 0.03) > 0)
    F = S.Field()
    F.add(*S.Box((x, yf - 0.022, hh * 0.62), (w / 2 + 0.004, 0.024, 0.002), 0.002, S.rot(-0.4, 0, 0)))
    for i in range(int(w / 0.015) + 1):
        xx = x - w / 2 + i * 0.015
        F.add(*S.Sph((xx, yf - 0.044, hh * 0.62 - 0.01), 0.0075), k=0.002)
    vlak(name + '_luifel', None, '#fbf7ef', None, h=0.0007, F=F, regions=[(aw, '#d9443a')], seed=23, lump=0.0003)
    # uithangbord met een groot koekje
    S2 = S.Field()
    S2.add(*S.Box((x + 0.105, yf - 0.012, hh * 0.78), (0.022, 0.003, 0.022), 0.003))
    vlak(name + '_bord', None, '#5b3b2a', None, h=0.0006, F=S2, seed=24)
    cookie(name + '_bordkoek', (x + 0.105, yf - 0.016, hh * 0.78), r=0.016, rot=(math.pi / 2, 0, 0), seed=9)
    K.curve_tube(name + '_ophang', [(x + 0.09, yf - 0.012, hh * 0.78 + 0.02), (x + 0.09, yf - 0.012, hh * 0.9)],
                 0.0008, plain_mat('Touwtje', '#d9cfae', rough=0.8))
    rh = w * 0.42

    def roof(P):
        q = P - np.array([x, yf + d / 2, hh], F32)
        tri = np.maximum(np.abs(q[:, 0]) * (rh / (w / 2 + 0.008)) + q[:, 2] - rh, -q[:, 2])
        return np.maximum(tri, np.abs(q[:, 1]) - d / 2 - 0.006) - 0.002
    vlak(name + '_dak', roof, '#8a3d2e', None, h=0.0012, lo=(x - w / 2 - 0.02, yf - 0.02, hh - 0.01),
         hi=(x + w / 2 + 0.02, yf + d + 0.02, hh + rh + 0.01), lump=0.0006, seed=25)
    return f


def cobbles(name, x0, x1, y0, y1, size=(0.0085, 0.0062, 0.0035), colors=('#8b8a86', '#9b9892', '#7d7c79', '#a29c91'),
            seed=2, base='#5c5b58'):
    rng = np.random.default_rng(seed)
    w, d, h = size
    locs, cols, sz = [], [], []
    row = 0
    yy = y0 + d
    while yy < y1:
        xx = x0 + (w if row % 2 else 0.0)
        while xx < x1:
            locs.append((xx + rng.normal(0, 0.0005), yy + rng.normal(0, 0.0004), h * 0.3))
            cols.append(c(colors[rng.integers(len(colors))]) * rng.uniform(0.92, 1.08))
            sz.append((w * rng.uniform(0.85, 0.95), d * rng.uniform(0.82, 0.94), h * rng.uniform(0.85, 1.1)))
            xx += 2 * w
        yy += 2 * d
        row += 1
    box(name + '_voeg', ((x0 + x1) / 2, (y0 + y1) / 2, -0.003), ((x1 - x0) / 2, (y1 - y0) / 2, 0.003), 0.002, base,
        h=0.002, seed=seed, lump=0.0002)
    return instances(name, locs, sz, cols, n=3.0, res=(12, 6), rotz=rng.normal(0, 0.05, len(locs)))


def street(x0=-0.45, x1=0.45, bakery_x=0.0, night=False, y_house=0.09, seed=1, trees=True, sky_y=0.3):
    """Straatje: keitjes, stoep, huisjes en bakkerij, met luchtdoek en wolken erachter."""
    sky(y=sky_y, width=x1 - x0 + 0.5, height=0.45, x0=(x0 + x1) / 2, night=night)
    if not night:
        cloud('Wolk1', ((x0 + x1) / 2 - 0.2, sky_y - 0.03, 0.3), 0.05, seed=seed)
        cloud('Wolk2', ((x0 + x1) / 2 + 0.15, sky_y - 0.03, 0.34), 0.04, seed=seed + 1)
    cobbles('Weg', x0, x1, -0.16, 0.035, seed=seed)
    cobbles('Stoep', x0, x1, 0.04, y_house + 0.004, size=(0.012, 0.012, 0.0025), seed=seed + 1,
            colors=('#ddd5c7', '#d2cabb', '#e4ddd0'), base='#b8b0a2')
    box('Stoeprand', ((x0 + x1) / 2, 0.038, 0.002), ((x1 - x0) / 2, 0.004, 0.004), 0.002, '#c4bcb0', h=0.0015)
    xs = []
    palette = [('#e9b44c', '#8a3d2e', '#2f6b8f'), ('#8fb8a8', '#4b5d7a', '#a83b3b'), ('#e88a7d', '#6b4a3a', '#4f7a3a'),
               ('#9fb3d9', '#8a3d2e', '#7a4f8f'), ('#c8553d', '#4b5d7a', '#2f6b8f')]
    i = 0
    if bakery_x is not None:
        bakery('Bakkerij', bakery_x, y=y_house, night=night)
        left, right = bakery_x - 0.095, bakery_x + 0.095
    else:
        left = right = (x0 + x1) / 2
    xx = left
    while xx > x0 - 0.1:
        w = 0.13 + 0.02 * (i % 2)
        col, rf, dr = palette[i % len(palette)]
        house(f'Huis{i}', xx - w / 2, w, 0.13 + 0.02 * (i % 3), y=y_house, color=col, roof=rf, door=dr, seed=i,
              night=night)
        xx -= w + 0.006
        i += 1
    xx = right
    while xx < x1 + 0.1:
        w = 0.13 + 0.02 * (i % 2)
        col, rf, dr = palette[i % len(palette)]
        house(f'Huis{i}', xx + w / 2, w, 0.13 + 0.02 * (i % 3), y=y_house, color=col, roof=rf, door=dr, seed=i,
              night=night)
        xx += w + 0.006
        i += 1


def park(x0=-0.45, x1=0.45, sky_y=0.28, night=False, seed=3, trees=None, bushes=None, path=True, tufts_n=900,
         flowers_n=26):
    sky(y=sky_y, width=x1 - x0 + 0.5, height=0.45, x0=(x0 + x1) / 2, night=night)
    cloud('Wolk1', ((x0 + x1) / 2 - 0.18, sky_y - 0.04, 0.27), 0.05, seed=seed)
    cloud('Wolk2', ((x0 + x1) / 2 + 0.2, sky_y - 0.04, 0.31), 0.04, seed=seed + 1)
    sun('Zon', ((x0 + x1) / 2 + 0.3, sky_y - 0.02, 0.33), 0.03)
    patches = []
    if path:
        patches.append((lambda V: smooth(0.004, -0.004, np.abs(V[:, 1] + 0.06 + 0.03 * np.sin(V[:, 0] * 9)) - 0.022),
                        '#d8c49a'))
    g, fg = ground(x0=x0, x1=x1, y0=-0.2, y1=sky_y - 0.01, color='#7fae4a', seed=seed, patches=patches,
                   hills=[(-0.25, 0.16, 0.18, 0.09, 0.05), (0.26, 0.17, 0.2, 0.1, 0.06), (0.0, 0.2, 0.12, 0.06, 0.03)])
    for i, (tx, ty, th, tr) in enumerate(trees if trees is not None else
                                         [(-0.2, 0.12, 0.12, 0.036), (0.22, 0.15, 0.1, 0.03)]):
        lolly_tree(f'Boom{i}', (tx, ty, height_at(fg, tx, ty)), h=th, r=tr, apples=5 if i == 0 else 0, seed=5 + i)
    for i, (bx, by, br) in enumerate(bushes if bushes is not None else [(0.12, 0.08, 0.022), (-0.1, 0.1, 0.02)]):
        bush(f'Struik{i}', (bx, by, height_at(fg, bx, by)), br, berries=5, seed=20 + i)
    tufts('Gras', fg, (x0 * 0.7, x1 * 0.7, -0.16, 0.14), tufts_n, seed=seed,
          mask=(lambda x, y: abs(y + 0.06 + 0.03 * math.sin(x * 9)) > 0.026) if path else None)
    flowers('Bloem', fg, (x0 * 0.6, x1 * 0.6, -0.04, 0.12), flowers_n, seed=seed + 1)
    return fg


# ------------------------------------------------------------------ rekwisieten
def cookie(name, loc, r=0.008, rot=(0, 0, 0), seed=0, bite=False, parent=None):
    rng = np.random.default_rng(seed)
    root = K.empty(name, loc, rot, 1.0, parent)
    F = S.Field()
    F.add(*S.Ell((0, 0, 0), (r, r, r * 0.3)))
    if bite:
        F.cut(*S.Sph((r * 0.95, r * 0.3, 0), r * 0.38), k=r * 0.08)
    chips = []
    for i in range(6):
        a = rng.uniform(0, 2 * math.pi)
        dd = rng.uniform(0, 0.68) * r
        chips.append((math.cos(a) * dd, math.sin(a) * dd))
    regs = [(edge(lambda V, cx=cx, cy=cy: np.where(V[:, 2] > 0, np.hypot(V[:, 0] - cx, V[:, 1] - cy) - r * 0.12, 1.0),
                  r * 0.03, 300 + i), '#4a2a17') for i, (cx, cy) in enumerate(chips)]
    regs.append((lambda V: 0.35 * smooth(r * 0.7, r * 1.0, np.hypot(V[:, 0], V[:, 1])), '#a8642a'))
    vlak(name + '_deeg', None, '#d9a35e', root, h=max(r / 28, 0.00018), F=F, regions=regs, seed=seed, lump=r * 0.03)
    return root


def crumbs(name, pts, size=0.0013, seed=1):
    rng = np.random.default_rng(seed)
    pts = np.asarray(pts, float)
    sz = np.stack([size * rng.uniform(0.6, 1.3, len(pts))] * 2 + [size * rng.uniform(0.5, 0.8, len(pts))], 1)
    cols = [c(['#b8742f', '#c98a40', '#a5652a'][i % 3]) * rng.uniform(0.9, 1.1) for i in range(len(pts))]
    return instances(name, pts, sz, cols, n=2.2, res=(8, 5))


def plate(name, loc, r=0.018, parent=None):
    F = S.Field()
    F.add(*S.Ell(tuple(loc), (r, r, 0.0022)))
    return vlak(name, None, '#fbf7ef', parent, h=0.0004, F=F, seed=31, lump=0.0002)


def sack(name, loc, size=0.035, cookies=4, seed=3, rot=(0, 0, 0)):
    root = K.empty(name, loc, rot, 1.0)
    F = S.Field()
    F.add(*S.Ell((0, 0, size * 0.55), (size * 0.62, size * 0.55, size * 0.58)))
    F.add(*S.Cone((0, 0, size * 0.92), (0, 0, size * 1.12), size * 0.18, size * 0.24), k=size * 0.12)
    f = lambda P: S.smax(F(P), -P[:, 2], size * 0.03)
    nz = Noise(seed, 400.0, 7)
    vlak(name + '_zak', f, '#b48c58', root, h=size / 70, lo=(-size, -size, -0.002), hi=(size, size, size * 1.3),
         lump=size * 0.02, seed=seed, regions=[(lambda V: 0.3 * (0.5 + 0.5 * nz(V)), '#8f6a3e')])
    K.curve_tube(name + '_touw', [(size * 0.2 * math.cos(t), size * 0.2 * math.sin(t), size * 0.98)
                                  for t in np.linspace(0, 2 * math.pi, 24)], size * 0.025,
                 plain_mat('Touw', '#e8d8a8', rough=0.8), root)
    for i in range(cookies):
        a = i * 2 * math.pi / max(cookies, 1)
        cookie(f'{name}_koek{i}', (math.cos(a) * size * 0.1, math.sin(a) * size * 0.1, size * 1.16), r=size * 0.2,
               rot=(0.6 * math.cos(a), 0.6 * math.sin(a), 0), seed=i, parent=root)
    return root


def magnifier(name, loc, rot=(0, 0, 0), r=0.008, parent=None):
    root = K.empty(name, loc, rot, 1.0, parent)
    F = S.Field()
    F.add(*S.Tor((0, 0, 0), r, r * 0.17, S.rot(math.pi / 2, 0, 0)))
    vlak(name + '_ring', None, '#e8b33c', root, h=0.00022, F=F, seed=41)
    K.blob(name + '_lens', (r * 0.95, r * 0.1, r * 0.95), 2.0, (32, 12),
           mat=plain_mat('Lensglas', '#ffffff', rough=0.0, trans=1.0), parent=root)
    H = S.Field()
    H.add(*S.Cap((0, 0, -r * 1.15), (0, 0, -r * 3.0), r * 0.18))
    vlak(name + '_steel', None, '#c63b33', root, h=0.00022, F=H, seed=42)
    return root


def medal(name, loc, r=0.0045, parent=None, rot=(0, 0, 0)):
    root = K.empty(name, loc, rot, 1.0, parent)
    F = S.Field()
    F.add(*S.Ell((0, 0, -r * 0.9), (r, r * 0.25, r)))
    vlak(name + '_munt', None, '#f0bd3c', root, h=0.00018, F=F, seed=51,
         regions=[(edge(lambda V: np.where(V[:, 1] < 0, poly_dist(np.stack([V[:, 0], V[:, 2] + r * 0.9], 1),
                                                                  _star(r * 0.6, r * 0.26)), 1.0), 0.0001, 52),
                   '#fff0a8')])
    L = S.Field()
    L.add(*S.Box((0, 0.0004, r * 0.6), (r * 0.35, r * 0.08, r * 0.7), r * 0.05))
    vlak(name + '_lint', None, '#3a6fd1', root, h=0.00018, F=L, seed=53)
    return root


def confetti(name, n, region, seed=4, size=0.0028):
    rng = np.random.default_rng(seed)
    (x0, y0, z0), (x1, y1, z1) = region
    locs = np.stack([rng.uniform(x0, x1, n), rng.uniform(y0, y1, n), rng.uniform(z0, z1, n)], 1)
    cols = [c(h) for h in rng.choice(['#d9443a', '#ffd34d', '#4f9ad9', '#7ab648', '#f27c9b', '#b47ae0'], n)]
    return instances(name, locs, (size, size, size * 0.2), cols, n=2.0, res=(10, 5), rotz=rng.uniform(0, 6.28, n))


def crate(name, loc, size=(0.06, 0.04, 0.03)):
    x, y, z = loc
    w, d, hh = size
    regs = [(lambda V, zz=zz: smooth(0.0004, 0.0, np.abs(V[:, 2] - zz) - 0.0006) * (V[:, 1] < y - d / 2 + 0.002),
             '#6b4428') for zz in (z + hh * 0.35, z + hh * 0.68)]
    return box(name, (x, y, z + hh / 2), (w / 2, d / 2, hh / 2), 0.003, '#c08a58', regs, h=0.0007, seed=61)


def table(name, loc, size=(0.14, 0.07, 0.045)):
    x, y, z = loc
    w, d, hh = size
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(f'{name}_poot{sx}{sy}', (x + sx * (w / 2 - 0.008), y + sy * (d / 2 - 0.008), z + hh / 2),
                (0.0035, 0.0035, hh / 2), 0.0015, '#8a5a36', h=0.0006, seed=70)
    chk = lambda V: ((np.sin((V[:, 0] - x) * 2 * math.pi / 0.02) > 0) ^ (np.sin((V[:, 1] + V[:, 2]) * 2 * math.pi / 0.02) > 0))
    return box(name + '_kleed', (x, y, z + hh - 0.004), (w / 2 + 0.006, d / 2 + 0.006, 0.006), 0.004, '#fbf7ef',
               [(chk, '#d9443a')], h=0.0007, seed=71)


def bunting(name, a, b, n=10, sag=0.03, colors=('#d9443a', '#ffd34d', '#4f9ad9', '#7ab648', '#f27c9b')):
    a, b = np.asarray(a, float), np.asarray(b, float)
    t = np.linspace(0, 1, 30)
    P = a[None] * (1 - t[:, None]) + b[None] * t[:, None]
    P[:, 2] -= sag * 4 * t * (1 - t)
    K.curve_tube(name + '_koord', [tuple(p) for p in P], 0.0007, plain_mat('Koord', '#f3ead8', rough=0.8))
    for i in range(n):
        u = (i + 0.5) / n
        p = a * (1 - u) + b * u
        p[2] -= sag * 4 * u * (1 - u)
        F = S.Field()
        tri = lambda P, p=p: np.maximum(np.maximum(np.abs(P[:, 0] - p[0]) * 2.2 + (p[2] - P[:, 2]) - 0.024,
                                                   P[:, 2] - p[2]), np.abs(P[:, 1] - p[1]) - 0.0012)
        vlak(f'{name}_vlag{i}', tri, colors[i % len(colors)], None, h=0.0005, lo=p - np.array([0.015, 0.004, 0.028]),
             hi=p + np.array([0.015, 0.004, 0.003]), lump=0.0002, seed=80 + i)


def police_car(name, loc, yaw=0.0, lights=True):
    """Open politieautootje van vilt (lengte ca. 20 cm): wit met blauwe band, wieltjes met knoopjes,
    beugel met blauw zwaailicht. Kijkt naar -y."""
    root = K.empty(name, loc, (0, 0, yaw), 1.0)
    F = S.Field()
    F.add(*S.Box((0, 0, 0.042), (0.052, 0.088, 0.02), 0.014))
    F.add(*S.Ell((0, -0.06, 0.046), (0.05, 0.04, 0.022)), k=0.01)
    F.cut(*S.Box((0, 0.018, 0.065), (0.04, 0.044, 0.03), 0.01), k=0.004)
    band = lambda V: smooth(0.0004, -0.0004, np.abs(V[:, 2] - 0.04) - 0.006)
    oranje = lambda V: smooth(0.0003, -0.0003, np.abs(V[:, 2] - 0.0478) - 0.0016)
    ob, fc = vlak(name + '_carrosserie', None, '#f7f6f2', root, h=0.0007, F=F, seed=91, lump=0.0005,
                  regions=[(band, '#2f5fc4'), (oranje, '#f08a1c')], fuzz=0.35)
    box(name + '_stoel', (0, 0.04, 0.05), (0.034, 0.014, 0.012), 0.004, '#2a3550', parent=root, h=0.0007, seed=92)
    box(name + '_leuning', (0, 0.054, 0.072), (0.034, 0.007, 0.024), 0.004, '#2a3550', parent=root, h=0.0007, seed=93)
    Sw = S.Field()
    Sw.add(*S.Tor((-0.014, 0.012, 0.075), 0.011, 0.0022, S.rot(math.radians(60), 0, 0)))
    vlak(name + '_stuur', None, '#202024', root, h=0.0003, F=Sw, seed=94)
    for sx in (-1, 1):
        for sy in (-0.058, 0.062):
            Wf = S.Field()
            Wf.add(*S.Tor((sx * 0.062, sy, 0.02), 0.013, 0.0075, S.rot(0, math.pi / 2, 0)))
            vlak(f'{name}_wiel{sx}{sy}', None, '#202024', root, h=0.0006, F=Wf, seed=95, fuzz=1.2)
            K.blob(f'{name}_naaf{sx}{sy}', (0.009, 0.009, 0.0025), 2.4, (20, 8),
                   mat=bead_mat('#e8eaee'), parent=root, loc=(sx * 0.0705, sy, 0.02), rot=(0, math.pi / 2, 0))
            for k in range(4):
                a = k * math.pi / 2 + math.pi / 4
                K.blob(f'{name}_gaatje{sx}{sy}{k}', (0.0015, 0.0015, 0.001), 2.0, (8, 6), mat=bead_mat('#202024'),
                       parent=root, loc=(sx * 0.0728, sy + math.cos(a) * 0.003, 0.02 + math.sin(a) * 0.003),
                       rot=(0, math.pi / 2, 0))
    for sx in (-1, 1):
        L1 = S.Field()
        L1.add(*S.Sph((sx * 0.03, -0.103, 0.046), 0.0065))
        vlak(f'{name}_koplamp{sx}', None, '#ffe48a', root, h=0.0003, F=L1, seed=96)
    Rb = S.Field()
    Rb.add(*S.Chain([(-0.036, 0.075, 0.05), (-0.034, 0.075, 0.105), (0.0, 0.075, 0.113), (0.034, 0.075, 0.105),
                     (0.036, 0.075, 0.05)], [0.0032] * 5))
    vlak(name + '_beugel', None, '#2f5fc4', root, h=0.0005, F=Rb, seed=97)
    K.blob(name + '_zwaailicht', (0.008, 0.006, 0.007), 2.0, (16, 10),
           mat=plain_mat('Zwaailicht', '#4aa3ff', emit=9.0 if lights else 0.6), parent=root, loc=(0, 0.075, 0.121))
    if lights:
        lt = K.light('POINT', (0, 0.075, 0.128), None, energy=0.25, size=0.006, color=(0.3, 0.6, 1.0))
        lt.parent = root
        lt.location = (0, 0.075, 0.128)
    return root, fc


def bedroom(night=False, bed_x=-0.06, bed_y=0.08, sleeper=False, window_x=0.08):
    """Slaapkamer-maquette: achterwand met sterretjes en raam, vloer, rond kleedje, bed met lappendeken."""
    wall = '#cfe4f2' if not night else '#7a8fbe'
    box('Achterwand', (0, 0.165, 0.14), (0.32, 0.01, 0.14), 0.004, wall, (), h=0.002, seed=401)
    rng = np.random.default_rng(5)
    for i in range(22):
        x, z = rng.uniform(-0.28, 0.28), rng.uniform(0.03, 0.26)
        if abs(x - window_x) < 0.07 and 0.07 < z < 0.22:
            continue
        prism(f'Behangster{i}', _star(0.006, 0.0026, rot=90 + rng.uniform(-20, 20)), x, z, 0.155, 0.0012,
              '#f4d36b' if not night else '#ffe9a0', seed=400 + i, h=0.0004, fuzz=0.6)
    felt_window('Raam', window_x, 0.145, 0.075, 0.08, 0.155, night=False, frame='#fbf7ef')
    if night:
        prism('Raamlucht', rrect_poly(0.075, 0.08, 0.003), window_x, 0.145, 0.1538, 0.0008, '#1c2856', seed=431,
              fuzz=0.3)
        prism('Raammaan', circle_poly(0.011, 32), window_x + 0.018, 0.16, 0.153, 0.0012, '#f7e6a3', seed=432)
        for i in range(5):
            prism(f'Raamster{i}', _star(0.003, 0.0013), window_x + rng.uniform(-0.03, 0.01),
                  0.145 + rng.uniform(-0.03, 0.03), 0.153, 0.0008, '#ffe17a', seed=433 + i, h=0.0003)
    box('Vloer', (0, 0.0, -0.004), (0.32, 0.17, 0.004), 0.002, '#cf9f6f', h=0.002, seed=402,
        regions=[(lambda V: 0.25 * (np.sin(V[:, 0] * 2 * math.pi / 0.03) > 0.92), '#a8744a')])
    rings = [(0.07, '#7ab3d9'), (0.054, '#f4d36b'), (0.038, '#f2a7b6'), (0.022, '#7ab648')]
    F = S.Field()
    F.add(*S.Ell((-0.02, -0.04, 0.0006), (0.075, 0.058, 0.0016)))
    rugregs = [(lambda V, r=r: smooth(0.0008, -0.0008, np.hypot((V[:, 0] + 0.02), (V[:, 1] + 0.04) * 1.29) - r), cc)
               for r, cc in rings]
    vlak('Kleed', None, rings[0][1], None, h=0.0006, F=F, regions=rugregs[1:], seed=403)
    # gordijntjes
    for s in (-1, 1):
        G = S.Field()
        for k in range(3):
            xx = window_x + s * (0.052 + k * 0.007)
            G.add(*S.Cap((xx, 0.148, 0.09), (xx, 0.148, 0.205), 0.0055), k=0.004)
        vlak(f'Gordijn{s}', None, '#f2a7b6', None, h=0.0006, F=G, seed=404 + s)
    # bed
    bx, by = bed_x, bed_y
    box('Hoofdeind', (bx, by + 0.055, 0.05), (0.045, 0.006, 0.05), 0.005, '#b98652', h=0.0008, seed=410)
    box('Voeteind', (bx, by - 0.066, 0.022), (0.045, 0.008, 0.022), 0.006, '#b98652', h=0.0008, seed=411)
    box('Bedbak', (bx, by - 0.005, 0.02), (0.043, 0.058, 0.012), 0.004, '#b98652', h=0.0008, seed=412)
    box('Matras', (bx, by - 0.005, 0.036), (0.041, 0.056, 0.007), 0.004, '#fbf7ef', h=0.0008, seed=413)
    P = S.Field()
    P.add(*S.Ell((bx, by + 0.04, 0.046), (0.028, 0.012, 0.007)))
    vlak('Kussen', None, '#fbf7ef', None, h=0.0005, F=P, seed=414)
    cols = ['#7ab3d9', '#f4d36b', '#f2a7b6', '#7ab648', '#fbf7ef', '#b47ae0']

    def quilt_col(V):
        i = np.floor((V[:, 0] - bx + 0.05) / 0.021).astype(int)
        j = np.floor((V[:, 1] - by + 0.07) / 0.019).astype(int)
        idx = (i + 2 * j) % len(cols)
        out = np.stack([c(cols[k]) for k in range(len(cols))])[idx]
        seam = (np.abs(((V[:, 0] - bx + 0.05) / 0.021) % 1 - 0.5) > 0.46) | \
               (np.abs(((V[:, 1] - by + 0.07) / 0.019) % 1 - 0.5) > 0.45)
        out[seam] *= 0.8
        return out
    Q = S.Field()
    zq = 0.044
    bump = (lambda P: F32(0.016) * np.exp(-((P[:, 0] - bx) / 0.022) ** 2).astype(F32) *
            (P[:, 1] < by + 0.02)) if sleeper else (lambda P: F32(0.0))
    qf = lambda P: S.rbox(P, (bx, by - 0.012, zq), (0.042, 0.046, 0.003), 0.003) - bump(P)
    vlak('Deken', qf, quilt_col, None, h=0.0006, lo=(bx - 0.06, by - 0.08, zq - 0.01), hi=(bx + 0.06, by + 0.05, zq + 0.03),
         seed=415, lump=0.0004)
    if night:
        box('Nachtkastje', (bx + 0.075, by + 0.03, 0.022), (0.018, 0.016, 0.022), 0.004, '#d9a874', h=0.0008, seed=416)
        K.blob('Lampkap', (0.012, 0.012, 0.01), 3.0, (24, 12), mat=plain_mat('Nachtlampje', '#ffcf7a', emit=6.0),
               loc=(bx + 0.075, by + 0.03, 0.06))
        lt = K.light('POINT', (bx + 0.075, by + 0.02, 0.06), None, energy=1.2, size=0.01, color=(1.0, 0.78, 0.45))
    else:
        # speelgoed: blokjes en een bal
        for i, cc in enumerate(('#d9443a', '#4f9ad9', '#ffd34d')):
            box(f'Blok{i}', (-0.2 + i * 0.016, 0.12, 0.0075), (0.0075, 0.0075, 0.0075), 0.002, cc, h=0.0005, seed=420 + i)
        B = S.Field()
        B.add(*S.Sph((-0.15, 0.1, 0.012), 0.012))
        vlak('Bal', None, '#f27c9b', None, h=0.0005, F=B, seed=425, regions=[(lambda V: (np.abs(V[:, 2] - 0.012) < 0.0025), '#fbf7ef')])


def shop(empty=True):
    """Bakkerswinkel van vilt: wand met ruitjes, schappen met broden of lege schaaltjes, toonbank."""
    chk = lambda V: ((np.sin(V[:, 0] * 2 * math.pi / 0.03) > 0) ^ (np.sin(V[:, 2] * 2 * math.pi / 0.03) > 0))
    box('Wand', (0, 0.15, 0.14), (0.3, 0.01, 0.14), 0.004, '#f6efe0', [(chk, '#f2d2c4')], h=0.0014, seed=501)
    box('Vloer', (0, 0, -0.004), (0.3, 0.16, 0.004), 0.002, '#c9b08a', h=0.002, seed=502)
    for z in (0.13, 0.18, 0.23):
        box(f'Schap{z}', (0, 0.13, z), (0.16, 0.014, 0.0025), 0.0015, '#9a6a40', h=0.0007, seed=503)
        for i, x in enumerate(np.linspace(-0.13, 0.13, 5)):
            if empty and z < 0.2:
                plate(f'Schaal{z}{i}', (x, 0.128, z + 0.004), r=0.012)
            else:
                B = S.Field()
                B.add(*S.Ell((x, 0.128, z + 0.01), (0.016, 0.009, 0.0075)))
                vlak(f'Brood{z}{i}', None, '#d99a55', None, h=0.0005, F=B, seed=510 + i,
                     regions=[(lambda V, x=x: (np.abs(np.sin((V[:, 0] - x) * 2 * math.pi / 0.008)) > 0.92) *
                               (V[:, 2] > z + 0.014), '#a8642a')])
    stripes = lambda V: (np.sin(V[:, 0] * 2 * math.pi / 0.03) > 0) * (V[:, 1] < 0.03) * (np.abs(V[:, 2] - 0.025) < 0.008)
    box('Toonbank', (0, 0.06, 0.022), (0.14, 0.028, 0.022), 0.004, '#f4e4c4', [(stripes, '#d9443a')], h=0.0009,
        seed=520)
    box('Toonbankblad', (0, 0.06, 0.0465), (0.148, 0.032, 0.0025), 0.0015, '#9a6a40', h=0.0007, seed=521)
    K.blob('Pot', (0.012, 0.012, 0.015), 2.5, (24, 12), mat=plain_mat('Potglas', '#ffffff', rough=0.0, trans=1.0),
           loc=(0.1, 0.06, 0.064))
    D = S.Field()
    D.add(*S.Ell((0.1, 0.06, 0.08), (0.013, 0.013, 0.003)))
    vlak('Potdeksel', None, '#d9443a', None, h=0.0004, F=D, seed=522)
