import pygame
import sys
import math
import re
import unicodedata

MENU_LOGICAL_SIZE = (800, 600)
CURSOR_MENU_INACTIVITY_MS = 1800
_CURSOR_MOUSE_EVENTS = (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL)
_CURSOR_NON_MOUSE_EVENTS = (
    pygame.KEYDOWN,
    pygame.JOYBUTTONDOWN,
    pygame.JOYAXISMOTION,
    pygame.JOYHATMOTION,
    pygame.JOYDEVICEADDED,
    pygame.JOYDEVICEREMOVED,
)
_WINDOW_INACTIVE_EVENTS = (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED)
_WINDOW_ACTIVE_EVENTS = (pygame.WINDOWFOCUSGAINED, pygame.WINDOWRESTORED, pygame.WINDOWSHOWN)
_JOYSTICK_INPUT_EVENTS = (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION)
_NOMBRES_CONTROL_ARCADE = {
    "controlador jugador 1",
    "controlador jugador 2",
}
_ultima_actividad_cursor = 0
_ultima_posicion_raton = None
_ultimo_dispositivo_menu = "teclado"
_tipos_joystick_por_instancia = {}


# --- Clase para el fondo animado ---
class BackgroundAnimation:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.sky = pygame.image.load("Media/Menu/Pantalla_principal/cielo.png").convert()
        self.sky = pygame.transform.scale(self.sky, (screen_width, screen_height))

        self.ground = pygame.image.load("Media/Menu/Pantalla_principal/ground2.png").convert_alpha()
        self.ground_width, self.ground_height = self.ground.get_size()
        self.ground = pygame.transform.scale(self.ground, (screen_width, self.ground_height))

        self.cloud1 = pygame.image.load("Media/Menu/Pantalla_principal/nube2.png").convert_alpha()
        self.cloud2 = pygame.image.load("Media/Menu/Pantalla_principal/nube3.png").convert_alpha()
        self.cloud1 = pygame.transform.scale(self.cloud1, (120, 60))
        self.cloud2 = pygame.transform.scale(self.cloud2, (200, 100))
        self.cloud1_width = self.cloud1.get_width()
        self.cloud2_width = self.cloud2.get_width()

        self.cloud1_x = screen_width
        self.cloud1_y = 50
        self.cloud2_x = -self.cloud2_width
        self.cloud2_y = 80

        self.zeppelin = pygame.image.load("Media/Menu/Pantalla_principal/zeppelin.png").convert_alpha()
        self.zeppelin = pygame.transform.scale(self.zeppelin, (300, 150))
        self.zeppelin_width = self.zeppelin.get_width()
        self.zeppelin_x = screen_width
        self.zeppelin_y = 130

        self.ground_speed = 2
        self.cloud1_speed = 1
        self.cloud2_speed = 0.5
        self.zeppelin_speed = 0.85
        self.ground_x = 0

    def update(self):
        self.cloud1_x += self.cloud1_speed
        if self.cloud1_x > self.screen_width:
            self.cloud1_x = -self.cloud1_width

        self.cloud2_x += self.cloud2_speed
        if self.cloud2_x > self.screen_width:
            self.cloud2_x = -self.cloud2_width

        self.zeppelin_x -= self.zeppelin_speed
        if self.zeppelin_x < -self.zeppelin_width:
            self.zeppelin_x = self.screen_width

        self.ground_x = (self.ground_x + self.ground_speed) % self.screen_width

    def draw(self, screen):
        screen.blit(self.sky, (0, 0))
        screen.blit(self.cloud1, (self.cloud1_x, self.cloud1_y))
        screen.blit(self.cloud2, (self.cloud2_x, self.cloud2_y))
        screen.blit(self.zeppelin, (self.zeppelin_x, self.zeppelin_y))
        screen.blit(self.ground, (self.ground_x - self.screen_width, self.screen_height - self.ground_height))
        screen.blit(self.ground, (self.ground_x, self.screen_height - self.ground_height))


def crear_pantalla_completa():
    info = pygame.display.Info()
    ancho = max(1, info.current_w)
    alto = max(1, info.current_h)
    return pygame.display.set_mode((ancho, alto), pygame.FULLSCREEN)


def crear_superficie_menu_logica():
    return pygame.Surface(MENU_LOGICAL_SIZE, pygame.SRCALPHA)


def convertir_mouse_a_logico(mouse_pos, display_screen):
    logical_w, logical_h = MENU_LOGICAL_SIZE
    display_w, display_h = display_screen.get_size()
    if (display_w, display_h) == MENU_LOGICAL_SIZE:
        return mouse_pos
    escala_x = display_w / logical_w
    escala_y = display_h / logical_h
    return int(mouse_pos[0] / escala_x), int(mouse_pos[1] / escala_y)


def presentar_menu_logico(display_screen, logical_surface):
    if logical_surface.get_size() == display_screen.get_size():
        display_screen.blit(logical_surface, (0, 0))
    else:
        frame = pygame.transform.smoothscale(logical_surface, display_screen.get_size())
        display_screen.blit(frame, (0, 0))


def dibujar_pantalla_carga(screen, angulo):
    """Dibuja el estado de carga sobre un fondo negro."""
    ancho, alto = screen.get_size()
    escala = min(ancho / 800, alto / 600)
    margen = max(24, round(28 * escala))
    radio = max(12, round(14 * escala))
    grosor = max(3, round(3 * escala))
    font = pygame.font.SysFont(None, max(24, round(25 * escala)), bold=True)

    screen.fill((0, 0, 0))
    texto = font.render("Cargando", True, (255, 255, 255))
    rect_texto = texto.get_rect(bottomright=(ancho - margen, alto - margen))
    screen.blit(texto, rect_texto)

    centro_x = rect_texto.left - margen // 2 - radio
    centro_y = rect_texto.centery
    rect_rueda = pygame.Rect(centro_x - radio, centro_y - radio, radio * 2, radio * 2)
    pygame.draw.circle(screen, (70, 70, 70), (centro_x, centro_y), radio, grosor)
    pygame.draw.arc(
        screen,
        (255, 255, 255),
        rect_rueda,
        angulo,
        angulo + math.radians(245),
        grosor,
    )


def mostrar_pantalla_carga(screen, duracion_ms=350):
    """Presenta brevemente un indicador animado y lo mantiene durante la carga posterior."""
    inicio = pygame.time.get_ticks()
    clock = pygame.time.Clock()
    while pygame.time.get_ticks() - inicio < duracion_ms:
        pygame.event.pump()
        transcurrido = pygame.time.get_ticks() - inicio
        dibujar_pantalla_carga(screen, math.radians((transcurrido * 0.42) % 360))
        pygame.display.flip()
        clock.tick(60)


def iniciar_cursor_menu():
    """Prepara los menus para empezar con el cursor oculto hasta que se use el raton."""
    global _ultima_actividad_cursor, _ultima_posicion_raton
    _ultima_actividad_cursor = 0
    pygame.event.clear(pygame.MOUSEMOTION)
    _ultima_posicion_raton = pygame.mouse.get_pos()
    pygame.mouse.set_visible(False)


def cursor_menu_activo():
    return pygame.mouse.get_visible()


def normalizar_nombre_dispositivo(nombre):
    """Normaliza el nombre que SDL entrega para comparar dispositivos de forma estable."""
    texto = unicodedata.normalize("NFKD", str(nombre or ""))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"[^a-z0-9]+", " ", texto.casefold()).strip()


def es_nombre_control_arcade(nombre):
    nombre_normalizado = normalizar_nombre_dispositivo(nombre)
    return any(
        re.search(rf"(?:^|\s){re.escape(nombre_arcade)}(?:\s|$)", nombre_normalizado)
        for nombre_arcade in _NOMBRES_CONTROL_ARCADE
    )


def registrar_joystick_menu(joystick):
    """Asocia el identificador estable de SDL con el tipo real de control."""
    if not joystick.get_init():
        joystick.init()
    tipo = "arcade" if es_nombre_control_arcade(joystick.get_name()) else "mando"
    _tipos_joystick_por_instancia[joystick.get_instance_id()] = tipo
    return tipo


def actualizar_joysticks_menu():
    """Actualiza el registro sin asumir que el indice SDL coincide con el instance_id."""
    instancias_conectadas = set()
    for indice in range(pygame.joystick.get_count()):
        try:
            joystick = pygame.joystick.Joystick(indice)
            registrar_joystick_menu(joystick)
            instancias_conectadas.add(joystick.get_instance_id())
        except pygame.error:
            continue

    for instance_id in list(_tipos_joystick_por_instancia):
        if instance_id not in instancias_conectadas:
            del _tipos_joystick_por_instancia[instance_id]


def obtener_tipo_joystick_evento(event):
    actualizar_joysticks_menu()
    instance_id = getattr(event, "instance_id", None)
    if instance_id in _tipos_joystick_por_instancia:
        return _tipos_joystick_por_instancia[instance_id]

    # En eventos antiguos, ``joy`` puede contener el instance_id o el indice SDL.
    joy_id = getattr(event, "joy", None)
    if joy_id in _tipos_joystick_por_instancia:
        return _tipos_joystick_por_instancia[joy_id]
    if isinstance(joy_id, int) and 0 <= joy_id < pygame.joystick.get_count():
        try:
            return registrar_joystick_menu(pygame.joystick.Joystick(joy_id))
        except pygame.error:
            pass

    return "mando"


def obtener_nombre_joystick_evento(event):
    """Devuelve el nombre del joystick que genero un evento, si sigue conectado."""
    instance_id = getattr(event, "instance_id", getattr(event, "joy", None))
    for indice in range(pygame.joystick.get_count()):
        try:
            joystick = pygame.joystick.Joystick(indice)
            if not joystick.get_init():
                joystick.init()
            if joystick.get_instance_id() == instance_id:
                return joystick.get_name()
        except pygame.error:
            continue
    return ""


def es_evento_joystick_relevante(event, umbral=0.35):
    if event.type == pygame.JOYAXISMOTION:
        return abs(getattr(event, "value", 0.0)) >= umbral
    if event.type == pygame.JOYHATMOTION:
        return getattr(event, "value", (0, 0)) != (0, 0)
    return event.type == pygame.JOYBUTTONDOWN


def es_evento_control_arcade(event):
    if event.type not in _JOYSTICK_INPUT_EVENTS or not es_evento_joystick_relevante(event):
        return False
    return obtener_tipo_joystick_evento(event) == "arcade"


def establecer_ultimo_dispositivo_menu(tipo_dispositivo):
    global _ultimo_dispositivo_menu
    if tipo_dispositivo in ("teclado", "mando", "arcade"):
        _ultimo_dispositivo_menu = tipo_dispositivo


def obtener_ultimo_dispositivo_menu():
    return _ultimo_dispositivo_menu


def tipo_joystick_menu(joystick):
    return registrar_joystick_menu(joystick)


def registrar_dispositivo_menu_evento(event):
    if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
        establecer_ultimo_dispositivo_menu("teclado")
    elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_visible():
        establecer_ultimo_dispositivo_menu("teclado")
    elif event.type in _JOYSTICK_INPUT_EVENTS and es_evento_joystick_relevante(event):
        establecer_ultimo_dispositivo_menu("arcade" if es_evento_control_arcade(event) else "mando")
    return obtener_ultimo_dispositivo_menu()


def evento_ventana_inactiva(event):
    return event.type in _WINDOW_INACTIVE_EVENTS


def congelar_menu_si_pierde_foco(event):
    if event.type not in _WINDOW_INACTIVE_EVENTS:
        return False

    mixer_activo = pygame.mixer.get_init() is not None
    musica_activa = mixer_activo and pygame.mixer.music.get_busy()
    canales_activos = mixer_activo and pygame.mixer.get_busy()
    if mixer_activo:
        if musica_activa:
            pygame.mixer.music.pause()
        pygame.mixer.pause()
    pygame.mouse.set_visible(False)

    while True:
        evento_espera = pygame.event.wait()
        if evento_espera.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if evento_espera.type in _WINDOW_ACTIVE_EVENTS:
            if mixer_activo and musica_activa:
                pygame.mixer.music.unpause()
            if mixer_activo and canales_activos:
                pygame.mixer.unpause()
            return True


def es_actividad_real_raton(event):
    """Descarta eventos de movimiento generados al abrir o redimensionar la ventana."""
    global _ultima_posicion_raton
    if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
        return True
    if event.type != pygame.MOUSEMOTION:
        return False

    posicion = getattr(event, "pos", pygame.mouse.get_pos())
    posicion_anterior = _ultima_posicion_raton
    _ultima_posicion_raton = posicion
    return posicion_anterior is not None and posicion != posicion_anterior


def registrar_actividad_cursor(event):
    """Muestra el cursor solo cuando hay entrada real de raton."""
    global _ultima_actividad_cursor
    if congelar_menu_si_pierde_foco(event):
        _ultima_actividad_cursor = 0
        return False
    if event.type in _CURSOR_MOUSE_EVENTS and es_actividad_real_raton(event):
        _ultima_actividad_cursor = pygame.time.get_ticks()
        pygame.mouse.set_visible(True)
        return True
    elif event.type in _CURSOR_NON_MOUSE_EVENTS:
        _ultima_actividad_cursor = 0
        pygame.mouse.set_visible(False)
    return False


def actualizar_cursor_menu():
    """Oculta de nuevo el cursor si el raton lleva un tiempo sin utilizarse."""
    if _ultima_actividad_cursor and pygame.time.get_ticks() - _ultima_actividad_cursor >= CURSOR_MENU_INACTIVITY_MS:
        pygame.mouse.set_visible(False)


def ocultar_cursor_partida():
    """Garantiza que el cursor no aparezca durante la partida activa."""
    global _ultima_actividad_cursor
    _ultima_actividad_cursor = 0
    pygame.mouse.set_visible(False)


def draw_bombeo_texto(screen, center, font, message):
    tiempo = pygame.time.get_ticks() / 300.0
    factor = 1 + 0.05 * math.sin(tiempo)
    texto_render = font.render(message, True, (255, 255, 255))
    new_width = int(texto_render.get_width() * factor)
    new_height = int(texto_render.get_height() * factor)
    texto_escala = pygame.transform.scale(texto_render, (new_width, new_height))
    rect = texto_escala.get_rect(center=center)
    screen.blit(texto_escala, rect)


def animar_titulo_kaboom(screen, logo_img, tiempo_inicio, screen_width):
    tiempo_actual = pygame.time.get_ticks()
    tiempo_transcurrido = (tiempo_actual - tiempo_inicio) / 1000.0

    duracion_aparicion = 0.7
    duracion_bote = 1.5
    screen_height = screen.get_height()
    x_centro = screen_width // 2
    y_base = screen_height // 2 - 50

    if tiempo_transcurrido < duracion_aparicion:
        alpha = int(255 * (tiempo_transcurrido / duracion_aparicion))
        escala = 0.15 + 0.15 * (tiempo_transcurrido / duracion_aparicion)
        y_actual = y_base
    else:
        alpha = 255
        escala = 0.3
        t_bote = tiempo_transcurrido - duracion_aparicion
        progreso_bote = t_bote % 1.0  # Bote continuo usando ciclo sin fin
        rebote = abs(math.sin(progreso_bote * math.pi * 2)) * 15
        y_actual = y_base + rebote

    logo_scaled = pygame.transform.rotozoom(logo_img, 0, escala)
    logo_scaled.set_alpha(alpha)
    rect = logo_scaled.get_rect(center=(x_centro, int(y_actual)))
    screen.blit(logo_scaled, rect)


def background_screen(screen):
    pygame.init()
    if screen is None:
        screen = crear_pantalla_completa()
    iniciar_cursor_menu()
    screen_width, screen_height = screen.get_size()
    pygame.display.set_caption("Pantalla de Inicio - Fondo Animado")
    clock = pygame.time.Clock()

    pygame.joystick.init()
    mandos = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for mando in mandos:
        mando.init()
    font = pygame.font.SysFont(None, 30)
    message = "PULSA CUALQUIER TECLA O BOTÓN PARA CONTINUAR"
    text_center = (screen_width // 2, screen_height - 100)

    key_sound = pygame.mixer.Sound("Media/Sonidos_juego/Botones/boton_inicio.mp3")
    key_sound.set_volume(1)

    bg_anim = BackgroundAnimation(screen_width, screen_height)
    tiempo_inicio = pygame.time.get_ticks()
    logo_img = pygame.image.load("Media/LOGO/kaboom_logo.png").convert_alpha()

    running = True
    while running:
        tiempo_actual = pygame.time.get_ticks()
        tiempo_transcurrido = (tiempo_actual - tiempo_inicio) / 1000.0
        progreso = min(tiempo_transcurrido / 1.5, 1)

        for event in pygame.event.get():
            registrar_actividad_cursor(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if (event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN) and progreso >= 1:
                registrar_dispositivo_menu_evento(event)
                key_sound.play()
                running = False

            if event.type == pygame.JOYBUTTONDOWN and progreso >= 1:
                registrar_dispositivo_menu_evento(event)
                key_sound.play()
                running = False

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1:
                    print("JUEGO CERRADO")
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                print("JUEGO CERRADO")
                pygame.quit()
                sys.exit()

            if event.type == pygame.JOYDEVICEADDED:
                nuevo_mando = pygame.joystick.Joystick(event.device_index)
                nuevo_mando.init()
                print("Mando conectado:", nuevo_mando.get_name())

        bg_anim.update()
        bg_anim.draw(screen)
        animar_titulo_kaboom(screen, logo_img, tiempo_inicio, screen_width)
        if progreso >= 1:
            draw_bombeo_texto(screen, text_center, font, message)

        actualizar_cursor_menu()
        pygame.display.flip()
        clock.tick(60)

    return bg_anim
