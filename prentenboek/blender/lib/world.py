"""Omgevingen: klinkers, stoep, gras, bomen, struiken, bloemen, Hollandse gevels, bakkerij, slaapkamer."""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler
from . import core as K, mats as M
from .core import gauss, smoothstep
from .body import nrm

_W = {}


def world_mats():
    if _W:
        return _W
    _W.update({
        'cobble': M.vertex_colored('Klinker', rough=0.8, bump=0.4, bump_scale=55.0),
        'tile': M.vertex_colored('Stoeptegel', rough=0.85, bump=0.25, bump_scale=30.0),
        'sand': M.painted('Voegzand', '#8a7a64', rough=0.95, var=0.1, scale=30, bump=0.2),
        'curb': M.painted('Stoeprand', '#b8b4ac', rough=0.8, var=0.06, scale=8, bump=0.15),
        'grass': M.vertex_colored('Gras', rough=0.55, bump=0.0, sheen=0.3),
        'soil': M.painted('Aarde', '#5d7a32', rough=0.95, var=0.15, scale=6, bump=0.1),
        'leaf': M.leaves('Blad'),
        'leaf_clump': M.painted('Bladmassa', '#3f7a2a', rough=0.7, var=0.15, scale=12, attr='col', bump=0.2),
        'bark': M.bark('Schors'),
        'brick': M.brick('Baksteen', '#a5523a', '#7f3a28', '#d8cfc0', scale=4.8),
        'brick2': M.brick('Baksteen geel', '#c99a5e', '#a77840', '#e2d9c8', scale=4.8),
        'brick3': M.brick('Baksteen donker', '#7b4535', '#5b3024', '#cfc4b3', scale=4.8),
        'frame': M.painted('Kozijn wit', '#f5f3ee', rough=0.35, var=0.02, coat=0.3, bump=0.02),
        'frame_green': M.painted('Kozijn groen', '#1f4d3c', rough=0.35, var=0.03, coat=0.4, bump=0.02),
        'window': M.thin_glass('Raam'),
        'window_dark': M.painted('Raam binnen', '#2b3442', rough=0.15, var=0.05, coat=1.0, bump=0.0),
        'curtain': M.fabric('Gordijn', '#f2e6cf', rough=0.9, sheen=0.6, weave=500),
        'door': M.painted('Deur', '#2d5a8c', rough=0.3, var=0.03, coat=0.6, bump=0.02),
        'door_red': M.painted('Deur rood', '#9c2f2a', rough=0.3, var=0.03, coat=0.6, bump=0.02),
        'roof': M.painted('Dakpan', '#8d3b2c', rough=0.7, var=0.12, scale=20, bump=0.3),
        'awning': M.fabric('Luifel', '#d93b3b', rough=0.75, sheen=0.5, weave=500, stripes=('#fbf6ea', 0.0)),
        'sign': M.painted('Uithangbord', '#1f4d3c', rough=0.35, var=0.03, coat=0.5, bump=0.02),
        'gold_letter': M.gold('Bladgoud', '#e7b54a', 0.2),
        'metal_dark': M.painted('Lantaarnpaal', '#2b3138', rough=0.4, var=0.03, coat=0.4, bump=0.0),
        'lamp_glow': M.emission('Lampgloed', '#ffd9a0', 4.0),
        'wall_room': M.painted('Muur kamer', '#cfe1ee', rough=0.85, var=0.04, scale=3, bump=0.03),
        'floor_wood': M.wood('Vloer', '#c99566', '#a8744a', rough=0.45, scale=4.0, coat=0.2),
        'rug': M.vertex_colored('Kleed', rough=0.95, bump=0.3, bump_scale=200.0, sheen=0.8),
        'duvet': M.fabric('Dekbed', '#f4d26a', rough=0.85, sheen=0.8, weave=600, dots=('#fff8e6', 26.0)),
        'pillow': M.fabric('Kussen', '#fbf8f1', rough=0.85, sheen=0.8, weave=700, var=0.02),
        'bed_wood': M.wood('Bedhout', '#e6c49a', '#c9a074', rough=0.4, coat=0.3),
        'sky_wall': M.emission('Lucht achter raam', '#bfe2f7', 1.0),
        'night_sky': M.emission('Nachtlucht', '#1b2a52', 1.0),
        'moon': M.emission('Maan', '#fff2c4', 8.0),
        'star': M.emission('Ster', '#fff6d8', 12.0),
        'counter': M.painted('Toonbank', '#f2e5cf', rough=0.4, var=0.03, coat=0.3, bump=0.02),
        'tile_wall': M.vertex_colored('Wandtegel', rough=0.15, bump=0.0, coat=1.0),
        'bread': M.cookie('Brood', '#c98a46', '#8a4b1f'),
        'basket': M.burlap('Mand', '#b88a52'),
        'water': M.painted('Plas', '#7f8ea1', rough=0.05, var=0.02, coat=1.0, bump=0.0),
        'flower_w': M.simple('Bloemblad wit', '#fbfaf5', rough=0.5, sss=0.3),
        'flower_y': M.simple('Bloemhart', '#f2b51c', rough=0.6),
        'flower_p': M.simple('Bloemblad roze', '#f28bb5', rough=0.5, sss=0.3),
        'flower_r': M.simple('Bloemblad rood', '#e2392f', rough=0.5, sss=0.3),
        'stem': M.simple('Steel', '#4f8a2e', rough=0.6),
        'bench': M.wood('Bank', '#9a6a3e', '#7a4c28', rough=0.5),
        'fence': M.painted('Hekwerk', '#2f3a33', rough=0.4, var=0.03, coat=0.3, bump=0.0),
    })
    return _W


# ------------------------------------------------------------------ bestrating
def _brick_field(name, rects, size, height, n_exp, colors, parent, jitter=0.004, seed=1, res=(14, 8), mat='cobble'):
    """rects: lijst (cx, cy, rot) per steen. Eén mesh met kleur per steen."""
    m = world_mats()
    rng = np.random.default_rng(seed)
    D, F = K.sph(*res)
    base = K.superdir(D, n_exp) * np.array([size[0] / 2, size[1] / 2, height / 2])
    F4 = np.array([f if len(f) == 4 else (f[0], f[1], f[2], f[2]) for f in F])
    Vs, Fs, Cs = [], [], []
    off = 0
    colors = np.array([K.srgb(c)[:3] for c in colors])
    for (cx, cy, rot) in rects:
        P = base * (1 + rng.normal(0, 0.03, 3))
        a = rot + rng.normal(0, 0.012)
        ca, sa = math.cos(a), math.sin(a)
        R = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])
        tilt = Euler((rng.normal(0, 0.012), rng.normal(0, 0.012), 0)).to_matrix()
        P = P @ (R @ np.array(tilt)).T
        P = P + np.array([cx, cy, height / 2 - 0.004 + rng.normal(0, jitter)])
        Vs.append(P)
        Fs.append(F4 + off)
        off += len(D)
        c = colors[rng.integers(len(colors))] * (0.75 + 0.45 * rng.random())
        Cs.append(np.repeat(c[None, :], len(D), 0))
    V = np.concatenate(Vs)
    Fa = np.concatenate(Fs).tolist()
    Fl = [tuple(f) if f[2] != f[3] else (f[0], f[1], f[2]) for f in Fa]
    return K.mesh_obj(name, V, Fl, m[mat], parent, attrs={'col': ('POINT', np.concatenate(Cs))})


def cobbles(name, x0, x1, y0, y1, parent=None, pattern='keper', seed=1):
    """Rode klinkers. keper = visgraat (90 graden), anders halfsteens."""
    L, Wd, j = 0.2, 0.1, 0.007
    rects = []
    if pattern == 'keper':
        # visgraat (90 graden), 45 graden gedraaid t.o.v. de straat. Rooster (u,u) en (2u,-2u) dekt het vlak.
        u = Wd + j
        cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
        R = max(x1 - x0, y1 - y0) * 0.8
        n = int(R / u) + 4
        c45, s45 = math.cos(math.pi / 4), math.sin(math.pi / 4)
        for i in range(-n, n):
            for k in range(-n // 2 - 2, n // 2 + 2):
                ox, oy = i * u + k * 2 * u, i * u - k * 2 * u
                for (dx, dy, r) in ((u, u / 2, 0.0), (u / 2, 2 * u, math.pi / 2)):
                    px, py = ox + dx, oy + dy
                    qx, qy = cx0 + px * c45 - py * s45, cy0 + px * s45 + py * c45
                    if x0 - 0.12 < qx < x1 + 0.12 and y0 - 0.12 < qy < y1 + 0.12:
                        rects.append((qx, qy, r + math.pi / 4))
    else:
        rows = int((y1 - y0) / (Wd + j)) + 2
        for r_ in range(rows):
            cy = y0 + r_ * (Wd + j) + Wd / 2
            offx = (L + j) / 2 if r_ % 2 else 0
            n = int((x1 - x0) / (L + j)) + 2
            for c in range(n):
                cx = x0 + c * (L + j) + L / 2 - offx
                rects.append((cx, cy, 0.0))
    cols = ['#9a4a35', '#8a3f2f', '#a8584a', '#7b4a44', '#96553f', '#6f4a46', '#a5634a']
    ob = _brick_field(name, rects, (L, Wd), 0.07, 6.0, cols, parent, seed=seed)
    sand = K.blob(name + '_zand', ((x1 - x0) / 2 + 0.2, (y1 - y0) / 2 + 0.2, 0.01), 8, (8, 4),
                  mat=world_mats()['sand'], parent=parent, loc=((x0 + x1) / 2, (y0 + y1) / 2, 0.035))
    return ob


def sidewalk(name, x0, x1, y0, y1, parent=None, seed=2, z=0.12):
    s, j = 0.3, 0.006
    rects = []
    for i in range(int((x1 - x0) / (s + j)) + 1):
        for k in range(int((y1 - y0) / (s + j)) + 1):
            rects.append((x0 + i * (s + j) + s / 2, y0 + k * (s + j) + s / 2, 0.0))
    ob = _brick_field(name, rects, (s, s), 0.05, 8.0, ['#bdb8ae', '#a9a49b', '#c7c2b8', '#b1aca2'], parent,
                      jitter=0.002, seed=seed, res=(16, 8), mat='tile')
    ob.location.z = z - 0.05
    K.blob(name + '_bed', ((x1 - x0) / 2, (y1 - y0) / 2, z / 2), 10, (8, 4), mat=world_mats()['sand'], parent=parent,
           loc=((x0 + x1) / 2, (y0 + y1) / 2, z / 2 - 0.02))
    return ob


def curb(name, x0, x1, y, parent=None, z=0.12):
    return K.blob(name, ((x1 - x0) / 2, 0.07, z / 2 + 0.01), 8, (48, 8), mat=world_mats()['curb'], parent=parent,
                  loc=((x0 + x1) / 2, y, z / 2))


# ------------------------------------------------------------------ gras en bloemen
def grass(name, region, density=2500, height=(0.05, 0.11), parent=None, seed=3, z=0.0, mask=None):
    """Grassprieten als Hair Curves in een rechthoek (x0, x1, y0, y1); mask(x,y)->0..1 optioneel."""
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = region
    n = int((x1 - x0) * (y1 - y0) * density)
    P = np.stack([rng.uniform(x0, x1, n), rng.uniform(y0, y1, n), np.full(n, z)], 1)
    if mask is not None:
        P = P[rng.random(n) < mask(P[:, 0], P[:, 1])]
        n = len(P)
    h = rng.uniform(*height, n)
    lean = rng.normal(0, 0.35, (n, 2))
    k = 5
    t = np.linspace(0, 1, k)[None, :]
    S = np.zeros((n, k, 3))
    S[..., 0] = P[:, 0:1] + lean[:, 0:1] * h[:, None] * t ** 1.6
    S[..., 1] = P[:, 1:2] + lean[:, 1:2] * h[:, None] * t ** 1.6
    S[..., 2] = z + h[:, None] * t * (1 - 0.25 * t * np.abs(lean).sum(1, keepdims=True))
    base = np.array([[0.16, 0.36, 0.07], [0.22, 0.42, 0.08], [0.3, 0.46, 0.1], [0.12, 0.3, 0.06],
                     [0.36, 0.48, 0.12]])
    C = base[rng.integers(len(base), size=n)] * (0.75 + 0.5 * rng.random((n, 1)))
    r = np.linspace(0.0016, 0.0003, k)[None, :].repeat(n, 0)
    m = world_mats()
    mat = m.get('grass_hair')
    if mat is None:
        mat = M.hair_color_mat('Grassprieten', None, rough=0.5, radial=0.4)
        m['grass_hair'] = mat
    return K.hair(name, S, r, mat, parent, col=C)


def ground(name, size, mat, parent=None, loc=(0, 0, 0)):
    return K.blob(name, (size[0] / 2, size[1] / 2, 0.02), 10, (16, 8), mat=mat, parent=parent,
                  loc=(loc[0], loc[1], loc[2] - 0.02))


def flowers(name, region, n, parent=None, seed=7, z=0.0, kinds=('w', 'y', 'p')):
    m = world_mats()
    rng = np.random.default_rng(seed)
    x0, x1, y0, y1 = region
    root = K.empty(name, (0, 0, 0), (0, 0, 0), 1.0, parent)
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        h = rng.uniform(0.08, 0.16)
        kind = kinds[rng.integers(len(kinds))]
        K.tube(name + f'_steel{i}', [(x, y, z), (x + rng.normal(0, 0.01), y + rng.normal(0, 0.01), z + h)],
               [0.0022, 0.0018], m['stem'], root, ring=6, per=2)
        petal = {'w': 'flower_w', 'y': 'flower_y', 'p': 'flower_p', 'r': 'flower_r'}[kind]
        fc = K.empty(name + f'_bloem{i}', (x, y, z + h), (rng.normal(0, 0.3), rng.normal(0, 0.3), rng.random() * 6), 1.0, root)
        for k in range(7):
            a = k / 7 * 2 * math.pi
            K.blob(name + f'_blad{i}_{k}', (0.011, 0.005, 0.0015), 2, (10, 6), mat=m[petal if kind != 'y' else 'flower_y'],
                   parent=fc, loc=(math.cos(a) * 0.011, math.sin(a) * 0.011, 0), rot=(0, 0.15, a))
        K.blob(name + f'_hart{i}', (0.006, 0.006, 0.004), 2, (10, 6), mat=m['flower_y' if kind != 'y' else 'flower_w'],
               parent=fc, loc=(0, 0, 0.002))
    return root


# ------------------------------------------------------------------ bladeren, bomen, struiken
def _leaf_mesh(n, centers, normals, size, rng, colors):
    """n blaadjes (8 hoekpunten, gebogen) op centers met naar buiten wijzende normals."""
    shape = np.array([[0, -1.0, 0], [0.45, -0.45, 0.06], [0.42, 0.25, 0.04], [0, 1.0, 0], [-0.42, 0.25, 0.04],
                      [-0.45, -0.45, 0.06], [0, -0.1, -0.05]])
    tris = [(6, 0, 1), (6, 1, 2), (6, 2, 3), (6, 3, 4), (6, 4, 5), (6, 5, 0)]
    Vs, Fs, Cs = [], [], []
    cols = np.array([K.srgb(c)[:3] for c in colors])
    for i in range(n):
        nn = normals[i] + rng.normal(0, 0.5, 3)
        nn = nn / (np.linalg.norm(nn) + 1e-9)
        t = np.cross(nn, rng.normal(size=3))
        t = t / (np.linalg.norm(t) + 1e-9)
        b = np.cross(nn, t)
        s = size * (0.7 + 0.6 * rng.random())
        loc = shape.copy()
        loc[:, 1] += 1.0
        P = centers[i] + (loc[:, 0:1] * t + loc[:, 1:2] * b * 0.5 + loc[:, 2:3] * nn) * s
        Vs.append(P)
        Fs.extend([(a + i * 7, b_ + i * 7, c + i * 7) for (a, b_, c) in tris])
        c = cols[rng.integers(len(cols))] * (0.8 + 0.4 * rng.random())
        Cs.append(np.repeat(c[None, :], 7, 0))
    return np.concatenate(Vs), Fs, np.concatenate(Cs)


def foliage(name, clumps, parent=None, leaf_size=0.06, density=900, seed=5, colors=None, inner_mat=True):
    """clumps: lijst (centrum, straal). Bolle bladmassa's met losse blaadjes erop."""
    m = world_mats()
    rng = np.random.default_rng(seed)
    colors = colors or ['#3f7d2b', '#4f9233', '#5ea83b', '#2f6a25', '#6db544', '#7fbf4a']
    root = K.empty(name, (0, 0, 0), (0, 0, 0), 1.0, parent)
    allV, allF, allC = [], [], []
    off = 0
    for ci, (c, r) in enumerate(clumps):
        c = np.asarray(c, dtype=float)
        ph = rng.random(4) * 10

        def deform(D, P, r=r, ph=ph):
            n = (np.sin(D[:, 0] * 5 + ph[0]) * np.sin(D[:, 1] * 4 + ph[1]) * np.sin(D[:, 2] * 5 + ph[2]) +
                 0.5 * np.sin(D[:, 0] * 11 + D[:, 2] * 9 + ph[3]))
            return P * (1 + 0.1 * n)[:, None]

        if inner_mat:
            col_fn = lambda D, P: {'col': ('POINT', np.repeat(np.array([K.srgb('#2f6224')[:3]]), len(D), 0) *
                                           (0.7 + 0.5 * smoothstep(-0.8, 0.9, D[:, 2:3])))}
            K.blob(name + f'_massa{ci}', (r * 0.9, r * 0.9, r * 0.82), 2.0, (32, 20), deform=deform,
                   mat=m['leaf_clump'], parent=root, loc=tuple(c), attrs_fn=col_fn)
        k = int(density * r * r * 4 * math.pi / 0.5 * 0.5)
        D = rng.normal(size=(k, 3))
        D /= np.linalg.norm(D, axis=1, keepdims=True)
        # minder blaadjes aan de onderkant
        D = D[rng.random(k) < (0.45 + 0.55 * smoothstep(-0.9, 0.3, D[:, 2]))]
        rr = r * (0.82 + 0.22 * rng.random(len(D)))
        P = c + D * rr[:, None]
        V, F, Cc = _leaf_mesh(len(D), P, D, leaf_size, rng, colors)
        allV.append(V)
        allF.extend([(a + off, b + off, cc + off) for (a, b, cc) in F])
        allC.append(Cc)
        off += len(V)
    leaves = K.mesh_obj(name + '_bladeren', np.concatenate(allV), allF, m['leaf'], root,
                        attrs={'col': ('POINT', np.concatenate(allC))})
    return root


def tree(name, loc=(0, 0, 0), height=4.5, crown=1.6, parent=None, seed=11, lean=(0.0, 0.0), leaf_size=0.07,
         density=700, trunk_r=0.17):
    m = world_mats()
    rng = np.random.default_rng(seed)
    root = K.empty(name, loc, (0, 0, rng.random() * 6.28), 1.0, parent)
    h0 = height * 0.55
    trunk = [(0, 0, -0.05), (lean[0] * 0.3, lean[1] * 0.3, h0 * 0.35), (lean[0] * 0.7, lean[1] * 0.7, h0 * 0.7),
             (lean[0], lean[1], h0)]
    rr = [trunk_r * 1.5, trunk_r * 1.05, trunk_r * 0.92, trunk_r * 0.8]
    K.tube(name + '_stam', trunk, rr, m['bark'], root, ring=28, per=8, caps=(False, True))
    # wortelaanzet
    for k in range(5):
        a = k / 5 * 6.28 + rng.random()
        K.tube(name + f'_wortel{k}', [(0, 0, 0.25), (math.cos(a) * 0.25, math.sin(a) * 0.25, 0.03),
                                      (math.cos(a) * 0.45, math.sin(a) * 0.45, -0.05)], [0.09, 0.06, 0.02],
               m['bark'], root, ring=12, per=5)
    top = np.array(trunk[-1])
    clumps = []
    for b in range(5):
        a = b / 5 * 6.28 + rng.random() * 0.8
        out = np.array([math.cos(a), math.sin(a), 0])
        end = top + out * crown * 0.55 + np.array([0, 0, height * (0.18 + 0.15 * rng.random())])
        mid = top + out * crown * 0.25 + np.array([0, 0, height * 0.08])
        K.tube(name + f'_tak{b}', [top - np.array([0, 0, 0.2]), mid, end], [trunk_r * 0.6, trunk_r * 0.42, trunk_r * 0.2],
               m['bark'], root, ring=16, per=6)
        clumps.append((end + np.array([0, 0, 0.15]), crown * (0.45 + 0.15 * rng.random())))
    clumps.append((top + np.array([0, 0, height * 0.35]), crown * 0.62))
    for k in range(4):
        a = rng.random() * 6.28
        clumps.append((top + np.array([math.cos(a) * crown * 0.5, math.sin(a) * crown * 0.5, height * (0.1 + 0.3 * rng.random())]),
                       crown * (0.35 + 0.15 * rng.random())))
    foliage(name + '_kruin', clumps, root, leaf_size=leaf_size, density=density, seed=seed)
    return root


def bush(name, loc=(0, 0, 0), size=1.0, parent=None, seed=13, leaf_size=0.045, density=1400, berries=False):
    rng = np.random.default_rng(seed)
    root = K.empty(name, loc, (0, 0, rng.random() * 6.28), 1.0, parent)
    clumps = []
    for k in range(7):
        a = k / 7 * 6.28 + rng.random() * 0.5
        d = size * 0.45 * rng.random()
        clumps.append(((math.cos(a) * d, math.sin(a) * d, size * (0.35 + 0.25 * rng.random())),
                       size * (0.32 + 0.12 * rng.random())))
    clumps.append(((0, 0, size * 0.62), size * 0.42))
    foliage(name + '_blad', clumps, root, leaf_size=leaf_size, density=density, seed=seed,
            colors=['#2f6a25', '#3d7d2c', '#4a8f32', '#58a03a', '#2a5e22'])
    return root


# ------------------------------------------------------------------ gevels
def window(name, parent, x, z, w, h, frame_mat, glass_mat, y=0.0, panes=(2, 3), sill=True):
    m = world_mats()
    root = K.empty(name, (x, y - 0.03, z), (0, 0, 0), 1.0, parent)
    K.blob(name + '_glas', (w / 2, 0.01, h / 2), 8, (16, 8), mat=glass_mat, parent=root, loc=(0, 0.015, 0))
    fw = 0.045
    for (cx, cz, sw, sh) in ((0, h / 2, w / 2 + fw, fw), (0, -h / 2, w / 2 + fw, fw), (-w / 2, 0, fw, h / 2),
                             (w / 2, 0, fw, h / 2)):
        K.blob(name + f'_kozijn{cx}{cz}', (sw, 0.04, sh), 8, (16, 8), mat=frame_mat, parent=root, loc=(cx, 0, cz))
    nx, nz = panes
    for i in range(1, nx):
        K.blob(name + f'_roede_v{i}', (0.015, 0.025, h / 2), 8, (8, 6), mat=frame_mat, parent=root,
               loc=(-w / 2 + w * i / nx, 0.01, 0))
    for i in range(1, nz):
        K.blob(name + f'_roede_h{i}', (w / 2, 0.025, 0.015), 8, (8, 6), mat=frame_mat, parent=root,
               loc=(0, 0.01, -h / 2 + h * i / nz))
    if sill:
        K.blob(name + '_dorpel', (w / 2 + 0.08, 0.08, 0.025), 8, (16, 8), mat=frame_mat, parent=root,
               loc=(0, -0.05, -h / 2 - 0.06))
    return root


def gable_house(name, x, width, height, parent=None, brick='brick', door='door', seed=0, gable='trap', y=0.0,
                floors=3, door_side=0.3, ground_window=True):
    """Smal Hollands huis: gevel in het xz-vlak (voorkant naar -y), trap- of klokgevel."""
    m = world_mats()
    rng = np.random.default_rng(seed)
    root = K.empty(name, (x, y, 0), (0, 0, 0), 1.0, parent)
    w2 = width / 2
    pts = [(-w2, 0), (w2, 0), (w2, height)]
    if gable == 'trap':
        steps = 3
        gh = 1.8
        for k in range(steps):
            xa = w2 - (k + 1) * w2 / (steps + 1)
            pts += [(xa + w2 / (steps + 1), height + k * gh / steps), (xa + w2 / (steps + 1), height + (k + 1) * gh / steps),
                    (xa, height + (k + 1) * gh / steps)]
        pts += [(w2 / (steps + 1) * 0.5, height + gh + 0.35), (-w2 / (steps + 1) * 0.5, height + gh + 0.35)]
        for k in reversed(range(steps)):
            xa = -(w2 - (k + 1) * w2 / (steps + 1))
            pts += [(xa, height + (k + 1) * gh / steps), (xa - w2 / (steps + 1), height + (k + 1) * gh / steps),
                    (xa - w2 / (steps + 1), height + k * gh / steps)]
        pts = [pts[0], pts[1], pts[2]] + pts[3:]
    elif gable == 'klok':
        for t in np.linspace(0, 1, 14):
            a = t * math.pi
            pts.append((w2 * math.cos(a) * (0.85 - 0.25 * math.sin(a)), height + math.sin(a) * 1.7 * (0.6 + 0.4 * math.sin(a))))
    else:
        pts.append((0, height + 1.5))
    pts.append((-w2, height))
    pts2 = [(p[0], p[1]) for p in pts]
    gev = K.poly_obj(name + '_gevel', pts2, depth=0.15, bevel=0.02, mat=m[brick], parent=root, loc=(0, 0.15, 0),
                     rot=(math.pi / 2, 0, 0))
    # ramen per verdieping
    fh = height / floors
    for f in range(floors):
        z = fh * (f + 0.55)
        n = 2 if width > 3.2 else 1
        for i in range(n):
            xx = -w2 + width * (i + 0.5) / n
            if f == 0 and abs(xx - door_side * w2) < 0.6 and n > 1:
                continue
            if f == 0 and not ground_window:
                continue
            window(name + f'_raam{f}{i}', root, xx, z, 0.95 if n > 1 else 1.2, fh * 0.58, m['frame'],
                   m['window_dark'], y=-0.0)
    if door:
        dx = door_side * w2
        K.blob(name + '_deur', (0.48, 0.05, 1.05), 8, (16, 8), mat=m[door], parent=root, loc=(dx, -0.04, 1.05))
        K.blob(name + '_deurkozijn', (0.56, 0.04, 1.12), 8, (16, 8), mat=m['frame'], parent=root, loc=(dx, -0.01, 1.08))
        K.blob(name + '_bovenlicht', (0.4, 0.03, 0.18), 8, (16, 8), mat=m['window_dark'], parent=root, loc=(dx, -0.05, 2.35))
        K.blob(name + '_stoep', (0.7, 0.3, 0.06), 8, (16, 8), mat=world_mats()['curb'], parent=root, loc=(dx, -0.3, 0.06))
    # dak achter de gevel
    K.blob(name + '_dak', (w2 * 0.95, 2.5, 0.8), 3.0, (32, 16), mat=m['roof'], parent=root, loc=(0, 2.7, height + 0.4))
    return root


def lamp_post(name, loc, parent=None, h=3.2, glow=True):
    m = world_mats()
    root = K.empty(name, loc, (0, 0, 0), 1.0, parent)
    K.tube(name + '_paal', [(0, 0, 0), (0, 0, h * 0.5), (0, 0, h)], [0.06, 0.045, 0.04], m['metal_dark'], root,
           ring=16, per=4)
    K.blob(name + '_voet', (0.1, 0.1, 0.12), 3, (16, 8), mat=m['metal_dark'], parent=root, loc=(0, 0, 0.12))
    K.lathe(name + '_kap', [(0.0, h + 0.4), (0.18, h + 0.32), (0.12, h + 0.25)], 24, m['metal_dark'], root)
    K.blob(name + '_glas', (0.12, 0.12, 0.2), 2.5, (16, 12), mat=m['lamp_glow'] if glow else m['window'], parent=root,
           loc=(0, 0, h + 0.15))
    return root


def bench(name, loc, rot=0.0, parent=None):
    m = world_mats()
    root = K.empty(name, loc, (0, 0, rot), 1.0, parent)
    for i in range(3):
        K.blob(name + f'_zitlat{i}', (0.8, 0.05, 0.02), 6, (16, 8), mat=m['bench'], parent=root,
               loc=(0, -0.12 + i * 0.12, 0.45))
    for i in range(2):
        K.blob(name + f'_rug{i}', (0.8, 0.02, 0.05), 6, (16, 8), mat=m['bench'], parent=root,
               loc=(0, 0.2, 0.65 + i * 0.14))
    for s in (-1, 1):
        K.tube(name + f'_poot{s}', [(s * 0.7, -0.15, 0), (s * 0.7, -0.1, 0.44), (s * 0.7, 0.18, 0.46), (s * 0.7, 0.22, 0.85)],
               [0.025] * 4, m['metal_dark'], root, ring=10, per=4)
    return root
