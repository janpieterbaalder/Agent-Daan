"""Ontwerpproef viltanimatie: Daan (met pet, saluut) en Joep op een gevilt heuveltje, wolken van plukwol,
lollybomen, gras en bloemetjes; macrocamera op ware grootte."""
from lib import core as K, stage, wol as W, wolset as WS
from lib.wolpop import Daan, Joep


def main(out, opts):
    Q = stage.setup(opts, 'spread', look='Medium Contrast')
    W.studio(key=(-0.32, -0.42, 0.45), target=(0, 0, 0.05), energy=16.0, size=0.5, fill_energy=4.0, rim_energy=7.0,
             world='#e8e2da', world_strength=0.45)
    g, fg = WS.ground(hills=[(0.0, 0.0, 0.16, 0.12, 0.008), (-0.25, 0.14, 0.18, 0.09, 0.05), (0.28, 0.16, 0.2, 0.1, 0.06)])
    WS.sky(y=0.24, width=1.0, height=0.4)
    WS.cloud('Wolk1', (-0.18, 0.2, 0.17), 0.045, seed=1)
    WS.cloud('Wolk2', (0.12, 0.21, 0.21), 0.035, seed=2)
    WS.cloud('Wolk3', (0.32, 0.2, 0.15), 0.04, seed=3)
    WS.sun('Zon', (0.22, 0.215, 0.24), 0.028)
    WS.lolly_tree('Boom1', (-0.13, 0.07, WS.height_at(fg, -0.13, 0.07)), h=0.11, r=0.034, apples=5, seed=5)
    WS.lolly_tree('Boom2', (0.2, 0.12, WS.height_at(fg, 0.2, 0.12)), h=0.09, r=0.028, color='#6fae55', seed=8)
    WS.bush('Struik', (0.11, 0.05, WS.height_at(fg, 0.11, 0.05)), 0.02, berries=5, seed=6)
    WS.tufts('Gras', fg, (-0.3, 0.3, -0.14, 0.12), 900, seed=4)
    WS.flowers('Bloem', fg, (-0.22, 0.25, -0.08, 0.08), 22, seed=7)
    z0 = WS.height_at(fg, -0.012, -0.02)
    Daan('Daan', pose=dict(root=(-0.012, -0.02, z0), yaw=10, arm_r='salute', arm_l='down', head=(3, 6, -4)),
         expr=dict(mouth='smile', look=(0.2, 0.2)), cap=True).build()
    z1 = WS.height_at(fg, 0.034, -0.036)
    Joep('Joep', pose=dict(root=(0.034, -0.036, z1), yaw=-18, arm_r='salute', arm_l='down', legs='sit',
                           head=(6, -6, 6)), cap=True).build()
    W.camera((0.035, -0.5, 0.085), (0.015, 0.0, 0.07), lens=55, fstop=3.5, focus=(-0.01, -0.035, 0.085))
    K.render(out)
