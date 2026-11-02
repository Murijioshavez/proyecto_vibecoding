"""Pruebas de lógica: puntuación, estados, reinicio, colisiones, dificultad.

No necesitan Pygame: la lógica está separada del dibujo.
"""
import json
import random

import pytest

from src import settings as cfg
from src.effects import Effects
from src.entities import Meteor, Player, PowerUp, Star, circles_collide
from src.game import Game, InputState, State

DT = 1 / 60


@pytest.fixture
def game(tmp_path):
    g = Game(rng=random.Random(42), highscore_path=tmp_path / "hs.json")
    return g


def playing(game):
    game.start()
    # Vaciar temporizadores para que no aparezcan objetos al azar.
    game.star_timer = game.meteor_timer = game.powerup_timer = -1e9
    return game


# ---------------------------------------------------------------- colisiones
def test_colision_circulos_se_tocan():
    assert circles_collide(0, 0, 5, 10, 0, 5)
    assert circles_collide(0, 0, 5, 3, 4, 1)


def test_colision_circulos_separados():
    assert not circles_collide(0, 0, 5, 10.01, 0, 5)


def test_estrella_colisiona_con_jugador():
    p = Player(100, 100)
    assert Star(100 + p.radius, 100).collides_with(p)
    assert not Star(300, 300).collides_with(p)


# ---------------------------------------------------------------- jugador
def test_jugador_se_mueve_y_no_sale_de_pantalla():
    p = Player(100, 100)
    p.update(0.1, InputState(right=True), 960, 640)
    assert p.x == pytest.approx(100 + cfg.PLAYER_SPEED * 0.1)
    for _ in range(200):
        p.update(0.05, InputState(left=True, up=True), 960, 640)
    assert p.x == p.radius and p.y == p.radius


def test_diagonal_no_es_mas_rapida():
    a, b = Player(400, 300), Player(400, 300)
    a.update(0.1, InputState(right=True), 960, 640)
    b.update(0.1, InputState(right=True, down=True), 960, 640)
    dist_b = ((b.x - 400) ** 2 + (b.y - 300) ** 2) ** 0.5
    assert dist_b == pytest.approx(a.x - 400, rel=0.01)


# ---------------------------------------------------------------- estados
def test_estado_inicial_es_menu(game):
    assert game.state == State.MENU


def test_flujo_de_estados(game):
    game.show_instructions()
    assert game.state == State.INSTRUCTIONS
    game.back_to_menu()
    game.start()
    assert game.state == State.PLAYING
    game.toggle_pause()
    assert game.state == State.PAUSED
    game.toggle_pause()
    assert game.state == State.PLAYING


def test_pausa_congela_el_mundo(game):
    playing(game)
    game.stars.append(Star(100, 100))
    game.toggle_pause()
    game.update(DT, InputState(right=True))
    assert game.stars[0].y == 100 and game.elapsed == 0


def test_instrucciones_solo_desde_menu(game):
    playing(game)
    game.show_instructions()
    assert game.state == State.PLAYING


# ---------------------------------------------------------------- puntuación
def test_recoger_estrella_suma_puntos(game):
    playing(game)
    game.stars.append(Star(game.player.x, game.player.y))
    game.update(DT, InputState())
    assert game.score == cfg.STAR_POINTS
    assert game.stars == []
    assert any(e[0] == "collect" for e in game.events)


def test_combo_multiplica_puntos(game):
    playing(game)
    for _ in range(3):
        game.stars.append(Star(game.player.x, game.player.y))
        game.update(DT, InputState())
    assert game.score == 10 + 20 + 30
    assert game.combo == 4


def test_combo_tiene_tope(game):
    playing(game)
    for _ in range(10):
        game.stars.append(Star(game.player.x, game.player.y))
        game.update(DT, InputState())
    assert game.combo == cfg.COMBO_MAX


def test_combo_caduca(game):
    playing(game)
    game.stars.append(Star(game.player.x, game.player.y))
    game.update(DT, InputState())
    for _ in range(int(cfg.COMBO_WINDOW / DT) + 5):
        game.update(DT, InputState())
    assert game.combo == 1


# ---------------------------------------------------------------- dificultad
def test_nivel_sube_con_puntuacion(game):
    playing(game)
    assert game.level == 1
    game.score = cfg.POINTS_PER_LEVEL * 3
    assert game.level == 4


def test_dificultad_progresiva(game):
    playing(game)
    v1, i1 = game.meteor_speed(), game.meteor_interval()
    game.score = 500
    assert game.meteor_speed() > v1
    assert game.meteor_interval() < i1
    game.score = 10 ** 6
    assert game.meteor_interval() == cfg.METEOR_MIN_INTERVAL


def test_evento_subida_de_nivel(game):
    playing(game)
    game.score = cfg.POINTS_PER_LEVEL - cfg.STAR_POINTS
    game.stars.append(Star(game.player.x, game.player.y))
    game.update(DT, InputState())
    assert any(e[0] == "level_up" for e in game.events)


# ---------------------------------------------------------------- choques
def test_meteoro_quita_una_vida(game):
    playing(game)
    game.meteors.append(Meteor(game.player.x, game.player.y, 20, 0, 0))
    game.update(DT, InputState())
    assert game.lives == cfg.PLAYER_LIVES - 1
    assert game.meteors == []


def test_invulnerabilidad_evita_daño_repetido(game):
    """Regresión del diagnóstico v1: un solo meteoro quitaba todas las vidas."""
    playing(game)
    for _ in range(30):
        game.meteors.append(Meteor(game.player.x, game.player.y, 20, 0, 0))
        game.update(DT, InputState())
    assert game.lives == cfg.PLAYER_LIVES - 1
    assert game.state == State.PLAYING


def test_escudo_absorbe_golpe(game):
    playing(game)
    game.powerups.append(PowerUp(game.player.x, game.player.y))
    game.update(DT, InputState())
    assert game.shield
    game.meteors.append(Meteor(game.player.x, game.player.y, 20, 0, 0))
    game.update(DT, InputState())
    assert not game.shield and game.lives == cfg.PLAYER_LIVES


def test_choque_reinicia_combo(game):
    playing(game)
    game.combo = 4
    game.meteors.append(Meteor(game.player.x, game.player.y, 20, 0, 0))
    game.update(DT, InputState())
    assert game.combo == 1


# ---------------------------------------------------------------- fin de partida
def test_game_over_al_perder_vidas(game):
    playing(game)
    game.lives = 1
    game.meteors.append(Meteor(game.player.x, game.player.y, 20, 0, 0))
    game.update(DT, InputState())
    assert game.state == State.GAME_OVER


def test_victoria(game):
    playing(game)
    game.score = cfg.VICTORY_SCORE - cfg.STAR_POINTS
    game.stars.append(Star(game.player.x, game.player.y))
    game.update(DT, InputState())
    assert game.state == State.VICTORY


def test_reinicio_restaura_todo(game):
    playing(game)
    game.score, game.lives, game.combo, game.shield = 340, 1, 3, True
    game.meteors.append(Meteor(10, 10, 20, 0, 0))
    game.finish(State.GAME_OVER)
    game.restart()
    assert game.state == State.PLAYING
    assert (game.score, game.lives, game.combo, game.shield) == (0, cfg.PLAYER_LIVES, 1, False)
    assert game.meteors == [] and game.stars == []


# ---------------------------------------------------------------- récord
def test_record_se_guarda_y_carga(tmp_path):
    path = tmp_path / "hs.json"
    g = Game(highscore_path=path)
    playing(g)
    g.score = 250
    g.finish(State.GAME_OVER)
    assert g.new_record
    assert Game(highscore_path=path).highscore == 250


def test_record_no_baja(tmp_path):
    path = tmp_path / "hs.json"
    path.write_text(json.dumps({"highscore": 500}))
    g = Game(highscore_path=path)
    playing(g)
    g.score = 100
    g.finish(State.GAME_OVER)
    assert g.highscore == 500 and not g.new_record


@pytest.mark.parametrize("content", ["{corrupto", "[]", '{"highscore": "x"}', '{"highscore": -5}', ""])
def test_record_corrupto_no_rompe_el_juego(tmp_path, content):
    path = tmp_path / "hs.json"
    path.write_text(content)
    assert Game(highscore_path=path).highscore == 0


def test_record_en_ruta_no_escribible(tmp_path):
    g = Game(highscore_path=tmp_path / "no_existe" / "hs.json")
    assert g.save_highscore() is False


# ---------------------------------------------------------------- estabilidad
def test_dt_limitado(game):
    playing(game)
    x0 = game.player.x
    game.update(3.0, InputState(right=True))
    assert game.player.x - x0 <= cfg.PLAYER_SPEED * cfg.MAX_DT + 1e-6


def test_objetos_fuera_de_pantalla_se_eliminan(game):
    playing(game)
    game.meteors.append(Meteor(100, game.height + 500, 20, 0, 0))
    game.stars.append(Star(100, game.height + 500))
    game.update(DT, InputState())
    assert game.meteors == [] and game.stars == []


def test_partida_larga_sin_acumular_objetos():
    g = Game(rng=random.Random(1), highscore_path=None)
    g.save_highscore = lambda: True
    g.start()
    for _ in range(60 * 120):
        g.lives = 99
        g.update(DT, InputState(left=True))
    assert len(g.meteors) <= cfg.MAX_METEORS
    assert len(g.meteors) < 20


def test_efectos_limitan_particulas():
    fx = Effects(960, 640, random.Random(0))
    for _ in range(100):
        fx.handle_events([("hit", 100, 100)])
    fx.update(DT)
    assert len(fx.particles) <= Effects.MAX_PARTICLES
    for _ in range(120):
        fx.update(DT)
    assert fx.particles == [] and fx.shake == 0
