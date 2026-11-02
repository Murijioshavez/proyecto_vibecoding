"""Funciones de dibujo con Pygame. Todos los gráficos se generan por código
(no hay imágenes externas): polígonos, círculos y superficies con alfa."""
import math

import pygame

from src import settings as cfg
from src.effects import Effects
from src.game import State


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.world = pygame.Surface((cfg.WIDTH, cfg.HEIGHT))
        self.font_big = pygame.font.Font(None, 92)
        self.font_mid = pygame.font.Font(None, 44)
        self.font_small = pygame.font.Font(None, 30)
        self.font_tiny = pygame.font.Font(None, 24)
        self.effects = Effects(cfg.WIDTH, cfg.HEIGHT)
        self.time = 0.0
        self._glow_cache = {}
        self.background = self._make_gradient()

    # ------------------------------------------------------------------ #
    # Utilidades
    # ------------------------------------------------------------------ #
    def _make_gradient(self):
        """Degradado vertical de azul noche a violeta."""
        surf = pygame.Surface((cfg.WIDTH, cfg.HEIGHT))
        top, bottom = (8, 10, 28), (38, 16, 58)
        for y in range(cfg.HEIGHT):
            t = y / cfg.HEIGHT
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(surf, color, (0, y), (cfg.WIDTH, y))
        return surf

    def glow(self, radius, color):
        """Halo circular para mezcla aditiva, cacheado por (radio, color).

        Corrección tras la revisión visual en Windows: antes se usaba una
        superficie SRCALPHA con BLEND_RGBA_ADD, pero ese modo suma el RGB
        ignorando el alfa y el halo salía como un disco sólido. Ahora la
        intensidad se "premultiplica" en el propio color (negro = no suma
        nada) y se mezcla con BLEND_RGB_ADD.
        """
        key = (int(radius), color)
        if key not in self._glow_cache:
            r = max(1, int(radius))
            surf = pygame.Surface((r * 2, r * 2))
            surf.fill((0, 0, 0))
            for i in range(r, 0, -2):
                k = 0.30 * (1 - i / r) ** 2          # 0 en el borde, 0.30 en el centro
                pygame.draw.circle(surf, tuple(int(c * k) for c in color), (r, r), i)
            self._glow_cache[key] = surf
        return self._glow_cache[key]

    def blit_glow(self, target, x, y, radius, color):
        g = self.glow(radius, color)
        target.blit(g, (x - int(radius), y - int(radius)), special_flags=pygame.BLEND_RGB_ADD)

    def text(self, target, msg, font, color, center, shadow=True):
        if shadow:
            s = font.render(msg, True, (0, 0, 0))
            target.blit(s, s.get_rect(center=(center[0] + 3, center[1] + 3)))
        surf = font.render(msg, True, color)
        rect = surf.get_rect(center=center)
        target.blit(surf, rect)
        return rect

    # ------------------------------------------------------------------ #
    # Fondo
    # ------------------------------------------------------------------ #
    def draw_background(self, target):
        target.blit(self.background, (0, 0))
        for _speed, size, stars in self.effects.starfield.layers:
            shade = 90 + size * 50
            for x, y in stars:
                twinkle = 0.75 + 0.25 * math.sin(self.time * 3 + x)
                c = int(shade * twinkle)
                pygame.draw.circle(target, (c, c, min(255, c + 30)), (int(x), int(y)), size)

    # ------------------------------------------------------------------ #
    # Entidades
    # ------------------------------------------------------------------ #
    def draw_player(self, target, player):
        x, y, r = player.x, player.y, player.radius
        tilt = player.tilt * 5
        # Llama del motor animada
        flame = r * (0.9 + 0.35 * math.sin(self.time * 30))
        pygame.draw.polygon(target, cfg.ORANGE,
                            [(x - r * 0.4, y + r * 0.6), (x + r * 0.4, y + r * 0.6),
                             (x, y + r * 0.6 + flame)])
        pygame.draw.polygon(target, cfg.YELLOW,
                            [(x - r * 0.2, y + r * 0.6), (x + r * 0.2, y + r * 0.6),
                             (x, y + r * 0.6 + flame * 0.55)])
        self.blit_glow(target, x, y, r * 2.4, cfg.CYAN)
        body = [(x, y - r * 1.25), (x - r + tilt, y + r), (x, y + r * 0.45),
                (x + r + tilt, y + r)]
        pygame.draw.polygon(target, (40, 140, 200), body)
        pygame.draw.polygon(target, cfg.CYAN, body, 3)
        pygame.draw.circle(target, cfg.WHITE, (int(x), int(y - r * 0.2)), max(3, r // 4))

    def star_points(self, x, y, r, rot=0.0):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + rot + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.45
            pts.append((x + math.cos(a) * rad, y + math.sin(a) * rad))
        return pts

    def draw_star(self, target, star):
        pulse = 1 + 0.15 * math.sin(star.phase * 2)
        r = star.radius * pulse
        self.blit_glow(target, star.x, star.y, r * 2.6, cfg.YELLOW)
        pts = self.star_points(star.x, star.y, r, star.phase * 0.3)
        pygame.draw.polygon(target, cfg.YELLOW, pts)
        pygame.draw.polygon(target, cfg.WHITE, pts, 1)

    def draw_meteor(self, target, meteor):
        pts = meteor.polygon()
        # Estela de fuego detrás del meteoro
        trail = (meteor.x - meteor.vx * 0.12, meteor.y - meteor.vy * 0.12)
        self.blit_glow(target, trail[0], trail[1], meteor.radius * 1.6, (120, 50, 20))
        pygame.draw.polygon(target, cfg.METEOR_COLOR, pts)
        pygame.draw.polygon(target, cfg.METEOR_EDGE, pts, 3)
        # Cráter decorativo
        cx = meteor.x + math.cos(meteor.angle) * meteor.radius * 0.3
        cy = meteor.y + math.sin(meteor.angle) * meteor.radius * 0.3
        pygame.draw.circle(target, cfg.METEOR_EDGE, (int(cx), int(cy)),
                           max(2, int(meteor.radius * 0.22)))

    def draw_powerup(self, target, p):
        self.blit_glow(target, p.x, p.y, p.radius * 2.6, cfg.GREEN)
        r = int(p.radius * (1 + 0.12 * math.sin(p.phase * 2)))
        pygame.draw.circle(target, (30, 90, 60), (int(p.x), int(p.y)), r)
        pygame.draw.circle(target, cfg.GREEN, (int(p.x), int(p.y)), r, 3)
        self.text(target, "S", self.font_tiny, cfg.WHITE, (p.x, p.y + 1), shadow=False)

    def draw_effects(self, target):
        for p in self.effects.particles:
            size = max(1, int(p.size * p.ratio))
            pygame.draw.circle(target, p.color, (int(p.x), int(p.y)), size)
        for t in self.effects.texts:
            alpha = max(0, min(255, int(255 * t.life / t.max_life)))
            surf = self.font_small.render(t.text, True, t.color)
            surf.set_alpha(alpha)
            target.blit(surf, surf.get_rect(center=(t.x, t.y)))

    # ------------------------------------------------------------------ #
    # HUD
    # ------------------------------------------------------------------ #
    def draw_heart(self, target, x, y, color):
        pygame.draw.circle(target, color, (x - 6, y), 7)
        pygame.draw.circle(target, color, (x + 6, y), 7)
        pygame.draw.polygon(target, color, [(x - 13, y + 2), (x + 13, y + 2), (x, y + 17)])

    def draw_hud(self, target, game):
        panel = pygame.Surface((cfg.WIDTH, 64), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 110))
        target.blit(panel, (0, 0))
        target.blit(self.font_mid.render(f"{game.score}", True, cfg.WHITE), (20, 14))
        target.blit(self.font_tiny.render("PUNTOS", True, cfg.GREY), (22, 44))
        # Barra de progreso hacia el siguiente nivel
        bx, by, bw = 330, 22, 300
        progress = (game.score % cfg.POINTS_PER_LEVEL) / cfg.POINTS_PER_LEVEL
        pygame.draw.rect(target, (50, 50, 80), (bx, by, bw, 14), border_radius=7)
        pygame.draw.rect(target, cfg.CYAN, (bx, by, int(bw * progress), 14), border_radius=7)
        self.text(target, f"NIVEL {game.level}", self.font_tiny, cfg.CYAN,
                  (bx + bw // 2, by + 30), shadow=False)
        if game.combo > 1:
            self.text(target, f"COMBO x{game.combo}", self.font_small, cfg.ORANGE,
                      (bx + bw + 90, 32), shadow=False)
        if game.shield:
            self.text(target, "ESCUDO", self.font_tiny, cfg.GREEN, (180, 32), shadow=False)
        for i in range(cfg.PLAYER_LIVES):
            color = cfg.RED if i < game.lives else (70, 60, 80)
            self.draw_heart(target, cfg.WIDTH - 40 - i * 36, 26, color)

    # ------------------------------------------------------------------ #
    # Pantallas
    # ------------------------------------------------------------------ #
    def overlay(self, target, alpha=150):
        shade = pygame.Surface((cfg.WIDTH, cfg.HEIGHT), pygame.SRCALPHA)
        shade.fill((5, 5, 20, alpha))
        target.blit(shade, (0, 0))

    def draw_world(self, target, game):
        for star in game.stars:
            self.draw_star(target, star)
        for meteor in game.meteors:
            self.draw_meteor(target, meteor)
        for p in game.powerups:
            self.draw_powerup(target, p)
        # Parpadeo durante la invulnerabilidad
        if game.invulnerable <= 0 or int(self.time * 12) % 2 == 0:
            self.draw_player(target, game.player)
        if game.shield:
            r = int(game.player.radius * 1.9 + 2 * math.sin(self.time * 6))
            pygame.draw.circle(target, cfg.GREEN, (int(game.player.x), int(game.player.y)), r, 3)
        self.draw_effects(target)
        self.draw_hud(target, game)

    def draw_menu(self, target, game):
        cx = cfg.WIDTH // 2
        bob = math.sin(self.time * 2) * 8
        self.blit_glow(target, cx, 190 + bob, 260, (90, 60, 160))
        self.text(target, "ASTRO", self.font_big, cfg.CYAN, (cx, 150 + bob))
        self.text(target, "RECOLECTOR", self.font_big, cfg.YELLOW, (cx, 225 + bob))
        # Estrella decorativa giratoria
        pts = self.star_points(cx, 320, 24, self.time)
        pygame.draw.polygon(target, cfg.YELLOW, pts)
        options = [("ENTER", "Jugar"), ("I", "Instrucciones"), ("ESC", "Salir")]
        for i, (key, label) in enumerate(options):
            y = 395 + i * 48
            pygame.draw.rect(target, (40, 40, 80), (cx - 170, y - 20, 340, 40), border_radius=10)
            pygame.draw.rect(target, cfg.PURPLE, (cx - 170, y - 20, 340, 40), 2, border_radius=10)
            self.text(target, f"{key}  -  {label}", self.font_small, cfg.WHITE, (cx, y), shadow=False)
        self.text(target, f"Récord: {game.highscore}", self.font_small, cfg.GREY, (cx, 560))

    def draw_instructions(self, target):
        cx = cfg.WIDTH // 2
        self.text(target, "Instrucciones", self.font_big, cfg.YELLOW, (cx, 90))
        lines = [
            ("Flechas / WASD", "mover la nave"),
            ("Estrella amarilla", "+10 puntos (combo hasta x5)"),
            ("Esfera verde S", "escudo: absorbe un choque"),
            ("Meteoro", "pierdes una vida"),
            ("Cada 100 puntos", "sube el nivel: más meteoros y más rápidos"),
            ("Meta", f"llegar a {cfg.VICTORY_SCORE} puntos"),
            ("P / ESC", "pausa / volver al menú"),
        ]
        for i, (k, v) in enumerate(lines):
            y = 190 + i * 50
            self.text(target, k, self.font_small, cfg.CYAN, (cx - 150, y), shadow=False)
            self.text(target, v, self.font_small, cfg.WHITE, (cx + 150, y), shadow=False)
        blink = int(self.time * 2) % 2 == 0
        if blink:
            self.text(target, "Pulsa ENTER para jugar", self.font_mid, cfg.GREEN, (cx, 560))

    def draw_end(self, target, game):
        self.overlay(target)
        cx = cfg.WIDTH // 2
        if game.state == State.VICTORY:
            self.text(target, "¡VICTORIA!", self.font_big, cfg.GREEN, (cx, 190))
        else:
            self.text(target, "GAME OVER", self.font_big, cfg.RED, (cx, 190))
        self.text(target, f"Puntuación: {game.score}", self.font_mid, cfg.WHITE, (cx, 290))
        self.text(target, f"Nivel alcanzado: {game.level}", self.font_small, cfg.CYAN, (cx, 340))
        record = "¡NUEVO RÉCORD!" if game.new_record else f"Récord: {game.highscore}"
        self.text(target, record, self.font_mid, cfg.YELLOW, (cx, 395))
        self.text(target, "R - Reiniciar      M - Menú", self.font_small, cfg.GREY, (cx, 480))

    # ------------------------------------------------------------------ #
    def draw(self, game, dt):
        self.time += dt
        self.effects.handle_events(game.events)
        boost = 1.0 + 0.25 * (game.level - 1) if game.state == State.PLAYING else 1.0
        self.effects.update(dt, boost)

        target = self.world
        self.draw_background(target)
        if game.state == State.MENU:
            self.draw_menu(target, game)
        elif game.state == State.INSTRUCTIONS:
            self.draw_instructions(target)
        else:
            self.draw_world(target, game)
            if game.state == State.PAUSED:
                self.overlay(target, 120)
                self.text(target, "PAUSA", self.font_big, cfg.WHITE,
                          (cfg.WIDTH // 2, cfg.HEIGHT // 2 - 20))
                self.text(target, "P para continuar", self.font_small, cfg.GREY,
                          (cfg.WIDTH // 2, cfg.HEIGHT // 2 + 40))
            elif game.state in (State.GAME_OVER, State.VICTORY):
                self.draw_end(target, game)

        ox, oy = self.effects.shake_offset()
        self.screen.fill((0, 0, 0))
        self.screen.blit(target, (ox, oy))
