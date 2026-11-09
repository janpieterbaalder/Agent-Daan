"""Bijfiguren: de twee boeven en de bakker. Zelfde opbouw als Daan (buizen + IK), volwassen hoofd.

Lokaal: kijkt naar -y, voeten op z=0, maten in meters. Gestileerd: groot hoofd, ronde vormen, niet eng.
"""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler
from . import core as K, body as B, mats as M
from .head import Head
from .body import nrm, ik2
from .core import gauss, smoothstep

_M = {}


def people_mats(base):
    if _M:
        return _M
    _M.update(base)
    _M.update({
        'face_a': M.skin('Huid volwassen', '#e9b48f', painted=True, sss=0.3),
        'skin_a': M.skin('Huid volw. lijf', '#e9b48f', painted=False, sss=0.3),
        'lid_a': M.skin('Ooglid volw.', '#e2a988', painted=False),
        'ear_a': M.skin('Oor volw.', '#e6a986', painted=False, sss=0.45),
        'eye_a': M.eye('Oog bruin', '#7a5a3c', '#3b2616', pupil_r=0.25, iris_r=0.55),
        'eye_b': M.eye('Oog groen', '#7f9a62', '#3c5226', pupil_r=0.25, iris_r=0.55),
        'stripe': M.fabric('Streepshirt', '#f2efe6', rough=0.85, sheen=0.5, weave=500, stripes=('#1d1e24', 70.0)),
        'pants_dark': M.fabric('Broek donker', '#2b2d36', rough=0.85, sheen=0.3, weave=700),
        'beanie': M.fabric('Muts', '#1c1d22', rough=0.9, sheen=0.4, weave=320, strength=0.6),
        'beanie2': M.fabric('Muts rood', '#9e2b2b', rough=0.9, sheen=0.4, weave=320, strength=0.6),
        'mask': M.simple('Masker', '#121214', rough=0.45, coat=0.2, sheen=0.3),
        'hair_brown': M.hair_mat('Haar bruin', melanin=0.55, redness=0.5, rough=0.35, root_dark=0.1),
        'hair_ginger': M.hair_mat('Haar rossig', melanin=0.32, redness=0.9, rough=0.35),
        'mustache': M.hair_mat('Snor', melanin=0.45, redness=0.55, rough=0.4),
        'stubble': M.hair_mat('Stoppels', melanin=0.6, redness=0.4, rough=0.5),
        'white_coat': M.fabric('Bakkersjas', '#f7f4ee', rough=0.85, sheen=0.5, weave=700, var=0.03),
        'apron': M.fabric('Schort', '#6f93bd', rough=0.85, sheen=0.4, weave=600),
        'toque': M.fabric('Koksmuts', '#fbfaf6', rough=0.9, sheen=0.6, weave=500, var=0.02),
        'shoe_brown': M.leather('Schoen bruin', '#4a2c1a', 0.4),
        'tongue': base['tongue'], 'teeth': base['teeth'],
    })
    return _M


ADULT_HEAD = dict(adult=True, cheek=0.1, cheek_pos=(0.62, -0.55, -0.4), cheek_sigma=0.42, eye_r=0.205,
                  eye_dir=(0.33, -0.92, 0.08), eye_depth=0.55, socket=-0.03, nose=0.26,
                  nose_pos=(0, -1, -0.12), nose_sigma=0.13, mouth_z=-0.47, mouth_w=0.24, mouth_curve=1.1,
                  chin=0.08, jaw=0.04, ear_size=1.25, ear_out=0.3, flat=0.02, scale=(1.0, 0.98, 1.08),
                  scalp=False)


class Person:
    """Volwassen bijfiguur. kind: 'lang' (dunne boef), 'dik' (ronde boef), 'bakker'."""

    def __init__(self, name, kind, pose=None, expr=None, mats=None, hat=True, mask_up=0.0, hat_pop=0.0,
                 puff=0.0, baker_hat=False):
        self.name, self.kind, self.m, self.hat = name, kind, mats, hat
        self.mask_up, self.hat_pop, self.puff, self.baker_hat = mask_up, hat_pop, puff, baker_hat
        self.pose = dict(root=(0, 0, 0), yaw=0.0, lean=(0.0, 0.0), head=(0, 0, 0), hand_r=None, hand_l=None,
                         elbow_r=(-0.3, 0.6, -0.3), elbow_l=(0.3, 0.6, -0.3), palm_r=None, palm_l=None,
                         fdir_r=None, fdir_l=None, fingers_r='relaxed', fingers_l='relaxed', foot_r=None,
                         foot_l=None, knee_r=(0, -1, 0), knee_l=(0, -1, 0), hip=None, toe_r=None, toe_l=None,
                         sit=False)
        self.pose.update(pose or {})
        self.expr = expr or {}
        if kind == 'lang':
            self.dim = dict(hip=0.78, spine=0.5, rx=0.16, ry=0.13, belly=0.0, sh=0.125, arm=(0.26, 0.24),
                            leg=(0.36, 0.34), legr=0.068, armr=0.055, head_s=0.2, cloth='stripe',
                            pants='pants_dark', shoe='shoe', hand=1.75)
        elif kind == 'dik':
            self.dim = dict(hip=0.5, spine=0.48, rx=0.27, ry=0.24, belly=0.07, sh=0.2, arm=(0.21, 0.2),
                            leg=(0.24, 0.22), legr=0.088, armr=0.068, head_s=0.21, cloth='stripe',
                            pants='pants_dark', shoe='shoe', hand=1.8)
        else:
            self.dim = dict(hip=0.62, spine=0.52, rx=0.26, ry=0.24, belly=0.08, sh=0.2, arm=(0.24, 0.22),
                            leg=(0.29, 0.28), legr=0.088, armr=0.072, head_s=0.21, cloth='white_coat',
                            pants='pants_dark', shoe='shoe_brown', hand=1.85)

    def build(self):
        p, m, d = self.pose, self.m, self.dim
        bpy.context.view_layer.update()
        root = K.empty(self.name)
        self.root = root
        hip = np.array(p['hip'] if p['hip'] is not None else (0, 0, d['hip']), dtype=float)
        lf, ls = p['lean']
        L = d['spine']
        zs = np.linspace(0, L, 6)
        spine = []
        for z in zs:
            t = z / L
            spine.append(hip + np.array([math.sin(ls * t) * z, -math.sin(lf * t) * z, z * math.cos(lf * t)]))
        spine = np.array(spine)
        self.spine = spine
        rx, ry, bel = d['rx'], d['ry'], d['belly']
        R = np.array([[rx * 0.95, ry * 0.92], [rx * 1.0 + bel, ry + bel], [rx * 1.02 + bel, ry + bel * 1.2],
                      [rx * 0.98 + bel * 0.5, ry * 0.95 + bel * 0.4], [rx * 0.86, ry * 0.8], [rx * 0.45, ry * 0.42]])
        sp = spine.copy()
        sp[1:4, 1] -= np.array([0.3, 0.6, 0.3]) * bel
        cloth = m[d['cloth']]
        self.torso_ob, self.torso = K.tube(self.name + '_romp', sp, R, cloth, root, ring=56, per=8,
                                           caps=(True, True), up=(0, -1, 0), capf=(0.7, 0.5))
        Bv = self.torso.B[-10]
        self.sh = {'r': spine[-2] - Bv * d['sh'] + np.array([0, 0.01, 0.0]),
                   'l': spine[-2] + Bv * d['sh'] + np.array([0, 0.01, 0.0])}
        self.neck = spine[-1]
        self._arms(cloth)
        self._legs(m[d['pants']])
        self._head()
        if self.kind == 'bakker':
            self._apron()
        root.location = p['root']
        root.rotation_euler = (0, 0, math.radians(p['yaw']))
        return root

    def _arms(self, cloth):
        p, m, d = self.pose, self.m, self.dim
        a, b = d['arm']
        r = d['armr']
        for side in (-1, 1):
            k = 'r' if side < 0 else 'l'
            S = self.sh[k]
            tgt = p['hand_' + k]
            if tgt is None:
                tgt = S + np.array([0.06 * side, 0.03, -(a + b) * 0.92])
            E, W = ik2(S, tgt, a, b, p['elbow_' + k], stretch=1.4)
            pts = [S + nrm(S - E) * 0.02, (S + E) / 2, E, E + (W - E) * 0.55, W]
            K.tube(self.name + f'_arm{k}', pts, [r * 1.08, r, r * 0.95, r * 0.88, r * 0.84], cloth, self.root,
                   ring=32, per=6, caps=(True, True), capf=(1, 0.3))
            fdir = nrm(W - E if p['fdir_' + k] is None else np.asarray(p['fdir_' + k], dtype=float))
            palm = p['palm_' + k] if p['palm_' + k] is not None else np.array([-side, 0, 0.0])
            B.hand(self.name + f'_hand{k}', W + fdir * 0.004, fdir, palm, side, m['skin_a'], self.root,
                   curl=p['fingers_' + k], scale=d['hand'], chub=1.05)

    def _legs(self, pants):
        p, m, d = self.pose, self.m, self.dim
        hip = np.array(p['hip'] if p['hip'] is not None else (0, 0, d['hip']), dtype=float)
        a, b = d['leg']
        r = d['legr']
        for side in (-1, 1):
            k = 'r' if side < 0 else 'l'
            H0 = hip + np.array([d['rx'] * 0.48 * side, 0, -0.02])
            tgt = p['foot_' + k]
            if tgt is None:
                tgt = (d['rx'] * 0.55 * side, 0.0, 0.075)
            Kn, Ft = ik2(H0, tgt, a, b, p['knee_' + k])
            pts = [H0 + np.array([0, 0, 0.05]), (H0 + Kn) / 2, Kn, Kn + (Ft - Kn) * 0.6, Ft + nrm(Ft - Kn) * 0.02]
            K.tube(self.name + f'_been{k}', pts, [r * 1.1, r, r * 0.92, r * 0.88, r * 0.9], pants, self.root,
                   ring=32, per=6, caps=(True, True), capf=(1, 0.3))
            toe = p['toe_' + k] or (0, -1, 0)
            sm = dict(m)
            sm['shoe'] = m[d['shoe']]
            B.shoe(self.name + f'_schoen{k}', Ft + np.array([0, 0, 0.015]), toe, sm, self.root, scale=1.45)

    def _head(self):
        p, m, d = self.pose, self.m, self.dim
        T = nrm(self.spine[-1] - self.spine[-3])
        top = self.neck
        neck_top = top + T * 0.02
        K.tube(self.name + '_nek', [top - T * 0.05, neck_top + T * 0.05], [0.07, 0.066], m['skin_a'], self.root,
               ring=24, per=3, caps=(False, False))
        pitch, yaw, roll = [math.radians(v) for v in p['head']]
        lf, ls = p['lean']
        piv = K.empty(self.name + '_hoofdpivot', tuple(neck_top), (0, 0, 0), 1.0, self.root)
        piv.rotation_mode = 'YXZ'
        piv.rotation_euler = (lf * 0.8 + pitch, ls * 0.8 + roll, yaw)
        S = d['head_s']
        hloc = (0, -0.02, S * 0.86)
        pp = dict(ADULT_HEAD)
        ex = dict(self.expr)
        if 'look_at' in ex:
            rl = Vector(p['root'])
            Mroot = Matrix.Translation(rl) @ Euler((0, 0, math.radians(p['yaw']))).to_matrix().to_4x4()
            loc = Mroot.inverted() @ Vector(ex['look_at'])
            Mpiv = Matrix.Translation(Vector(neck_top)) @ Euler(tuple(piv.rotation_euler), 'YXZ').to_matrix().to_4x4()
            hl = (Mpiv @ Matrix.Translation(Vector(hloc)) @ Matrix.Scale(S, 4)).inverted() @ loc
            ex['look'] = (hl.x, hl.y, hl.z, 1.0)
        if self.kind == 'dik':
            pp.update(cheek=0.2 + self.puff, cheek_sigma=0.5, nose=0.3, nose_sigma=0.14, scale=(1.04, 0.98, 1.0))
        elif self.kind == 'lang':
            pp.update(cheek=0.04 + self.puff, scale=(0.92, 0.98, 1.16), nose=0.28, nose_pos=(0, -1, -0.1),
                      chin=0.12, jaw=0.0)
        hm = dict(m)
        hm.update(face=m['face_a'], lid=m['lid_a'], ear=m['ear_a'],
                  eye=m['eye_b'] if self.kind == 'lang' else m['eye_a'])
        h = Head(self.name + '_hoofd', p=pp, expr=ex)
        h.build(piv, hm, scale=S, loc=hloc)
        self.headobj = h
        hair_col = m['hair_ginger'] if self.kind == 'dik' else m['hair_brown']
        h.brows(hm, hair_col, density=1.6, length=0.09)
        if self.kind in ('lang', 'dik'):
            self._mask(h)
            if self.baker_hat:
                self._toque(h, hair=False)
            elif self.hat:
                self._beanie(h, m['beanie'] if self.kind == 'lang' else m['beanie2'])
            self._stubble(h)
        else:
            self._mustache(h)
            self._toque(h)
        self.piv = piv

    def _mask(self, h):
        """Zwart oogmasker (domino) als schil om de ogen."""
        D, F = K.sph(160, 90)
        x, y, z = D[:, 0], D[:, 1], D[:, 2]
        ez = h.p['eye_dir'][2] + self.mask_up
        band = np.exp(-((z - ez) / 0.17) ** 4) * smoothstep(-0.1, -0.5, y) * (1 - 0.6 * np.exp(-(x / 0.06) ** 2) *
                                                                            smoothstep(ez - 0.02, ez - 0.2, z))
        keep = band > 0.35
        P = h.shape(D) * 1.0 + D * 0.025
        # alleen vlakken waarvan alle hoeken binnen het masker liggen
        Fk = [f for f in F if all(keep[i] for i in f)]
        used = sorted({i for f in Fk for i in f})
        remap = {o: n for n, o in enumerate(used)}
        V = P[used]
        Fn = [tuple(remap[i] for i in f) for f in Fk]
        ob = K.mesh_obj(h.name + '_masker', V, Fn, self.m['mask'], h.root)
        if self.mask_up:
            ob.location = (0, 0, 0.0)
            # opgeschoven masker ligt iets verder van het hoofd af (op het voorhoofd)
            for v in ob.data.vertices:
                v.co = v.co * 1.04
        K.solidify(ob, 0.02, 0.0)
        K.subsurf(ob, 1)
        # ooggaten: oogleden staan er al; het masker ligt eroverheen tot aan de oogbol

    def _beanie(self, h, mat):
        prof = [(0.98, 0.3), (1.02, 0.42), (1.0, 0.62), (0.88, 0.82), (0.62, 0.98), (0.28, 1.06), (0.0, 1.08)]
        hp = K.empty(h.name + '_mutsrig', (0, 0, self.hat_pop), (-0.12 - 0.5 * self.hat_pop, 0, 0.3 * self.hat_pop), 1.0, h.root)
        ob = K.lathe(h.name + '_muts', prof, 64, mat, hp, sx=1.03, sy=1.0, close_bot=False)
        rim = K.lathe(h.name + '_mutsrand', [(1.0, 0.28), (1.07, 0.32), (1.08, 0.46), (1.02, 0.5)], 64, mat, hp,
                      sx=1.03, sy=1.0, close_bot=False, close_top=False)
        K.blob(h.name + '_pompon', (0.2, 0.2, 0.2), 2.0, (24, 16), mat=mat, parent=hp, loc=(0, 0.1, 1.15))

    def _stubble(self, h, n=5000):
        rng = np.random.default_rng(21)
        D = rng.normal(size=(n * 3, 3))
        D /= np.linalg.norm(D, axis=1, keepdims=True)
        w = smoothstep(-0.15, -0.55, D[:, 2]) * smoothstep(0.0, -0.4, D[:, 1])
        w *= 1 - np.exp(-((D[:, 2] - h.p['mouth_z']) / 0.05) ** 2) * (np.abs(D[:, 0]) < 0.2)
        D = D[rng.random(len(D)) < w][:n]
        P = h.shape(D)
        Nn = P / np.linalg.norm(P, axis=1, keepdims=True)
        S = np.stack([P - Nn * 0.003, P + Nn * 0.012], 1)
        K.hair(h.name + '_stoppels', S, (0.0018, 0.0008), self.m['stubble'], h.root)

    def _mustache(self, h):
        rng = np.random.default_rng(31)
        strands = []
        for s in (-1, 1):
            for i in range(1400):
                t = rng.random()
                d = np.array([s * (0.02 + 0.2 * t), -1, h.p['nose_pos'][2] - 0.13 - 0.04 * t + rng.normal(0, 0.015)])
                sp, n = h.surface(d)
                out = nrm(np.array([s * 1.0, -0.4, -0.25 + 0.5 * t * t]))
                L = 0.09 + 0.1 * (1 - abs(t - 0.5))
                pts = [sp - n * 0.005]
                for k in range(1, 5):
                    f = k / 4
                    pts.append(sp + n * 0.035 * math.sin(f * 2.2) + out * L * f + np.array([0, 0, 0.06 * f * f * t]))
                strands.append(np.array(pts))
        K.hair(h.name + '_snor', strands, (0.006, 0.002), self.m['mustache'], h.root)

    def _toque(self, h, hair=True):
        band = K.lathe(h.name + '_koksband', [(1.0, 0.35), (1.02, 0.6), (1.0, 0.7)], 64, self.m['toque'], h.root,
                       sx=1.0, sy=1.0, close_bot=False, close_top=False)
        rng = np.random.default_rng(5)
        for i in range(9):
            a = i / 9 * 2 * math.pi
            K.blob(h.name + f'_koksbol{i}', (0.42, 0.42, 0.42), 2.0, (32, 20), mat=self.m['toque'], parent=h.root,
                   loc=(math.cos(a) * 0.55, math.sin(a) * 0.55, 1.05 + 0.08 * rng.random()))
        K.blob(h.name + '_kokstop', (0.75, 0.75, 0.5), 2.0, (40, 24), mat=self.m['toque'], parent=h.root,
               loc=(0, 0, 1.15))
        K.lathe(h.name + '_kokscil', [(0.98, 0.65), (1.08, 1.0)], 64, self.m['toque'], h.root, close_bot=False,
                close_top=False)
        if not hair:
            return
        # kort haar opzij
        D = np.random.default_rng(9).normal(size=(9000, 3))
        D /= np.linalg.norm(D, axis=1, keepdims=True)
        D = D[(D[:, 2] < 0.4) & (D[:, 2] > -0.25) & (D[:, 1] > -0.3)]
        D = D[np.abs(D[:, 0]) > 0.3]
        P = h.shape(D)
        Nn = P / np.linalg.norm(P, axis=1, keepdims=True)
        S = np.stack([P - Nn * 0.004, P + Nn * 0.02 + np.array([0, 0.02, -0.03]), P + Nn * 0.03 + np.array([0, 0.03, -0.06])], 1)
        K.hair(h.name + '_zijhaar', S, (0.004, 0.0015), self.m['hair_brown'], h.root)

    def _apron(self):
        t = self.torso
        V, F = [], []
        nu, nv = 16, 18
        for i in range(nu):
            for j in range(nv):
                a = -0.95 + 1.9 * i / (nu - 1)
                u = 0.0 + 0.62 * j / (nv - 1)
                pnt, n = t.point(u, a, 0.012)
                V.append(pnt + np.array([0, 0, -0.18 * (1 - j / (nv - 1)) ** 2 * 0.0]))
        for i in range(nu - 1):
            for j in range(nv - 1):
                F.append((i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1))
        ob = K.mesh_obj(self.name + '_schort', np.array(V), F, self.m['apron'], self.root)
        K.solidify(ob, 0.006, 1.0)
        # knoopjes jas
        for i, u in enumerate((0.72, 0.82, 0.92)):
            for s in (-0.25, 0.25):
                pnt, n = t.point(u, s, 0.006)
                K.blob(self.name + f'_jasknoop{i}{s}', (0.012, 0.012, 0.012), 2.0, (12, 8), mat=self.m['gold'],
                       parent=self.root, loc=tuple(pnt))
