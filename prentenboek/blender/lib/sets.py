"""Decors: slaapkamer (dag/nacht), straat met bakkerij, park, bakkerij van binnen."""
import math
import bpy
import numpy as np
from . import core as K, mats as M, world as Wd, props as P
from .core import smoothstep

# ------------------------------------------------------------------ materialen voor de decors
_S = {}


def set_mats():
    if _S:
        return _S
    w = Wd.world_mats()
    g = M.NT('Behang sterren')
    co = g.coord('Object')
    x, y, z = g.sep(co)
    v = g.voronoi(g.comb(g.math('MULTIPLY', x, 1.0), g.math('MULTIPLY', y, 1.0), z), 5.0, out='Distance', rand=0.6)
    star = g.math('LESS_THAN', v, 0.06)
    stripes = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', g.math('ADD', x, y), 40.0)), 0.92)
    base = g.mix(stripes, K.srgb('#cfe3f1'), K.srgb('#d9eaf5'))
    col = g.mix(star, base, K.srgb('#f6dd8a'))
    n = g.noise(co, 3, 3)
    col = g.mix(g.maprange(n, 0.3, 0.7, 0, 0.08), col, K.srgb('#a9c4da'))
    p = g.principled(color=col, rough=0.85, sheen=0.2)
    _S['wallpaper'] = g.done(p)
    g = M.NT('Planken')
    co = g.coord('Object')
    b = g.n('ShaderNodeTexBrick', offset=0.37, squash=1.0)
    g.set(b, 'Vector', g.mapping(co, scale=(1, 6, 1)))
    g.set(b, 'Color1', K.srgb('#c48f5f'))
    g.set(b, 'Color2', K.srgb('#a8744a'))
    g.set(b, 'Mortar', K.srgb('#5e3d22'))
    g.set(b, 'Scale', 1.2)
    g.set(b, 'Mortar Size', 0.006)
    g.set(b, 'Brick Width', 1.6)
    g.set(b, 'Row Height', 0.18)
    w_ = g.wave(g.mapping(co, scale=(1, 30, 1)), 3, 'BANDS', 'X', 'SIN', distortion=8, detail=3)
    col = g.mix(g.maprange(w_, 0.2, 1, 0, 0.35), g._out(b, 'Color'), K.srgb('#7f5232'))
    p = g.principled(color=col, rough=0.35, coat=0.35, coat_rough=0.15)
    g.set(p, 'Normal', g.bump(g.math('SUBTRACT', 1.0, g._out(b, 'Fac')), 0.3, 0.003))
    _S['planks'] = g.done(p)
    _S['gravel'] = M.painted('Grind', '#c9b48e', rough=0.95, var=0.2, scale=90, bump=0.6)
    _S['lawn'] = M.painted('Grasveld', '#4e8a2c', rough=0.9, var=0.18, scale=3, bump=0.25)
    _S['blocks'] = M.vertex_colored('Blokken', rough=0.35, bump=0.05, coat=0.4)
    _S['books'] = M.vertex_colored('Boeken', rough=0.5, bump=0.02)
    _S['tile_white'] = M.painted('Tegels', '#f6f2ea', rough=0.12, var=0.02, coat=0.9, bump=0.0)
    return _S


def _box(name, size, loc, mat, parent=None, n=8.0, rot=(0, 0, 0)):
    return K.blob(name, (size[0] / 2, size[1] / 2, size[2] / 2), n, (16, 8), mat=mat, parent=parent, loc=loc, rot=rot)


# ------------------------------------------------------------------ slaapkamer
def bedroom(night=False, parent=None, rug=True, bed=True, shelf=True, toys=True, window_x=0.4, sleeper=False):
    """Kamer 4,4 x 4 m; vloer op z=0, achterwand op y=+2, linkerwand op x=-2.2. Raam in de achterwand."""
    w, s, pm = Wd.world_mats(), set_mats(), P.prop_mats()
    root = K.empty('Kamer', (0, 0, 0), (0, 0, 0), 1.0, parent)
    _box('Vloer', (4.6, 4.4, 0.04), (0, 0, -0.02), s['planks'], root, n=10)
    # wanden met raamopening (achterwand in delen)
    wx0, wx1, wz0, wz1 = window_x - 0.65, window_x + 0.65, 0.85, 2.15
    _box('Wand_achter_l', (wx0 + 2.3, 0.1, 2.8), ((wx0 - 2.3) / 2, 2.05, 1.4), s['wallpaper'], root, n=10)
    _box('Wand_achter_r', (2.3 - wx1, 0.1, 2.8), ((wx1 + 2.3) / 2, 2.05, 1.4), s['wallpaper'], root, n=10)
    _box('Wand_achter_o', (wx1 - wx0, 0.1, wz0), ((wx0 + wx1) / 2, 2.05, wz0 / 2), s['wallpaper'], root, n=10)
    _box('Wand_achter_b', (wx1 - wx0, 0.1, 2.8 - wz1), ((wx0 + wx1) / 2, 2.05, (wz1 + 2.8) / 2), s['wallpaper'], root, n=10)
    _box('Wand_links', (0.1, 4.4, 2.8), (-2.3, 0, 1.4), s['wallpaper'], root, n=10)
    _box('Wand_rechts', (0.1, 4.4, 2.8), (2.3, 0, 1.4), s['wallpaper'], root, n=10)
    _box('Plafond', (4.6, 4.4, 0.06), (0, 0, 2.83), w['frame'], root, n=10)
    for nm, x in (('Plint_l', -2.24), ('Plint_r', 2.24)):
        _box(nm, (0.03, 4.4, 0.1), (x, 0, 0.05), w['frame'], root)
    _box('Plint_a', (4.6, 0.03, 0.1), (0, 1.99, 0.05), w['frame'], root)
    # raamkozijn en vensterbank
    for (cx, cz, sx, sz) in (((wx0 + wx1) / 2, wz0, wx1 - wx0 + 0.12, 0.08), ((wx0 + wx1) / 2, wz1, wx1 - wx0 + 0.12, 0.08),
                             (wx0, (wz0 + wz1) / 2, 0.08, wz1 - wz0), (wx1, (wz0 + wz1) / 2, 0.08, wz1 - wz0),
                             ((wx0 + wx1) / 2, (wz0 + wz1) / 2, 0.05, wz1 - wz0), ((wx0 + wx1) / 2, wz0 + (wz1 - wz0) * 0.62, wx1 - wx0, 0.05)):
        _box(f'Kozijn{cx:.2f}{cz:.2f}{sx:.2f}', (sx, 0.14, sz), (cx, 2.0, cz), w['frame'], root)
    _box('Vensterbank', (wx1 - wx0 + 0.3, 0.26, 0.04), ((wx0 + wx1) / 2, 1.92, wz0 - 0.02), w['frame'], root)
    # buiten: lucht (dag) of nacht met maan en sterren
    if night:
        bo = _box('Buiten', (6, 0.05, 4), (window_x, 4.5, 1.5), w['night_sky'], root)
        bo.visible_shadow = False
        mo = K.blob('Maan', (0.3, 0.05, 0.3), 2, (32, 8), mat=w['moon'], parent=root, loc=(window_x - 0.15, 4.4, 1.75))
        mo.visible_shadow = False
        rng = np.random.default_rng(3)
        for i in range(30):
            K.blob(f'Ster{i}', (0.012, 0.01, 0.012), 2, (8, 4), mat=w['star'], parent=root,
                   loc=(window_x + rng.uniform(-1.4, 1.4), 4.4, rng.uniform(0.9, 2.4)))
    else:
        bo = _box('Buiten', (8, 0.05, 5), (window_x, 5.5, 1.5), w['sky_wall'], root)
        bo.visible_shadow = False
        t = Wd.tree('BoomBuiten', (window_x + 2.6, 7.5, -1.0), height=5.5, crown=2.0, seed=41, density=250)
    # gordijnen
    for sgn in (-1, 1):
        x0 = (wx0 - 0.42) if sgn < 0 else (wx1 + 0.42)
        def cur(U, V, x0=x0, sgn=sgn):
            x = x0 + (U - 0.5) * 0.5 + 0.035 * np.sin(U * 18)
            y = 1.9 - 0.05 * np.cos(U * 18) * (0.6 + 0.4 * V)
            z = 0.55 + V * 1.95
            return np.stack([x, y, z], 1)
        c = K.grid_mesh(f'Gordijn{sgn}', 48, 12, cur, w['curtain'], root)
        K.solidify(c, 0.006, 0)
    K.tube('Gordijnroede', [(wx0 - 0.6, 1.88, 2.5), (wx1 + 0.6, 1.88, 2.5)], [0.015, 0.015], w['metal_dark'], root,
           ring=10, per=2)
    if rug:
        # rond gevlochten kleed: concentrische ringen
        nr, na = 90, 200
        rr = np.linspace(0.0, 1.05, nr)
        A = np.linspace(0, 2 * math.pi, na, endpoint=False)
        V, F, C = [], [], []
        cols = np.array([K.srgb(c)[:3] for c in ('#efe0c2', '#86acd3', '#f2c763', '#e8927d', '#a3c79f', '#f6eddc')])
        for i, r in enumerate(rr):
            band = int(r / 1.05 * 13)
            braid = 0.5 + 0.5 * np.cos(A * 70 + i * 1.3)
            z = 0.014 * np.sqrt(max(0.0, 1 - (r / 1.06) ** 8)) + 0.002 * braid * (r > 0.02)
            for k, a_ in enumerate(A):
                V.append((math.cos(a_) * r, math.sin(a_) * r, z[k] if np.ndim(z) else z))
                C.append(cols[band % len(cols)] * (0.88 + 0.12 * braid[k]))
        for i in range(nr - 1):
            for k in range(na):
                F.append((i * na + k, i * na + (k + 1) % na, (i + 1) * na + (k + 1) % na, (i + 1) * na + k))
        K.mesh_obj('Kleed', np.array(V), F, w['rug'], root, loc=(0.25, -0.25, 0.004),
                   attrs={'col': ('POINT', np.array(C))})
    if bed:
        bx, by = -1.35, 0.85
        _box('Bed_onder', (1.0, 1.9, 0.3), (bx, by, 0.28), w['bed_wood'], root, n=5)
        for (px, py) in ((-0.48, -0.92), (0.48, -0.92), (-0.48, 0.92), (0.48, 0.92)):
            K.tube(f'Bedpoot{px}{py}', [(bx + px, by + py, 0), (bx + px, by + py, 0.55 if py > 0 else 0.42)],
                   [0.05, 0.045], w['bed_wood'], root, ring=16, per=2)
            K.blob(f'Bedknop{px}{py}', (0.06, 0.06, 0.06), 2, (16, 10), mat=w['bed_wood'], parent=root,
                   loc=(bx + px, by + py, 0.59 if py > 0 else 0.46))
        _box('Hoofdbord', (1.0, 0.06, 0.55), (bx, by + 0.93, 0.62), w['bed_wood'], root, n=5)
        _box('Voetbord', (1.0, 0.06, 0.3), (bx, by - 0.93, 0.5), w['bed_wood'], root, n=5)
        _box('Matras', (0.94, 1.82, 0.16), (bx, by, 0.5), w['pillow'], root, n=4)

        def duvet(U, V):
            x = bx + (U - 0.5) * 1.12
            y = by - 0.95 + V * 1.45
            z = 0.62 + 0.06 * np.sin(U * 3.14) - 0.2 * smoothstep(0.38, 0.5, np.abs(U - 0.5)) + 0.015 * np.sin(V * 9 + U * 4)
            if sleeper:
                z = z + 0.2 * np.exp(-((x - bx - 0.05) / 0.2) ** 2) * smoothstep(by - 0.95, by - 0.6, y)
            return np.stack([x, y, z], 1)
        d = K.grid_mesh('Dekbed', 40, 40, duvet, w['duvet'], root)
        K.solidify(d, 0.04, -1)
        K.subsurf(d, 1)
        K.blob('Kussen', (0.36, 0.22, 0.06 if sleeper else 0.08), 2.6, (32, 16), mat=w['pillow'], parent=root,
               loc=(bx, by + 0.7, 0.62 if sleeper else 0.66))
    if shelf:
        sx = 2.12
        for k, z in enumerate((0.45, 0.9, 1.35)):
            _box(f'Plank{k}', (0.3, 1.2, 0.03), (sx, 0.2, z), w['bed_wood'], root)
        rng = np.random.default_rng(8)
        V, F, C = [], [], []
        cols = [K.srgb(c)[:3] for c in ('#d94f3d', '#3d7fd9', '#f2c14b', '#5cb85c', '#9b59b6', '#f08a3c', '#2c3e50')]
        y = -0.35
        for k in range(14):
            h, t = 0.18 + 0.1 * rng.random(), 0.03 + 0.03 * rng.random()
            D_, F_ = K.sph(8, 4)
            Pp = K.superdir(D_, 8) * np.array([0.1, t / 2, h / 2]) + np.array([sx - 0.02, y, 0.92 + h / 2])
            off = len(V)
            V.extend(Pp)
            F.extend([tuple(i + off for i in f) for f in F_])
            C.extend([cols[k % len(cols)]] * len(D_))
            y += t + 0.005
        K.mesh_obj('Boeken', np.array(V), F, s['books'], root, attrs={'col': ('POINT', np.array(C))})
    if toys:
        rng = np.random.default_rng(12)
        V, F, C = [], [], []
        cols = [K.srgb(c)[:3] for c in ('#e74c3c', '#3498db', '#f1c40f', '#2ecc71', '#ff8fb1')]
        for k, (x, y, z, r) in enumerate(((1.25, 0.9, 0.05, 0.3), (1.38, 0.95, 0.05, -0.2), (1.31, 0.92, 0.15, 0.6),
                                          (-0.6, -1.3, 0.05, 0.4), (1.0, -1.1, 0.05, 1.0))):
            D_, F_ = K.sph(12, 6)
            Pp = K.superdir(D_, 6) * 0.05
            Rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
            Pp = Pp @ Rz.T + np.array([x, y, z])
            off = len(V)
            V.extend(Pp)
            F.extend([tuple(i + off for i in f) for f in F_])
            C.extend([cols[k % len(cols)]] * len(D_))
        K.mesh_obj('Blokken', np.array(V), F, s['blocks'], root, attrs={'col': ('POINT', np.array(C))})
    return root


# ------------------------------------------------------------------ straat met bakkerij
def bakery_facade(name, x, width=5.2, height=9.0, parent=None, y=5.0):
    w, pm = Wd.world_mats(), P.prop_mats()
    root = K.empty(name, (x, y, 0), (0, 0, 0), 1.0, parent)
    Wd.gable_house(name + '_huis', 0, width, height, root, brick='brick', door=None, gable='klok', floors=3,
                   ground_window=False)
    # winkelpui: groen kozijn, grote etalage, deur
    _box(name + '_pui', (width - 0.2, 0.18, 2.9), (0, -0.06, 1.45), w['frame_green'], root, n=8)
    _box(name + '_etalage', (width * 0.56, 0.05, 1.7), (-width * 0.16, -0.17, 1.35), w['window_dark'], root, n=10)
    _box(name + '_deur', (0.95, 0.06, 2.2), (width * 0.32, -0.17, 1.1), w['door'], root, n=8)
    _box(name + '_deurglas', (0.6, 0.03, 1.1), (width * 0.32, -0.2, 1.45), w['window_dark'], root, n=10)
    # uithangbord BAKKER
    _box(name + '_bord', (width * 0.75, 0.08, 0.5), (0, -0.2, 2.65), w['sign'], root, n=8)
    K.text_obj(name + '_tekst', 'BAKKER', size=0.36, extrude=0.02, bevel=0.006, mat=w['gold_letter'], parent=root,
               loc=(0, -0.26, 2.65), rot=(math.pi / 2, 0, 0), font='MuseoSansRounded900.otf', spacing=1.15)
    # gestreepte luifel
    g = M.NT('Luifelstrepen')
    co = g.coord('Object')
    xx, yy, zz = g.sep(co)
    st = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', xx, 14.0)), 0.0)
    col = g.mix(st, K.srgb('#d8383a'), K.srgb('#fbf5e8'))
    p = g.principled(color=col, rough=0.75, sheen=0.5)
    g.set(p, 'Normal', g.bump(g.wave(co, 600, 'BANDS', 'Z'), 0.1, 0.001))
    am = g.done(p)

    def awn(U, V):
        xq = (U - 0.5) * (width - 0.1)
        yq = -0.25 - V * 1.25
        zq = 2.45 - V * 0.55 + 0.03 * np.sin(U * 40) * V
        return np.stack([xq, yq, zq], 1)
    a = K.grid_mesh(name + '_luifel', 80, 10, awn, am, root)
    K.solidify(a, 0.01, 0)
    # golfrand
    def flap(U, V):
        xq = (U - 0.5) * (width - 0.1)
        yq = np.full_like(U, -1.5)
        zq = 1.9 - V * 0.22 * (0.75 + 0.25 * np.abs(np.sin(U * 40)))
        return np.stack([xq, yq, zq], 1)
    f = K.grid_mesh(name + '_luifelrand', 160, 4, flap, am, root)
    K.solidify(f, 0.008, 0)
    # in de etalage: broden en manden (licht van binnen)
    for i in range(5):
        K.blob(name + f'_brood{i}', (0.16, 0.09, 0.08), 2.2, (24, 12), mat=w['bread'], parent=root,
               loc=(-width * 0.16 - 1.0 + i * 0.5, -0.05, 0.75), rot=(0, 0, 0.3 * i))
    K.light('AREA', (x - width * 0.16, y + 0.6, 1.8), (x - width * 0.16, y - 1.0, 0.8), energy=120, size=1.5,
            color=(1.0, 0.8, 0.55))
    return root


def street(parent=None, bakery_x=0.0, quality=None, houses=True, trees=True, y_fac=5.0, cob=(-8, 8, -3.2, 2.6),
           seed=0, lamp=True):
    """Straat langs x. Klinkers, stoepen, gevelrij op y=5 met de bakkerij op bakery_x."""
    q = quality or {}
    Wd.cobbles('Klinkers', *cob, pattern='keper', seed=seed + 1)
    Wd.curb('Stoeprand', -16, 16, 2.68)
    Wd.sidewalk('Stoep', -16, 16, 2.75, y_fac)
    Wd.curb('Stoeprand2', -16, 16, -3.28)
    Wd.sidewalk('Stoep2', -14, 14, -6.0, -3.35)
    if houses:
        specs = [(4.2, 9.5, 'brick', 'trap', 'door'), (3.6, 10.5, 'brick2', 'klok', 'door_red'),
                 (4.6, 9.0, 'brick3', 'trap', 'door'), ('BAKKERIJ',), (3.8, 11.0, 'brick', 'klok', 'door_red'),
                 (4.4, 9.8, 'brick2', 'trap', 'door'), (3.6, 10.2, 'brick3', 'klok', 'door'),
                 (4.0, 9.4, 'brick', 'trap', 'door_red')]
        widths = [s[0] if len(s) > 1 else 5.2 for s in specs]
        # bakkerij op bakery_x
        idx = 3
        x = bakery_x - 2.6 - sum(widths[:idx]) - 0.05 * idx
        for i, sp in enumerate(specs):
            if len(sp) == 1:
                bakery_facade('Bakkerij', x + 2.6, parent=parent, y=y_fac)
                x += 5.2 + 0.05
                continue
            w_, h, b, g, d = sp
            Wd.gable_house(f'Huis{i}', x + w_ / 2, w_, h, parent, brick=b, gable=g, door=d, seed=i, y=y_fac,
                           door_side=0.45 if i % 2 else -0.45)
            x += w_ + 0.05
    if trees:
        for i, tx in enumerate((bakery_x - 10.5, bakery_x - 5.0, bakery_x + 5.6, bakery_x + 11.0)):
            Wd.tree(f'Boom{i}', (tx, y_fac - 0.9, 0.12), height=5.2, crown=1.7, seed=20 + i,
                    density=int(500 * q.get('leaves', 1.0)))
    if lamp:
        for i, lx in enumerate((bakery_x - 7.6, bakery_x + 7.8)):
            Wd.lamp_post(f'Lantaarn{i}', (lx, y_fac - 2.0, 0.12), glow=False)


# ------------------------------------------------------------------ park
def park(parent=None, quality=None, grass_region=(-3, 3, -3, 3), seed=0, trees=None, bushes=None, path=True,
         flowers_n=40, houses=True, grass_density=2600):
    q = quality or {}
    s, w = set_mats(), Wd.world_mats()
    Wd.ground('Grasveld', (80, 80), s['lawn'], parent)
    if grass_region:
        Wd.grass('Gras', grass_region, density=int(grass_density * q.get('grass', 1.0)), seed=seed + 3,
                 height=(0.05, 0.12))
    if path:
        def pth(U, V):
            x = (U - 0.5) * 40
            y = 3.2 + 0.6 * np.sin(x * 0.12) + (V - 0.5) * 1.6
            return np.stack([x, y, np.full_like(x, 0.006)], 1)
        K.grid_mesh('Pad', 120, 6, pth, s['gravel'], parent)
    for i, (tx, ty, h, c) in enumerate(trees or []):
        Wd.tree(f'Boom{i}', (tx, ty, 0), height=h, crown=c, seed=50 + i, density=int(650 * q.get('leaves', 1.0)),
                leaf_size=0.08)
    for i, (bx, by, sz) in enumerate(bushes or []):
        Wd.bush(f'Struik{i}', (bx, by, 0), size=sz, seed=70 + i, density=int(1500 * q.get('leaves', 1.0)))
    if flowers_n:
        x0, x1, y0, y1 = grass_region or (-3, 3, -3, 3)
        Wd.flowers('Bloemen', (x0, x1, y0, y1), flowers_n, seed=seed + 9)
    if houses:
        for i in range(8):
            Wd.gable_house(f'Parkhuis{i}', -18 + i * 4.6, 4.4, 9 + (i % 3), parent, brick=('brick', 'brick2', 'brick3')[i % 3],
                           gable=('trap', 'klok')[i % 2], door='door', seed=i, y=22)


# ------------------------------------------------------------------ bakkerij van binnen
def bakery_inside(parent=None):
    """Toonbank met glazen vitrine langs x op y=0 (voorkant op y=-0.45), wand achter op y=+2."""
    w, s, pm = Wd.world_mats(), set_mats(), P.prop_mats()
    root = K.empty('Winkel', (0, 0, 0), (0, 0, 0), 1.0, parent)
    _box('Winkelvloer', (10, 10, 0.04), (0, 0, -0.02), s['planks'], root, n=10)
    # wandtegels met kleurattribuut (wit/blauw ruit)
    V, F, C = [], [], []
    k = 0
    for i in range(-30, 30):
        for j in range(0, 16):
            x0, z0 = i * 0.15, j * 0.15
            off = len(V)
            V.extend([(x0, 2.0, z0), (x0 + 0.145, 2.0, z0), (x0 + 0.145, 2.0, z0 + 0.145), (x0, 2.0, z0 + 0.145)])
            F.append((off, off + 1, off + 2, off + 3))
            c = K.srgb('#f6f2ea')[:3] if (i + j) % 7 else K.srgb('#6f9ccc')[:3]
            C.extend([c] * 4)
    t = K.mesh_obj('Wandtegels', np.array(V), F, w['tile_wall'], root, attrs={'col': ('POINT', np.array(C))})
    K.solidify(t, 0.01, 0)
    _box('Voegen', (9.0, 0.02, 2.4), (0, 2.02, 1.2), w['sand'], root, n=10)
    _box('Wand', (10, 0.1, 4), (0, 2.1, 2), s['wallpaper'], root, n=10)
    # schappen met brood
    rng = np.random.default_rng(4)
    for z in (1.2, 1.65, 2.1):
        _box(f'Schap{z}', (3.6, 0.35, 0.04), (0, 1.8, z), w['bed_wood'], root)
        for i in range(9):
            K.blob(f'Brood{z}{i}', (0.13 + 0.03 * rng.random(), 0.1, 0.07 + 0.02 * rng.random()), 2.2, (24, 12),
                   mat=w['bread'], parent=root, loc=(-1.6 + i * 0.4 + rng.normal(0, 0.03), 1.75, z + 0.08),
                   rot=(0, 0, rng.normal(0, 0.3)))
    # toonbank met vitrine (glas)
    _box('Toonbank', (3.2, 0.9, 0.75), (0, 0.0, 0.375), w['counter'], root, n=6)
    _box('Toonbankblad', (3.3, 0.95, 0.04), (0, 0.0, 0.77), w['bed_wood'], root, n=6)
    return root
