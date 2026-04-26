import pygame
import sys

from PantallaPrincipal import background_screen
from PantallaPrincipal import BackgroundAnimation
from PantallaPrincipal import crear_pantalla_completa
from PantallaConfigPartida import pantalla2_main
from PantallaMapas import pantalla_mapas
from PantallaAudio import pantalla_audio
from PantallaPersonajes import pantalla_personajes
from AprendeControles import pantalla_controles
def main():
    pygame.init()

    # Inicializa el mezclador de audio antes de cargar música o efectos.
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    # Música del menú en bucle.
    pygame.mixer.music.load("Media/Sonidos_juego/musica_fondo/menu.mp3")
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play(-1)

    screen = crear_pantalla_completa()
    screen_width, screen_height = screen.get_size()
    pygame.display.set_caption("KaBoom")

    # Fondo animado compartido entre pantallas de menú.
    bg_anim = BackgroundAnimation(screen_width, screen_height)

    # Flujo principal de pantallas antes de iniciar la partida.
    if not background_screen(screen):
        return
    if not pantalla2_main(screen, bg_anim):
        return
    if not pantalla_mapas(screen, bg_anim):
        return
    if not pantalla_audio(screen, bg_anim, pygame.mixer):
        return
    if not pantalla_controles(screen, bg_anim):
        return
    if not pantalla_personajes(screen, bg_anim):
        return
    from KaBoom import iniciar_partida
    iniciar_partida(screen)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
