"""Materialen (Cycles-nodes), allemaal procedureel."""
import bpy
from .core import srgb, mixc


class NT:
    """Klein hulpje om node-bomen in code op te bouwen."""

    def __init__(self, name):
        self.m = bpy.data.materials.new(name)
        self.m.use_nodes = True
        self.t = self.m.node_tree
        self.t.nodes.clear()
        self.out = self.t.nodes.new('ShaderNodeOutputMaterial')

    def _in(self, nd, k):
        if isinstance(k, int):
            return nd.inputs[k]
        for s in nd.inputs:
            if (s.name == k or s.identifier == k) and s.enabled:
                return s
        return nd.inputs[k]

    def _out(self, nd, k=None):
        if k is None:
            for s in nd.outputs:
                if s.enabled:
                    return s
            return nd.outputs[0]
        if isinstance(k, int):
            return nd.outputs[k]
        for s in nd.outputs:
            if (s.name == k or s.identifier == k) and s.enabled:
                return s
        return nd.outputs[k]

    def set(self, nd, k, v):
        s = self._in(nd, k)
        if isinstance(v, bpy.types.NodeSocket):
            self.t.links.new(v, s)
        elif isinstance(v, bpy.types.Node):
            self.t.links.new(self._out(v), s)
        else:
            if isinstance(v, (tuple, list)) and len(v) == 3 and len(s.default_value) == 4:
                v = (*v, 1.0)
            s.default_value = v

    def n(self, typ, ins=None, **attrs):
        nd = self.t.nodes.new(typ)
        for k, v in attrs.items():
            setattr(nd, k, v)
        for k, v in (ins or {}).items():
            self.set(nd, k, v)
        return nd

    # --- bouwstenen
    def coord(self, kind='Object'):
        return self._out(self.n('ShaderNodeTexCoord'), kind)

    def attr(self, name, out='Color', kind='GEOMETRY'):
        nd = self.n('ShaderNodeAttribute', attribute_name=name, attribute_type=kind)
        return self._out(nd, out)

    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.n('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.set(nd, 0, a)
        if b is not None:
            self.set(nd, 1, b)
        if c is not None:
            self.set(nd, 2, c)
        return nd.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        nd = self.n('ShaderNodeVectorMath', operation=op)
        self.set(nd, 0, a)
        if b is not None:
            self.set(nd, 1, b)
        if scale is not None:
            self.set(nd, 'Scale', scale)
        return self._out(nd, 'Value' if op in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE') else 'Vector')

    def sep(self, v):
        nd = self.n('ShaderNodeSeparateXYZ')
        self.set(nd, 0, v)
        return nd.outputs[0], nd.outputs[1], nd.outputs[2]

    def comb(self, x, y, z):
        nd = self.n('ShaderNodeCombineXYZ')
        for i, v in enumerate((x, y, z)):
            self.set(nd, i, v)
        return nd.outputs[0]

    def mix(self, fac, a, b, blend='MIX', clamp=True):
        nd = self.n('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_result=clamp)
        self.set(nd, 'Factor', fac)
        self.set(nd, 'A', a)
        self.set(nd, 'B', b)
        return self._out(nd, 'Result')

    def mixf(self, fac, a, b):
        nd = self.n('ShaderNodeMix', data_type='FLOAT')
        self.set(nd, 'Factor', fac)
        self.set(nd, 'A', a)
        self.set(nd, 'B', b)
        return self._out(nd, 'Result')

    def maprange(self, v, a, b, c=0.0, d=1.0, interp='LINEAR', clamp=True):
        nd = self.n('ShaderNodeMapRange', interpolation_type=interp, clamp=clamp)
        self.set(nd, 'Value', v)
        self.set(nd, 'From Min', a)
        self.set(nd, 'From Max', b)
        self.set(nd, 'To Min', c)
        self.set(nd, 'To Max', d)
        return self._out(nd, 'Result')

    def ramp(self, fac, stops, interp='LINEAR'):
        nd = self.n('ShaderNodeValToRGB')
        self.set(nd, 'Fac', fac)
        cr = nd.color_ramp
        cr.interpolation = interp
        while len(cr.elements) < len(stops):
            cr.elements.new(0.5)
        for e, (p, c) in zip(cr.elements, stops):
            e.position = p
            e.color = c if len(c) == 4 else (*c, 1)
        return nd.outputs['Color']

    def noise(self, vec=None, scale=5.0, detail=2.0, rough=0.5, distortion=0.0, dims='3D', out='Fac', w=None):
        nd = self.n('ShaderNodeTexNoise', noise_dimensions=dims)
        if vec is not None:
            self.set(nd, 'Vector', vec)
        self.set(nd, 'Scale', scale)
        self.set(nd, 'Detail', detail)
        self.set(nd, 'Roughness', rough)
        self.set(nd, 'Distortion', distortion)
        if w is not None:
            self.set(nd, 'W', w)
        return self._out(nd, out)

    def voronoi(self, vec=None, scale=5.0, feature='F1', out='Distance', rand=1.0, metric='EUCLIDEAN'):
        nd = self.n('ShaderNodeTexVoronoi', feature=feature, distance=metric)
        if vec is not None:
            self.set(nd, 'Vector', vec)
        self.set(nd, 'Scale', scale)
        self.set(nd, 'Randomness', rand)
        return self._out(nd, out)

    def wave(self, vec=None, scale=5.0, kind='BANDS', axis='X', profile='SIN', distortion=0.0, detail=0.0,
             phase=0.0):
        nd = self.n('ShaderNodeTexWave', wave_type=kind, bands_direction=axis, rings_direction=axis,
                    wave_profile=profile)
        if vec is not None:
            self.set(nd, 'Vector', vec)
        self.set(nd, 'Scale', scale)
        self.set(nd, 'Distortion', distortion)
        self.set(nd, 'Detail', detail)
        self.set(nd, 'Phase Offset', phase)
        return self._out(nd, 'Fac')

    def mapping(self, vec, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        nd = self.n('ShaderNodeMapping')
        self.set(nd, 'Vector', vec)
        self.set(nd, 'Location', loc)
        self.set(nd, 'Rotation', rot)
        self.set(nd, 'Scale', scale)
        return nd.outputs[0]

    def bump(self, height, strength=0.3, distance=0.01, normal=None):
        nd = self.n('ShaderNodeBump')
        self.set(nd, 'Height', height)
        self.set(nd, 'Strength', strength)
        self.set(nd, 'Distance', distance)
        if normal is not None:
            self.set(nd, 'Normal', normal)
        return nd.outputs[0]

    def principled(self, **kw):
        nd = self.n('ShaderNodeBsdfPrincipled')
        names = {
            'color': 'Base Color', 'rough': 'Roughness', 'metal': 'Metallic', 'sss': 'Subsurface Weight',
            'sss_radius': 'Subsurface Radius', 'sss_scale': 'Subsurface Scale', 'coat': 'Coat Weight',
            'coat_rough': 'Coat Roughness', 'sheen': 'Sheen Weight', 'sheen_rough': 'Sheen Roughness',
            'sheen_tint': 'Sheen Tint', 'emit': 'Emission Color', 'emit_strength': 'Emission Strength',
            'trans': 'Transmission Weight', 'ior': 'IOR', 'normal': 'Normal', 'alpha': 'Alpha',
            'spec': 'Specular IOR Level', 'aniso': 'Anisotropic', 'coat_normal': 'Coat Normal',
            'spec_tint': 'Specular Tint', 'coat_tint': 'Coat Tint',
        }
        for k, v in kw.items():
            self.set(nd, names.get(k, k), v)
        return nd

    def done(self, shader, disp=None):
        self.t.links.new(self._out(shader) if isinstance(shader, bpy.types.Node) else shader,
                         self.out.inputs['Surface'])
        if disp is not None:
            self.t.links.new(disp, self.out.inputs['Displacement'])
        return self.m


C = lambda h: srgb(h)


# ---------------------------------------------------------------- basismaterialen
def simple(name, color, rough=0.5, metal=0.0, coat=0.0, sheen=0.0, sss=0.0, bump=0.0, bump_scale=60.0, **kw):
    g = NT(name)
    nrm = None
    if bump:
        nrm = g.bump(g.noise(g.coord('Object'), bump_scale, 4, 0.6), bump, 0.01)
    col = C(color) if isinstance(color, str) else color
    p = g.principled(color=col, rough=rough, metal=metal, coat=coat, sheen=sheen, sss=sss, **kw)
    if nrm is not None:
        g.set(p, 'Normal', nrm)
    return g.done(p)


def emission(name, color, strength=5.0):
    g = NT(name)
    nd = g.n('ShaderNodeEmission', {'Color': C(color) if isinstance(color, str) else color, 'Strength': strength})
    return g.done(nd)


def glass(name, tint='#ffffff', rough=0.0, ior=1.45, alpha_refl=False):
    g = NT(name)
    p = g.principled(color=C(tint), rough=rough, trans=1.0, ior=ior)
    return g.done(p)


def thin_glass(name, tint='#ffffff', refl=0.12):
    """Ruit: bijna onzichtbaar, met spiegeling (geen breking)."""
    g = NT(name)
    tr = g.n('ShaderNodeBsdfTransparent', {'Color': C(tint)})
    gl = g.n('ShaderNodeBsdfGlossy', {'Color': (1, 1, 1, 1), 'Roughness': 0.03})
    fr = g.n('ShaderNodeFresnel', {'IOR': 1.5})
    f = g.math('ADD', g._out(fr), refl * 0.2)
    mx = g.n('ShaderNodeMixShader')
    g.set(mx, 0, f)
    g.set(mx, 1, tr)
    g.set(mx, 2, gl)
    return g.done(mx)


def gold(name='Goud', color='#e9b44c', rough=0.2):
    g = NT(name)
    co = g.coord('Object')
    rv = g.maprange(g.noise(co, 220, 3, 0.6), 0.3, 0.7, rough * 0.7, rough * 1.5)
    p = g.principled(color=C(color), metal=1.0, rough=rv)
    g.set(p, 'Normal', g.bump(g.noise(co, 900, 2), 0.04, 0.002))
    return g.done(p)


def silver(name='Zilver'):
    return gold(name, '#c9ced6', 0.22)


def gloss_black(name='Lak zwart', rough=0.18):
    g = NT(name)
    co = g.coord('Object')
    p = g.principled(color=C('#0c0d11'), rough=rough, coat=1.0, coat_rough=0.04, spec=0.5)
    g.set(p, 'Normal', g.bump(g.noise(co, 140, 3), 0.025, 0.01))
    return g.done(p)


def leather(name, color='#141416', rough=0.45):
    g = NT(name)
    co = g.coord('Object')
    p = g.principled(color=C(color), rough=rough, coat=0.3, coat_rough=0.25)
    h = g.voronoi(co, 900, out='Distance')
    g.set(p, 'Normal', g.bump(h, 0.12, 0.002))
    return g.done(p)


# ---------------------------------------------------------------- huid
def skin(name='Huid', base='#f4c9b1', painted=True, sss=0.35, rough=0.42):
    """Huid met subsurface. painted: kleur uit kleurattribuut 'paint' (blos, lippen) maal basiskleur."""
    g = NT(name)
    co = g.coord('Object')
    basec = C(base)
    if painted:
        col = g.mix(1.0, basec, g.attr('paint'), blend='MULTIPLY')
    else:
        col = basec
    # heel lichte vlekjes en variatie
    var = g.noise(co, 9, 3, 0.5)
    col = g.mix(g.maprange(var, 0.35, 0.7, 0.0, 0.06), col, C('#e9a48f'))
    rough_v = g.maprange(g.noise(co, 35, 2), 0.3, 0.7, rough - 0.06, rough + 0.06)
    p = g.principled(color=col, rough=rough_v, sss=sss, sss_radius=(1.0, 0.42, 0.25), sss_scale=0.018,
                     spec=0.42, coat=0.04, coat_rough=0.3)
    pores = g.noise(co, 420, 2, 0.5)
    g.set(p, 'Normal', g.bump(pores, 0.025, 0.0006))
    return g.done(p)


def eye(name='Oog', iris='#6f8fae', iris2='#3f5f7f', pupil_r=0.2, iris_r=0.48):
    """Oogbol in eenheidscoördinaten, kijkt naar -Y. Iris en pupil uit de objectcoördinaten."""
    g = NT(name)
    co = g.coord('Object')
    x, y, z = g.sep(co)
    r = g.math('SQRT', g.math('ADD', g.math('MULTIPLY', x, x), g.math('MULTIPLY', z, z)))
    front = g.math('LESS_THAN', y, 0.0)
    rr = g.math('ADD', g.math('MULTIPLY', r, front), g.math('MULTIPLY', g.math('SUBTRACT', 1.0, front), 1.0))
    ang = g.math('ARCTAN2', x, z)
    fib = g.noise(g.comb(g.math('MULTIPLY', ang, 3.0), g.math('MULTIPLY', rr, 2.0), 0.0), 6.0, 3, 0.6)
    fib2 = g.noise(g.comb(g.math('MULTIPLY', ang, 9.0), g.math('MULTIPLY', rr, 12.0), 0.0), 3.0, 2, 0.6)
    ic, ic2 = C(iris), C(iris2)
    light = mixc(ic, (1, 1, 1, 1), 0.18)
    irisc = g.ramp(rr, [(0.0, (0.004, 0.004, 0.006, 1)), (pupil_r, (0.004, 0.004, 0.006, 1)),
                        (pupil_r + 0.025, mixc(ic2, (0, 0, 0, 1), 0.3)),
                        (pupil_r + 0.09, light),
                        (iris_r - 0.1, ic),
                        (iris_r - 0.025, ic2),
                        (iris_r, (0.03, 0.035, 0.05, 1)),
                        (iris_r + 0.04, C('#efece8')),
                        (1.0, C('#e6d9d4'))])
    t = g.math('MULTIPLY', g.maprange(rr, pupil_r, iris_r, 0, 1), g.math('LESS_THAN', rr, iris_r))
    shade = g.maprange(g.math('ADD', fib, g.math('MULTIPLY', fib2, 0.5)), 0.4, 1.1, 0.75, 1.25)
    shade = g.mixf(t, 1.0, shade)
    col = g.mix(1.0, irisc, g.comb(shade, shade, shade), blend='MULTIPLY')
    p = g.principled(color=col, rough=0.03, coat=1.0, coat_rough=0.0, spec=0.6, sss=0.08,
                     sss_radius=(0.5, 0.3, 0.3), sss_scale=0.004)
    g.m['nofelt'] = 1
    return g.done(p)


def hair_mat(name='Haar', melanin=0.16, redness=0.45, rough=0.32, radial=0.35, random_color=0.12, coat=0.05,
             tint=(1, 1, 1), root_dark=0.0):
    g = NT(name)
    h = g.n('ShaderNodeBsdfHairPrincipled', parametrization='MELANIN')
    try:
        h.model = 'CHIANG'
    except Exception:
        pass
    ins = {'Melanin': melanin, 'Melanin Redness': redness, 'Roughness': rough, 'Radial Roughness': radial,
           'Random Color': random_color, 'Coat': coat, 'Tint': (*tint, 1), 'Random Roughness': 0.15}
    for k, v in ins.items():
        try:
            g.set(h, k, v)
        except Exception:
            pass
    rnd = g.n('ShaderNodeHairInfo')
    g.set(h, 'Random', g._out(rnd, 'Random'))
    if root_dark:
        # wortels iets donkerder: diepte in de lokken
        mel = g.maprange(g._out(rnd, 'Intercept'), 0.0, 0.45, melanin + root_dark, melanin)
        g.set(h, 'Melanin', mel)
    return g.done(h)


def hair_color_mat(name, color=None, rough=0.45, radial=0.6, attr='col', coat=0.0):
    """Haar/vacht met directe kleur (per haar uit attribuut 'col' of vaste kleur)."""
    g = NT(name)
    h = g.n('ShaderNodeBsdfHairPrincipled', parametrization='COLOR')
    try:
        h.model = 'CHIANG'
    except Exception:
        pass
    g.set(h, 'Color', g.attr(attr) if color is None else C(color))
    g.set(h, 'Roughness', rough)
    g.set(h, 'Radial Roughness', radial)
    try:
        g.set(h, 'Coat', coat)
        g.set(h, 'Random Roughness', 0.2)
    except Exception:
        pass
    return g.done(h)


# ---------------------------------------------------------------- stof
def fabric(name, color, rough=0.75, sheen=0.6, weave=900.0, strength=0.22, stripes=None, dots=None,
           sheen_tint=(1, 1, 1), var=0.07):
    """Geweven stof. stripes=(kleur2, frequentie op z), dots=(kleur2, schaal)."""
    g = NT(name)
    co = g.coord('Object')
    c1 = C(color) if isinstance(color, str) else color
    col = c1
    if stripes:
        c2, freq = stripes
        x, y, z = g.sep(co)
        s = g.math('GREATER_THAN', g.math('SINE', g.math('MULTIPLY', z, freq)), 0.0)
        col = g.mix(s, c1, C(c2))
    if dots:
        c2, sc = dots
        d = g.voronoi(co, sc, out='Distance', rand=0.0)
        col = g.mix(g.math('LESS_THAN', d, 0.22), col, C(c2))
    v = g.noise(co, 6, 3, 0.55)
    col = g.mix(g.maprange(v, 0.3, 0.7, 0, 1), g.mix(1.0, col, (1 - var, 1 - var, 1 - var, 1), 'MULTIPLY'),
                g.mix(1.0, col, (1 + var, 1 + var, 1 + var, 1), 'MULTIPLY'))
    w1 = g.wave(co, weave, 'BANDS', 'X', 'SIN')
    w2 = g.wave(co, weave, 'BANDS', 'Z', 'SIN')
    w3 = g.wave(co, weave, 'BANDS', 'Y', 'SIN')
    h = g.math('ADD', g.math('MULTIPLY', w1, w2), g.math('MULTIPLY', w3, 0.5))
    h = g.math('ADD', h, g.math('MULTIPLY', g.noise(co, weave * 0.25, 2), 0.6))
    p = g.principled(color=col, rough=rough, sheen=sheen, sheen_rough=0.45, sheen_tint=(*sheen_tint, 1),
                     spec=0.3)
    g.set(p, 'Normal', g.bump(h, strength, 0.0015))
    return g.done(p)


def plush(name='Pluche', brown='#a8622b', cream='#ecd6b1', worn=0.12):
    """Basis onder de vacht van Joep: kleur uit attribuut 'face' (0 bruin, 1 crème), naden uit 'seam'."""
    g = NT(name)
    co = g.coord('Object')
    face = g.math('MINIMUM', g.attr('face', 'Fac'), 1.0)
    col = g.mix(face, C(brown), C(cream))
    v = g.noise(co, 30, 4, 0.6)
    col = g.mix(g.maprange(v, 0.35, 0.75, 0, worn), col, C('#5a3015'))
    seam = g.attr('seam', 'Fac')
    p = g.principled(color=col, rough=0.9, sheen=1.0, sheen_rough=0.35, sheen_tint=(1, 0.92, 0.8, 1), spec=0.2)
    h = g.math('SUBTRACT', g.math('MULTIPLY', g.noise(co, 400, 2), 0.25), g.math('MULTIPLY', seam, 1.0))
    g.set(p, 'Normal', g.bump(h, 0.6, 0.0015))
    return g.done(p)


def thread(name='Borduurgaren', color='#0d0c0c', scale=900.0, axis='X'):
    g = NT(name)
    co = g.coord('Object')
    w = g.wave(co, scale, 'BANDS', axis, 'SIN', distortion=1.5, detail=1)
    p = g.principled(color=C(color), rough=0.38, sheen=0.6, sheen_rough=0.3, spec=0.5, aniso=0.6)
    g.set(p, 'Normal', g.bump(w, 0.6, 0.0008))
    g.m['nofelt'] = 1
    return g.done(p)


def ribbon(name, color, rough=0.6):
    """Band (lusje, staartje): keperweefsel."""
    g = NT(name)
    co = g.coord('Object')
    m = g.mapping(co, rot=(0, 0, 0.785))
    w = g.wave(m, 1400, 'BANDS', 'X', 'SIN')
    p = g.principled(color=C(color), rough=rough, sheen=0.5, sheen_rough=0.4)
    g.set(p, 'Normal', g.bump(w, 0.25, 0.001))
    return g.done(p)


# ---------------------------------------------------------------- omgeving
def painted(name, base='#ffffff', rough=0.55, var=0.06, scale=4.0, attr=None, bump=0.05, coat=0.0,
            sheen=0.0):
    """Gelakt/geverfd oppervlak met lichte variatie. attr: kleur uit attribuut vermenigvuldigd."""
    g = NT(name)
    co = g.coord('Object')
    col = C(base) if isinstance(base, str) else base
    if attr:
        col = g.mix(1.0, col, g.attr(attr), 'MULTIPLY')
    v = g.noise(co, scale, 3, 0.55)
    col = g.mix(g.maprange(v, 0.25, 0.75, 0, 1), g.mix(1.0, col, (1 - var,) * 3 + (1,), 'MULTIPLY'),
                g.mix(1.0, col, (1 + var,) * 3 + (1,), 'MULTIPLY'))
    p = g.principled(color=col, rough=rough, coat=coat, coat_rough=0.1, sheen=sheen)
    if bump:
        g.set(p, 'Normal', g.bump(g.noise(co, 80, 3), bump, 0.004))
    return g.done(p)


def wood(name='Hout', c1='#c48a52', c2='#9a6232', rough=0.45, scale=6.0, coat=0.0):
    g = NT(name)
    co = g.coord('Object')
    m = g.mapping(co, scale=(1, 1, 8))
    w = g.wave(m, scale, 'RINGS', 'Z', 'SAW', distortion=6, detail=3)
    n = g.noise(co, 40, 3)
    col = g.mix(g.maprange(g.math('ADD', w, g.math('MULTIPLY', n, 0.3)), 0.2, 1.0, 0, 1), C(c1), C(c2))
    p = g.principled(color=col, rough=rough, coat=coat, coat_rough=0.12, spec=0.4)
    g.set(p, 'Normal', g.bump(g.math('ADD', w, n), 0.06, 0.003))
    return g.done(p)


def brick(name='Baksteen', c1='#a24a32', c2='#7b3626', mortar='#d9cfbf', scale=6.0, rough=0.85):
    g = NT(name)
    co = g.coord('Object')
    b = g.n('ShaderNodeTexBrick', offset=0.5, squash=1.0)
    g.set(b, 'Vector', co)
    g.set(b, 'Color1', C(c1))
    g.set(b, 'Color2', C(c2))
    g.set(b, 'Mortar', C(mortar))
    g.set(b, 'Scale', scale)
    g.set(b, 'Mortar Size', 0.03)
    g.set(b, 'Mortar Smooth', 0.3)
    g.set(b, 'Bias', 0.0)
    g.set(b, 'Brick Width', 1.0)
    g.set(b, 'Row Height', 0.25)
    n = g.noise(co, 30, 4)
    col = g.mix(g.maprange(n, 0.3, 0.8, 0, 0.25), g._out(b, 'Color'), C('#5a2a1a'))
    p = g.principled(color=col, rough=rough, spec=0.3)
    h = g.math('ADD', g.math('MULTIPLY', g.math('SUBTRACT', 1.0, g._out(b, 'Fac')), 1.0),
               g.math('MULTIPLY', n, 0.15))
    g.set(p, 'Normal', g.bump(h, 0.35, 0.01))
    return g.done(p)


def vertex_colored(name, rough=0.7, bump=0.15, bump_scale=60.0, sss=0.0, coat=0.0, attr='col', sheen=0.0,
                   trans=0.0):
    """Kleur uit kleurattribuut (bijv. per klinker of per blad)."""
    g = NT(name)
    co = g.coord('Object')
    col = g.attr(attr)
    n = g.noise(co, bump_scale, 4, 0.6)
    col = g.mix(g.maprange(n, 0.3, 0.8, 0, 0.18), col, (0.2, 0.15, 0.1, 1), 'MULTIPLY')
    p = g.principled(color=col, rough=rough, sss=sss, sss_radius=(1, 0.8, 0.4), sss_scale=0.01, coat=coat,
                     sheen=sheen, trans=trans)
    if bump:
        g.set(p, 'Normal', g.bump(n, bump, 0.005))
    return g.done(p)


def leaves(name='Blad', attr='col'):
    """Bladeren: kleur per blad, doorschijnend."""
    g = NT(name)
    co = g.coord('Object')
    col = g.attr(attr)
    n = g.noise(co, 25, 3)
    col = g.mix(g.maprange(n, 0.3, 0.8, 0, 0.2), col, C('#d6e86a'))
    p = g.principled(color=col, rough=0.48, sheen=0.25, spec=0.45)
    tr = g.n('ShaderNodeBsdfTranslucent', {'Color': g.mix(1.0, col, (1.3, 1.5, 0.8, 1), 'MULTIPLY')})
    mx = g.n('ShaderNodeMixShader')
    g.set(mx, 0, 0.28)
    g.set(mx, 1, p)
    g.set(mx, 2, tr)
    return g.done(mx)


def bark(name='Schors', c1='#7a5236', c2='#4b3020'):
    g = NT(name)
    co = g.coord('Object')
    m = g.mapping(co, scale=(1, 1, 0.18))
    n = g.noise(m, 18, 6, 0.65, distortion=0.4)
    v = g.voronoi(m, 14, out='Distance')
    h = g.math('ADD', n, g.math('MULTIPLY', v, 0.7))
    col = g.mix(g.maprange(h, 0.4, 1.3, 0, 1), C(c2), C(c1))
    p = g.principled(color=col, rough=0.8)
    g.set(p, 'Normal', g.bump(h, 0.6, 0.02))
    return g.done(p)


def cookie(name='Koek', c1='#d8a058', c2='#a8642a'):
    g = NT(name)
    co = g.coord('Object')
    n = g.noise(co, 90, 6, 0.65)
    v = g.voronoi(co, 140, out='Distance')
    rim = g.attr('rim', 'Fac')
    col = g.mix(g.math('ADD', g.math('MULTIPLY', rim, 0.8), g.maprange(n, 0.35, 0.8, 0, 0.3)), C(c1), C(c2))
    p = g.principled(color=col, rough=0.72, sss=0.15, sss_radius=(1, 0.6, 0.3), sss_scale=0.003, sheen=0.3)
    h = g.math('ADD', n, g.math('MULTIPLY', g.math('SUBTRACT', 1.0, v), 0.4))
    g.set(p, 'Normal', g.bump(h, 0.55, 0.002))
    return g.done(p)


def burlap(name='Jute', color='#b48c58'):
    g = NT(name)
    co = g.coord('Object')
    w1 = g.wave(co, 260, 'BANDS', 'X', 'SIN', distortion=2, detail=2)
    w2 = g.wave(co, 260, 'BANDS', 'Z', 'SIN', distortion=2, detail=2)
    h = g.math('MAXIMUM', w1, w2)
    n = g.noise(co, 40, 4)
    col = g.mix(g.maprange(g.math('ADD', h, n), 0.6, 1.8, 0, 1), C('#6e5130'), C(color))
    p = g.principled(color=col, rough=0.95, sheen=0.7, sheen_rough=0.5)
    g.set(p, 'Normal', g.bump(g.math('ADD', h, g.math('MULTIPLY', n, 0.5)), 0.7, 0.002))
    return g.done(p)


def ground_cobble(name='Klinker'):
    return vertex_colored(name, rough=0.82, bump=0.35, bump_scale=45.0)


def cornea(name='Hoornvlies', ior=1.376):
    """Glas voor camera- en reflectiestralen, doorzichtig voor schaduwstralen (geen zwarte iris)."""
    g = NT(name)
    lp = g.n('ShaderNodeLightPath')
    gl = g.n('ShaderNodeBsdfGlass', {'Color': (1, 1, 1, 1), 'Roughness': 0.0, 'IOR': ior})
    tr = g.n('ShaderNodeBsdfTransparent', {'Color': (1, 1, 1, 1)})
    mx = g.n('ShaderNodeMixShader')
    g.set(mx, 0, g._out(lp, 'Is Shadow Ray'))
    g.set(mx, 1, gl)
    g.set(mx, 2, tr)
    return g.done(mx)
