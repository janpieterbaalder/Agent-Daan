import math
from lib import core as K, cast, mats as MM
from lib.people import Person, people_mats
from lib.daan import Daan


def main(out, opts):
    K.reset()
    w = int(opts.get('w') or 1800)
    K.render_setup(w, int(w * 0.55), samples=int(opts.get('samples') or 64))
    K.world_color('#9a8f86', 0.25)
    dm = cast.char_mats()
    pm = people_mats(dm)
    cam = (0, -5.2, 1.0)
    Person('Lange', 'lang', pose=dict(root=(-1.0, 0, 0), yaw=10), expr=dict(smile=1.0, look_at=cam), mats=pm).build()
    Person('Dikkie', 'dik', pose=dict(root=(0.0, 0, 0), yaw=-5), expr=dict(mouth='o', open=0.8, smile=0.0, lids=1.0, look_at=cam), mats=pm).build()
    Person('Bakker', 'bakker', pose=dict(root=(1.1, 0, 0), yaw=-15), expr=dict(smile=1.0, look_at=cam), mats=pm).build()
    Daan('Daan', pose=dict(root=(0.55, -0.6, 0), yaw=-10), cap=True, mats=dm, hair_density=0.5, expr=dict(look_at=cam)).build()
    K.camera(cam, (0, 0, 0.85), lens=45)
    K.light('AREA', (-2.5, -3.0, 3.0), (0, 0, 0.8), energy=900, size=3.0, color=(1, 0.93, 0.85))
    K.light('AREA', (3.0, -2.5, 1.5), (0, 0, 0.8), energy=250, size=3.0, color=(0.85, 0.92, 1))
    K.light('AREA', (1.0, 3.0, 3.0), (0, 0, 1.0), energy=700, size=2.0)
    K.blob('vloer', (8, 8, 0.01), 6, (8, 4), mat=MM.simple('vloer', '#b8aea2', 0.7), loc=(0, 0, -0.01))
    K.render(out)
