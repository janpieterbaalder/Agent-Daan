"""Viltstijl: zet een complete scène om naar naaldvilt, vlak voor het renderen.

1. feltify(): elk Principled-materiaal wordt wol: volledig mat, zachte glans (sheen), wolvlekken,
   vezelstreepjes en naaldputjes in de kleur en het reliëf; het oorspronkelijke kleurverloop blijft.
2. fuzz(): echte losse pluisvezels (Hair Curves) op alle viltoppervlakken, met een vaste dichtheid per
   beeldvlak (dichtbij veel, ver weg weinig, buiten beeld niets). De kleur per vezel komt uit een kleine
   evaluator van de materiaalnodes (inclusief kleurattributen zoals blos of klinkerkleur).
3. backdrop(): luchtdoek van vilt als achtergrond (alleen zichtbaar voor de camera).
4. miniatuur: kleinere scherptediepte, zodat het geheel als een vilten diorama leest.

Materialen met de eigenschap 'nofelt' (ogen, glas, metaal, borduurgaren) blijven zoals ze zijn.
"""
import math
import bpy
import numpy as np
from mathutils import Matrix

DENS = 150000.0       # vezels per m2 binnen D0 van de camera
D0 = 1.7
BUDGET = 2600000
FSTOP_MULT = 0.38


# ------------------------------------------------------------------ materialen
def _principled_nodes(m):
    if not m or not m.use_nodes or not m.node_tree:
        return []
    return [n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled']


def _inp(nd, name):
    for s in nd.inputs:
        if s.name == name and s.enabled:
            return s
    return nd.inputs.get(name)


def _val(nd, name, default=0.0):
    s = _inp(nd, name)
    if s is None or s.is_linked:
        return default
    v = s.default_value
    try:
        return float(v)
    except TypeError:
        return tuple(v)


def _skip(m, p):
    if m.get('nofelt'):
        return True
    if _val(p, 'Metallic') > 0.5 or _val(p, 'Transmission Weight') > 0.5:
        return True
    return False


def _felt_nodes(m, p, sheet=False):
    t = m.node_tree
    N, L = t.nodes, t.links
    geo = N.new('ShaderNodeNewGeometry')
    pos = geo.outputs['Position']

    def noise(scale, detail, rough, dist=0.0):
        n = N.new('ShaderNodeTexNoise')
        L.new(pos, n.inputs['Vector'])
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        n.inputs['Distortion'].default_value = dist
        return n.outputs['Fac']

    def math_(op, a, b):
        n = N.new('ShaderNodeMath')
        n.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, bpy.types.NodeSocket):
                L.new(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]

    def maprange(v, a, b, c, d):
        n = N.new('ShaderNodeMapRange')
        L.new(v, n.inputs['Value'])
        n.inputs['From Min'].default_value = a
        n.inputs['From Max'].default_value = b
        n.inputs['To Min'].default_value = c
        n.inputs['To Max'].default_value = d
        return n.outputs['Result']

    mott = noise(11.0, 4.0, 0.62)
    fib = noise(150.0 if not sheet else 240.0, 3.0, 0.65, 4.0)
    fib2 = noise(560.0, 2.0, 0.6, 2.0)
    vor = N.new('ShaderNodeTexVoronoi')
    L.new(pos, vor.inputs['Vector'])
    vor.inputs['Scale'].default_value = 190.0 if not sheet else 260.0
    pit = maprange(vor.outputs['Distance'], 0.0, 0.22, 1.0, 0.0)
    # kleurvariatie: grote wolvlekken + vezels, donkerder in de putjes
    var = math_('ADD', math_('MULTIPLY', mott, 0.6), math_('MULTIPLY', fib, 0.4))
    shade = maprange(var, 0.28, 0.72, 0.86, 1.12)
    shade = math_('SUBTRACT', shade, math_('MULTIPLY', pit, 0.08))
    bc = _inp(p, 'Base Color')
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.clamp_result = True
    mix.inputs['Factor'].default_value = 1.0
    a_in = [s for s in mix.inputs if s.name == 'A' and s.enabled][0]
    b_in = [s for s in mix.inputs if s.name == 'B' and s.enabled][0]
    if bc.is_linked:
        L.new(bc.links[0].from_socket, a_in)
    else:
        a_in.default_value = bc.default_value
    comb = N.new('ShaderNodeCombineXYZ')
    for i in range(3):
        L.new(shade, comb.inputs[i])
    L.new(comb.outputs[0], b_in)
    L.new([s for s in mix.outputs if s.name == 'Result' and s.enabled][0], bc)
    # reliëf: vezels en putjes, bovenop een eventueel bestaand reliëf
    h = math_('SUBTRACT', math_('ADD', math_('MULTIPLY', fib, 0.7), math_('MULTIPLY', fib2, 0.45)),
              math_('MULTIPLY', pit, 0.3))
    bump = N.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.55 if not sheet else 0.4
    bump.inputs['Distance'].default_value = 0.003
    L.new(h, bump.inputs['Height'])
    nin = _inp(p, 'Normal')
    if nin.is_linked:
        L.new(nin.links[0].from_socket, bump.inputs['Normal'])
    L.new(bump.outputs['Normal'], nin)
    # wol: mat, zachte glans, iets doorschijnend
    for name, v in (('Roughness', 1.0), ('Coat Weight', 0.0), ('Specular IOR Level', 0.2),
                    ('Sheen Weight', 0.55), ('Sheen Roughness', 0.45)):
        s = _inp(p, name)
        if s is None:
            continue
        for l in list(s.links):
            L.remove(l)
        s.default_value = v
    st = _inp(p, 'Sheen Tint')
    if st is not None:
        # vezels hebben zelf kleur: glans in een lichtere tint van de wol
        lite = N.new('ShaderNodeMix')
        lite.data_type = 'RGBA'
        lite.blend_type = 'MIX'
        lite.inputs['Factor'].default_value = 0.35
        la = [s_ for s_ in lite.inputs if s_.name == 'A' and s_.enabled][0]
        lb = [s_ for s_ in lite.inputs if s_.name == 'B' and s_.enabled][0]
        L.new([s_ for s_ in mix.outputs if s_.name == 'Result' and s_.enabled][0], la)
        lb.default_value = (1.0, 1.0, 1.0, 1.0)
        L.new([s_ for s_ in lite.outputs if s_.name == 'Result' and s_.enabled][0], st)
    ss = _inp(p, 'Subsurface Weight')
    if ss is not None and not ss.is_linked:
        ss.default_value = max(ss.default_value, 0.12)
        sc = _inp(p, 'Subsurface Scale')
        if sc is not None and not sc.is_linked:
            sc.default_value = min(max(sc.default_value, 0.004), 0.012)


def feltify():
    done = 0
    for m in list(bpy.data.materials):
        if m.get('felted'):
            continue
        ps = _principled_nodes(m)
        hairs = [n for n in (m.node_tree.nodes if m.use_nodes and m.node_tree else [])
                 if n.bl_idname == 'ShaderNodeBsdfHairPrincipled']
        for h in hairs:
            if m.get('nofelt'):
                continue
            for name, v in (('Roughness', 0.55), ('Radial Roughness', 0.9), ('Coat', 0.0)):
                s = _inp(h, name)
                if s is not None and not s.is_linked:
                    s.default_value = v
        felt_any = False
        for p in ps:
            if _skip(m, p):
                continue
            _felt_nodes(m, p, sheet=bool(m.get('sheet')))
            felt_any = True
        if felt_any:
            m['felt'] = 1
            done += 1
        m['felted'] = 1
    return done


# ------------------------------------------------------------------ kleur-evaluator (voor de vezels)
def _vec(v):
    a = np.asarray(v, dtype=float)
    if a.ndim == 0:
        return np.full(3, float(a))
    return a[..., :3]


class _Eval:
    def __init__(self, attr_fn):
        self.attr_fn = attr_fn

    def inp(self, s):
        if s is None:
            return 0.5
        if s.is_linked:
            l = s.links[0]
            if not l.is_valid or l.is_muted:
                return 0.5
            return self.out(l.from_node, l.from_socket)
        v = s.default_value
        try:
            return np.asarray(v[:], dtype=float)[:3] if len(v) >= 3 else float(v[0])
        except TypeError:
            return float(v)

    def _named(self, nd, name):
        return _inp(nd, name)

    def out(self, nd, sock):
        t = nd.bl_idname
        try:
            if t == 'ShaderNodeAttribute':
                c = self.attr_fn(nd.attribute_name)
                if c is None:
                    c = np.ones(3)
                if sock.name in ('Fac', 'Alpha'):
                    return np.asarray(c)[..., :3].mean(-1, keepdims=False)
                return c
            if t == 'ShaderNodeRGB':
                return np.asarray(sock.default_value[:3], float)
            if t == 'ShaderNodeValue':
                return float(sock.default_value)
            if t == 'ShaderNodeMix':
                fac = self.inp([s for s in nd.inputs if s.name == 'Factor' and s.enabled][0])
                a = self.inp([s for s in nd.inputs if s.name == 'A' and s.enabled][0])
                b = self.inp([s for s in nd.inputs if s.name == 'B' and s.enabled][0])
                f = np.asarray(fac, float)
                if f.ndim >= 1 and f.shape[-1] == 3:
                    f = f.mean(-1)
                if nd.data_type == 'RGBA':
                    a, b = _vec(a), _vec(b)
                    f = f[..., None] if f.ndim else f
                    bt = nd.blend_type
                    if bt == 'MULTIPLY':
                        r = a * (1 - f + f * b)
                    elif bt == 'ADD':
                        r = a + f * b
                    else:
                        r = a * (1 - f) + b * f
                    return np.clip(r, 0, None)
                return np.asarray(a, float) * (1 - f) + np.asarray(b, float) * f
            if t == 'ShaderNodeMixRGB':
                f = np.asarray(self.inp(nd.inputs[0]), float)
                a, b = _vec(self.inp(nd.inputs[1])), _vec(self.inp(nd.inputs[2]))
                f = f[..., None] if f.ndim else f
                if nd.blend_type == 'MULTIPLY':
                    return a * (1 - f + f * b)
                return a * (1 - f) + b * f
            if t == 'ShaderNodeTexBrick':
                c1, c2 = _vec(self.inp(_inp(nd, 'Color1'))), _vec(self.inp(_inp(nd, 'Color2')))
                mo = _vec(self.inp(_inp(nd, 'Mortar')))
                if sock.name == 'Fac':
                    return 0.9
                return (c1 + c2) * 0.45 + mo * 0.1
            if t == 'ShaderNodeValToRGB':
                f = np.asarray(self.inp(_inp(nd, 'Fac')), float)
                els = nd.color_ramp.elements
                xs = [e.position for e in els]
                cs = np.array([list(e.color)[:3] for e in els])
                r = np.stack([np.interp(f, xs, cs[:, i]) for i in range(3)], -1)
                if sock.name == 'Alpha':
                    return float(np.mean(r))
                return r
            if t == 'ShaderNodeMapRange':
                v = np.asarray(self.inp(_inp(nd, 'Value')), float)
                a, b = self.inp(_inp(nd, 'From Min')), self.inp(_inp(nd, 'From Max'))
                c, d = self.inp(_inp(nd, 'To Min')), self.inp(_inp(nd, 'To Max'))
                x = (v - a) / (b - a if abs(b - a) > 1e-9 else 1e-9)
                if nd.clamp:
                    x = np.clip(x, 0, 1)
                return c + (d - c) * x
            if t == 'ShaderNodeMath':
                a = np.asarray(self.inp(nd.inputs[0]), float)
                b = np.asarray(self.inp(nd.inputs[1]), float)
                op = nd.operation
                r = {'ADD': lambda: a + b, 'SUBTRACT': lambda: a - b, 'MULTIPLY': lambda: a * b,
                     'MINIMUM': lambda: np.minimum(a, b), 'MAXIMUM': lambda: np.maximum(a, b),
                     'GREATER_THAN': lambda: 0.5, 'LESS_THAN': lambda: 0.5,
                     'DIVIDE': lambda: a / np.where(np.abs(b) < 1e-9, 1e-9, b)}.get(op, lambda: 0.5)()
                if nd.use_clamp:
                    r = np.clip(r, 0, 1)
                return r
            if t == 'ShaderNodeCombineXYZ' or t == 'ShaderNodeCombineColor':
                vals = np.broadcast_arrays(*[np.asarray(self.inp(nd.inputs[i]), float) for i in range(3)])
                return np.stack(vals, -1)
            if t in ('ShaderNodeTexNoise', 'ShaderNodeTexVoronoi', 'ShaderNodeTexWave', 'ShaderNodeTexGradient',
                     'ShaderNodeTexMusgrave', 'ShaderNodeTexMagic'):
                return 0.5 if sock.name in ('Fac', 'Distance') else np.full(3, 0.5)
        except Exception:
            return 0.5
        return 0.5


def _mat_color(m, attr_fn):
    for p in _principled_nodes(m):
        c = _Eval(attr_fn).inp(_inp(p, 'Base Color'))
        return np.clip(_vec(c), 0, 1)
    return np.full(3, 0.5)


# ------------------------------------------------------------------ vezels
def _cam_info():
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        return None
    M = np.array(cam.matrix_world.inverted())
    cd = cam.data
    W, H = sc.render.resolution_x, sc.render.resolution_y
    tx = (cd.sensor_width / 2) / cd.lens
    ty = tx * H / W
    return M, np.array(cam.matrix_world.translation), tx * (1 + 2 * abs(cd.shift_x)), ty * (1 + 2 * abs(cd.shift_y))


def fuzz(seed=7, dens=DENS, budget=BUDGET):
    bpy.context.view_layer.update()
    ci = _cam_info()
    if ci is None:
        return None
    Mc, cpos, tx, ty = ci
    rng = np.random.default_rng(seed)
    dg = bpy.context.evaluated_depsgraph_get()
    chunks = []
    total = 0.0
    dbg = dict(cand=0, mesh=0)
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH' or ob.hide_render or not ob.visible_camera:
            continue
        mats = [s.material for s in ob.material_slots]
        if not any(m is not None and m.get('felt') for m in mats):
            continue
        dbg['cand'] += 1
        oe = ob.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        me.calc_loop_triangles()
        nt = len(me.loop_triangles)
        if nt == 0:
            oe.to_mesh_clear()
            continue
        V = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get('co', V)
        V = V.reshape(-1, 3).astype(float)
        T = np.empty(nt * 3, np.int32)
        me.loop_triangles.foreach_get('vertices', T)
        T = T.reshape(-1, 3)
        Lp = np.empty(nt * 3, np.int32)
        me.loop_triangles.foreach_get('loops', Lp)
        Lp = Lp.reshape(-1, 3)
        MI = np.empty(nt, np.int32)
        me.loop_triangles.foreach_get('material_index', MI)
        Mw = np.array(oe.matrix_world)
        Vw = V @ Mw[:3, :3].T + Mw[:3, 3]
        A, B, C = Vw[T[:, 0]], Vw[T[:, 1]], Vw[T[:, 2]]
        cr = np.cross(B - A, C - A)
        area = np.linalg.norm(cr, axis=1) * 0.5
        nrm = cr / (2 * area[:, None] + 1e-12)
        cen = (A + B + C) / 3
        # zichtbaarheid en afstand
        pc = cen @ Mc[:3, :3].T + Mc[:3, 3]
        z = -pc[:, 2]
        vis = (z > 0.02) & (np.abs(pc[:, 0]) < z * tx * 1.08 + 0.05) & (np.abs(pc[:, 1]) < z * ty * 1.08 + 0.05)
        d = np.linalg.norm(cen - cpos, axis=1)
        fall = np.minimum(1.0, (D0 / np.maximum(d, 1e-3)) ** 2)
        mul = np.zeros(nt)
        for i, m in enumerate(mats):
            if m is not None and m.get('felt'):
                mul[MI == i] = float(m.get('fuzz', 1.0))
        w = area * dens * fall * vis * mul
        dbg['mesh'] += 1
        dbg[ob.name] = (round(float(area.sum()), 3), int(vis.sum()), nt, round(float(w.sum())))
        if w.sum() < 1:
            oe.to_mesh_clear()
            continue
        # kleur per driehoek
        attrs = {}

        def attr_fn(name, me=me, T=T, Lp=Lp):
            if name in attrs:
                return attrs[name]
            a = me.attributes.get(name) or me.color_attributes.get(name) if hasattr(me, 'color_attributes') else None
            if a is None:
                attrs[name] = None
                return None
            n_el = len(a.data)
            try:
                buf = np.empty(n_el * 4, np.float32)
                a.data.foreach_get('color', buf)
                arr = buf.reshape(-1, 4)[:, :3]
            except Exception:
                try:
                    buf = np.empty(n_el, np.float32)
                    a.data.foreach_get('value', buf)
                    arr = np.repeat(buf[:, None], 3, 1)
                except Exception:
                    attrs[name] = None
                    return None
            idx = Lp if a.domain == 'CORNER' else (T if a.domain == 'POINT' else None)
            if idx is None:
                res = None
            else:
                res = arr[idx].mean(1)
            attrs[name] = res
            return res

        col = np.zeros((nt, 3))
        for i, m in enumerate(mats):
            sel = MI == i
            if m is None or not m.get('felt') or not sel.any():
                continue
            attrs.clear()
            c = np.asarray(_mat_color(m, attr_fn), float)
            if c.ndim == 2 and c.shape[0] != nt:
                c = c.mean(0)
            c = np.broadcast_to(c, (nt, 3))
            col[sel] = c[sel]
        chunks.append((A, B, C, nrm, w, col))
        total += w.sum()
        oe.to_mesh_clear()
    if not chunks:
        print('vilt: geen vezels', {k: v for k, v in list(dbg.items())[:12]})
        return None
    scale = min(1.0, budget / max(total, 1.0))
    P_, N_, C_ = [], [], []
    for A, B, C, nrm, w, col in chunks:
        lam = w * scale
        cnt = np.floor(lam + rng.random(len(lam))).astype(np.int64)
        idx = np.repeat(np.arange(len(lam)), cnt)
        if len(idx) == 0:
            continue
        r1, r2 = rng.random(len(idx)), rng.random(len(idx))
        s = np.sqrt(r1)
        a, b, c = 1 - s, s * (1 - r2), s * r2
        P_.append(A[idx] * a[:, None] + B[idx] * b[:, None] + C[idx] * c[:, None])
        N_.append(nrm[idx])
        C_.append(col[idx])
    P = np.concatenate(P_)
    Nn = np.concatenate(N_)
    Cc = np.concatenate(C_)
    n = len(P)
    # vezel: start net onder het oppervlak, gaat schuin omhoog en buigt terug
    r = rng.normal(size=(n, 3))
    tng = r - Nn * (r * Nn).sum(1, keepdims=True)
    tng /= np.linalg.norm(tng, axis=1, keepdims=True) + 1e-12
    elev = rng.uniform(0.12, 0.6, n)[:, None]
    dirv = Nn * elev + tng * (1 - elev)
    dirv /= np.linalg.norm(dirv, axis=1, keepdims=True)
    L = (0.0035 + 0.009 * rng.random(n) ** 1.6 + (rng.random(n) < 0.04) * 0.012)[:, None]
    side = np.cross(Nn, tng)
    k = 5
    t = np.linspace(0, 1, k)[None, :, None]
    wig = rng.normal(0, 1, (n, 1, 1)) * 0.25
    S = (P - Nn * 0.0007)[:, None, :] + dirv[:, None, :] * (L[:, None, :] * t) \
        - Nn[:, None, :] * (L[:, None, :] * 0.25 * t ** 2) \
        + side[:, None, :] * (L[:, None, :] * wig * np.sin(t * math.pi))
    rad = np.linspace(0.00011, 0.00004, k)[None, :].repeat(n, 0)
    jit = rng.uniform(0.92, 1.12, (n, 1))
    col = np.clip(Cc * jit, 0, 1)
    from . import core as K, mats as MM
    mat = MM.hair_color_mat('Pluis', rough=0.5, radial=0.9, attr='col')
    mat['nofelt'] = 1
    ob = K.hair('Viltpluis', S.astype(np.float32), rad, mat, None, col=col)
    ob.visible_shadow = False
    print(f'vilt: {n} pluisvezels (schaal {scale:.2f})')
    return ob


# ------------------------------------------------------------------ luchtdoek en miniatuur
def backdrop(sky):
    """Luchtdoek: grote koepel met wollen verloop, alleen voor de camera zichtbaar."""
    if not sky:
        return None
    from . import core as K, mats as MM
    zen, hor, gnd = sky[:3]
    g = MM.NT('Luchtdoek vilt')
    co = g.coord('Object')
    x, y, z = g.sep(co)
    f = g.maprange(z, -0.08, 0.75, 0.0, 1.0)
    col = g.ramp(f, [(0.0, K.srgb(hor)), (0.12, K.srgb(hor)), (1.0, K.srgb(zen))])
    v = g.noise(co, 2.2, 4, 0.6)
    col = g.mix(1.0, col, g.comb(*(g.maprange(v, 0.3, 0.7, 0.93, 1.06),) * 3), 'MULTIPLY')
    em = g.n('ShaderNodeEmission')
    g.set(em, 'Color', col)
    g.set(em, 'Strength', float(sky[3]) if len(sky) > 3 else 1.0)
    g.m['nofelt'] = 1
    g.done(em)
    seg, ring = 64, 32
    V, F = [], []
    for i in range(ring + 1):
        th = -0.15 + (math.pi / 2 + 0.15) * i / ring
        for j in range(seg):
            ph = 2 * math.pi * j / seg
            V.append((math.cos(th) * math.cos(ph), math.cos(th) * math.sin(ph), math.sin(th)))
    for i in range(ring):
        for j in range(seg):
            j2 = (j + 1) % seg
            F.append((i * seg + j, i * seg + j2, (i + 1) * seg + j2, (i + 1) * seg + j))
    R = 90.0
    ob = K.mesh_obj('Luchtdoek', np.array(V) * R, F, g.m)
    for attr in ('visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_shadow',
                 'visible_volume_scatter'):
        setattr(ob, attr, False)
    return ob


def miniature():
    cam = bpy.context.scene.camera
    if cam is None:
        return
    cd = cam.data
    if cd.dof.use_dof:
        cd.dof.aperture_fstop = max(0.35, cd.dof.aperture_fstop * FSTOP_MULT)


def finalize():
    from . import core as K
    n = feltify()
    if getattr(K, 'SKY', None) and not bpy.data.objects.get('Luchtdoek'):
        backdrop(K.SKY)
    miniature()
    fz = fuzz()
    print(f'vilt: {n} materialen omgezet')
    return fz
