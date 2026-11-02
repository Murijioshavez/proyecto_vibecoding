# Script de diagnóstico usado en el desarrollo. Ejecutar desde la raíz: python docs/diagnostico.py
import random, json, os, tempfile, sys
sys.path.insert(0, os.getcwd())
from src.game import Game, InputState, State
from src.entities import Meteor
tmp = tempfile.mkdtemp()
g = Game(rng=random.Random(1), highscore_path=os.path.join(tmp,"hs.json")); g.start()
# 1) Un meteoro detenido sobre la nave durante 0.5 s
g.meteors.append(Meteor(g.player.x, g.player.y, 20, 0, 0, random.Random(2)))
for _ in range(30): g.update(1/60, InputState())
print("1) vidas tras 0.5 s de contacto con UN meteoro:", g.lives, "estado:", g.state)
# 2) Crecimiento de la lista de meteoros
g = Game(rng=random.Random(1), highscore_path=os.path.join(tmp,"hs2.json")); g.start(); g.lives=10**9
for _ in range(60*120): g.update(1/60, InputState(left=True))
print("2) meteoros en memoria tras 120 s:", len(g.meteors), "visibles:", sum(1 for m in g.meteors if m.y < g.height+m.radius))
# 3) Archivo de récord corrupto
p=os.path.join(tmp,"bad.json"); open(p,"w").write("{corrupto")
try: Game(highscore_path=p); print("3) récord corrupto: OK")
except Exception as e: print("3) récord corrupto -> excepción:", type(e).__name__)
# 4) dt enorme (ventana arrastrada / pausa del SO)
g = Game(rng=random.Random(1), highscore_path=os.path.join(tmp,"hs3.json")); g.start()
g.update(3.0, InputState(right=True)); print("4) dt=3s: desplazamiento de la nave en un solo frame:", round(g.player.x-480), "px")
