import pygame
import sys
from PantallaPrincipal import actualizar_cursor_menu, iniciar_cursor_menu, registrar_actividad_cursor

def pantalla_guia(screen):
    """
    Muestra la pantalla de guía del juego y vuelve al menú de pausa al salir.
    """
    iniciar_cursor_menu()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 40)

    texto = font.render("Guía del juego", True, (255, 255, 255))
    texto_rect = texto.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))

    running = True
    while running:
        for event in pygame.event.get():
            registrar_actividad_cursor(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1:  # Botón B del mando
                    running = False

        # PINTAR FONDO GUARDADO (de la partida pausada)
        screen.fill((0, 0, 0))
        # PINTAR TEXTO
        screen.blit(texto, texto_rect)

        actualizar_cursor_menu()
        pygame.display.flip()
        clock.tick(60)

    return
