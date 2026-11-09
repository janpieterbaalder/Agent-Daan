"""Basis voor alle scènes: scène leegmaken, Cycles, camera, licht, wereld, meshes, haar.

Alles is procedureel: elke vorm wordt hier in Python opgebouwd (numpy), er worden geen
externe modellen of beelddiensten gebruikt.
"""
import bpy, math, random, os
import numpy as np
from mathutils import Vector, Matrix, Euler, Quaternion

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")


# ---------------------------------------------------------------- kleur
def srgb(h, a=1.0):
    """'#rrggbb' of (r,g,b) in 0-1 sRGB -> lineaire RGBA."""
    if isinstance(h, str):
        h = h.lstrip('#')
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    else:
        c = list(h)
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (lin[0], lin[1], lin[2], a)


def mixc(a, b, t):
    return tuple(a[i] * (1 - t) + b[i] * t for i in range(4))


# ---------------------------------------------------------------- scène
def reset(seed=1):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    random.seed(seed)
    np.random.seed(seed)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    return sc


def gpu():
    p = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX', 'CUDA'):
        try:
            p.compute_device_type = t
            p.get_devices()
            ok = False
            for d in p.devices:
                d.use = d.type == t
                ok = ok or d.use
            if ok:
                return t
        except Exception:
            pass
    return 'CPU'


def _set_enum(obj, prop, wanted):
    for w in wanted:
        try:
            setattr(obj, prop, w)
            return w
        except TypeError:
            continue
    return None


def render_setup(w, h, samples=256, transparent=False, exposure=0.0, look='Medium High Contrast'):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    dev = gpu()
    sc.cycles.device = 'GPU' if dev != 'CPU' else 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.006
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
        sc.cycles.denoising_use_gpu = True
    except Exception:
        pass
    sc.cycles.max_bounces = 10
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 4
    sc.cycles.transmission_bounces = 10
    sc.cycles.transparent_max_bounces = 24
    sc.cycles.volume_bounces = 0
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.sample_clamp_indirect = 6.0
    sc.cycles.blur_glossy = 1.0
    try:
        sc.cycles_curves.shape = 'THICK'
        sc.cycles_curves.subdivisions = 2
    except Exception:
        pass
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    sc.render.image_settings.color_depth = '8'
    sc.render.dither_intensity = 1.0
    _set_enum(sc.view_settings, 'view_transform', ['AgX', 'Filmic'])
    if look:
        _set_enum(sc.view_settings, 'look', ['AgX - ' + look, look, 'None'])
    sc.view_settings.exposure = exposure
    sc.view_settings.gamma = 1.0
    return dev


STYLE = os.environ.get('PRENTEN_STIJL', 'papier')
SKY = None


def render(path):
    sc = bpy.context.scene
    if STYLE == 'wol':
        from . import wol
        wol.finalize()
    elif STYLE == 'vilt':
        from . import felt
        felt.finalize()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


# ---------------------------------------------------------------- objecten
def link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, parent=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.1
    e.location = loc
    e.rotation_euler = rot
    e.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    return link(e, parent)


def mesh_obj(name, V, F, mat=None, parent=None, smooth=True, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0,
             attrs=None):
    """Mesh uit numpy-hoekpunten en vlakken (lijst van tuples of (n,k)-array)."""
    V = np.asarray(V, dtype=np.float32).reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set('co', V.ravel())
    if isinstance(F, np.ndarray):
        sizes = np.full(len(F), F.shape[1], dtype=np.int32)
        loops = F.astype(np.int32).ravel()
    else:
        sizes = np.fromiter((len(f) for f in F), dtype=np.int32, count=len(F))
        loops = np.fromiter((i for f in F for i in f), dtype=np.int32, count=int(sizes.sum()))
    me.loops.add(len(loops))
    me.loops.foreach_set('vertex_index', loops)
    me.polygons.add(len(sizes))
    starts = np.zeros(len(sizes), dtype=np.int32)
    starts[1:] = np.cumsum(sizes)[:-1]
    me.polygons.foreach_set('loop_start', starts)
    me.update(calc_edges=True)
    me.validate(clean_customdata=False)
    if smooth:
        me.polygons.foreach_set('use_smooth', np.ones(len(sizes), dtype=bool))
    if attrs:
        for an, (dom, arr) in attrs.items():
            arr = np.asarray(arr, dtype=np.float32)
            if arr.ndim == 1:
                a = me.attributes.new(an, 'FLOAT', dom)
                a.data.foreach_set('value', arr)
            else:
                if arr.shape[1] == 3:
                    arr = np.concatenate([arr, np.ones((len(arr), 1), np.float32)], 1)
                a = me.attributes.new(an, 'FLOAT_COLOR', dom)
                a.data.foreach_set('color', arr.ravel())
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    if mat is not None:
        for m in (mat if isinstance(mat, (list, tuple)) else [mat]):
            me.materials.append(m)
    return link(ob, parent)


def set_face_mats(ob, idx):
    """idx: per-vlak materiaalindex (numpy)."""
    ob.data.polygons.foreach_set('material_index', np.asarray(idx, dtype=np.int32))


def modifier(ob, kind, **kw):
    m = ob.modifiers.new(kind.lower(), kind)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def subsurf(ob, levels=1, render=None):
    return modifier(ob, 'SUBSURF', levels=levels, render_levels=levels if render is None else render)


def look_at_rot(src, dst, up=(0, 0, 1)):
    d = Vector(dst) - Vector(src)
    return d.to_track_quat('-Z', 'Y').to_euler()


# ---------------------------------------------------------------- bol en vormen
def sphere_grid(nu=64, nv=32):
    """Eenheidsbol: richtingen (N,3) en vlakken. Polen op +z en -z."""
    th = np.linspace(0, np.pi, nv + 1)[1:-1]
    ph = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    T, P = np.meshgrid(th, ph, indexing='ij')
    d = np.stack([np.sin(T) * np.cos(P), np.sin(T) * np.sin(P), np.cos(T)], -1).reshape(-1, 3)
    D = np.vstack([[0, 0, 1], d, [0, 0, -1]])
    nr = nv - 1
    vid = lambda r, j: 1 + r * nu + (j % nu)
    F = []
    for j in range(nu):
        F.append((0, vid(0, j), vid(0, j + 1)))
    for r in range(nr - 1):
        for j in range(nu):
            F.append((vid(r, j), vid(r + 1, j), vid(r + 1, j + 1), vid(r, j + 1)))
    last = len(D) - 1
    for j in range(nu):
        F.append((vid(nr - 1, j), last, vid(nr - 1, j + 1)))
    return D, F


_SPH = {}


def sph(nu, nv):
    k = (nu, nv)
    if k not in _SPH:
        _SPH[k] = sphere_grid(nu, nv)
    return _SPH[k]


def superdir(D, n):
    """Richtingen naar superellipsoïde (n=2 bol, groter = hoekiger)."""
    if np.isscalar(n):
        n = (n, n, n)
    s = (np.abs(D[:, 0]) ** n[0] + np.abs(D[:, 1]) ** n[1] + np.abs(D[:, 2]) ** n[2])
    # per-as exponent: los op met benadering (geldt exact bij gelijke n)
    ne = (n[0] + n[1] + n[2]) / 3
    return D / s[:, None] ** (1.0 / ne)


def blob(name, size=(1, 1, 1), n=2.0, res=(48, 24), deform=None, mat=None, parent=None, loc=(0, 0, 0),
         rot=(0, 0, 0), smooth=True, attrs_fn=None):
    """Afgeronde vorm: superellipsoïde met halve maten `size`, optionele vervorming f(D, P)->P."""
    D, F = sph(*res)
    P = superdir(D, n) * np.asarray(size)
    if deform is not None:
        P = deform(D, P)
    attrs = attrs_fn(D, P) if attrs_fn else None
    return mesh_obj(name, P, F, mat, parent, smooth, loc, rot, attrs=attrs)


def gauss(D, c, sigma):
    c = np.asarray(c, dtype=float)
    c = c / np.linalg.norm(c)
    d2 = ((D - c) ** 2).sum(1)
    return np.exp(-d2 / (2 * sigma * sigma))


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- buizen langs een spline
def catmull(P, n=10):
    """Catmull-Rom door punten P (k,3); geeft (m,3) en parameter u in [0,1]."""
    P = np.asarray(P, dtype=float)
    if len(P) == 2:
        t = np.linspace(0, 1, n + 1)[:, None]
        return P[0] * (1 - t) + P[1] * t, t[:, 0]
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        ts = np.linspace(0, 1, n, endpoint=False)
        for t in ts:
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-1])
    C = np.array(out)
    u = np.linspace(0, 1, len(C))
    return C, u


def frames(C, up=(0, 0, 1)):
    """Parallel-transportframes langs curve C."""
    T = np.gradient(C, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None] + 1e-12
    up = np.asarray(up, dtype=float)
    N = np.zeros_like(C)
    n0 = up - T[0] * np.dot(up, T[0])
    if np.linalg.norm(n0) < 1e-6:
        n0 = np.cross(T[0], [1, 0, 0])
    N[0] = n0 / np.linalg.norm(n0)
    for i in range(1, len(C)):
        a, b = T[i - 1], T[i]
        v = np.cross(a, b)
        s = np.linalg.norm(v)
        c = np.dot(a, b)
        n = N[i - 1]
        if s > 1e-9:
            k = v / s
            ang = math.atan2(s, c)
            n = n * math.cos(ang) + np.cross(k, n) * math.sin(ang) + k * np.dot(k, n) * (1 - math.cos(ang))
        n = n - b * np.dot(n, b)
        N[i] = n / (np.linalg.norm(n) + 1e-12)
    B = np.cross(T, N)
    return T, N, B


class Tube:
    """Buis langs een spline met (rx, ry) per controlepunt; afgeronde doppen."""

    def __init__(self, P, R, ring=32, per=10, caps=(True, True), up=(0, 0, 1), capf=(1.0, 1.0), twist=0.0,
                 rfn=None):
        self.C, self.u = catmull(P, per)
        R = np.asarray(R, dtype=float)
        if R.ndim == 1:
            R = np.stack([R, R], 1)
        k = len(P)
        idx = self.u * (k - 1)
        self.R = np.stack([np.interp(idx, np.arange(k), R[:, 0]), np.interp(idx, np.arange(k), R[:, 1])], 1)
        self.T, self.N, self.B = frames(self.C, up)
        if twist:
            for i in range(len(self.C)):
                a = twist * self.u[i]
                n, b = self.N[i].copy(), self.B[i].copy()
                self.N[i] = n * math.cos(a) + b * math.sin(a)
                self.B[i] = -n * math.sin(a) + b * math.cos(a)
        self.ring = ring
        self.caps = caps
        self.capf = capf
        self.rfn = rfn

    def point(self, u, ang, off=0.0):
        """Oppervlaktepunt bij parameter u (0-1) en hoek (0 = N-richting); geeft (p, normaal)."""
        i = np.interp(u, self.u, np.arange(len(self.u)))
        i0 = int(min(max(math.floor(i), 0), len(self.u) - 2))
        f = i - i0
        L = lambda A: A[i0] * (1 - f) + A[i0 + 1] * f
        C, N, B, R = L(self.C), L(self.N), L(self.B), L(self.R)
        rx, ry = R
        if self.rfn is not None:
            s = self.rfn(np.array([u]), np.array([ang]))[0]
            rx, ry = rx * s, ry * s
        dirv = N * math.cos(ang) * rx + B * math.sin(ang) * ry
        nrm = N * math.cos(ang) / max(rx, 1e-6) + B * math.sin(ang) / max(ry, 1e-6)
        nrm /= np.linalg.norm(nrm)
        return C + dirv + nrm * off, nrm

    def build(self, name, mat=None, parent=None, smooth=True, attrs_fn=None):
        C, N, B, R, T = self.C, self.N, self.B, self.R, self.T
        m = len(C)
        a = np.linspace(0, 2 * np.pi, self.ring, endpoint=False)
        ca, sa = np.cos(a), np.sin(a)
        U = np.repeat(self.u[:, None], self.ring, 1)
        A = np.repeat(a[None, :], m, 0)
        S = np.ones_like(U) if self.rfn is None else self.rfn(U, A)
        V = (C[:, None, :] + N[:, None, :] * (ca[None, :, None] * R[:, 0, None, None] * S[..., None]) +
             B[:, None, :] * (sa[None, :, None] * R[:, 1, None, None] * S[..., None]))
        V = V.reshape(-1, 3)
        UU, AA = U.ravel(), A.ravel()
        F = []
        rg = self.ring
        for i in range(m - 1):
            for j in range(rg):
                F.append((i * rg + j, i * rg + (j + 1) % rg, (i + 1) * rg + (j + 1) % rg, (i + 1) * rg + j))
        extra, eu, ea = [], [], []
        base = len(V)

        def cap(end):
            nonlocal base
            i = 0 if end == 0 else m - 1
            sgn = -1 if end == 0 else 1
            K = 6
            prev = [i * rg + j for j in range(rg)]
            r_avg = R[i].mean() * self.capf[end]
            for k in range(1, K + 1):
                phi = k / K * (np.pi / 2)
                if k < K:
                    s0 = S[i] if self.rfn is not None else np.ones(rg)
                    ring_pts = (C[i] + T[i] * sgn * r_avg * math.sin(phi) +
                                (N[i] * (ca * R[i, 0] * s0)[:, None] + B[i] * (sa * R[i, 1] * s0)[:, None]) * math.cos(phi))
                    cur = list(range(base, base + rg))
                    extra.extend(ring_pts)
                    eu.extend([self.u[i]] * rg)
                    ea.extend(list(a))
                    base += rg
                    for j in range(rg):
                        q = (prev[j], prev[(j + 1) % rg], cur[(j + 1) % rg], cur[j])
                        F.append(q if end == 1 else q[::-1])
                    prev = cur
                else:
                    tip = C[i] + T[i] * sgn * r_avg
                    extra.append(tip)
                    eu.append(self.u[i])
                    ea.append(0.0)
                    t_id = base
                    base += 1
                    for j in range(rg):
                        tri = (prev[j], prev[(j + 1) % rg], t_id)
                        F.append(tri if end == 1 else tri[::-1])

        # oriëntatie: zijkant kijkt naar buiten als N x B = T; vlakvolgorde hierboven gaat met T mee
        if self.caps[0]:
            cap(0)
        if self.caps[1]:
            cap(1)
        if extra:
            V = np.vstack([V, np.array(extra)])
            UU = np.concatenate([UU, eu])
            AA = np.concatenate([AA, ea])
        attrs = attrs_fn(V, UU, AA) if attrs_fn else None
        # zijvlak (j -> j+1 -> volgende ring): normaal = B x T = N, dus naar buiten
        return mesh_obj(name, V, F, mat, parent, smooth, attrs=attrs)


def tube(name, P, R, mat=None, parent=None, **kw):
    bk = {k: kw.pop(k) for k in list(kw) if k in ('attrs_fn', 'smooth')}
    t = Tube(P, R, **kw)
    ob = t.build(name, mat, parent, **bk)
    return ob, t


def lathe(name, prof, seg=48, mat=None, parent=None, sx=1.0, sy=1.0, smooth=True, close_top=True,
          close_bot=True, zfn=None):
    """Draaivorm om de z-as uit profiel [(r, z), ...] van onder naar boven."""
    prof = np.asarray(prof, dtype=float)
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    V = []
    for r, z in prof:
        for t in a:
            x, y = r * math.cos(t) * sx, r * math.sin(t) * sy
            V.append((x, y, z + (zfn(x, y) if zfn else 0)))
    F = []
    n = len(prof)
    for i in range(n - 1):
        for j in range(seg):
            F.append((i * seg + j, i * seg + (j + 1) % seg, (i + 1) * seg + (j + 1) % seg, (i + 1) * seg + j))
    if close_bot and prof[0][0] > 1e-6:
        V.append((0, 0, prof[0][1]))
        c = len(V) - 1
        for j in range(seg):
            F.append(((j + 1) % seg, j, c))
    if close_top and prof[-1][0] > 1e-6:
        V.append((0, 0, prof[-1][1] + (zfn(0, 0) if zfn else 0)))
        c = len(V) - 1
        for j in range(seg):
            F.append(((n - 1) * seg + j, (n - 1) * seg + (j + 1) % seg, c))
    return mesh_obj(name, np.array(V), F, mat, parent, smooth)


def grid_mesh(name, nx, ny, fn, mat=None, parent=None, smooth=True, attrs_fn=None):
    """Raster (u,v) in [0,1]^2 -> fn(U,V) geeft (nx*ny,3)."""
    u = np.linspace(0, 1, nx)
    v = np.linspace(0, 1, ny)
    U, Vv = np.meshgrid(u, v, indexing='ij')
    P = fn(U.ravel(), Vv.ravel())
    F = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            F.append((i * ny + j, (i + 1) * ny + j, (i + 1) * ny + j + 1, i * ny + j + 1))
    attrs = attrs_fn(U.ravel(), Vv.ravel(), P) if attrs_fn else None
    return mesh_obj(name, P, F, mat, parent, smooth, attrs=attrs)


def solidify(ob, t, offset=-1.0):
    return modifier(ob, 'SOLIDIFY', thickness=t, offset=offset, use_even_offset=True)


# ---------------------------------------------------------------- haar
def hair(name, strands, radius, mat=None, parent=None, col=None, attrs=None):
    """strands: lijst van (k,3) arrays of één (n,k,3) array; radius: (n,k) of (root, tip)."""
    if isinstance(strands, np.ndarray) and strands.ndim == 3:
        n, k, _ = strands.shape
        sizes = [k] * n
        pos = strands.reshape(-1, 3)
    else:
        sizes = [len(s) for s in strands]
        pos = np.concatenate(strands)
        n = len(sizes)
    hc = bpy.data.hair_curves.new(name)
    hc.add_curves(sizes)
    hc.attributes['position'].data.foreach_set('vector', pos.astype(np.float32).ravel())
    if isinstance(radius, tuple):
        r0, r1 = radius
        rr = []
        for k in sizes:
            t = np.linspace(0, 1, k)
            rr.append(r0 * (1 - t) + r1 * t)
        rad = np.concatenate(rr)
    else:
        rad = np.asarray(radius).ravel()
    ra = hc.attributes.get('radius') or hc.attributes.new('radius', 'FLOAT', 'POINT')
    ra.data.foreach_set('value', rad.astype(np.float32))
    if col is not None:
        col = np.asarray(col, dtype=np.float32)
        if col.shape[1] == 3:
            col = np.concatenate([col, np.ones((len(col), 1), np.float32)], 1)
        ca = hc.attributes.new('col', 'FLOAT_COLOR', 'CURVE')
        ca.data.foreach_set('color', col.ravel())
    if attrs:
        for an, arr in attrs.items():
            a = hc.attributes.new(an, 'FLOAT', 'CURVE')
            a.data.foreach_set('value', np.asarray(arr, dtype=np.float32))
    ob = bpy.data.objects.new(name, hc)
    if mat is not None:
        hc.materials.append(mat)
    return link(ob, parent)


def sample_surface(V, F, n, mask_fn=None, rng=None):
    """Willekeurige punten op driehoeken/vierhoeken, gewogen naar oppervlak. Geeft (pos, normaal, faceidx, bary)."""
    rng = rng or np.random.default_rng(1)
    tris = []
    for f in F:
        if len(f) == 3:
            tris.append(f)
        else:
            tris.append((f[0], f[1], f[2]))
            tris.append((f[0], f[2], f[3]))
    tris = np.array(tris)
    A, B, C = V[tris[:, 0]], V[tris[:, 1]], V[tris[:, 2]]
    cr = np.cross(B - A, C - A)
    area = np.linalg.norm(cr, axis=1) * 0.5
    nrm = cr / (np.linalg.norm(cr, axis=1)[:, None] + 1e-12)
    if mask_fn is not None:
        w = mask_fn((A + B + C) / 3)
        area = area * w
    p = area / area.sum()
    ti = rng.choice(len(tris), size=n, p=p)
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)
    a, b, c = 1 - s, s * (1 - r2), s * r2
    pos = A[ti] * a[:, None] + B[ti] * b[:, None] + C[ti] * c[:, None]
    return pos, nrm[ti], ti


def obj_mesh_np(ob, world=False):
    """Hoekpunten en vlakken van een (geëvalueerd) object als numpy."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get('co', V)
    V = V.reshape(-1, 3).astype(float)
    F = [tuple(p.vertices) for p in me.polygons]
    if world:
        M = np.array(ob.matrix_world)
        V = V @ M[:3, :3].T + M[:3, 3]
    ev.to_mesh_clear()
    return V, F


# ---------------------------------------------------------------- tekst en vormen van curves
def text_obj(name, body, font='MuseoSansRounded900.otf', size=0.1, extrude=0.01, bevel=0.003, mat=None,
             parent=None, align='CENTER', loc=(0, 0, 0), rot=(0, 0, 0), spacing=1.0):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    try:
        cu.font = bpy.data.fonts.load(os.path.join(FONT_DIR, font), check_existing=True)
    except Exception:
        pass
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 3
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.space_character = spacing
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = rot
    if mat is not None:
        cu.materials.append(mat)
    return link(ob, parent)


def poly_obj(name, pts2d, depth=0.01, bevel=0.003, mat=None, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Vlakke vorm uit 2D-punten (xy), geëxtrudeerd met afgeronde rand."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'
    cu.extrude = depth
    cu.bevel_depth = bevel
    cu.bevel_resolution = 4
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts2d) - 1)
    for p, (x, y) in zip(sp.points, pts2d):
        p.co = (x, y, 0, 1)
    sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = rot
    if mat is not None:
        cu.materials.append(mat)
    return link(ob, parent)


def star_pts(r=1.0, inner=0.45, n=5, rot=math.pi / 2):
    pts = []
    for i in range(2 * n):
        a = rot + i * math.pi / n
        rr = r if i % 2 == 0 else r * inner
        pts.append((math.cos(a) * rr, math.sin(a) * rr))
    return pts


def round_star_pts(r=1.0, inner=0.5, n=5, seg=6, round_=0.18):
    """Ster met afgeronde punten (voor de gouden ster)."""
    base = star_pts(r, inner, n)
    out = []
    m = len(base)
    for i in range(m):
        p0 = np.array(base[i - 1])
        p1 = np.array(base[i])
        p2 = np.array(base[(i + 1) % m])
        if i % 2 == 0:
            a = p1 + (p0 - p1) * round_
            b = p1 + (p2 - p1) * round_
            for t in np.linspace(0, 1, seg):
                q = (1 - t) ** 2 * a + 2 * (1 - t) * t * p1 + t * t * b
                out.append(tuple(q))
        else:
            out.append(tuple(p1))
    return out


def curve_tube(name, pts, radius, mat=None, parent=None, res=6, cyclic=False):
    """Dunne buis (draad, naad, veter) langs punten."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new('NURBS')
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (c[0], c[1], c[2], 1)
    sp.order_u = min(4, len(pts))
    sp.use_endpoint_u = not cyclic
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    if mat is not None:
        cu.materials.append(mat)
    return link(ob, parent)


# ---------------------------------------------------------------- camera, licht, wereld
def camera(loc, target, lens=35, fstop=None, focus=None, sensor=36, shift=(0, 0), roll=0.0, name='Cam',
           clip=(0.01, 200)):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = 'HORIZONTAL'
    cd.shift_x, cd.shift_y = shift
    cd.clip_start, cd.clip_end = clip
    ob = bpy.data.objects.new(name, cd)
    link(ob)
    ob.location = loc
    q = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Quaternion((0, 0, 1), roll)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = q
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.aperture_blades = 7
        cd.dof.aperture_rotation = 0.3
        if isinstance(focus, bpy.types.Object):
            cd.dof.focus_object = focus
        elif focus is not None and not isinstance(focus, (int, float)):
            cd.dof.focus_distance = (Vector(focus) - Vector(loc)).length
        elif focus is not None:
            cd.dof.focus_distance = focus
        else:
            cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
    bpy.context.scene.camera = ob
    return ob


def light(kind, loc, target=None, energy=100, color=(1, 1, 1), size=1.0, name=None, angle=None, spot=None,
          shadow_soft=None, visible_glossy=True, size_y=None, shape=None):
    ld = bpy.data.lights.new(name or kind.lower(), kind)
    ld.energy = energy
    ld.color = color[:3]
    if kind == 'AREA':
        ld.size = size
        if size_y is not None:
            ld.shape = shape or 'RECTANGLE'
            ld.size_y = size_y
        elif shape:
            ld.shape = shape
    elif kind in ('POINT', 'SPOT'):
        ld.shadow_soft_size = size
    if kind == 'SUN':
        ld.angle = math.radians(angle if angle is not None else 3.0)
    if kind == 'SPOT' and spot:
        ld.spot_size = math.radians(spot)
        ld.spot_blend = 0.6
    ob = bpy.data.objects.new(ld.name, ld)
    link(ob)
    ob.location = loc
    if target is not None:
        ob.rotation_euler = look_at_rot(loc, target)
    try:
        ob.visible_glossy = visible_glossy
    except Exception:
        pass
    return ob


def sun_dir(azimuth, elevation, energy=3.0, color=(1.0, 0.94, 0.85), angle=3.0):
    az, el = math.radians(azimuth), math.radians(elevation)
    d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    ob = light('SUN', d * 10, (0, 0, 0), energy=energy, color=color, angle=angle, name='Zon')
    return ob


def world_sky(zenith='#6fa9e6', horizon='#e9f1f4', ground='#9a9076', strength=1.0, sun_glow=None):
    """Zachte gradiëntlucht als omgevingslicht."""
    global SKY
    SKY = (zenith, horizon, ground, strength)
    w = bpy.data.worlds.new('Lucht')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    # Generated op de wereld = richting; z van -1 tot 1
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    mp = nt.nodes.new('ShaderNodeMapRange')
    mp.inputs['From Min'].default_value = -1
    mp.inputs['From Max'].default_value = 1
    nt.links.new(sep.outputs['Z'], mp.inputs['Value'])
    nt.links.new(mp.outputs['Result'], ramp.inputs['Fac'])
    cr = ramp.color_ramp
    cr.interpolation = 'B_SPLINE'
    cr.elements[0].position = 0.0
    cr.elements[0].color = srgb(ground)
    cr.elements[1].position = 0.5
    cr.elements[1].color = srgb(horizon)
    e = cr.elements.new(0.62)
    e.color = mixc(srgb(horizon), srgb(zenith), 0.55)
    e = cr.elements.new(1.0)
    e.color = srgb(zenith)
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return w


def world_color(col, strength=1.0):
    w = bpy.data.worlds.new('Wereld')
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background') or w.node_tree.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = srgb(col) if isinstance(col, str) else col
    bg.inputs['Strength'].default_value = strength
    return w


# ---------------------------------------------------------------- beweging (motion blur)
def keyframe_move(ob, delta, frames=(0, 2)):
    """Object beweegt `delta` tussen twee frames; render op het middelste frame."""
    sc = bpy.context.scene
    base = ob.location.copy()
    sc.frame_set(frames[0])
    ob.location = base - Vector(delta) * 0.5
    ob.keyframe_insert('location', frame=frames[0])
    ob.location = base + Vector(delta) * 0.5
    ob.keyframe_insert('location', frame=frames[1])
    try:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    except Exception:
        pass


def keyframe_rot(ob, axis, angle, frames=(0, 2)):
    base = ob.rotation_euler.copy()
    a = 'xyz'.index(axis)
    r0, r1 = base.copy(), base.copy()
    r0[a] -= angle * 0.5
    r1[a] += angle * 0.5
    ob.rotation_euler = r0
    ob.keyframe_insert('rotation_euler', frame=frames[0])
    ob.rotation_euler = r1
    ob.keyframe_insert('rotation_euler', frame=frames[1])
    try:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    except Exception:
        pass
