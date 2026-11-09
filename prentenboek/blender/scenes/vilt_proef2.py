"""Proefplaat bijrollen: bakker, lange boef, dikke boef, met Daan en Joep erbij voor de maat."""
import numpy as np
from lib import core as K
from lib.viltpop import Daan, Joep, Mens, wol


def main(out, opts):
    K.reset()
    w = int(opts.get('w') or 1600)
    K.render_setup(w, int(w * 0.56), samples=int(opts.get('samples') or 128), look='Medium High Contrast')
    K.world_color('#b9aea4', 0.35)
    U, V = np.meshgrid(np.linspace(0, 1, 60), np.linspace(0, 1, 40))
    x = (U - 0.5) * 9
    y = V * 6 - 1.5
    z = np.where(y > 1.4, (y - 1.4) ** 2 * 0.9, 0)
    y2 = np.where(y > 1.4, 1.4 + (y - 1.4) * 0.35, y)
    P = np.stack([x, y2, z], -1).reshape(-1, 3)
    F = [(i * 60 + j, i * 60 + j + 1, i * 60 + j + 61, i * 60 + j + 60) for i in range(39) for j in range(59)]
    K.mesh_obj('Studio', P, F, wol('Vilt studio', '#d8cfc4'))
    Mens('Bakker', 'bakker', pose=dict(root=(-0.95, 0.2, 0), yaw=10, arm_r='hip', arm_l='wave'),
         expr=dict(mouth='grin', look=(0.3, 0))).build()
    Mens('Lange', 'lang', pose=dict(root=(0.25, 0.3, 0), yaw=-5, arm_r='down', arm_l='down'),
         expr=dict(mouth='o', brows='worried')).build()
    Mens('Dikkie', 'dik', pose=dict(root=(0.95, 0.15, 0), yaw=-18, arm_r='hold', arm_l='hold'),
         expr=dict(mouth='smile', look=(-0.3, 0))).build()
    Daan('Daan', pose=dict(root=(-0.35, -0.3, 0), yaw=8, arm_r='point', arm_l='down'),
         expr=dict(mouth='open', brows='cross'), cap=True).build()
    Joep('Joep', pose=dict(root=(-0.05, -0.45, 0), yaw=-10, arm_r='up', arm_l='up', legs='sit'), cap=True).build()
    K.camera((0.0, -3.6, 0.85), (0.0, 0.0, 0.62), lens=40, fstop=3.5, focus=(0.0, -0.1, 0.7))
    K.light('AREA', (-1.6, -2.0, 2.4), (0, 0, 0.7), energy=420, size=1.8, color=(1.0, 0.94, 0.86))
    K.light('AREA', (2.0, -1.5, 1.2), (0, 0, 0.7), energy=140, size=2.0, color=(0.9, 0.95, 1.0))
    K.light('AREA', (0.6, 2.0, 2.0), (0, 0, 0.8), energy=220, size=1.0)
    K.render(out)
