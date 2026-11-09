"""Rekwisieten: koekjes, kruimels, zak, vergrootglas, medaille, confetti, politieauto, meubels."""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler
from . import core as K, mats as M, body as B
from .core import gauss, smoothstep
from .body import nrm

_P = {}


def prop_mats(base=None):
    if _P:
        return _P
    _P.update({
        'cookie': M.cookie('Koek', '#d9a056', '#9a5524'),
        'cookie_light': M.cookie('Boterkoek', '#e8bf78', '#b77a36'),
        'choc': M.simple('Chocolade', '#3a1d0e', rough=0.35, coat=0.2),
        'cake': M.cookie('Cake', '#e6b46e', '#b97a3c'),
        'fondant': M.simple('Roze glazuur', '#f08aa6', rough=0.22, coat=0.6, sss=0.25),
        'sugar': M.simple('Suiker', '#fff6ec', rough=0.3, sss=0.3),
        'burlap': M.burlap('Jute', '#b48c58'),
        'rope': M.fabric('Touw', '#a0794a', rough=0.9, weave=300, strength=0.6),
        'glass': M.glass('Glas lens', '#ffffff', 0.0, 1.5),
        'thin_glass': M.thin_glass('Ruit'),
        'wood': M.wood('Hout', '#b9804a', '#8a5530'),
        'wood_light': M.wood('Licht hout', '#e0b583', '#c08f5c', rough=0.5),
        'brass': M.gold('Messing', '#c9a14a', 0.25),
        'gold': M.gold('Medaillegoud', '#f1be45', 0.15),
        'ribbon_r': M.fabric('Lint rood', '#c8283a', rough=0.5, sheen=0.8, weave=1400),
        'ribbon_w': M.fabric('Lint wit', '#f4f1ea', rough=0.5, sheen=0.8, weave=1400),
        'ribbon_b': M.fabric('Lint blauw', '#24459c', rough=0.5, sheen=0.8, weave=1400),
        'car_white': M.painted('Autolak wit', '#f4f6f8', rough=0.18, var=0.01, coat=1.0, bump=0.0),
        'car_blue': M.painted('Autolak blauw', '#1d3f9e', rough=0.2, var=0.01, coat=1.0, bump=0.0),
        'car_orange': M.painted('Autolak oranje', '#f08a1c', rough=0.2, var=0.01, coat=1.0, bump=0.0),
        'chrome': M.gold('Chroom', '#d9dde3', 0.08),
        'tire': M.simple('Band', '#1b1b1d', rough=0.75, bump=0.2, bump_scale=200),
        'hub': M.painted('Velg', '#e8eaee', rough=0.25, coat=0.8, bump=0.0),
        'siren': M.emission('Zwaailicht', '#2f6bff', 30.0),
        'siren_glass': M.glass('Zwaailichtkap', '#5d8cff', 0.05, 1.45),
        'headlight': M.emission('Koplamp', '#fff1d6', 6.0),
        'taillight': M.emission('Achterlicht', '#ff2a1a', 3.0),
        'seat': M.fabric('Stoel', '#2a2c33', rough=0.8, weave=600),
        'dash': M.simple('Dashboard', '#25262b', rough=0.5),
        'confetti': M.vertex_colored('Confetti', rough=0.4, bump=0.0, coat=0.3),
        'white': M.simple('Wit', '#f8f6f2', rough=0.35, coat=0.3),
        'plate': M.simple('Bord', '#fbf9f4', rough=0.12, coat=1.0),
        'cloth_check': None,
    })
    g = M.NT('Tafelkleed ruit')
    co = g.coord('Object')
    x, y, z = g.sep(co)
    a = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', x, 31.4)), 0.0)
    b = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', y, 31.4)), 0.0)
    f = g.math('MULTIPLY', g.math('ADD', a, b), 0.5)
    col = g.ramp(f, [(0.0, K.srgb('#fbf7ee')), (0.5, K.srgb('#e98f8f')), (1.0, K.srgb('#cf3f45'))])
    p = g.principled(color=col, rough=0.8, sheen=0.6)
    g.set(p, 'Normal', g.bump(g.wave(co, 900, 'BANDS', 'X'), 0.15, 0.001))
    _P['cloth_check'] = g.done(p)
    return _P


# ------------------------------------------------------------------ koekjes
def cookie(name, kind='choc', r=0.035, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), seed=0, bite=0.0):
    m = prop_mats()
    rng = np.random.default_rng(seed)
    root = K.empty(name, loc, rot, 1.0, parent)
    ph = rng.random(3) * 10

    def lumpy(D, P):
        P = P.copy()
        top = smoothstep(0.0, 0.6, D[:, 2])
        n = (np.sin(D[:, 0] * 9 + ph[0]) * np.sin(D[:, 1] * 8 + ph[1]) + np.sin(D[:, 0] * 17 + D[:, 1] * 13 + ph[2]) * 0.5)
        P[:, 2] += top * n * r * 0.04
        rr = np.sqrt(D[:, 0] ** 2 + D[:, 1] ** 2)
        P[:, :2] *= (1 + 0.04 * np.sin(np.arctan2(D[:, 1], D[:, 0]) * 7 + ph[0]))[:, None]
        if bite > 0:
            bc = np.array([0.9, 0.3])
            dd = np.sqrt((D[:, 0] - bc[0]) ** 2 + (D[:, 1] - bc[1]) ** 2)
            cut = smoothstep(bite, bite * 0.6, dd)
            P[:, :2] -= (P[:, :2] / (np.linalg.norm(P[:, :2], axis=1, keepdims=True) + 1e-9)) * (cut * r * 0.45)[:, None]
        return P

    rim_fn = lambda D, P: {'rim': ('POINT', smoothstep(0.55, 0.98, np.sqrt(D[:, 0] ** 2 + D[:, 1] ** 2)) *
                                    (1 - smoothstep(0.3, 0.9, D[:, 2])))}
    if kind == 'choc':
        K.blob(name + '_deeg', (r, r, r * 0.27), 2.4, (48, 24), deform=lumpy, mat=m['cookie'], parent=root,
               attrs_fn=rim_fn)
        for i in range(9):
            a = rng.random() * 2 * math.pi
            d = math.sqrt(rng.random()) * r * 0.72
            s = r * (0.11 + 0.06 * rng.random())
            K.blob(name + f'_chip{i}', (s, s * 0.9, s * 0.7), 2.6, (12, 8), mat=m['choc'], parent=root,
                   loc=(math.cos(a) * d, math.sin(a) * d, r * 0.22), rot=tuple(rng.random(3) * 0.8))
    elif kind == 'roze':
        K.blob(name + '_cake', (r, r, r * 0.3), 3.0, (48, 20), mat=m['cake'], parent=root, attrs_fn=rim_fn)

        def icing(D, P):
            P = P.copy()
            P[:, 2] = np.maximum(P[:, 2], -r * 0.02)
            return P

        K.blob(name + '_glazuur', (r * 1.0, r * 1.0, r * 0.2), 2.4, (48, 20), deform=icing, mat=m['fondant'],
               parent=root, loc=(0, 0, r * 0.2))
    elif kind == 'ster':
        st = K.poly_obj(name + '_ster', K.round_star_pts(r * 1.15, 0.58, seg=8, round_=0.3), depth=r * 0.14,
                        bevel=r * 0.1, mat=m['cookie_light'], parent=root)
        st.data.bevel_resolution = 5
        for i in range(14):
            a = rng.random() * 2 * math.pi
            d = math.sqrt(rng.random()) * r * 0.5
            K.blob(name + f'_suiker{i}', (r * 0.04,) * 3, 2, (8, 6), mat=m['sugar'], parent=root,
                   loc=(math.cos(a) * d, math.sin(a) * d, r * 0.25))
    return root


def crumbs(name, pts, sizes, parent=None, seed=1, mat=None):
    """Kruimels als één mesh: pts (n,3), sizes (n,)."""
    m = prop_mats()
    rng = np.random.default_rng(seed)
    D, F = K.sph(8, 6)
    Vs, Fs = [], []
    off = 0
    F = np.array([f if len(f) == 4 else (f[0], f[1], f[2], f[2]) for f in F])
    for p, s in zip(pts, sizes):
        sc = s * (0.6 + 0.8 * rng.random(3))
        P = D * sc * (0.75 + 0.5 * rng.random((len(D), 1)))
        R = Euler(tuple(rng.random(3) * 6.28)).to_matrix()
        P = P @ np.array(R).T + p
        Vs.append(P)
        Fs.append(F + off)
        off += len(D)
    V = np.concatenate(Vs)
    Fa = np.concatenate(Fs)
    Fl = [tuple(f) if f[2] != f[3] else (f[0], f[1], f[2]) for f in Fa.tolist()]
    return K.mesh_obj(name, V, Fl, mat or m['cookie'], parent,
                      attrs={'rim': ('POINT', rng.random(len(V)) * 0.6)})


def sack(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), size=0.32, open_=True, seed=3, cookies_in=6):
    m = prop_mats()
    rng = np.random.default_rng(seed)
    root = K.empty(name, loc, rot, 1.0, parent)
    ph = rng.random(4) * 6

    def deform(D, P):
        P = P.copy()
        z = D[:, 2]
        # breed onder, ingesnoerd boven
        w = 1.0 + 0.12 * smoothstep(0.3, -0.6, z) - 0.55 * smoothstep(0.35, 0.95, z)
        P[:, 0] *= w
        P[:, 1] *= w
        P[:, 2] = np.where(z < -0.7, -size * 0.62 - (z + 0.7) * size * 0.08, P[:, 2])
        a = np.arctan2(D[:, 1], D[:, 0])
        wr = np.sin(a * 5 + ph[0]) * 0.035 + np.sin(a * 11 + ph[1] + z * 4) * 0.02
        P[:, :2] *= (1 + wr * smoothstep(-0.8, 0.9, z))[:, None]
        return P

    K.blob(name + '_zak', (size * 0.55, size * 0.5, size * 0.62), 2.0, (64, 40), deform=deform, mat=m['burlap'],
           parent=root, loc=(0, 0, size * 0.62))
    # hals en touw
    neck_z = size * 1.18
    K.lathe(name + '_hals', [(size * 0.14, neck_z - 0.02), (size * 0.12, neck_z + 0.03), (size * 0.2, neck_z + 0.09),
                             (size * 0.24, neck_z + 0.12)], 32, m['burlap'], root, close_top=False, close_bot=False)
    A = np.linspace(0, 2 * math.pi, 25)
    pts = [(math.cos(a) * size * 0.125, math.sin(a) * size * 0.125, neck_z + 0.012) for a in A]
    K.curve_tube(name + '_touw', pts, 0.006, m['rope'], root, cyclic=False)
    if open_:
        kinds = ['choc', 'roze', 'ster']
        for i in range(cookies_in):
            a = i / max(cookies_in, 1) * 6.28 + rng.random()
            cookie(name + f'_koek{i}', kinds[i % 3], 0.033, root,
                   loc=(math.cos(a) * size * 0.1, math.sin(a) * size * 0.1, neck_z + 0.07 + 0.02 * (i % 2)),
                   rot=(0.9 + rng.random() * 0.5, rng.random() * 0.6, a), seed=i)
    return root


def magnifier(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), r=0.06):
    m = prop_mats()
    root = K.empty(name, loc, rot, 1.0, parent)
    # ring
    A = np.linspace(0, 2 * math.pi, 64, endpoint=False)
    pts = [(math.cos(a) * r, 0, math.sin(a) * r) for a in A]
    ob, _ = K.tube(name + '_ring', np.vstack([pts, pts[:3]]), [[0.007, 0.012]] * (len(pts) + 3), m['brass'], root,
                   ring=16, per=3, up=(0, 1, 0), caps=(False, False))
    # lens (bolle schijf)
    K.blob(name + '_lens', (r * 0.98, r * 0.12, r * 0.98), 2.0, (48, 24), mat=m['glass'], parent=root)
    # steel
    K.tube(name + '_steel', [(0, 0, -r - 0.004), (0, 0, -r - 0.03), (0, 0, -r - 0.11)], [0.011, 0.012, 0.013],
           m['wood'], root, ring=20, per=4)
    K.tube(name + '_bus', [(0, 0, -r - 0.004), (0, 0, -r - 0.026)], [0.0125, 0.0125], m['brass'], root, ring=20,
           per=2)
    return root


def medal(name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), r=0.035, ribbon_len=0.12):
    m = prop_mats()
    root = K.empty(name, loc, rot, 1.0, parent)
    K.blob(name + '_munt', (r, r * 0.16, r), 3.0, (40, 16), mat=m['gold'], parent=root)
    st = K.poly_obj(name + '_ster', K.round_star_pts(r * 0.62, 0.5), depth=r * 0.06, bevel=r * 0.05,
                    mat=m['gold'], parent=root, loc=(0, -r * 0.17, 0), rot=(math.pi / 2, 0, 0))
    # lint in drie banen
    for i, mt in enumerate(('ribbon_r', 'ribbon_w', 'ribbon_b')):
        x = (i - 1) * r * 0.36
        pts = [(x, 0, r * 0.9), (x * 1.3, 0.003, r + ribbon_len * 0.5), (x * 1.6, 0.0, r + ribbon_len)]
        K.tube(name + f'_lint{i}', pts, [[r * 0.18, 0.0012]] * 3, m[mt], root, ring=8, per=4, up=(0, 1, 0))
    return root


def confetti(name, n, box, parent=None, seed=4, size=0.012):
    m = prop_mats()
    rng = np.random.default_rng(seed)
    cols = [K.srgb(c)[:3] for c in ('#e94b4b', '#f6c544', '#3fa7e8', '#5dc46b', '#f07ad0', '#ffffff', '#ff8d2e')]
    lo, hi = np.array(box[0]), np.array(box[1])
    V, F, C = [], [], []
    for i in range(n):
        c = lo + (hi - lo) * rng.random(3)
        R = np.array(Euler(tuple(rng.random(3) * 6.28)).to_matrix())
        w, h = size * (0.6 + 0.6 * rng.random()), size * (1.0 + 0.8 * rng.random())
        quad = np.array([[-w, -h, 0], [w, -h, 0], [w, h, 0], [-w, h, 0]]) @ R.T + c
        # licht gebogen
        quad[1] += R[:, 2] * w * 0.3
        quad[2] += R[:, 2] * w * 0.3
        k = len(V)
        V.extend(quad)
        F.append((k, k + 1, k + 2, k + 3))
        col = cols[rng.integers(len(cols))]
        C.extend([col] * 4)
    ob = K.mesh_obj(name, np.array(V), F, m['confetti'], parent, attrs={'col': ('POINT', np.array(C))})
    K.solidify(ob, size * 0.05, 0.0)
    return ob


def plate(name, parent=None, loc=(0, 0, 0), r=0.13):
    m = prop_mats()
    return K.lathe(name, [(0.0, 0.0), (r * 0.6, 0.0), (r * 0.66, 0.004), (r * 0.7, 0.008), (r * 0.95, 0.016),
                          (r, 0.02), (r * 0.98, 0.022), (r * 0.9, 0.014), (r * 0.62, 0.01), (0.0, 0.01)], 64,
                   m['plate'], parent, close_top=False, close_bot=False) if False else _plate(name, parent, loc, r)


def _plate(name, parent, loc, r):
    m = prop_mats()
    prof = [(0.0, 0.0), (r * 0.6, 0.0), (r * 0.66, 0.006), (r * 0.72, 0.01), (r * 0.95, 0.018), (r, 0.022),
            (r * 0.97, 0.025), (r * 0.9, 0.018), (r * 0.65, 0.012), (0.0, 0.012)]
    ob = K.lathe(name, prof, 72, m['plate'], parent, close_top=False, close_bot=False)
    ob.location = loc
    return ob


# ------------------------------------------------------------------ politieauto
def police_car(name, parent=None, loc=(0, 0, 0), yaw=0.0, wheel_spin=0.0, lights_on=True, door_open=False,
               scale=0.62, convertible=True):
    """Mollige politieauto op kindermaat (open, met rolbeugel en zwaailichtbalk) in Nederlandse striping.
    Ontwerpmaat 2,1 m, standaard geschaald naar ca. 1,3 m. Kijkt naar -y."""
    m = prop_mats()
    root = K.empty(name, loc, (0, 0, yaw), scale, parent)
    L, W, H = 1.05, 0.62, 0.36  # halve maten onderbak

    def body_def(D, P):
        P = P.copy()
        # voorkant iets lager, achterkant bol
        P[:, 2] -= 0.06 * smoothstep(0.0, -0.9, D[:, 1]) * (D[:, 2] > 0)
        # wielkasten: inham boven de wielen
        for wy in (-0.62, 0.62):
            for s in (-1, 1):
                d = np.sqrt(((D[:, 1] - wy) / 0.26) ** 2 + ((D[:, 2] + 0.55) / 0.5) ** 2)
                P[:, 0] -= s * (D[:, 0] * s > 0.5) * smoothstep(1.0, 0.6, d) * 0.04
        return P

    body = K.blob(name + '_bak', (W, L, H), 3.2, (96, 48), deform=body_def, mat=m['car_white'], parent=root,
                  loc=(0, 0, 0.47))
    # striping: blauwe band met oranje lijn, als aparte schillen over de flanken
    for mat, z0, z1, off in (('car_blue', -0.55, -0.05, 0.004), ('car_orange', -0.05, 0.08, 0.004)):
        D, F = K.sph(96, 48)
        P = body_def(D, K.superdir(D, 3.2) * np.array([W, L, H]))
        keep = (D[:, 2] > z0) & (D[:, 2] < z1) & (np.abs(D[:, 0]) > 0.35)
        Fk = [f for f in F if all(keep[i] for i in f)]
        used = sorted({i for f in Fk for i in f})
        rm = {o: n for n, o in enumerate(used)}
        V = P[used] + (P[used] / np.linalg.norm(P[used], axis=1, keepdims=True)) * off
        ob = K.mesh_obj(name + '_streep' + mat, V, [tuple(rm[i] for i in f) for f in Fk], m[mat], root,
                        loc=(0, 0, 0.47))
    # open kuip: zachte rand rond de zitplaats
    rim = []
    for a in np.linspace(0, 2 * math.pi, 49):
        rim.append((math.cos(a) * W * 0.8, 0.22 + math.sin(a) * 0.5, 0.84))
    K.curve_tube(name + '_kuiprand', rim, 0.035, m['seat'], root)
    K.blob(name + '_kuip', (W * 0.78, 0.48, 0.05), 3, (48, 16), mat=m['seat'], parent=root, loc=(0, 0.22, 0.8))
    # rolbeugel achter de stoelen met de zwaailichtbalk erop
    arch = [(-W * 0.82, 0.72, 0.8), (-W * 0.8, 0.72, 1.25), (-W * 0.5, 0.72, 1.42), (W * 0.5, 0.72, 1.42),
            (W * 0.8, 0.72, 1.25), (W * 0.82, 0.72, 0.8)]
    K.tube(name + '_rolbeugel', arch, [0.035] * 6, m['chrome'], root, ring=16, per=8)
    # voorruit
    ws = K.grid_mesh(name + '_voorruit', 8, 8, lambda U, V: np.stack([(U - 0.5) * 2 * W * 0.7,
                                                                      -0.32 + 0.1 * V - 0.05 * np.sin(U * 3.14),
                                                                      0.84 + 0.22 * V], 1), m['thin_glass'], root)
    wsr = []
    for t in np.linspace(0, 1, 20):
        wsr.append(((t - 0.5) * 2 * W * 0.7, -0.22 - 0.05 * math.sin(t * 3.14), 1.06))
    K.curve_tube(name + '_ruitrand', wsr, 0.018, m['chrome'], root)
    # zwaailichtbalk
    K.blob(name + '_balk', (0.42, 0.12, 0.05), 4.0, (40, 16), mat=m['car_white'], parent=root, loc=(0, 0.72, 1.47))
    for s in (-1, 1):
        K.blob(name + f'_lamp{s}', (0.16, 0.1, 0.08), 2.4, (32, 20), mat=m['siren'] if lights_on else m['siren_glass'],
               parent=root, loc=(s * 0.22, 0.72, 1.53))
        K.blob(name + f'_lampkap{s}', (0.17, 0.11, 0.09), 2.4, (32, 20), mat=m['siren_glass'], parent=root,
               loc=(s * 0.22, 0.72, 1.535))
    # wielen
    wheels = []
    for wy in (-0.62, 0.62):
        for s in (-1, 1):
            w = K.empty(name + f'_wiel{s}{wy}', (s * (W - 0.02), wy, 0.27), (0, wheel_spin, 0), 1.0, root)
            tire = K.blob(name + f'_band{s}{wy}', (0.12, 0.27, 0.27), 2.6, (48, 24), mat=m['tire'], parent=w)
            hub = K.blob(name + f'_velg{s}{wy}', (0.06, 0.16, 0.16), 2.2, (32, 20), mat=m['hub'], parent=w,
                         loc=(s * 0.08, 0, 0))
            for k in range(5):
                a = k / 5 * 2 * math.pi
                K.blob(name + f'_moer{s}{wy}{k}', (0.015, 0.018, 0.018), 2, (8, 6), mat=m['chrome'], parent=w,
                       loc=(s * 0.135, math.cos(a) * 0.075, math.sin(a) * 0.075))
            wheels.append(w)
    # koplampen, bumpers, grille
    for s in (-1, 1):
        K.blob(name + f'_koplamp{s}', (0.09, 0.05, 0.08), 2.2, (24, 16), mat=m['headlight'], parent=root,
               loc=(s * 0.38, -L - 0.005, 0.56))
        K.blob(name + f'_koplamprand{s}', (0.105, 0.04, 0.095), 2.2, (24, 16), mat=m['chrome'], parent=root,
               loc=(s * 0.38, -L + 0.012, 0.56))
        K.blob(name + f'_achterlicht{s}', (0.07, 0.04, 0.09), 3, (20, 12), mat=m['taillight'], parent=root,
               loc=(s * 0.42, L - 0.01, 0.6))
    for sy in (-1, 1):
        K.blob(name + f'_bumper{sy}', (W * 0.95, 0.07, 0.065), 3.0, (48, 16), mat=m['chrome'], parent=root,
               loc=(0, sy * (L + 0.02), 0.32))
    # tekst POLITIE op de flanken en de neus
    for s in (-1, 1):
        t = K.text_obj(name + f'_tekst{s}', 'POLITIE', size=0.17, extrude=0.004, bevel=0.002, mat=m['car_blue'],
                       parent=root, loc=(s * (W + 0.012), 0.0, 0.72), rot=(math.pi / 2, 0, s * math.pi / 2))
    K.text_obj(name + '_neustekst', 'POLITIE', size=0.13, extrude=0.003, bevel=0.0015, mat=m['car_blue'], parent=root,
               loc=(0, -0.75, 0.8), rot=(math.radians(72), 0, 0))
    # stoelen en stuur
    for s in (-1, 1):
        K.blob(name + f'_stoel{s}', (0.24, 0.2, 0.07), 3, (24, 12), mat=m['seat'], parent=root, loc=(s * 0.28, 0.38, 0.84))
        K.blob(name + f'_leuning{s}', (0.24, 0.07, 0.26), 3, (24, 12), mat=m['seat'], parent=root, loc=(s * 0.28, 0.6, 1.08))
    K.blob(name + '_dashboard', (W * 0.8, 0.12, 0.08), 3, (32, 12), mat=m['dash'], parent=root, loc=(0, -0.28, 0.9))
    A = np.linspace(0, 2 * math.pi, 40)
    st = K.empty(name + '_stuur', (0.28, -0.08, 1.04), (math.radians(-55), 0, 0), 1.0, root)
    pts = [(math.cos(a) * 0.14, math.sin(a) * 0.14, 0) for a in A]
    K.curve_tube(name + '_stuurring', pts, 0.02, m['dash'], st, cyclic=False)
    K.tube(name + '_stuuras', [(0.28, -0.08, 1.04), (0.28, -0.26, 0.92)], [0.022, 0.022], m['dash'], root, ring=12, per=2)
    root['seat_l'] = (0.28 * scale, 0.38 * scale, 0.9 * scale)
    root['seat_r'] = (-0.28 * scale, 0.38 * scale, 0.9 * scale)
    root['wheel_hand'] = (0.28 * scale, -0.08 * scale, 1.04 * scale)
    return root, wheels
