import pygame
import sys
from Config import config, personajes, audio
from ConfiguraciónMandos import gestor_jugadores
from PantallaPersonajes import reiniciar_estado_personajes

def reiniciar_estado():
    print("[ESTADO] Reiniciando estado de la partida...")

    # La configuración de partida se conserva al volver al menú.
    #config.reset()

    # Limpia la selección de personajes.
    personajes.reset()
    print("[ESTADO] Selección de personajes reseteada.")

    # Reinicia jugadores y dispositivos registrados.
    gestor_jugadores.reset()
    print("[ESTADO] Gestor de jugadores reseteado.")

    reiniciar_estado_personajes()


    # Restaura la música del menú.
    pygame.mixer.music.stop()
    try:
        pygame.mixer.music.load("Media/Sonidos_juego/musica_fondo/menu.mp3")
        pygame.mixer.music.set_volume(audio.volume)
        pygame.mixer.music.play(-1)
        print("[ESTADO] Música del menú iniciada.")
    except Exception as e:
        print(f"[ESTADO] Error al cargar o reproducir música del menú: {e}")

    print("[ESTADO] Todos los datos han sido reseteados.")
    return None