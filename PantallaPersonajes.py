import pygame
import sys
import math
from ConfiguraciónMandos import gestor_jugadores
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

pygame.init()

if not pygame.mixer.get_init():
    pygame.mixer.init()
import os
from pygame import mixer

# Inicializar sonidos de selección
SONIDOS_PERSONAJE = {
    "Mork": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Yeeaah.mp3")),
    "Mortis": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Mortis.mp3")),
    "Calvo": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Calvo.mp3")),
    "Guerrero Negro": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Guerrero Negro.mp3")),
    "Guerrero Rojo": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Guerrero Rojo.mp3")),
    "Guerrero Blanco": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Guerrero Blanco.mp3")),
    "Vael": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Vael.mp3")),
    "Grimfang": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Grimfang.mp3")),
    "Guerrero Azul": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Sonido raro.mp3")),
    "Warlord": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Warlord.mp3")),
    "Ragnar": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Gladiador.mp3")),
    "Sarthus": mixer.Sound(os.path.join("Media", "Sonidos_juego", "Escoger_personaje", "Gladiador.mp3")),

}
# Opcional: ajustar volumen
for s in SONIDOS_PERSONAJE.values():
    s.set_volume(1.0)

# Diccionario temporal para guardar estado de mandos desconectados
temporizador_listos = {}  # Diccionario para guardar si un jugador está listo
estado_mandos_desconectados = {}
recien_unidos = set()

mensaje_error = ""
mensaje_timer = 0


def reiniciar_estado_personajes():
    global temporizador_listos, estado_mandos_desconectados, recien_unidos, mensaje_error, mensaje_timer
    temporizador_listos.clear()
    estado_mandos_desconectados.clear()
    recien_unidos.clear()
    mensaje_error = ""
    mensaje_timer = 0
    print("[PANTALLA_PERSONAJES] Estado local reseteado.")


def draw_personaje_con_bombeo(screen, imagen, texto, center, flecha_izq, flecha_der, mostrar_flechas, bombeo=True):
    tiempo = pygame.time.get_ticks() / 300.0
    factor = 1 + 0.02 * math.sin(tiempo) if bombeo else 1.0

    ancho_original, alto_original = imagen.get_size()
    ancho_bombeo = int(ancho_original * factor)
    alto_bombeo = int(alto_original * factor)
    imagen_bombeada = pygame.transform.scale(imagen, (ancho_bombeo, alto_bombeo))
    imagen_rect = imagen_bombeada.get_rect(center=center)
    screen.blit(imagen_bombeada, imagen_rect)

    fuente = pygame.font.Font(None, size=20)
    texto_render = fuente.render(texto, True, (0, 0, 0))
    texto_rect = texto_render.get_rect(center=(center[0], imagen_rect.bottom + 10))
    screen.blit(texto_render, texto_rect)

    if mostrar_flechas:
        y_flechas = texto_rect.centery
        flecha_izq_rect = flecha_izq.get_rect(midright=(center[0] - 52, y_flechas))
        flecha_der_rect = flecha_der.get_rect(midleft=(center[0] + 52, y_flechas))
        screen.blit(flecha_izq, flecha_izq_rect)
        screen.blit(flecha_der, flecha_der_rect)

    return imagen_rect


def draw_mensaje_inicio(screen, imagen_rect, tipo_jugador, listo):
    fuente = pygame.font.Font(None, size=22)
    if listo:
        pygame.draw.rect(screen, (255, 255, 0), (imagen_rect.centerx - 60, imagen_rect.bottom + 35, 120, 30))
        texto = "LISTO"
    else:
        texto = "Enter para empezar" if tipo_jugador == "teclado" else "A para empezar"
    texto_render = fuente.render(texto, True, (0, 0, 0))
    texto_rect = texto_render.get_rect(center=(imagen_rect.centerx, imagen_rect.bottom + 50))
    screen.blit(texto_render, texto_rect)


def draw_texto_inferior_bombeo(screen, texto, pos_centro):
    tiempo = pygame.time.get_ticks() / 300.0
    factor = 1 + 0.02 * math.sin(tiempo)
    fuente = pygame.font.Font(None, size=26)
    texto_render = fuente.render(texto, True, (255, 255, 255))
    ancho = int(texto_render.get_width() * factor)
    alto = int(texto_render.get_height() * factor)
    texto_escalado = pygame.transform.scale(texto_render, (ancho, alto))
    rect = texto_escalado.get_rect(center=pos_centro)
    screen.blit(texto_escalado, rect)


def draw_etiqueta_jugador(screen, texto, posicion):
    fuente = pygame.font.Font(None, size=24)
    texto_render = fuente.render(texto, True, (0, 0, 0))
    texto_rect = texto_render.get_rect()
    texto_rect.topright = (posicion[0] + 70, posicion[1] - 70)
    screen.blit(texto_render, texto_rect)


def draw_base_cpu(screen, center, tamano=(160, 160)):
    rect = pygame.Rect(0, 0, tamano[0], tamano[1])
    rect.center = center
    pygame.draw.rect(screen, (255, 255, 255), rect)
    pygame.draw.rect(screen, (0, 0, 0), rect, width=2)


def obtener_id_estado_jugador(jugador):
    if jugador is None:
        return None
    if jugador["tipo"] == "teclado":
        return "teclado"
    return jugador.get("instance_id")


def limpiar_listos_huerfanos(gestor, listos):
    ids_validos = {
        obtener_id_estado_jugador(jugador)
        for jugador in gestor.todos()
        if obtener_id_estado_jugador(jugador) is not None
    }
    for clave in list(listos.keys()):
        if clave not in ids_validos:
            del listos[clave]


def obtener_ultima_cpu(gestor):
    for jugador in reversed(gestor.todos()):
        if jugador["tipo"] == "cpu":
            return jugador
    return None


def obtener_cpu_editando(gestor, listos):
    for jugador in reversed(gestor.todos()):
        if jugador["tipo"] == "cpu" and not listos.get(obtener_id_estado_jugador(jugador), False):
            return jugador
    return None


def obtener_rects_flechas(center, imagen, flecha_izq, flecha_der, bombeo=True):
    tiempo = pygame.time.get_ticks() / 300.0
    factor = 1 + 0.02 * math.sin(tiempo) if bombeo else 1.0
    _, alto_original = imagen.get_size()
    alto_bombeo = int(alto_original * factor)
    y_flechas = center[1] + (alto_bombeo // 2) + 10
    return (
        flecha_izq.get_rect(midright=(center[0] - 52, y_flechas)),
        flecha_der.get_rect(midleft=(center[0] + 52, y_flechas)),
    )


def procesar_cancelacion_j1(gestor, listos):
    ultima_cpu = obtener_ultima_cpu(gestor)
    if ultima_cpu is not None:
        clave_cpu = obtener_id_estado_jugador(ultima_cpu)
        if listos.get(clave_cpu, False):
            del listos[clave_cpu]
        else:
            gestor.jugadores.remove(ultima_cpu)
            gestor.reordenar_jugadores()
            limpiar_listos_huerfanos(gestor, listos)
        return True

    jugador1 = gestor.get(0)
    if jugador1 is None:
        return False

    clave_j1 = obtener_id_estado_jugador(jugador1)
    if listos.get(clave_j1, False):
        del listos[clave_j1]
    else:
        gestor.jugadores.remove(jugador1)
        gestor.reordenar_jugadores()
        limpiar_listos_huerfanos(gestor, listos)
    return True


# Gestión de las ranuras de CPU que configura el jugador 1.
def procesar_input_j1_cpu(tipo_input, gestor, listos, nombres_personajes, sonidos):
    cpu_editando = obtener_cpu_editando(gestor, listos)

    if cpu_editando:
        id_cpu = obtener_id_estado_jugador(cpu_editando)
        if tipo_input == "derecha":
            cpu_editando["indice"] = (cpu_editando.get("indice", 0) + 1) % len(nombres_personajes)
            return True
        elif tipo_input == "izquierda":
            cpu_editando["indice"] = (cpu_editando.get("indice", 0) - 1) % len(nombres_personajes)
            return True
        elif tipo_input == "confirmar":
            listos[id_cpu] = True
            nombre = nombres_personajes[cpu_editando["indice"]]
            if nombre in sonidos:
                sonidos[nombre].play()
            return True
    else:
        if len(gestor.todos()) < gestor.max_jugadores:
            if tipo_input in ["derecha", "izquierda"]:
                nuevo_index = gestor.unir_cpu()
                if nuevo_index:
                    jug_cpu = gestor.get(nuevo_index - 1)
                    jug_cpu["indice"] = 0
                    return True
    return False


# -----------------------------------------------------

def pantalla_personajes(screen, bg_anim):
    global mensaje_error, mensaje_timer
    display_screen = screen
    screen = crear_superficie_menu_logica()
    iniciar_cursor_menu()

    pygame.joystick.init()
    mandos = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for mando in mandos:
        mando.init()

    clock = pygame.time.Clock()
    pygame.display.set_caption("Pantalla Personajes")

    # Botón de vuelta al menú de mapas.
    atras = pygame.transform.scale(pygame.image.load("Media/Menu/Botones/siguiente.png"), (40, 40))
    atras_rotate = pygame.transform.rotate(atras, 180)
    atras_rect = atras_rotate.get_rect(bottomright=(70, screen.get_height() - 25))

    # Botón para iniciar la partida cuando todos estén listos.
    siguiente = pygame.transform.scale(pygame.image.load("Media/Menu/Botones/siguiente.png").convert_alpha(), (40, 40))
    siguiente_rect = siguiente.get_rect(bottomright=(screen.get_width() - 25, screen.get_height() - 25))

    # Botón de ajustes.
    audio = pygame.transform.scale(pygame.image.load("Media/Menu/Botones/settings.png"), (50, 40))
    audio_rect = audio.get_rect(topleft=(25, 25))

    # Iconos de ayuda visual para teclado y mando.
    imagen_boton_b = pygame.image.load("Media/Menu/Botones/boton_B.png").convert_alpha()
    imagen_tecla_escape = pygame.image.load("Media/Menu/Botones/escape.png").convert_alpha()
    imagen_boton_options = pygame.image.load("Media/Menu/Botones/options.png").convert_alpha()
    imagen_boton_a = pygame.image.load("Media/Menu/Botones/boton_A.png").convert_alpha()
    imagen_tecla_control = pygame.image.load("Media/Menu/Botones/tecla_control.png").convert_alpha()
    imagen_tecla_enter = pygame.image.load("Media/Menu/Botones/enter.png").convert_alpha()
    imagen_boton_e = pygame.image.load("Media/Menu/Botones/boton_E.png").convert_alpha()
    imagen_boton_d = pygame.image.load("Media/Menu/Botones/boton_D.png").convert_alpha()
    imagen_boton_pause = pygame.image.load("Media/Menu/Botones/pause.png").convert_alpha()

    # Escalado base de iconos de ayuda.
    imagen_boton_b = pygame.transform.scale(imagen_boton_b, (50, 50))
    imagen_boton_a = pygame.transform.scale(imagen_boton_a, (50, 50))
    imagen_boton_options = pygame.transform.scale(imagen_boton_options, (40, 40))
    imagen_tecla_escape = pygame.transform.scale(imagen_tecla_escape, (40, 40))
    imagen_tecla_control = pygame.transform.scale(imagen_tecla_control, (50, 40))
    imagen_tecla_enter = pygame.transform.scale(imagen_tecla_enter, (50, 40))
    imagen_boton_e = pygame.transform.scale(imagen_boton_e, (50, 50))
    imagen_boton_d = pygame.transform.scale(imagen_boton_d, (50, 50))
    imagen_boton_pause = pygame.transform.scale(imagen_boton_pause, (40, 40))

    # FONDO
    fondo = pygame.transform.scale(pygame.image.load("Media/Menu/fondobasico.png").convert_alpha(), (750, 450))
    fondo_rect = fondo.get_rect(midright=(screen.get_width(), screen.get_height() // 2))

    img_default = pygame.transform.scale(
        pygame.image.load("Media/Menu/Pantalla_personajes/selec_pers.png").convert_alpha(), (130, 130))
    img_teclado = pygame.transform.scale(
        pygame.image.load("Media/Menu/Pantalla_personajes/teclado.png").convert_alpha(), (160, 160))
    img_mando = pygame.transform.scale(pygame.image.load("Media/Menu/Pantalla_personajes/mando.png").convert_alpha(),
                                       (160, 160))

    flecha_izq = pygame.transform.scale(
        pygame.image.load("Media/Menu/Pantalla_personajes/flecha_izquierda.png").convert_alpha(), (20, 20))
    flecha_der = pygame.transform.scale(
        pygame.image.load("Media/Menu/Pantalla_personajes/flecha_derecha.png").convert_alpha(), (20, 20))

    personajes_disponibles = [
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Mork.png").convert_alpha(), (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Guerrero Rojo.png").convert_alpha(),
                               (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Mortis.png").convert_alpha(), (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Grimfang.png").convert_alpha(), (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Warlord.png").convert_alpha(), (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Vael.png").convert_alpha(), (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Sarthus.png").convert_alpha(), (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Guerrero Azul.png").convert_alpha(),
                               (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Guerrero Blanco.png").convert_alpha(),
                               (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/Guerrero Negro.png").convert_alpha(),
                               (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/calvo.png").convert_alpha(), (90, 90)),
        pygame.transform.scale(pygame.image.load("Media/Jugadores/Dibujos/ragnar.png").convert_alpha(), (90, 90))
    ]

    nombres_personajes = ["Mork", "Guerrero Rojo", "Mortis", "Grimfang", "Warlord", "Vael", "Sarthus", "Guerrero Azul",
                          "Guerrero Blanco", "Guerrero Negro", "Calvo", "Ragnar"]

    personajes_centros = [(160 + i * (110 + 70), 280) for i in range(4)]

    mostrar_mensaje_j1 = False

    THRESHOLD = 0.6
    DEADZONE = 0.3
    joystick_ready = {}

    last_input_type = obtener_ultimo_dispositivo_menu()

    def intentar_iniciar_partida():
        global mensaje_error, mensaje_timer
        listos_confirmados = [valor for valor in temporizador_listos.values() if valor]
        total_conectados = len(gestor_jugadores.jugadores)
        if len(listos_confirmados) >= 2:
            if len(listos_confirmados) == total_conectados:
                from KaBoom import iniciar_partida
                iniciar_partida(display_screen)
                return True
            mensaje_error = "Todos tus rivales no están listos"
        else:
            mensaje_error = "¡Deben estar listos al menos 2 jugadores!"
        mensaje_timer = pygame.time.get_ticks()
        return False

    running = True
    while running:
        mouse_pos = convertir_mouse_a_logico(pygame.mouse.get_pos(), display_screen)

        for event in pygame.event.get():
            registrar_actividad_cursor(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Registra el último tipo de entrada para mostrar las ayudas visuales correctas.
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION,
                              pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION]:
                last_input_type = registrar_dispositivo_menu_evento(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                jugador1 = gestor_jugadores.get(0)
                id_j1 = obtener_id_estado_jugador(jugador1)
                j1_listo = bool(jugador1 and temporizador_listos.get(id_j1, False))

                if j1_listo:
                    cpu_editando = obtener_cpu_editando(gestor_jugadores, temporizador_listos)
                    if cpu_editando is not None:
                        idx_cpu = gestor_jugadores.todos().index(cpu_editando)
                        pos_cpu = personajes_centros[idx_cpu]
                        personaje_cpu = personajes_disponibles[cpu_editando["indice"]]
                        flecha_izq_rect, flecha_der_rect = obtener_rects_flechas(
                            pos_cpu, personaje_cpu, flecha_izq, flecha_der, bombeo=False
                        )
                        if flecha_izq_rect.collidepoint(mouse_pos):
                            procesar_input_j1_cpu("izquierda", gestor_jugadores, temporizador_listos,
                                                  nombres_personajes, SONIDOS_PERSONAJE)
                            continue
                        if flecha_der_rect.collidepoint(mouse_pos):
                            procesar_input_j1_cpu("derecha", gestor_jugadores, temporizador_listos,
                                                  nombres_personajes, SONIDOS_PERSONAJE)
                            continue
                    elif len(gestor_jugadores.todos()) < gestor_jugadores.max_jugadores:
                        idx_vacio = len(gestor_jugadores.todos())
                        pos_vacio = personajes_centros[idx_vacio]
                        flecha_izq_rect, flecha_der_rect = obtener_rects_flechas(
                            pos_vacio, img_default, flecha_izq, flecha_der, bombeo=True
                        )
                        if flecha_izq_rect.collidepoint(mouse_pos):
                            procesar_input_j1_cpu("izquierda", gestor_jugadores, temporizador_listos,
                                                  nombres_personajes, SONIDOS_PERSONAJE)
                            continue
                        if flecha_der_rect.collidepoint(mouse_pos):
                            procesar_input_j1_cpu("derecha", gestor_jugadores, temporizador_listos,
                                                  nombres_personajes, SONIDOS_PERSONAJE)
                            continue

                if atras_rect.collidepoint(mouse_pos):
                    from PantallaMapas import pantalla_mapas
                    gestor_jugadores.reset()
                    temporizador_listos.clear()
                    estado_mandos_desconectados.clear()
                    recien_unidos.clear()
                    pantalla_mapas(display_screen, bg_anim)
                    return

                if siguiente_rect.collidepoint(mouse_pos):
                    if intentar_iniciar_partida():
                        return

                if audio_rect.collidepoint(mouse_pos):
                    from PantallaAudio import pantalla_audio
                    pantalla_audio(display_screen, bg_anim, volver_callback=pantalla_personajes)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
                    from PantallaAudio import pantalla_audio
                    pantalla_audio(display_screen, bg_anim, volver_callback=pantalla_personajes)
                    continue

                jugador_teclado = gestor_jugadores.get_teclado()

                if jugador_teclado is None:
                    if event.key == pygame.K_ESCAPE:
                        if not gestor_jugadores.todos():
                            from PantallaMapas import pantalla_mapas
                            gestor_jugadores.reset()
                            temporizador_listos.clear()
                            estado_mandos_desconectados.clear()
                            recien_unidos.clear()
                            pantalla_mapas(display_screen, bg_anim)
                            return
                        continue
                    union_ok = gestor_jugadores.unir_teclado()
                    if union_ok:
                        limpiar_listos_huerfanos(gestor_jugadores, temporizador_listos)
                    continue

                if event.key == pygame.K_ESCAPE:
                    if gestor_jugadores.get(0) == jugador_teclado:
                        if procesar_cancelacion_j1(gestor_jugadores, temporizador_listos):
                            continue
                    id_jugador = obtener_id_estado_jugador(jugador_teclado)
                    if temporizador_listos.get(id_jugador, False):
                        del temporizador_listos[id_jugador]
                    else:
                        gestor_jugadores.eliminar_teclado()
                        limpiar_listos_huerfanos(gestor_jugadores, temporizador_listos)
                    continue

                jugador = jugador_teclado
                if jugador:
                    if event.key == pygame.K_RETURN:
                        if temporizador_listos.get("teclado", False):
                            jugador1 = gestor_jugadores.get(0)
                            if jugador1 and jugador1["tipo"] == "teclado":
                                if procesar_input_j1_cpu("confirmar", gestor_jugadores, temporizador_listos,
                                                         nombres_personajes, SONIDOS_PERSONAJE):
                                    continue
                                if intentar_iniciar_partida():
                                    return
                        else:
                            temporizador_listos["teclado"] = True
                            personaje_idx = jugador["indice"]
                            nombre = nombres_personajes[personaje_idx]
                            if nombre in SONIDOS_PERSONAJE:
                                SONIDOS_PERSONAJE[nombre].play()

                    elif not temporizador_listos.get("teclado"):
                        if event.key == pygame.K_LEFT:
                            jugador["indice"] = (jugador.get("indice", 0) - 1) % len(personajes_disponibles)
                        elif event.key == pygame.K_RIGHT:
                            jugador["indice"] = (jugador.get("indice", 0) + 1) % len(personajes_disponibles)

                    elif temporizador_listos.get("teclado") and gestor_jugadores.get(0) == jugador:
                        if event.key == pygame.K_LEFT:
                            procesar_input_j1_cpu("izquierda", gestor_jugadores, temporizador_listos,
                                                  nombres_personajes, SONIDOS_PERSONAJE)
                        elif event.key == pygame.K_RIGHT:
                            procesar_input_j1_cpu("derecha", gestor_jugadores, temporizador_listos, nombres_personajes,
                                                  SONIDOS_PERSONAJE)

            if event.type == pygame.JOYBUTTONDOWN:
                instance_id = event.instance_id
                jugador = gestor_jugadores.get_jugador_por_joy(instance_id)

                if jugador is None:
                    union_ok = gestor_jugadores.unir_mando(event.joy)
                    if union_ok:
                        limpiar_listos_huerfanos(gestor_jugadores, temporizador_listos)
                    continue

                id_jugador = obtener_id_estado_jugador(jugador)
                if event.button == 0:  # Botón A
                    if temporizador_listos.get(id_jugador, False):
                        if jugador == gestor_jugadores.get(0):
                            if procesar_input_j1_cpu("confirmar", gestor_jugadores, temporizador_listos,
                                                     nombres_personajes, SONIDOS_PERSONAJE):
                                continue
                            if intentar_iniciar_partida():
                                return
                    else:
                        temporizador_listos[id_jugador] = True
                        if jugador:
                            personaje_idx = jugador["indice"]
                            nombre = nombres_personajes[personaje_idx]
                            if nombre in SONIDOS_PERSONAJE:
                                SONIDOS_PERSONAJE[nombre].play()

                elif event.button in (7, 9):  # OPTIONS
                    from PantallaAudio import pantalla_audio
                    pantalla_audio(display_screen, bg_anim, volver_callback=pantalla_personajes)

                elif event.button == 1:  # B (Atrás)
                    if jugador == gestor_jugadores.get(0):
                        if procesar_cancelacion_j1(gestor_jugadores, temporizador_listos):
                            continue
                    elif temporizador_listos.get(id_jugador, False):
                        del temporizador_listos[id_jugador]
                    else:
                        gestor_jugadores.eliminar_jugador_por_joy(instance_id)
                        limpiar_listos_huerfanos(gestor_jugadores, temporizador_listos)

            if event.type == pygame.JOYHATMOTION:
                instance_id = event.instance_id
                jugador = gestor_jugadores.get_jugador_por_joy(instance_id)
                id_jugador = obtener_id_estado_jugador(jugador)
                if jugador and not temporizador_listos.get(id_jugador, False):
                    x, _ = event.value
                    if x == -1:
                        jugador["indice"] = (jugador.get("indice", 0) - 1) % len(personajes_disponibles)
                    elif x == 1:
                        jugador["indice"] = (jugador.get("indice", 0) + 1) % len(personajes_disponibles)
                elif jugador and temporizador_listos.get(id_jugador, False) and jugador == gestor_jugadores.get(0):
                    x, _ = event.value
                    if x == -1:
                        procesar_input_j1_cpu("izquierda", gestor_jugadores, temporizador_listos, nombres_personajes,
                                              SONIDOS_PERSONAJE)
                    elif x == 1:
                        procesar_input_j1_cpu("derecha", gestor_jugadores, temporizador_listos, nombres_personajes,
                                              SONIDOS_PERSONAJE)

            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:  # Eje horizontal del joystick izquierdo
                    instance_id = event.instance_id
                    jugador = gestor_jugadores.get_jugador_por_joy(instance_id)
                    id_jugador = obtener_id_estado_jugador(jugador)

                    if jugador and not temporizador_listos.get(id_jugador, False):
                        # Solo ejecutar si el jugador no está marcado como listo
                        if abs(event.value) > THRESHOLD and joystick_ready.get(instance_id, True):
                            if event.value > 0:
                                jugador["indice"] = (jugador.get("indice", 0) + 1) % len(personajes_disponibles)
                            else:
                                jugador["indice"] = (jugador.get("indice", 0) - 1) % len(personajes_disponibles)

                            joystick_ready[instance_id] = False
                        elif abs(event.value) < DEADZONE:
                            joystick_ready[instance_id] = True  # Rearme
                    elif jugador and temporizador_listos.get(id_jugador, False) and jugador == gestor_jugadores.get(0):
                        if abs(event.value) > THRESHOLD and joystick_ready.get(instance_id, True):
                            if event.value > 0:
                                procesar_input_j1_cpu("derecha", gestor_jugadores, temporizador_listos,
                                                      nombres_personajes, SONIDOS_PERSONAJE)
                            else:
                                procesar_input_j1_cpu("izquierda", gestor_jugadores, temporizador_listos,
                                                      nombres_personajes, SONIDOS_PERSONAJE)
                            joystick_ready[instance_id] = False
                        elif abs(event.value) < DEADZONE:
                            joystick_ready[instance_id] = True

            if event.type == pygame.JOYDEVICEREMOVED:
                instance_id = event.instance_id
                jugador = gestor_jugadores.get_jugador_por_joy(instance_id)
                if jugador:
                    id_jugador = obtener_id_estado_jugador(jugador)
                    if id_jugador in temporizador_listos:
                        del temporizador_listos[id_jugador]

                    if instance_id in joystick_ready:
                        del joystick_ready[instance_id]
                    gestor_jugadores.eliminar_jugador_por_joy(instance_id)
                    limpiar_listos_huerfanos(gestor_jugadores, temporizador_listos)

            if event.type == pygame.JOYDEVICEADDED:
                nuevo_mando = pygame.joystick.Joystick(event.device_index)
                nuevo_mando.init()

        bg_anim.update()
        bg_anim.draw(display_screen)
        screen.fill((0, 0, 0, 0))
        screen.blit(fondo, fondo_rect)

        for i in range(4):
            pos = personajes_centros[i]
            jugador = gestor_jugadores.get(i)
            if jugador and "indice" in jugador:
                tipo_jugador = jugador["tipo"]
                img_base = None
                if tipo_jugador == "teclado":
                    img_base = img_teclado
                elif tipo_jugador == "mando":
                    img_base = img_mando
                elif tipo_jugador == "cpu":
                    draw_base_cpu(screen, pos)
                if img_base is not None:
                    base_rect = img_base.get_rect(center=pos)
                    screen.blit(img_base, base_rect)

                etiqueta = f"J{i + 1}"
                if tipo_jugador == "cpu":
                    etiqueta = "CPU"
                draw_etiqueta_jugador(screen, etiqueta, pos)

                personaje_img = personajes_disponibles[jugador["indice"]]
                nombre_personaje = nombres_personajes[jugador["indice"]]

                id_jugador = obtener_id_estado_jugador(jugador)
                listo = temporizador_listos.get(id_jugador, False)
                is_cpu_editing = (tipo_jugador == "cpu" and not listo)

                rect_img = draw_personaje_con_bombeo(screen, personaje_img, nombre_personaje, pos, flecha_izq,
                                                     flecha_der, (not listo or is_cpu_editing), bombeo=False)

                if tipo_jugador == "cpu":
                    fuente = pygame.font.Font(None, size=22)
                    if listo:
                        pygame.draw.rect(screen, (255, 255, 0), (rect_img.centerx - 60, rect_img.bottom + 35, 120, 30))
                        texto_cpu = "LISTO"
                    else:
                        texto_cpu = "J1: Confirma skin"
                    texto_render = fuente.render(texto_cpu, True, (0, 0, 0))
                    texto_rect = texto_render.get_rect(center=(rect_img.centerx, rect_img.bottom + 50))
                    screen.blit(texto_render, texto_rect)
                else:
                    draw_mensaje_inicio(screen, rect_img, tipo_jugador, listo)
            else:
                j1 = gestor_jugadores.get(0)
                j1_listo = False
                if j1:
                    id_j1 = obtener_id_estado_jugador(j1)
                    j1_listo = temporizador_listos.get(id_j1, False)

                es_primer_vacio = (i == len(gestor_jugadores.todos()))
                if j1_listo and es_primer_vacio:
                    rect_img = draw_personaje_con_bombeo(screen, img_default, "NINGUNO", pos, flecha_izq, flecha_der,
                                                         True, bombeo=True)
                    fuente_cpu = pygame.font.Font(None, size=20)
                    texto_cpu = fuente_cpu.render("J1 puedes añadir a la CPU", True, (0, 0, 0))
                    texto_cpu_rect = texto_cpu.get_rect(center=(rect_img.centerx, rect_img.bottom + 50))
                    screen.blit(texto_cpu, texto_cpu_rect)
                else:
                    draw_personaje_con_bombeo(screen, img_default, "NINGUNO", pos, flecha_izq, flecha_der, False,
                                              bombeo=True)

        draw_texto_inferior_bombeo(screen, "Pulsa para unirte", (screen.get_width() // 2, screen.get_height() - 30))

        for img, rect in [(atras_rotate, atras_rect), (siguiente, siguiente_rect), (audio, audio_rect)]:
            if rect.collidepoint(mouse_pos):
                hover = pygame.transform.scale(img, (int(rect.width * 1.1), int(rect.height * 1.1)))
                rect_hover = hover.get_rect(center=rect.center)
                screen.blit(hover, rect_hover)
            else:
                screen.blit(img, rect)

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

        font2 = pygame.font.Font(None, 36)
        title_surf = font2.render("PERSONAJES Y JUGADORES", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(537, 105))
        screen.blit(title_surf, title_rect)

        # Aviso de inicio cuando todos los jugadores conectados están listos.
        listos = [j for j in temporizador_listos.values() if j]
        total_conectados = len(gestor_jugadores.jugadores)
        mostrar_mensaje_j1 = len(listos) >= 2 and len(listos) == total_conectados

        if mensaje_error and pygame.time.get_ticks() - mensaje_timer < 3000:
            font = pygame.font.Font(None, 30)
            error_surf = font.render(mensaje_error, True, (255, 0, 0))
            error_rect = error_surf.get_rect(center=(screen.get_width() // 2, screen.get_height() - 100))
            screen.blit(error_surf, error_rect)

        if mostrar_mensaje_j1:
            font = pygame.font.Font(None, 28)
            aviso_surf = font.render("Jugador 1 puedes iniciar partida", True, (0, 100, 0))
            aviso_rect = aviso_surf.get_rect(center=(screen.get_width() // 2, screen.get_height() - 130))

            resaltado = pygame.Surface((aviso_rect.width, aviso_rect.height // 2), pygame.SRCALPHA)
            resaltado.fill((180, 255, 180, 120))

            screen.blit(resaltado, (aviso_rect.left, aviso_rect.top + aviso_rect.height // 2 - 4))

            screen.blit(aviso_surf, aviso_rect)

        presentar_menu_logico(display_screen, screen)
        actualizar_cursor_menu()
        pygame.display.flip()
        clock.tick(60)
