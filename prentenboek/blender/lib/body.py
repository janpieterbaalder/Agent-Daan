"""Lichaamsdelen: IK, handen, schoenen, en de politiepet. Alle maten in meters (behalve de pet:
die wordt in hoofd-eenheden gebouwd en door de aanroeper geschaald)."""
import math
import numpy as np
from mathutils import Vector, Matrix
from . import core as K
from .core import smoothstep


def nrm(v):
    v = np.asarray(v, dtype=float)
    return v / (np.linalg.norm(v) + 1e-12)


def ik2(S, W, a, b, pole, stretch=1.0):
    """Twee-botten-IK: schouder S, doel W, lengtes a, b, poolrichting -> elleboog E en (bereikbaar) W.
    stretch > 1: rekbare ledematen (cartoon) tot die factor als het doel buiten bereik ligt."""
    S, W, pole = map(lambda v: np.asarray(v, dtype=float), (S, W, pole))
    d = W - S
    L = np.linalg.norm(d)
    if stretch > 1.0 and L > (a + b) * 0.97:
        f = min(L / ((a + b) * 0.97), stretch)
        a, b = a * f, b * f
    L2 = min(max(L, abs(a - b) + 1e-4), a + b - 1e-4)
    dn = d / (L + 1e-12)
    W = S + dn * L2
    x = (a * a - b * b + L2 * L2) / (2 * L2)
    h = math.sqrt(max(a * a - x * x, 0))
    p = pole - dn * np.dot(pole, dn)
    if np.linalg.norm(p) < 1e-6:
        p = np.cross(dn, [1, 0, 0])
    p = nrm(p)
    E = S + dn * x + p * h
    return E, W


def frame_from(F, Pn):
    """Rotatiematrix (3x3, kolommen x,y,z) met y = vingerrichting F, -z = palmnormaal Pn."""
    y = nrm(F)
    z = -np.asarray(Pn, dtype=float)
    z = nrm(z - y * np.dot(z, y))
    x = np.cross(y, z)
    return np.stack([x, y, z], 1)


# ------------------------------------------------------------------ hand
FINGERS = [  # (x-positie op de palm, lengte, straal) voor de rechterhand, duim apart
    (-0.0135, 0.026, 0.0074),  # wijsvinger (duimkant = -x)
    (-0.0045, 0.029, 0.0077),
    (0.0048, 0.027, 0.0074),
    (0.0135, 0.021, 0.0067),
]
PRESETS = {
    'relaxed': (0.25, 0.35, 0.4, 0.45, 0.5),
    'open': (0.0, 0.05, 0.05, 0.08, 0.1),
    'flat': (0.1, 0.0, 0.0, 0.0, 0.0),
    'fist': (0.75, 1.0, 1.0, 1.0, 1.0),
    'grip': (0.55, 0.7, 0.75, 0.8, 0.85),
    'point': (0.6, 0.0, 1.0, 1.0, 1.0),
    'hold': (0.45, 0.55, 0.6, 0.65, 0.7),
    'spread': (0.0, -0.05, 0.0, 0.0, 0.05),
}


def hand(name, wrist, F, Pn, side, mat, parent, curl='relaxed', scale=1.0, spread=1.0, chub=1.0):
    """Mollig kinderhandje vanaf de pols. F = vingerrichting, Pn = kant waar de palm naar kijkt.
    side = -1 rechterhand, +1 linkerhand (lokaal: duim op -x voor rechts, +x voor links)."""
    c = PRESETS[curl] if isinstance(curl, str) else curl
    R = frame_from(F, Pn)
    W = np.asarray(wrist, dtype=float)
    m = -side  # spiegelfactor t.o.v. de rechterhand-tabel (rechts: 1, links: -1)
    objs = []
    tw = lambda q: W + R @ (np.asarray(q, dtype=float) * scale)
    ob = K.blob(name + '_palm', (0.0215 * chub, 0.026, 0.0115 * chub), 2.3, (32, 20), mat=mat, parent=parent)
    ob.scale = (scale, scale, scale)
    ob.matrix_world = _mat(tw([0, 0.021, 0.001]), R) @ Matrix.Scale(scale, 4)
    objs.append(ob)
    for k, (x0, L, r) in enumerate(FINGERS):
        cu = c[k + 1]
        x = x0 * m * spread
        base = np.array([x, 0.041, 0.0])
        d = nrm(np.array([x * 0.15 / max(abs(x), 1e-6) * min(abs(x) / 0.0135, 1) * spread, 1.0, 0.0]))
        pts = [base - d * 0.009]
        p = base.copy()
        ang = 0.0
        for j, sg in enumerate((0.42, 0.33, 0.25)):
            ang += cu * (0.9 if j == 0 else 0.8)
            dj = nrm(np.array([d[0], d[1] * math.cos(ang), -math.sin(ang)]))
            p = p + dj * L * sg
            pts.append(p.copy())
        rr = np.array([r, r * 1.02, r * 0.98, r * 0.9]) * chub * scale
        o, _ = K.tube(name + f'_vinger{k}', [tw(q) for q in pts], rr, mat, parent, ring=14, per=5)
        objs.append(o)
    cu = c[0]
    tb = np.array([-0.0185 * m, 0.012, -0.004])
    td = nrm(np.array([-0.75 * m, 0.75, -0.25 - 0.5 * cu]))
    tip = nrm(td + np.array([0.7 * m * cu, 0.25, -0.45 * cu]))
    pts = [tb, tb + td * 0.014, tb + td * 0.014 + tip * 0.016]
    o, _ = K.tube(name + '_duim', [tw(q) for q in pts], np.array([0.0094, 0.009, 0.008]) * chub * scale, mat,
                  parent, ring=14, per=5)
    objs.append(o)
    return objs


# ------------------------------------------------------------------ schoen
def shoe(name, ankle, fwd, mats, parent, scale=1.0, lift=0.0):
    """Zwart kinderschoentje; ankle = enkelpunt, fwd = looprichting (xy)."""
    f = nrm([fwd[0], fwd[1], 0])
    side = np.cross([0, 0, 1], f)
    A = np.asarray(ankle, dtype=float)
    ground = A[2] - 0.055 * scale
    c = A + f * 0.022 * scale
    M = np.stack([side, -f, np.array([0, 0, 1.0])], 1)  # lokaal: -y = voor

    def deform(D, P):
        P = P.copy()
        front = smoothstep(0.0, -0.9, D[:, 1])
        P[:, 2] += 0.012 * front * (D[:, 2] > -0.2)
        P[:, 0] *= 1 + 0.12 * front
        # bovenkant platter achter (instap)
        P[:, 2] -= 0.01 * smoothstep(0.2, 0.9, D[:, 1]) * (D[:, 2] > 0)
        return P

    objs = []
    body = K.blob(name, (0.039 * scale, 0.072 * scale, 0.034 * scale), 2.5, (48, 28), deform=deform,
                  mat=mats['shoe'], parent=parent)
    body.matrix_world = _mat(c + np.array([0, 0, ground - c[2] + 0.034 * scale + 0.006 * scale]), M)
    objs.append(body)
    sole = K.blob(name + '_zool', (0.037 * scale, 0.068 * scale, 0.009 * scale), 3.5, (40, 16),
                  mat=mats['sole'], parent=parent)
    sole.matrix_world = _mat(c + np.array([0, 0, ground - c[2] + 0.009 * scale]), M)
    objs.append(sole)
    # veters
    for i in range(3):
        y = (-0.004 - i * 0.014) * scale
        p0 = np.array([-0.012 * scale, y, 0.0 * scale])
        p1 = np.array([0.012 * scale, y - 0.006 * scale, 0.0])
        top = ground + 0.064 * scale + 0.004 * (2 - i) * scale * 0
        pts = [c + M @ p0 + np.array([0, 0, top - c[2]]), c + M @ ((p0 + p1) / 2) + np.array([0, 0, top - c[2] + 0.003 * scale]),
               c + M @ p1 + np.array([0, 0, top - c[2]])]
        objs.append(K.curve_tube(name + f'_veter{i}', pts, 0.0022 * scale, mats['lace'], parent))
    return objs


def _mat(loc, R3):
    M4 = Matrix.Identity(4)
    for i in range(3):
        for j in range(3):
            M4[i][j] = R3[i, j]
    return Matrix.Translation(Vector(loc)) @ M4


def set_world(ob, loc, R3):
    ob.matrix_world = _mat(loc, R3)


# ------------------------------------------------------------------ politiepet (hoofd-eenheden)
def police_cap(name, parent, mats, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, band=(0.97, 1.01)):
    """Pet met donkerblauwe bol, zwarte band, glimmende klep, gouden schild. Onderkant band in de oorsprong."""
    root = K.empty(name, loc, rot, scale, parent)
    bx, by = band
    # band (zwart onderaan, blauw erboven)
    K.lathe(name + '_band', [(1.0, 0.0), (1.0, 0.085)], 72, mats['gloss'], root, sx=bx, sy=by,
            close_top=False, close_bot=False)
    K.lathe(name + '_rand', [(1.0, 0.085), (1.02, 0.16), (1.03, 0.25)], 72, mats['navy'], root, sx=bx, sy=by,
            close_top=False, close_bot=False)
    # bol: wijder dan de band, voorkant hoger
    prof = [(1.03, 0.25), (1.12, 0.31), (1.2, 0.39), (1.235, 0.45), (1.21, 0.5), (1.08, 0.545), (0.7, 0.57),
            (0.0, 0.575)]
    K.lathe(name + '_bol', prof, 96, mats['navy'], root, sx=bx * 1.0, sy=by * 1.06, close_bot=False,
            zfn=lambda x, y: 0.13 * max(0.0, -y) ** 1.6)
    # binnenkant dicht (onder de bol)
    K.lathe(name + '_binnen', [(1.03, 0.25), (0.0, 0.26)], 48, mats['navy_dark'], root, sx=bx, sy=by,
            close_top=False, close_bot=False)
    # klep: halve ellips naar voren en omlaag
    na, nr = 40, 10
    A = np.linspace(-1.35, 1.35, na)
    V, F = [], []
    for i, a in enumerate(A):
        for j, t in enumerate(np.linspace(0, 1, nr)):
            ex = 1.0 + 0.0 * t
            px = math.sin(a) * bx * (1.0 + 0.04 * t)
            reach = 0.36 * (1 - (a / 1.35) ** 2) ** 0.5
            py = -math.cos(a) * by - reach * t
            pz = 0.035 - 0.18 * (reach * t) - 0.02 * t * t
            V.append((px, py, pz))
    for i in range(na - 1):
        for j in range(nr - 1):
            F.append((i * nr + j, (i + 1) * nr + j, (i + 1) * nr + j + 1, i * nr + j + 1))
    visor = K.mesh_obj(name + '_klep', np.array(V), F, mats['gloss'], root)
    K.solidify(visor, 0.032, 0.0)
    K.subsurf(visor, 1)
    # kinriem en knoopjes
    A = np.linspace(-1.25, 1.25, 30)
    pts = [(math.sin(a) * bx * 1.012, -math.cos(a) * by * 1.012, 0.1 + 0.035 * (a / 1.25) ** 2) for a in A]
    K.curve_tube(name + '_kinriem', pts, 0.022, mats['gloss'], root)
    for sgn in (-1, 1):
        a = 1.3 * sgn
        K.blob(name + f'_knoop{sgn}', (0.035, 0.035, 0.035), 2.0, (16, 10), mat=mats['gold'], parent=root,
               loc=(math.sin(a) * bx * 1.02, -math.cos(a) * by * 1.02, 0.12))
    # schild met ster
    shield = [(0, 0.16), (0.08, 0.15), (0.14, 0.12), (0.135, 0.0), (0.11, -0.09), (0.0, -0.17), (-0.11, -0.09),
              (-0.135, 0.0), (-0.14, 0.12), (-0.08, 0.15)]
    sh = K.poly_obj(name + '_schild', shield, depth=0.012, bevel=0.012, mat=mats['gold'], parent=root,
                    loc=(0, -by * 1.12, 0.39), rot=(math.radians(68), 0, 0))
    st = K.poly_obj(name + '_ster', K.round_star_pts(0.075, 0.48), depth=0.01, bevel=0.008, mat=mats['gold'],
                    parent=root, loc=(0, -by * 1.12 - 0.03, 0.39), rot=(math.radians(68), 0, 0))
    return root
