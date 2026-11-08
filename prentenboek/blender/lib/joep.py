"""Joep: het knuffelaapje van Daan (ca. 36 cm). Pluche basis + korte vacht (Hair Curves), geborduurd gezicht.

Lokaal: kijkt naar -y, z omhoog, voeten op z=0. Ledematen worden geposeerd met controlepunten.
"""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix
from . import core as K, body as B, mats as M
from .core import gauss, smoothstep
from .body import nrm

HR = 0.062  # straal hoofd

_MATS = {}


def joep_mats(daan_mats=None):
    if _MATS:
        return _MATS
    _MATS.update({
        'plush': M.plush('Pluche Joep', '#9a5626', '#ecd5ae'),
        'fur': M.hair_color_mat('Vacht Joep', None, rough=0.55, radial=0.7),
        'thread': M.thread('Borduursel', '#0b0a0a', 2600),
        'tail': M.ribbon('Staartje', '#5e321a'),
        'loop': M.ribbon('Lusje', '#f1ede4'),
    })
    if daan_mats:
        for k in ('navy', 'navy_dark', 'gloss', 'gold'):
            _MATS[k] = daan_mats[k]
    return _MATS


def face_mask(D):
    x, y, z = D[:, 0], D[:, 1], D[:, 2]
    front = smoothstep(0.05, -0.3, y)
    d_eye = np.sqrt((np.abs(x) - 0.3) ** 2 + (z - 0.12) ** 2) - 0.335
    d_muz = (np.sqrt((x / 0.5) ** 2 + ((z + 0.33) / 0.4) ** 2) - 1.0) * 0.42
    sd = np.minimum(d_eye, d_muz)
    mask = smoothstep(0.012, -0.012, sd) * front
    seam = np.exp(-(sd / 0.014) ** 2) * front
    # middennaad van de snuit (onder de neus)
    seam += np.exp(-(x / 0.012) ** 2) * smoothstep(-0.36, -0.5, z) * smoothstep(-0.8, -0.95, y) * 0.8
    # naad over het achterhoofd
    seam += np.exp(-(x / 0.012) ** 2) * smoothstep(0.1, 0.4, y) * 0.7
    return mask, np.clip(seam, 0, 1)


def head_shape(D):
    P = D * np.array([1.0, 0.94, 0.97])
    add = 0.28 * gauss(D, (0, -1, -0.45), 0.32)
    add += 0.03 * gauss(D, (0, -1, 0.15), 0.35)
    add -= 0.05 * gauss(D, (0, 0, -1), 0.4)
    return (P + D * add[:, None]) * HR


def head_surface(d):
    d = nrm(d)
    a = nrm(np.cross(d, [0, 0, 1]) if abs(d[2]) < 0.99 else np.cross(d, [1, 0, 0]))
    b = nrm(np.cross(d, a))
    e = 0.004
    D = np.array([d, nrm(d + a * e), nrm(d + b * e)])
    P = head_shape(D)
    n = nrm(np.cross(P[1] - P[0], P[2] - P[0]))
    if np.dot(n, d) < 0:
        n = -n
    return P[0], n


DEFAULT = dict(
    root=(0, 0, 0), rot=(0, 0, 0), body_tilt=(0.0, 0.0), head=(0.0, 0.0, 0.0),
    arm_r=[(-0.012, 0.0, -0.05), (-0.022, -0.004, -0.1), (-0.026, -0.008, -0.14)],
    arm_l=[(0.012, 0.0, -0.05), (0.022, -0.004, -0.1), (0.026, -0.008, -0.14)],
    leg_r=[(0.0, 0.0, -0.06), (0.002, -0.003, -0.11), (0.0, -0.008, -0.145)],
    leg_l=[(0.0, 0.0, -0.06), (-0.002, -0.003, -0.11), (0.0, -0.008, -0.145)],
    tail=[(0, 0.02, -0.03), (0.01, 0.035, -0.07), (0.02, 0.03, -0.1)],
    cap=False, cap_tilt=(-0.25, 0.18, 0.1), scale=0.82, look=None,
)


class Joep:
    def __init__(self, name='Joep', pose=None, mats=None, fur=1.0, smile=1.0):
        self.name = name
        self.p = dict(DEFAULT)
        self.p.update(pose or {})
        self.m = mats
        self.fur = fur
        self.smile = smile
        self.parts = []  # (obj, V, F, maskfn) voor de vacht

    def build(self):
        p, m = self.p, self.m
        bpy.context.view_layer.update()
        root = K.empty(self.name)
        self.root = root
        body = K.empty(self.name + '_lijf', (0, 0, 0.15), (p['body_tilt'][0], p['body_tilt'][1], 0), 1.0, root)
        self.body = body
        # boonvormig lijfje
        def bean(D, P):
            P = P.copy()
            P[:, 1] -= 0.006 * gauss(D, (0, -1, -0.2), 0.5)  # buikje
            P[:, 0] *= 1 + 0.12 * smoothstep(0.3, -0.6, D[:, 2])
            return P

        lijf = K.blob(self.name + '_romp', (0.041, 0.035, 0.056), 2.0, (64, 40), deform=bean, mat=m['plush'],
                      parent=body, loc=(0, 0, 0.045),
                      attrs_fn=lambda D, P: {'face': ('POINT', np.zeros(len(D))),
                                             'seam': ('POINT', np.exp(-(D[:, 0] / 0.03) ** 2) * 0.6)})
        self.parts.append(lijf)
        # hoofd
        piv = K.empty(self.name + '_nek', (0, 0, 0.098), (0, 0, 0), 1.0, body)
        hp = p['head']
        piv.rotation_euler = (hp[0], hp[2], hp[1])
        self.piv = piv
        D, F = K.sph(160, 96)
        P = head_shape(D)
        mask, seam = face_mask(D)
        hc = (0, -0.004, 0.056)
        head = K.mesh_obj(self.name + '_hoofd', P, F, m['plush'], piv, loc=hc,
                          attrs={'face': ('POINT', mask), 'seam': ('POINT', seam)})
        self.head = head
        self.parts.append(head)
        self.head_D = D
        # oren
        for s in (-1, 1):
            sp, n = head_surface((s, 0.12, 0.08))
            def ear_def(Dd, Pp, s=s):
                Pp = Pp.copy()
                Pp[:, 0] -= 0.4 * gauss(Dd, (-s, -0.3, 0), 0.6) * 0.008
                return Pp
            ear = K.blob(self.name + f'_oor{s}', (0.0085, 0.025, 0.027), 2.0, (32, 24), deform=ear_def,
                         mat=m['plush'], parent=head, loc=tuple(sp + n * 0.012),
                         rot=(0, 0, -s * 0.35),
                         attrs_fn=lambda Dd, Pp: {'face': ('POINT', 0.25 * gauss(Dd, (-1, -0.3, 0), 0.6)),
                                                  'seam': ('POINT', np.exp(-(Dd[:, 0] / 0.12) ** 2) * 0.7)})
            self.parts.append(ear)
        self._embroidery(head)
        # lusje bovenop
        sp, n = head_surface((0, 0.05, 1))
        A = np.linspace(0.15, math.pi - 0.15, 16)
        pts = [sp + np.array([0, 0.0, -0.002]) + np.array([math.cos(a) * 0.0085, 0, math.sin(a) * 0.016]) for a in A]
        lo, _ = K.tube(self.name + '_lusje', pts, [[0.0013, 0.0045]] * len(pts), m['loop'], head, ring=10,
                       per=3, up=(0, 1, 0))
        # armen en benen
        sh = {'r': np.array([-0.033, -0.002, 0.075]), 'l': np.array([0.033, -0.002, 0.075])}
        hi = {'r': np.array([-0.019, -0.004, 0.005]), 'l': np.array([0.019, -0.004, 0.005])}
        for k in ('r', 'l'):
            pts = [sh[k]] + [sh[k] + np.array(q) for q in p['arm_' + k]]
            rad = [0.0118, 0.0112, 0.0118, 0.0142]
            ob, t = K.tube(self.name + f'_arm{k}', pts, rad[:len(pts)] + [0.0142] * (len(pts) - 4), m['plush'],
                           body, ring=24, per=8, caps=(True, True), capf=(0.8, 1.0),
                           attrs_fn=lambda V, U, A: {'face': ('POINT', np.zeros(len(V))),
                                                     'seam': ('POINT', np.exp(-((np.cos(A) + 1) / 0.04) ** 2) * 0.8)})
            self.parts.append(ob)
            pts = [hi[k]] + [hi[k] + np.array(q) for q in p['leg_' + k]]
            rad = [0.013, 0.0128, 0.0132, 0.0158]
            ob, t = K.tube(self.name + f'_been{k}', pts, rad[:len(pts)] + [0.0158] * (len(pts) - 4), m['plush'],
                           body, ring=24, per=8, caps=(True, True), capf=(0.8, 1.0),
                           attrs_fn=lambda V, U, A: {'face': ('POINT', np.zeros(len(V))),
                                                     'seam': ('POINT', np.exp(-((np.cos(A) + 1) / 0.04) ** 2) * 0.8)})
            self.parts.append(ob)
        # staartje (plat band)
        tp = [np.array([0, 0.03, 0.012])] + [np.array([0, 0.03, 0.012]) + np.array(q) for q in p['tail']]
        K.tube(self.name + '_staart', tp, [[0.0075, 0.0018]] * len(tp), m['tail'], body, ring=16, per=8,
               up=(0, 1, 0), caps=(False, True), capf=(1, 0.4))
        if p['cap']:
            ct = p['cap_tilt']
            B.police_cap(self.name + '_pet', head, m, loc=(0.003, 0.004, 0.047), rot=ct, scale=0.0345,
                         band=(0.97, 1.01))
        if self.fur > 0:
            self._fur()
        root.location = p['root']
        root.rotation_euler = p['rot']
        root.scale = (p['scale'],) * 3
        return root

    def _embroidery(self, head):
        m = self.m
        for s in (-1, 1):
            sp, n = head_surface((0.27 * s, -1, 0.1))
            ob = K.blob(self.name + f'_oog{s}', (0.0052, 0.0072, 0.0018), 2.0, (24, 16), mat=m['thread'],
                        parent=head)
            z = n
            x = nrm(np.cross([0, 0, 1], z))
            y = np.cross(z, x)
            ob.matrix_world = Matrix.Translation(Vector(sp + n * 0.0003)) @ _rot(x, y, z)
        # neus: driehoekje
        sp, n = head_surface((0, -1, -0.27))
        tri = [(-0.0075, 0.004), (0.0075, 0.004), (0.0, -0.0055)]
        ob = K.poly_obj(self.name + '_neus', [(0.0, -0.0062), (0.0065, 0.0035), (0.0045, 0.0052), (-0.0045, 0.0052),
                                              (-0.0065, 0.0035)], depth=0.0008, bevel=0.0012, mat=m['thread'],
                        parent=head)
        z = n
        x = nrm(np.cross([0, 0, 1], z))
        y = np.cross(z, x)
        ob.matrix_world = Matrix.Translation(Vector(sp + n * 0.001)) @ _rot(x, y, z)
        # lach
        pts = []
        for t in np.linspace(-1, 1, 15):
            d = np.array([0.22 * t, -1, -0.5 + 0.13 * self.smile * t * t])
            q, nn = head_surface(d)
            pts.append(q + nn * 0.0006)
        K.curve_tube(self.name + '_lach', pts, 0.00085, m['thread'], head)

    def _fur(self):
        """Korte vacht op alle pluchedelen; kleur uit het gezichtsmasker."""
        rng = np.random.default_rng(11)
        bpy.context.view_layer.update()
        allS, allC = [], []
        for ob in self.parts:
            V, F = K.obj_mesh_np(ob, world=False)
            me = ob.data
            fa = np.zeros(len(me.vertices), np.float32)
            me.attributes['face'].data.foreach_get('value', fa)
            area = 0.0
            tris = []
            n = int(self._area(V, F) * 2.2e6 * self.fur)
            if n < 50:
                continue
            pos, nn, ti = K.sample_surface(V, F, n, rng=rng)
            # gezichtsmasker per wortel (dichtstbijzijnde hoek van de driehoek)
            tri_v = self._tri_first(F)[ti]
            face = fa[tri_v]
            # geen vacht op het borduursel
            if ob is self.head:
                dirs = nrm_rows(pos / np.array([1.0, 0.94, 0.97]))
                keep = np.ones(len(pos), bool)
                for c in ((0.27, -1, 0.1), (-0.27, -1, 0.1), (0, -1, -0.27)):
                    keep &= gauss(dirs, c, 0.06) < 0.5
                pos, nn, face = pos[keep], nn[keep], face[keep]
            Mw = np.array(ob.matrix_world)
            L = np.where(face > 0.5, 0.0024, 0.0034) * (0.75 + 0.5 * rng.random(len(pos)))
            tilt = nrm_rows(rng.normal(size=(len(pos), 3)))
            tilt = tilt - nn * (tilt * nn).sum(1, keepdims=True)
            down = np.array([0, 0, -1.0]) - nn * nn[:, 2:3]
            d = nrm_rows(nn + tilt * 0.55 + down * 0.35)
            k = 4
            t = np.linspace(0, 1, k)[None, :, None]
            S = pos[:, None, :] - nn[:, None, :] * 0.0004 + d[:, None, :] * L[:, None, None] * t
            S = S + (tilt[:, None, :] * 0.0006) * t ** 2
            Sw = S.reshape(-1, 3) @ Mw[:3, :3].T + Mw[:3, 3]
            allS.append(Sw.reshape(-1, k, 3))
            brown = np.array([0.27, 0.095, 0.03]) * (0.8 + 0.4 * rng.random((len(pos), 1)))
            cream = np.array([0.74, 0.56, 0.36]) * (0.9 + 0.2 * rng.random((len(pos), 1)))
            col = brown * (1 - face[:, None]) + cream * face[:, None]
            # wat sleets: lichtere puntjes en donkere plekjes
            col *= (0.85 + 0.3 * rng.random((len(pos), 1)))
            allC.append(col)
        S = np.concatenate(allS)
        C = np.concatenate(allC)
        rr = np.array([0.00011, 0.00009, 0.00006, 0.00003])[None, :].repeat(len(S), 0)
        # in wereldcoördinaten opgebouwd; root staat nog op de oorsprong
        self.fur_ob = K.hair(self.name + '_vacht', S, rr, self.m['fur'], None, col=C)
        self.fur_ob.parent = self.root

    @staticmethod
    def _area(V, F):
        a = 0.0
        for f in F[::max(1, len(F) // 4000)]:
            p = V[list(f)]
            a += np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])) * (1.0 if len(f) == 3 else 1.0)
        return a * max(1, len(F) // 4000) * 0.5 * 1.6

    @staticmethod
    def _tri_first(F):
        out = []
        for f in F:
            out.append(f[0])
            if len(f) == 4:
                out.append(f[0])
        return np.array(out)


def nrm_rows(A):
    return A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-12)


def _rot(x, y, z):
    M4 = Matrix.Identity(4)
    for i in range(3):
        M4[i][0], M4[i][1], M4[i][2] = x[i], y[i], z[i]
    return M4
