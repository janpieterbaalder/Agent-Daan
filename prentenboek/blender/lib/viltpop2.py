"""Viltpoppen v2: slanke poppen, opgebouwd zoals een echte viltpop.

- Een naaldgevilte kern (kop, nek, handjes) in huidkleurige wol.
- Kleding als losse lapjes vilt over die kern: een hemd met mouwen en een uitlopende zoom, een broek met
  rechte pijpen, witte sokjes, laarsjes met veters en een lichtere zoolrand. Elk lapje heeft een zichtbare
  dikte en rand, met rijgsteken langs de randen.
- Gezicht zoals bij viltpoppen: glanzende kraaloogjes, een bolletje als neus, roze blosjes, een klein
  geborduurd mondje en (bij uitdrukkingen) dunne wenkbrauwen van garen.
- Haar van garen: lokjes van gedraaide wol die onder de pet uitkomen of een kuif vormen.

Lokaal: pop kijkt naar -y, x = linkerkant van de pop, z omhoog, maten in meters.
"""
import math
import numpy as np
from . import core as K, sdf as S, mats as M
from .body import ik2
from .viltpop import (wol, kraal, garen, Lump, fbounds, piece, to_surf, surf, hit, frame, applique, stitches,
                      thread_line, ellipse, rrect, star, shield, _n, _rot_to, F32, _MC, _cached, wol_streep, ARMS,
                      _densify)

ONES = lambda V: {'paint': ('POINT', np.ones((len(V), 3), F32))}

DAAN = dict(
    skin='#f2c9ae', hair='#efd28a', shirt='#1a2552', shirt2='#24316a', pants='#161f45', shoe='#232327',
    sock='#f4f1ea', star='#f2b21a', iris='#1c2c4c',
    head_c=(0, -0.004, 0.655), head_r=(0.132, 0.122, 0.138),
    torso=[((0, 0.0, 0.415), (0.082, 0.068, 0.13)), ((0, 0.0, 0.33), (0.086, 0.07, 0.07))],
    shoulder=(0.08, 0.0, 0.525), arm=(0.115, 0.11), arm_r=0.029, hand=(0.029, 0.025, 0.04),
    hip=(0.042, 0.0, 0.305), leg=(0.108, 0.104), leg_r=0.041, ankle_z=0.098,
    hem=0.285, belt=0.322, cloth=0.012, neck=0.027,
    foot=(0.038, 0.062, 0.034), hair_style='auto',
)


def _rot_cols(d, up=(0, 0, 1)):
    """Rotatiematrix (kolommen = lokale assen) met lokale z langs d."""
    d = _n(d)
    u = np.cross(up, d)
    if np.linalg.norm(u) < 1e-4:
        u = np.cross((0, 1, 0), d)
    u = _n(u)
    v = np.cross(d, u)
    return np.stack([u, v, d], 1).astype(F32)


def ring_stitch(name, c, axis, rad, mat, parent, dash=0.0045, gap=0.003):
    axis = _n(axis)
    R = _rot_cols(axis)
    th = np.linspace(0, 2 * math.pi, 120)
    N = np.cos(th)[:, None] * R[:, 0] + np.sin(th)[:, None] * R[:, 1]
    return stitches(name, np.asarray(c) + N * rad, N, mat, parent, dash=dash, gap=gap)


class Pop:
    """Slanke viltpop. pose: root, yaw, lean (graden), head (pitch, yaw, roll), arm_r/arm_l (ARMS-naam,
    'salute' of (dx,dy,dz) t.o.v. de schouder), legs ('stand', 'step', 'sit', 'floor', 'tiptoe').
    expr: mouth ('smile', 'grin', 'open', 'o', 'sad', 'flat', 'none'), eyes ('open', 'closed', 'happy'),
    brows ('none', 'up', 'worried', 'cross'), blush."""

    def __init__(self, name, spec, pose=None, expr=None, outfit='uniform', cap=True):
        self.name = name
        self.sp = dict(spec)
        self.p = dict(root=(0, 0, 0), yaw=0.0, lean=0.0, head=(0, 0, 0), arm_r='down', arm_l='down', legs='stand')
        self.p.update(pose or {})
        self.e = dict(mouth='smile', eyes='open', brows='none', blush=1.0, look=(0, 0))
        self.e.update(expr or {})
        self.outfit = outfit
        self.cap = cap

    # ------------------------------------------------------------------ materialen per outfit
    def _mats(self):
        sp = self.sp
        o = self.outfit
        m = dict(skin=wol('Vilt huid2 ' + sp['skin'], sp['skin'], attr='paint', fuzz=1.6),
                 shoe=wol('Vilt laars ' + sp['shoe'], sp['shoe'], fuzz=1.6),
                 sole=wol('Vilt zool', '#8c857a', sheet=True),
                 sock=wol('Vilt sok', sp['sock'], fuzz=2.0),
                 black=wol('Vilt zwart2', '#202024', fuzz=1.6),
                 thread=garen('Garen licht', '#d8deef'))
        if o == 'pyjama':
            m.update(shirt=wol('Vilt pyjama2', '#8fc0e2', fuzz=1.8), pants=wol('Vilt pyjama2', '#8fc0e2', fuzz=1.8),
                     shirt2=wol('Vilt pyjama licht2', '#e2f0f8', sheet=True), thread=garen('Garen wit', '#ffffff'))
        elif o == 'bakker':
            m.update(shirt=wol('Vilt bakkerwit2', '#efe9dd', fuzz=1.8), pants=wol('Vilt bakkerbroek2', '#5a5d6a', fuzz=1.8),
                     shirt2=wol('Vilt schort', '#fbf8f2', sheet=True), thread=garen('Garen rood', '#c63b33'))
        elif o == 'boef':
            m.update(shirt=wol_streep('Vilt boevenstreep2', '#efebe2', '#222329', 0.045),
                     pants=wol('Vilt boevenbroek', '#26262c', fuzz=1.8), shirt2=wol('Vilt grijs2', '#9a9aa2', sheet=True),
                     thread=garen('Garen wit', '#ffffff'))
        else:
            m.update(shirt=wol('Vilt hemd ' + sp['shirt'], sp['shirt'], fuzz=1.8),
                     pants=wol('Vilt broek ' + sp['pants'], sp['pants'], fuzz=1.8),
                     shirt2=wol('Vilt hemd2 ' + sp['shirt2'], sp['shirt2'], sheet=True))
        return m

    # ------------------------------------------------------------------ skelet
    def _tilt(self, c):
        lean = math.radians(self.p['lean'])
        zp = self.sp['hip'][2]
        return np.array([c[0], c[1] - math.sin(lean) * (c[2] - zp), zp + (c[2] - zp) * math.cos(lean)])

    def _arm(self, s, key):
        sp = self.sp
        Sh = self._tilt((s * sp['shoulder'][0], sp['shoulder'][1], sp['shoulder'][2]))
        a = self.p['arm_' + key]
        if isinstance(a, str) and a == 'salute':
            hr = sp['head_r']
            W = self.hc + np.array([s * hr[0] * 0.92, -hr[1] * 0.55, hr[2] * 0.12])
            pole = np.array([s * 1.0, 0.2, -0.5])
        else:
            off, pole = ARMS[a] if isinstance(a, str) else (a, (1, 0.3, -0.3))
            k = (sp['arm'][0] + sp['arm'][1]) / 0.172 if isinstance(a, str) else 1.0
            W = Sh + np.array([s * off[0], off[1], off[2]]) * k
            pole = np.array([s * pole[0], pole[1], pole[2]])
        E, W = ik2(Sh, W, sp['arm'][0], sp['arm'][1], pole, stretch=1.15)
        return Sh, E, W

    def _legs(self):
        sp, p = self.sp, self.p
        hx, hy, hz = sp['hip']
        L0, L1 = sp['leg']
        az = sp['ankle_z']
        ax = hx + 0.006
        kind = p['legs']
        pres = {
            'stand': [(ax, 0.0, az), (ax, 0.0, az)],
            'step': [(ax, -0.32 * (L0 + L1), az), (ax, 0.22 * (L0 + L1), az + 0.01)],
            'tiptoe': [(ax, 0.03, az + 0.03), (ax, -0.02, az + 0.01)],
            'sit': [(ax + 0.004, -L0 * 0.98, hz - L1 * 0.95), (ax + 0.004, -L0 * 0.98, hz - L1 * 0.95)],
            'floor': [(ax + 0.01, -(L0 + L1) * 0.93, hz - 0.01), (ax + 0.01, -(L0 + L1) * 0.93, hz - 0.01)],
        }
        pts = pres[kind] if isinstance(kind, str) else kind
        out = {}
        for s, key, (fx, fy, fz) in ((-1, 'r', pts[0]), (1, 'l', pts[1])):
            Hh = np.array([s * hx, hy, hz])
            A = np.array([s * fx, fy, fz])
            pole = np.array([0, -0.15, 1.0]) if kind in ('sit', 'floor') else np.array([0, -1.0, 0.25])
            Kn, A = ik2(Hh, A, L0, L1, pole, stretch=1.1)
            out[key] = (Hh, Kn, A)
        return out

    # ------------------------------------------------------------------ opbouw
    def build(self):
        sp, p, e = self.sp, self.p, self.e
        root = K.empty(self.name)
        self.root = root
        m = self.m = self._mats()
        self.hc = self._tilt(sp['head_c'])
        arms = {k: self._arm(s, k) for s, k in ((-1, 'r'), (1, 'l'))}
        legs = self._legs()
        self.hands = {k: (v[2], _n(v[2] - v[1])) for k, v in arms.items()}
        off = sp['cloth']
        # romp-kern (alleen als vorm voor de kleding)
        T = S.Field()
        for c, r in sp['torso']:
            T.add(*S.Ell(tuple(self._tilt(c)), r), k=0.06)
        self.T = T
        # ---- hemd: romp met uitlopende zoom + mouwen tot de pols
        hem = sp['hem']
        flare = lambda P: F32(0.014) * np.clip((hem + 0.07 - P[:, 2]) / 0.07, 0, 1).astype(F32)
        torso_sh = lambda P: S.smax(T(P) - off - flare(P), hem - P[:, 2], 0.004)
        SF = S.Field()
        SF.add(torso_sh, bound=((0, 0, (hem + sp['shoulder'][2]) / 2), 0.5))
        ar = sp['arm_r']
        for key, (Sh, E, W) in arms.items():
            d = _n(W - E)
            SF.add(*S.Cap(tuple(Sh), tuple(E), ar + off), k=0.035)
            SF.add(*S.Cyl(tuple(E), tuple(W - d * 0.004), ar * 0.96 + off), k=0.015)
        lump = Lump(3, 0.0012, 26)
        fsh = lambda P: SF(P) + lump(P)
        self.fshirt = fsh
        piece(self.name + '_hemd', fsh, *fbounds(SF, 0.03), m['shirt'], root, h=0.003 * sp.get('res_k', 1.0))
        for key, (Sh, E, W) in arms.items():
            d = _n(W - E)
            ring_stitch(self.name + f'_mouwsteek{key}', W - d * 0.012, d, ar * 0.96 + off + 0.0008, m['thread'], root)
        # ---- broek: bekken + rechte pijpen
        PF = S.Field()
        pc, pr = sp['torso'][-1]
        PF.add(*S.Ell(tuple(self._tilt(pc)), tuple(np.array(pr) + off * 0.6)))
        lr = sp['leg_r']
        for key, (Hh, Kn, A) in legs.items():
            d = _n(A - Kn)
            PF.add(*S.Cap(tuple(Hh + np.array([0, 0, 0.02])), tuple(Kn), lr + 0.002), k=0.03)
            PF.add(*S.Cyl(tuple(Kn), tuple(A), lr), k=0.012)
        fp = lambda P: S.smax(PF(P) + lump(P), P[:, 2] - (sp['belt'] + 0.03), 0.004)
        piece(self.name + '_broek', fp, *fbounds(PF, 0.03), m['pants'], root, h=0.003 * sp.get('res_k', 1.0))
        # ---- sokjes en laarsjes
        fk = sp.get('foot_k', 1.0)
        for s, key in ((-1, 'r'), (1, 'l')):
            Hh, Kn, A = legs[key]
            d = _n(A - Kn)
            ring_stitch(self.name + f'_zoomsteek{key}', A - d * 0.01, d, lr + 0.0008, m['thread'], root)
            Fk = S.Field()
            Fk.add(*S.Cyl(tuple(A - d * 0.006), tuple(A + d * 0.02 * fk), lr * 0.86))
            piece(self.name + f'_sok{key}', Fk, *fbounds(Fk, 0.01), m['sock'], root, h=0.0024)
            fwd = _n(np.array([s * 0.1, -1.0, 0.0]))
            if p['legs'] in ('sit', 'floor'):
                fwd = _n(np.array([s * 0.1, -0.35, 1.0])) if p['legs'] == 'floor' else _n(np.array([s * 0.1, -1.0, 0.1]))
            fo = sp['foot']
            Fb = S.Field()
            top = A + d * 0.018 * fk
            Fb.add(*S.Cyl(tuple(top), tuple(top + d * 0.03 * fk), lr * 0.92))
            fc = top + d * (0.028 + fo[2] * 0.75) * fk + fwd * 0.022 * fk
            Fb.add(*S.Ell(tuple(fc), tuple(np.array(fo) * fk), _rot_cols(d * -1, up=tuple(fwd))[:, [0, 2, 1]]
                          if False else _boot_R(d, fwd)), k=0.02)
            bot = fc - d * fo[2] * fk * 0.82
            nb = -d
            fbt = lambda P, Fb=Fb, bot=bot, nb=nb: S.smax(Fb(P), ((P - bot.astype(F32)) @ nb.astype(F32)), 0.004)
            lo, hi = fbounds(Fb, 0.02)
            piece(self.name + f'_laars{key}', fbt, lo, hi, m['shoe'], root, h=0.0026)
            fz = lambda P, fbt=fbt, bot=bot, nb=nb: S.smax(fbt(P) - 0.0035,
                                                           -((P - bot.astype(F32)) @ nb.astype(F32)) - 0.009, 0.002)
            piece(self.name + f'_zool{key}', fz, lo, hi, m['sole'], root, h=0.0022)
            # veters: zigzag over de wreef
            zz = [(0.011 * (1 if i % 2 else -1), 0.008 * i) for i in range(5)]
            try:
                thread_line(self.name + f'_veter{key}', fbt, tuple(top + d * 0.03 * fk - fwd * 0.2), zz,
                            garen('Garen veter', '#d9d4c8'), root, r=0.0011, up=tuple(-d), ray=tuple(fwd))
            except Exception:
                pass
        # ---- nek en handjes
        Fn = S.Field()
        Fn.add(*S.Cap(tuple(self.hc + np.array([0, 0.004, -sp['head_r'][2] * 0.75])),
                      tuple(self._tilt((0, 0, sp['shoulder'][2] - 0.02))), sp['neck']))
        piece(self.name + '_nek', Fn, *fbounds(Fn, 0.01), m['skin'], root, h=0.0026, attrs_fn=ONES)
        hd = sp['hand']
        for key, (Sh, E, W) in arms.items():
            d = _n(W - E)
            Fh = S.Field()
            Fh.add(*S.Ell(tuple(W + d * hd[2] * 0.72), hd, _boot_R(d, np.array([0, -1.0, 0.0]))))
            Fh.add(*S.Cyl(tuple(W - d * 0.012), tuple(W + d * 0.012), ar * 0.8), k=0.01)
            piece(self.name + f'_hand{key}', lambda P, Fh=Fh: Fh(P) + lump(P) * 0.5, *fbounds(Fh, 0.01), m['skin'],
                  root, h=0.0022, attrs_fn=ONES)
        # ---- details per outfit
        self._details()
        # ---- hoofd
        self._head()
        rl = list(p['root'])
        if p['legs'] == 'floor':
            rl[2] -= sp['hip'][2] - lr * 0.95
        root.location = rl
        root.rotation_euler = (0, 0, math.radians(p['yaw']))
        return root

    # ------------------------------------------------------------------ kleding-details
    def _collar(self, mat, thread, points=True):
        sp, root, fsh = self.sp, self.root, self.fshirt
        hc = self.hc
        zc = sp['shoulder'][2] + 0.012
        Fk = S.Field()
        Fk.add(*S.Tor((hc[0], hc[1] + 0.004, zc), sp['neck'] + 0.016, 0.011))
        piece(self.name + '_kraagband', Fk, *fbounds(Fk, 0.01), mat, root, h=0.0022)
        if points:
            for s in (-1, 1):
                tri = np.array([(s * 0.004, 0.0), (s * 0.045, 0.006), (s * 0.014, -0.034)])
                tri = _densify(np.concatenate([tri, tri[:1]]), 6)[:-1]
                applique(self.name + f'_kraagpunt{s}', fsh, (0, -0.3, zc - 0.014), tri, 0.005, mat, root,
                         stitch=thread, inset=0.0045)

    def _details(self):
        o = self.outfit
        sp, root, m, fsh = self.sp, self.root, self.m, self.fshirt
        T = self.T
        zb = sp['belt']
        top = sp['shoulder'][2]
        if o in ('uniform', 'pyjama'):
            self._collar(m['shirt2'], m['thread'])
            # knoopsluiting: een strook met knoopjes
            hgt = (top - 0.03) - (zb + 0.02)
            applique(self.name + '_beleg', fsh, (0, -0.3, (top - 0.03 + zb + 0.02) / 2), rrect(0.028, hgt, 0.006),
                     0.004, m['shirt2'] if o == 'uniform' else m['shirt'], root, stitch=m['thread'], inset=0.004)
            beads = kraal('Knoopje2', '#b8bcc6' if o == 'uniform' else '#ffffff')
            for z in np.linspace(top - 0.05, zb + 0.04, 3):
                q, nq = surf(fsh, (0, -0.3, z))
                K.blob(self.name + f'_knoop{z:.3f}', (0.0055, 0.0055, 0.0028), 2.2, (14, 8), mat=beads, parent=root,
                       loc=tuple(q + nq * 0.0055), rot=tuple(_rot_to(nq)))
        if o == 'uniform':
            for s in (-1, 1):
                zp = top - 0.085
                applique(self.name + f'_zak{s}', fsh, (s * 0.046, -0.3, zp), rrect(0.04, 0.038, 0.008), 0.004,
                         m['shirt2'], root, stitch=m['thread'], inset=0.0042)
                applique(self.name + f'_klep{s}', fsh, (s * 0.046, -0.3, zp + 0.024), rrect(0.046, 0.014, 0.005), 0.004,
                         m['shirt2'], root, lift=0.004, stitch=m['thread'], inset=0.003)
            applique(self.name + '_ster', fsh, (0.05, -0.3, top - 0.03), star(0.017, 0.0072), 0.0045,
                     wol('Vilt ster2', sp['star'], sheet=True), root, lift=0.0006,
                     stitch=garen('Garen goud', '#9a6d12'), inset=0.003)
            for s in (-1, 1):
                applique(self.name + f'_epaulet{s}', fsh, (s * 0.07, 0.0, top + 0.1), rrect(0.04, 0.016, 0.006), 0.004,
                         m['shirt2'], root, up=(0, -1, 0), stitch=m['thread'], inset=0.003, ray=(0, 0, -1))
        if o in ('uniform', 'boef', 'bakker'):
            # riem
            fr = lambda P: S.smax(T(P) - sp['cloth'] - 0.008, np.abs(P[:, 2] - zb) - 0.013, 0.003)
            belt_m = m['black'] if o != 'bakker' else wol('Vilt riembruin2', '#6b4a2f')
            piece(self.name + '_riem', fr, (-0.4, -0.4, zb - 0.03), (0.4, 0.4, zb + 0.03), belt_m, root, h=0.0024)
            applique(self.name + '_gesp', fr, (0, -0.4, zb), rrect(0.03, 0.024, 0.004), 0.003,
                     wol('Vilt gesp', '#c2c6ce', sheet=True), root)
            applique(self.name + '_gespgat', fr, (0, -0.4, zb), rrect(0.018, 0.011, 0.003), 0.0012, belt_m, root,
                     lift=0.003, bevel=False)
        if o == 'uniform':
            Fr = S.Field()
            Fr.add(*S.Box((-0.095, -0.03, zb - 0.03), (0.011, 0.018, 0.028), 0.007, S.rot(0, 0, 0.5)))
            Fr.add(*S.Cap((-0.097, -0.026, zb - 0.0), (-0.097, -0.026, zb + 0.045), 0.0042), k=0.004)
            piece(self.name + '_portofoon', Fr, *fbounds(Fr, 0.02), m['black'], root, h=0.002)
            K.blob(self.name + '_led', (0.0028, 0.0028, 0.0028), 2, (8, 6), mat=M.emission('Lampje2', '#ff4040', 6),
                   parent=root, loc=(-0.097, -0.042, zb + 0.015))
        if o == 'pyjama':
            rng = np.random.default_rng(4)
            ym = wol('Vilt ster2', '#f2c54a', sheet=True)
            for i in range(10):
                z = rng.uniform(zb - 0.02, top - 0.04)
                a = rng.uniform(-1.0, 1.0)
                applique(self.name + f'_pjster{i}', fsh, (math.sin(a) * 0.3, -math.cos(a) * 0.3, z), star(0.009, 0.004),
                         0.002, ym, root, bevel=False, ray=(-math.sin(a), math.cos(a), 0))
        if o == 'bakker':
            self._collar(wol('Vilt rood2', '#c63b33'), m['thread'], points=False)
            zt, zbm = top - 0.03, sp['hip'][2] - 0.03
            zm_, hh = (zt + zbm) / 2, (zt - zbm) / 2
            fa = lambda P: S.smax(S.smax(S.smax(T(P) - sp['cloth'] - 0.012, P[:, 1] + 0.03, 0.01),
                                         np.abs(P[:, 2] - zm_) - hh, 0.004), np.abs(P[:, 0]) - 0.12, 0.004)
            piece(self.name + '_schort', fa, (-0.4, -0.4, zbm - 0.03), (0.4, 0.1, zt + 0.03), m['shirt2'], root,
                  h=0.0028)
            applique(self.name + '_schortzak', fa, (0.0, -0.4, zbm + hh * 0.7), rrect(0.09, 0.06, 0.012), 0.004,
                     m['shirt2'], root, stitch=m['thread'], inset=0.005)
        if o == 'boef':
            self._collar(wol('Vilt sjaal ' + self.sp.get('scarf', '#3f7a4a'), self.sp.get('scarf', '#3f7a4a')),
                         m['thread'], points=False)

    # ------------------------------------------------------------------ hoofd
    def _head(self):
        sp, p, e, m = self.sp, self.p, self.e, self.m
        pitch, yaw, roll = [math.radians(v) for v in p['head']]
        piv = K.empty(self.name + '_hoofd', tuple(self.hc), (0, 0, 0), 1.0, self.root)
        piv.rotation_mode = 'YXZ'
        piv.rotation_euler = (math.radians(p['lean']) - pitch, roll, yaw)
        self.head_root = piv
        hr = sp['head_r']
        F = S.Field()
        F.add(*S.Ell((0, 0, 0), hr))
        cs = sp.get('cheek', 0.055)
        for s in (-1, 1):
            F.add(*S.Sph((s * hr[0] * 0.46, -hr[1] * 0.55, -hr[2] * 0.32), cs), k=0.04)
            F.add(*S.Ell((s * hr[0] * 0.98, 0.004, -0.004), (0.011, 0.022, 0.03), S.rot(0, 0, -s * 0.3)), k=0.008)
        base = F
        qn, nn = surf(base, (0, -0.4, -hr[2] * 0.18))
        nk, nr = sp.get('nose', ('bol', 0.012))
        if nk == 'lang':
            F.add(*S.Ell(tuple(qn + nn * 0.012), (nr * 0.8, nr * 1.5, nr * 0.85)), k=0.006)
        else:
            F.add(*S.Sph(tuple(qn + nn * nr * 0.45), nr), k=0.006)
        lump = Lump(11, 0.0009, 26)
        fh = lambda P: F(P) + lump(P)
        self.fhead = fh

        def paint(V):
            col = np.ones((len(V), 3), F32)
            g = lambda c, s_: np.exp(-((V - np.asarray(c, F32)) ** 2).sum(1) / (2 * s_ * s_))
            b = 0.85 * e['blush']
            for s in (-1, 1):
                w = (b * g((s * hr[0] * 0.5, -hr[1] * 0.85, -hr[2] * 0.25), 0.024))[:, None]
                col = col * (1 - w) + col * np.array([1.0, 0.58, 0.56], F32) * w
            w = (0.45 * g(qn + nn * 0.01, 0.014))[:, None]
            col = col * (1 - w) + col * np.array([1.0, 0.72, 0.68], F32) * w
            return {'paint': ('POINT', col)}
        piece(self.name + '_kop', fh, (-0.25, -0.25, -0.25), (0.25, 0.25, 0.25), m['skin'], piv, h=0.0023,
              attrs_fn=paint)
        self._face(fh, piv)
        self._hair(fh, piv)
        self._headwear(piv)

    def _face(self, fh, piv):
        sp, e = self.sp, self.e
        hr = sp['head_r']
        ex, ez = sp.get('eye', (0.045, -0.004))
        dark = garen('Garen bruin2', '#3a2a22')
        lx, lz = e['look']
        bead = kraal('Oogkraal2', sp.get('iris', '#1c2c4c'))
        er = sp.get('eye_r', 0.0118)
        for s in (-1, 1):
            anc = (s * ex, -0.4, ez)
            if e['eyes'] == 'closed':
                arc = [(x, -0.004 * (1 - (x / 0.012) ** 2)) for x in np.linspace(-0.012, 0.012, 9)]
                thread_line(self.name + f'_slaapoog{s}', fh, anc, arc, dark, piv, r=0.0013)
                continue
            if e['eyes'] == 'happy':
                arc = [(x, 0.005 * (1 - (x / 0.012) ** 2)) for x in np.linspace(-0.012, 0.012, 9)]
                thread_line(self.name + f'_lachoog{s}', fh, anc, arc, dark, piv, r=0.0014)
                continue
            q, nq = surf(fh, (s * ex + lx * 0.003, -0.4, ez + lz * 0.003))
            K.blob(self.name + f'_oog{s}', (er, er, er * 0.72), 2.0, (20, 12), mat=bead, parent=piv,
                   loc=tuple(q + nq * er * 0.3), rot=tuple(_rot_to(nq)))
        b = e['brows']
        if b != 'none':
            tilt = {'up': 0.0, 'worried': 0.4, 'cross': -0.4}.get(b, 0.0)
            bz = ez + 0.03 + (0.006 if b in ('up', 'worried') else 0.0)
            for s in (-1, 1):
                pts = [(x, 0.003 * (1 - (x / 0.011) ** 2) - s * tilt * x * 0.5) for x in np.linspace(-0.011, 0.011, 7)]
                thread_line(self.name + f'_wenkbrauw{s}', fh, (s * ex, -0.4, bz), pts,
                            garen('Garen brauw ' + sp.get('brow', '#b08a55'), sp.get('brow', '#b08a55')), piv, r=0.0013)
        mouth = e['mouth']
        mz = sp.get('mouth_z', -hr[2] * 0.42)
        mw = sp.get('mouth_w', 0.012)
        red = garen('Garen roze2', '#a5464d')
        dm = wol('Vilt mond2', '#6e1f2a', sheet=True, fuzz=0.3)
        anc = (0, -0.4, mz)
        if mouth in ('smile', 'sad', 'flat'):
            k = {'smile': 1.0, 'sad': -0.9, 'flat': 0.0}[mouth]
            pts = [(x, 0.006 * k * (x / mw) ** 2) for x in np.linspace(-mw, mw, 9)]
            thread_line(self.name + '_mond', fh, anc, pts, red, piv, r=0.0013)
        elif mouth in ('grin', 'open'):
            w = mw * 1.3
            hgt = mw * (1.1 if mouth == 'grin' else 1.4)
            t = np.linspace(0, math.pi, 14)
            top = [(x, 0.002 * (x / w) ** 2) for x in np.linspace(w, -w, 10)]
            bot = [(-w * math.cos(a), -hgt * math.sin(a)) for a in t[1:-1]]
            applique(self.name + '_mondopen', fh, anc, np.array(top + bot), 0.0015, dm, piv, bevel=False)
        elif mouth == 'o':
            applique(self.name + '_mondo', fh, (0, -0.4, mz - 0.002), ellipse(mw * 0.45, mw * 0.6), 0.0015, dm, piv,
                     bevel=False)

    # ------------------------------------------------------------------ haar van garen
    def _hair(self, fh, piv):
        sp = self.sp
        style = sp.get('hair_style', 'auto')
        if style == 'auto':
            style = 'pet' if self.cap else 'kuif'
        if style == 'none':
            return
        hr = sp['head_r']
        col = sp.get('hair', '#efd28a')
        # vilten onderlaag
        xs = [0, 35, 70, 100, 140, 180]
        zs = np.array(sp.get('hairline', [0.62, 0.55, 0.3, 0.12, -0.2, -0.35])) * hr[2]
        base = lambda P: S.ellipsoid(P, (0, 0, 0), hr)

        def region(P):
            az = np.degrees(np.abs(np.arctan2(P[:, 0], -P[:, 1])))
            return np.interp(az, xs, zs).astype(F32) - P[:, 2]
        fhb = lambda P: S.smax(base(P) - 0.006, region(P), 0.004)
        piece(self.name + '_haarbasis', fhb, (-0.2, -0.2, -0.2), (0.2, 0.2, 0.22),
              wol('Vilt haar ' + col, col, fuzz=2.2), piv, h=0.0026)
        rng = np.random.default_rng(len(self.name) + 3)
        # lokjes: wortels op de onderlaag, richting afhankelijk van de stijl
        Dd = _n(rng.normal(size=(4000, 3)))
        P0 = Dd * 0.4
        az = np.degrees(np.abs(np.arctan2(Dd[:, 0], -Dd[:, 1])))
        zline = np.interp(az, xs, zs) / hr[2]
        if style == 'pet':
            band = sp.get('cap_line', 0.5)
            keep = (Dd[:, 2] > zline) & (Dd[:, 2] < band + 0.12) & (Dd[:, 2] > band - 0.28)
            n_locks = 46
        elif style == 'kuif':
            keep = Dd[:, 2] > zline + 0.02
            n_locks = 70
        else:
            keep = Dd[:, 2] > zline
            n_locks = 50
        Dd = Dd[keep]
        sel = [0]
        dmin = ((Dd - Dd[0]) ** 2).sum(1)
        for _ in range(min(n_locks, len(Dd)) - 1):
            j = int(np.argmax(dmin))
            sel.append(j)
            dmin = np.minimum(dmin, ((Dd - Dd[j]) ** 2).sum(1))
        G = Dd[sel]
        roots = np.array([hit(fhb, g * 0.4, -g) for g in G])
        strands, cols = [], []
        c0 = np.array(K.srgb(col)[:3])
        for g, r0 in zip(G, roots):
            out = _n(g)
            front = -g[1]
            if style == 'pet':
                L = rng.uniform(0.035, 0.06)
                dirv = _n(out * 0.55 + np.array([0, -0.25 * max(front, 0), -1.0]))
            elif style == 'kuif':
                top = g[2]
                L = rng.uniform(0.045, 0.075) * (1.25 if front > 0.3 else 1.0)
                if front > 0.2 and top > 0.4:
                    dirv = _n(out * 0.7 + np.array([g[0] * 0.3, -0.6, 0.8]))
                else:
                    dirv = _n(out * 0.45 + np.array([g[0] * 0.4, -0.3 * front, -0.6 if top < 0.55 else 0.2]))
            else:
                L = rng.uniform(0.03, 0.05)
                dirv = _n(out * 0.5 + np.array([0, 0, -1.0]))
            k = 7
            path = [r0 - out * 0.003]
            d = dirv.copy()
            curl = _n(np.cross(out, d) + rng.normal(0, 0.3, 3))
            for i in range(1, k):
                d = _n(d + np.array([0, 0, -0.08]) + curl * 0.22 * (i / k))
                path.append(path[-1] + d * L / (k - 1))
            path = np.array(path)
            # garen: een bundel gedraaide draadjes
            T_ = _n(np.gradient(path, axis=0))
            U = _n(np.cross(T_, out))
            V_ = np.cross(T_, U)
            nstr = 16
            tw = rng.uniform(4, 7)
            for j in range(nstr):
                a0 = j * 2 * math.pi / nstr
                rr = 0.0042 * math.sqrt(rng.random())
                t = np.linspace(0, 1, k)
                ang = a0 + tw * t
                taper = 1 - 0.65 * t ** 1.5
                st = path + (U * np.cos(ang)[:, None] + V_ * np.sin(ang)[:, None]) * (rr * taper)[:, None]
                strands.append(st)
                cols.append(c0 * rng.uniform(0.85, 1.12))
        mat = _cached('Garen haar ' + col)
        if mat is None:
            mat = M.hair_color_mat('Garen haar ' + col, rough=0.62, radial=0.9, attr='col')
            _MC['Garen haar ' + col] = mat
        K.hair(self.name + '_garenhaar', np.array(strands), (0.00095, 0.0005), mat, piv, col=np.array(cols))

    # ------------------------------------------------------------------ hoofddeksel
    def _headwear(self, piv):
        sp, p = self.sp, self.p
        hw = sp.get('hat', 'pet' if self.cap else None)
        if self.outfit == 'boef' and not self.cap:
            hw = None
        if hw == 'pet':
            felt_cap(self.name + '_pet', piv, sp['head_r'], loc=(0, 0.004, p.get('cap_lift', 0.0)),
                     rot=tuple(p.get('cap_rot', (-0.12, 0, 0))))
        elif hw == 'muts':
            beanie2(self.name + '_muts', piv, sp['head_r'], sp.get('beanie', '#1d1d22'), sp.get('beanie2', '#9a2c2c'))
        elif hw == 'koksmuts':
            chef_hat2(self.name + '_koksmuts', piv, sp['head_r'])
        if sp.get('mask') and self.outfit == 'boef':
            hr = sp['head_r']
            ez = sp.get('eye', (0.045, -0.004))[1]
            zm = ez + (0.045 if sp.get('mask_up') else 0.0)
            fm = lambda P, zm=zm: S.smax(S.smax(self.fhead(P) - 0.0045, np.abs(P[:, 2] - zm) - 0.017, 0.004),
                                          P[:, 1] - 0.02, 0.008)
            piece(self.name + '_masker', fm, (-0.25, -0.25, zm - 0.04), (0.25, 0.1, zm + 0.04),
                  wol('Vilt zwart2', '#202024', fuzz=1.6), piv, h=0.002)
            if not sp.get('mask_up'):
                # kraaloogjes opnieuw, nu boven op het masker
                bead = kraal('Oogkraal wit', '#f4f1ea')
                for s in (-1, 1):
                    q, nq = surf(lambda P: np.minimum(self.fhead(P), fm(P)), (s * sp.get('eye', (0.045, 0))[0], -0.4, ez))
                    K.blob(self.name + f'_maskeroog{s}', (0.0075, 0.0075, 0.003), 2.0, (16, 8), mat=bead, parent=piv,
                           loc=tuple(q + nq * 0.002), rot=tuple(_rot_to(nq)))


def _boot_R(d, fwd):
    """Rotatie voor een ellipsoïde met lokale y langs fwd (voorvoet) en lokale z langs -d (omhoog)."""
    z = _n(-np.asarray(d, float))
    y = np.asarray(fwd, float) - z * np.dot(fwd, z)
    if np.linalg.norm(y) < 1e-4:
        y = np.array([0, -1.0, 0])
    y = _n(y)
    x = np.cross(y, z)
    return np.stack([x, y, z], 1).astype(F32)


def felt_cap(name, parent, hr, loc=(0, 0, 0), rot=(0, 0, 0), stitch=True):
    """Politiepet van lapjes vilt: band, bol kussentje, platte klep met rand, schildje."""
    root = K.empty(name, loc, rot, 1.0, parent)
    navy = wol('Vilt petblauw', '#18214a', fuzz=1.8)
    black = wol('Vilt zwart2', '#202024', fuzz=1.6)
    zb = hr[2] * 0.6
    hb = hr[2] * 0.15
    ax = hr[0] * math.sqrt(max(1 - (zb / hr[2]) ** 2, 0.05)) + 0.016
    ay = hr[1] * math.sqrt(max(1 - (zb / hr[2]) ** 2, 0.05)) + 0.016

    def band(P, ax=ax, ay=ay, zc=zb, hh=hb, r=0.004):
        q = np.sqrt((P[:, 0] / ax) ** 2 + ((P[:, 1] - 0.004) / ay) ** 2)
        d2 = (q - 1) * min(ax, ay)
        dz = np.abs(P[:, 2] - zc) - hh
        return np.minimum(np.maximum(d2, dz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz, 0) ** 2) - r
    F = S.Field()
    F.add(band, bound=((0, 0, zb), 0.25))
    F.add(*S.Ell((0, -0.01, zb + hb + 0.016), (ax * 1.22, ay * 1.28, hr[2] * 0.24), S.rot(0.1, 0, 0)), k=0.012)
    lump = Lump(31, 0.001, 30)
    fcap = lambda P: F(P) + lump(P)
    piece(name + '_bol', fcap, (-0.25, -0.25, zb - hb - 0.02), (0.25, 0.25, zb + 0.15), navy, root, h=0.0022)
    fb = lambda P: band(P, ax + 0.003, ay + 0.003, zb - hb + 0.006, 0.006, 0.002)
    piece(name + '_band', fb, (-0.2, -0.2, zb - hb - 0.02), (0.2, 0.2, zb), black, root, h=0.0018)
    Rv = S.rot(-0.38, 0, 0)

    def visor(P):
        e = S.ellipsoid(P, (0, -ay - 0.002, zb - hb + 0.004), (ax * 0.86, ay * 0.62, 0.0038), Rv)
        return S.smax(e, P[:, 1] + ay * 0.92, 0.003)
    piece(name + '_klep', visor, (-0.2, -0.3, zb - 0.08), (0.2, 0.0, zb + 0.05), black, root, h=0.0016)
    gold = wol('Vilt goud2', '#f0b52a', sheet=True)
    applique(name + '_schild', fcap, (0, -0.4, zb + hb + 0.022), shield(0.024, 0.027), 0.0035, gold, root,
             stitch=garen('Garen goud', '#9a6d12') if stitch else None, inset=0.003)
    if stitch:
        th = np.linspace(0, 2 * math.pi, 140)
        P = np.stack([np.cos(th) * (ax + 0.0045), np.sin(th) * (ay + 0.0045) + 0.004, np.full(len(th), zb + hb - 0.004)],
                     1)
        N = _n(np.stack([np.cos(th) / ax, np.sin(th) / ay, np.zeros(len(th))], 1))
        stitches(name + '_bandsteek', P, N, garen('Garen licht', '#d8deef'), root)
    return root


def beanie2(name, parent, hr, color, stripe):
    """Gebreide/gevilte muts met omgeslagen rand en bolletje (zoals een echte viltmuts)."""
    m = wol('Vilt muts ' + color, color, fuzz=2.0)
    m2 = wol('Vilt muts ' + stripe, stripe, fuzz=2.0)
    zb = hr[2] * 0.12
    base = lambda P: S.ellipsoid(P, (0, 0.006, 0.012), (hr[0] + 0.012, hr[1] + 0.012, hr[2] + 0.02))
    dome = lambda P: S.smax(base(P), zb - P[:, 2], 0.004)
    piece(name, dome, (-0.25, -0.25, zb - 0.02), (0.25, 0.25, hr[2] + 0.06), m, parent, h=0.0026)
    Fr = S.Field()
    Fr.add(*S.Tor((0, 0.006, zb + 0.012), (hr[0] + hr[1]) / 2 * 0.98 + 0.01, 0.017))
    piece(name + '_rand', lambda P: Fr(P) + F32(0.0012) * np.sin(np.arctan2(P[:, 0], -P[:, 1]) * 40), *fbounds(Fr, 0.01),
          m2, parent, h=0.0024)
    Fp = S.Field()
    Fp.add(*S.Sph((0, 0.012, hr[2] + 0.035), 0.026))
    piece(name + '_bol', lambda P: Fp(P) + Lump(7, 0.003, 60)(P), *fbounds(Fp, 0.01), m2, parent, h=0.0018)


def chef_hat2(name, parent, hr):
    white = wol('Vilt koksmuts2', '#fbfaf6', fuzz=1.8)
    F = S.Field()
    zb = hr[2] * 0.45
    F.add(*S.Cyl((0, 0, zb), (0, 0, zb + 0.06), hr[0] * 0.98))
    for i in range(6):
        a = i * math.pi / 3
        F.add(*S.Sph((math.cos(a) * 0.065, math.sin(a) * 0.06, zb + 0.13), 0.06), k=0.03)
    F.add(*S.Sph((0, 0, zb + 0.15), 0.07), k=0.03)
    lump = Lump(51, 0.0018, 24)
    piece(name, lambda P: F(P) + lump(P), (-0.2, -0.2, zb - 0.03), (0.2, 0.2, zb + 0.28), white, parent, h=0.003)


# ------------------------------------------------------------------ figuren
def Daan(name='Daan', pose=None, expr=None, cap=True, outfit='uniform', **kw):
    sp = dict(DAAN)
    if outfit == 'pyjama':
        sp['shoe'] = '#8fc0e2'
    return Pop(name, sp, pose, expr, outfit, cap)


ADULT = dict(
    bakker=dict(skin='#efc0a0', head_c=(0, -0.004, 1.06), head_r=(0.112, 0.106, 0.12),
                torso=[((0, 0.0, 0.73), (0.12, 0.1, 0.19)), ((0, 0.0, 0.6), (0.135, 0.115, 0.12))],
                shoulder=(0.105, 0.0, 0.92), arm=(0.17, 0.165), arm_r=0.034, hand=(0.033, 0.028, 0.045),
                hip=(0.058, 0.0, 0.52), leg=(0.22, 0.21), leg_r=0.048, ankle_z=0.1, hem=0.5, belt=0.56, cloth=0.012,
                neck=0.032, foot=(0.042, 0.07, 0.036), hair='#6e4a2c', brow='#5a3a22', hair_style='rand',
                hat='koksmuts', nose=('bol', 0.02), eye=(0.04, 0.0), eye_r=0.0105, shoe='#3a2a20', sock='#f4f1ea',
                iris='#2a2420', mouth_w=0.013, hairline=[0.3, 0.25, 0.12, 0.05, -0.15, -0.3], res_k=1.25),
    lang=dict(skin='#ecc2a2', head_c=(0, -0.004, 1.2), head_r=(0.098, 0.096, 0.115),
              torso=[((0, 0.0, 0.84), (0.085, 0.07, 0.2)), ((0, 0.0, 0.7), (0.09, 0.072, 0.1))],
              shoulder=(0.09, 0.0, 1.04), arm=(0.21, 0.2), arm_r=0.028, hand=(0.03, 0.026, 0.044),
              hip=(0.046, 0.0, 0.62), leg=(0.27, 0.26), leg_r=0.04, ankle_z=0.1, hem=0.6, belt=0.64, cloth=0.011,
              neck=0.028, foot=(0.04, 0.072, 0.034), hair='#3b2a20', brow='#2a1d16', hair_style='rand',
              hat='muts', beanie='#24242a', beanie2='#3f7a4a', scarf='#3f7a4a', nose=('lang', 0.016), eye=(0.036, 0.004),
              eye_r=0.0095, shoe='#5a3b24', sock='#f4f1ea', iris='#161616', mask=True, mouth_w=0.012,
              hairline=[0.2, 0.15, 0.05, -0.05, -0.2, -0.3], res_k=1.25),
    dik=dict(skin='#f0c19f', head_c=(0, -0.006, 0.86), head_r=(0.118, 0.112, 0.118),
             torso=[((0, 0.0, 0.56), (0.15, 0.135, 0.19)), ((0, 0.0, 0.44), (0.14, 0.125, 0.11))],
             shoulder=(0.115, 0.0, 0.72), arm=(0.14, 0.135), arm_r=0.035, hand=(0.034, 0.029, 0.044),
             hip=(0.065, 0.0, 0.36), leg=(0.14, 0.135), leg_r=0.052, ankle_z=0.1, hem=0.36, belt=0.42, cloth=0.012,
             neck=0.03, foot=(0.043, 0.072, 0.036), hair='#7a3f22', brow='#5a2e18', hair_style='rand', hat='muts',
             beanie='#9a2c2c', beanie2='#e8d9b0', scarf='#c63b33', nose=('bol', 0.02), eye=(0.04, 0.004), eye_r=0.01,
             shoe='#5a3b24', sock='#f4f1ea', iris='#161616', mask=True, mouth_w=0.013,
             hairline=[0.2, 0.15, 0.05, -0.05, -0.2, -0.3], res_k=1.25),
)


def Mens(name, kind='bakker', pose=None, expr=None, mask_up=False, baker_hat=False, **kw):
    sp = dict(DAAN)
    sp.update(ADULT[kind])
    sp['mask_up'] = mask_up
    if baker_hat:
        sp['hat'] = 'koksmuts'
    return Pop(name, sp, pose, expr, 'bakker' if kind == 'bakker' else 'boef', cap=False)
