"""Papieren decors voor de kijkdoos: alles uitgeknipt karton in laagjes (vormen in cm, plaatsing in m).

Rechtop staande kaarten kijken naar -y; de grond ligt plat (xy). Een decor is een stapel kaarten op
verschillende diepte: lucht achteraan, dan heuvels of huizen, dan de grond met de figuurtjes."""
import math
import contextlib
import bpy
import numpy as np
from . import core as K
from .papier import (piece, group, circle, ellipse, rrect, star, rotate, chaikin, strip, arc_pts, radial_union,
                     scallop, plain_mat, tiles, CM)


def card(name, poly, color, y, x=0.0, z=0.0, layer=0.0, thick=0.0006, edge=None, bend=0.0, jitter=0.01, rot=0.0,
         paper='karton', col2=None):
    """Rechtopstaande kaart op diepte y (m), verschoven over x/z (m)."""
    ob = piece(name, poly, color, None, layer, edge=edge, thick=thick, bend=bend, jitter=jitter, paper=paper,
               col2=col2)
    ob.location = (x, y, z)
    if rot:
        ob.rotation_euler = (0, math.radians(rot), 0)
    return ob


def flat(name, poly, color, z=0.0, x=0.0, y=0.0, layer=0.0, thick=0.0006, edge=None, rotz=0.0, paper='karton',
         col2=None):
    """Platliggend stuk karton (grond, kleedje, kruimels)."""
    ob = piece(name, poly, color, None, layer, edge=edge, thick=thick, bend=0.0, jitter=0.008, plane='xy', z=z,
               paper=paper, col2=col2)
    ob.location = (x, y, 0)
    if rotz:
        ob.rotation_euler = (0, 0, rotz)
    return ob


# ------------------------------------------------------------------ lucht en landschap
def sky(y=0.3, w=140, h=70, night=False, sun=(32, 46), clouds=((-38, 44, 1.0), (8, 52, 0.8), (46, 40, 0.9)),
        x0=0.0):
    """Luchtkaart in drie banen (licht naar donker), met papieren wolkjes en een zon (of maan en sterren)."""
    bands = ['#a3d4f5', '#7fc0f0', '#5eaaea'] if not night else ['#2b3b78', '#223066', '#1a2552']
    for i, col in enumerate(bands):
        top = h * (0.38 + 0.31 * (i + 1)) if i < 2 else h + 10
        bot = -10 if i == 0 else h * (0.38 + 0.31 * i) - 3
        poly = np.array([(-w / 2, bot), (w / 2, bot)] + list(scallop(w / 2, -w / 2, top, 1.6, 9, up=True)[1:]))
        card(f'Lucht{i}', poly, col, y + 0.002 * (2 - i), x=x0, layer=0, paper='aquarel')
    if night:
        card('Maan', _moon(9), '#f6e7a8', y - 0.006, x=x0 + sun[0] * CM, z=sun[1] * CM, paper='aquarel')
        rng = np.random.default_rng(3)
        for i in range(22):
            sx, sz = rng.uniform(-w / 2 + 5, w / 2 - 5), rng.uniform(h * 0.35, h - 4)
            card(f'Ster{i}', star(0, 0, rng.uniform(1.0, 1.8), 0.5), '#ffe58a', y - 0.006, x=x0 + sx * CM, z=sz * CM,
                 paper='folie')
    else:
        if sun:
            card('Zon', circle(0, 0, 6.5, 64), '#ffd24a', y - 0.006, x=x0 + sun[0] * CM, z=sun[1] * CM, paper='aquarel')
            for i in range(12):
                a = i * 30
                ray = rotate(np.array([(-1.1, 8.0), (1.1, 8.0), (0.0, 11.5)]), a)
                card(f'Zonnestraal{i}', ray, '#ffc23a', y - 0.005, x=x0 + sun[0] * CM, z=sun[1] * CM, paper='crepe')
        for i, (cx, cz, s) in enumerate(clouds):
            cloud(f'Wolk{i}', x0 + cx * CM, y - 0.008 - 0.002 * i, cz * CM, s)


def _moon(r):
    out = []
    for t in np.linspace(0, 2 * math.pi, 64, endpoint=False):
        p = np.array([math.cos(t), math.sin(t)]) * r
        q = p - np.array([r * 0.45, r * 0.25])
        if np.linalg.norm(q) < r * 0.85:
            p = np.array([r * 0.45, r * 0.25]) + q / np.linalg.norm(q) * r * 0.85
        out.append(p)
    return np.array(out)


def cloud(name, x, y, z, s=1.0):
    shape = radial_union((0, 1.5), [(-5.5, 0.5, 4.0, 3.2), (0, 2.5, 5.2, 4.5), (5.5, 0.8, 4.2, 3.4),
                                    (-2.0, 0.0, 6.0, 2.5), (2.5, 0.0, 6.0, 2.5)])
    shape = shape * s
    shape[:, 1] = np.maximum(shape[:, 1], -2.2 * s)
    card(name + '_schaduw', shape + np.array([0.5, -0.5]), '#dfe9f1', y + 0.0015, x=x, z=z)
    card(name, shape, '#ffffff', y, x=x, z=z, paper='zijde')


def hills(y0=0.18, colors=('#9cc96b', '#86bb5a', '#70a94b'), w=140, x0=0.0, seed=1):
    """Glooiende heuvellaagjes van groen karton (achter naar voor)."""
    rng = np.random.default_rng(seed)
    for i, col in enumerate(colors):
        top = []
        ph = rng.uniform(0, 6.28)
        hgt = 26 - i * 6
        for x in np.linspace(-w / 2, w / 2, 40):
            top.append((x, hgt + 5 * math.sin(x / (14 + 5 * i) + ph) + 3 * math.sin(x / 7.0 + ph * 2)))
        poly = np.array([(-w / 2, -6), (w / 2, -6)] + top[::-1])
        card(f'Heuvel{i}', poly, col, y0 - i * 0.03, x=x0, paper=('aquarel', 'linnen', 'crepe')[i % 3])


def ground(name='Grond', color='#7fb352', w=1.4, d=0.6, y0=-0.3, z=0.0):
    return flat(name, rrect(0, 0, w * 100, d * 100, 2), color, z=z, x=0, y=y0 + d / 2, thick=0.001, paper='linnen')


def grass_edge(name, y, x0=-0.7, x1=0.7, color='#5f9a3f', h=2.2):
    """Grasrandje: zigzagstrook vooraan of achter een laag."""
    pts = [(x0 * 100, -1.0)]
    n = int((x1 - x0) * 100 / 1.4)
    for i in range(n + 1):
        x = x0 * 100 + i * 1.4
        pts.append((x, h * (0.6 + 0.4 * ((i * 7) % 5) / 4) if i % 2 else 0.2))
    pts.append((x1 * 100, -1.0))
    card(name, np.array(pts), color, y, paper='crepe')


def tree(name, x, y, h=17, r=7.5, color='#5fa344', color2='#4d8f38', apples=0, seed=0):
    rng = np.random.default_rng(seed)
    card(name + '_stam', rrect(0, h * 0.35, 2.2, h * 0.75, 0.8), '#8a5a36', y, x=x, paper='kraft')
    lobes = [(0, h * 0.75 + r * 0.2, r, r * 0.9)]
    for i in range(6):
        a = i * math.pi / 3 + rng.uniform(0, 0.4)
        lobes.append((math.cos(a) * r * 0.62, h * 0.75 + r * 0.2 + math.sin(a) * r * 0.5, r * 0.55, r * 0.5))
    crown = radial_union((0, h * 0.75 + r * 0.2), lobes)
    card(name + '_kruinachter', crown + np.array([0.6, -0.5]), color2, y - 0.002, x=x)
    card(name + '_kruin', crown, color, y - 0.004, x=x, paper='crepe')
    for i in range(apples):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.2, 0.75) * r
        card(f'{name}_appel{i}', circle(math.cos(a) * d, h * 0.75 + r * 0.2 + math.sin(a) * d * 0.8, 0.9, 24),
             '#c4271d', y - 0.006, x=x, paper='karton')


def bush(name, x, y, w=10, h=6, color='#4f9a48', color2='#3f8240', berries=0, seed=0):
    rng = np.random.default_rng(seed)
    lobes = [(0, h * 0.45, w * 0.5, h * 0.5)]
    for i in range(5):
        lobes.append((rng.uniform(-0.6, 0.6) * w * 0.5, h * rng.uniform(0.35, 0.75), w * 0.28, h * 0.4))
    shape = radial_union((0, h * 0.45), lobes)
    shape[:, 1] = np.maximum(shape[:, 1], 0)
    card(name + '_achter', shape * 1.04 + np.array([0.5, 0.0]), color2, y + 0.002, x=x)
    card(name, shape, color, y, x=x, paper='crepe')
    for i in range(berries):
        bx = rng.uniform(-0.75, 0.75) * w * 0.5
        bz = rng.uniform(0.25, 0.85) * h
        card(f'{name}_bes{i}', circle(bx, bz, 0.55, 20), '#e2425b', y - 0.002, x=x, paper='glans')


def flowers(name, x0, x1, y, n=10, seed=4, colors=('#f27c9b', '#ffd34d', '#ffffff', '#b47ae0', '#ff9a52')):
    rng = np.random.default_rng(seed)
    for i in range(n):
        x = rng.uniform(x0, x1)
        hgt = rng.uniform(2.0, 3.6)
        yy = y + rng.uniform(-0.01, 0.01)
        card(f'{name}{i}_steel', strip([(0, 0), (0.2, hgt * 0.5), (0, hgt)], 0.28), '#4f8a35', yy, x=x)
        col = colors[rng.integers(len(colors))]
        petals = radial_union((0, hgt), [(math.cos(a) * 0.7, hgt + math.sin(a) * 0.7, 0.62, 0.62)
                                         for a in np.linspace(0, 2 * math.pi, 5, endpoint=False)])
        card(f'{name}{i}_bloem', petals, col, yy - 0.0015, x=x, paper='zijde')
        card(f'{name}{i}_hart', circle(0, hgt, 0.42, 20), '#f5c242', yy - 0.003, x=x)


def landscape(night=False, x0=0.0, sky_y=0.32, trees=((-38, 0.2, 18, 8, 5), (40, 0.22, 16, 7, 0)), bushes=(),
              flowers_n=12):
    sky(y=sky_y, night=night, x0=x0)
    hills(y0=sky_y - 0.06, x0=x0)
    for i, (tx, ty, th, tr, ap) in enumerate(trees):
        tree(f'Boom{i}', x0 + tx * CM, ty, th, tr, apples=ap, seed=i)
    for i, (bx, by, bw, bh, be) in enumerate(bushes):
        bush(f'Struik{i}', x0 + bx * CM, by, bw, bh, berries=be, seed=10 + i)
    ground('Gras', '#86bb5a', y0=-0.35, d=0.5)
    grass_edge('Grasrand_voor', -0.22, color='#6aa84a')
    if flowers_n:
        flowers('Bloem', x0 - 0.45, x0 + 0.45, 0.05, flowers_n)


# ------------------------------------------------------------------ straat
def window(name, cx, cz, w, h, y, lit=False, frame='#fbf7ef'):
    card(name + '_kozijn', rrect(cx, cz, w + 1.2, h + 1.2, 0.6), frame, y)
    ob = card(name + '_ruit', rrect(cx, cz, w, h, 0.4), '#ffd98a' if lit else '#bfe3f5', y - 0.0012, paper='glans')
    if lit:
        ob.data.materials[0] = plain_mat('Raamlicht', '#ffcf7a', emit=2.5)
    card(name + '_roede1', rrect(cx, cz, 0.45, h, 0.15), frame, y - 0.0024)
    card(name + '_roede2', rrect(cx, cz, w, 0.45, 0.15), frame, y - 0.0024)
    card(name + '_bank', rrect(cx, cz - h / 2 - 0.9, w + 2.4, 0.9, 0.3), frame, y - 0.003)


def door(name, cx, y, color, w=4.6, h=8.0):
    arch = [(cx + w / 2 * math.cos(t), h - w / 2 + w / 2 * math.sin(t)) for t in np.linspace(0, math.pi, 16)]
    card(name, np.array([(cx + w / 2, 0)] + arch + [(cx - w / 2, 0)]), color, y, paper='linnen')
    card(name + '_klink', circle(cx + w * 0.3, h * 0.48, 0.38, 16), '#e3b23c', y - 0.0015, paper='folie')


def house(name, x, y, w=14, h=16, color='#e9b44c', roof='#b8503e', door_col='#2f6b8f', seed=0, lit=False):
    """Huisgevel van karton met puntdak, schoorsteen, raampjes en een deurtje (x, y in m; maten in cm)."""
    card(name, rrect(0, h / 2, w, h, 0.6), color, y, x=x, paper=('aquarel', 'linnen', 'karton')[seed % 3])
    rh = w * 0.5
    roof_poly = roof_shape(w, h, rh)
    card(name + '_schoorsteen', rrect(w * 0.24, h + rh * 0.5, 2.0, rh * 0.9, 0.3), '#a9493a', y + 0.002, x=x,
         paper='kraft')
    card(name + '_dak', roof_poly, roof, y - 0.0015, x=x, paper='golf')
    card(name + '_dakrand', strip([(-w / 2 - 1.2, h - 0.5), (w / 2 + 1.2, h - 0.5)], 0.7), roof, y - 0.0025, x=x,
         paper='karton')
    rng = np.random.default_rng(seed)
    dx = w * (0.24 if seed % 2 else -0.24)
    door(name + '_deur', x * 100 + dx, y - 0.0015, door_col)
    window(name + '_raam1', x * 100 - dx, 5.0, 3.6, 3.6, y - 0.0015, lit)
    for i, wx in enumerate((-w * 0.24, w * 0.24)):
        window(f'{name}_raam_b{i}', x * 100 + wx, h * 0.72, 3.4, 3.8, y - 0.0015, lit)
        if rng.random() < 0.5:
            for sx in (-1, 1):
                card(f'{name}_luik{i}{sx}', rrect(x * 100 + wx + sx * 2.9, h * 0.72, 1.4, 4.2, 0.3),
                     door_col, y - 0.001, paper='linnen')


def roof_shape(w, h, rh):
    tri = np.array([(-w / 2 - 1.2, h - 0.5), (w / 2 + 1.2, h - 0.5), (0.0, h + rh)])
    dense = []
    for i in range(3):
        a, b = tri[i], tri[(i + 1) % 3]
        for t in np.linspace(0, 1, 8, endpoint=False):
            dense.append(a + (b - a) * t)
    return chaikin(np.array(dense), 2)


def bakery(name, x, y, w=20, h=17, lit=False):
    card(name, rrect(0, h / 2, w, h, 0.6), '#f4e4c4', y, x=x, paper='stippen', col2='#efd6ae')
    rh = w * 0.42
    card(name + '_dak', roof_shape(w, h, rh), '#b8503e', y - 0.0015, x=x, paper='golf')
    # etalage met koekjes
    card(name + '_etalagekozijn', rrect(x * 100 - 3.0, 5.6, 11.0, 7.0, 0.6), '#2f5d4a', y - 0.0015, paper='linnen')
    ob = card(name + '_etalage', rrect(x * 100 - 3.0, 5.6, 9.8, 5.8, 0.4), '#fff3d6', y - 0.003, paper='zijde')
    if lit:
        ob.data.materials[0] = plain_mat('Etalagelicht', '#ffe2a8', emit=2.0)
    card(name + '_plank', rrect(x * 100 - 3.0, 4.0, 9.8, 0.6, 0.2), '#8a5a36', y - 0.0045, paper='kraft')
    for i, cx in enumerate(np.linspace(x * 100 - 6.6, x * 100 + 0.6, 4)):
        cookie(f'{name}_etalagekoek{i}', cx * CM, y - 0.006, 5.45 * CM, r=1.0, seed=i)
    door(name + '_deur', x * 100 + 6.2, y - 0.0015, '#a83b3b', w=4.8, h=8.6)
    window(name + '_raam1', x * 100 - 5.0, h * 0.8, 3.2, 3.0, y - 0.0015, lit)
    window(name + '_raam2', x * 100 + 5.0, h * 0.8, 3.2, 3.0, y - 0.0015, lit)
    # luifel: rood-wit gestreept met schulprand
    aw_y = y - 0.012
    n = 8
    for i in range(n):
        x0 = -w / 2 - 0.5 + i * (w + 1) / n
        poly = np.array([(x0, h * 0.6), (x0 + (w + 1) / n, h * 0.6), (x0 + (w + 1) / n + 0.3, h * 0.6 - 3.2),
                         (x0 + 0.3, h * 0.6 - 3.2)])
        card(f'{name}_luifel{i}', poly, '#d9443a' if i % 2 == 0 else '#fbf7ef', aw_y, x=x, paper='linnen')
        card(f'{name}_schulp{i}', circle(x0 + (w + 1) / n / 2 + 0.3, h * 0.6 - 3.2, (w + 1) / n / 2, 24),
             '#d9443a' if i % 2 == 0 else '#fbf7ef', aw_y - 0.0005, x=x, paper='linnen')
    # uithangbord met koekje
    card(name + '_bord', rrect(w / 2 + 3.2, h * 0.78, 5.2, 5.2, 0.6), '#5b3b2a', y - 0.01, x=x, paper='kraft')
    cookie(name + '_bordkoek', x + (w / 2 + 3.2) * CM, y - 0.012, h * 0.78 * CM, r=2.0, seed=9)
    card(name + '_stang', rrect(w / 2 + 1.0, h * 0.9, 4.6, 0.4, 0.15), '#3a2a20', y - 0.009, x=x)


def street(x0=-0.6, x1=0.6, bakery_x=0.0, y_house=0.1, lit=False, night=False, seed=1, sky_y=0.32, hs=1.0,
           far=True, cobbles=True):
    if sky_y is not None:
        sky(y=sky_y, night=night, x0=(x0 + x1) / 2)
    # verre huizenrij (kleiner, lichter)
    rng = np.random.default_rng(seed)
    xx = x0 - 0.05
    i = 0
    while far and xx < x1 + 0.05:
        w = rng.uniform(10, 13)
        col = ['#f3d9b4', '#d9e3ef', '#f2c8bd', '#dfe8d2'][i % 4]
        with scaled((xx, y_house + 0.1, 0.0), hs):
            house(f'Verhuis{i}', xx, y_house + 0.1, w, rng.uniform(19, 24), col, '#c87a6a', '#8fa8c8', seed=i + 50,
                  lit=lit)
        xx += w * CM * hs + 0.004
        i += 1
    palette = [('#e9b44c', '#b8503e', '#2f6b8f'), ('#8fb8a8', '#4b5d7a', '#a83b3b'), ('#e88a7d', '#6b4a3a', '#4f7a3a'),
               ('#9fb3d9', '#b8503e', '#7a4f8f'), ('#c8553d', '#4b5d7a', '#2f6b8f')]
    i = 0
    if bakery_x is not None:
        with scaled((bakery_x, y_house, 0.0), hs):
            bakery('Bakkerij', bakery_x, y_house, lit=lit)
        left, right = bakery_x - 0.11 * hs, bakery_x + 0.11 * hs
    else:
        left = right = (x0 + x1) / 2
    xx = left
    while xx > x0 - 0.1:
        w = 14 + 2 * (i % 2)
        col, rf, dr = palette[i % len(palette)]
        hx = xx - w / 2 * CM * hs
        with scaled((hx, y_house, 0.0), hs):
            house(f'Huis{i}', hx, y_house + 0.003 * (i % 2), w, 15 + 2 * (i % 3), col, rf, dr, seed=i, lit=lit)
        xx -= w * CM * hs + 0.006
        i += 1
    xx = right
    while xx < x1 + 0.1:
        w = 14 + 2 * (i % 2)
        col, rf, dr = palette[i % len(palette)]
        hx = xx + w / 2 * CM * hs
        with scaled((hx, y_house, 0.0), hs):
            house(f'Huis{i}', hx, y_house + 0.003 * (i % 2), w, 15 + 2 * (i % 3), col, rf, dr, seed=i, lit=lit)
        xx += w * CM * hs + 0.006
        i += 1
    # stoep en keitjesweg (plat), met een stoeprand
    flat('Stoep', rrect(0, 0, (x1 - x0) * 100 + 20, 9, 0.5), '#ddd5c7', z=0.0, x=(x0 + x1) / 2, y=y_house - 0.04,
         thick=0.001, paper='linnen')
    flat('Weg', rrect(0, 0, (x1 - x0) * 100 + 20, 40, 0.5), '#6f6e6a', z=0.0, x=(x0 + x1) / 2, y=-0.12, thick=0.001,
         paper='kraft')
    rngc = np.random.default_rng(seed + 5)
    k = 0
    for row, yy in enumerate(np.arange(-0.3, y_house - 0.085, 0.022) if cobbles else []):
        for xx in np.arange(x0 - 0.1 + (0.012 if row % 2 else 0), x1 + 0.1, 0.024):
            col = ['#9a978f', '#8f8c85', '#a6a39b', '#86837d'][rngc.integers(4)]
            flat(f'Kei{k}', rrect(0, 0, 2.0, 1.7, 0.6), col, z=0.001, x=xx + rngc.normal(0, 0.0015), y=yy, thick=0.0006,
                 rotz=rngc.normal(0, 0.05))
            k += 1
    card('Stoeprand', rrect(0, 0.4, (x1 - x0) * 100 + 20, 0.9, 0.3), '#c4bcb0', y_house - 0.085, x=(x0 + x1) / 2)


# ------------------------------------------------------------------ voorwerpen
def gingerbread_outline(r=1.0):
    """Silhouet van een koekmannetje, hoogte 2r (cm), middelpunt op de buik."""
    P = [(0.17, 0.32), (0.42, 0.37), (0.74, 0.35), (0.86, 0.24), (0.8, 0.1), (0.46, 0.07), (0.37, -0.12),
         (0.52, -0.78), (0.47, -0.93), (0.32, -0.97), (0.2, -0.88), (0.05, -0.44), (-0.05, -0.44),
         (-0.2, -0.88), (-0.32, -0.97), (-0.47, -0.93), (-0.52, -0.78), (-0.37, -0.12), (-0.46, 0.07),
         (-0.8, 0.1), (-0.86, 0.24), (-0.74, 0.35), (-0.42, 0.37), (-0.17, 0.32)]
    P += [(0.34 * math.cos(a), 0.64 + 0.34 * math.sin(a)) for a in np.radians(np.linspace(240, -60, 22))]
    return chaikin(np.array(P), 2) * r


def cookie(name, x, y, z, r=1.0, seed=0, bite=False, rot=0.0, parent=None, layer=0.0, flat_=False):
    """Koekmannetje van bruin kraftpapier (hoogte 2r cm): donkere bakrand, wit glazuur aan polsen en enkels,
    oogjes, glimlach en twee snoepknoopjes. bite: er is een hap uit zijn arm."""
    rng = np.random.default_rng(seed + 11)
    shape = gingerbread_outline(r)
    if bite:
        bc = np.array([0.86 * r, 0.3 * r])
        out = []
        for pnt in shape:
            d = np.linalg.norm(pnt - bc)
            out.append(bc + (pnt - bc) / max(d, 1e-6) * r * 0.3 if d < r * 0.3 else pnt)
        shape = np.array(out)
    root = K.empty(name, (x, y, z), (0, 0, math.radians(rot)) if flat_ else (0, math.radians(rot), 0), 1.0, parent)
    kw = dict(plane='xy', z=0.0) if flat_ else {}
    piece(name + '_rand', shape * 1.0, '#8e4b22', root, layer, paper='kraft', jitter=0.004, **kw)
    piece(name + '_koek', shape * 0.9 + np.array([0, 0.02 * r]), '#bf7536', root, layer + 0.5, paper='kraft',
          edge='#d99a5c', jitter=0.004, **kw)
    W = '#fbf6ea'
    for sx in (-1, 1):
        if not (bite and sx == 1):
            piece(f'{name}_glazuurarm{sx}', strip([(sx * 0.6 * r, 0.33 * r), (sx * 0.66 * r, 0.22 * r),
                                                  (sx * 0.6 * r, 0.11 * r)], 0.06 * r), W, root, layer + 1.0,
                  paper='glans', jitter=0.0, **kw)
        piece(f'{name}_glazuurbeen{sx}', strip([(sx * 0.24 * r, -0.72 * r), (sx * 0.33 * r, -0.78 * r),
                                               (sx * 0.42 * r, -0.72 * r)], 0.06 * r), W, root, layer + 1.0,
              paper='glans', jitter=0.0, **kw)
        piece(f'{name}_oog{sx}', circle(sx * 0.11 * r, 0.7 * r, 0.05 * r, 12), '#3a1d10', root, layer + 1.0,
              paper='glans', jitter=0.0, **kw)
    piece(name + '_mond', strip([(-0.12 * r, 0.56 * r), (0, 0.5 * r), (0.12 * r, 0.56 * r)], 0.045 * r), W, root,
          layer + 1.0, paper='glans', jitter=0.0, **kw)
    for i, (by, col) in enumerate(((0.14, '#d9443a'), (-0.12, '#4f9a48'))):
        piece(f'{name}_knoop{i}', circle(0, by * r, 0.08 * r, 14), col, root, layer + 1.0, paper='glans',
              jitter=0.0, **kw)
    return root


def crumbs(name, pts, seed=1, z=0.0012, size=1.0):
    """Kruimels: grillige stukjes kraftpapier (pts in m, plat)."""
    from .papierpop import irregular
    rng = np.random.default_rng(seed)
    polys, cols = [], []
    for i, (x, y) in enumerate(pts):
        polys.append(irregular(x * 100, y * 100, rng.uniform(0.3, 0.6) * size, 6, rng, k=0.3))
        cols.append(['#d39a50', '#b8732f', '#e2b46a', '#3a1d10'][i % 4 if i % 7 else 3])
    tiles(name, polys, cols, paper='mat', plane='xy', z=z, thick=0.0006, edge_mix=0.1)


def sack(name, x, y, z=0.0, s=1.0, cookies_out=3):
    poly = chaikin(np.array([(-3.4, 0), (3.4, 0), (3.8, 3.5), (2.6, 6.2), (1.2, 7.2), (-1.2, 7.2), (-2.6, 6.2),
                             (-3.8, 3.5)]), 3) * s
    card(name, poly, '#c49a63', y, x=x, z=z, paper='kraft', edge='#e2c79c')
    card(name + '_vouw', strip([(-1.5 * s, 6.6 * s), (0, 6.2 * s), (1.5 * s, 6.6 * s)], 0.25 * s), '#8e6840',
         y - 0.0012, x=x, z=z, paper='kraft')
    card(name + '_touw', strip([(-1.9 * s, 6.0 * s), (0, 5.7 * s), (1.9 * s, 6.0 * s)], 0.35 * s), '#efe0b5',
         y - 0.0018, x=x, z=z, paper='crepe')
    for i in range(cookies_out):
        cookie(f'{name}_koek{i}', x + (-1.1 + 1.1 * i) * s * CM, y + 0.0015, z + (7.3 + (i % 2) * 0.5) * s * CM,
               r=0.85 * s, seed=i + 3, rot=(-18 + 18 * i))


def magnifier(name, parent, loc_cm, layer, rot=0.0, s=1.0):
    g = group(name, parent, loc_cm, angle=rot)
    piece(name + '_steel', rrect(0, -2.6 * s, 0.75 * s, 3.4 * s, 0.35 * s), '#c63b33', g, layer, paper='glans')
    ring = np.concatenate([circle(0, 0, 1.8 * s, 48)])
    piece(name + '_ring', ring, '#e8b33c', g, layer + 0.5, paper='folie')
    piece(name + '_lens', circle(0, 0, 1.3 * s, 48), '#d8eef8', g, layer + 0.9, paper='zijde')
    piece(name + '_glim', ellipse(-0.45 * s, 0.45 * s, 0.35 * s, 0.2 * s, 24, rot=40), '#ffffff', g, layer + 1.2,
          paper='glans')
    return g


def medal(name, parent, loc_cm, layer, s=1.0):
    g = group(name, parent, loc_cm)
    piece(name + '_lint', np.array([(-0.7, 1.6), (0.7, 1.6), (0.45, -0.2), (-0.45, -0.2)]) * s, '#3a6fd1', g, layer,
          paper='strepen', col2='#d9443a')
    piece(name + '_munt', circle(0, -0.6 * s, 1.0 * s, 36), '#f0bd3c', g, layer + 0.5, paper='folie')
    piece(name + '_ster', star(0, -0.6 * s, 0.6 * s, 0.26 * s), '#fff0a8', g, layer + 0.9, paper='glans')
    return g


def confetti(name, n, x0, x1, z0, z1, y0, y1, seed=4):
    rng = np.random.default_rng(seed)
    cols = ['#d9443a', '#ffd34d', '#4f9ad9', '#7ab648', '#f27c9b', '#b47ae0']
    for i in range(n):
        poly = rrect(0, 0, rng.uniform(0.5, 0.9), rng.uniform(0.3, 0.5), 0.1) if i % 2 else circle(0, 0, 0.3, 12)
        card(f'{name}{i}', rotate(poly, rng.uniform(0, 180)), cols[i % len(cols)], rng.uniform(y0, y1),
             x=rng.uniform(x0, x1), z=rng.uniform(z0, z1), rot=rng.uniform(-40, 40),
             paper=('folie' if i % 5 == 0 else 'zijde'))


def bunting(name, x0, x1, z, y, n=12, sag=2.5):
    pts = [(x * 100, z * 100 - sag * 4 * t * (1 - t)) for t, x in zip(np.linspace(0, 1, 20), np.linspace(x0, x1, 20))]
    card(name + '_koord', strip(pts, 0.2), '#f3ead8', y, paper='crepe')
    cols = ['#d9443a', '#ffd34d', '#4f9ad9', '#7ab648', '#f27c9b']
    for i in range(n):
        t = (i + 0.5) / n
        x = (x0 + (x1 - x0) * t) * 100
        zz = z * 100 - sag * 4 * t * (1 - t)
        card(f'{name}_vlag{i}', np.array([(x - 1.4, zz), (x + 1.4, zz), (x, zz - 3.0)]), cols[i % len(cols)],
             y - 0.0012, paper=('stippen', 'linnen', 'ruit')[i % 3], col2='#fbf7ef')


def crate(name, x, y, w=8, h=4, d_y=0.0):
    card(name, rrect(0, h / 2, w, h, 0.4), '#c08a58', y, x=x, paper='kraft')
    for k in (h * 0.33, h * 0.66):
        card(f'{name}_lat{k:.1f}', rrect(0, k, w - 0.6, 0.25, 0.1), '#8a5a36', y - 0.001, x=x, paper='kraft')


def table(name, x, y, w=16, h=6.5, depth=2.8):
    """Tafel in zijaanzicht met een boerenbont kleed: plat tafelblad (diepte in cm) waar dingen op staan,
    een recht neerhangende voorkant met witte zoom, poten eronder. Geeft hoogte en voor/achterkant (m)."""
    wood = '#9a6a40'
    for sx in (-1, 1):
        card(f'{name}_poot{sx}', rrect(sx * (w / 2 - 1.4), (h - 2.0) / 2, 1.0, h - 2.0, 0.3), wood, y + 0.004, x=x,
             paper='kraft')
        card(f'{name}_achterpoot{sx}', rrect(sx * (w / 2 - 1.4), (h - 2.0) / 2, 1.0, h - 2.0, 0.3), '#7d5432',
             y + depth * CM - 0.003, x=x, paper='kraft')
    card(name + '_dwarslat', rrect(0, 1.4, w - 3.0, 0.6, 0.2), '#7d5432', y + 0.005, x=x, paper='kraft')
    flat(name + '_blad', rrect(0, depth / 2, w + 1.6, depth, 0.2), '#d9443a', z=h * CM, x=x, y=y, thick=0.0008,
         paper='ruit', col2='#fbf7ef')
    card(name + '_kleed', rrect(0, h - 1.75, w + 1.6, 3.5, 0.2), '#d9443a', y - 0.0004, x=x, paper='ruit',
         col2='#fbf7ef')
    card(name + '_zoom', rrect(0, h - 3.45, w + 1.6, 0.45, 0.15), '#fbf7ef', y - 0.0012, x=x, paper='crepe')
    return dict(top=h * CM, front=y, back=y + depth * CM)


def police_car(name, x, y, z=0.0, facing=1, lights=True, scale=1.0, window_open=True, back_open=False):
    """Nederlandse politieauto in zijaanzicht, op Daan-schaal (36 x 17 cm): wit glanspapier, blauwe band met
    geeloranje bies en schuine blokken op het voorscherm, POLITIE op de voordeur, lichtbalk op het dak.
    De ramen zijn echte openingen: binnenin zit een donkere achterwand, daartussen kan Daan achter het stuur
    zitten (plek 'driver') en Joep achterin ('back'). facing 1 = neus naar rechts."""
    from .papier import strip
    f = facing
    root = K.empty(name, (x, y, z), (0, 0, 0), scale)
    M_ = np.array([f, 1.0])

    def C(nm, poly, col, dy, paper='glans', col2=None, edge=None, jitter=0.006):
        ob = piece(nm, np.asarray(poly, float) * M_, col, root, 0, paper=paper, col2=col2, edge=edge, bend=0.0,
                   jitter=jitter)
        ob.location = (0, dy, 0)
        return ob
    WHITE, BLUE, ORANGE, GREY, DARK = '#f5f6f2', '#1b46a6', '#f07d10', '#9a9ea6', '#24262c'
    # binnenkant (achter de figuren)
    cabin = chaikin(np.array([(10.6, 8.2), (4.9, 15.3), (-11.4, 15.5), (-16.4, 8.2)]), 2)
    C(name + '_binnen', cabin, '#3d4352', 0.012, paper='karton')
    C(name + '_stoel', chaikin(np.array([(-3.6, 8.2), (-3.0, 13.4), (-1.4, 13.6), (-1.6, 8.2)]), 2), '#2a2e38',
      0.0105, paper='linnen')
    C(name + '_stuur', strip([(6.2, 9.2), (7.6, 11.6)], 0.55), '#1c1d22', 0.0035, paper='glans')
    # carrosserie onder de raamlijn
    low = np.array([(-17.4, 2.0), (17.4, 2.0), (18.3, 3.6), (18.2, 6.4), (17.2, 7.5), (10.8, 8.6), (-16.2, 8.6),
                    (-17.8, 7.6), (-18.3, 4.2)])
    C(name + '_carrosserie', chaikin(low, 2), WHITE, 0.0)
    C(name + '_onderkant', rrect(0.0, 1.6, 30.0, 1.8, 0.6), '#2c2e34', 0.004, paper='karton', jitter=0.0)
    # dak en stijlen
    C(name + '_dak', chaikin(np.array([(5.3, 14.7), (4.7, 15.8), (-11.7, 16.0), (-11.6, 14.8)]), 2), WHITE, 0.0)
    C(name + '_astijl', strip([(10.9, 8.4), (4.9, 15.2)], 1.0, cap=False), WHITE, 0.0)
    C(name + '_bstijl', rrect(-2.4, 11.8, 1.0, 6.8, 0.2), WHITE, 0.0)
    C(name + '_cstijl', chaikin(np.array([(-9.4, 8.5), (-9.0, 15.0), (-11.7, 15.9), (-16.6, 8.5)]), 2), WHITE, 0.0)
    C(name + '_raamrubber', strip([(10.4, 8.75), (-9.5, 8.75)], 0.35, cap=False), '#3a3d45', -0.0012,
      paper='karton')
    # ramen: glas tussen carrosserie en figuren (voor- en achterraam kunnen open)
    if not window_open:
        C(name + '_voorraam', np.array([(10.6, 8.5), (5.0, 15.0), (-2.4, 15.0), (-2.4, 8.5)]), '#a6cfea', 0.0015,
          paper='raam', jitter=0.0)
    if not back_open:
        C(name + '_achterraam', np.array([(-2.4, 8.5), (-2.4, 15.0), (-9.6, 15.0), (-9.6, 8.5)]), '#a6cfea', 0.0015,
          paper='raam', jitter=0.0)
    # striping: blauwe band, geeloranje bies, schuine blokken op het voorscherm
    C(name + '_blauw', np.array([(-18.3, 3.5), (17.9, 3.5), (18.2, 5.6), (-18.3, 5.6)]), BLUE, -0.0016)
    C(name + '_oranje', np.array([(-18.2, 5.6), (18.2, 5.6), (18.0, 6.35), (-18.0, 6.35)]), ORANGE, -0.0016)
    for i in range(5):
        x0 = 11.4 + i * 1.3
        C(f'{name}_blok{i}', np.array([(x0, 3.5), (x0 + 0.65, 3.5), (x0 + 1.55, 6.35), (x0 + 0.9, 6.35)]),
          ORANGE if i % 2 == 0 else BLUE, -0.0021, jitter=0.0)
    # deurnaden, grepen, dorpel, spiegel, bumpers, lampen
    C(name + '_naadvoor', strip([(10.5, 8.5), (10.9, 5.5), (10.6, 2.8)], 0.16, cap=False), GREY, -0.0024,
      paper='karton', jitter=0.0)
    C(name + '_naadmidden', rrect(-2.4, 5.6, 0.16, 6.0, 0.05), GREY, -0.0024, paper='karton', jitter=0.0)
    C(name + '_naadachter', strip([(-9.5, 8.5), (-10.4, 5.5), (-10.0, 2.8)], 0.16, cap=False), GREY, -0.0024,
      paper='karton', jitter=0.0)
    for i, dx in enumerate((0.9, -7.6)):
        C(f'{name}_greep{i}', rrect(dx, 7.75, 1.6, 0.42, 0.18), GREY, -0.0026, paper='folie')
    C(name + '_dorpel', rrect(0.0, 2.55, 21.0, 0.9, 0.3), '#7d8189', -0.0012, paper='linnen')
    C(name + '_spiegelvoet', rrect(10.0, 9.1, 0.6, 0.7, 0.1), DARK, -0.0026, paper='karton')
    C(name + '_spiegel', chaikin(np.array([(9.1, 9.3), (11.2, 9.4), (11.0, 10.7), (9.3, 10.6)]), 2), WHITE,
      -0.0032)
    C(name + '_bumpervoor', rrect(17.6, 2.9, 2.2, 1.6, 0.6), '#6f737b', -0.0024, paper='linnen')
    C(name + '_bumperachter', rrect(-17.7, 2.9, 2.2, 1.6, 0.6), '#6f737b', -0.0024, paper='linnen')
    C(name + '_koplamp', chaikin(np.array([(18.2, 6.6), (16.2, 7.3), (16.3, 6.5), (18.3, 5.9)]), 2), '#fff3c4',
      -0.0028, paper='glans')
    C(name + '_achterlicht', chaikin(np.array([(-18.2, 6.0), (-16.8, 6.1), (-16.9, 7.9), (-17.9, 7.8)]), 2),
      '#d63a33', -0.0028)
    # lichtbalk
    C(name + '_balkvoet', rrect(-3.2, 16.3, 8.6, 0.7, 0.25), '#33363e', 0.0004, paper='karton')
    for i, dx in enumerate((-6.2, -0.2)):
        lamp = C(f'{name}_zwaailicht{i}', rrect(dx, 17.15, 2.6, 1.3, 0.5), '#4aa3ff', 0.0, paper='zijde')
        if lights:
            lamp.data.materials[0] = plain_mat('Zwaailicht', '#62b2ff', emit=6.0)
    C(name + '_balkmidden', rrect(-3.2, 17.15, 3.4, 1.1, 0.25), WHITE, -0.0004)
    # wielen
    for i, wx in enumerate((-11.6, 11.4)):
        arch = circle(wx, 3.6, 4.35, 60)
        arch[:, 1] = np.maximum(arch[:, 1], 2.0)
        C(f'{name}_wielkast{i}', arch, '#1e1f24', -0.0008, paper='karton', jitter=0.0)
        C(f'{name}_band{i}', circle(wx, 3.6, 3.6, 60), '#232428', -0.0034, paper='linnen')
        C(f'{name}_velg{i}', circle(wx, 3.6, 2.3, 48), '#cdd1d8', -0.0046, paper='folie')
        for k in range(5):
            C(f'{name}_spaak{i}{k}', rotate(rrect(0, 1.05, 0.5, 1.5, 0.2), k * 72) + np.array([wx, 3.6]), '#8a8e96',
              -0.0054, paper='karton', jitter=0.0)
        C(f'{name}_naaf{i}', circle(wx, 3.6, 0.55, 24), '#9da1a9', -0.006, paper='folie')
    # POLITIE op de voordeur
    K.text_obj(name + '_politie', 'POLITIE', size=1.55 * CM, extrude=0.00012, bevel=0.0,
               mat=plain_mat('Autoletters', BLUE, rough=0.6), parent=root,
               loc=(f * 4.2 * CM, -0.0028, 7.05 * CM), rot=(math.pi / 2, 0, 0), spacing=1.05)
    if lights:
        K.light('POINT', (x - f * 3.2 * CM * scale, y - 0.03, z + 18.0 * CM * scale), None, energy=0.6, size=0.01,
                color=(0.35, 0.6, 1.0))
    s_ = CM * scale
    return dict(root=root, facing=f,
                driver=(x + f * 3.0 * s_, y + 0.006 * scale, z + 1.2 * s_),
                back=(x - f * 6.2 * s_, y + 0.006 * scale, z + 7.2 * s_))


# ------------------------------------------------------------------ binnen
def bedroom(night=False, bed_x=0.1, window_x=-0.12, y_wall=0.16, bed=True, toys=True, w=180):
    """Kinderkamer: behang met stippen, raam met boerenbont gordijnen, houten vloer van stroken, rond kleedje,
    bed met lappendeken van verschillende papiertjes. Geeft maten van bed en kussen terug."""
    wall, dots = ('#bfdcf0', '#e9f4fb') if not night else ('#2c3a73', '#3c4c8c')
    card('Wand', rrect(0, 32, w, 80, 1), wall, y_wall, paper='stippen', col2=dots, jitter=0.0)
    card('Plint', rrect(0, 1.0, w, 2.0, 0.3), '#fbf7ef' if not night else '#8a93b8', y_wall - 0.0012, paper='karton')
    wx = window_x * 100
    card('Raamkozijn', rrect(wx, 30, 21, 23, 1.0), '#fbf7ef' if not night else '#c9cde0', y_wall - 0.0012)
    card('Raamlucht', rrect(wx, 30, 18.5, 20.5, 0.6), '#14204d' if night else '#8cc6ee', y_wall - 0.0024,
         paper='aquarel')
    rng = np.random.default_rng(5)
    if night:
        card('Raammaan', _moon(3.2), '#f6e7a8', y_wall - 0.0036, x=(wx + 4.5) * CM, z=35 * CM, paper='aquarel')
        for i in range(6):
            card(f'Raamster{i}', star(wx + rng.uniform(-7.5, 1), rng.uniform(23, 38), 0.75, 0.32), '#ffe17a',
                 y_wall - 0.0036, paper='folie')
    else:
        cloud('Raamwolk', (wx - 3) * CM, y_wall - 0.004, 33 * CM, 0.42)
        card('Raamboom', radial_union((0, 0), [(-2.5, 0, 3.2, 2.6), (2.0, 0.5, 3.0, 2.8), (0, 2.0, 3.0, 2.4)]),
             '#7fb352', y_wall - 0.0038, x=(wx + 5) * CM, z=21.5 * CM, paper='crepe')
    card('Raamroede1', rrect(wx, 30, 0.7, 20.5, 0.2), '#fbf7ef' if not night else '#c9cde0', y_wall - 0.005)
    card('Raamroede2', rrect(wx, 30, 18.5, 0.7, 0.2), '#fbf7ef' if not night else '#c9cde0', y_wall - 0.005)
    card('Vensterbank', rrect(wx, 18.2, 24, 1.2, 0.3), '#fbf7ef' if not night else '#c9cde0', y_wall - 0.006)
    for sgn in (-1, 1):
        cur = chaikin(np.array([(wx + sgn * 9.0, 43), (wx + sgn * 15.5, 43), (wx + sgn * 16.0, 16),
                                (wx + sgn * 13.0, 17.5), (wx + sgn * 10.5, 22), (wx + sgn * 9.5, 30)]), 2)
        card(f'Gordijn{sgn}', cur, '#e8607a' if not night else '#8f4a7a', y_wall - 0.008, paper='ruit',
             col2='#fbf7ef' if not night else '#c9b8d8')
        card(f'Gordijnband{sgn}', rrect(wx + sgn * 12.0, 24.5, 5.5, 0.8, 0.3), '#f4d36b', y_wall - 0.0092,
             paper='crepe')
    card('Gordijnroede', rrect(wx, 43.6, 38, 0.9, 0.3), '#9a6a40', y_wall - 0.01, paper='kraft')
    # houten vloer van stroken en een rond kleedje
    planks, cols = [], []
    for i, yy in enumerate(np.arange(-80, y_wall * 100 + 1, 3.0)):
        off = (i % 3) * 7
        for xx in np.arange(-w / 2 - off, w / 2, 21):
            planks.append(rrect(xx + 10.5, yy + 1.5, 20.8, 2.85, 0.2, 2))
            cols.append(['#d9a978', '#cf9d6c', '#e0b386', '#c99563'][(i * 3 + int(xx)) % 4] if not night else
                        ['#6d5d72', '#655669', '#74647a', '#5e5063'][(i * 3 + int(xx)) % 4])
    flat('Vloer', rrect(0, (y_wall * 100 - 80) / 2, w, y_wall * 100 + 80, 1), '#8a6440', z=0.0, x=0, y=0,
         thick=0.0006, paper='mat')
    tiles('Planken', planks, cols, paper='mat', plane='xy', z=0.0006, thick=0.0006, edge_mix=0.1)
    for i, (r, col) in enumerate([(15, '#7ab3d9'), (12, '#f4d36b'), (9, '#f2a7b6'), (6, '#7ab648')]):
        flat(f'Kleed{i}', ellipse(0, 0, r, r * 0.62, 64), col if not night else '#4a5a8a', z=0.0014 + i * 0.0005,
             x=-0.03, y=-0.07, paper='brei' if i % 2 == 0 else 'linnen',
             col2=None if i % 2 else '#ffffff')
    info = dict(y_wall=y_wall)
    if bed:
        bx = bed_x * 100
        yb = y_wall - 0.03
        wood = '#b98652' if not night else '#6f5a5e'
        card('Hoofdeind', chaikin(np.array([(bx - 15, 0), (bx - 11, 0), (bx - 11, 17), (bx - 13, 19.5),
                                            (bx - 15, 17)]), 2), wood, yb, paper='kraft')
        card('Hoofdeindknop', circle(bx - 13, 20.2, 1.1, 24), wood, yb - 0.001, paper='kraft')
        card('Voeteind', rrect(bx + 13, 6.5, 3, 13, 1.2), wood, yb - 0.03, paper='kraft')
        card('Bedbak', rrect(bx, 4.5, 26, 5, 0.8), wood, yb - 0.012, paper='kraft')
        card('Matras', rrect(bx, 8.0, 25, 2.6, 0.8), '#fbf7ef' if not night else '#c9cde0', yb - 0.014,
             paper='linnen')
        card('Kussen', ellipse(bx - 9.0, 10.6, 3.8, 2.0), '#fbf7ef' if not night else '#d6d9ea', yb - 0.016,
             paper='linnen')
        kinds = [('stippen', '#7ab3d9', '#ffffff'), ('ruit', '#f2a7b6', '#ffffff'), ('linnen', '#f4d36b', None),
                 ('strepen', '#7ab648', '#fbf7ef'), ('brei', '#b47ae0', '#9a62c8'), ('linnen', '#fbf7ef', None)]
        k = 0
        for i, xx in enumerate(np.arange(bx - 5.0, bx + 12.5, 3.0)):
            for j, zz in enumerate((7.3, 9.8)):
                pk, col, c2 = kinds[(i + 2 * j) % len(kinds)]
                if night:
                    col = {'#7ab3d9': '#4f6aa8', '#f2a7b6': '#8a5a8a', '#f4d36b': '#a89a6a', '#7ab648': '#4f7a5a',
                           '#b47ae0': '#6a4f98', '#fbf7ef': '#9aa0c0'}[col]
                card(f'Lap{k}', rrect(xx, zz, 2.95, 2.45, 0.3), col, yb - 0.018, paper=pk, col2=c2)
                k += 1
        info.update(bed_x=bed_x, bed_y=yb, mattress_z=9.3 * CM, pillow_x=(bx - 9.0) * CM,
                    post=((bx - 13) * CM, yb - 0.002, 21.0 * CM))
    if night:
        bx = bed_x * 100
        yb = y_wall - 0.03
        card('Nachtkastje', rrect(bx - 20.0, 5.5, 6, 11, 0.6), '#8a6a6a', yb + 0.004, paper='kraft')
        card('Lampvoet', rrect(bx - 20.0, 12.5, 1.2, 3, 0.4), '#7ab3d9', yb + 0.002, paper='glans')
        lamp = card('Lampkap', chaikin(np.array([(-2.6, 0), (2.6, 0), (1.7, 2.8), (-1.7, 2.8)]), 2), '#ffd27a',
                    yb + 0.001, x=(bx - 20.0) * CM, z=14 * CM)
        lamp.data.materials[0] = plain_mat('Nachtlampje', '#ffcf7a', emit=5.0)
        K.light('POINT', ((bx - 20.0) * CM, yb - 0.03, 15 * CM), None, energy=2.0, size=0.02,
                color=(1.0, 0.78, 0.45))
    elif toys:
        for i, (col, xx, zz) in enumerate((('#d9443a', -40, 1.6), ('#4f9ad9', -36.6, 1.6), ('#ffd34d', -38.3, 4.8))):
            card(f'Blok{i}', rrect(xx, zz, 3.2, 3.2, 0.4), col, y_wall - 0.05, paper='glans')
            card(f'Blokletter{i}', star(xx, zz, 1.0, 0.45), '#fbf7ef', y_wall - 0.0512, paper='karton')
        card('Bal', circle(-47, 3.0, 3.0, 48), '#f27c9b', y_wall - 0.06, paper='glans')
        card('Balstreep', rrect(-47, 3.0, 6.0, 1.0, 0.4), '#fbf7ef', y_wall - 0.0612, paper='glans')
    return info


def shop(empty=True, y_wall=0.16, w=180):
    """Bakkerij van binnen: tegelwand (één mesh), schappen met broden van kraftpapier, lege bakplaten,
    toonbank met rood-witte strepen, glazen koekjespot. Geeft hoogte en diepte van de toonbank terug."""
    card('Wand', rrect(0, 32, w, 80, 1), '#f2cf7e', y_wall, paper='stippen', col2='#f6dc9c')
    tl, tc = [], []
    for i, x in enumerate(np.arange(-w / 2, w / 2, 4.0)):
        for j, z in enumerate(np.arange(0, 20, 4.0)):
            tl.append(rrect(x + 2, z + 2, 3.8, 3.8, 0.3, 2))
            tc.append('#4f7fc4' if (i + j) % 2 == 0 else '#f7f4ec')
    card('Tegelrand', rrect(0, 20.4, w, 0.9, 0.3), '#2f5d9a', y_wall - 0.0016, paper='glans')
    tiles('Tegels', tl, tc, paper='glans', plane='xz', y=y_wall - 0.0008, thick=0.0006, edge_mix=0.2)
    for z in (24, 31, 38):
        card(f'Schap{z}', rrect(0, z, 52, 1.2, 0.3), '#9a6a40', y_wall - 0.004, paper='kraft')
        for i, x in enumerate(np.linspace(-20, 20, 5)):
            if empty and z < 36:
                card(f'Bakplaat{z}{i}', rrect(x, z + 1.0, 7.0, 0.7, 0.2), '#b7bcc4', y_wall - 0.006, paper='folie')
            else:
                card(f'Brood{z}{i}', ellipse(x, z + 2.4, 3.6, 2.0), '#cf8f4a', y_wall - 0.006, paper='kraft',
                     edge='#e8b878')
                for kk in range(3):
                    card(f'Broodsnee{z}{i}{kk}', strip([(x - 1.5 + kk * 1.5, z + 3.5), (x - 0.9 + kk * 1.5, z + 1.7)],
                                                       0.3), '#f0c890', y_wall - 0.0072, paper='kraft')
    # bord boven de schappen
    card('Bord', rrect(0, 44.5, 34, 6, 1.0), '#5b3b2a', y_wall - 0.004, paper='kraft')
    for i, xx in enumerate((-13.5, 13.5)):
        cookie(f'Bordkoek{i}', xx * CM, y_wall - 0.006, 44.5 * CM, r=2.0, seed=40 + i)
    K.text_obj('Bordtekst', 'KOEKJES', size=3.6 * CM, extrude=0.0002, bevel=0.0,
               mat=plain_mat('Bordletters', '#f6e7c4', rough=0.7), loc=(0, y_wall - 0.0065, 44.5 * CM),
               rot=(math.pi / 2, 0, 0))
    yc = y_wall - 0.09
    card('Toonbank', rrect(0, 5.0, 52, 10, 0.6), '#f4e4c4', yc, paper='linnen')
    for i in range(9):
        card(f'Toonbankpaneel{i}', rrect(-23.1 + i * 5.78, 5.2, 4.6, 7.4, 0.6), '#d9443a', yc - 0.0012,
             paper='linnen')
    card('Toonbankblad', rrect(0, 10.4, 54, 1.1, 0.3), '#9a6a40', yc - 0.002, paper='kraft')
    card('Toonbankplint', rrect(0, 0.6, 52, 1.2, 0.3), '#9a6a40', yc - 0.002, paper='kraft')
    # lege glazen koekjespot op de toonbank
    jar = chaikin(np.array([(-3.0, 0), (3.0, 0), (3.4, 4.8), (2.4, 5.8), (-2.4, 5.8), (-3.4, 4.8)]), 2)
    card('Pot', jar, '#cfe6f2', yc + 0.01, x=0.17, z=10.95 * CM, paper='raam')
    card('Potdeksel', rrect(0, 0, 5.2, 1.0, 0.4), '#d9443a', yc + 0.009, x=0.17, z=17.1 * CM, paper='glans')
    card('Potknop', circle(0, 0, 0.7, 20), '#d9443a', yc + 0.009, x=0.17, z=18.0 * CM, paper='glans')
    crumbs('Potkruimel', [(0.155, yc + 0.012), (0.17, yc + 0.0125), (0.183, yc + 0.012)], seed=8,
           z=10.96 * CM, size=0.7)
    return dict(counter_z=10.9 * CM, counter_y=yc)


# ------------------------------------------------------------------ hulpjes voor de kijkdoos
@contextlib.contextmanager
def scaled(origin, s):
    """Alles wat binnen dit blok wordt gemaakt (zonder ouder) schaalt s keer rond origin (m)."""
    before = set(bpy.data.objects.keys())
    yield
    if abs(s - 1.0) < 1e-6:
        return
    o = np.array(origin, float)
    for nm in set(bpy.data.objects.keys()) - before:
        ob = bpy.data.objects[nm]
        if ob.parent is not None:
            continue
        ob.location = tuple(o + (np.array(ob.location) - o) * s)
        ob.scale = tuple(np.array(ob.scale) * s)


def thread(name, x, y, z0, z1=1.2):
    """Dun wit draadje waaraan wolk of zon in de kijkdoos hangt."""
    card(name, rrect(0, (z0 + z1) * 50, 0.07, (z1 - z0) * 100, 0.03), '#f7f3ea', y + 0.0008, x=x, jitter=0.0,
         paper='karton')


def puff(name, x, y, z, s=1.0, col='#ffffff'):
    """Wolkje (uitlaat, stof, sprong) van zijdepapier."""
    shape = radial_union((0, 0), [(-1.2, 0, 1.3, 1.1), (0.4, 0.5, 1.5, 1.3), (1.5, -0.2, 1.1, 1.0)]) * s
    return card(name, shape, col, y, x=x, z=z, paper='zijde')


def tuft(name, x, y, h=4.0, w=5.0, color='#5f9a3f', seed=0, n=7):
    """Polletje gras van crêpepapier (voor- of achtergrond)."""
    rng = np.random.default_rng(seed)
    pts = [(-w / 2, 0.0)]
    for i in range(n):
        t = (i + 0.5) / n
        pts.append((-w / 2 + w * t + rng.uniform(-0.2, 0.2), h * rng.uniform(0.6, 1.0) * (1 - 0.5 * abs(t - 0.5))))
        pts.append((-w / 2 + w * (i + 1) / n, h * 0.15))
    pts[-1] = (w / 2, 0.0)
    return card(name, np.array(pts), color, y, x=x, paper='crepe')


def leaf(name, x, y, z, L=8.0, W=3.2, rot=0.0, color='#4f9a48', vein='#3d7f3a'):
    """Groot blad van crêpepapier met een nerf (voorgrondkader)."""
    t = np.linspace(0, math.pi, 24)
    top = [(L * (1 - math.cos(a)) / 2, W / 2 * math.sin(a)) for a in t]
    bot = [(L * (1 - math.cos(a)) / 2, -W / 2 * math.sin(a)) for a in t[::-1][1:-1]]
    poly = rotate(np.array(top + bot), rot)
    card(name, poly, color, y, x=x, z=z, paper='crepe')
    card(name + '_nerf', rotate(strip([(0.3, 0), (L * 0.5, 0.1), (L * 0.92, 0)], 0.18), rot), vein, y - 0.0008, x=x,
         z=z, paper='karton')


def speedlines(name, x, y, z, n=4, L=7.0, gap=1.4, col='#ffffff'):
    for i in range(n):
        card(f'{name}{i}', strip([(0, 0), (-(L - i * 1.2), 0)], 0.3), col, y, x=x, z=z + i * gap * CM, paper='zijde')


def pavement(name, x0, x1, y0, y1, kind='klinker', z=0.0, seed=1, w=2.0):
    """Nederlandse straat: 'klinker' = rode klinkers in visgraat, 'tegel' = grijze stoeptegels.
    Eén mesh met voegzand eronder (x, y in m)."""
    rng = np.random.default_rng(seed)
    polys, cols = [], []
    X0, X1, Y0, Y1 = x0 * 100, x1 * 100, y0 * 100, y1 * 100
    if kind == 'klinker':
        pal = ['#73291f', '#7f3024', '#6a261c', '#8a3828', '#5f2219', '#93402e', '#7a2d21']
        R = np.array([[math.cos(math.pi / 4), -math.sin(math.pi / 4)], [math.sin(math.pi / 4), math.cos(math.pi / 4)]])
        cx0, cy0 = (X0 + X1) / 2, (Y0 + Y1) / 2
        span = int(max(X1 - X0, Y1 - Y0) / w) + 4
        g = 0.09
        for k in range(-span // 2 - 2, span // 2 + 2):
            for n in range(-span, span):
                for (bx, by, bw, bh) in ((n + 2 * k, n - 2 * k, 2, 1), (n + 2 * k, n - 2 * k + 1, 1, 2)):
                    c0 = np.array([bx + bw / 2, by + bh / 2]) * w
                    c1 = R @ c0 + np.array([cx0, cy0])
                    if not (X0 - 2 < c1[0] < X1 + 2 and Y0 - 2 < c1[1] < Y1 + 2):
                        continue
                    P = rrect(0, 0, bw * w - g * 2, bh * w - g * 2, 0.18, 2) + c0
                    polys.append((R @ P.T).T + np.array([cx0, cy0]))
                    cols.append(pal[rng.integers(len(pal))])
        base = '#b9a68c'
    else:
        pal = ['#cfcac2', '#c5c0b7', '#d7d2c9', '#bdb8af']
        t = 3.0
        for i, xx in enumerate(np.arange(X0, X1, t)):
            for j, yy in enumerate(np.arange(Y0, Y1, t)):
                polys.append(rrect(xx + t / 2, yy + t / 2, t - 0.16, t - 0.16, 0.25, 2))
                cols.append(pal[rng.integers(len(pal))])
        base = '#9f9a92'
    flat(name + '_voeg', rrect((X0 + X1) / 2, (Y0 + Y1) / 2, X1 - X0, Y1 - Y0, 0.3), base, z=z, thick=0.0006,
         paper='mat')
    return tiles(name, polys, cols, paper='mat', plane='xy', z=z + 0.0006, thick=0.0007, edge_mix=0.12)


def fence(name, x0, x1, y, h=8.0, color='#fbf7ef'):
    """Wit tuinhekje: latjes met punt en twee dwarslatten (één mesh)."""
    polys, cols = [], []
    for xx in np.arange(x0 * 100, x1 * 100, 2.6):
        polys.append(np.array([(xx - 0.8, 0), (xx + 0.8, 0), (xx + 0.8, h - 0.9), (xx, h), (xx - 0.8, h - 0.9)]))
        cols.append(color)
    for zz in (h * 0.3, h * 0.7):
        polys.append(rrect((x0 + x1) * 50, zz, (x1 - x0) * 100, 0.9, 0.2, 2))
        cols.append('#e9e2d2')
    return tiles(name, polys, cols, paper='karton', plane='xz', y=y, thick=0.0008, edge_mix=0.2)


def windmill(name, x, y, s=1.0, rot=12.0):
    """Hollandse molen van papier: romp, kap, stelling, wieken van latjes."""
    body = np.array([(-4.2, 0), (4.2, 0), (2.6, 16), (-2.6, 16)]) * s
    card(name + '_romp', body, '#6d5a4f', y, x=x, paper='kraft')
    card(name + '_stelling', rrect(0, 6.0 * s, 11.0 * s, 0.6 * s, 0.2), '#4a3b33', y - 0.0012, x=x, paper='kraft')
    card(name + '_deur', rrect(0, 1.6 * s, 2.0 * s, 3.2 * s, 0.6 * s), '#2f4a3a', y - 0.0012, x=x, paper='linnen')
    card(name + '_raam', rrect(0, 10.5 * s, 1.4 * s, 1.8 * s, 0.4 * s), '#fbf7ef', y - 0.0012, x=x)
    card(name + '_kap', chaikin(np.array([(-3.2, 15.4), (3.2, 15.4), (2.4, 18.4), (0, 19.2), (-2.4, 18.4)]) * s, 2),
         '#3e4a5a', y - 0.0006, x=x, paper='golf')
    hub = np.array([0, 17.0 * s])
    for k in range(4):
        a = rot + k * 90
        arm = rotate(rrect(0, 7.5 * s, 0.5 * s, 15 * s, 0.2), a) + hub
        card(f'{name}_roe{k}', arm, '#4a3b33', y - 0.0025, x=x, paper='kraft')
        sail = rotate(np.array([(0.3, 2.5), (2.6, 2.5), (2.6, 14.0), (0.3, 14.0)]) * s, a) + hub
        card(f'{name}_zeil{k}', sail, '#f3ead8', y - 0.0032, x=x, paper='linnen')
        for j in range(1, 6):
            bar = rotate(rrect(1.45, 2.5 + j * 2.0, 2.4, 0.18, 0.05), a) * s + hub
            card(f'{name}_lat{k}{j}', bar, '#4a3b33', y - 0.004, x=x, paper='karton', jitter=0.0)
    card(name + '_as', circle(0, 17.0 * s, 0.7 * s, 20), '#2a2b30', y - 0.005, x=x, paper='glans')


def bench(name, x, y, w=14):
    card(name + '_leuning', rrect(0, 7.5, w, 1.4, 0.3), '#9a6a40', y, x=x, paper='kraft')
    card(name + '_zitting', rrect(0, 4.5, w + 1, 1.2, 0.3), '#8a5a36', y - 0.0015, x=x, paper='kraft')
    for sx in (-1, 1):
        card(f'{name}_poot{sx}', rrect(sx * (w / 2 - 1.5), 2.6, 0.9, 5.2, 0.2), '#3a3d45', y - 0.003, x=x,
             paper='glans')


def lamppost(name, x, y, h=30):
    card(name + '_paal', rrect(0, h / 2, 1.0, h, 0.3), '#2f3a4a', y, x=x, paper='glans')
    card(name + '_kap', chaikin(np.array([(-2.2, h), (2.2, h), (1.4, h + 3.2), (-1.4, h + 3.2)]), 2), '#2f3a4a',
         y - 0.0012, x=x, paper='glans')
    card(name + '_glas', rrect(0, h + 1.5, 2.6, 2.4, 0.4), '#fff1c4', y - 0.0018, x=x, paper='zijde')


def road(name, x0, x1, y0, y1, dash=True):
    """Polderweggetje: grijs asfaltpapier met witte streepjes."""
    flat(name, rrect((x0 + x1) * 50, (y0 + y1) * 50, (x1 - x0) * 100, (y1 - y0) * 100, 0.3), '#7d7f84', z=0.0004,
         thick=0.0008, paper='mat')
    if dash:
        polys = [rrect(xx, (y0 + y1) * 50, 4.0, 0.5, 0.15, 2) for xx in np.arange(x0 * 100, x1 * 100, 7.0)]
        tiles(name + '_streep', polys, ['#f4f1ea'] * len(polys), paper='mat', plane='xy', z=0.0012, thick=0.0004)


def grassland(name='Gras', y0=-0.6, y1=0.5, w=200, color='#86bb5a'):
    flat(name, rrect(0, (y0 + y1) * 50, w, (y1 - y0) * 100, 1), color, z=0.0, thick=0.001, paper='linnen')


def big_tree(name, x, y, h=36.0, apples=7):
    """Grote parkboom: stam van kraftpapier met schorslijnen, twee takken, kruin van crepepapier met appels."""
    card(name + '_stam', chaikin(np.array([(-4.2, 0), (4.4, 0), (3.0, 4), (2.6, h), (-2.6, h), (-3.0, 4)]), 2),
            '#8a5a36', y, x=x, paper='kraft')
    for i, (x0, z0, z1) in enumerate(((-1.2, 3, 12), (1.0, 8, 19), (-0.6, 17, 27), (1.3, 24, 33))):
        card(f'{name}_schors{i}', strip([(x0, z0), (x0 + 0.4, (z0 + z1) / 2), (x0 - 0.2, z1)], 0.35), '#6b4428',
                y - 0.0012, x=x, paper='kraft')
    card(name + '_tak0', strip([(1.5, h - 6), (9, h + 1), (14, h + 3)], 2.0), '#8a5a36', y + 0.001, x=x,
            paper='kraft')
    card(name + '_tak1', strip([(-1.5, h - 3), (-10, h + 3), (-15, h + 3.5)], 1.8), '#8a5a36', y + 0.001, x=x,
            paper='kraft')
    lobes = [(0, h + 9, 17, 11), (-14, h + 4, 9, 7), (14, h + 5, 10, 8), (-7, h + 15, 9, 7), (8, h + 16, 10, 7)]
    crown = radial_union((0, h + 8), lobes, n=160)
    card(name + '_kruinachter', crown * 1.03 + np.array([0.8, -0.6]), '#4d8f38', y + 0.004, x=x, paper='karton')
    card(name + '_kruin', crown, '#5fa344', y + 0.002, x=x, paper='crepe')
    rng = np.random.default_rng(3)
    for i in range(apples):
        a = rng.uniform(np.pi * 1.08, np.pi * 1.92)
        d = rng.uniform(0.3, 0.75)
        card(f'{name}_appel{i}', circle(np.cos(a) * 13 * d, h + 8 + np.sin(a) * 8 * d, 1.1, 24), '#c4271d',
                y - 0.0005, x=x, paper='karton')
