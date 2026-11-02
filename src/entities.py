"""Entidades del juego (lógica pura, sin dependencias de Pygame).

Separar la lógica del dibujo permite probar movimiento y colisiones con
pruebas automatizadas sin abrir ninguna ventana.
"""
import math
import random

from src import settings as cfg


def circles_collide(x1, y1, r1, x2, y2, r2):
    """Devuelve True si dos círculos se tocan o se solapan."""
    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy <= (r1 + r2) ** 2


class Entity:
    """Clase base: posición, radio y bandera de vida."""

    def __init__(self, x, y, radius):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.alive = True

    def collides_with(self, other):
        return circles_collide(self.x, self.y, self.radius,
                               other.x, other.y, other.radius)


class Player(Entity):
    """Nave controlada por el jugador."""

    def __init__(self, x, y):
        super().__init__(x, y, cfg.PLAYER_RADIUS)
        self.speed = cfg.PLAYER_SPEED
        self.tilt = 0.0  # inclinación visual según la dirección

    def update(self, dt, inp, width, height):
        dx = (1 if inp.right else 0) - (1 if inp.left else 0)
        dy = (1 if inp.down else 0) - (1 if inp.up else 0)
        if dx and dy:
            # Normalizar para que la diagonal no sea más rápida.
            dx *= 0.7071
            dy *= 0.7071
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
        # Mantener la nave dentro de la pantalla.
        self.x = max(self.radius, min(width - self.radius, self.x))
        self.y = max(self.radius, min(height - self.radius, self.y))
        self.tilt = dx


class Star(Entity):
    """Estrella que cae suavemente y da puntos al recogerla."""

    def __init__(self, x, y, speed=cfg.STAR_SPEED):
        super().__init__(x, y, cfg.STAR_RADIUS)
        self.speed = speed
        self.phase = random.uniform(0, math.tau)

    def update(self, dt):
        self.phase += dt * 4
        self.y += self.speed * dt
        self.x += math.sin(self.phase) * 20 * dt


class Meteor(Entity):
    """Meteoro que cae; tocarlo cuesta una vida."""

    def __init__(self, x, y, radius, vx, vy, rng=random):
        super().__init__(x, y, radius)
        self.vx = vx
        self.vy = vy
        self.angle = 0.0
        self.spin = rng.uniform(-2.5, 2.5)
        # Forma irregular: 9 vértices con radios aleatorios.
        self.shape = [rng.uniform(0.75, 1.1) for _ in range(9)]

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.spin * dt

    def polygon(self):
        """Puntos del polígono para dibujar el meteoro."""
        n = len(self.shape)
        pts = []
        for i, k in enumerate(self.shape):
            a = self.angle + i * math.tau / n
            pts.append((self.x + math.cos(a) * self.radius * k,
                        self.y + math.sin(a) * self.radius * k))
        return pts


class PowerUp(Entity):
    """Escudo: absorbe el siguiente impacto de meteoro."""

    def __init__(self, x, y, kind="shield"):
        super().__init__(x, y, cfg.SHIELD_RADIUS)
        self.kind = kind
        self.phase = 0.0

    def update(self, dt):
        self.phase += dt * 3
        self.y += cfg.SHIELD_SPEED * dt
