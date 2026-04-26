import pygame
import sys
import math

MENU_LOGICAL_SIZE = (800, 600)


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
    screen_width, screen_height = screen.get_size()
    pygame.display.set_caption("Pantalla de Inicio - Fondo Animado")
    clock = pygame.time.Clock()

    pygame.joystick.init()
    mandos = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for mando in mandos:
        mando.init()

    font = pygame.font.SysFont(None, 30)
    message = "Pulsa cualquier tecla o botón del mando para continuar"
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
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if (event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN) and progreso >= 1:
                key_sound.play()
                running = False

            if event.type == pygame.JOYBUTTONDOWN and progreso >= 1:
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

        pygame.display.flip()
        clock.tick(60)

    return bg_anim
