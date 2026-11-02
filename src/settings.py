"""Configuración global de Astro Recolector.

Todas las constantes del juego viven aquí para poder ajustar el balance
sin tocar la lógica.
"""

# --- Ventana ---------------------------------------------------------------
WIDTH = 960
HEIGHT = 640
FPS = 60
TITLE = "Astro Recolector"

# --- Colores (R, G, B) ----------------------------------------------------
BG_COLOR = (10, 12, 30)
WHITE = (240, 240, 255)
GREY = (140, 145, 170)
YELLOW = (255, 214, 90)
CYAN = (90, 230, 255)
RED = (255, 90, 110)
ORANGE = (255, 150, 70)
GREEN = (120, 255, 160)
PURPLE = (170, 120, 255)
METEOR_COLOR = (150, 110, 90)
METEOR_EDGE = (90, 60, 50)

# --- Jugador ---------------------------------------------------------------
PLAYER_SPEED = 330.0      # píxeles por segundo
PLAYER_RADIUS = 18
PLAYER_LIVES = 3

# --- Estrellas (objetos a recolectar) --------------------------------------
STAR_RADIUS = 11
STAR_POINTS = 10
STAR_SPEED = 110.0
STAR_SPAWN_INTERVAL = 0.9  # segundos

# --- Meteoros (obstáculos) -------------------------------------------------
METEOR_MIN_RADIUS = 14
METEOR_MAX_RADIUS = 34
METEOR_BASE_SPEED = 140.0
METEOR_SPEED_PER_LEVEL = 28.0
METEOR_BASE_INTERVAL = 1.1
METEOR_INTERVAL_PER_LEVEL = 0.09
METEOR_MIN_INTERVAL = 0.28

# --- Progresión ------------------------------------------------------------
POINTS_PER_LEVEL = 100     # cada 100 puntos sube un nivel
VICTORY_SCORE = 1000       # puntuación para ganar la partida

# --- Archivos --------------------------------------------------------------
# Ruta independiente del directorio desde el que se lance el juego
# (iteración 3): el récord siempre se guarda junto al proyecto.
from pathlib import Path  # noqa: E402

PROJECT_DIR = Path(__file__).resolve().parent.parent
HIGHSCORE_FILE = PROJECT_DIR / "highscore.json"

# --- Iteración 2: jugabilidad ----------------------------------------------
INVULNERABLE_TIME = 1.5    # segundos de invulnerabilidad tras un choque
COMBO_WINDOW = 1.6         # segundos para encadenar estrellas
COMBO_MAX = 5              # multiplicador máximo
SHIELD_SPAWN_INTERVAL = 14.0
SHIELD_RADIUS = 13
SHIELD_SPEED = 95.0

# --- Iteración 3: estabilidad -----------------------------------------------
MAX_DT = 0.05              # límite de dt por fotograma (evita "saltos")
MAX_METEORS = 40           # tope de seguridad de objetos simultáneos
OFFSCREEN_MARGIN = 60      # margen para eliminar objetos fuera de pantalla
