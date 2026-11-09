"""Haar van Daan als Hair Curves: lange kuif met plukken bovenop, kort opgeschoren zijkanten.

Werkt in de eenheidsruimte van het hoofd (zie head.py). De strengen worden stap voor stap over een
'haarschil' boven de hoofdhuid gelegd; vooraan lopen ze door naar voren en omhoog (de kuif).
"""
import math
import numpy as np
from . import core as K
from .core import smoothstep


def _norm(A):
    return A / (np.linalg.norm(A, axis=-1, keepdims=True) + 1e-12)


def _azimuth(D):
    # 0 = voorkant (-y), positief naar +x
    return np.arctan2(D[:, 0], -D[:, 1])


_HL = None   # haargrens van het huidige hoofd (head.hair_zs), gezet door build()


def hairline(D):
    """Hoogte (z) van de haargrens als functie van de richting rond het hoofd."""
    az = np.abs(np.degrees(_azimuth(D)))
    xs = [0, 30, 55, 75, 95, 115, 140, 180]
    zs = _HL or [0.40, 0.38, 0.30, 0.20, 0.17, -0.05, -0.38, -0.5]
    return np.interp(az, xs, zs)


def scalp_mask(D):
    z = D[:, 2]
    h = hairline(D)
    m = smoothstep(h, h + 0.05, z)
    # oren vrijhouden
    ear = np.exp(-(((np.abs(D[:, 0]) - 0.98) ** 2) / 0.02 + ((D[:, 1] - 0.02) ** 2) / 0.05 +
                   ((z + 0.08) ** 2) / 0.05))
    return m * (1 - ear)


def top_weight(D):
    """1 op de kruin/bovenkant (lang haar), 0 op de zijkanten (kort)."""
    c = _norm(np.array([0.0, 0.08, 1.0]))
    ang = np.degrees(np.arccos(np.clip(D @ c, -1, 1)))
    # vooraan reikt het lange haar verder naar beneden (tot de haargrens)
    az = np.abs(np.degrees(_azimuth(D)))
    lim = np.interp(az, [0, 40, 80, 130, 180], [62, 56, 47, 46, 50])
    return 1 - smoothstep(lim - 6, lim + 2, ang)


def flow(D, P):
    """Kamrichting (raaklijn): naar voren, iets naar buiten; achter en opzij naar beneden."""
    nrm = _norm(P)
    fwd = np.array([0.0, -1.0, 0.25])
    side = np.stack([D[:, 0], np.zeros(len(D)), np.zeros(len(D))], 1) * 0.35
    down = np.array([0.0, 0.25, -1.0])
    tw = top_weight(D)[:, None]
    f = (fwd + side) * tw + down * (1 - tw)
    f = f - nrm * (f * nrm).sum(1, keepdims=True)
    return _norm(f)


def build(head, mats, style='kuif', n_top=60000, n_short=110000, seed=5, cap_line=None, mess=1.0, pony=False):
    """style 'kuif' (zonder pet) of 'pet' (alleen plukjes onder de pet uit). Geeft lijst objecten."""
    global _HL
    _HL = getattr(head, 'hair_zs', None)
    rng = np.random.default_rng(seed)
    out = []
    shape = head.shape

    def surf(D):
        return shape(D)

    # ------------------------------------------------ wortels
    def sample_dirs(n, wfn):
        m = n * 4
        D = _norm(rng.normal(size=(m, 3)))
        w = wfn(D)
        keep = rng.random(m) < w
        D = D[keep][:n]
        return D

    # -------------------------------------------- kort haar (opzij en achter, en onder de pet)
    def short_w(D):
        w = scalp_mask(D) * (1 - top_weight(D) * (0.35 if style == 'kuif' else 0.0))
        if style == 'pet':
            w = w * (D[:, 2] < cap_line(D) + 0.06)
        return w

    Ds = sample_dirs(n_short, short_w)
    Ps = surf(Ds)
    Ns = _norm(Ps)
    Fs = flow(Ds, Ps)
    tw = top_weight(Ds)
    if style == 'kuif':
        Ls = 0.04 + 0.06 * tw + 0.012 * rng.random(len(Ds))
    else:
        # onder de pet uit: langere zachte plukjes bij slapen en nek
        near = smoothstep(-0.25, 0.02, Ds[:, 2] - cap_line(Ds))
        temple = np.exp(-((np.abs(Ds[:, 0]) - 0.8) ** 2) / 0.04 - ((Ds[:, 1] + 0.25) ** 2) / 0.12)
        Ls = 0.035 + (0.09 + 0.14 * temple) * near * (0.6 + 0.4 * rng.random(len(Ds)))
    k = 5
    t = np.linspace(0, 1, k)[None, :, None]
    lean = (0.12 + 0.12 * rng.random((len(Ds), 1))) * (1 - 0.7 * tw[:, None])
    d0 = _norm(Ns * lean + Fs * (1 - lean))
    jitter = _norm(rng.normal(size=(len(Ds), 3))) * 0.25
    d0 = _norm(d0 + jitter - Ns * (jitter * Ns).sum(1, keepdims=True))
    S = (Ps - Ns * 0.006)[:, None, :] + d0[:, None, :] * (Ls[:, None, None] * t)
    # licht naar de huid toe buigen
    S = S - Ns[:, None, :] * (Ls[:, None, None] * 0.2 * t ** 2)
    r = np.linspace(0.0009 + 0.0006 * 0, 0.0003, k)[None, :].repeat(len(Ds), 0)
    r = r * (1 + 0.6 * tw[:, None])
    col_short = None
    out.append(K.hair(head.name + '_kort', S, r, mats['hair'], head.root))

    if style == 'pet':
        # pony onder de klep: korte plukjes die schuin naar voren/beneden vallen
        Df = sample_dirs(500, lambda D: ((D[:, 1] < -0.55) & (np.abs(D[:, 0]) < 0.55)).astype(float) *
                         smoothstep(0.34, 0.4, D[:, 2]) * (D[:, 2] < cap_line(D) + 0.02))
        if len(Df) > 40 and pony:
            out.append(_locks(head, Df, mats, rng, kind='pony', mess=mess))
        return out

    # -------------------------------------------- lange kuif bovenop
    Dt = sample_dirs(n_top, lambda D: scalp_mask(D) * top_weight(D))
    out.append(_locks(head, Dt, mats, rng, kind='kuif', mess=mess))
    return out


def _frames_along(Gp, Ng):
    """Frame per punt langs elke gidscurve: T (richting), S (zij), U (omhoog van de hoofdhuid af)."""
    T = np.gradient(Gp, axis=1)
    T = _norm(T)
    U0 = Ng[:, None, :].repeat(Gp.shape[1], 1)
    S = _norm(np.cross(T, U0))
    U = _norm(np.cross(S, T))
    return T, S, U


def _resample(S, lf):
    """Knip elke streng af op fractie lf van zijn lengte (lineair langs de punten)."""
    n, k, _ = S.shape
    t = np.linspace(0, 1, k)[None, :] * lf[:, None] * (k - 1)
    i0 = np.clip(np.floor(t).astype(int), 0, k - 2)
    f = (t - i0)[..., None]
    idx = np.arange(n)[:, None]
    return S[idx, i0] * (1 - f) + S[idx, i0 + 1] * f


def _locks(head, D, mats, rng, kind='kuif', mess=1.0):
    """Lokken: gidsen lopen over de haarschil; elke lok is een plat lint van parallelle strengen."""
    shape = head.shape
    n_guides = 380 if kind == 'kuif' else 40
    # gelijkmatig verdeelde gidswortels (verste-punt-selectie)
    sel = [int(rng.integers(len(D)))]
    dmin = ((D - D[sel[0]]) ** 2).sum(1)
    for _ in range(n_guides - 1):
        j = int(np.argmax(dmin * (0.85 + 0.3 * rng.random(len(D)))))
        sel.append(j)
        dmin = np.minimum(dmin, ((D - D[j]) ** 2).sum(1))
    G = D[np.array(sel)]
    K_ = 18
    Pg = shape(G)
    Ng = _norm(Pg)
    if kind == 'kuif':
        front = smoothstep(0.1, -0.75, G[:, 1])
        L = (0.36 + 0.42 * front) * (0.88 + 0.24 * rng.random(n_guides))
        vol = (0.1 + 0.24 * front) * (0.6 + 0.4 * rng.random(n_guides))
    else:
        L = 0.1 + 0.06 * rng.random(n_guides)
        vol = np.full(n_guides, 0.01)
    pos = Pg.copy()
    path = [pos.copy()]
    f0 = flow(G, Pg) if kind == 'kuif' else _norm(np.array([0, -0.5, -1.0]) + 0 * Pg)
    dirv = _norm(Ng * 1.0 + f0 * 0.6)
    lift_side = rng.normal(0, 0.25, n_guides)
    for k in range(1, K_):
        step = (L / (K_ - 1))[:, None]
        u = _norm(pos)
        Rs = np.linalg.norm(shape(u), axis=1)
        cur = np.linalg.norm(pos, axis=1) - Rs
        tk = k / (K_ - 1)
        target = vol * (0.55 + 0.45 * smoothstep(0, 0.35, tk))
        if kind == 'kuif':
            fl = np.stack([u[:, 0] * 0.3, -1.0 + 0 * u[:, 0], 0.3 + 0 * u[:, 0]], 1)
            fl = _norm(fl - u * (fl * u).sum(1, keepdims=True))
        else:
            fl = _norm(np.array([0, -0.45, -1.0]) + 0 * pos)
        corr = ((target - cur) * 2.2)[:, None] * u
        nd = _norm(fl + corr / np.maximum(step, 1e-4) * 0.08)
        if kind == 'kuif':
            fz = smoothstep(-0.45, -0.75, u[:, 1]) * smoothstep(0.9, 0.55, u[:, 2])
            curl = smoothstep(0.55, 1.0, tk)
            up = _norm(np.stack([u[:, 0] * 0.14 + lift_side * 0.18, -0.2 - 0.3 * curl + 0 * u[:, 0],
                                 1.0 - 0.25 * curl + 0 * u[:, 0]], 1))
            nd = _norm(nd * (1 - fz[:, None] * 0.9) + up * fz[:, None] * 0.9)
        dirv = _norm(dirv * 0.5 + nd * 0.5)
        pos = pos + dirv * step
        path.append(pos.copy())
    Gp = np.stack(path, 1)
    tt = np.linspace(0, 1, K_)[None, :, None]
    # zachte S-golf per lok
    T, Sd, U = _frames_along(Gp, Ng)
    ph = rng.random((n_guides, 1, 1)) * 6.28
    fr = 1.5 + rng.random((n_guides, 1, 1)) * 1.5
    Gp = Gp + Sd * (np.sin(tt * fr * math.pi + ph) * 0.02 * mess * tt)
    T, Sd, U = _frames_along(Gp, Ng)

    # strengen per lok
    per = 240 if kind == 'kuif' else 120
    n = n_guides * per
    gid = np.repeat(np.arange(n_guides), per)
    width = (0.1 if kind == 'kuif' else 0.035) * (0.8 + 0.4 * rng.random(n_guides))
    a = rng.normal(0, 1, n) * width[gid] * 0.5
    b = np.abs(rng.normal(0, 1, n)) * (0.022 if kind == 'kuif' else 0.012) - 0.005
    t1 = np.linspace(0, 1, K_)[None, :]
    taper = 1 - (0.3 + 0.3 * rng.random((n, 1))) * t1 ** 1.3
    S = Gp[gid] + Sd[gid] * (a[:, None] * taper)[..., None] + U[gid] * (b[:, None] * taper)[..., None]
    # wortel op de hoofdhuid leggen
    r0 = S[:, 0, :]
    d0 = _norm(r0)
    root = shape(d0)
    S = S + (root - r0)[:, None, :] * (1 - t1[0] ** 0.5)[None, :, None]
    S[:, 0, :] = root - d0 * 0.006
    # eigen lengte, een paar losse haren
    lf = 0.78 + 0.22 * rng.random(n)
    S = _resample(S, lf)
    stray = rng.random(n) < 0.01 * mess
    noise = rng.normal(0, 0.0012, (n, K_, 3)) * tt ** 2 * (1 + 6 * stray[:, None, None])
    S = S + noise
    r = np.linspace(0.0011, 0.00035, K_)[None, :].repeat(n, 0)
    return K.hair(head.name + '_' + kind, S, r, mats['hair'], head.root)
