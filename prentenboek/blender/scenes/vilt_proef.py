"""Proefplaat viltpoppen: Daan met pet, Daan zonder pet (kuif) en Joep, in een eenvoudige studio."""
import math
import numpy as np
from lib import core as K
from lib.viltpop import Daan, Joep, wol


def main(out, opts):
    K.reset()
    w = int(opts.get('w') or 1600)
    K.render_setup(w, int(w * 0.62), samples=int(opts.get('samples') or 128), look='Medium High Contrast')
    K.world_color('#b9aea4', 0.35)
    # vilten vloer en achterdoek in één bocht
    U, V = np.meshgrid(np.linspace(0, 1, 60), np.linspace(0, 1, 40))
    x = (U - 0.5) * 7
    y = V * 5 - 1.2
    z = np.where(y > 1.4, (y - 1.4) ** 2 * 0.9, 0)
    y2 = np.where(y > 1.4, 1.4 + (y - 1.4) * 0.35, y)
    P = np.stack([x, y2, z], -1).reshape(-1, 3)
    F = []
    for i in range(39):
        for j in range(59):
            a = i * 60 + j
            F.append((a, a + 1, a + 61, a + 60))
    K.mesh_obj('Studio', P, F, wol('Vilt studio', '#d8cfc4'))
    a = Daan('DaanPet', pose=dict(root=(-0.3, 0.0, 0), yaw=12, arm_r='salute', arm_l='down', head=(4, 6, -4)),
             expr=dict(mouth='smile', look=(0.3, 0.1)), cap=True)
    a.build()
    b = Daan('DaanKuif', pose=dict(root=(0.36, 0.12, 0), yaw=-22, arm_l='wave', arm_r='hip', head=(2, -8, 5)),
             expr=dict(mouth='grin', look=(-0.4, 0.0), brows='up'), cap=False)
    b.build()
    j = Joep('Joep', pose=dict(root=(0.02, -0.28, 0.0), yaw=-10, arm_r='salute', arm_l='down', legs='sit',
                               head=(6, 8, 6)), cap=True)
    j.build()
    K.camera((0.05, -2.2, 0.5), (0.03, 0.0, 0.38), lens=50, fstop=2.8, focus=(0.0, -0.05, 0.5))
    K.light('AREA', (-1.4, -1.6, 1.8), (0, 0, 0.5), energy=260, size=1.4, color=(1.0, 0.94, 0.86))
    K.light('AREA', (1.6, -1.2, 0.9), (0, 0, 0.5), energy=90, size=1.8, color=(0.9, 0.95, 1.0))
    K.light('AREA', (0.6, 1.5, 1.6), (0, 0, 0.6), energy=160, size=0.8)
    K.render(out)
