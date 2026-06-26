import pygame
import os
import sys
import math
import random
import time
import PIL.Image as PILImage
from Config import config, audio
from ConfiguraciónMandos import gestor_jugadores
from PausaPartida import menu_pausa
from itertools import combinations
from PantallaPrincipal import crear_pantalla_completa, evento_ventana_inactiva, ocultar_cursor_partida


# ------------------------------------------------------------------------------------
# Inicialización y configuración de pantalla
# ------------------------------------------------------------------------------------
pygame.init()
pygame.mixer.init()

# Inicialización de mandos
pygame.joystick.init()


def get_joystick_by_instance_id(instance_id: int):
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        if joy.get_instance_id() == instance_id:
            return joy
    return None  # si se ha desconectado


BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "Media")

TOP_OFFSET = 80  # Espacio para el contador y el HUD
BOTTOM_OFFSET = 20
TILE_SIZE = 40
GRID_COLS = 21
GRID_ROWS = 17

# Dimensiones lógicas del tablero y de las zonas laterales de HUD.
SCOREBOARD_AREA_WIDTH = 250  # Ancho del área en cada lado para los marcadores.
GRID_WIDTH = GRID_COLS * TILE_SIZE  # Ancho de la cuadrícula del juego.
WIDTH = GRID_WIDTH + 2 * SCOREBOARD_AREA_WIDTH  # Ancho total de la ventana.
HEIGHT = GRID_ROWS * TILE_SIZE + TOP_OFFSET + BOTTOM_OFFSET

CURSES = {
    "reset": {"duration": None, "shows_in_hud": False, "clears_previous": False, "transmittable": False,
              "set_effect": lambda p, c: p._do_reset(),
              "clear_effect": lambda p, c: None},
    "no_ability": {"duration": 40.0, "shows_in_hud": True, "clears_previous": True, "transmittable": True,
                   "set_effect": lambda p, c: p._set_curse_effects(c),
                   "clear_effect": lambda p, c: p._clear_curse_effects(c)},
    "no_bomb": {"duration": 40.0, "shows_in_hud": True, "clears_previous": True, "transmittable": True,
                "set_effect": lambda p, c: p._set_curse_effects(c),
                "clear_effect": lambda p, c: p._clear_curse_effects(c)},
    "auto_bomb": {"duration": 40.0, "shows_in_hud": True, "clears_previous": True, "transmittable": True,
                  "set_effect": lambda p, c: p._set_curse_effects(c),
                  "clear_effect": lambda p, c: p._clear_curse_effects(c)},
    "inverted": {"duration": 40.0, "shows_in_hud": True, "clears_previous": True, "transmittable": True,
                 "set_effect": lambda p, c: p._set_curse_effects(c),
                 "clear_effect": lambda p, c: p._clear_curse_effects(c)},
    "hyper_speed": {"duration": 40.0, "shows_in_hud": True, "clears_previous": True, "transmittable": True,
                    "set_effect": lambda p, c: p._set_curse_effects(c),
                    "clear_effect": lambda p, c: p._clear_curse_effects(c)},
    "slow_speed": {"duration": 40.0, "shows_in_hud": True, "clears_previous": True, "transmittable": True,
                   "set_effect": lambda p, c: p._set_curse_effects(c),
                   "clear_effect": lambda p, c: p._clear_curse_effects(c)},
}

pygame.display.set_caption("KaBoom")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
font = pygame.font.SysFont("Arial", 20)
ability_font = pygame.font.SysFont("Eras Bold ITC", 22, bold=True)
EXPLOSION_DURATION = 0.75
PUSH_SPEED = 3

exploding_blocks = {}


def presentar_superficie_escalada(screen, logical_surface):
    if logical_surface.get_size() == screen.get_size():
        screen.blit(logical_surface, (0, 0))
    else:
        frame = pygame.transform.smoothscale(logical_surface, screen.get_size())
        screen.blit(frame, (0, 0))


# ------------------------------------------------------------------------------------
# Función para cargar imágenes
# ------------------------------------------------------------------------------------
def load_image(file, size, folder=ASSETS_DIR):
    return pygame.transform.scale(
        pygame.image.load(os.path.join(folder, file)).convert_alpha(),
        size
    )
def to_grayscale(surface):
    """Convierte una superficie de Pygame a escala de grises y la hace semitransparente."""
    # Creamos una copia para no modificar la imagen original
    grayscale_surface = surface.copy()
    # Usamos el modo de fusión BLEND_RGB_MULT para un efecto de escala de grises eficiente
    grayscale_surface.fill((120, 120, 120), special_flags=pygame.BLEND_RGB_MULT)
    # Hacemos que la imagen sea un poco transparente para dar un mejor efecto de "apagado"
    grayscale_surface.set_alpha(160)
    return grayscale_surface

def cargar_mapa():  # FUNCION CARGAR MAPA SEGUN SELECCION
    nombre_mapa = config.selected_map
    mapa_path = os.path.join(ASSETS_DIR, "Mapas", "Mapa" + str(nombre_mapa))
    SUELO1 = load_image("suelo1.png", (TILE_SIZE, TILE_SIZE), folder=mapa_path)
    SUELO2 = load_image("suelo2.png", (TILE_SIZE, TILE_SIZE), folder=mapa_path)
    STONE = load_image("muro_irrompible.png", (TILE_SIZE, TILE_SIZE), folder=mapa_path)
    BRICK = load_image("muro_rompible.png", (TILE_SIZE, TILE_SIZE), folder=mapa_path)
    LIMIT_IMG = load_image("limite_mapa.png", (TILE_SIZE, TILE_SIZE), folder=mapa_path)

    return SUELO1, SUELO2, STONE, BRICK, LIMIT_IMG


# Habilidades
SPEED_IMG = load_image("mas_velocidad.png", (40, 40), folder=os.path.join(ASSETS_DIR, "Gadgets", "Habilidades"))
MORE_BOMB_IMG = load_image("mas_bombas.png", (40, 40), folder=os.path.join(ASSETS_DIR, "Gadgets", "Habilidades"))
MAYOR_EXPLOSION_IMG = load_image("mayor_explosion.png", (40, 40),
                                 folder=os.path.join(ASSETS_DIR, "Gadgets", "Habilidades"))

# Poderes
PUSH_BOMB_IMG = load_image("patada.png", (40, 40), folder=os.path.join(ASSETS_DIR, "Gadgets", "Poderes"))
PUÑO_IMG = load_image("puño.png", (40, 40), folder=os.path.join(ASSETS_DIR, "Gadgets", "Poderes"))
ESCUDO_IMG = load_image("escudo.png", (40, 40), folder=os.path.join(ASSETS_DIR, "Gadgets", "Poderes"))

# Maldiciones
CALAVERA_IMG = load_image("calavera.png", (40, 40), folder=os.path.join(ASSETS_DIR, "Gadgets", "Maldiciones"))

# Lapidas
LAPIDA_IMG = load_image("lapida.png", (TILE_SIZE, TILE_SIZE), folder=os.path.join(ASSETS_DIR, "Mapas"))

try:
    mapa_path_general = os.path.join(ASSETS_DIR, "Mapas")
    BLOQUE_FINAL_IMG = load_image("Bloque_final.png", (TILE_SIZE, TILE_SIZE), folder=mapa_path_general)
except pygame.error:
    print(f"ADVERTENCIA: No se pudo cargar 'Bloque_final.png'. Se usará una imagen por defecto.")
    BLOQUE_FINAL_IMG = pygame.Surface((TILE_SIZE, TILE_SIZE))
    BLOQUE_FINAL_IMG.fill((20, 20, 30))

# Creamos una imagen para la marca de advertencia en el suelo
BLOQUE_FINAL_MARCA_IMG = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
pygame.draw.rect(BLOQUE_FINAL_MARCA_IMG, (255, 0, 0, 100), (0, 0, TILE_SIZE, TILE_SIZE),
                 3)  # Borde rojo semitransparente

# --- CARGAMOS LAS IMÁGENES DE OVERLAY PARA MARCADORES ---
try:
    marcadores_folder = os.path.join(ASSETS_DIR, "Marcadores")
    MARCADOR_ESCUDO_IMG = pygame.image.load(os.path.join(marcadores_folder, "escudo.png")).convert_alpha()
    MARCADOR_XUT_IMG = pygame.image.load(os.path.join(marcadores_folder, "xut.png")).convert_alpha()
    MARCADOR_PUÑO_IMG = pygame.image.load(os.path.join(marcadores_folder, "puño.png")).convert_alpha()
    MARCADOR_ERROR_IMG = pygame.image.load(os.path.join(marcadores_folder, "error.png")).convert_alpha()
except pygame.error as e:
    print(f"ADVERTENCIA: No se pudieron cargar las imágenes de overlay de marcadores: {e}")
    # Si fallan, creamos variables vacías para que el juego no se rompa
    MARCADOR_ESCUDO_IMG = None
    MARCADOR_XUT_IMG = None
    MARCADOR_PUÑO_IMG = None
    MARCADOR_ERROR_IMG = None


def load_mark_scaled(path):
    full_path = os.path.join(ASSETS_DIR, "Jugadores", "Marca", path)
    img = pygame.image.load(full_path).convert_alpha()
    scale_factor = 0.03  # ajusta este factor según lo pequeño que lo quieras
    new_width = int(img.get_width() * scale_factor)
    new_height = int(img.get_height() * scale_factor)
    return pygame.transform.smoothscale(img, (new_width, new_height))


PLAYER_MARKS = [
    load_mark_scaled("Jugador 1.png"),
    load_mark_scaled("Jugador 2.png"),
    load_mark_scaled("Jugador 3.png"),
    load_mark_scaled("Jugador 4.png")
]

# Sonidos
SOUND_BOMB_PATH = os.path.join(ASSETS_DIR, "Sonidos_juego", "bomba", "explotar_bomba.wav")
EXPLOSION_SOUND = pygame.mixer.Sound(SOUND_BOMB_PATH)
EXPLOSION_SOUND.set_volume(0.35)

COLOCAR_BOMBA_SOUND_PATH = os.path.join(ASSETS_DIR, "Sonidos_juego", "bomba", "colocar_bomba.wav")
COLOCAR_BOMBA_SOUND = pygame.mixer.Sound(COLOCAR_BOMBA_SOUND_PATH)
COLOCAR_BOMBA_SOUND.set_volume(0.35)

FOOTSTEP_SOUND_PATH = os.path.join(ASSETS_DIR, "Sonidos_juego", "movimiento", "pisadas_jugador.wav")
FOOTSTEP_SOUND = pygame.mixer.Sound(FOOTSTEP_SOUND_PATH)
FOOTSTEP_SOUND.set_volume(1)

COGER_HABILIDAD_SOUND_PATH = os.path.join(ASSETS_DIR, "Sonidos_juego", "habilidades", "coger_habilidad.wav")
COGER_HABILIDAD_SOUND = pygame.mixer.Sound(COGER_HABILIDAD_SOUND_PATH)
COGER_HABILIDAD_SOUND.set_volume(0.35)

COGER_MALDICION_SOUND = pygame.mixer.Sound(
    os.path.join(ASSETS_DIR, "Sonidos_juego", "habilidades", "coger_maldicion.mp3"))
COGER_MALDICION_SOUND.set_volume(0.35)

MUERTE_SOUND_PATH = os.path.join(ASSETS_DIR, "Sonidos_juego", "Personajes", "muerte.mp3")
MUERTE_SOUND = pygame.mixer.Sound(MUERTE_SOUND_PATH)
MUERTE_SOUND.set_volume(0.4)

REAPARICION_SOUND_PATH = os.path.join(ASSETS_DIR, "Sonidos_juego", "Personajes", "reaparicion.mp3")
REAPARICION_SOUND = pygame.mixer.Sound(REAPARICION_SOUND_PATH)
REAPARICION_SOUND.set_volume(0.4)

FANTASMA_SOUND_PATH = os.path.join(ASSETS_DIR, "Sonidos_juego", "movimiento", "fantasma.mp3")
FANTASMA_SOUND = pygame.mixer.Sound(FANTASMA_SOUND_PATH)
FANTASMA_SOUND.set_volume(0.7)
try:
    BLOQUE_FINAL_SOUND_PATH = os.path.join(ASSETS_DIR, "Sonidos_juego", "Partida", "bloque final.mp3")
    BLOQUE_FINAL_SOUND = pygame.mixer.Sound(BLOQUE_FINAL_SOUND_PATH)
    BLOQUE_FINAL_SOUND.set_volume(0.5)  # Puedes ajustar este volumen (0.0 a 1.0)
except pygame.error as e:
    print(f"ADVERTENCIA: No se pudo cargar el sonido 'bloque final.mp3': {e}")
    BLOQUE_FINAL_SOUND = None  # Si no se encuentra el audio, el juego no se romperá


# ------------------------------------------------------------------------------------
# Clase para gestionar el fondo animado (GIF)
# ------------------------------------------------------------------------------------
class AnimatedBackground:
    def __init__(self, gif_path, size):
        self.frames = []
        self.frame_duration = 100  # Duración por defecto si el GIF no la especifica
        self.last_update = pygame.time.get_ticks()
        self.frame_index = 0

        try:
            # Usamos la librería PIL (Pillow) para abrir el GIF
            pil_image = PILImage.open(gif_path)
            # Obtenemos la duración de cada fotograma desde el propio GIF
            self.frame_duration = pil_image.info.get('duration', 100)

            # Recorremos cada fotograma del GIF
            for i in range(pil_image.n_frames):
                pil_image.seek(i)
                frame = pil_image.convert("RGBA")
                pygame_frame = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)

                # Escalamos el fotograma al tamaño completo de la pantalla y lo optimizamos
                scaled_frame = pygame.transform.scale(pygame_frame, size).convert_alpha()
                self.frames.append(scaled_frame)

        except (FileNotFoundError, pygame.error) as e:
            # Si el GIF no se encuentra, creamos un fondo negro para que el juego no falle
            print(f"ADVERTENCIA: No se pudo cargar el fondo animado '{gif_path}': {e}")
            fallback_surface = pygame.Surface(size)
            fallback_surface.fill(BLACK)
            self.frames.append(fallback_surface)

    def update(self):
        # Avanza al siguiente fotograma si ha pasado el tiempo suficiente
        if len(self.frames) > 1 and pygame.time.get_ticks() - self.last_update > self.frame_duration:
            self.last_update = pygame.time.get_ticks()
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self, surface):
        # Dibuja el fotograma actual en la pantalla
        if self.frames:
            surface.blit(self.frames[self.frame_index], (0, 0))


modo_posicion = config.current_position_index

posiciones_iniciales = [
    (1, 1),
    (GRID_COLS - 2, GRID_ROWS - 2),
    (1, GRID_ROWS - 2),
    (GRID_COLS - 2, 1),
]

# Controles por defecto para teclado
controles_teclado = {
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "bomb": pygame.K_RETURN,
    "hit": pygame.K_p,
}

# Animaciones de explosión de la bomba
CENTER_EXPLOSION_FRAMES = []
for i in range(1, 18):
    nombre = f"bomba_c{i}.png"
    img = load_image(nombre, (40, 40), folder=os.path.join(ASSETS_DIR, "Bombas"))
    CENTER_EXPLOSION_FRAMES.append({"image": img, "name": nombre})

EXTREME_EXPLOSION_FRAMES = []
for i in range(1, 18):
    nombre = f"ex_e{i}.png"
    img = load_image(nombre, (40, 40), folder=os.path.join(ASSETS_DIR, "Bombas"))
    EXTREME_EXPLOSION_FRAMES.append({"image": img, "name": nombre})

LATERAL_EXPLOSION_FRAMES = []
for i in range(1, 18):
    nombre = f"ex_l{i}.png"
    img = load_image(nombre, (40, 40), folder=os.path.join(ASSETS_DIR, "Bombas"))
    LATERAL_EXPLOSION_FRAMES.append({"image": img, "name": nombre})

ABILITY_EXPLOSION_FRAMES = [load_image("habilidad_ex" + str(i) + ".png", (40, 40),
                                       folder=os.path.join(ASSETS_DIR, "Gadgets", "Explosion_gadget"))
                            for i in range(1, 18)]

POWERUP_DESTROY_FRAMES = [pygame.Surface((40, 40)), pygame.Surface((40, 40))]
POWERUP_DESTROY_FRAMES[0].fill((255, 200, 0))
POWERUP_DESTROY_FRAMES[1].fill((255, 100, 0))

BOMB_IMAGES = []
bomb_folder = os.path.join(ASSETS_DIR, "Bombas")
for i in range(1, 16):
    img = load_image("bomb" + str(i) + ".png", (40, 40), folder=bomb_folder)
    BOMB_IMAGES.append(img)

POWERUP_DESTROY_FRAMES = [pygame.Surface((40, 40)), pygame.Surface((40, 40))]
POWERUP_DESTROY_FRAMES[0].fill((255, 200, 0))
POWERUP_DESTROY_FRAMES[1].fill((255, 100, 0))


# ------------------------------------------------------------------------------------
# Funciones auxiliares
# ------------------------------------------------------------------------------------
def tile_blocked_for_player(grid, bombs, tile_x, tile_y, player):
    if tile_x < 0 or tile_x >= GRID_COLS or tile_y < 0 or tile_y >= GRID_ROWS:
        return True

    # Comprobar si el jugador es un fantasma
    if player.is_ghost:
        # Un fantasma solo es bloqueado por muros irrompibles (2) y límites (3)
        if grid[tile_y][tile_x] in (2, 3, 4):
            return True
        # Los fantasmas ignoran bloques rompibles (1) y bombas, así que no hacemos más comprobaciones
        return False
    else:
        # Lógica original para jugadores vivos
        if grid[tile_y][tile_x] in (1, 2, 3, 4):
            return True
        for b in bombs:
            if b.tile_x == tile_x and b.tile_y == tile_y:
                if player in b.passable_players:
                    return False
                else:
                    return True
        return False


def registrar_jugadores_pasables_en_bomba(bomba, jugadores):
    bomb_rect = pygame.Rect(bomba.pos_x, bomba.pos_y, TILE_SIZE, TILE_SIZE)
    for jugador in jugadores:
        if getattr(jugador, "is_eliminated", False):
            continue
        try:
            if jugador.get_hitbox().colliderect(bomb_rect):
                bomba.passable_players.add(jugador)
        except Exception:
            continue


def generar_poderes_al_morir(grid, bombs, powerups, players):

    tipos_poderes = ["speed", "more_bomb", "major_explosion", "push_bomb", "golpear_bombas"]
    cantidad = random.randint(2, 5)
    celdas_validas = []

    for y in range(1, GRID_ROWS - 1):
        for x in range(1, GRID_COLS - 1):
            if grid[y][x] != 0:
                continue
            if any(b.tile_x == x and b.tile_y == y for b in bombs):
                continue
            if any(p.x == x and p.y == y and p.visible for p in powerups):
                continue
            if any(
                    pygame.Rect(jugador.x, jugador.y, jugador.hitbox_size, jugador.hitbox_size).colliderect(
                        pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    ) for jugador in players
            ):
                continue
            # Casilla válida
            celdas_validas.append((x, y))

    random.shuffle(celdas_validas)
    for i in range(min(cantidad, len(celdas_validas))):
        x, y = celdas_validas[i]
        tipo = random.choice(tipos_poderes)
        nuevo_poder = PowerUp(x, y, tipo)
        nuevo_poder.visible = True
        nuevo_poder.start_spawn_animation()
        powerups.append(nuevo_poder)


def reveal_powerup_if_any(powerups, x, y):
    for p in powerups:
        if p.x == x and p.y == y and not p.visible:
            p.visible = True


def get_available_free_cells(grid, powerups):
    cells = []
    for y in range(1, GRID_ROWS - 1):
        for x in range(1, GRID_COLS - 1):
            if grid[y][x] == 0:
                if not any(p.x == x and p.y == y and p.visible for p in powerups):
                    cells.append((x, y))
    return cells


def get_free_cells(grid):
    cells = []
    for y in range(1, GRID_ROWS - 1):
        for x in range(1, GRID_COLS - 1):
            if grid[y][x] == 0:
                cells.append((x, y))
    return cells


def find_free_cell_far_from(player, grid):
    player_tile = player.get_center_tile()
    free_cells = get_free_cells(grid)
    if free_cells:
        far_cell = max(free_cells, key=lambda cell: math.hypot(cell[0] - player_tile[0], cell[1] - player_tile[1]))
        return far_cell
    return player_tile


def update_powerups(powerups, dt):
    to_remove = []
    for p in powerups:
        p.update(dt)
        if p.is_destroyed():
            to_remove.append(p)
    for r in to_remove:
        powerups.remove(r)


def draw_powerups(surface, powerups):
    # Dibujamos los powerups (maldiciones) después de las explosiones para que se vean por encima
    for p in powerups:
        p.draw(surface)

# ------------------------------------------------------------------------------------
# Temporizador
# ------------------------------------------------------------------------------------
def load_timer_images():
    DIGIT_SIZE = (40, 60)
    SEPARADOR_SIZE = (20, 60)
    MARCO_SIZE = (200, 80)
    contador_dir = os.path.join(ASSETS_DIR, "Contador")
    timer_digits = {}
    for i in range(10):
        timer_digits[str(i)] = load_image(f"{i}.png", DIGIT_SIZE, folder=contador_dir)
    timer_separador = load_image("separador.png", SEPARADOR_SIZE, folder=contador_dir)
    timer_marco = load_image("marco_contador.png", MARCO_SIZE, folder=contador_dir)
    return timer_digits, timer_separador, timer_marco, DIGIT_SIZE, SEPARADOR_SIZE, MARCO_SIZE


timer_digits, timer_separador, timer_marco, DIGIT_SIZE, SEPARADOR_SIZE, MARCO_SIZE = load_timer_images()


def draw_timer(surface, remaining_time):
    remaining = int(remaining_time)
    minutes = remaining // 60
    seconds = remaining % 60
    time_str = f"{minutes:02d}{seconds:02d}"
    timer_width = 4 * DIGIT_SIZE[0] + SEPARADOR_SIZE[0]
    marco_width = MARCO_SIZE[0]
    marco_x = (GRID_WIDTH - marco_width) // 2
    marco_y = 10
    surface.blit(timer_marco, (marco_x, marco_y))
    timer_x = marco_x + (marco_width - timer_width) // 2
    timer_y = marco_y + (MARCO_SIZE[1] - DIGIT_SIZE[1]) // 2
    surface.blit(timer_digits[time_str[0]], (timer_x, timer_y))
    surface.blit(timer_digits[time_str[1]], (timer_x + DIGIT_SIZE[0], timer_y))
    surface.blit(timer_separador, (timer_x + 2 * DIGIT_SIZE[0], timer_y))
    surface.blit(timer_digits[time_str[2]], (timer_x + 2 * DIGIT_SIZE[0] + SEPARADOR_SIZE[0], timer_y))
    surface.blit(timer_digits[time_str[3]], (timer_x + 3 * DIGIT_SIZE[0] + SEPARADOR_SIZE[0], timer_y))


# ------------------------------------------------------------------------------------
# Marcadores laterales de sets ganados
# ------------------------------------------------------------------------------------
def draw_scoreboards(surface, players, scoreboard_images, set_positions, total_width, total_height):
    if not scoreboard_images:
        return

    sample_img = None
    for p_idx in scoreboard_images:
        if scoreboard_images[p_idx]:
            sample_img = next(iter(scoreboard_images[p_idx].values()))
            break
    if not sample_img: return

    w, h = sample_img.get_size()
    SCOREBOARD_IMG_WIDTH = 230
    SCOREBOARD_IMG_SIZE = (SCOREBOARD_IMG_WIDTH, int(SCOREBOARD_IMG_WIDTH * h / w))

    margin = 15
    vertical_offset = - 80
    pos_tl = (margin, TOP_OFFSET + vertical_offset)
    pos_tr = (total_width - SCOREBOARD_IMG_SIZE[0] - margin, TOP_OFFSET + vertical_offset)
    pos_bl = (margin, total_height - SCOREBOARD_IMG_SIZE[1] - margin)
    pos_br = (total_width - SCOREBOARD_IMG_SIZE[0] - margin, total_height - SCOREBOARD_IMG_SIZE[1] - margin)

    spawn_tl = (1, 1)
    spawn_br = (GRID_COLS - 2, GRID_ROWS - 2)
    spawn_bl = (1, GRID_ROWS - 2)
    spawn_tr = (GRID_COLS - 2, 1)

    for player in players:
        if player.player_index < len(set_positions):
            player_start_pos = set_positions[player.player_index]
            target_pos = None

            if player_start_pos == spawn_tl:
                target_pos = pos_tl
            elif player_start_pos == spawn_br:
                target_pos = pos_br
            elif player_start_pos == spawn_bl:
                target_pos = pos_bl
            elif player_start_pos == spawn_tr:
                target_pos = pos_tr

            if target_pos:
                marcador_sets_rect = pygame.Rect(target_pos, SCOREBOARD_IMG_SIZE)

                # --- INICIO DE LA LÓGICA DE BLANCO Y NEGRO ---
                is_eliminated = player.is_eliminated or player.is_ghost

                # Cargar la imagen base del marcador
                base_marcador_img = None
                if player.player_index in scoreboard_images and player.sets_won in scoreboard_images[
                    player.player_index]:
                    base_marcador_img = pygame.transform.scale(scoreboard_images[player.player_index][player.sets_won],
                                                               SCOREBOARD_IMG_SIZE)

                # Cargar el retrato del jugador
                portrait_img = None
                if hasattr(player, 'portrait_image') and player.portrait_image:
                    portrait_img = player.portrait_image

                # Convertir a escala de grises si el jugador está eliminado
                if is_eliminated:
                    if base_marcador_img: base_marcador_img = to_grayscale(base_marcador_img)
                    if portrait_img: portrait_img = to_grayscale(portrait_img)
                    text_color = (150, 150, 150)  # Color de texto gris
                else:
                    text_color = (255, 255, 255)  # Color de texto blanco

                # Dibujar los elementos base
                if base_marcador_img:
                    surface.blit(base_marcador_img, target_pos)
                if portrait_img:
                    portrait_rect = portrait_img.get_rect(centerx=marcador_sets_rect.centerx,
                                                          centery=marcador_sets_rect.centery - 50)
                    surface.blit(portrait_img, portrait_rect)

                # Dibujar las capas de poderes (se convierten a grises si es necesario)
                if not player.active_curse:
                    if player.escudo_available and MARCADOR_ESCUDO_IMG:
                        img_to_draw = to_grayscale(MARCADOR_ESCUDO_IMG) if is_eliminated else MARCADOR_ESCUDO_IMG
                        surface.blit(pygame.transform.scale(img_to_draw, SCOREBOARD_IMG_SIZE), target_pos)
                    if player.push_bomb_available and MARCADOR_XUT_IMG:
                        img_to_draw = to_grayscale(MARCADOR_XUT_IMG) if is_eliminated else MARCADOR_XUT_IMG
                        surface.blit(pygame.transform.scale(img_to_draw, SCOREBOARD_IMG_SIZE), target_pos)
                    if player.hit_bomb_available and MARCADOR_PUÑO_IMG:
                        img_to_draw = to_grayscale(MARCADOR_PUÑO_IMG) if is_eliminated else MARCADOR_PUÑO_IMG
                        surface.blit(pygame.transform.scale(img_to_draw, SCOREBOARD_IMG_SIZE), target_pos)

                # Dibujar los textos de habilidades con el color correspondiente
                bomb_text = ability_font.render(f"x{player.bomb_limit}", True, text_color)
                range_text = ability_font.render(f"x{player.bomb_range}", True, text_color)
                speed_text = ability_font.render(f"x{player.display_speed}", True, text_color)
                y_pos = marcador_sets_rect.bottom - 85
                surface.blit(bomb_text, bomb_text.get_rect(midtop=(marcador_sets_rect.left + 70, y_pos)))
                surface.blit(range_text, range_text.get_rect(midtop=(marcador_sets_rect.centerx + 18, y_pos)))
                surface.blit(speed_text, speed_text.get_rect(midtop=(marcador_sets_rect.right - 35, y_pos)))

                # Dibujar la imagen de la maldición AL FINAL
                if player.active_curse and MARCADOR_ERROR_IMG:
                    img_to_draw = to_grayscale(MARCADOR_ERROR_IMG) if is_eliminated else MARCADOR_ERROR_IMG
                    surface.blit(pygame.transform.scale(img_to_draw, SCOREBOARD_IMG_SIZE), target_pos)


# ------------------------------------------------------------------------------------
# Clase PowerUp (maldición que rebota de 1 en 1)
# ------------------------------------------------------------------------------------
class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type
        self.completed = False
        self.visible = False
        self.block_explosion = True
        self.disappearing = False
        self.destroy_frames = POWERUP_DESTROY_FRAMES
        self.destroy_frame_index = 0
        self.destroy_frame_time = 100
        self.last_update = pygame.time.get_ticks()
        self.vanished = False
        self.spawn_timer = 0.0
        self.spawning = True
        # atributos para rebote:
        self.bouncing = False
        self.bounce_dir = (0, 0)
        self.bounce_path = []  # lista de tiles [(x1,y1), (x2,y2), …]
        self.bounce_index = 0  # casilla actual en path
        self.bounce_timer = 0.0  # acumulador de tiempo
        self.bounce_cell_time = 0.15  # segundos que dura botar de una celda a la siguiente

    def start_spawn_animation(self):
        self.spawning = True
        self.spawn_timer = 0.0

    def update(self, dt):
        # Lógica de animación de spawn (si self.spawning está activo)
        if self.spawning:
            self.spawn_timer += dt
            if self.spawn_timer >= 0.5:  # media segundo de animación
                self.spawning = False

    def update(self, dt):
        if self.disappearing:
            now = pygame.time.get_ticks()
            if now - self.last_update > self.destroy_frame_time:
                self.destroy_frame_index += 1
                self.last_update = now

        if self.vanished:
            self.disappearing = True
            self.destroy_frame_index = len(self.destroy_frames)

        if self.bouncing:
            self.bounce_timer += dt

            # Solo avanzar si hay otra celda a la que moverse
            if self.bounce_index + 1 < len(self.bounce_path):
                if self.bounce_timer >= self.bounce_cell_time:
                    self.bounce_timer -= self.bounce_cell_time
                    self.bounce_index += 1

                    if self.bounce_index >= len(self.bounce_path):
                        fx, fy = self.bounce_path[-1]
                        self.x, self.y = fx, fy
                        self.bouncing = False
                    else:
                        self.x, self.y = self.bounce_path[self.bounce_index]
            else:
                # Si ya no hay siguiente, terminamos la animación
                fx, fy = self.bounce_path[-1]
                self.x, self.y = fx, fy
                self.bouncing = False

    def draw(self, surface):
        if not self.visible or self.vanished:
            return

        if self.bouncing and len(self.bounce_path) >= 2:
            ability_size = int(TILE_SIZE * 0.8)

            # Usamos el índice actual y forzamos siempre la animación del tramo activo
            idx = self.bounce_index
            x1, y1 = self.bounce_path[idx]
            x2, y2 = self.bounce_path[min(idx + 1, len(self.bounce_path) - 1)]

            px1 = x1 * TILE_SIZE + TILE_SIZE // 2
            py1 = y1 * TILE_SIZE + TILE_SIZE // 2 + TOP_OFFSET
            px2 = x2 * TILE_SIZE + TILE_SIZE // 2
            py2 = y2 * TILE_SIZE + TILE_SIZE // 2 + TOP_OFFSET

            # t controla el progreso dentro del tramo, garantiza curva desde el principio
            t = max(0.0, min(self.bounce_timer / self.bounce_cell_time, 1.0))

            dx_px = px2 - px1
            dy_px = py2 - py1

            map_w = GRID_WIDTH
            map_h = HEIGHT - TOP_OFFSET
            half_w = map_w // 2
            half_h = map_h // 2

            if abs(dx_px) > half_w:
                dx_px -= map_w * (1 if dx_px > 0 else -1)
            if abs(dy_px) > half_h:
                dy_px -= map_h * (1 if dy_px > 0 else -1)

            interp_x = px1 + dx_px * t
            interp_y = py1 + dy_px * t

            # Esta es la parábola para el efecto de bote, ahora visible desde el primer salto
            arc = -TILE_SIZE * 0.45 * math.sin(math.pi * t)
            interp_y += arc

            if self.teleporting:
                if abs(px2 - px1) > half_w:
                    interp_x += WIDTH if px2 > px1 else -WIDTH
                if abs(py2 - py1) > half_h:
                    interp_y += HEIGHT if py2 > py1 else -HEIGHT

            img = pygame.transform.scale(CALAVERA_IMG, (ability_size, ability_size))
            surface.blit(img, (interp_x - ability_size // 2, interp_y - ability_size // 2))
            return

        # Dibujo estático/flotante
        ability_size = int(TILE_SIZE * 0.8)
        amplitude = 3.0
        freq = 0.4
        offset_y = amplitude * math.sin(2 * math.pi * freq * time.time())
        center_x = self.x * TILE_SIZE + TILE_SIZE // 2
        center_y = self.y * TILE_SIZE + TILE_SIZE // 2 + TOP_OFFSET + int(offset_y)
        top_left_x = center_x - ability_size // 2
        top_left_y = center_y - ability_size // 2

        if self.type == "major_explosion":
            img = MAYOR_EXPLOSION_IMG
        elif self.type == "speed":
            img = SPEED_IMG
        elif self.type == "more_bomb":
            img = MORE_BOMB_IMG
        elif self.type == "calavera":
            img = CALAVERA_IMG
        elif self.type == "push_bomb":
            img = PUSH_BOMB_IMG
        elif self.type == "golpear_bombas":
            img = PUÑO_IMG
        elif self.type == "escudo":
            img = ESCUDO_IMG
        elif self.type == "reset":
            img = CALAVERA_IMG
        elif self.type in CURSES:
            img = CALAVERA_IMG
        else:
            if self.destroy_frame_index < len(self.destroy_frames):
                img = self.destroy_frames[self.destroy_frame_index]
            else:
                img = CALAVERA_IMG

        scaled_img = pygame.transform.scale(img, (ability_size, ability_size))
        surface.blit(scaled_img, (top_left_x, top_left_y))

    def start_disappear(self):
        self.disappearing = True
        self.destroy_frame_index = 0
        self.last_update = pygame.time.get_ticks()

    def is_destroyed(self):
        if self.vanished:
            return True
        return (self.disappearing and (self.destroy_frame_index >= len(self.destroy_frames)))

    def calculate_bounce_path(self, direction, grid, bombs, powerups):
        """
        direction: (dx,dy) de la explosión.
        Devuelve la secuencia de celdas destino hasta encontrar una libre.
        Con wrap-around en bordes.
        """
        dx, dy = direction
        path = []
        cx, cy = self.x, self.y

        # avanzamos 1 en 1 hasta encontrar un destino válido
        while True:
            nx = (cx + dx) % GRID_COLS
            ny = (cy + dy) % GRID_ROWS
            if (dx == 1 and nx == 0) or (dx == -1 and nx == GRID_COLS - 1):
                self.teleporting = True
            elif (dy == 1 and ny == 0) or (dy == -1 and ny == GRID_ROWS - 1):
                self.teleporting = True
            else:
                self.teleporting = False
            # ¿casilla libre para terminar?
            libre = (grid[ny][nx] == 0 and
                     not any(p.x == nx and p.y == ny and p.visible and p.type in CURSES for p in powerups))
            path.append((nx, ny))

            if libre:
                break

            # sino, saltamos a la siguiente
            cx, cy = nx, ny

        return path

    def start_bounce(self, direction, grid, bombs, powerups):
        # Construye la ruta incluyendo la posición actual como primer punto
        path = []
        cx, cy = self.x, self.y
        dx, dy = direction

        while True:
            nx = (cx + dx) % GRID_COLS
            ny = (cy + dy) % GRID_ROWS

            # Si hay wrap-around, activa teleporting
            if (dx == 1 and nx == 0) or (dx == -1 and nx == GRID_COLS - 1):
                self.teleporting = True
            elif (dy == 1 and ny == 0) or (dy == -1 and ny == GRID_ROWS - 1):
                self.teleporting = True
            else:
                self.teleporting = False

            # Detectar si hay otra maldición visible
            otra_maldicion = any(
                p.x == nx and p.y == ny and p.visible and not p.disappearing and p.type == "calavera"
                for p in powerups
            )

            # Detectar si hay una habilidad distinta a calavera
            habilidad_diferente = None
            for p in powerups:
                if p.x == nx and p.y == ny and p.visible and not p.disappearing and p.type != "calavera":
                    habilidad_diferente = p
                    break

            if habilidad_diferente:
                habilidad_diferente.start_disappear()

            # Si no hay otra maldición, esta casilla es válida para terminar
            if grid[ny][nx] == 0 and not otra_maldicion:
                path.append((nx, ny))
                break

            path.append((nx, ny))
            cx, cy = nx, ny

        # Incluye la posición actual como primer paso para animar desde el inicio
        self.bounce_path = [(self.x, self.y)] + path
        self.bouncing = True
        self.bounce_index = 0
        self.bounce_timer = 0.0


# ------------------------------------------------------------------------------------
# Clase BloqueFinal
# ------------------------------------------------------------------------------------
class BloqueFinal:
# gestion bloque final
    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.anim_duration = 0.5  # segundos que tarda en caer
        self.anim_timer = 0.0
        self.start_y = -TILE_SIZE  # Aparece justo encima de la pantalla
        self.target_y = self.tile_y * TILE_SIZE + TOP_OFFSET
        self.current_y = self.start_y
        self.state = "falling"  # Estados: "falling", "landed"

    def update(self, dt):
        if self.state == "falling":
            self.anim_timer += dt
            if self.anim_timer >= self.anim_duration:
                self.anim_timer = self.anim_duration
                self.current_y = self.target_y
                self.state = "landed"
            else:
                # Interpolación suave (ease-out)
                progress = self.anim_timer / self.anim_duration
                self.current_y = self.start_y + (self.target_y - self.start_y) * (1 - (1 - progress) ** 2)

    def draw_marker(self, surface):
        if self.state == "falling":
            surface.blit(BLOQUE_FINAL_MARCA_IMG, (self.tile_x * TILE_SIZE, self.tile_y * TILE_SIZE + TOP_OFFSET))

    def draw(self, surface):
        if self.state == "falling":
            surface.blit(BLOQUE_FINAL_IMG, (self.tile_x * TILE_SIZE, self.current_y))


# ------------------------------------------------------------------------------------
# Jugador humano o CPU dentro de la partida
# ------------------------------------------------------------------------------------
class Player:
    INVERT_COMBINATIONS = [
        # Combinación 1: Inversión total
        {"up": "down", "down": "up", "left": "right", "right": "left"},
        # Combinación 2
        {"up": "down", "down": "right", "left": "up", "right": "left"},
        # Combinación 3
        {"up": "down", "down": "left", "left": "right", "right": "up"},
        # Combinación 4
        {"up": "right", "down": "up", "left": "down", "right": "left"},
        # Combinación 5
        {"up": "right", "down": "left", "left": "up", "right": "down"},
        # Combinación 6
        {"up": "left", "down": "up", "left": "right", "right": "down"},
        # Combinación 7
        {"up": "left", "down": "right", "left": "down", "right": "up"},
    ]

    def __init__(self, init_tile_x, init_tile_y, color, controls):
        self.initial_tile_x = init_tile_x
        self.initial_tile_y = init_tile_y
        self.active_curse = None
        self.curse_ends_at = None
        self.x = init_tile_x * TILE_SIZE - 40
        self.y = init_tile_y * TILE_SIZE - 40
        self.color = color
        self.can_pick_abilities = True
        self.can_place_bombs = True
        self.auto_bombing = False
        self.invert_controls = False
        self.base_speed = 2.0
        self.speed = 2.0
        self.display_speed = 1
        self.pending_speed_boosts = 0
        self.controls = controls
        self.original_controls = controls.copy()
        self.bomb_range = 1
        self.bomb_limit = 1
        self.sprite_size = 120
        self.hitbox_size = 36
        self.sprite_draw_offset_y = -10
        self.anim_frame = 0
        self.last_anim_update = time.time()
        self.anim_delay = 0.2
        self.current_direction = "right"
        self.prev_x = self.x
        self.prev_y = self.y
        self.last_step_sound = 0
        self.step_delay = 0.3
        self.auto_align_factor = 0.5
        self.curse = None
        self.curse_start = None
        self.curse_multiplier = 1
        self.last_curse_exchange = 0
        self.flashing = False
        self.flash_count = 0
        self.flash_timer = 0
        self.last_auto_bomb_tile = None
        self.push_bomb_available = False
        self.hit_bomb_available = False
        self.is_ghost = False
        self.ghost_animations = {}  # diccionario para animaciones fantasma
        self.ghost_anim_frame_index = 0
        self.last_ghost_anim_update = 0
        self.ghost_anim_delay = 150
        self.last_ghost_sound_time = 0
        self.last_bomb_placed_time = 0
        self.ghost_bomb_cooldown = 30.0  # 30 segundos
        self.is_invulnerable = False
        self.invulnerable_until = 0
        self.invulnerable_duration = 3.0  # 3 segundos
        self.invulnerable_flash_timer = 0
        self.escudo_available = False
        self.escudo_active = False
        self.escudo_activation_time = 0
        self.escudo_duration = 10.0
        self.escudo_cooldown_end_time = 0
        self.escudo_cooldown_duration = 30.0
        self.sets_won = 0
        self.is_set_winner = False
        self.set_winner_start_time = 0.0
        self.is_eliminated = False
        self.last_auto_bomb_tile = None
        self.inversion_map = None

    def get_center_coords(self):
        return (self.x + self.sprite_size / 2, self.y + self.sprite_size / 2)

    def get_hitbox(self):
        center_x = self.x + self.sprite_size // 2
        center_y = self.y + self.sprite_size // 2
        left = center_x - self.hitbox_size // 2
        top = center_y - self.hitbox_size // 2
        return pygame.Rect(left, top, self.hitbox_size, self.hitbox_size)

    def get_center_tile(self):
        cx, cy = self.get_center_coords()
        return int(cx // TILE_SIZE), int(cy // TILE_SIZE)

    def check_collision(self, grid, bombs):
        # Los fantasmas usan colisiones reducidas para atravesar bloques rompibles y bombas.
        if self.is_ghost:
            rect = self.get_hitbox()
            left_cell = rect.left // TILE_SIZE
            right_cell = (rect.right - 1) // TILE_SIZE
            top_cell = rect.top // TILE_SIZE
            bottom_cell = (rect.bottom - 1) // TILE_SIZE

            for cell_x in range(left_cell, right_cell + 1):
                for cell_y in range(top_cell, bottom_cell + 1):
                    if cell_x < 0 or cell_x >= GRID_COLS or cell_y < 0 or cell_y >= GRID_ROWS:
                        return True
                    if grid[cell_y][cell_x] in (2, 3, 4):
                        return True
            return False

        # Los jugadores vivos chocan con límites, muros, bloques rompibles y bloques finales.
        rect = self.get_hitbox()
        left_cell = rect.left // TILE_SIZE
        right_cell = (rect.right - 1) // TILE_SIZE
        top_cell = rect.top // TILE_SIZE
        bottom_cell = (rect.bottom - 1) // TILE_SIZE
        for cell_x in range(left_cell, right_cell + 1):
            for cell_y in range(top_cell, bottom_cell + 1):
                if cell_x < 0 or cell_x >= GRID_COLS or cell_y < 0 or cell_y >= GRID_ROWS:
                    return True
                if grid[cell_y][cell_x] in (1, 2, 3, 4):
                    return True
        for bomb in bombs:
            bomb_rect = pygame.Rect(bomb.pos_x, bomb.pos_y, TILE_SIZE, TILE_SIZE)
            if rect.colliderect(bomb_rect) and self not in bomb.passable_players:
                return True
        return False

    def is_compressed_vertically(self, grid, bombs):
        cx, cy = self.get_center_tile()
        up_blocked = tile_blocked_for_player(grid, bombs, cx, cy - 1, self)
        down_blocked = tile_blocked_for_player(grid, bombs, cx, cy + 1, self)
        return up_blocked and down_blocked

    def is_compressed_horizontally(self, grid, bombs):
        cx, cy = self.get_center_tile()
        left_blocked = tile_blocked_for_player(grid, bombs, cx - 1, cy, self)
        right_blocked = tile_blocked_for_player(grid, bombs, cx + 1, cy, self)
        return left_blocked and right_blocked

    def auto_align_x_once(self, grid, bombs):
        cx, cy = self.get_center_tile()
        desired_x = cx * TILE_SIZE + (TILE_SIZE // 2) - self.sprite_size // 2
        dist = desired_x - self.x
        if abs(dist) < 0.1:
            return True
        direction = 1 if dist > 0 else -1
        max_move = min(abs(dist), self.speed * self.auto_align_factor)
        old_x = self.x
        self.x += direction * max_move
        if self.check_collision(grid, bombs):
            self.x = old_x
            return True
        if abs(self.x - desired_x) < 0.1:
            self.x = desired_x
            return True
        return False

    def auto_align_y_once(self, grid, bombs):
        cx, cy = self.get_center_tile()
        desired_y = cy * TILE_SIZE + (TILE_SIZE // 2) - self.sprite_size // 2
        dist = desired_y - self.y
        if abs(dist) < 0.1:
            return True
        direction = 1 if dist > 0 else -1
        max_move = min(abs(dist), self.speed * self.auto_align_factor)
        old_y = self.y
        self.y += direction * max_move
        if self.check_collision(grid, bombs):
            self.y = old_y
            return True
        if abs(self.y - desired_y) < 0.1:
            self.y = desired_y
            return True
        return False

    def activate_escudo(self):
        current_time = time.time()
        if (self.escudo_available and
                not self.escudo_active and
                current_time >= self.escudo_cooldown_end_time):
            self.escudo_active = True
            self.escudo_activation_time = current_time

    def update_escudo(self):
        if self.escudo_active and time.time() > self.escudo_activation_time + self.escudo_duration:
            self.escudo_active = False
            self.escudo_cooldown_end_time = time.time() + self.escudo_cooldown_duration

    def move_in_small_steps(self, dx, dy, grid, bombs):
        steps_int = int(self.speed)
        frac = self.speed - steps_int
        for _ in range(steps_int):
            old_x, old_y = self.x, self.y
            self.x += dx
            self.y += dy
            if self.check_collision(grid, bombs):
                self.x, self.y = old_x, old_y

                if self.push_bomb_available:
                    cx = old_x + self.sprite_size // 2
                    cy = old_y + self.sprite_size // 2
                    tile_x = int(cx // TILE_SIZE)
                    tile_y = int(cy // TILE_SIZE)
                    dir_x, dir_y = dx, dy
                    if abs(dir_x) > abs(dir_y):
                        dir_y = 0
                        dir_x = 1 if dir_x > 0 else -1
                    else:
                        dir_x = 0
                        dir_y = 1 if dir_y > 0 else -1
                    next_tile_x = tile_x + dir_x
                    next_tile_y = tile_y + dir_y

                    bomb_target = next(
                        (b for b in bombs if b.tile_x == next_tile_x and b.tile_y == next_tile_y and not b.exploded),
                        None)
                    if bomb_target:
                        if not bomb_target.sliding:
                            bomb_target.try_start_push(dir_x, dir_y, grid, bombs, players, powerups)

        if frac > 0:
            old_x, old_y = self.x, self.y
            self.x += dx * frac
            self.y += dy * frac
            if self.check_collision(grid, bombs):
                self.x, self.y = old_x, old_y

    def move(self, direction, grid, bombs, powerups, lapidas):
        """
        Aplica la inversión de controles si la maldición está activa.
        """
        final_direction = direction
        if self.inversion_map:
            final_direction = self.inversion_map.get(direction, direction)

        # Llamamos a la función de movimiento correspondiente a la dirección final
        if final_direction == "up":
            self.move_up(grid, bombs, powerups, lapidas)
        elif final_direction == "down":
            self.move_down(grid, bombs, powerups, lapidas)
        elif final_direction == "left":
            self.move_left(grid, bombs, powerups, lapidas)
        elif final_direction == "right":
            self.move_right(grid, bombs, powerups, lapidas)

    def move_up(self, grid, bombs, powerups, lapidas):
        self.current_direction = "up"
        if self.is_compressed_vertically(grid, bombs):
            return
        if self.auto_align_x_once(grid, bombs):
            self.move_in_small_steps(0, -1, grid, bombs)
            new_tile = self.get_center_tile()
            if self.auto_bombing and new_tile != self.last_auto_bomb_tile:
                self.place_bomb(bombs, powerups, grid, lapidas, forced=True)

    def move_down(self, grid, bombs, powerups, lapidas):
        self.current_direction = "down"
        if self.is_compressed_vertically(grid, bombs):
            return
        if self.auto_align_x_once(grid, bombs):
            self.move_in_small_steps(0, 1, grid, bombs)
            new_tile = self.get_center_tile()
            if self.auto_bombing and new_tile != self.last_auto_bomb_tile:
                self.place_bomb(bombs, powerups, grid, lapidas, forced=True)

    def move_left(self, grid, bombs, powerups, lapidas):
        self.current_direction = "left"
        if self.is_compressed_horizontally(grid, bombs):
            return
        if self.auto_align_y_once(grid, bombs):
            self.move_in_small_steps(-1, 0, grid, bombs)
            new_tile = self.get_center_tile()
            if self.auto_bombing and new_tile != self.last_auto_bomb_tile:
                self.place_bomb(bombs, powerups, grid, lapidas, forced=True)

    def move_right(self, grid, bombs, powerups, lapidas):
        self.current_direction = "right"
        if self.is_compressed_horizontally(grid, bombs):
            return
        if self.auto_align_y_once(grid, bombs):
            self.move_in_small_steps(1, 0, grid, bombs)
            new_tile = self.get_center_tile()
            if self.auto_bombing and new_tile != self.last_auto_bomb_tile:
                self.place_bomb(bombs, powerups, grid, lapidas, forced=True)

    def update_passable(self, bombs):
        for bomb in bombs:
            if self in bomb.passable_players:
                bomb_rect = pygame.Rect(bomb.pos_x, bomb.pos_y, TILE_SIZE, TILE_SIZE)
                if not self.get_hitbox().colliderect(bomb_rect):
                    bomb.passable_players.remove(self)

    def update_animation(self):
        if self.is_ghost:
            return

        current_time = time.time()
        if (self.x != self.prev_x or self.y != self.prev_y):
            if (current_time - self.last_step_sound >= self.step_delay):
                FOOTSTEP_SOUND.play()
                self.last_step_sound = current_time
            if (current_time - self.last_anim_update >= self.anim_delay):
                self.anim_frame = (self.anim_frame + 1) % 9
                self.last_anim_update = current_time
        else:
            self.anim_frame = 0
        self.prev_x = self.x
        self.prev_y = self.y

    def update_ghost_sound(self):

        GHOST_SOUND_INTERVAL = 10.0

        current_time = time.time()
        if current_time - self.last_ghost_sound_time > GHOST_SOUND_INTERVAL:
            FANTASMA_SOUND.play()
            self.last_ghost_sound_time = current_time  # Reinicia el temporizador

    def apply_curse(self, curse_name):
        if curse_name == "reset":
            global grid, powerups, dropped_abilities
            trigger_reset_effect(self, grid, powerups, dropped_abilities)
            return

        meta = CURSES[curse_name]

        if meta.get("clears_previous", False) and self.active_curse:
            self._clear_curse_effects(self.active_curse)

        if curse_name in ("hyper_speed", "slow_speed"):
            self._saved_speed_before_curse = self.speed
            self.pending_speed_boosts = 0

        self.active_curse = curse_name
        duration = meta.get("duration")
        self.curse_ends_at = time.time() + duration if duration is not None else None

        meta["set_effect"](self, curse_name)

    def receive_transmitted_curse(self, new_curse_name, new_curse_ends_at):
        """Aplica una maldición y su tiempo restante al recibirla de otro jugador."""
        if self.active_curse:
            self._clear_curse_effects(self.active_curse)

        self.active_curse = new_curse_name
        self.curse_ends_at = new_curse_ends_at

        if self.active_curse:
            self._set_curse_effects(self.active_curse)
        else:  # Si se recibe 'None', es que el jugador ha quedado limpio
            self.inversion_map = None  # Asegurarse de limpiar el mapa de inversión

    def update_curse(self):
        if self.active_curse and self.curse_ends_at:
            if time.time() >= self.curse_ends_at:
                ended = self.active_curse
                self._clear_curse_effects(ended)
                self.active_curse = None
                self.curse_ends_at = None
                self.flashing = True
                self.flash_count = 3
                self.flash_timer = time.time()

    def become_ghost(self):
        """
        Transforma al jugador en un fantasma en la casilla donde murió.
        """
        print(f"¡El jugador {self.player_index + 1} se ha convertido en un fantasma!")

        # Estado de fantasma
        self.is_ghost = True
        self.is_invulnerable = False  # No es invulnerable como fantasma

        self.last_ghost_sound_time = time.time()

        # Limpiar estado de jugador vivo
        if self.active_curse:
            self._clear_curse_effects(self.active_curse)
        self.active_curse = None
        self.curse_ends_at = None
        self.bomb_limit = 1
        self.bomb_range = 1
        self.push_bomb_available = False
        self.hit_bomb_available = False
        self.display_speed = 1  # Mostramos la velocidad del fantasma
        self.pending_speed_boosts = 0
        # Resetear estado del escudo
        self.escudo_available = False
        self.escudo_active = False
        self.escudo_cooldown_end_time = 0

        # Aplicar propiedades de fantasma
        self.speed = 1  # Velocidad reducida



    def eliminate(self):
        print(f"¡El jugador {self.player_index + 1} ha sido eliminado de la ronda!")
        self.is_eliminated = True

    def resurrect(self):
        """
        Devuelve al fantasma a la vida en su posición inicial.
        """
        print(f"¡El jugador {self.player_index + 1} ha vuelto a la vida!")
        REAPARICION_SOUND.play()  # Reproduce el sonido de reaparición
        self.is_ghost = False

        # Restaurar habilidades y estado de jugador vivo
        self.bomb_limit = 1
        self.bomb_range = 1
        self.speed = self.base_speed
        self.display_speed = 1
        self.push_bomb_available = False
        self.hit_bomb_available = False
        self.active_curse = None  # Limpiar cualquier maldición residual

        # Resetear estado del escudo
        self.escudo_available = False
        self.escudo_active = False
        self.escudo_cooldown_end_time = 0

        # Mover al jugador a su posición de inicio de partida
        self.x = self.initial_tile_x * TILE_SIZE - 40
        self.y = self.initial_tile_y * TILE_SIZE - 40

        # Activar invulnerabilidad temporal con parpadeo
        self.is_invulnerable = True
        self.invulnerable_until = time.time() + self.invulnerable_duration
        self.invulnerable_flash_timer = time.time()  # Inicia el temporizador para el parpadeo

    def draw(self, surface):
        if self.is_ghost:
            animacion_actual = self.ghost_animations.get(self.current_direction, [])
            if not animacion_actual:
                return
            current_time_ms = pygame.time.get_ticks()
            if current_time_ms - self.last_ghost_anim_update > self.ghost_anim_delay:
                self.last_ghost_anim_update = current_time_ms
                self.ghost_anim_frame_index = (self.ghost_anim_frame_index + 1) % len(animacion_actual)
            sprite = animacion_actual[self.ghost_anim_frame_index]
            sprite_con_alpha = sprite.copy()
            sprite_con_alpha.set_alpha(int(255 * 0.90))
            draw_x = self.x + (self.sprite_size - sprite.get_width()) // 2
            draw_y = self.y + (self.sprite_size - sprite.get_height()) // 2 + self.sprite_draw_offset_y + TOP_OFFSET
            surface.blit(sprite_con_alpha, (draw_x, draw_y))
            return

        # --- PARPADEO DEL GANADOR DEL SET ---
        if self.is_set_winner:
            flash_interval = 0.1
            if int((time.time() - self.set_winner_start_time) / flash_interval) % 2 == 0:
                flash_surf = pygame.Surface((self.sprite_size, self.sprite_size), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, 150))
                surface.blit(flash_surf, (self.x, self.y + self.sprite_draw_offset_y + TOP_OFFSET))

        # Aura por detrás (solo si hay maldición activa)
        if self.active_curse and CURSES[self.active_curse]["duration"] is not None:
            if not hasattr(Player, 'aura_frames'):
                aura_path = os.path.join(os.path.dirname(__file__), ASSETS_DIR, "Gadgets", "Efectos_visuales",
                                         "maldicion.gif")
                pil_image = PILImage.open(aura_path)
                frames = []
                try:
                    while True:
                        frame = pil_image.convert("RGBA")
                        data = frame.tobytes()
                        mode = frame.mode
                        size = frame.size
                        pygame_surface = pygame.image.fromstring(data, size, mode)
                        frames.append(pygame_surface)
                        pil_image.seek(pil_image.tell() + 1)
                except EOFError:
                    pass
                Player.aura_frames = frames
                Player.aura_frame_count = len(frames)
                Player.aura_frame_duration = 100
            current_time_ms = pygame.time.get_ticks()
            frame_index = (current_time_ms // Player.aura_frame_duration) % Player.aura_frame_count
            aura_image = Player.aura_frames[frame_index]
            new_size = int(self.sprite_size * 0.9)
            aura_image_scaled = pygame.transform.scale(aura_image, (new_size, new_size))
            aura_behind = aura_image_scaled.copy()
            aura_behind.set_alpha(150)
            aura_rect_behind = aura_behind.get_rect(center=(self.x + self.sprite_size // 2,
                                                            self.y + self.sprite_draw_offset_y + TOP_OFFSET + self.sprite_size // 2 - 10))
            surface.blit(aura_behind, aura_rect_behind)

        # DIBUJO DEL ESCUDO (DETRÁS)
        if self.escudo_active:
            if not hasattr(Player, 'escudo_frames'):
                escudo_path = os.path.join(os.path.dirname(__file__), ASSETS_DIR, "Gadgets", "Efectos_visuales",
                                           "escudo.gif")
                try:
                    pil_image = PILImage.open(escudo_path)
                    frames = []
                    while True:
                        frame = pil_image.convert("RGBA")
                        pygame_frame = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
                        frames.append(pygame_frame)
                        pil_image.seek(pil_image.tell() + 1)
                except EOFError:
                    pass
                except (FileNotFoundError, ImportError):
                    frames = []
                Player.escudo_frames = frames
                Player.escudo_frame_count = len(frames) if frames else 1
                Player.escudo_frame_duration = 100
            if Player.escudo_frames:
                current_time_ms = pygame.time.get_ticks()
                frame_index = (current_time_ms // Player.escudo_frame_duration) % Player.escudo_frame_count
                escudo_image = Player.escudo_frames[frame_index]
                new_size = int(self.sprite_size)
                escudo_image_scaled = pygame.transform.smoothscale(escudo_image, (new_size, new_size))
                escudo_behind = escudo_image_scaled.copy()
                escudo_behind.set_alpha(int(255 * 0.50))
                escudo_rect_behind = escudo_behind.get_rect(center=(self.x + self.sprite_size // 2,
                                                                    self.y + self.sprite_draw_offset_y + TOP_OFFSET + self.sprite_size // 2))
                surface.blit(escudo_behind, escudo_rect_behind)

        # Dibujo del jugador (sprite según dirección y personaje)
        if hasattr(self, "animaciones") and self.current_direction in self.animaciones:
            debe_dibujarse = True
            if self.is_invulnerable:
                # Esta condición hace que el jugador parpadee
                if int(time.time() * 10) % 2 != 0:
                    debe_dibujarse = False

            if debe_dibujarse:
                image_list = self.animaciones[self.current_direction]
                sprite = image_list[self.anim_frame % len(image_list)]
                surface.blit(sprite, (self.x, self.y + self.sprite_draw_offset_y + TOP_OFFSET))
                if hasattr(self, "player_index") and 0 <= self.player_index < len(PLAYER_MARKS):
                    mark_img = PLAYER_MARKS[self.player_index]
                    mark_rect = mark_img.get_rect()
                    altura_offset = +25
                    mark_rect.midbottom = (self.x + self.sprite_size // 2,
                                           self.y + self.sprite_draw_offset_y + TOP_OFFSET + altura_offset)
                    surface.blit(mark_img, mark_rect)

        # Aura por delante (solo si hay maldición activa)
        if self.active_curse and CURSES[self.active_curse]["duration"] is not None:
            aura_front = aura_image_scaled.copy()
            aura_front.set_alpha(100)
            aura_rect_front = aura_front.get_rect(center=(self.x + self.sprite_size // 2,
                                                          self.y + self.sprite_draw_offset_y + TOP_OFFSET + self.sprite_size // 2 - 10))
            surface.blit(aura_front, aura_rect_front)

        # DIBUJO DEL ESCUDO (DELANTE)
        if self.escudo_active and hasattr(Player, 'escudo_frames') and Player.escudo_frames:
            current_time_ms = pygame.time.get_ticks()
            frame_index = (current_time_ms // Player.escudo_frame_duration) % Player.escudo_frame_count
            escudo_image = Player.escudo_frames[frame_index]
            new_size = int(self.sprite_size)
            escudo_image_scaled = pygame.transform.smoothscale(escudo_image, (new_size, new_size))
            escudo_overlay = escudo_image_scaled.copy()
            escudo_overlay.set_alpha(int(255 * 0.30))
            escudo_rect_front = escudo_overlay.get_rect(center=(self.x + self.sprite_size // 2,
                                                                self.y + self.sprite_draw_offset_y + TOP_OFFSET + self.sprite_size // 2))
            surface.blit(escudo_overlay, escudo_rect_front)

        # Efecto de parpadeo al expirar la maldición
        if self.flashing:
            flash_surf = pygame.Surface((self.sprite_size, self.sprite_size))
            flash_surf.fill(WHITE)
            flash_surf.set_alpha(180)
            surface.blit(flash_surf, (self.x, self.y + self.sprite_draw_offset_y + TOP_OFFSET))
            if time.time() - self.flash_timer >= 0.4:
                self.flash_timer = time.time()
                self.flash_count -= 1
                if self.flash_count <= 0:
                    self.flashing = False

    def place_bomb(self, bombs, powerups, grid, lapidas, forced=False):
        # La lógica para fantasmas no cambia
        if self.is_ghost:
            current_time = time.time()
            if current_time - self.last_bomb_placed_time >= self.ghost_bomb_cooldown:
                cx = self.x + self.sprite_size // 2
                cy = self.y + self.sprite_size // 2
                bomb_tile_x = int(cx // TILE_SIZE)
                bomb_tile_y = int(cy // TILE_SIZE)
                if grid[bomb_tile_y][bomb_tile_x] == 1:
                    return
                if any(b.tile_x == bomb_tile_x and b.tile_y == bomb_tile_y and not b.exploded for b in bombs):
                    return
                for p in powerups[:]:
                    if p.visible and not p.disappearing and (p.x, p.y) == (bomb_tile_x, bomb_tile_y):
                        p.start_disappear()
                for lapida in lapidas[:]:
                    if (lapida.tile_x, lapida.tile_y) == (bomb_tile_x, bomb_tile_y):
                        lapida.start_slow_fade()
                new_bomb = Bomb(bomb_tile_x, bomb_tile_y, 1)
                new_bomb.owner = self
                registrar_jugadores_pasables_en_bomba(new_bomb, globals().get("players", []))
                bombs.append(new_bomb)
                COLOCAR_BOMBA_SOUND.play()
                self.last_bomb_placed_time = current_time
            return

        # --- Lógica para el jugador VIVO ---

        # Si la maldición auto_bomb está activa, el botón manual no funciona.
        # Solo se pueden colocar bombas si 'forced' es True (desde el movimiento).
        if self.auto_bombing and not forced:
            return

        if not self.can_place_bombs:  # Esto ya gestiona la maldición "no_bomb"
            return

        # El resto de la lógica original se mantiene
        current_bombs = [b for b in bombs if b.owner == self and not b.exploded]
        if len(current_bombs) >= self.bomb_limit:
            return

        cx = self.x + self.sprite_size // 2
        cy = self.y + self.sprite_size // 2
        bomb_tile_x = int(cx // TILE_SIZE)
        bomb_tile_y = int(cy // TILE_SIZE)

        if any(b.tile_x == bomb_tile_x and b.tile_y == bomb_tile_y and not b.exploded for b in bombs):
            return

        new_bomb = Bomb(bomb_tile_x, bomb_tile_y, self.bomb_range)
        new_bomb.owner = self
        new_bomb.passable_players.add(self)
        registrar_jugadores_pasables_en_bomba(new_bomb, globals().get("players", []))
        bombs.append(new_bomb)
        COLOCAR_BOMBA_SOUND.play()

        # Guardamos la casilla donde se ha puesto la bomba para la lógica de auto_bomb
        if self.auto_bombing:
            self.last_auto_bomb_tile = (bomb_tile_x, bomb_tile_y)

        if self.active_curse == "no_ability":
            for p in powerups[:]:
                if p.visible and not p.disappearing and (p.x, p.y) == (bomb_tile_x, bomb_tile_y):
                    p.start_disappear()

    def _set_curse_effects(self, curse_name):
        if curse_name == "no_ability":
            self.can_pick_abilities = False
        elif curse_name == "no_bomb":
            self.can_place_bombs = False
        elif curse_name == "auto_bomb":
            self.auto_bombing = True
            self.last_auto_bomb_tile = self.get_center_tile()
        elif curse_name == "inverted":
            self.inversion_map = random.choice(self.INVERT_COMBINATIONS)
        elif curse_name == "hyper_speed":
            self.speed = 20
        elif curse_name == "slow_speed":
            self.speed = 0.5

    def _clear_curse_effects(self, curse_name):
        if curse_name == "no_ability":
            self.can_pick_abilities = True
        elif curse_name == "no_bomb":
            self.can_place_bombs = True
        elif curse_name == "auto_bomb":
            self.auto_bombing = False
            self.last_auto_bomb_tile = None
        elif curse_name == "inverted":
            self.inversion_map = None
        elif curse_name in ("hyper_speed", "slow_speed"):
            original = getattr(self, "_saved_speed_before_curse", self.base_speed)
            self.speed = original + self.pending_speed_boosts
            self._saved_speed_before_curse = None
            self.pending_speed_boosts = 0

    def check_static_push(self, grid, bombs, players, powerups):
        if not self.push_bomb_available:
            return

        tile_x, tile_y = self.get_center_tile()

        direction_map = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }

        if self.current_direction not in direction_map:
            return

        dx, dy = direction_map[self.current_direction]
        target_x = tile_x + dx
        target_y = tile_y + dy

        if target_x < 0 or target_x >= GRID_COLS or target_y < 0 or target_y >= GRID_ROWS:
            return

        # Comprobamos si la casilla objetivo tiene una bomba
        for b in bombs:
            if b.tile_x == target_x and b.tile_y == target_y and not b.exploded:
                if not b.sliding:
                    b.try_start_push(dx, dy, grid, bombs, players, powerups)
                break

    def reset_for_new_set(self, init_tile_x, init_tile_y):
        """ Reinicia el estado del jugador para un nuevo set. """
        self.initial_tile_x = init_tile_x
        self.initial_tile_y = init_tile_y
        self.x = init_tile_x * TILE_SIZE - 40
        self.y = init_tile_y * TILE_SIZE - 40
        self.is_ghost = False
        self.is_eliminated = False
        self.is_set_winner = False

        self.bomb_range = 1
        self.bomb_limit = 1
        self.speed = 2.0
        self.base_speed = 2.0
        self.display_speed = 1
        self.pending_speed_boosts = 0
        self.push_bomb_available = False
        self.hit_bomb_available = False
        self.escudo_available = False
        self.escudo_active = False
        self.pending_speed_boosts = 0

        if self.active_curse:
            self._clear_curse_effects(self.active_curse)
        self.active_curse = None
        self.curse_ends_at = None
        self.controls = self.original_controls.copy()

        # orientacion inicial del personaje
        self.current_direction = "down"
        self.anim_frame = 0


# --------------------------------------------------------------------------------
# Función para cargar animaciones de un personaje según su nombre
def cargar_animaciones_personaje(nombre_personaje):
    animaciones = {}
    for direccion in ["right", "left", "up", "down"]:
        carpeta = os.path.join(ASSETS_DIR, "Jugadores", nombre_personaje, direccion)
        imagenes = []
        for i in range(1, 8):
            img = load_image(f"{direccion}{i}.png", (120, 120), folder=carpeta)
            imagenes.append(img)
        animaciones[direccion] = imagenes
    return animaciones


def cargar_animaciones_fantasma_por_direccion(player_index):
    animaciones = {}
    direcciones = ["up", "down", "left", "right"]

    GHOST_TARGET_WIDTH = 55

    base_path = os.path.join(ASSETS_DIR, "Jugadores", "Fantasma muerto", f"Jugador {player_index + 1}")

    for direccion in direcciones:
        frames = []
        ruta_carpeta = os.path.join(base_path, direccion)

        if not os.path.isdir(ruta_carpeta):
            print(f"ADVERTENCIA: No se encontró la carpeta de animación: {ruta_carpeta}")
            continue

        for i in range(1, 5):
            nombre_fichero = f"{direccion}{i}.png"
            ruta_imagen = os.path.join(ruta_carpeta, nombre_fichero)

            if os.path.exists(ruta_imagen):
                try:
                    original_image = pygame.image.load(ruta_imagen).convert_alpha()
                    original_width, original_height = original_image.get_size()

                    if original_width > 0:  # Evitar división por cero
                        aspect_ratio = original_height / original_width
                        new_height = int(GHOST_TARGET_WIDTH * aspect_ratio)
                        # Usamos smoothscale para un mejor resultado al ampliar
                        imagen = pygame.transform.smoothscale(original_image, (GHOST_TARGET_WIDTH, new_height))
                        frames.append(imagen)

                except pygame.error as e:
                    print(f"Error al cargar la imagen del fantasma: {ruta_imagen} - {e}")
                    break
            else:
                print(f"ADVERTENCIA: No se encontró el frame '{ruta_imagen}'.")
                break

        if len(frames) < 4:
            print(
                f"INFO: Se cargaron {len(frames)}/4 frames para la dirección '{direccion}' del Jugador {player_index + 1}.")

        animaciones[direccion] = frames

    if not any(animaciones.values()):
        print(f"ERROR CRÍTICO: No se pudo cargar ninguna animación para el fantasma del Jugador {player_index + 1}.")
        return {d: [] for d in direcciones}

    return animaciones


# Diccionario de nombres por índice desde la pantalla de personajes
nombres_por_indice = {
    0: "Mork",
    1: "Guerrero Rojo",
    2: "Mortis",
    3: "Grimfang",
    4: "Warlord",
    5: "Vael",
    6: "Sarthus",
    7: "Guerrero Azul",
    8: "Guerrero Blanco",
    9: "Guerrero Negro",
    10: "Calvo",
    11: "Ragnar"
}


# ------------------------------------------------------------------------------------
# Clase Bomb (con modificación en explode para que la explosión se detenga en la maldición)
# ------------------------------------------------------------------------------------
class Bomb:
    def __init__(self, tile_x, tile_y, blast_range):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.blast_range = blast_range
        self.timer = 3
        self.plant_time = time.time()
        self.exploded = False
        self.passable_players = set()
        self.chain_triggered = False
        self.chain_trigger_time = None
        self.owner = None
        self.pos_x = self.tile_x * TILE_SIZE
        self.pos_y = self.tile_y * TILE_SIZE
        self.push_direction = None
        self.push_path = []
        self.push_index = 0
        self.push_timer = 0.0
        self.push_duration = 0.0
        self.push_speed = 0.0
        self.can_be_pushed = False
        self.sliding = False
        self.slide_start_x = 0
        self.slide_start_y = 0
        self.slide_target_x = 0
        self.slide_target_y = 0
        self.slide_duration = 0
        self.slide_elapsed = 0
        self.hit_bouncing = False
        self.hit_bounce_path = []
        self.hit_bounce_index = 0
        self.hit_bounce_start_time = 0
        self.hit_bounce_duration = 300  # ms por salto de casilla
        self.hit_bounce_height = 30  # Altura del arco en píxeles
        self.timer_frozen = False
        self.freeze_start_time = None

    def tile_blocked_for_bomb(self, grid, bombs, tx, ty):
        if tx < 0 or tx >= GRID_COLS or ty < 0 or ty >= GRID_ROWS:
            return True
        if grid[ty][tx] in (1, 2, 3, 4):
            return True
        for b in bombs:
            if b is not self and not b.exploded:
                if b.tile_x == tx and b.tile_y == ty:
                    return True
        return False

    def center_of_tile(self, tx, ty):
        return (tx * TILE_SIZE + TILE_SIZE / 2,
                ty * TILE_SIZE + TILE_SIZE / 2)

    def start_sliding_to(self, next_tx, next_ty):
        self.sliding = True
        self.slide_elapsed = 0
        start_center = self.center_of_tile(self.tile_x, self.tile_y)
        self.slide_start_x = start_center[0]
        self.slide_start_y = start_center[1]
        target_center = self.center_of_tile(next_tx, next_ty)
        self.slide_target_x = target_center[0]
        self.slide_target_y = target_center[1]
        dist = math.hypot(self.slide_target_x - self.slide_start_x,
                          self.slide_target_y - self.slide_start_y)
        self.slide_duration = dist / PUSH_SPEED

    def update_sliding(self):
        if not self.sliding:
            return
        dt = 1
        self.slide_elapsed += dt
        if self.slide_elapsed >= self.slide_duration:
            self.slide_elapsed = self.slide_duration
            self.sliding = False
            dest_tx = int(self.slide_target_x // TILE_SIZE)
            dest_ty = int(self.slide_target_y // TILE_SIZE)
            self.tile_x = dest_tx
            self.tile_y = dest_ty
            self.pos_x = self.slide_target_x - TILE_SIZE / 2
            self.pos_y = self.slide_target_y - TILE_SIZE / 2
        else:
            ratio = self.slide_elapsed / self.slide_duration
            new_cx = (1 - ratio) * self.slide_start_x + ratio * self.slide_target_x
            new_cy = (1 - ratio) * self.slide_start_y + ratio * self.slide_target_y
            self.pos_x = new_cx - TILE_SIZE / 2
            self.pos_y = new_cy - TILE_SIZE / 2

    def update_push(self, grid, bombs):
        if self.sliding:
            self.update_sliding()
            if self.sliding:
                return
        if not self.push_direction:
            return
        while True:
            dx, dy = self.push_direction
            next_tx = self.tile_x + dx
            next_ty = self.tile_y + dy
            if self.tile_blocked_for_bomb(grid, bombs, next_tx, next_ty):
                self.push_direction = None
                return
            self.start_sliding_to(next_tx, next_ty)
            self.update_sliding()
            if self.sliding:
                break

    def draw(self, surface):
        self.update_push_slide()  # actualiza animación de empuje continuo
        draw_x = self.pos_x
        draw_y = self.pos_y
        if self.chain_triggered:
            total_time = 0.75
            elapsed = time.time() - self.chain_trigger_time
        else:
            total_time = 3.0
            elapsed = time.time() - self.plant_time
        frame_time = total_time / 15.0
        frame_index = min(int(elapsed / frame_time), 14)
        bomb_image = BOMB_IMAGES[frame_index]
        base_scale = 1.4
        oscillation = 0.15 * math.sin(2 * math.pi * (elapsed / total_time))
        bomb_image_scaled = pygame.transform.scale(
            bomb_image,
            (int(bomb_image.get_width() * (base_scale + oscillation)),
             int(bomb_image.get_height() * (base_scale + oscillation)))
        )
        px = draw_x + (TILE_SIZE - bomb_image_scaled.get_width()) // 2
        py = draw_y + (TILE_SIZE - bomb_image_scaled.get_height()) // 2 + TOP_OFFSET
        surface.blit(bomb_image_scaled, (px, py))

    def explode(self, grid, players, bombs, powerups):
        if self.hit_bouncing:
            return []
        if self.exploded:
            return []
        self.exploded = True
        if self in bombs:
            bombs.remove(self)
        EXPLOSION_SOUND.play()

        # --- LÓGICA MODIFICADA PARA CREAR OBJETOS EXPLOSION CON DUEÑO ---
        explosions = [Explosion(self.tile_x, self.tile_y, "center", None, owner=self.owner)]
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]

        for dx, dy in directions:
            for i in range(1, self.blast_range + 1):
                nx = self.tile_x + dx * i
                ny = self.tile_y + dy * i

                if not (0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS):
                    break
                if grid[ny][nx] == 1:
                    if (nx, ny) not in exploding_blocks:
                        exploding_blocks[(nx, ny)] = time.time()
                        reveal_powerup_if_any(powerups, nx, ny)
                    break
                if grid[ny][nx] in (2, 3):
                    break

                bomb_found = next((b for b in bombs if b.tile_x == nx and b.tile_y == ny and not b.exploded), None)
                if bomb_found is not None:
                    if not bomb_found.chain_triggered:
                        bomb_found.chain_triggered = True
                        bomb_found.chain_trigger_time = time.time()
                    break

                found_powerup = False
                for p in powerups:
                    if p.x == nx and p.y == ny and p.visible and not p.disappearing:
                        if p.type == "calavera":
                            p.visible = True
                            p.start_bounce((dx, dy), grid, bombs, powerups)
                        else:
                            p.start_disappear()
                            explosions.append(Explosion(nx, ny, "ability", (dx, dy), owner=self.owner))
                        found_powerup = True
                        break
                if found_powerup:
                    break

                # Añadimos la explosión como un objeto completo con su dueño
                if i == self.blast_range:
                    explosions.append(Explosion(nx, ny, "extreme", (dx, dy), owner=self.owner))
                else:
                    explosions.append(Explosion(nx, ny, "lateral", (dx, dy), owner=self.owner))

        return explosions

    def hit_by_player(self, dx, dy, grid, bombs, powerups, players, bounce_length=3):
        import math

        # Obtén la celda de partida y su centro en píxeles
        start_tile = (self.tile_x, self.tile_y)
        start_center = (
            start_tile[0] * TILE_SIZE + TILE_SIZE / 2,
            start_tile[1] * TILE_SIZE + TILE_SIZE / 2
        )

        per_cell_duration = 150  # ms por casilla (valor base para calcular el tiempo)
        path_tiles = [start_tile]

        # Primer salto: se intenta saltar 3 casillas de un solo bote
        intended_tile = (
            (start_tile[0] + dx * bounce_length) % GRID_COLS,
            (start_tile[1] + dy * bounce_length) % GRID_ROWS
        )
        path_tiles.append(intended_tile)

        # Función para determinar si una celda está libre:
        def cell_free(tile, bombs, powerups):
            tx, ty = tile
            # Si es un muro o bloque inamovible:
            if grid[ty][tx] in (1, 2, 3):
                return False
            # Si hay alguna bomba activa (que no sea self) en esa celda:
            for bomb in bombs:
                if bomb is not self and not bomb.exploded:
                    if bomb.tile_x == tx and bomb.tile_y == ty:
                        return False
            # Si hay alguna maldición (powerup de tipo CURSE) visible bloqueante:
            for p in powerups:
                if p.x == tx and p.y == ty and p.visible and p.type in CURSES:
                    return False
            return True

        # Si la casilla destino del salto de 3 casillas no está libre, encadena saltos de 1 celda
        if not cell_free(intended_tile, bombs, powerups):
            current = intended_tile
            while not cell_free(current, bombs, powerups):
                next_tile = ((current[0] + dx) % GRID_COLS, (current[1] + dy) % GRID_ROWS)
                path_tiles.append(next_tile)
                current = next_tile

        # Convertir la secuencia de celdas a coordenadas en píxeles (centrando la posición de cada celda)
        pixel_path = [
            (t[0] * TILE_SIZE + TILE_SIZE / 2, t[1] * TILE_SIZE + TILE_SIZE / 2)
            for t in path_tiles
        ]

        # Cálculo de la duración para cada segmento basándose en la distancia real recorrida (con wrap-around)
        duration_list = []
        total_time = 0
        for i in range(len(pixel_path) - 1):
            p1 = pixel_path[i]
            p2 = pixel_path[i + 1]

            dx_px = p2[0] - p1[0]
            dy_px = p2[1] - p1[1]

            # Ajuste horizontal para wrap-around
            map_width_px = GRID_COLS * TILE_SIZE
            if abs(dx_px) > map_width_px / 2:
                if dx_px > 0:
                    dx_px -= map_width_px
                else:
                    dx_px += map_width_px

            # Ajuste vertical para wrap-around
            map_height_px = GRID_ROWS * TILE_SIZE
            if abs(dy_px) > map_height_px / 2:
                if dy_px > 0:
                    dy_px -= map_height_px
                else:
                    dy_px += map_height_px

            dist_segment = math.hypot(dx_px, dy_px)
            # La duración se calcula proporcional a la distancia recorrida; por ejemplo:
            time_segment = (dist_segment / TILE_SIZE) * per_cell_duration
            duration_list.append(time_segment)
            total_time += time_segment

        # Configura los parámetros para que update_hit_bounce realice la interpolación continua.
        self.hit_bouncing = True
        self.hit_bounce_pixel_path = pixel_path
        self.hit_bounce_durations = duration_list
        self.hit_bounce_total_time = total_time
        self.hit_bounce_start_time = pygame.time.get_ticks()
        self.hit_bounce_height = 15  # Ajusta la altura del arco del salto si lo deseas

        # Congela el temporizador de la bomba hasta que finalice la animación
        self.timer_frozen = True
        self.freeze_start_time = time.time()

    def update_hit_bounce(self, grid, players, bombs, powerups):
        import math

        if not self.hit_bouncing:
            return

        now = pygame.time.get_ticks()
        elapsed = now - self.hit_bounce_start_time

        # Si la animación ya terminó, fijamos la bomba en la última celda
        if elapsed >= self.hit_bounce_total_time:
            final_point = self.hit_bounce_pixel_path[-1]
            self.pos_x = final_point[0] - TILE_SIZE / 2
            self.pos_y = final_point[1] - TILE_SIZE / 2
            self.tile_x = int(final_point[0] // TILE_SIZE)
            self.tile_y = int(final_point[1] // TILE_SIZE)
            self.hit_bouncing = False

            # Reanudamos el temporizador de la bomba (pausado)
            if self.timer_frozen:
                freeze_time = time.time() - self.freeze_start_time
                self.plant_time += freeze_time
                self.timer_frozen = False

                # Verificamos si ha caído sobre una calavera o poder
                for p in powerups:
                    if p.x == self.tile_x and p.y == self.tile_y and p.visible and not p.disappearing:
                        if p.type == "calavera":
                            # Obtenemos la dirección del último movimiento
                            last_point_index = max(0, len(self.hit_bounce_pixel_path) - 2)
                            dx = self.tile_x - int(self.hit_bounce_pixel_path[last_point_index][0] // TILE_SIZE)
                            dy = self.tile_y - int(self.hit_bounce_pixel_path[last_point_index][1] // TILE_SIZE)

                            # Normalizamos la dirección para asegurar que sea (1,0), (-1,0), (0,1) o (0,-1)
                            if dx != 0: dx = 1 if dx > 0 else -1
                            if dy != 0: dy = 1 if dy > 0 else -1

                            # Inicia un nuevo rebote de una sola casilla
                            self.hit_by_player(dx, dy, grid, bombs, powerups, players, bounce_length=1)
                            return  # La animación de rebote pasa a controlar el desplazamiento.
                        else:
                            # Si es una habilidad, desaparecer inmediatamente
                            p.start_disappear()
                return

        # tramo de la ruta nos encontramos según el tiempo transcurrido
        t_accum = 0
        segment_index = 0
        for i, dur in enumerate(self.hit_bounce_durations):
            if elapsed < t_accum + dur:
                segment_index = i
                break
            t_accum += dur

        # Progreso dentro del tramo actual (entre 0 y 1)
        segment_elapsed = elapsed - t_accum
        segment_duration = self.hit_bounce_durations[segment_index]
        t_seg = max(0, min(1, segment_elapsed / segment_duration))

        # Calcula la posición de inicio y fin (en píxeles) para este tramo
        p_start = self.hit_bounce_pixel_path[segment_index]
        p_end = self.hit_bounce_pixel_path[segment_index + 1]

        dx_px = p_end[0] - p_start[0]
        dy_px = p_end[1] - p_start[1]
        map_width_px = GRID_COLS * TILE_SIZE
        map_height_px = GRID_ROWS * TILE_SIZE

        if abs(dx_px) > map_width_px / 2:
            dx_px += -map_width_px if dx_px > 0 else map_width_px
        if abs(dy_px) > map_height_px / 2:
            dy_px += -map_height_px if dy_px > 0 else map_height_px

        interp_x = p_start[0] + dx_px * t_seg
        interp_y = p_start[1] + dy_px * t_seg

        arc = -self.hit_bounce_height * math.sin(math.pi * t_seg)
        interp_y += arc

        self.pos_x = interp_x - TILE_SIZE / 2
        self.pos_y = interp_y - TILE_SIZE / 2

    def try_start_push(self, dx, dy, grid, bombs, players, powerups):
        if self.sliding:
            return
        path = []
        cx, cy = self.tile_x, self.tile_y
        while True:
            nx, ny = cx + dx, cy + dy
            # Condición de parada 1: bloque
            if nx < 0 or nx >= GRID_COLS or ny < 0 or ny >= GRID_ROWS:
                break
            if grid[ny][nx] in (1, 2, 3):
                break
            # Condición de parada 2: otra bomba
            if any(b.tile_x == nx and b.tile_y == ny and not b.exploded and b != self for b in bombs):
                break
            # Condición de parada 3: powerup/maldición
            if any(p.x == nx and p.y == ny and p.visible for p in powerups):
                break
            # Condición de parada 4: jugador ocupando >25%
            for p in players:
                rect = p.get_hitbox()
                tx = nx * TILE_SIZE
                ty = ny * TILE_SIZE
                tile_rect = pygame.Rect(tx, ty, TILE_SIZE, TILE_SIZE)
                inter = tile_rect.clip(rect)
                if inter.width * inter.height >= (TILE_SIZE * TILE_SIZE * 0.25):
                    break
            else:
                path.append((nx, ny))
                cx, cy = nx, ny
                continue
            break

        if path:
            self.push_path = [(self.tile_x, self.tile_y)] + path
            self.sliding = True
            self.push_index = 0
            self.push_speed = 10 * TILE_SIZE  # píxeles por segundo
            self.push_timer = 0
            self.push_duration = TILE_SIZE / self.push_speed
            self.set_tile_pos(*self.push_path[0])

    def update_push_slide(self):
        if not self.sliding or not self.push_path:
            return
        self.push_timer += 1 / 60
        if self.push_timer >= self.push_duration:
            self.push_timer -= self.push_duration
            self.push_index += 1
            if self.push_index >= len(self.push_path):
                self.sliding = False
                return
            self.set_tile_pos(*self.push_path[self.push_index])

        if self.push_index + 1 < len(self.push_path):
            sx, sy = self.push_path[self.push_index]
            dx, dy = self.push_path[self.push_index + 1]
            prog = self.push_timer / self.push_duration
            px = (sx * (1 - prog) + dx * prog) * TILE_SIZE
            py = (sy * (1 - prog) + dy * prog) * TILE_SIZE
            self.pos_x = px
            self.pos_y = py

    def set_tile_pos(self, tx, ty):
        self.tile_x = tx
        self.tile_y = ty
        self.pos_x = tx * TILE_SIZE
        self.pos_y = ty * TILE_SIZE


# ------------------------------------------------------------------------------------
# Animación y celda lógica de explosión
# ------------------------------------------------------------------------------------
class Explosion:
    def __init__(self, tile_x, tile_y, explosion_type="normal", direction=None, owner=None):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.explosion_type = explosion_type
        self.direction = direction
        self.owner = owner
        self.current_frame = 0
        self.last_update = pygame.time.get_ticks()
        self.finished = False
        if explosion_type == "center":
            self.frames = CENTER_EXPLOSION_FRAMES
            TOTAL_EXPLOSION_TIME = 0.3
            self.frame_duration = TOTAL_EXPLOSION_TIME / len(self.frames)
            self.rotation_angle = 0
        elif explosion_type == "extreme":
            self.frames = EXTREME_EXPLOSION_FRAMES
            TOTAL_EXPLOSION_TIME = 0.3
            self.frame_duration = TOTAL_EXPLOSION_TIME / len(self.frames)
            if direction == (1, 0):
                self.rotation_angle = 90
            elif direction == (0, 1):
                self.rotation_angle = 180
            elif direction == (-1, 0):
                self.rotation_angle = 270
            else:
                self.rotation_angle = 0
        elif explosion_type == "lateral":
            self.frames = LATERAL_EXPLOSION_FRAMES
            TOTAL_EXPLOSION_TIME = 0.3
            self.frame_duration = TOTAL_EXPLOSION_TIME / len(self.frames)
            if direction == (1, 0):
                self.rotation_angle = 90
            elif direction == (0, 1):
                self.rotation_angle = 180
            elif direction == (-1, 0):
                self.rotation_angle = 270
            else:
                self.rotation_angle = 0
        elif explosion_type == "ability":
            self.frames = ABILITY_EXPLOSION_FRAMES
            TOTAL_EXPLOSION_TIME = 0.85
            self.frame_duration = TOTAL_EXPLOSION_TIME / len(self.frames)
            self.rotation_angle = 0
        else:
            self.frame_duration = 0.1
            self.rotation_angle = 0

    def update(self):
        now = pygame.time.get_ticks()
        if not self.finished and (now - self.last_update > self.frame_duration * 1000):
            self.current_frame += 1
            self.last_update = now
            if self.current_frame >= len(self.frames):
                self.finished = True

    def draw(self, surface):
        if not self.finished:
            px = self.tile_x * TILE_SIZE
            py = self.tile_y * TILE_SIZE + TOP_OFFSET

            frame_data = self.frames[self.current_frame]

            # Comprobamos si el frame es un diccionario o una imagen directa
            if isinstance(frame_data, dict):
                frame_image = frame_data.get("image")
            else:
                frame_image = frame_data  # Es directamente una Surface

            # Si por alguna razón no se encuentra la imagen, no hacemos nada para evitar un error.
            if frame_image is None:
                return

            self.current_sprite = frame_data  # guardamos también el nombre para detección

            if self.explosion_type in ("extreme", "lateral") and self.rotation_angle != 0:
                frame_image = pygame.transform.rotate(frame_image, -self.rotation_angle)

            surface.blit(frame_image, (px, py))


# ------------------------------------------------------------------------------------
# Clase Lapida
# ------------------------------------------------------------------------------------
class Lapida:
    def __init__(self, tile_x, tile_y, image):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.image = image
        self.creation_time = time.time()
        self.duration = 10.0  # Durará 10 segundos
        self.state = "active"  # Estados: active, fading
        self.fade_duration = 1.0  # Duración del desvanecimiento
        self.fade_start_time = 0
        self.alpha = 255

    def update(self):
        current_time = time.time()
        # Si han pasado los 10 segundos, empieza a desvanecerse
        if self.state == "active" and current_time - self.creation_time > self.duration:
            self.state = "fading"
            self.fade_start_time = current_time

        # Lógica de la animación de desvanecimiento
        if self.state == "fading":
            elapsed_fade = current_time - self.fade_start_time
            if elapsed_fade >= self.fade_duration:
                self.alpha = 0
            else:
                self.alpha = 255 * (1 - (elapsed_fade / self.fade_duration))

    def is_finished(self):
        return self.alpha <= 0

    def draw(self, surface):
        if self.alpha > 0:
            temp_image = self.image.copy()
            temp_image.set_alpha(self.alpha)
            surface.blit(temp_image, (self.tile_x * TILE_SIZE, self.tile_y * TILE_SIZE + TOP_OFFSET))

    def start_slow_fade(self):
        self.state = "fading"
        self.fade_start_time = time.time()
        self.fade_duration = 3.0  # duración más lenta al contagiar


# ------------------------------------------------------------------------------------
# Animación de habilidades soltadas en el mapa
# ------------------------------------------------------------------------------------
class DroppedAbility:
    def __init__(self, start_pos, image, target_cell, ability_type):
        self.start_x, self.start_y = start_pos
        self.image = image
        self.target_cell = target_cell
        self.ability_type = ability_type

        # Fase inicial: la habilidad sube antes de desplazarse a su celda final.
        self.rise_height = 40  # Píxeles que sube sobre el jugador
        self.rise_duration = 0.4  # Segundos para subir
        self.pos_after_rise = (self.start_x, self.start_y - self.rise_height)

        # Segunda fase: trayectoria en arco hasta la casilla disponible.
        self.arc_duration = 1.1  # Segundos para el arco
        self.target_pos = (
            target_cell[0] * TILE_SIZE + TILE_SIZE // 2,
            target_cell[1] * TILE_SIZE + TILE_SIZE // 2 + TOP_OFFSET
        )

        self.current_pos = start_pos
        self.elapsed = 0
        self.duration = self.rise_duration + self.arc_duration

        self.completed = False
        self.dropped = False

    def update(self, dt, grid, powerups):
        if self.completed:
            return

        self.elapsed += dt

        # --- Lógica de animación ---
        # Fase 1: Subida vertical
        if self.elapsed < self.rise_duration:
            progress = self.elapsed / self.rise_duration
            # Interpola la posición Y para la subida
            self.current_pos = (self.start_x, self.start_y - self.rise_height * progress)
        # Fase 2: Arco parabólico
        else:
            progress = (self.elapsed - self.rise_duration) / self.arc_duration
            progress = min(progress, 1.0)  # Asegura que no pase de 1

            # Interpola X e Y linealmente
            new_x = self.pos_after_rise[0] + (self.target_pos[0] - self.pos_after_rise[0]) * progress
            new_y = self.pos_after_rise[1] + (self.target_pos[1] - self.pos_after_rise[1]) * progress

            # Añade el arco parabólico a la altura
            arc_height = math.sin(math.pi * progress) * 50  # 50px de altura del arco
            new_y -= arc_height

            self.current_pos = (new_x, new_y)

        # --- Final de la animación ---

        if self.elapsed >= self.duration:
            self.current_pos = self.target_pos
            self.completed = True
            if not self.dropped:
                # Comprueba si la celda sigue libre, si no, busca otra
                available = get_available_free_cells(grid, powerups)
                if self.target_cell not in available:
                    if available:
                        self.target_cell = random.choice(available)

                # Crea el PowerUp final
                new_powerup = PowerUp(self.target_cell[0], self.target_cell[1], self.ability_type)
                new_powerup.visible = True
                powerups.append(new_powerup)
                self.dropped = True

    def draw(self, surface):
        # Escala la imagen a medida que avanza la animación
        progress = self.elapsed / self.duration

        # Empieza pequeña y crece hasta el tamaño normal
        scale_factor = 0.1 + 0.9 * min(progress, 1.0)

        img_size = int(TILE_SIZE * scale_factor)
        if img_size <= 0: return

        scaled_img = pygame.transform.scale(self.image, (img_size, img_size))
        rect = scaled_img.get_rect(center=self.current_pos)
        surface.blit(scaled_img, rect)


# ------------------------------------------------------------------------------------
# Funciones auxiliares para celdas libres
# ------------------------------------------------------------------------------------
def get_available_free_cells(grid, powerups):
    cells = []
    for y in range(1, GRID_ROWS - 1):
        for x in range(1, GRID_COLS - 1):
            if grid[y][x] == 0:
                if not any(p.x == x and p.y == y and p.visible for p in powerups):
                    cells.append((x, y))
    return cells


def get_free_cells(grid):
    cells = []
    for y in range(1, GRID_ROWS - 1):
        for x in range(1, GRID_COLS - 1):
            if grid[y][x] == 0:
                cells.append((x, y))
    return cells


def find_free_cell_far_from(player, grid):
    player_tile = player.get_center_tile()
    free_cells = get_free_cells(grid)
    if free_cells:
        far_cell = max(free_cells, key=lambda cell: math.hypot(cell[0] - player_tile[0], cell[1] - player_tile[1]))
        return far_cell
    return player_tile


dropped_abilities = []


def trigger_reset_effect(player, grid, powerups, dropped_abilities):
    print(f"¡Jugador {player.player_index + 1} ha activado la maldición de RESET!")

    abilities_to_drop = []
    # Contar las habilidades y poderes que tiene el jugador
    ability_images = {
        "speed": SPEED_IMG,
        "more_bomb": MORE_BOMB_IMG,
        "major_explosion": MAYOR_EXPLOSION_IMG,
        "push_bomb": PUSH_BOMB_IMG,
        "golpear_bombas": PUÑO_IMG,
        "escudo": ESCUDO_IMG
    }

    # Habilidades acumulables
    for _ in range(player.display_speed - 1): abilities_to_drop.append("speed")
    for _ in range(player.bomb_limit - 1): abilities_to_drop.append("more_bomb")
    for _ in range(player.bomb_range - 1): abilities_to_drop.append("major_explosion")

    # Poderes (no acumulables)
    if player.push_bomb_available: abilities_to_drop.append("push_bomb")
    if player.hit_bomb_available: abilities_to_drop.append("golpear_bombas")
    if player.escudo_available: abilities_to_drop.append("escudo")

    if not abilities_to_drop:
        return  # No hacer nada si no hay nada que resetear

    # Resetear las estadísticas del jugador a los valores iniciales
    player.base_speed -= (player.display_speed - 1)
    player.speed = player.base_speed
    player.display_speed = 1
    player.bomb_limit = 1
    player.bomb_range = 1
    player.push_bomb_available = False
    player.hit_bomb_available = False
    player.escudo_available = False
    player.escudo_active = False  # También desactiva el escudo si estaba activo

    # Encontrar casillas libres para soltar los objetos
    player_tile = player.get_center_tile()
    all_free_cells = get_available_free_cells(grid, powerups)

    # Filtra las celdas para que estén a una distancia mínima del jugador
    min_distance = 3
    far_cells = [
        cell for cell in all_free_cells
        if math.hypot(cell[0] - player_tile[0], cell[1] - player_tile[1]) > min_distance
    ]

    # Si no hay suficientes celdas lejanas, usa cualquiera que esté libre
    if len(far_cells) < len(abilities_to_drop):
        far_cells = all_free_cells

    random.shuffle(far_cells)

    # Iniciar una animación de caída por cada habilidad/poder
    player_start_pos = (
        player.x + player.sprite_size // 2,
        player.y + player.sprite_draw_offset_y + TOP_OFFSET + player.sprite_size // 2
    )

    for i, ability_type in enumerate(abilities_to_drop):
        if not far_cells: break  # No hay más celdas libres

        target_cell = far_cells.pop()
        image = ability_images.get(ability_type)

        if image:
            drop_anim = DroppedAbility(player_start_pos, image, target_cell, ability_type)
            dropped_abilities.append(drop_anim)


# ------------------------------------------------------------------------------------
# Función generate_grid_and_powerups
# ------------------------------------------------------------------------------------
def check_pickup(players, powerups, lapidas):
    powerups_to_remove = []

    for p in powerups:
        if not (p.visible and not p.disappearing and not p.bouncing):
            continue

        powerup_rect = pygame.Rect(p.x * TILE_SIZE, p.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

        for player in players:
            if player.is_ghost:
                continue

            player_hitbox = player.get_hitbox()

            if player_hitbox.colliderect(powerup_rect):
                # --- LÓGICA DE RECOGIDA DE MALDICIONES ---
                if p.type == "calavera":
                    COGER_MALDICION_SOUND.play()

                    standard_curses = ["no_ability", "no_bomb", "auto_bomb", "inverted", "hyper_speed", "slow_speed"]
                    has_upgrades = (player.bomb_limit > 1 or
                                    player.bomb_range > 1 or
                                    player.display_speed > 1 or
                                    player.push_bomb_available or
                                    player.hit_bomb_available or
                                    player.escudo_available)

                    curse_to_apply = ""
                    if has_upgrades:
                        all_curses = standard_curses + ["reset"]
                        curse_to_apply = random.choice(all_curses)
                    else:
                        curse_to_apply = random.choice(standard_curses)

                    player.apply_curse(curse_to_apply)
                    powerups_to_remove.append(p)
                    break

                # --- LÓGICA DE RECOGIDA DE HABILIDADES Y PODERES ---
                else:
                    if not player.can_pick_abilities:
                        continue

                    COGER_HABILIDAD_SOUND.play()

                    if p.type == "speed":
                        # Si el jugador está bajo una maldición de velocidad...
                        if player.active_curse in ("hyper_speed", "slow_speed"):
                            player.pending_speed_boosts += 1.0
                            player.display_speed += 1  # Actualizamos el HUD para que el jugador vea que la recogió.
                        else:
                            # Si no hay maldición de velocidad, se aplica directamente.
                            player.base_speed += 1.0
                            player.speed = player.base_speed
                            player.display_speed += 1

                    elif p.type == "more_bomb":
                        player.bomb_limit += 1
                    elif p.type == "major_explosion":
                        player.bomb_range += 1
                    elif p.type == "push_bomb":
                        player.push_bomb_available = True
                    elif p.type == "golpear_bombas":
                        player.hit_bomb_available = True
                    elif p.type == "escudo":
                        player.escudo_available = True

                    powerups_to_remove.append(p)
                    break

    for item in powerups_to_remove:
        if item in powerups:
            powerups.remove(item)

    # Las lápidas activas conceden maldiciones al primer jugador vivo que las pisa.
    for lapida in lapidas:
        if lapida.state != "active":
            continue

        lapida_rect = pygame.Rect(lapida.tile_x * TILE_SIZE, lapida.tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

        for player in players:
            if player.is_ghost:
                continue
            if player.get_hitbox().colliderect(lapida_rect):
                COGER_MALDICION_SOUND.play()
                standard_curses = ["no_ability", "no_bomb", "auto_bomb", "inverted", "hyper_speed", "slow_speed"]
                has_upgrades = (player.bomb_limit > 1 or player.bomb_range > 1 or player.display_speed > 1 or
                                player.push_bomb_available or player.hit_bomb_available or player.escudo_available)

                if has_upgrades:
                    all_curses = standard_curses + ["reset"]
                    curse_name = random.choice(all_curses)
                else:
                    curse_name = random.choice(standard_curses)

                player.apply_curse(curse_name)
                lapida.start_slow_fade()
                break


def generate_grid_and_powerups():
    grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    powerups = []
    num_jugadores = len(gestor_jugadores.todos())
    probabilidad_por_jugadores = {
        2: 0.40,  # 40% de probabilidad para 2 jugadores
        3: 0.50,  # 50% de probabilidad para 3 jugadores
        4: 0.60  # 60% de probabilidad para 4 jugadores
    }
    prob_total_habilidad = probabilidad_por_jugadores.get(num_jugadores, 0.30)
    for x in range(GRID_COLS):
        grid[0][x] = 3
        grid[GRID_ROWS - 1][x] = 3
    for y in range(GRID_ROWS):
        grid[y][0] = 3
        grid[y][GRID_COLS - 1] = 3
    for y in range(1, GRID_ROWS - 1):
        for x in range(1, GRID_COLS - 1):
            grid[y][x] = 0
    for y in range(1, GRID_ROWS - 1):
        for x in range(1, GRID_COLS - 1):
            if (x % 2 == 0) and (y % 2 == 0):
                grid[y][x] = 2
    for y in range(1, GRID_ROWS - 1):
        for x in range(1, GRID_COLS - 1):
            if grid[y][x] == 0:
                if random.random() < 0.7:
                    grid[y][x] = 1
                    if random.random() < prob_total_habilidad:
                        r_tipo = random.random()

                        if r_tipo < 0.40:  # 40% de ser "mayor_explosion"
                            powerups.append(PowerUp(x, y, "major_explosion"))
                        elif r_tipo < 0.75:  # 25% de ser "more_bomb"
                            powerups.append(PowerUp(x, y, "more_bomb"))
                        elif r_tipo < 0.80:  # 20%
                            powerups.append(PowerUp(x, y, "speed"))
                        elif r_tipo < 0.90:  # 10%
                            if config.current_ultimas_index.get("Maldiciones", 0) == 0:
                                powerups.append(PowerUp(x, y, "calavera"))
                        else:  # 5%
                            power_choice = random.choice(["push_bomb", "golpear_bombas", "escudo"])
                            powerups.append(PowerUp(x, y, power_choice))
    if grid[1][1] != 2:
        grid[1][1] = 0
    if grid[1][2] != 2:
        grid[1][2] = 0
    if grid[2][1] != 2:
        grid[2][1] = 0
    if grid[2][2] != 2:
        grid[2][2] = 1
    if grid[1][GRID_COLS - 2] != 2:
        grid[1][GRID_COLS - 2] = 0
    if grid[1][GRID_COLS - 3] != 2:
        grid[1][GRID_COLS - 3] = 0
    if grid[2][GRID_COLS - 2] != 2:
        grid[2][GRID_COLS - 2] = 0
    if grid[2][GRID_COLS - 3] != 2:
        grid[2][GRID_COLS - 3] = 1
    if grid[GRID_ROWS - 2][1] != 2:
        grid[GRID_ROWS - 2][1] = 0
    if grid[GRID_ROWS - 2][2] != 2:
        grid[GRID_ROWS - 2][2] = 0
    if grid[GRID_ROWS - 3][1] != 2:
        grid[GRID_ROWS - 3][1] = 0
    if grid[GRID_ROWS - 3][2] != 2:
        grid[GRID_ROWS - 3][2] = 1
    if grid[GRID_ROWS - 2][GRID_COLS - 2] != 2:
        grid[GRID_ROWS - 2][GRID_COLS - 2] = 0
    if grid[GRID_ROWS - 2][GRID_COLS - 3] != 2:
        grid[GRID_ROWS - 2][GRID_COLS - 3] = 0
    if grid[GRID_ROWS - 3][GRID_COLS - 2] != 2:
        grid[GRID_ROWS - 3][GRID_COLS - 2] = 0
    if grid[GRID_ROWS - 3][GRID_COLS - 3] != 2:
        grid[GRID_ROWS - 3][GRID_COLS - 3] = 1
    forced_bricks = [(4, 1), (3, 2), (2, 3), (1, 4),
                     (4, 15), (3, 14), (2, 13), (1, 12),
                     (19, 4), (18, 3), (17, 2), (16, 1),
                     (16, 15), (17, 14), (18, 13), (19, 12)]
    for (fx, fy) in forced_bricks:
        grid[fy][fx] = 1
    return grid, powerups


def draw_grid(surface, grid, SUELO1, SUELO2, STONE, BRICK, LIMIT_IMG):
    current_time = time.time()
    # Dibujar el suelo en todas las casillas de forma alternada
    for y in range(GRID_ROWS):
        for x in range(GRID_COLS):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE + TOP_OFFSET, TILE_SIZE, TILE_SIZE)
            if (x + y) % 2 == 0:
                surface.blit(SUELO1, rect)
            else:
                surface.blit(SUELO2, rect)
    # Dibujar los elementos del grid por encima
    for y in range(GRID_ROWS):
        for x in range(GRID_COLS):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE + TOP_OFFSET, TILE_SIZE, TILE_SIZE)
            if grid[y][x] == 1:
                if (x, y) in exploding_blocks:
                    elapsed = current_time - exploding_blocks[(x, y)]
                    if elapsed < EXPLOSION_DURATION:
                        temp = BRICK.copy()
                        temp.fill((255, 165, 0), special_flags=pygame.BLEND_RGB_MULT)
                        alpha = int(255 * (1 - (elapsed / EXPLOSION_DURATION)))
                        temp.set_alpha(alpha)
                        surface.blit(temp, rect)
                    else:
                        grid[y][x] = 0
                        del exploding_blocks[(x, y)]
                        # No se dibuja nada, ya se ve el suelo debajo
                else:
                    surface.blit(BRICK, rect)
            elif grid[y][x] == 2:
                surface.blit(STONE, rect)
            elif grid[y][x] == 3:
                surface.blit(LIMIT_IMG, rect)
            elif grid[y][x] == 4:
                surface.blit(BLOQUE_FINAL_IMG, rect)


def draw_grid_lines(surface):
    overlay = pygame.Surface((GRID_WIDTH, HEIGHT), pygame.SRCALPHA)
    line_color = (0, 0, 0, 80)
    for row in range(GRID_ROWS + 1):
        start = (0, row * TILE_SIZE + TOP_OFFSET)
        end = (GRID_WIDTH, row * TILE_SIZE + TOP_OFFSET)
        pygame.draw.line(overlay, line_color, start, end, 1)
    for col in range(GRID_COLS + 1):
        start = (col * TILE_SIZE, TOP_OFFSET)
        end = (col * TILE_SIZE, GRID_ROWS * TILE_SIZE + TOP_OFFSET)
        pygame.draw.line(overlay, line_color, start, end, 1)
    surface.blit(overlay, (0, 0))


def draw_curse_info(surface, player, color, pos):
    x, y = pos
    if getattr(player, 'active_curse', None) and getattr(player, 'curse_ends_at', None):
        duration = CURSES[player.active_curse]['duration']
        if duration is not None:
            remaining = max(0, int(player.curse_ends_at - time.time()))
            text = f"{player.active_curse}: {remaining}s"
        else:
            text = "No curse"
    else:
        text = "No curse"
    surface.blit(font.render(text, True, color), (x, y))


# CONDICION POSICION FIJA O ALEATORIA
def obtener_posiciones_aleatorias(num_players):
    # Esquinas interiores seguras (no borde del mapa)
    esquinas = [
        (1, 1),
        (GRID_COLS - 2, GRID_ROWS - 2),
        (1, GRID_ROWS - 2),
        (GRID_COLS - 2, 1),
    ]
    random.shuffle(esquinas)
    return esquinas[:num_players]


# Obtener el modo desde la configuración
modo_posicion = config.current_position_index  # 0 = fija, 1 = aleatoria


def generar_ruta_espiral(): # para los bloques final
    ruta = []
    min_x, max_x = 0, GRID_COLS - 1
    min_y, max_y = 0, GRID_ROWS - 1

    while min_x <= max_x and min_y <= max_y:

        # --- TRAMO 1: Subir por la columna izquierda (INICIO) ---
        for y in range(max_y, min_y - 1, -1):
            ruta.append((min_x, y))
        min_x += 1
        if min_x > max_x: break

        # --- TRAMO 2: Derecha por la fila superior ---
        for x in range(min_x, max_x + 1):
            ruta.append((x, min_y))
        min_y += 1
        if min_y > max_y: break

        # --- TRAMO 3: Bajar por la columna derecha ---
        for y in range(min_y, max_y + 1):
            ruta.append((max_x, y))
        max_x -= 1
        if min_x > max_x: break

        # --- TRAMO 4: Izquierda por la fila inferior ---
        for x in range(max_x, min_x - 1, -1):
            ruta.append((x, max_y))
        max_y -= 1
        if min_y > max_y: break

    return ruta


# funcion para animacion mensajes antes de iniciar partida
def draw_animated_text(screen, image, start_time, duration=2.0, max_opacity=0.8):
    if not image:
        return time.time() - start_time > duration

    elapsed = time.time() - start_time
    if elapsed >= duration:
        return True  # La animación ha terminado

    fade_in_time = 0.25
    fade_out_time = 0.50

    alpha = 255 * max_opacity

    if elapsed < fade_in_time:
        alpha *= (elapsed / fade_in_time)
    elif elapsed > duration - fade_out_time:
        alpha *= (duration - elapsed) / fade_out_time

    temp_img = image.copy()
    temp_img.set_alpha(int(max(0, alpha)))

    img_rect = temp_img.get_rect(center=(screen.get_width() / 2, screen.get_height() / 2))
    screen.blit(temp_img, img_rect)

    return False


def check_curse_transmission(players, cooldown_set):
    """Comprueba colisiones entre jugadores y transmite maldiciones."""

    # Gestionar colisiones y transmisiones
    # Usamos itertools.combinations para obtener cada par de jugadores una sola vez
    for player1, player2 in combinations(players, 2):
        # Ignorar si alguno de los jugadores está eliminado, es fantasma o invulnerable
        if player1.is_eliminated or player1.is_ghost or player2.is_eliminated or player2.is_ghost or player1.is_invulnerable or player2.is_invulnerable:
            continue

        # Crear una clave única para el par de jugadores
        pair_key = tuple(sorted((player1.player_index, player2.player_index)))

        # Comprobar si hay colisión de hitboxes
        if player1.get_hitbox().colliderect(player2.get_hitbox()):
            # Si el par ya está en cooldown, no hacer nada
            if pair_key in cooldown_set:
                continue

            # Solo se intercambian maldiciones marcadas como transmisibles.
            p1_curse = player1.active_curse
            p2_curse = player2.active_curse
            p1_transmittable = p1_curse and CURSES[p1_curse].get("transmittable", False)
            p2_transmittable = p2_curse and CURSES[p2_curse].get("transmittable", False)

            if not p1_transmittable and not p2_transmittable:
                continue

            print(
                f"¡Transmisión de maldición entre Jugador {player1.player_index + 1} y Jugador {player2.player_index + 1}!")

            p1_ends_at = player1.curse_ends_at
            p2_ends_at = player2.curse_ends_at

            player1.receive_transmitted_curse(p2_curse, p2_ends_at)
            player2.receive_transmitted_curse(p1_curse, p1_ends_at)

            # Evita que dos jugadores intercambien la misma maldición en cada frame mientras se tocan.
            cooldown_set.add(pair_key)

        else:
            if pair_key in cooldown_set:
                cooldown_set.remove(pair_key)

# ------------------------------------------------------------------------------------
# Bucle principal
# ------------------------------------------------------------------------------------
def iniciar_partida(screen):
    # Carga configuración, recursos y estado inicial de la partida.
    screen = crear_pantalla_completa()
    ocultar_cursor_partida()
    MUSIC_PATH = os.path.join(ASSETS_DIR, "Sonidos_juego", "musica_fondo", "juego.mp3")
    pygame.mixer.music.load(MUSIC_PATH)
    pygame.mixer.music.set_volume(audio.volume)
    pygame.mixer.music.play(-1)
    try:
        DATE_PRISA_IMG = pygame.image.load(
            os.path.join(ASSETS_DIR, "Textos", "date prisa.png")).convert_alpha()
        DATE_PRISA_SOUND = pygame.mixer.Sound(
            os.path.join(ASSETS_DIR, "Sonidos_juego", "Partida", "date prisa.mp3"))
        DATE_PRISA_SOUND.set_volume(0.5)
    except pygame.error as e:
        print(f"Error al cargar recursos 'Date Prisa': {e}")
        DATE_PRISA_IMG = None
        DATE_PRISA_SOUND = None

    try:
        PREPARADOS_IMG = pygame.image.load(
            os.path.join(ASSETS_DIR, "Textos", "preparados.png")).convert_alpha()
        ADELANTE_IMG = pygame.image.load(
            os.path.join(ASSETS_DIR, "Textos", "adelante.png")).convert_alpha()
        PREPARADOS_SOUND = pygame.mixer.Sound(
            os.path.join(ASSETS_DIR, "Sonidos_juego", "Partida", "preparados.mp3"))
        ADELANTE_SOUND = pygame.mixer.Sound(
            os.path.join(ASSETS_DIR, "Sonidos_juego", "Partida", "adelante.mp3"))
        PREPARADOS_SOUND.set_volume(0.5)
        ADELANTE_SOUND.set_volume(0.5)
    except pygame.error as e:
        print(f"Error al cargar recursos de inicio de ronda: {e}")
        PREPARADOS_IMG = None
        ADELANTE_IMG = None
        PREPARADOS_SOUND = None
        ADELANTE_SOUND = None

    try:
        GANADOR_SET_IMG = pygame.image.load(os.path.join(ASSETS_DIR, "Textos", "ganador_set.png")).convert_alpha()
        GANADOR_PARTIDA_IMG = pygame.image.load(
            os.path.join(ASSETS_DIR, "Textos", "ganador_partida.png")).convert_alpha()
        JUGADOR_VICTORIA_IMGS = [
            pygame.image.load(os.path.join(ASSETS_DIR, "Textos", "jugador", f"j{i}.png")).convert_alpha()
            for i in range(1, 5)
        ]
        GANADOR_SET_SOUND = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "Sonidos_juego", "Partida", "ganador set.mp3"))
        GANADOR_PARTIDA_SOUND = pygame.mixer.Sound(
            os.path.join(ASSETS_DIR, "Sonidos_juego", "Partida", "ganador partida.mp3"))

        SET_FINALIZADO_IMG = pygame.image.load(os.path.join(ASSETS_DIR, "Textos", "set_finalizado.png")).convert_alpha()
        EMPATE_IMG = pygame.image.load(os.path.join(ASSETS_DIR, "Textos", "empate.png")).convert_alpha()

    except pygame.error as e:
        print(f"ADVERTENCIA: No se pudieron cargar las imágenes o sonidos de victoria: {e}")
        GANADOR_SET_IMG = None
        GANADOR_PARTIDA_IMG = None
        JUGADOR_VICTORIA_IMGS = []
        GANADOR_SET_SOUND = None
        GANADOR_PARTIDA_SOUND = None
        SET_FINALIZADO_IMG = None
        EMPATE_IMG = None

    global players


    players = []
    color_pool = [RED, BLUE, (0, 255, 0), (255, 255, 0)]

    # --- NUEVO: LISTA PARA LOS CEREBROS DE LA IA ---
    cerebros_ia = []
    # -----------------------------------------------

    for idx, jugador in enumerate(gestor_jugadores.todos()):
        if idx >= len(posiciones_iniciales): break
        tipo = jugador.get("tipo")
        personaje_idx = jugador.get("indice", 0)
        tile_x, tile_y = posiciones_iniciales[idx]
        color = color_pool[idx % len(color_pool)]

        if tipo == "teclado":
            controls = controles_teclado
        elif tipo == "mando":
            controls = {"instance_id": jugador["instance_id"]}
        elif tipo == "cpu":  # <--- NUEVO: DEJAMOS PASAR A LA CPU
            controls = {"cpu": True}  # Le damos unos controles virtuales
        else:
            continue

        nombre_personaje = nombres_por_indice.get(personaje_idx, "Mork")
        animaciones = cargar_animaciones_personaje(nombre_personaje)
        portrait_image = None
        try:
            portrait_path = os.path.join(ASSETS_DIR, "Jugadores", "Dibujos", f"{nombre_personaje}.png")
            portrait_full_size = pygame.image.load(portrait_path).convert_alpha()
            portrait_image = pygame.transform.scale(portrait_full_size, (110, 110))
        except pygame.error as e:
            print(f"ADVERTENCIA: No se pudo cargar el retrato para {nombre_personaje}: {e}")
            portrait_image = pygame.Surface((80, 80))
            portrait_image.fill((50, 50, 50))

        nuevo_jugador = Player(tile_x, tile_y, color, controls)
        nuevo_jugador.animaciones = animaciones
        nuevo_jugador.portrait_image = portrait_image
        nuevo_jugador.player_index = idx
        nuevo_jugador.ghost_animations = cargar_animaciones_fantasma_por_direccion(idx)
        players.append(nuevo_jugador)

        # --- NUEVO: ASIGNAR EL CEREBRO A LA CPU ---
        if tipo == "cpu":
            from IA_CPU import CerebroCPU  # Importamos la IA aquí por seguridad

            nuevo_cerebro = CerebroCPU(jugador["id_jugador"])
            cerebros_ia.append((nuevo_cerebro, nuevo_jugador))
            nuevo_jugador.cerebro_ia = nuevo_cerebro
        # ------------------------------------------

    scoreboard_images = {}
    sets_to_win_value = config.set_options[config.current_set_index]
    for p_idx in range(len(gestor_jugadores.todos())):
        scoreboard_images[p_idx] = {}
        folder_path = os.path.join(ASSETS_DIR, "Marcadores", f"Jugador {p_idx + 1}", f"{sets_to_win_value} set")
        if os.path.isdir(folder_path):
            for i in range(sets_to_win_value + 2):
                img_path = os.path.join(folder_path, f"{i}.png")
                if os.path.isfile(img_path):
                    try:
                        scoreboard_images[p_idx][i] = pygame.image.load(img_path).convert_alpha()
                    except pygame.error as e:
                        print(f"Error al cargar la imagen del marcador {img_path}: {e}")

    global grid, powerups, bombs, explosions, lapidas, lapida_por_colocar, exploding_blocks, dropped_abilities
    sets_to_win = config.set_options[config.current_set_index]
    usar_fantasmas = config.current_ultimas_index.get("Fantasmas", 0) == 0
    SUELO1, SUELO2, STONE, BRICK, LIMIT_IMG = cargar_mapa()
    for p in players: p.sets_won = 0
    map_backgrounds = {1: "fondo_clasico.gif", 2: "fondo_desierto.gif", 3: "fondo_jungla.gif"}
    selected_map_num = config.selected_map
    gif_filename = map_backgrounds.get(selected_map_num, "fondo_clasico.gif")
    gif_path = os.path.join(ASSETS_DIR, "Mapas", f"Mapa{selected_map_num}", gif_filename)
    background_gif = AnimatedBackground(gif_path, (WIDTH, HEIGHT))

    match_running = True
    match_winner = None
    bloques_finales_activados = config.current_ultimas_index.get("Bloques_final", 1) == 0
    ruta_espiral = []
    final_blocks = []
    tiempo_por_bloque = 0
    proximo_bloque_idx = 0
    temporizador_caida_bloque = 0.0

    if bloques_finales_activados:
        ruta_espiral = generar_ruta_espiral()
        if ruta_espiral: tiempo_por_bloque = 55.0 / len(ruta_espiral)
    curse_transmission_cooldown_pairs = set()
    while match_running:
        grid, powerups = generate_grid_and_powerups()
        final_blocks.clear()
        proximo_bloque_idx = 0
        temporizador_caida_bloque = 0.0
        bombs, explosions, lapidas, dropped_abilities = [], [], [], []
        lapida_por_colocar = None
        exploding_blocks = {}
        if config.current_position_index == 1:
            set_positions = obtener_posiciones_aleatorias(len(players))
        else:
            set_positions = posiciones_iniciales[:len(players)]
        for i, player in enumerate(players):
            x, y = set_positions[i]
            player.reset_for_new_set(x, y)
        estado_set = "preparados"
        tiempo_anim_texto = time.time()
        if PREPARADOS_SOUND: PREPARADOS_SOUND.play()

        start_time = 0
        TOTAL_TIME = config.current_minute * 60
        set_winner = None
        set_end_sequence_start_time = None
        hurry_up_mode_activated = False
        date_prisa_anim_start_time = None
        clock = pygame.time.Clock()

        set_running = True
        while set_running:
            dt = clock.tick(60) / 1000.0
            if dt > 0.1: dt = 1 / 60.0

            if start_time > 0:
                remaining_time = max(0, TOTAL_TIME - (time.time() - start_time))
            else:
                remaining_time = TOTAL_TIME

            if start_time > 0 and remaining_time <= 60 and not hurry_up_mode_activated:
                hurry_up_mode_activated = True
                date_prisa_anim_start_time = time.time()
                if DATE_PRISA_SOUND: DATE_PRISA_SOUND.play()
                for player in players:
                    if player.is_ghost: player.eliminate(); print(
                        f"El fantasma del jugador {player.player_index + 1} ha desaparecido.")

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
                    ocultar_cursor_partida()
                should_pause = False
                pause_instance_id = "teclado"
                if estado_set == "jugando":
                    if evento_ventana_inactiva(event):
                        should_pause = True
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        should_pause = True
                        pause_instance_id = "teclado"
                    elif event.type == pygame.JOYBUTTONDOWN and event.button in (7, 9):
                        should_pause = True
                        pause_instance_id = event.instance_id
                if should_pause:
                    musica_activa = pygame.mixer.get_init() is not None and pygame.mixer.music.get_busy()
                    if musica_activa:
                        pygame.mixer.music.pause()
                    pygame.mixer.pause()
                    time_before_pause_sec = time.time()
                    ticks_before_pause_ms = pygame.time.get_ticks()
                    resultado = menu_pausa(screen, pause_instance_id, screen.copy())
                    ocultar_cursor_partida()
                    if musica_activa:
                        pygame.mixer.music.unpause()
                    pygame.mixer.unpause()
                    if resultado == "Salir de la partida": pygame.mixer.music.stop(); FANTASMA_SOUND.stop(); return
                    pause_duration_sec = time.time() - time_before_pause_sec
                    pause_duration_ms = pygame.time.get_ticks() - ticks_before_pause_ms
                    if start_time > 0: start_time += pause_duration_sec
                    if date_prisa_anim_start_time: date_prisa_anim_start_time += pause_duration_sec
                    if tiempo_anim_texto: tiempo_anim_texto += pause_duration_sec
                    for p in players:
                        if p.active_curse and p.curse_ends_at: p.curse_ends_at += pause_duration_sec
                        if p.escudo_cooldown_end_time > 0: p.escudo_cooldown_end_time += pause_duration_sec
                        if p.escudo_active: p.escudo_activation_time += pause_duration_sec
                        if p.is_ghost and p.last_bomb_placed_time > 0: p.last_bomb_placed_time += pause_duration_sec
                        if p.is_invulnerable: p.invulnerable_until += pause_duration_sec
                        if p.is_set_winner: p.set_winner_start_time += pause_duration_sec
                        if p.flashing: p.flash_timer += pause_duration_sec
                        p.last_step_sound += pause_duration_sec
                        p.last_anim_update += pause_duration_sec
                        p.last_ghost_sound_time += pause_duration_sec
                        if p.is_ghost: p.last_ghost_anim_update += pause_duration_ms
                    for b in bombs:
                        b.plant_time += pause_duration_sec
                        if b.chain_trigger_time: b.chain_trigger_time += pause_duration_sec
                        if b.timer_frozen and b.freeze_start_time: b.freeze_start_time += pause_duration_sec
                        if b.hit_bouncing: b.hit_bounce_start_time += pause_duration_ms
                    for l in lapidas:
                        l.creation_time += pause_duration_sec
                        if l.fade_start_time > 0: l.fade_start_time += pause_duration_sec
                    for key in list(exploding_blocks.keys()): exploding_blocks[key] += pause_duration_sec
                    for e in explosions: e.last_update += pause_duration_ms
                    for p in powerups:
                        if p.disappearing: p.last_update += pause_duration_ms
                    continue

                if estado_set == "jugando" and not set_end_sequence_start_time:
                    if event.type == pygame.KEYDOWN:
                        for player in players:
                            if "up" in player.controls and event.key == pygame.K_o: player.activate_escudo()
                            if 'bomb' in player.controls and event.key == player.controls['bomb']:
                                player.place_bomb(bombs, powerups, grid, lapidas)
                            elif 'hit' in player.controls and event.key == player.controls['hit']:
                                if player.hit_bomb_available:
                                    dx, dy = (0, -1) if player.current_direction == "up" else (
                                    0, 1) if player.current_direction == "down" else (
                                    -1, 0) if player.current_direction == "left" else (1, 0)
                                    bomba_golpeada = False
                                    player_tile_x, player_tile_y = player.get_center_tile()
                                    for b in bombs:
                                        if b.tile_x == player_tile_x and b.tile_y == player_tile_y and not b.hit_bouncing and not b.sliding: b.hit_by_player(
                                            dx, dy, grid, bombs, powerups, players); bomba_golpeada = True; break
                                    if not bomba_golpeada:
                                        front_tile_x = player_tile_x + dx
                                        front_tile_y = player_tile_y + dy
                                        for b in bombs:
                                            if b.tile_x == front_tile_x and b.tile_y == front_tile_y and not b.hit_bouncing and not b.sliding: b.hit_by_player(
                                                dx, dy, grid, bombs, powerups, players); break
                    elif event.type == pygame.JOYBUTTONDOWN:
                        for player in players:
                            if 'instance_id' in player.controls and getattr(event, "instance_id", event.joy) == \
                                    player.controls['instance_id']:
                                if event.button == 0:
                                    player.place_bomb(bombs, powerups, grid, lapidas)
                                elif event.button == 1 and player.hit_bomb_available:
                                    dx, dy = (0, -1) if player.current_direction == "up" else (
                                    0, 1) if player.current_direction == "down" else (
                                    -1, 0) if player.current_direction == "left" else (1, 0)
                                    bomba_golpeada = False
                                    player_tile_x, player_tile_y = player.get_center_tile()
                                    for b in bombs:
                                        if b.tile_x == player_tile_x and b.tile_y == player_tile_y and not b.hit_bouncing and not b.sliding: b.hit_by_player(
                                            dx, dy, grid, bombs, powerups, players); bomba_golpeada = True; break
                                    if not bomba_golpeada:
                                        front_tile_x = player_tile_x + dx
                                        front_tile_y = player_tile_y + dy
                                        for b in bombs:
                                            if b.tile_x == front_tile_x and b.tile_y == front_tile_y and not b.hit_bouncing and not b.sliding: b.hit_by_player(
                                                dx, dy, grid, bombs, powerups, players); break
                                elif event.button == 2:
                                    player.activate_escudo()

            if estado_set == "jugando":
                check_curse_transmission(players, curse_transmission_cooldown_pairs)
                keys = pygame.key.get_pressed()
                player_list_to_update = [set_winner] if set_end_sequence_start_time and set_winner else players
                for player in player_list_to_update:
                    if set_end_sequence_start_time and player != set_winner: continue
                    if player.is_eliminated: continue
                    if player.is_invulnerable and time.time() > player.invulnerable_until: player.is_invulnerable = False

                    # --- 1. LÓGICA DE LA CPU ---
                    if hasattr(player, 'cerebro_ia') and player.cerebro_ia is not None:
                        # El cerebro analiza el entorno y devuelve un diccionario de botones pulsados
                        inputs_cpu = player.cerebro_ia.pensar(player, grid, bombs, players)

                        if inputs_cpu.get("up"):
                            player.move("up", grid, bombs, powerups, lapidas)
                        elif inputs_cpu.get("down"):
                            player.move("down", grid, bombs, powerups, lapidas)
                        elif inputs_cpu.get("left"):
                            player.move("left", grid, bombs, powerups, lapidas)
                        elif inputs_cpu.get("right"):
                            player.move("right", grid, bombs, powerups, lapidas)

                        if inputs_cpu.get("bomb"):
                            player.place_bomb(bombs, powerups, grid, lapidas)

                        # --- 2. LÓGICA DEL TECLADO ---
                    elif 'up' in player.controls:
                        if keys[player.controls['up']]:
                            player.move("up", grid, bombs, powerups, lapidas)
                        elif keys[player.controls['down']]:
                            player.move("down", grid, bombs, powerups, lapidas)
                        elif keys[player.controls['left']]:
                            player.move("left", grid, bombs, powerups, lapidas)
                        elif keys[player.controls['right']]:
                            player.move("right", grid, bombs, powerups, lapidas)
                    elif "instance_id" in player.controls and player.controls.get("active", True):
                        joy = get_joystick_by_instance_id(player.controls["instance_id"])
                        if joy:
                            dx, dy, hat_x, hat_y = joy.get_axis(0), joy.get_axis(1), joy.get_hat(0)[0], joy.get_hat(0)[
                                1]
                            if hat_x == -1:
                                player.move("left", grid, bombs, powerups, lapidas)
                            elif hat_x == 1:
                                player.move("right", grid, bombs, powerups, lapidas)
                            elif hat_y == 1:
                                player.move("up", grid, bombs, powerups, lapidas)
                            elif hat_y == -1:
                                player.move("down", grid, bombs, powerups, lapidas)
                            elif abs(dx) > 0.3 or abs(dy) > 0.3:
                                if abs(dx) > abs(dy):
                                    if dx > 0.3:
                                        player.move("right", grid, bombs, powerups, lapidas)
                                    else:
                                        player.move("left", grid, bombs, powerups, lapidas)
                                else:
                                    if dy > 0.3:
                                        player.move("down", grid, bombs, powerups, lapidas)
                                    else:
                                        player.move("up", grid, bombs, powerups, lapidas)
                    player.update_animation()
                    if player.is_ghost: player.update_ghost_sound()
                    if not set_end_sequence_start_time: player.update_passable(
                        bombs); player.update_curse(); player.update_escudo()

                for bomb in bombs[:]:
                    bomb.update_push_slide()
                    bomb.update_hit_bounce(grid, players, bombs, powerups)
                    if not bomb.exploded and time.time() - bomb.plant_time >= bomb.timer and not bomb.timer_frozen:
                        explosions.extend(bomb.explode(grid, players, bombs, powerups))
                if lapida_por_colocar and not explosions:
                    pos = lapida_por_colocar
                    if not any(l.tile_x == pos[0] and l.tile_y == pos[1] for l in lapidas):
                        lapidas.append(Lapida(pos[0], pos[1], LAPIDA_IMG))
                    lapida_por_colocar = None
                for lapida in lapidas[:]:
                    lapida.update()
                    if lapida.is_finished(): lapidas.remove(lapida); continue
                    debe_ser_eliminada = False
                    if any(b.tile_x == lapida.tile_x and b.tile_y == lapida.tile_y for b in bombs):
                        debe_ser_eliminada = True
                    elif any(e.tile_x == lapida.tile_x and e.tile_y == lapida.tile_y for e in explosions):
                        debe_ser_eliminada = True
                    elif any(p.x == lapida.tile_x and p.y == lapida.tile_y and p.visible for p in powerups):
                        debe_ser_eliminada = True
                    if debe_ser_eliminada: lapidas.remove(lapida)
                for da in dropped_abilities[:]:
                    da.update(dt, grid, powerups)
                    if da.completed: dropped_abilities.remove(da)
                update_powerups(powerups, dt)
                if not set_end_sequence_start_time: check_pickup(players, powerups, lapidas)
                mortal_tiles_with_owner = {(e.tile_x, e.tile_y): e.owner for e in explosions if not e.finished}
                if mortal_tiles_with_owner and not set_end_sequence_start_time:
                    muertes_en_frame = []
                    for player in players[:]:
                        if player.is_ghost or player.is_invulnerable or player.escudo_active or player.is_eliminated: continue
                        player_hitbox = player.get_hitbox()
                        if player_hitbox.width * player_hitbox.height == 0: continue
                        total_overlap_area = 0
                        killer = None
                        min_tile_x = player_hitbox.left // TILE_SIZE
                        max_tile_x = (player_hitbox.right - 1) // TILE_SIZE
                        min_tile_y = player_hitbox.top // TILE_SIZE
                        max_tile_y = (player_hitbox.bottom - 1) // TILE_SIZE
                        for tx in range(min_tile_x, max_tile_x + 1):
                            for ty in range(min_tile_y, max_tile_y + 1):
                                if (tx, ty) in mortal_tiles_with_owner:
                                    mortal_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                                    overlap_rect = player_hitbox.clip(mortal_rect)
                                    total_overlap_area += overlap_rect.width * overlap_rect.height
                                    if mortal_tiles_with_owner[(tx, ty)] is not None: killer = mortal_tiles_with_owner[
                                        (tx, ty)]
                        if (total_overlap_area / (
                                player_hitbox.width * player_hitbox.height)) >= 0.15: muertes_en_frame.append(
                            {'player': player, 'killer': killer})
                    if muertes_en_frame:
                        jugadores_vivos_antes = [p for p in players if not p.is_ghost and not p.is_eliminated]
                        num_vivos_antes = len(jugadores_vivos_antes)
                        num_muertes = len(muertes_en_frame)
                        killer_fantasma = muertes_en_frame[0]['killer']
                        if (
                                num_vivos_antes == 2 and num_muertes == 2 and killer_fantasma and killer_fantasma.is_ghost and
                                muertes_en_frame[1]['killer'] == killer_fantasma):
                            MUERTE_SOUND.play()
                            killer_fantasma.resurrect()
                            set_winner = killer_fantasma
                            set_winner.sets_won += 1
                            set_winner.is_set_winner = True
                            set_winner.set_winner_start_time = time.time()
                            for muerte in muertes_en_frame: muerte['player'].eliminate()
                            set_end_sequence_start_time = time.time()
                        elif num_vivos_antes == num_muertes and num_muertes > 1:
                            muerte_por_fantasma = any(m['killer'] and m['killer'].is_ghost for m in muertes_en_frame)
                            if not muerte_por_fantasma:
                                print("¡EMPATE! La ronda no cuenta.")
                                MUERTE_SOUND.play()
                                for muerte in muertes_en_frame:
                                    if usar_fantasmas and not hurry_up_mode_activated:
                                        muerte['player'].become_ghost()
                                    else:
                                        muerte['player'].eliminate()
                                set_winner = None
                                set_end_sequence_start_time = time.time()
                        else:
                            for muerte in muertes_en_frame:
                                player_muerto = muerte['player']
                                killer = muerte['killer']
                                MUERTE_SOUND.play()
                                if killer and killer.is_ghost:
                                    killer.resurrect()
                                    if usar_fantasmas and not hurry_up_mode_activated:
                                        player_muerto.become_ghost()
                                    else:
                                        player_muerto.eliminate()
                                else:
                                    if usar_fantasmas and not hurry_up_mode_activated:
                                        player_muerto.become_ghost()
                                    else:
                                        player_muerto.eliminate()
                                if lapida_por_colocar is None: lapida_por_colocar = player_muerto.get_center_tile()
                                generar_poderes_al_morir(grid, bombs, powerups, players)
                if bloques_finales_activados and remaining_time <= 55 and proximo_bloque_idx < len(ruta_espiral):
                    temporizador_caida_bloque += dt
                    if proximo_bloque_idx == 0 and len(final_blocks) == 0:
                        tx, ty = ruta_espiral[proximo_bloque_idx]
                        if grid[ty][tx] != 4: final_blocks.append(BloqueFinal(tx, ty));
                        if BLOQUE_FINAL_SOUND: BLOQUE_FINAL_SOUND.play()
                        proximo_bloque_idx += 1
                        temporizador_caida_bloque = 0
                    elif temporizador_caida_bloque >= tiempo_por_bloque:
                        temporizador_caida_bloque -= tiempo_por_bloque
                        tx, ty = ruta_espiral[proximo_bloque_idx]
                        if grid[ty][tx] != 4: final_blocks.append(BloqueFinal(tx, ty));
                        if BLOQUE_FINAL_SOUND: BLOQUE_FINAL_SOUND.play()
                        proximo_bloque_idx += 1
                bloques_para_remover = []
                for bloque in final_blocks:
                    bloque.update(dt)
                    if bloque.state == "landed":
                        tx, ty = bloque.tile_x, bloque.tile_y
                        if 0 <= ty < GRID_ROWS and 0 <= tx < GRID_COLS: grid[ty][tx] = 4
                        for p in powerups[:]:
                            if p.x == tx and p.y == ty: powerups.remove(p)
                        for l in lapidas[:]:
                            if l.tile_x == tx and l.tile_y == ty: lapidas.remove(l)
                        for player in players:
                            if player.is_eliminated: continue
                            player_tile = player.get_center_tile()
                            if player_tile == (tx, ty):
                                MUERTE_SOUND.play()
                                if usar_fantasmas and not hurry_up_mode_activated:
                                    player.become_ghost()
                                else:
                                    player.eliminate()
                        bloques_para_remover.append(bloque)
                for bloque in bloques_para_remover: final_blocks.remove(bloque)
                if not set_end_sequence_start_time:
                    alive_players = [p for p in players if not p.is_ghost and not p.is_eliminated]
                    if len(alive_players) <= 1:
                        set_end_sequence_start_time = time.time()
                        if len(alive_players) == 1:
                            set_winner = alive_players[0]
                            set_winner.sets_won += 1
                            set_winner.is_set_winner = True
                            set_winner.set_winner_start_time = time.time()
                            if GANADOR_SET_SOUND: GANADOR_SET_SOUND.play()
                    elif remaining_time <= 0:
                        set_end_sequence_start_time = time.time()
                        if len(alive_players) > 1:
                            print("¡TIEMPO AGOTADO! EMPATE. La ronda no cuenta."); set_winner = None
                        elif len(alive_players) == 1:
                            set_winner = alive_players[0]
                            set_winner.sets_won += 1
                            set_winner.is_set_winner = True
                            set_winner.set_winner_start_time = time.time()
                            if GANADOR_SET_SOUND: GANADOR_SET_SOUND.play()

            # Dibuja el frame completo de la partida.
            background_gif.update()
            frame_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            background_gif.draw(frame_surface)
            game_surface = pygame.Surface((GRID_WIDTH, HEIGHT), pygame.SRCALPHA)
            draw_grid(game_surface, grid, SUELO1, SUELO2, STONE, BRICK, LIMIT_IMG)

            # Los objetos del mapa se actualizan únicamente durante el estado jugable.
            if estado_set == "jugando":
                for bloque in final_blocks: bloque.draw_marker(game_surface)
                for lapida in lapidas: lapida.draw(game_surface)
                for p in powerups: p.draw(game_surface)
                for b in bombs: b.draw(game_surface)
                for da in dropped_abilities: da.draw(game_surface)
                for explosion in explosions[:]:
                    explosion.update()
                    if explosion.finished:
                        explosions.remove(explosion)
                    else:
                        explosion.draw(game_surface)
                for bloque in final_blocks: bloque.draw(game_surface)

            # Los jugadores vivos se ordenan por coordenada vertical para simular profundidad.
            drawable_players = [set_winner] if set_end_sequence_start_time and set_winner else players
            sorted_players = sorted([p for p in drawable_players if not p.is_ghost], key=lambda p: p.y)
            for p in sorted_players:
                if p.is_eliminated: continue
                p.draw(game_surface)

            for p in drawable_players:
                if p.is_ghost and not p.is_eliminated:
                    p.draw(game_surface)

            draw_timer(game_surface, remaining_time)
            frame_surface.blit(game_surface, (SCOREBOARD_AREA_WIDTH, 0))
            draw_scoreboards(frame_surface, players, scoreboard_images, set_positions, WIDTH, HEIGHT)

            # Dibujar textos de animación ("PREPARADOS", "GANADOR", etc.)
            if estado_set == "preparados":
                if draw_animated_text(frame_surface, PREPARADOS_IMG, tiempo_anim_texto, duration=1.5):
                    estado_set = "adelante"
                    tiempo_anim_texto = time.time()
                    if ADELANTE_SOUND: ADELANTE_SOUND.play()

            elif estado_set == "adelante":
                if draw_animated_text(frame_surface, ADELANTE_IMG, tiempo_anim_texto, duration=1.5):
                    estado_set = "jugando"
                    start_time = time.time()

            elif estado_set == "jugando":
                if date_prisa_anim_start_time and DATE_PRISA_IMG:
                    anim_duration = 3.0
                    elapsed = time.time() - date_prisa_anim_start_time
                    if elapsed < anim_duration:
                        new_width = DATE_PRISA_IMG.get_width() // 2
                        new_height = DATE_PRISA_IMG.get_height() // 2
                        scaled_img = pygame.transform.scale(DATE_PRISA_IMG, (new_width, new_height))
                        fade_in_time = 0.25
                        fade_out_time = 0.25
                        alpha = 255 * 0.8
                        if elapsed < fade_in_time:
                            alpha *= (elapsed / fade_in_time)
                        elif elapsed > anim_duration - fade_out_time:
                            alpha *= (anim_duration - elapsed) / fade_out_time
                        temp_img = scaled_img.copy()
                        temp_img.set_alpha(int(max(0, alpha)))
                        img_rect = temp_img.get_rect(center=(WIDTH / 2, HEIGHT / 2))
                        frame_surface.blit(temp_img, img_rect)
                    else:
                        date_prisa_anim_start_time = None

            if set_end_sequence_start_time:
                anim_duration = 3.0
                elapsed = time.time() - set_end_sequence_start_time

                # Solo animar durante la duración establecida
                if elapsed < anim_duration:
                    # Calcular el efecto de fade-in y fade-out
                    fade_in_time = 0.25
                    fade_out_time = 0.50
                    alpha = 255

                    if elapsed < fade_in_time:
                        alpha *= (elapsed / fade_in_time)
                    elif elapsed > anim_duration - fade_out_time:
                        alpha *= (anim_duration - elapsed) / fade_out_time

                    alpha = int(max(0, alpha))

                    # Hay un ganador para el set
                    if set_winner and GANADOR_SET_IMG and JUGADOR_VICTORIA_IMGS:
                        # Dibujar "ganador_set.png"
                        img_ganador_set = GANADOR_SET_IMG.copy()
                        img_ganador_set.set_alpha(alpha)
                        rect_ganador = img_ganador_set.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 40))
                        frame_surface.blit(img_ganador_set, rect_ganador)

                        # Dibujar "jX.png" debajo
                        if 0 <= set_winner.player_index < len(JUGADOR_VICTORIA_IMGS):
                            img_jugador = JUGADOR_VICTORIA_IMGS[set_winner.player_index].copy()
                            img_jugador.set_alpha(alpha)
                            rect_jugador = img_jugador.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 40))
                            frame_surface.blit(img_jugador, rect_jugador)

                    # El set termina en empate (no hay ganador)
                    elif not set_winner and SET_FINALIZADO_IMG and EMPATE_IMG:

                        # Dibujar "set_finalizado.png"
                        img_set_fin = SET_FINALIZADO_IMG.copy()
                        img_set_fin.set_alpha(alpha)
                        rect_fin = img_set_fin.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 40))
                        frame_surface.blit(img_set_fin, rect_fin)

                        # Dibujar "empate.png" debajo
                        img_empate = EMPATE_IMG.copy()
                        img_empate.set_alpha(alpha)
                        rect_empate = img_empate.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 40))
                        frame_surface.blit(img_empate, rect_empate)

            presentar_superficie_escalada(screen, frame_surface)
            pygame.display.flip()
            if estado_set == "jugando" and set_end_sequence_start_time and (
                    time.time() - set_end_sequence_start_time > 3.0):
                set_running = False

        FANTASMA_SOUND.stop()

        if set_winner and set_winner.sets_won >= sets_to_win:
            match_winner = set_winner
            match_running = False


    FANTASMA_SOUND.stop()

    if match_winner:
        if GANADOR_PARTIDA_SOUND: GANADOR_PARTIDA_SOUND.play()
        try:
            confeti_path = os.path.join(ASSETS_DIR, "Mapas", "confeti.gif")
            confeti_gif = AnimatedBackground(confeti_path, (WIDTH, HEIGHT))
        except (FileNotFoundError, pygame.error) as e:
            print(f"ADVERTENCIA: No se pudo cargar confeti.gif: {e}")
            confeti_gif = None
        victory_start_time = time.time()
        while time.time() - victory_start_time < 5.0:
            background_gif.update()
            frame_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            background_gif.draw(frame_surface)
            game_surface.fill((0, 0, 0, 0))
            draw_grid(game_surface, grid, SUELO1, SUELO2, STONE, BRICK, LIMIT_IMG)
            match_winner.draw(game_surface)
            draw_timer(game_surface, 0)
            frame_surface.blit(game_surface, (SCOREBOARD_AREA_WIDTH, 0))
            draw_scoreboards(frame_surface, players, scoreboard_images, set_positions, WIDTH, HEIGHT)
            if GANADOR_PARTIDA_IMG and JUGADOR_VICTORIA_IMGS:
                rect_partida = GANADOR_PARTIDA_IMG.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 40))
                frame_surface.blit(GANADOR_PARTIDA_IMG, rect_partida)
                if 0 <= match_winner.player_index < len(JUGADOR_VICTORIA_IMGS):
                    rect_jugador_final = JUGADOR_VICTORIA_IMGS[match_winner.player_index].get_rect(
                        center=(WIDTH / 2, HEIGHT / 2 + 40))
                    frame_surface.blit(JUGADOR_VICTORIA_IMGS[match_winner.player_index], rect_jugador_final)
            if confeti_gif:
                confeti_gif.update()
                confeti_gif.draw(frame_surface)
            presentar_superficie_escalada(screen, frame_surface)
            pygame.display.flip()
            clock.tick(60)

    from EstadoPartida import reiniciar_estado
    reiniciar_estado()
    from PantallaConfigPartida import pantalla2_main
    from PantallaPrincipal import BackgroundAnimation
    screen = crear_pantalla_completa()
    bg_anim = BackgroundAnimation(screen.get_width(), screen.get_height())
    pantalla2_main(screen, bg_anim)
