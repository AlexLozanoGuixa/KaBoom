import pygame
import sys

# Importar configuración global para guardar selección
from Config import config
from PantallaPrincipal import (
    actualizar_cursor_menu,
    convertir_mouse_a_logico,
    crear_superficie_menu_logica,
    es_evento_control_arcade,
    es_evento_joystick_relevante,
    obtener_ultimo_dispositivo_menu,
    iniciar_cursor_menu,
    presentar_menu_logico,
    registrar_actividad_cursor,
    registrar_dispositivo_menu_evento,
)


def pantalla_mapas(screen, bg_anim):
    display_screen = screen
    screen = crear_superficie_menu_logica()
    global current_time
    clock = pygame.time.Clock()
    pygame.display.set_caption("Pantalla Mapas")
    iniciar_cursor_menu()


    # INICIALIZAR MANDOS
    pygame.joystick.init()
    mandos = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for mando in mandos:
        mando.init()

    # Cooldown para evitar repeticiones continuas al navegar con mando.
    mando_delay = 200
    last_input_time = pygame.time.get_ticks() - mando_delay

    # BOTON ATRAS
    atras = pygame.transform.scale(pygame.image.load("Media/Menu/Botones/siguiente.png"), (40, 40))
    atras_rotate = pygame.transform.rotate(atras, 180)
    atras_rect = atras_rotate.get_rect(bottomright=(70, screen.get_height() - 25))

    # BOTON SIGUIENTE
    siguiente = pygame.transform.scale(pygame.image.load("Media/Menu/Botones/siguiente.png"), (40, 40))
    siguiente_rect = siguiente.get_rect(bottomright=(screen.get_width() - 25, screen.get_height() - 25))

    # BOTON SETTINGS
    audio = pygame.transform.scale(pygame.image.load("Media/Menu/Botones/settings.png"), (50, 40))
    audio_rect = audio.get_rect(topleft=(25, 25))

    # MARCO CENTRAL
    marco = pygame.transform.scale(pygame.image.load("Media/Menu/Pantalla_mapas/Mapselect.png"), (750, 450))
    marco_rect = marco.get_rect(midright=(screen.get_width(), screen.get_height() // 2))

    # ACLARACIÓN VISUAL
    # Cargar imágenes
    imagen_boton_b = pygame.image.load("Media/Menu/Botones/boton_B.png").convert_alpha()
    imagen_tecla_escape = pygame.image.load("Media/Menu/Botones/escape.png").convert_alpha()
    imagen_boton_options = pygame.image.load("Media/Menu/Botones/options.png").convert_alpha()
    imagen_boton_a = pygame.image.load("Media/Menu/Botones/boton_A.png").convert_alpha()
    imagen_tecla_control = pygame.image.load("Media/Menu/Botones/tecla_control.png").convert_alpha()
    imagen_tecla_enter = pygame.image.load("Media/Menu/Botones/enter.png").convert_alpha()
    imagen_boton_e = pygame.image.load("Media/Menu/Botones/boton_E.png").convert_alpha()
    imagen_boton_d = pygame.image.load("Media/Menu/Botones/boton_D.png").convert_alpha()
    imagen_boton_pause = pygame.image.load("Media/Menu/Botones/pause.png").convert_alpha()

    # Redimensionar si es necesario
    imagen_boton_b = pygame.transform.scale(imagen_boton_b, (50, 50))
    imagen_boton_a = pygame.transform.scale(imagen_boton_a, (50, 50))
    imagen_boton_options = pygame.transform.scale(imagen_boton_options, (40, 40))
    imagen_tecla_escape = pygame.transform.scale(imagen_tecla_escape, (40, 40))
    imagen_tecla_control = pygame.transform.scale(imagen_tecla_control, (50, 40))
    imagen_tecla_enter = pygame.transform.scale(imagen_tecla_enter, (50, 40))
    imagen_boton_e = pygame.transform.scale(imagen_boton_e, (50, 50))
    imagen_boton_d = pygame.transform.scale(imagen_boton_d, (50, 50))
    imagen_boton_pause = pygame.transform.scale(imagen_boton_pause, (40, 40))

    # Nombres de los mapas
    map_names = ["CLASSIC VINTAGE", "SOBEK OASIS", "GREEN VALLEY"]
    font = pygame.font.Font(None, 26)
    name_surfs = [font.render(name, True, (255,255,255)) for name in map_names]

    # MAPAS
    mapas = []  # Miniatura, previsualización, rectángulo de clic y nombre renderizado.
    x = 185
    start_y = 220
    gap = 15
    for i in range(3):
        mini = pygame.image.load(f"Media/Menu/Pantalla_mapas/mapa{i+1}.png").convert_alpha()
        mini = pygame.transform.scale(mini, (120, 105))
        big = pygame.image.load(f"Media/Menu/Pantalla_mapas/mapa{i+1}big.png").convert_alpha()
        y = start_y + i * (100 + gap)
        rect = mini.get_rect(center=(x, y))
        mapas.append((mini, big, rect, name_surfs[i]))

    # Parámetros de contorno hover
    hover_color = (0, 255, 255)
    border_thickness = 4

    # Índice del mapa seleccionado (por defecto el primer mapa)
    selected_index = config.selected_map - 1

    # indices para doble click de raton y seleccionar mapa
    last_click_time = 0
    double_click_delay = 300  # milisegundos

    # Ajustar sensibilidad del eje del mando
    axis_ready = True
    THRESHOLD = 0.5
    DEADZONE = 0.2
    AXIS_REARM_DELAY = 120
    axis_last_value = 0.0
    axis_centered_since = None

    last_input_type = obtener_ultimo_dispositivo_menu()

    running = True
    while running:
        mouse_pos = convertir_mouse_a_logico(pygame.mouse.get_pos(), display_screen)
        mouse_click = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            registrar_actividad_cursor(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Registra el último tipo de entrada para mostrar las ayudas visuales correctas.
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION,
                              pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION]:
                last_input_type = registrar_dispositivo_menu_evento(event)

            if event.type == pygame.JOYDEVICEADDED:
                nuevo = pygame.joystick.Joystick(event.device_index)
                nuevo.init()
                mandos.append(nuevo)

            elif event.type == pygame.JOYHATMOTION and event.hat == 0:
                _, hat_y = event.value  # D-pad vertical para cambiar de fase.
                tiempo_actual = pygame.time.get_ticks()
                if tiempo_actual - last_input_time >= mando_delay:
                    if hat_y == -1:
                        selected_index = (selected_index + 1) % len(mapas)
                        last_input_time = tiempo_actual
                    elif hat_y == 1:
                        selected_index = (selected_index - 1) % len(mapas)
                        last_input_time = tiempo_actual
                    config.selected_map = selected_index + 1

            # Solo el primer mando controla la selección de mapa.
            elif event.type == pygame.JOYAXISMOTION:
                if event.axis == 1:  # eje vertical
                    tiempo_actual = pygame.time.get_ticks()
                    axis_last_value = event.value
                    if abs(event.value) > THRESHOLD:
                        axis_centered_since = None
                        if axis_ready and tiempo_actual - last_input_time >= mando_delay:
                            if event.value < 0:
                                selected_index = (selected_index - 1) % len(mapas)
                            else:
                                selected_index = (selected_index + 1) % len(mapas)
                            config.selected_map = selected_index + 1
                            last_input_time = tiempo_actual
                        axis_ready = False
                    elif abs(event.value) < DEADZONE and axis_centered_since is None:
                        axis_centered_since = tiempo_actual
                    elif abs(event.value) >= DEADZONE:
                        axis_centered_since = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    from PantallaConfigPartida import pantalla2_main
                    pantalla2_main(display_screen, bg_anim)
                    return

                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    from PantallaAudio import pantalla_audio
                    pantalla_audio(display_screen, bg_anim, volver_callback=pantalla_mapas)

                elif event.key == pygame.K_RETURN and selected_index >= 0:
                    from PantallaPersonajes import pantalla_personajes
                    pantalla_personajes(display_screen, bg_anim)
                    return

                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(mapas)
                    config.selected_map = selected_index + 1

                elif event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(mapas)
                    config.selected_map = selected_index + 1

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Botón izquierdo del ratón
                current_time = pygame.time.get_ticks()
                mouse_pos = convertir_mouse_a_logico(pygame.mouse.get_pos(), display_screen)

                # Botón ATRÁS
                if atras_rect.collidepoint(mouse_pos):
                    from PantallaConfigPartida import pantalla2_main
                    pantalla2_main(display_screen, bg_anim)
                    return

                # Botón SIGUIENTE
                if siguiente_rect.collidepoint(mouse_pos) and selected_index >= 0:
                    from PantallaPersonajes import pantalla_personajes
                    pantalla_personajes(display_screen, bg_anim)
                    return

                if audio_rect.collidepoint(mouse_pos):
                    from PantallaAudio import pantalla_audio
                    pantalla_audio(display_screen, bg_anim, volver_callback=pantalla_mapas)

                # CLIC SOBRE MAPA
                for idx, (mini, big, rect, name_surf) in enumerate(mapas):
                    if rect.collidepoint(mouse_pos):
                        if idx == selected_index and current_time - last_click_time <= double_click_delay:
                            # Doble clic sobre el mapa ya seleccionado → avanzar pantalla
                            from PantallaPersonajes import pantalla_personajes
                            pantalla_personajes(display_screen, bg_anim)
                            return
                        else:
                            # Selección normal de mapa
                            selected_index = idx
                            config.selected_map = idx + 1
                            last_click_time = current_time
                        break  # Salimos del bucle después de encontrar un mapa


            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # Botón A: avanzar a selección de personajes.
                    from PantallaPersonajes import pantalla_personajes
                    pantalla_personajes(display_screen, bg_anim)
                    return

                elif event.button == 1:  # Botón B: volver atrás.
                    from PantallaConfigPartida import pantalla2_main
                    pantalla2_main(display_screen, bg_anim)
                    return

                elif event.button in (7, 9):  # El botón Options abre los ajustes.
                    from PantallaAudio import pantalla_audio
                    pantalla_audio(display_screen, bg_anim, volver_callback=pantalla_mapas)
        if not axis_ready and abs(axis_last_value) < DEADZONE:
            tiempo_actual = pygame.time.get_ticks()
            if axis_centered_since is None:
                axis_centered_since = tiempo_actual
            elif tiempo_actual - axis_centered_since >= AXIS_REARM_DELAY:
                axis_ready = True
                axis_centered_since = None

        # Dibujar fondo y marco
        bg_anim.update()
        bg_anim.draw(display_screen)
        screen.fill((0, 0, 0, 0))
        screen.blit(marco, marco_rect)

        # Dibujar mapas, hover y selección fija
        for idx, (mini, big, rect, name_surf) in enumerate(mapas):
            screen.blit(mini, rect)
            if (selected_index == -1 and rect.collidepoint(mouse_pos)) or idx == selected_index:
                # dibujar contorno celeste
                hover_rect = rect.inflate(border_thickness, border_thickness)
                pygame.draw.rect(screen, hover_color, hover_rect, border_thickness)
                # vista previa grande
                preview = pygame.transform.scale(big, (405, 345))
                preview_rect = preview.get_rect(midright=(screen.get_width() - 30, screen.get_height() // 2))
                screen.blit(preview, preview_rect)
                # mostrar nombre debajo de la preview
                name_rect = name_surf.get_rect(midtop=(preview_rect.centerx + 20, preview_rect.bottom + 22))
                screen.blit(name_surf, name_rect)

        # Botones fijos
        for img, rc in [(atras_rotate, atras_rect), (siguiente, siguiente_rect), (audio, audio_rect)]:
            if rc.collidepoint(mouse_pos):
                screen.blit(pygame.transform.scale(img, (int(rc.width * 1.1), int(rc.height * 1.1))), rc)
            else:
                screen.blit(img, rc)

        # Ayudas visuales del control activo.
        if last_input_type == "arcade":
            imagen = imagen_boton_e
        elif last_input_type == "mando":
            imagen = imagen_boton_b
        else:
            imagen = imagen_tecla_escape

        pos_x = atras_rect.right + 10
        pos_y = atras_rect.centery - imagen.get_height() // 2
        screen.blit(imagen, (pos_x, pos_y))

        if last_input_type == "arcade":
            imagen = imagen_boton_d
        elif last_input_type == "mando":
            imagen = imagen_boton_a
        else:
            imagen = imagen_tecla_enter

        pos_x = siguiente_rect.left - imagen.get_width() - 10
        pos_y = siguiente_rect.centery - imagen.get_height() // 2
        screen.blit(imagen, (pos_x, pos_y))

        if last_input_type == "arcade":
            imagen = imagen_boton_pause
        elif last_input_type == "mando":
            imagen = imagen_boton_options
        else:
            imagen = imagen_tecla_control

        pos_x = audio_rect.right + 10
        pos_y = audio_rect.centery - imagen.get_height() // 2
        screen.blit(imagen, (pos_x, pos_y))

        # Mostrar título
        font = pygame.font.Font(None, 21)
        title_surf = font.render("SELECCIONA UNA FASE", True, (255,255,255))
        title_rect = title_surf.get_rect(center=(185, 130))
        screen.blit(title_surf, title_rect)

        # Mostrar título principal
        font2 = pygame.font.Font(None, 36)
        title_surf = font2.render("CAMPOS DE BATALLA", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(537, 98))
        screen.blit(title_surf, title_rect)

        presentar_menu_logico(display_screen, screen)
        actualizar_cursor_menu()
        pygame.display.flip()
        clock.tick(60)
