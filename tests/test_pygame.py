"""Pruebas de ejecución con Pygame real (ventana virtual 'dummy').

Si Pygame no está instalado se marcan como SKIPPED, no como superadas.
"""
import random

import pytest

pygame = pytest.importorskip("pygame")

from src import settings as cfg  # noqa: E402
from src.game import Game, InputState, State  # noqa: E402


@pytest.fixture
def screen():
    pygame.init()
    surf = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
    yield surf
    pygame.quit()


def test_importacion_modulos_pygame():
    import src.app  # noqa: F401
    import src.demo  # noqa: F401
    import src.render  # noqa: F401


def test_render_todos_los_estados(screen, tmp_path):
    from src.render import Renderer
    g = Game(rng=random.Random(0), highscore_path=tmp_path / "hs.json")
    r = Renderer(screen)
    for setup in (lambda: None, g.show_instructions, g.start, g.toggle_pause,
                  lambda: g.finish(State.GAME_OVER), g.restart,
                  lambda: g.finish(State.VICTORY)):
        setup()
        for _ in range(5):
            g.update(1 / 60, InputState())
            r.draw(g, 1 / 60)
    # El fotograma no está vacío: hay más de un color en pantalla.
    colors = {screen.get_at((x, y))[:3] for x in range(0, cfg.WIDTH, 40) for y in range(0, cfg.HEIGHT, 40)}
    assert len(colors) > 5


def test_teclas_cambian_estado(tmp_path):
    from src.app import handle_key
    g = Game(highscore_path=tmp_path / "hs.json")
    assert handle_key(g, pygame.K_i) and g.state == State.INSTRUCTIONS
    handle_key(g, pygame.K_RETURN); assert g.state == State.PLAYING
    handle_key(g, pygame.K_p); assert g.state == State.PAUSED
    handle_key(g, pygame.K_p); assert g.state == State.PLAYING
    g.finish(State.GAME_OVER)
    handle_key(g, pygame.K_r); assert g.state == State.PLAYING
    handle_key(g, pygame.K_ESCAPE); assert g.state == State.MENU
    assert handle_key(g, pygame.K_ESCAPE) is False   # ESC en el menú = salir


def test_prueba_de_humo_recorre_estados():
    from src.demo import smoke_test
    visited = smoke_test(300)
    assert {State.MENU, State.INSTRUCTIONS, State.PLAYING, State.PAUSED,
            State.GAME_OVER} <= visited
