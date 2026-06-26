import pygame
import sys
from Config import audio
from PantallaPrincipal import (
    actualizar_cursor_menu,
    es_evento_control_arcade,
    es_evento_joystick_relevante,
    es_nombre_control_arcade,
    iniciar_cursor_menu,
    registrar_actividad_cursor,
)

# Constantes para los colores
AZUL = (0, 0, 255)
BLANCO = (255, 255, 255)
ROJO = (255, 0, 0)
NEGRO = (0, 0, 0)
GRIS_CLARO = (200, 200, 200)
GRIS_MEDIO = (150, 150, 150)
GRIS_OSCURO = (100, 100, 100)
VERDE_HOVER = (210, 255, 210)
ROJO_HOVER = (255, 200, 200)

# Solo un tipo de volumen
TIPOS_DE_VOLUMEN = ["GENERAL"]

last_input_method = "mouse"  # Último dispositivo usado para navegar por el menú.
selected_element_index = 0  # Elemento activo dentro del menú de pausa.
hover_casillas = [False] * 5  # Estado visual de cada opción interactiva.
ultimo_index_hover = 0  # Última opción señalada por el cursor.
tiempo_ultimo_movimiento = 0  # Controla el intervalo entre entradas de mando.
JOYSTICK_COOLDOWN = 200  # milisegundos
last_joystick_move_time = 0  # Último movimiento registrado del joystick.


class SliderRect:
    def __init__(self, x, y, width, height, initial=1.0, tipo_volumen="GENERAL"):
        self.rect = pygame.Rect(x, y, width, height)
        self.value = initial
        self.handle_size = 15
        self.tipo_volumen = tipo_volumen

    def draw(self, screen):
        x, y, w, h = self.rect
        center_x = x + int(self.value * w)
        ancho_azul = center_x - x
        ancho_blanco = w - ancho_azul

        if ancho_azul > 0:
            pygame.draw.rect(screen, AZUL, (x, y, ancho_azul, h))
        if ancho_blanco > 0:
            pygame.draw.rect(screen, BLANCO, (center_x, y, ancho_blanco, h))
        pygame.draw.rect(screen, NEGRO, self.rect, 1)

        handle_left = center_x - self.handle_size // 2
        pygame.draw.rect(screen, ROJO, (handle_left,
                                        y + (h - self.handle_size) // 2,
                                        self.handle_size,
                                        self.handle_size))

    def update(self, mouse_pos, mouse_click):
        if mouse_click and self.rect.collidepoint(mouse_pos):
            rel_x = mouse_pos[0] - self.rect.left
            self.value = max(0.0, min(1.0, rel_x / self.rect.width))


def inicializar_componentes_ui(screen):
    ancho = 750
    alto = 450
    fondo_gris = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    rect_fondo_gris = fondo_gris.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))

    return  fondo_gris, rect_fondo_gris


def crear_sliders(rect_fondo_gris):
    base_x, base_y = audio.slider_pos
    ancho_slider, alto_slider = audio.slider_size
    sliders = []

    slider = SliderRect(
        rect_fondo_gris.left + base_x,
        rect_fondo_gris.top + base_y,
        ancho_slider,
        alto_slider,
        initial=audio.volume,
        tipo_volumen="GENERAL"
    )
    sliders.append(slider)
    return sliders


def dibujar_seleccion(screen, rect, seleccionado, color_hover, color_fondo, color_borde):
    if seleccionado:
        pygame.draw.rect(screen, color_hover, rect, border_radius=10)
    else:
        pygame.draw.rect(screen, color_fondo, rect, border_radius=10)
    pygame.draw.rect(screen, color_borde, rect, width=3, border_radius=10)

def cambiar_a_teclado():
    global last_input_method, hover_casillas
    last_input_method = "keyboard"
    hover_casillas = [False] * len(hover_casillas)


def cambiar_a_raton():
    global last_input_method
    last_input_method = "mouse"


def dispositivo_controles_inicial():
    if last_input_method == "arcade":
        return "panel"
    if last_input_method == "gamepad":
        return "mando"
    return "teclado"


def registrar_entrada_joystick(event):
    global last_input_method
    if es_evento_joystick_relevante(event):
        last_input_method = "arcade" if es_evento_control_arcade(event) else "gamepad"


def tipo_joystick_activo(joystick):
    return "arcade" if es_nombre_control_arcade(joystick.get_name()) else "gamepad"


def dibujar_ui(screen, bg_anim, fondo_gris, rect_fondo_gris, sliders):
    global hover_casillas, casillas_rects, last_input_method, ultimo_hover_index
    from Config import audio

    font_titulo = pygame.font.SysFont(None, 30)
    font_opciones = pygame.font.SysFont(None, 20)

    titulo_surf = font_titulo.render("AJUSTES DE JUEGO", True, NEGRO)
    titulo_rect = titulo_surf.get_rect(center=(rect_fondo_gris.centerx, rect_fondo_gris.top + 30))

    pygame.draw.rect(screen, GRIS_MEDIO, rect_fondo_gris, border_radius=10)
    pygame.draw.rect(screen, GRIS_OSCURO, rect_fondo_gris, width=4, border_radius=10)
    screen.blit(titulo_surf, titulo_rect)

    # Casilla para reanudar la partida.
    casilla_reanudar_rect = pygame.Rect(rect_fondo_gris.centerx - 150, titulo_rect.bottom + 24, 300, 52)

    # Casilla de fondo del slider de volumen.
    slider = sliders[0]
    ancho_slider, alto_slider = audio.slider_size

    slider_bg_rect = pygame.Rect(
        rect_fondo_gris.centerx - 285,
        casilla_reanudar_rect.bottom + 28,
        ancho_slider + 290, 46
    )

    slider.rect.width = ancho_slider
    slider.rect.height = alto_slider
    slider.rect.center = (slider_bg_rect.centerx + 65, slider_bg_rect.centery)

    # Casillas restantes distribuidas en vertical.
    casilla_ancho = 340
    casilla_alto = 48
    espacio_vertical = 22
    casillas_top = slider_bg_rect.bottom + 35
    casilla_left = rect_fondo_gris.centerx - casilla_ancho // 2
    casilla1_rect = pygame.Rect(casilla_left, casillas_top, casilla_ancho, casilla_alto)
    casilla2_rect = pygame.Rect(casilla_left, casilla1_rect.bottom + espacio_vertical, casilla_ancho, casilla_alto)
    casilla_roja_rect = pygame.Rect(casilla_left, casilla2_rect.bottom + espacio_vertical, casilla_ancho, casilla_alto)

    casillas_rects = [
        casilla_reanudar_rect,  # [0]
        slider_bg_rect,         # [1]
        casilla1_rect,          # [2] Aprende controles
        casilla2_rect,          # [3] Guía del juego
        casilla_roja_rect       # [4] Salir
    ]

    # ------------------ DETECCIÓN DE HOVER ------------------
    mouse_pos = pygame.mouse.get_pos()
    if last_input_method == "mouse":
        if 'ultimo_hover_index' not in globals():
            ultimo_hover_index = 0

        nueva_hover_casilla = -1
        for i, rect in enumerate(casillas_rects):
            if rect.collidepoint(mouse_pos):
                nueva_hover_casilla = i
                break

        if nueva_hover_casilla != -1:
            hover_casillas = [j == nueva_hover_casilla for j in range(len(casillas_rects))]
            ultimo_hover_index = nueva_hover_casilla
        else:
            hover_casillas = [j == ultimo_hover_index for j in range(len(casillas_rects))]
    else:
        hover_casillas = [False] * len(casillas_rects)

    if last_input_method == "mouse":
        seleccionados = hover_casillas
    else:
        seleccionados = [selected_element_index == i for i in range(len(casillas_rects))]

    # ------------------ DIBUJAR CASILLAS ------------------
    dibujar_seleccion(screen, casilla_reanudar_rect, seleccionados[0], VERDE_HOVER, (230, 230, 230), (0, 200, 0))
    dibujar_seleccion(screen, slider_bg_rect, seleccionados[1], VERDE_HOVER, GRIS_CLARO, GRIS_OSCURO)
    dibujar_seleccion(screen, casilla1_rect, seleccionados[2], VERDE_HOVER, (230, 230, 230), (0, 200, 0))
    dibujar_seleccion(screen, casilla2_rect, seleccionados[3], VERDE_HOVER, (230, 230, 230), (0, 200, 0))
    dibujar_seleccion(screen, casilla_roja_rect, seleccionados[4], ROJO_HOVER, (255, 180, 180), (200, 0, 0))

    # Textos
    font = pygame.font.SysFont(None, 16)
    etiqueta_font = pygame.font.SysFont(None, 20)

    texto_reanudar = font_opciones.render("REANUDAR PARTIDA", True, NEGRO)
    screen.blit(texto_reanudar, texto_reanudar.get_rect(center=casilla_reanudar_rect.center))

    etiqueta_surf = etiqueta_font.render("VOLUMEN DEL JUEGO", True, BLANCO)
    etiqueta_bg_rect = pygame.Rect(
        slider_bg_rect.left + 15, slider_bg_rect.top + 12,
        etiqueta_surf.get_width() + 10, etiqueta_surf.get_height() + 4
    )
    pygame.draw.rect(screen, GRIS_OSCURO, etiqueta_bg_rect, border_radius=6)
    pygame.draw.rect(screen, NEGRO, etiqueta_bg_rect, width=2, border_radius=6)
    screen.blit(etiqueta_surf, (etiqueta_bg_rect.left + 5, etiqueta_bg_rect.top + 2))

    slider.draw(screen)
    porcentaje = round(slider.value * 100)
    valor_surf = font.render(f"{porcentaje}%", True, NEGRO)
    valor_x = slider.rect.right + 10
    valor_y = slider.rect.y + (slider.rect.height // 2 - valor_surf.get_height() // 2)
    screen.blit(valor_surf, (valor_x, valor_y))

    # Textos de casillas inferiores
    texto_casilla1 = font_opciones.render("APRENDE LOS CONTROLES", True, NEGRO)
    texto_casilla2 = font_opciones.render("GUÍA DEL JUEGO", True, NEGRO)
    texto_rojo = font_opciones.render("SALIR DE LA PARTIDA", True, NEGRO)
    screen.blit(texto_casilla1, texto_casilla1.get_rect(center=casilla1_rect.center))
    screen.blit(texto_casilla2, texto_casilla2.get_rect(center=casilla2_rect.center))
    screen.blit(texto_rojo, texto_rojo.get_rect(center=casilla_roja_rect.center))



def manejar_eventos(sliders, screen, bg_anim):
    global selected_element_index, casillas_rects, last_input_method
    if 'casillas_rects' not in globals() or not casillas_rects:
        return

    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()[0]

    for event in pygame.event.get():
        registrar_actividad_cursor(event)
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEMOTION:
            cambiar_a_raton()

        if event.type == pygame.MOUSEBUTTONDOWN:
            cambiar_a_raton()
            for i, rect in enumerate(casillas_rects):
                if rect.collidepoint(mouse_pos):
                    selected_element_index = i

                    if i == 0:  # REANUDAR PARTIDA
                        guardar_volumenes(sliders)
                        return "ATRAS"
                    elif i == 2:
                        from AprendeControlesPartida import pantalla_controles
                        guardar_volumenes(sliders)
                        fondo_pausa = screen.copy()  # Guardar el fondo antes de cambiar de pantalla
                        pantalla_controles(
                            screen,
                            fondo_pausa,
                            dispositivo_inicial=dispositivo_controles_inicial(),
                            tipo_controles_inicial="combate",
                        )
                        screen.blit(fondo_pausa, (0, 0))  # Restaurar el fondo
                    elif i == 3:
                        from GuiaJuego import pantalla_guia
                        guardar_volumenes(sliders)
                        fondo_pausa = screen.copy()  # Guardar el fondo antes de cambiar de pantalla
                        pantalla_guia(screen)
                        screen.blit(fondo_pausa, (0, 0))  # Restaurar el fondo
                    elif i == 4:
                        guardar_volumenes(sliders)
                        confirmar_salida(screen, bg_anim, fondo_anterior=screen.copy())

        if event.type == pygame.KEYDOWN:
            cambiar_a_teclado()
            if event.key == pygame.K_ESCAPE:
                guardar_volumenes(sliders)
                return "ATRAS"
            elif event.key == pygame.K_DOWN:
                selected_element_index = (selected_element_index + 1) % len(casillas_rects)
            elif event.key == pygame.K_UP:
                selected_element_index = (selected_element_index - 1) % len(casillas_rects)
            elif selected_element_index == 1:
                if event.key == pygame.K_RIGHT:
                    sliders[0].value = min(1.0, sliders[0].value + 0.01)
                elif event.key == pygame.K_LEFT:
                    sliders[0].value = max(0.0, sliders[0].value - 0.01)
            elif event.key == pygame.K_RETURN:
                if selected_element_index == 0:
                    guardar_volumenes(sliders)
                    return "ATRAS"
                elif selected_element_index == 2:
                    from AprendeControlesPartida import pantalla_controles
                    guardar_volumenes(sliders)
                    fondo_pausa = screen.copy()  # Guardar el fondo antes de cambiar de pantalla
                    pantalla_controles(
                        screen,
                        fondo_pausa,
                        dispositivo_inicial=dispositivo_controles_inicial(),
                        tipo_controles_inicial="combate",
                    )
                    screen.blit(fondo_pausa, (0, 0))  # Restaurar el fondo
                elif selected_element_index == 3:
                    from GuiaJuego import pantalla_guia
                    guardar_volumenes(sliders)
                    fondo_pausa = screen.copy()  # Guardar el fondo antes de cambiar de pantalla
                    pantalla_guia(screen)
                    screen.blit(fondo_pausa, (0, 0))  # Restaurar el fondo
                elif selected_element_index == 4:
                    guardar_volumenes(sliders)
                    confirmar_salida(screen, bg_anim, fondo_anterior=screen.copy())

        if event.type == pygame.JOYBUTTONDOWN:
            registrar_entrada_joystick(event)
            if event.button == 0:
                if selected_element_index == 0:
                    guardar_volumenes(sliders)
                    return "ATRAS"
                elif selected_element_index == 2:
                    from AprendeControlesPartida import pantalla_controles
                    guardar_volumenes(sliders)
                    fondo_pausa = screen.copy()  # Guardar el fondo antes de cambiar de pantalla
                    pantalla_controles(
                        screen,
                        fondo_pausa,
                        dispositivo_inicial=dispositivo_controles_inicial(),
                        tipo_controles_inicial="combate",
                    )
                    screen.blit(fondo_pausa, (0, 0))  # Restaurar el fondo
                elif selected_element_index == 3:
                    from GuiaJuego import pantalla_guia
                    guardar_volumenes(sliders)
                    fondo_pausa = screen.copy()  # Guardar el fondo antes de cambiar de pantalla
                    pantalla_guia(screen)
                    screen.blit(fondo_pausa, (0, 0))  # Restaurar el fondo
                elif selected_element_index == 4:
                    guardar_volumenes(sliders)
                    confirmar_salida(screen, bg_anim, fondo_anterior=screen.copy())
            elif event.button in (7, 9):
                guardar_volumenes(sliders)
                return "ATRAS"

    # Movimiento con HAT del mando
    joys = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    if joys:
        joy = joys[0]
        hat_x, hat_y = joy.get_hat(0)

        global tiempo_ultimo_movimiento
        current_time = pygame.time.get_ticks()
        delay = 200

        if current_time - tiempo_ultimo_movimiento > delay:
            if hat_y == -1:
                last_input_method = tipo_joystick_activo(joy)
                selected_element_index = min(selected_element_index + 1, len(casillas_rects) - 1)
                tiempo_ultimo_movimiento = current_time
            elif hat_y == 1:
                last_input_method = tipo_joystick_activo(joy)
                selected_element_index = max(selected_element_index - 1, 0)
                tiempo_ultimo_movimiento = current_time
            elif hat_x == -1:
                last_input_method = tipo_joystick_activo(joy)
                if selected_element_index == 1:
                    sliders[0].value = max(0.0, sliders[0].value - 0.01)
                tiempo_ultimo_movimiento = current_time
            elif hat_x == 1:
                last_input_method = tipo_joystick_activo(joy)
                if selected_element_index == 1:
                    sliders[0].value = min(1.0, sliders[0].value + 0.01)
                tiempo_ultimo_movimiento = current_time

    global last_joystick_move_time
    current_time = pygame.time.get_ticks()
    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        y_axis = joystick.get_axis(1)
        if abs(y_axis) > 0.5 and current_time - last_joystick_move_time > JOYSTICK_COOLDOWN:
            last_input_method = tipo_joystick_activo(joystick)
            if y_axis > 0.5:
                selected_element_index = (selected_element_index + 1) % len(casillas_rects)
            elif y_axis < -0.5:
                selected_element_index = (selected_element_index - 1) % len(casillas_rects)
            last_joystick_move_time = current_time

        x_axis = joystick.get_axis(0)
        if abs(x_axis) > 0.5 and current_time - last_joystick_move_time > JOYSTICK_COOLDOWN:
            last_input_method = tipo_joystick_activo(joystick)
            if selected_element_index == 1:
                if x_axis > 0.5:
                    sliders[0].value = min(1.0, sliders[0].value + 0.01)
                elif x_axis < -0.5:
                    sliders[0].value = max(0.0, sliders[0].value - 0.01)
            last_joystick_move_time = current_time

    for slider in sliders:
        slider.update(mouse_pos, mouse_click)

    for slider in sliders:
        if slider.tipo_volumen == "GENERAL":
            pygame.mixer.music.set_volume(slider.value)
            audio.volume = slider.value
            audio.volume_effects = slider.value
            for efecto in audio.efectos.values():
                efecto.set_volume(slider.value)



def guardar_volumenes(sliders):
    for slider in sliders:
        if slider.tipo_volumen == "GENERAL":
            audio.volume = slider.value
            audio.volume_effects = slider.value
            for efecto in audio.efectos.values():
                efecto.set_volume(slider.value)
    audio.save()



def menu_pausa(screen, bg_anim, fondo_pausa):
    global selected_element_index, last_input_method, hover_casillas, ultimo_hover_index
    selected_element_index = 0
    last_input_method = "keyboard"
    hover_casillas = [False] * 5
    ultimo_hover_index = 0

    iniciar_cursor_menu()
    pygame.display.set_caption("KaBoom - Pausa")
    clock = pygame.time.Clock()

    if not hasattr(bg_anim, 'update') or not hasattr(bg_anim, 'draw'):
        class DummyBG:
            def update(self): pass

            def draw(self, s): pass

        bg_anim = DummyBG()

    pygame.joystick.init()
    mandos = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for mando in mandos:
        mando.init()

    fondo_gris, rect_fondo_gris = inicializar_componentes_ui(screen)
    sliders = crear_sliders(rect_fondo_gris)

    # Estado inicial de navegación por teclado.
    selected_element_index = 0
    last_input_method = "keyboard"
    hover_casillas = [False] * 5

    while True:
        pygame.mixer.pause()
        resultado = manejar_eventos(sliders, screen, bg_anim)
        if resultado == "ATRAS":
            return

        screen.blit(fondo_pausa, (0,0))
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 85))
        screen.blit(overlay, (0, 0))
        dibujar_ui(screen, bg_anim, fondo_gris, rect_fondo_gris, sliders)
        actualizar_cursor_menu()
        pygame.display.flip()
        clock.tick(60)


# CONFIRMAR CIERRE DEL JUEGO
def confirmar_salida(screen, bg_anim, fondo_anterior):
    global last_input_method
    clock = pygame.time.Clock()
    seleccion = 0  # 0 = SI, 1 = NO
    font = pygame.font.SysFont(None, 30)
    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()

        # Restaurar el fondo anterior
        screen.blit(fondo_anterior, (0, 0))

        # Capa translúcida suave
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 40))  # Muy tenue
        screen.blit(overlay, (0, 0))

        # Cuadro central
        ancho_ventana, alto_ventana = 400, 200
        ventana_rect = pygame.Rect(
            (screen.get_width() - ancho_ventana) // 2,
            (screen.get_height() - alto_ventana) // 2,
            ancho_ventana,
            alto_ventana
        )

        pygame.draw.rect(screen, (50, 50, 50), ventana_rect, border_radius=12)
        pygame.draw.rect(screen, BLANCO, ventana_rect, width=3, border_radius=12)

        texto = font.render("¿Desea salir del juego?", True, BLANCO)
        texto_rect = texto.get_rect(center=(ventana_rect.centerx, ventana_rect.top + 50))
        screen.blit(texto, texto_rect)

        # Botones SI y NO
        boton_ancho = 100
        boton_alto = 40
        espacio = 50

        si_rect = pygame.Rect(
            ventana_rect.centerx - boton_ancho - espacio // 2,
            ventana_rect.centery + 30,
            boton_ancho,
            boton_alto
        )
        no_rect = pygame.Rect(
            ventana_rect.centerx + espacio // 2,
            ventana_rect.centery + 30,
            boton_ancho,
            boton_alto
        )

        # Hover con ratón
        hover_si = si_rect.collidepoint(mouse_pos)
        hover_no = no_rect.collidepoint(mouse_pos)

        for event in pygame.event.get():
            registrar_actividad_cursor(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEMOTION:
                last_input_method = "mouse"
                if hover_si:
                    seleccion = 0
                elif hover_no:
                    seleccion = 1

            elif event.type == pygame.MOUSEBUTTONDOWN:
                last_input_method = "mouse"
                if si_rect.collidepoint(mouse_pos):
                    from EstadoPartida import reiniciar_estado
                    reiniciar_estado()
                    from PantallaConfigPartida import pantalla2_main
                    from PantallaPrincipal import BackgroundAnimation, crear_pantalla_completa
                    screen = crear_pantalla_completa()
                    bg_anim = BackgroundAnimation(screen.get_width(), screen.get_height())
                    pantalla2_main(screen, bg_anim)
                    return
                elif no_rect.collidepoint(mouse_pos):
                    return

            elif event.type == pygame.KEYDOWN:
                last_input_method = "keyboard"
                if event.key in [pygame.K_LEFT, pygame.K_a]:
                    seleccion = 0
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    seleccion = 1
                elif event.key == pygame.K_RETURN:
                    if seleccion == 0:
                        from EstadoPartida import reiniciar_estado
                        reiniciar_estado()
                        from PantallaConfigPartida import pantalla2_main
                        from PantallaPrincipal import BackgroundAnimation, crear_pantalla_completa
                        screen = crear_pantalla_completa()
                        bg_anim = BackgroundAnimation(screen.get_width(), screen.get_height())
                        pantalla2_main(screen, bg_anim)
                        return
                    else:
                        return

            elif event.type == pygame.JOYHATMOTION:
                last_input_method = "gamepad"
                hat_x, hat_y = event.value
                if hat_x < 0:
                    seleccion = 0
                elif hat_x > 0:
                    seleccion = 1

            elif event.type == pygame.JOYAXISMOTION:
                last_input_method = "gamepad"
                axis_x = event.axis
                axis_value = event.value
                if axis_x == 0:
                    if axis_value < -0.5:
                        seleccion = 0
                    elif axis_value > 0.5:
                        seleccion = 1

            elif event.type == pygame.JOYBUTTONDOWN:
                last_input_method = "gamepad"
                if event.button == 0:  # Botón A
                    if seleccion == 0:
                        from EstadoPartida import reiniciar_estado
                        reiniciar_estado()
                        from PantallaConfigPartida import pantalla2_main
                        from PantallaPrincipal import BackgroundAnimation, crear_pantalla_completa
                        screen = crear_pantalla_completa()
                        bg_anim = BackgroundAnimation(screen.get_width(), screen.get_height())
                        pantalla2_main(screen, bg_anim)
                        return
                    else:
                        return

        # Pintar botones con hover y selección
        for i, rect in enumerate([si_rect, no_rect]):
            if i == 0:
                hover = hover_si
                texto_btn = "SI"
            else:
                hover = hover_no
                texto_btn = "NO"

            if seleccion == i:
                color_fondo = (220, 255, 220)  # mismo color para teclado o ratón
            else:
                color_fondo = GRIS_OSCURO

            pygame.draw.rect(screen, color_fondo, rect, border_radius=6)
            pygame.draw.rect(screen, BLANCO, rect, width=2, border_radius=6)

            label = font.render(texto_btn, True, ROJO)
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)

        actualizar_cursor_menu()
        pygame.display.flip()
        clock.tick(60)

