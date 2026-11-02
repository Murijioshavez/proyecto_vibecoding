"""Capa Pygame: ventana, eventos de teclado y bucle principal."""
import pygame

from src import settings as cfg
from src.game import Game, InputState, State
from src.render import Renderer


def read_input(keys):
    """Convierte el estado del teclado de Pygame en un InputState."""
    return InputState(
        left=keys[pygame.K_LEFT] or keys[pygame.K_a],
        right=keys[pygame.K_RIGHT] or keys[pygame.K_d],
        up=keys[pygame.K_UP] or keys[pygame.K_w],
        down=keys[pygame.K_DOWN] or keys[pygame.K_s],
    )


def handle_key(game, key):
    """Gestiona las teclas que cambian de estado. Devuelve False para salir."""
    if game.state == State.MENU:
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            game.start()
        elif key == pygame.K_i:
            game.show_instructions()
        elif key == pygame.K_ESCAPE:
            return False
    elif game.state == State.INSTRUCTIONS:
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            game.start()
        elif key == pygame.K_ESCAPE:
            game.back_to_menu()
    elif game.state in (State.PLAYING, State.PAUSED):
        if key == pygame.K_p:
            game.toggle_pause()
        elif key == pygame.K_ESCAPE:
            game.back_to_menu()
    elif game.state in (State.GAME_OVER, State.VICTORY):
        if key in (pygame.K_r, pygame.K_RETURN):
            game.restart()
        elif key in (pygame.K_m, pygame.K_ESCAPE):
            game.back_to_menu()
    return True


def run():
    pygame.init()
    screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
    pygame.display.set_caption(cfg.TITLE)
    clock = pygame.time.Clock()
    game = Game()
    renderer = Renderer(screen)

    running = True
    while running:
        dt = clock.tick(cfg.FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                running = handle_key(game, event.key) and running
        game.update(dt, read_input(pygame.key.get_pressed()))
        renderer.draw(game, dt)
        pygame.display.flip()
    pygame.quit()
