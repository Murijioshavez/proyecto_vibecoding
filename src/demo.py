"""Modo de evidencias y prueba de humo.

Ejecuta el juego REAL (misma lógica y mismo renderizador que al jugar) con
un "piloto automático" sencillo y guarda capturas con pygame.image.save.
No se fabrica ninguna imagen: cada PNG es el contenido de la ventana en ese
fotograma.

Uso:
    python main.py --capturas evidencias      # genera capturas
    python main.py --prueba-humo 600          # 600 fotogramas y sale
"""
import math
import os
import random
import time

import pygame

from src import settings as cfg
from src.entities import Meteor
from src.game import Game, InputState, State
from src.render import Renderer


def autopilot(game):
    """IA simple: va hacia la estrella más cercana y huye de meteoros."""
    p = game.player
    tx, ty = p.x, cfg.HEIGHT - 90
    targets = game.stars + game.powerups
    if targets:
        t = min(targets, key=lambda s: (s.x - p.x) ** 2 + (s.y - p.y) ** 2)
        tx, ty = t.x, max(t.y, 200)
    fx, fy = tx - p.x, ty - p.y
    for m in game.meteors:
        dx, dy = p.x - m.x, p.y - m.y
        d = math.hypot(dx, dy) or 1
        if d < m.radius + 120:
            push = (m.radius + 120 - d) * 6
            fx += dx / d * push
            fy += dy / d * push
    dead = 8
    return InputState(left=fx < -dead, right=fx > dead, up=fy < -dead, down=fy > dead)


class Session:
    def __init__(self, headless, seed=3, highscore_path=None):
        if headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
        self.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
        pygame.display.set_caption(cfg.TITLE + " - modo evidencias")
        self.game = Game(rng=random.Random(seed), highscore_path=highscore_path)
        self.renderer = Renderer(self.screen)
        self.dt = 1 / cfg.FPS
        self.frames = 0

    def step(self, inp=None, n=1):
        for _ in range(n):
            pygame.event.pump()
            self.game.update(self.dt, inp if inp is not None else InputState())
            self.renderer.draw(self.game, self.dt)
            pygame.display.flip()
            self.frames += 1

    def play(self, seconds, until=None):
        for _ in range(int(seconds * cfg.FPS)):
            if self.game.state != State.PLAYING:
                break
            self.step(autopilot(self.game))
            if until and until(self.game):
                break

    def save(self, folder, name):
        path = os.path.join(folder, name)
        pygame.image.save(self.screen, path)
        print(f"  captura: {path}")


def capture_evidence(folder, headless=False):
    os.makedirs(folder, exist_ok=True)
    s = Session(headless, highscore_path=os.path.join(folder, "_record_demo.json"))
    g = s.game
    print("Generando capturas reales del juego...")
    s.step(n=40)
    s.save(folder, "01_menu_principal.png")

    g.show_instructions()
    s.step(n=30)
    s.save(folder, "02_instrucciones.png")

    g.start()
    s.play(6)
    s.save(folder, "03_partida_en_ejecucion.png")

    s.play(30, until=lambda gm: gm.combo >= 3)
    s.step(autopilot(g), n=2)
    s.save(folder, "04_puntuacion_y_combo.png")

    # Escudo y partículas (mejoras de las iteraciones 1 y 2)
    s.play(40, until=lambda gm: gm.shield)
    s.step(autopilot(g), n=10)
    s.save(folder, "05_mejora_escudo_y_efectos.png")

    g.toggle_pause()
    s.step(n=5)
    s.save(folder, "06_pausa.png")
    g.toggle_pause()

    # Se deja la nave quieta para forzar el Game Over de forma natural.
    t0 = time.time()
    while g.state == State.PLAYING and time.time() - t0 < 120:
        target = min(g.meteors, key=lambda m: abs(m.x - g.player.x), default=None)
        inp = InputState()
        if target:
            inp = InputState(left=target.x < g.player.x - 5, right=target.x > g.player.x + 5)
        s.step(inp)
    s.step(n=30)
    s.save(folder, "07_game_over.png")

    g.restart()
    s.step(n=20)
    s.save(folder, "08_reinicio_nueva_partida.png")
    try:
        os.remove(os.path.join(folder, "_record_demo.json"))
    except OSError:
        pass
    print(f"Listo: {s.frames} fotogramas renderizados.")
    pygame.quit()


def smoke_test(frames=600):
    """Recorre todos los estados durante `frames` fotogramas sin ventana."""
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "astro_smoke_record.json")
    s = Session(headless=True, highscore_path=tmp)
    g = s.game
    visited = set()
    t0 = time.perf_counter()
    s.step(n=10); visited.add(g.state)
    g.show_instructions(); s.step(n=10); visited.add(g.state)
    g.start()
    for i in range(frames):
        if g.state != State.PLAYING:
            break
        s.step(autopilot(g))
        visited.add(g.state)
        if i == frames // 2:
            g.toggle_pause(); s.step(n=5); visited.add(g.state); g.toggle_pause()
    g.lives = 1
    while g.state == State.PLAYING:
        g.invulnerable = 0
        g.shield = False
        g.meteors.append(Meteor(g.player.x, g.player.y, 20, 0, 0))
        s.step()
    visited.add(g.state)
    g.restart(); s.step(n=5); visited.add(g.state)
    elapsed = time.perf_counter() - t0
    pygame.quit()
    print(f"Prueba de humo OK: {s.frames} fotogramas en {elapsed:.2f}s "
          f"({s.frames / elapsed:.0f} FPS sin límite). Estados: {sorted(visited)}")
    return visited
