"""Efectos visuales (lógica pura): partículas, textos flotantes, fondo
estrellado con paralaje y sacudida de pantalla.

No dependen de Pygame, solo calculan posiciones; render.py los dibuja.
"""
import math
import random

from src import settings as cfg


class Particle:
    def __init__(self, x, y, vx, vy, life, color, size):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size

    @property
    def alive(self):
        return self.life > 0

    @property
    def ratio(self):
        """1.0 al nacer, 0.0 al morir: sirve para desvanecer."""
        return max(0.0, self.life / self.max_life)

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.96
        self.vy *= 0.96


class FloatingText:
    def __init__(self, x, y, text, color, life=0.8):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.life = self.max_life = life

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.life -= dt
        self.y -= 45 * dt


class Starfield:
    """Tres capas de estrellas que se desplazan a distinta velocidad."""

    def __init__(self, width, height, rng=None):
        rng = rng or random.Random(7)
        self.width, self.height = width, height
        self.layers = []
        for speed, count, size in ((15, 70, 1), (35, 40, 2), (70, 18, 3)):
            stars = [[rng.uniform(0, width), rng.uniform(0, height)]
                     for _ in range(count)]
            self.layers.append((speed, size, stars))

    def update(self, dt, boost=1.0):
        for speed, _size, stars in self.layers:
            for s in stars:
                s[1] += speed * boost * dt
                if s[1] > self.height:
                    s[1] -= self.height


class Effects:
    """Agrupa todos los efectos y reacciona a los eventos del juego."""

    MAX_PARTICLES = 600

    def __init__(self, width, height, rng=None):
        self.rng = rng or random.Random()
        self.particles = []
        self.texts = []
        self.starfield = Starfield(width, height)
        self.shake = 0.0

    def burst(self, x, y, color, count=18, speed=180, life=0.6, size=4):
        for _ in range(count):
            a = self.rng.uniform(0, math.tau)
            v = self.rng.uniform(speed * 0.3, speed)
            self.particles.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v,
                                           self.rng.uniform(life * 0.5, life),
                                           color, self.rng.uniform(2, size)))

    def handle_events(self, events):
        for kind, x, y, *extra in events:
            if kind == "collect":
                self.burst(x, y, cfg.YELLOW, 14, 160, 0.5, 4)
                label = extra[0] if extra else "+10"
                self.texts.append(FloatingText(x, y - 10, label, cfg.YELLOW))
            elif kind == "hit":
                self.burst(x, y, cfg.ORANGE, 34, 280, 0.9, 6)
                self.shake = 0.35
            elif kind == "level_up":
                self.texts.append(FloatingText(x, y, "¡NIVEL ARRIBA!", cfg.CYAN, 1.4))

    def update(self, dt, boost=1.0):
        self.starfield.update(dt, boost)
        for p in self.particles:
            p.update(dt)
        for t in self.texts:
            t.update(dt)
        self.particles = [p for p in self.particles if p.alive][-self.MAX_PARTICLES:]
        self.texts = [t for t in self.texts if t.alive]
        self.shake = max(0.0, self.shake - dt)

    def shake_offset(self):
        if self.shake <= 0:
            return 0, 0
        k = 14 * self.shake
        return self.rng.uniform(-k, k), self.rng.uniform(-k, k)
