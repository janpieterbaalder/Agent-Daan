"""Daan: peuter van drie in politie-uniform (of pyjama). Bouwt alles rond een root-empty op de grond.

Lokaal: personage kijkt naar -y, x = zijn linkerkant, z omhoog. Maten in meters (ca. 0,95 m lang).
"""
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler
from . import core as K, body as B, hair as H
from .head2 import Head
from .body import nrm, ik2, frame_from

HEAD_S = 0.152

DEFAULT_POSE = dict(
    root=(0, 0, 0), yaw=0.0, lean=(0.0, 0.0), twist=0.0, hip=(0, 0, 0.29), hip_tilt=0.0,
    head=(0.0, 0.0, 0.0),
    hand_r=None, hand_l=None, elbow_r=(-0.3, 0.6, -0.2), elbow_l=(0.3, 0.6, -0.2),
    palm_r=None, palm_l=None, fdir_r=None, fdir_l=None, fingers_r='relaxed', fingers_l='relaxed',
    foot_r=(-0.066, 0.0, 0.058), foot_l=(0.066, 0.0, 0.058), knee_r=(0, -1, 0), knee_l=(0, -1, 0),
    toe_r=None, toe_l=None,
)


class Daan:
    def __init__(self, name='Daan', pose=None, expr=None, outfit='uniform', cap=True, hair='auto', mats=None,
                 hair_density=1.0):
        self.name = name
        self.pose = dict(DEFAULT_POSE)
        self.pose.update(pose or {})
        self.expr = expr or {}
        self.outfit = outfit
        self.cap = cap
        self.hair = ('pet' if cap else 'kuif') if hair == 'auto' else hair
        self.m = mats
        self.hd = hair_density

    # ------------------------------------------------------------------ romp
    def build(self):
        p, m = self.pose, self.m
        bpy.context.view_layer.update()
        root = K.empty(self.name)
        self.root = root
        hip = np.array(p['hip'], dtype=float)
        lf, ls = p['lean']
        # wervelkolom: bekken -> nek, buigt naar voren (-y) en opzij
        zs = np.array([0.0, 0.06, 0.12, 0.18, 0.24, 0.285])
        spine = []
        for z in zs:
            t = z / zs[-1]
            ang_f, ang_s = lf * t, ls * t
            spine.append(hip + np.array([math.sin(ang_s) * z * 0.9, -math.sin(ang_f) * z * 0.9 - 0.008 * math.sin(t * 3),
                                         z * math.cos(ang_f) * math.cos(ang_s)]))
        spine = np.array(spine)
        self.spine = spine
        twist = p['twist']
        shirt = m['pj'] if self.outfit == 'pajama' else m['navy']
        pants = m['pj'] if self.outfit == 'pajama' else m['navy']
        # rompbuis (shirt): ellipsen, buikje naar voren
        R = np.array([[0.112, 0.094], [0.122, 0.104], [0.127, 0.11], [0.122, 0.1], [0.11, 0.088],
                      [0.068, 0.058]])
        sp_shirt = spine.copy()
        sp_shirt[1:4, 1] -= np.array([0.006, 0.012, 0.006])
        up = (math.sin(twist), -math.cos(twist), 0)
        self.torso_ob, self.torso = K.tube(self.name + '_romp', sp_shirt[1:], R[1:], shirt, root, ring=56, per=8,
                                           caps=(True, True), up=up, capf=(0.6, 0.55))
        # broek: heupen
        hp = np.array([hip + np.array([0, 0.004, -0.012]), hip + np.array([0, 0, 0.025]),
                       spine[1] + np.array([0, -0.004, 0.015])])
        self.pants_ob, self.pants = K.tube(self.name + '_broekromp', hp,
                                           [[0.11, 0.09], [0.123, 0.103], [0.128, 0.108]], pants, root, ring=48,
                                           per=6, caps=(True, False), up=up, capf=(0.7, 1))
        top = spine[-1]
        T, N, Bv = self.torso.T, self.torso.N, self.torso.B
        tN, tB = N[-12], Bv[-12]
        self.sh_r = spine[-2] + np.array([0, 0.006, -0.006]) - tB * 0.098
        self.sh_l = spine[-2] + np.array([0, 0.006, -0.006]) + tB * 0.098
        self.neck = top
        self._arms(shirt)
        self._legs(pants)
        self._head()
        if self.outfit == 'uniform':
            self._uniform_details()
        else:
            self._pajama_details()
        # alles staat lokaal; nu pas de root plaatsen
        root.location = p['root']
        root.rotation_euler = (0, 0, math.radians(p['yaw']))
        return root

    # ------------------------------------------------------------------ armen
    def _arms(self, shirt):
        p, m = self.pose, self.m
        a, b = 0.112, 0.1
        self.wrists = {}
        for side, S0 in ((-1, self.sh_r), (1, self.sh_l)):
            k = 'r' if side < 0 else 'l'
            tgt = p['hand_' + k]
            if tgt is None:
                tgt = S0 + np.array([0.04 * side, 0.015, -0.19])
            E, W = ik2(S0, tgt, a, b, p['elbow_' + k], stretch=1.75)
            S = S0
            pts = [S + nrm(S - E) * 0.012, S + (E - S) * 0.5, E, E + (W - E) * 0.55, W]
            rad = [[0.047, 0.045], [0.044, 0.042], [0.04, 0.039], [0.038, 0.037], [0.036, 0.035]]
            K.tube(self.name + f'_mouw{k}', pts, rad, shirt, self.root, ring=32, per=6, caps=(True, False),
                   up=(0, 0, 1))
            fdir = W - E if p['fdir_' + k] is None else np.asarray(p['fdir_' + k], dtype=float)
            fdir = nrm(fdir)
            # manchet
            cuff_mat = m['pj_cuff'] if self.outfit == 'pajama' else m['navy_dark']
            K.tube(self.name + f'_manchet{k}', [W - fdir * 0.016, W + fdir * 0.002], [[0.039, 0.038], [0.038, 0.037]],
                   cuff_mat, self.root, ring=32, per=3, caps=(False, True), capf=(1, 0.3))
            palm = p['palm_' + k]
            if palm is None:
                palm = np.array([-side * 1.0, 0.0, 0.0])
            wrist = W + fdir * 0.006
            B.hand(self.name + f'_hand{k}', wrist, fdir, palm, side, m['skin'], self.root, curl=p['fingers_' + k],
                   scale=1.2)
            self.wrists[k] = (wrist, fdir, palm)
            if self.outfit == 'uniform':
                self._ring_stitch(self.name + f'_stiksel_manchet{k}', W - fdir * 0.0115, fdir, 0.0393)

    # ------------------------------------------------------------------ benen
    def _legs(self, pants):
        p, m = self.pose, self.m
        hip = np.array(p['hip'], dtype=float)
        a, b = 0.122, 0.112
        for side in (-1, 1):
            k = 'r' if side < 0 else 'l'
            H0 = hip + np.array([0.064 * side, 0.002, -0.02])
            A, _ = None, None
            tgt = np.asarray(p['foot_' + k], dtype=float)
            Kn, Ft = ik2(H0, tgt, a, b, p['knee_' + k])
            pts = [H0 + np.array([0, 0, 0.03]), H0 + (Kn - H0) * 0.5, Kn, Kn + (Ft - Kn) * 0.6, Ft + nrm(Ft - Kn) * 0.01]
            rad = [[0.064, 0.06], [0.06, 0.058], [0.054, 0.053], [0.051, 0.05], [0.05, 0.049]]
            K.tube(self.name + f'_been{k}', pts, rad, pants, self.root, ring=36, per=6, caps=(False, True),
                   up=(0, -1, 0), capf=(1, 0.25))
            toe = p['toe_' + k]
            fwd = (0, -1, 0) if toe is None else toe
            if self.outfit == 'pajama':
                foot = K.blob(self.name + f'_voet{k}', (0.036, 0.06, 0.028), 2.2, (32, 20), mat=m['skin'],
                              parent=self.root, loc=tuple(Ft + nrm(np.array([fwd[0], fwd[1], 0])) * 0.03 -
                                                          np.array([0, 0, 0.03])))
            else:
                B.shoe(self.name + f'_schoen{k}', Ft, fwd, m, self.root)

    # ------------------------------------------------------------------ hoofd
    def _head(self):
        p, m = self.pose, self.m
        top = self.neck
        T = nrm(self.spine[-1] - self.spine[-3])
        # nek
        neck_top = top + T * 0.045
        K.tube(self.name + '_nek', [top - T * 0.03, neck_top + T * 0.03], [0.05, 0.048], m['skin'], self.root,
               ring=24, per=3, caps=(False, False))
        pitch, yaw, roll = [math.radians(v) for v in p['head']]
        lf, ls = p['lean']
        base = Euler((lf * 0.9 + pitch, ls * 0.9 + roll, p['twist'] + yaw), 'YXZ')
        piv = K.empty(self.name + '_hoofdpivot', tuple(neck_top), (0, 0, 0), 1.0, self.root)
        piv.rotation_mode = 'YXZ'
        piv.rotation_euler = (lf * 0.85 + pitch, ls * 0.85 + roll, p['twist'] + yaw)
        # hoofd: midden boven en iets voor de nek
        hloc = (0, -0.012, 0.108)
        if 'look_at' in self.expr:
            rl = Vector(p['root'])
            Mroot = Matrix.Translation(rl) @ Euler((0, 0, math.radians(p['yaw']))).to_matrix().to_4x4()
            loc = Mroot.inverted() @ Vector(self.expr['look_at'])
            Mpiv = Matrix.Translation(Vector(neck_top)) @ Euler(tuple(piv.rotation_euler), 'YXZ').to_matrix().to_4x4()
            Mh = Mpiv @ Matrix.Translation(Vector(hloc)) @ Matrix.Scale(HEAD_S, 4)
            hl = Mh.inverted() @ loc
            self.expr = dict(self.expr)
            self.expr['look'] = (hl.x, hl.y, hl.z, 1.0)
        self.head = Head(self.name + '_hoofd', expr=self.expr)
        self.head.build(piv, m, scale=HEAD_S, loc=hloc)
        self.head.brows(m, m['brow'])
        cap_line = lambda D: 0.5 - 0.07 * D[:, 1]
        hs = self.hair
        if hs == 'kuif':
            H.build(self.head, m, 'kuif', n_top=int(60000 * self.hd), n_short=int(110000 * self.hd))
        elif hs == 'pet':
            H.build(self.head, m, 'pet', n_short=int(110000 * self.hd), cap_line=cap_line, pony=True)
        if self.cap:
            B.police_cap(self.name + '_pet', self.head.root, m, loc=(0, 0.1, 0.6), rot=(-0.1, 0, 0), scale=1.05)
        self.piv = piv

    # ------------------------------------------------------------------ uniform
    def _surf(self, tube, u, ang, off=0.0):
        p, n = tube.point(u, ang, off)
        return np.asarray(p), np.asarray(n)

    def _u_at_z(self, tube, z):
        return float(np.interp(z, tube.C[:, 2], tube.u))

    def _patch(self, name, tube, z0, z1, a0, a1, off, mat, thick=0.003, nu=10, nv=8, round_bottom=0.0):
        """Lapje (zak, klep, beleg) dat het rompoppervlak volgt."""
        V, F = [], []
        for i in range(nu):
            for j in range(nv):
                t = i / (nu - 1)
                s = j / (nv - 1)
                z = z0 + (z1 - z0) * s
                # onderhoeken afronden
                shrink = 0.0
                if round_bottom and s < 0.25:
                    edge = min(t, 1 - t)
                    shrink = round_bottom * (1 - s / 0.25) ** 2 * (1 - min(edge / 0.25, 1)) ** 2
                a = a0 + (a1 - a0) * (t * (1 - 2 * shrink) + shrink)
                u = self._u_at_z(tube, z)
                pnt, _ = self._surf(tube, u, a, off)
                V.append(pnt)
        for i in range(nu - 1):
            for j in range(nv - 1):
                F.append((i * nv + j, (i + 1) * nv + j, (i + 1) * nv + j + 1, i * nv + j + 1))
        ob = K.mesh_obj(name, np.array(V), F, mat, self.root)
        K.solidify(ob, thick, 1.0)
        K.modifier(ob, 'BEVEL', width=thick * 0.45, segments=2, limit_method='ANGLE')
        return ob

    def _path(self, tube, az, off, per=40):
        """Lijn over het rompoppervlak door punten (hoek, z); geeft punten en normalen."""
        az = np.asarray(az, float)
        A, Z = [], []
        for i in range(len(az) - 1):
            t = np.linspace(0, 1, per, endpoint=False)
            A.append(az[i, 0] + (az[i + 1, 0] - az[i, 0]) * t)
            Z.append(az[i, 1] + (az[i + 1, 1] - az[i, 1]) * t)
        A.append([az[-1, 0]])
        Z.append([az[-1, 1]])
        A, Z = np.concatenate(A), np.concatenate(Z)
        P, N = [], []
        for a, z in zip(A, Z):
            pnt, n = self._surf(tube, self._u_at_z(tube, z), a, off)
            P.append(pnt)
            N.append(n)
        return np.array(P), np.array(N)

    def _stitches(self, name, P, Nn, dash=0.0052, gap=0.0034, r=0.0008):
        """Rijgsteek: korte stukjes garen die in en uit de stof duiken."""
        mat = self.m.get('stitch_thread')
        if mat is None:
            from . import mats as MM
            mat = self.m['stitch_thread'] = MM.thread('Stiksel', '#a6b5dc', scale=3000)
        P, Nn = np.asarray(P, float), np.asarray(Nn, float)
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        strands = []
        x = gap * 0.5
        lift = np.array([-0.0007, 0.0004, 0.0004, -0.0007])
        while x + dash < s[-1]:
            ts = np.linspace(x, x + dash, 4)
            q = np.stack([np.interp(ts, s, P[:, i]) for i in range(3)], 1)
            n = np.stack([np.interp(ts, s, Nn[:, i]) for i in range(3)], 1)
            n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
            strands.append(q + n * lift[:, None])
            x += dash + gap
        if strands:
            K.hair(name, strands, (r, r * 0.9), mat, self.root)

    def _ring_stitch(self, name, c, axis, rad):
        axis = nrm(axis)
        e1 = nrm(np.cross(axis, [0, 0, 1]) if abs(axis[2]) < 0.9 else np.cross(axis, [1, 0, 0]))
        e2 = np.cross(axis, e1)
        th = np.linspace(0, 2 * math.pi, 140)
        Nn = np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2
        self._stitches(name, c + Nn * rad, Nn)

    def _button(self, name, pos, n, mat, r=0.0055, h=0.0025):
        # knoop: platte cilinder (blob) met de as langs de normaal
        ob = K.blob(name, (r, r, h), 3.0, (24, 12), mat=mat, parent=self.root)
        z = nrm(n)
        x = nrm(np.cross([0, 0, 1], z) if abs(z[2]) < 0.95 else np.cross([0, 1, 0], z))
        y = np.cross(z, x)
        B.set_world(ob, pos + z * h * 0.6, np.stack([x, y, z], 1))
        return ob

    def _uniform_details(self):
        m, t = self.m, self.torso
        z_top = t.C[-1, 2]
        zb = self.pose['hip'][2] + 0.05
        # knoopsluiting (beleg) midden voor
        self._patch(self.name + '_beleg', t, zb, z_top - 0.05, -0.085, 0.085, 0.0005, m['navy'], thick=0.0025,
                    nu=6, nv=14)
        for s_ in (-1, 1):
            P_, N_ = self._path(t, [(s_ * 0.062, zb + 0.004), (s_ * 0.062, z_top - 0.052)], 0.0036)
            self._stitches(self.name + f'_stiksel_beleg{s_}', P_, N_)
        for i, z in enumerate(np.linspace(zb + 0.03, z_top - 0.075, 4)):
            u = self._u_at_z(t, z)
            pnt, n = self._surf(t, u, 0.0, 0.003)
            self._button(self.name + f'_knoop{i}', pnt, n, m['silver'], r=0.0052)
        # borstzakken met klep en knoopje
        for s in (-1, 1):
            zc = z_top - 0.105
            a0, a1 = (0.22, 0.62) if s > 0 else (-0.62, -0.22)
            self._patch(self.name + f'_zak{s}', t, zc - 0.045, zc + 0.006, a0, a1, 0.0008, m['navy'], thick=0.003,
                        round_bottom=0.6)
            self._patch(self.name + f'_klep{s}', t, zc - 0.002, zc + 0.016, a0 - 0.03, a1 + 0.03, 0.0035,
                        m['navy'], thick=0.003, nv=5, round_bottom=0.3)
            da, dz = 0.05, 0.006
            P_, N_ = self._path(t, [(a0 + da, zc - 0.002), (a0 + da, zc - 0.045 + dz), (a1 - da, zc - 0.045 + dz),
                                    (a1 - da, zc - 0.002)], 0.0044)
            self._stitches(self.name + f'_stiksel_zak{s}', P_, N_)
            P_, N_ = self._path(t, [(a0 - 0.03 + da, zc + 0.012), (a0 - 0.03 + da, zc + 0.002),
                                    (a1 + 0.03 - da, zc + 0.002), (a1 + 0.03 - da, zc + 0.012)], 0.0071)
            self._stitches(self.name + f'_stiksel_klep{s}', P_, N_)
            u = self._u_at_z(t, zc + 0.002)
            pnt, n = self._surf(t, u, (a0 + a1) / 2, 0.0075)
            self._button(self.name + f'_zakknoop{s}', pnt, n, m['silver'], r=0.0042)
        # gouden ster links op de borst (boven de zak)
        u = self._u_at_z(t, z_top - 0.07)
        pnt, n = self._surf(t, u, 0.44, 0.004)
        st = K.poly_obj(self.name + '_ster', K.round_star_pts(0.0175, 0.5), depth=0.002, bevel=0.0018,
                        mat=m['gold'], parent=self.root)
        z = nrm(n)
        x = nrm(np.cross([0, 0, 1], z))
        y = np.cross(z, x)
        B.set_world(st, pnt + z * 0.002, np.stack([x, y, z], 1))
        # kraag
        self._collar(m['navy'])
        # schouderlusjes
        for s, S0 in ((-1, self.sh_r), (1, self.sh_l)):
            c = self.neck + (S0 - self.neck) * 0.15 + np.array([0, 0, -0.012])
            e = S0 + np.array([0, 0, 0.012])
            d = nrm(e - c)
            pts = [c, (c + e) / 2 + np.array([0, 0, 0.004]), e]
            ob, tb = K.tube(self.name + f'_epaulet{s}', pts, [[0.004, 0.012]] * 3, m['navy_dark'], self.root,
                            ring=16, per=4, up=(0, 0, 1))
            self._button(self.name + f'_epknoop{s}', e - d * 0.012 + np.array([0, 0, 0.006]), np.array([0, 0, 1.0]),
                         m['silver'], r=0.0045)
        # riem met gesp
        zbelt = self.pose['hip'][2] + 0.035
        up = self.pants.N[len(self.pants.C) // 2]
        hp = self.pants
        uu = float(np.interp(zbelt, hp.C[:, 2], hp.u))
        # riem als band: lathe-achtige ring van de broekrompbuis
        V, F = [], []
        nA = 64
        for i, a in enumerate(np.linspace(0, 2 * math.pi, nA, endpoint=False)):
            for j, dz in enumerate((-0.014, 0.014)):
                u2 = float(np.interp(zbelt + dz, hp.C[:, 2], hp.u))
                q, nn = hp.point(u2, a, 0.0045)
                V.append(q)
        for i in range(nA):
            i2 = (i + 1) % nA
            F.append((i * 2, i2 * 2, i2 * 2 + 1, i * 2 + 1))
        rb = K.mesh_obj(self.name + '_riemband', np.array(V), F, m['belt'], self.root)
        K.solidify(rb, 0.004, 1.0)
        K.modifier(rb, 'BEVEL', width=0.0015, segments=2, limit_method='ANGLE')
        for dz in (-0.0095, 0.0095):
            u2 = float(np.interp(zbelt + dz, hp.C[:, 2], hp.u))
            P_, N_ = [], []
            for a in np.linspace(0.35, 2 * math.pi - 0.35, 160):
                q_, n_ = hp.point(u2, a, 0.0089)
                P_.append(q_)
                N_.append(n_)
            self._stitches(self.name + f'_stiksel_riem{dz > 0}', P_, N_, dash=0.0045, gap=0.003, r=0.0007)
        q, nn = hp.point(uu, 0.0, 0.009)
        z = nrm(nn)
        x = nrm(np.cross([0, 0, 1], z))
        y = np.cross(z, x)
        gesp = K.blob(self.name + '_gesp', (0.019, 0.015, 0.004), 6.0, (24, 12), mat=m['silver'], parent=self.root)
        B.set_world(gesp, q, np.stack([x, y, z], 1))
        inner = K.blob(self.name + '_gespgat', (0.013, 0.009, 0.004), 6.0, (24, 12), mat=m['belt'],
                       parent=self.root)
        B.set_world(inner, q + z * 0.0015, np.stack([x, y, z], 1))
        # portofoon op de rechterheup
        q, nn = hp.point(uu - 0.12, -1.75, 0.02)
        z = nrm(nn)
        x = nrm(np.cross([0, 0, 1], z))
        y = np.cross(z, x)
        rad = K.blob(self.name + '_portofoon', (0.019, 0.032, 0.012), 4.0, (32, 16), mat=m['radio'],
                     parent=self.root)
        B.set_world(rad, q + np.array([0, 0, -0.012]), np.stack([x, y, z], 1))
        ant = K.tube(self.name + '_antenne', [q + np.array([0, 0, 0.018]) + x * 0.009, q + np.array([0, 0, 0.055]) + x * 0.009],
                     [0.0035, 0.0028], m['radio'], self.root, ring=10, per=2)
        led = K.blob(self.name + '_led', (0.0025, 0.0025, 0.0025), 2, (8, 6), mat=m['radio_led'], parent=self.root,
                     loc=tuple(q + np.array([0, 0, 0.016]) + z * 0.012 - x * 0.008))

    def _collar(self, mat):
        """Overhemdkraag: band om de nek die naar buiten omslaat, met punten voor."""
        nk = self.neck
        T = nrm(self.spine[-1] - self.spine[-3])
        V, F = [], []
        nA, nR = 48, 6
        A = np.linspace(-math.pi + 0.22, math.pi - 0.22, nA)  # opening vooraan
        for i, a in enumerate(A):
            front = abs(a) / math.pi
            for j, t in enumerate(np.linspace(0, 1, nR)):
                # binnen (rechtop tegen de nek) -> buiten (plat op de schouders), punten voor langer
                r = 0.05 + 0.032 * t + 0.022 * t * front ** 3
                z = 0.022 * (1 - t) - 0.012 * t - 0.03 * t * front ** 4
                x = math.sin(a) * r
                y = math.cos(a) * r * 0.92  # a=0 achter? -> zet voor op -y
                V.append(nk + np.array([x, y, z]) + T * 0.0)
        # oriëntatie: a=0 => +y (achter); opening vooraan bij a = +-pi (-y)
        for i in range(nA - 1):
            for j in range(nR - 1):
                F.append((i * nR + j, i * nR + j + 1, (i + 1) * nR + j + 1, (i + 1) * nR + j))
        ob = K.mesh_obj(self.name + '_kraag', np.array(V), F, mat, self.root)
        K.solidify(ob, 0.004, 0.0)
        K.subsurf(ob, 1)
        return ob

    def _pajama_details(self):
        self._collar(self.m['pj_cuff'])
