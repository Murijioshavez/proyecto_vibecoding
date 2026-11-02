"""Lógica central y máquina de estados de Astro Recolector.

Esta clase no importa Pygame: recibe el tiempo transcurrido (dt) y el estado
de las teclas (InputState) y actualiza el mundo. La capa gráfica (app.py)
solo traduce eventos de teclado y dibuja.
"""
import json
import random
from dataclasses import dataclass

from src import settings as cfg
from src.entities import Meteor, Player, PowerUp, Star


class State:
    MENU = "menu"
    INSTRUCTIONS = "instructions"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    VICTORY = "victory"


@dataclass
class InputState:
    left: bool = False
    right: bool = False
    up: bool = False
    down: bool = False


class Game:
    def __init__(self, width=cfg.WIDTH, height=cfg.HEIGHT, rng=None,
                 highscore_path=None):
        self.width = width
        self.height = height
        self.rng = rng or random.Random()
        self.highscore_path = highscore_path or cfg.HIGHSCORE_FILE
        self.highscore = self.load_highscore()
        self.state = State.MENU
        self.reset()

    # ------------------------------------------------------------------ #
    # Récords
    # ------------------------------------------------------------------ #
    def load_highscore(self):
        """Lee el récord. Un archivo ausente, corrupto o con datos inválidos
        no debe impedir jugar: en ese caso el récord vale 0."""
        try:
            with open(self.highscore_path, "r", encoding="utf-8") as f:
                value = json.load(f).get("highscore", 0)
            return value if isinstance(value, int) and value >= 0 else 0
        except (OSError, ValueError, AttributeError):
            return 0

    def save_highscore(self):
        """Guarda el récord; si no se puede escribir, el juego continúa."""
        try:
            with open(self.highscore_path, "w", encoding="utf-8") as f:
                json.dump({"highscore": self.highscore}, f)
            return True
        except OSError:
            return False

    # ------------------------------------------------------------------ #
    # Transiciones de estado
    # ------------------------------------------------------------------ #
    def reset(self):
        self.player = Player(self.width / 2, self.height - 80)
        self.stars = []
        self.meteors = []
        self.score = 0
        self.lives = cfg.PLAYER_LIVES
        self.elapsed = 0.0
        self.star_timer = 0.0
        self.meteor_timer = 0.0
        self.events = []  # eventos para efectos visuales: (tipo, x, y, ...)
        # Iteración 2: invulnerabilidad, combo y escudo
        self.powerups = []
        self.powerup_timer = 0.0
        self.invulnerable = 0.0
        self.shield = False
        self.combo = 1
        self.combo_timer = 0.0
        self.new_record = False

    def start(self):
        self.reset()
        self.state = State.PLAYING

    def restart(self):
        self.start()

    def show_instructions(self):
        if self.state == State.MENU:
            self.state = State.INSTRUCTIONS

    def back_to_menu(self):
        self.state = State.MENU

    def toggle_pause(self):
        if self.state == State.PLAYING:
            self.state = State.PAUSED
        elif self.state == State.PAUSED:
            self.state = State.PLAYING

    # ------------------------------------------------------------------ #
    # Dificultad progresiva
    # ------------------------------------------------------------------ #
    @property
    def level(self):
        return 1 + self.score // cfg.POINTS_PER_LEVEL

    def meteor_speed(self):
        return cfg.METEOR_BASE_SPEED + (self.level - 1) * cfg.METEOR_SPEED_PER_LEVEL

    def meteor_interval(self):
        interval = cfg.METEOR_BASE_INTERVAL - (self.level - 1) * cfg.METEOR_INTERVAL_PER_LEVEL
        return max(cfg.METEOR_MIN_INTERVAL, interval)

    # ------------------------------------------------------------------ #
    # Generación de objetos
    # ------------------------------------------------------------------ #
    def spawn_star(self):
        x = self.rng.uniform(40, self.width - 40)
        self.stars.append(Star(x, -20))

    def on_screen(self, e):
        """True mientras el objeto siga cerca del área visible."""
        m = cfg.OFFSCREEN_MARGIN
        return (-m - e.radius <= e.x <= self.width + m + e.radius
                and e.y <= self.height + m + e.radius)

    def spawn_meteor(self):
        if len(self.meteors) >= cfg.MAX_METEORS:
            return
        r =self.rng.randint(cfg.METEOR_MIN_RADIUS, cfg.METEOR_MAX_RADIUS)
        x = self.rng.uniform(r, self.width - r)
        speed = self.meteor_speed() * self.rng.uniform(0.85, 1.2)
        vx = self.rng.uniform(-60, 60)
        self.meteors.append(Meteor(x, -r, r, vx, speed, self.rng))

    # ------------------------------------------------------------------ #
    # Bucle de actualización
    # ------------------------------------------------------------------ #
    def update(self, dt, inp):
        self.events.clear()
        if self.state != State.PLAYING:
            return
        # Un dt enorme (ventana arrastrada, equipo lento) haría que los
        # objetos "atraviesen" la nave: se limita a MAX_DT.
        dt = max(0.0, min(dt, cfg.MAX_DT))

        self.elapsed += dt
        self.player.update(dt, inp, self.width, self.height)

        self.star_timer += dt
        if self.star_timer >= cfg.STAR_SPAWN_INTERVAL:
            self.star_timer = 0.0
            self.spawn_star()

        self.meteor_timer += dt
        if self.meteor_timer >= self.meteor_interval():
            self.meteor_timer = 0.0
            self.spawn_meteor()

        self.powerup_timer += dt
        if self.powerup_timer >= cfg.SHIELD_SPAWN_INTERVAL:
            self.powerup_timer = 0.0
            self.powerups.append(PowerUp(self.rng.uniform(40, self.width - 40), -20))

        # El combo se pierde si pasa demasiado tiempo sin recoger estrellas.
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 1
        self.invulnerable = max(0.0, self.invulnerable - dt)

        old_level = self.level
        for star in self.stars:
            star.update(dt)
            if star.alive and star.collides_with(self.player):
                self.collect_star(star)

        for p in self.powerups:
            p.update(dt)
            if p.alive and p.collides_with(self.player):
                p.alive = False
                self.shield = True
                self.events.append(("collect", p.x, p.y, "¡ESCUDO!"))

        for meteor in self.meteors:
            meteor.update(dt)
            if meteor.alive and meteor.collides_with(self.player):
                self.hit_by(meteor)

        if self.level > old_level:
            self.events.append(("level_up", self.width / 2, self.height / 2))

        self.stars = [s for s in self.stars if s.alive and self.on_screen(s)]
        self.meteors = [m for m in self.meteors if m.alive and self.on_screen(m)]
        self.powerups = [p for p in self.powerups if p.alive and self.on_screen(p)]

        if self.score >= cfg.VICTORY_SCORE:
            self.finish(State.VICTORY)
        elif self.lives <= 0:
            self.finish(State.GAME_OVER)

    def collect_star(self, star):
        """Suma puntos con el multiplicador de combo actual."""
        star.alive = False
        gained = cfg.STAR_POINTS * self.combo
        self.score += gained
        label = f"+{gained}" if self.combo == 1 else f"+{gained} x{self.combo}"
        self.events.append(("collect", star.x, star.y, label))
        self.combo = min(cfg.COMBO_MAX, self.combo + 1)
        self.combo_timer = cfg.COMBO_WINDOW

    def hit_by(self, meteor):
        """Gestiona un choque. Durante la invulnerabilidad no pasa nada."""
        if self.invulnerable > 0:
            return
        meteor.alive = False
        self.events.append(("hit", self.player.x, self.player.y))
        self.combo = 1
        self.combo_timer = 0.0
        if self.shield:
            self.shield = False          # el escudo absorbe el golpe
        else:
            self.lives -= 1
        self.invulnerable = cfg.INVULNERABLE_TIME

    def finish(self, final_state):
        self.state = final_state
        if self.score > self.highscore:
            self.highscore = self.score
            self.new_record = True
            self.save_highscore()
