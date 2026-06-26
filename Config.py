


class Config:
    def __init__(self):
        # Valores por defecto
        self.current_set_index = 2  # Índice para set_options (1,3,5) → inicialmente 3 sets
        self.current_minute = 3  # Número de minutos
        self.current_level_index = 1  # Nivel COM: 0:"Fácil", 1:"Intermedio", 2:"Avanzado"
        self.current_position_index = 0  # Posición inicial: 0:"Fija", 1:"Aleatoria"
        self.current_ultimas_index = {
            "Fantasmas": 0,  # 0:"Sí", 1:"No"
            "Maldiciones": 0,
            "Bloques_final": 0
        }
        # Opciones fijas
        self.set_options = [1, 2, 3, 4, 5]
        self.position_options = ["Fija", "Aleatoria"]
        self.ultimas_opciones = ["Sí", "No"]

        # Configuración mapa
        self.selected_map = 1

    def reset(self):
        # Resetea todas las configuraciones a sus valores por defecto
        self.current_set_index = 2
        self.current_minute = 3
        self.current_level_index = 1
        self.current_position_index = 0
        self.current_ultimas_index = {
            "Fantasmas": 0,
            "Maldiciones": 0,
            "Bloques_final": 0
        }
        self.selected_map = 1
config = Config()



import pygame
import os

class Audio:
    def __init__(self):
        self.volume = 1.0
        self.slider_pos = (350, 150) # POSICIÓN DEL SLIDER MENU PAUSA
        self.slider_pos2 = (300, 97) # POSICIÓN DEL SLIDER MENU AJUSTES
        self.slider_size = (280, 10) # TAMAÑO DEL SLIDER MENU PAUSA
        self.slider_size2 = (280, 10) # TAMAÑO DEL SLIDER MENU AJUSTES
        self.slider_values = [1.0]

        self.efectos = {}
        self._cargar_efectos()

    def _cargar_efectos(self):
        pygame.mixer.init()
        carpeta_base = os.path.join("Media", "Sonidos_juego")
        if not os.path.exists(carpeta_base):
            print(f"[AUDIO] Carpeta no encontrada: {carpeta_base}")
            return

        for subdir, _, archivos in os.walk(carpeta_base):
            for archivo in archivos:
                if archivo.endswith((".wav", ".ogg")):
                    nombre_carpeta = os.path.basename(subdir)
                    nombre_archivo = os.path.splitext(archivo)[0]
                    clave = f"{nombre_carpeta}_{nombre_archivo}".lower()
                    ruta = os.path.join(subdir, archivo)
                    try:
                        sonido = pygame.mixer.Sound(ruta)
                        sonido.set_volume(self.volume)
                        self.efectos[clave] = sonido
                    except pygame.error as e:
                        print(f"[AUDIO] Error cargando {ruta}: {e}")

    def reproducir(self, nombre):
        if nombre in self.efectos:
            self.efectos[nombre].play()
        else:
            print(f"[AUDIO] Efecto no encontrado: {nombre}")

    def save(self):
        self.slider_values = [self.volume]

    def load(self):
        if len(self.slider_values) >= 1:
            self.volume = self.slider_values[0]
        else:
            self.volume = 1.0

audio = Audio()
audio.load()




# clase para guardar seleccion de personajes para cada uno de los jugadores

class Personajes:
    def __init__(self):
        self.seleccion = {
            "jugador_1": {"personaje": None},
            "jugador_2": {"personaje": None},
            "jugador_3": {"personaje": None},
            "jugador_4": {"personaje": None},
        }

    def reset(self):
        self.seleccion = {
            "jugador_1": {"personaje": None},
            "jugador_2": {"personaje": None},
            "jugador_3": {"personaje": None},
            "jugador_4": {"personaje": None},
        }

    def set_personaje(self, jugador_id, personaje_nombre):
        if jugador_id in self.seleccion:
            self.seleccion[jugador_id]["personaje"] = personaje_nombre

    def get_personaje(self, jugador_id):
        return self.seleccion.get(jugador_id, {}).get("personaje")

    def reset(self):
        for jugador in self.seleccion:
            self.seleccion[jugador]["personaje"] = None

# Instancia global de los personajes
personajes = Personajes()


# CONFIGURACIÓN COMPLETA
from ConfiguraciónMandos import gestor_jugadores




