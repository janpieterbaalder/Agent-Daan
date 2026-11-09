"""Proefplaat decor: vilten straat met bakkerij, politieautootje, Daan en Joep."""
import math
from lib import core as K, stage, viltdecor as D
from lib.viltpop import Daan, Joep


def main(out, opts):
    Q = stage.setup(opts, 'spread')
    stage.sky('#78b8e6', '#cfe8f6', '#9a9c8f', 0.9)
    stage.sun(215, 42, 3.2, color=(1.0, 0.94, 0.84))
    D.street(x0=-7, x1=7, bakery_x=-1.2)
    D.police_car('Auto', loc=(1.9, -0.6, 0), yaw=math.radians(-28))
    Daan('Daan', pose=dict(root=(0.3, -1.1, 0), yaw=10, arm_r='salute', arm_l='down'),
         expr=dict(mouth='smile', look=(0.0, 0.1)), cap=True).build()
    Joep('Joep', pose=dict(root=(-0.25, -1.25, 0.0), yaw=-15, arm_r='salute', arm_l='down', legs='sit'),
         cap=True).build()
    K.camera((0.0, -6.2, 1.15), (0.0, 0.0, 1.0), lens=35, fstop=4.0, focus=(0.1, -1.1, 0.5))
    K.light('AREA', (-3.0, -4.0, 4.0), (0, 0, 0.5), energy=900, size=4.0, color=(1.0, 0.96, 0.9))
    K.render(out)
