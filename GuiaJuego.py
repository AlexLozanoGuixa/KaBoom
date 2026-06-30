import os
import sys

import pygame

from PantallaPrincipal import (
    actualizar_cursor_menu,
    iniciar_cursor_menu,
    registrar_actividad_cursor,
)


RUTA_PAGINAS = os.path.join("Media", "Menu", "GuiaJuego")
COLOR_PANEL = (224, 224, 220)
COLOR_CABECERA = (31, 45, 38)
COLOR_FONDO_LECTURA = (186, 190, 184)
COLOR_BARRA = (92, 102, 95)
COLOR_DESLIZADOR = (32, 184, 95)


def obtener_instance_id_evento(event):
    return getattr(event, "instance_id", getattr(event, "joy", None))


def evento_pertenece_solicitante(event, solicitante):
    dispositivo = solicitante["dispositivo"]
    if dispositivo == "teclado":
        return event.type in (
            pygame.KEYDOWN,
            pygame.KEYUP,
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEWHEEL,
        )
    return (
        event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION)
        and obtener_instance_id_evento(event) == dispositivo
    )


def obtener_joystick_solicitante(solicitante):
    dispositivo = solicitante["dispositivo"]
    if dispositivo == "teclado":
        return None
    for indice in range(pygame.joystick.get_count()):
        try:
            joystick = pygame.joystick.Joystick(indice)
            if not joystick.get_init():
                joystick.init()
            if joystick.get_instance_id() == dispositivo:
                return joystick
        except pygame.error:
            continue
    return None


def cargar_paginas(ancho_maximo):
    paginas = []
    rutas = [
        os.path.join(RUTA_PAGINAS, nombre)
        for nombre in sorted(os.listdir(RUTA_PAGINAS))
        if nombre.lower().endswith(".png")
    ]
    for ruta in rutas:
        pagina = pygame.image.load(ruta).convert()
        if pagina.get_width() > ancho_maximo:
            escala = ancho_maximo / pagina.get_width()
            pagina = pygame.transform.smoothscale(
                pagina,
                (ancho_maximo, max(1, round(pagina.get_height() * escala))),
            )
        paginas.append(pagina)
    return paginas


def cargar_boton_retorno(screen, metodo):
    escala = min(screen.get_width() / 800, screen.get_height() / 600)
    lado_flecha = max(40, round(40 * escala))
    flecha = pygame.image.load("Media/Menu/Botones/siguiente.png").convert_alpha()
    flecha = pygame.transform.rotate(flecha, 180)
    flecha = pygame.transform.smoothscale(flecha, (lado_flecha, lado_flecha))

    if metodo == "arcade":
        ruta_ayuda = "Media/Menu/Botones/boton_E.png"
        lado_ayuda = max(50, round(50 * escala))
    elif metodo == "gamepad":
        ruta_ayuda = "Media/Menu/Botones/boton_B.png"
        lado_ayuda = max(50, round(50 * escala))
    else:
        ruta_ayuda = "Media/Menu/Botones/escape.png"
        lado_ayuda = max(40, round(40 * escala))

    ayuda = pygame.image.load(ruta_ayuda).convert_alpha()
    ayuda = pygame.transform.smoothscale(ayuda, (lado_ayuda, lado_ayuda))
    margen = max(24, round(25 * escala))
    rect_flecha = flecha.get_rect(bottomleft=(margen, screen.get_height() - margen))
    rect_ayuda = ayuda.get_rect(midleft=(rect_flecha.right + max(8, round(8 * escala)), rect_flecha.centery))
    return flecha, rect_flecha, ayuda, rect_ayuda


def calcular_pagina_actual(scroll, posiciones_paginas):
    referencia = scroll + 20
    actual = 0
    for indice, (inicio, fin) in enumerate(posiciones_paginas):
        if referencia >= inicio:
            actual = indice
        if inicio <= referencia < fin:
            break
    return actual


def pantalla_guia(screen, solicitante=None, fondo_origen=None):
    """Muestra la guía completa dentro del juego y limita el control al dispositivo de acceso."""
    if solicitante is None:
        solicitante = {"dispositivo": "teclado", "metodo": "keyboard"}

    iniciar_cursor_menu()
    pygame.display.set_caption("KaBoom - Guía del juego")
    clock = pygame.time.Clock()
    fondo_origen = fondo_origen.copy() if fondo_origen is not None else screen.copy()

    ancho_pantalla, alto_pantalla = screen.get_size()
    ancho_panel = min(round(ancho_pantalla * 0.78), 1120)
    alto_panel = min(round(alto_pantalla * 0.86), 900)
    rect_panel = pygame.Rect(0, 0, ancho_panel, alto_panel)
    rect_panel.center = (ancho_pantalla // 2, alto_pantalla // 2)

    alto_cabecera = max(58, round(alto_panel * 0.075))
    alto_pie = max(34, round(alto_panel * 0.05))
    rect_visor = pygame.Rect(
        rect_panel.left + 18,
        rect_panel.top + alto_cabecera,
        rect_panel.width - 48,
        rect_panel.height - alto_cabecera - alto_pie,
    )

    paginas = cargar_paginas(rect_visor.width - 32)
    if not paginas:
        raise FileNotFoundError(f"No se encontraron páginas de la guía en {RUTA_PAGINAS}")

    separacion = 24
    posiciones_paginas = []
    altura_total = 14
    for pagina in paginas:
        inicio = altura_total
        altura_total += pagina.get_height()
        posiciones_paginas.append((inicio, altura_total))
        altura_total += separacion
    altura_total += 14 - separacion
    scroll_maximo = max(0, altura_total - rect_visor.height)

    flecha, rect_flecha, ayuda, rect_ayuda = cargar_boton_retorno(
        screen, solicitante.get("metodo", "keyboard")
    )
    permite_raton = solicitante["dispositivo"] == "teclado"
    scroll = 0.0
    running = True

    font_titulo = pygame.font.SysFont(None, max(28, round(alto_panel * 0.044)), bold=True)
    font_pie = pygame.font.SysFont(None, max(18, round(alto_panel * 0.026)))

    while running:
        dt = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos() if permite_raton else (-1, -1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if not evento_pertenece_solicitante(event, solicitante):
                continue
            registrar_actividad_cursor(event)

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_LCTRL, pygame.K_RCTRL):
                    running = False
                elif event.key == pygame.K_DOWN:
                    scroll += 120
                elif event.key == pygame.K_UP:
                    scroll -= 120
                elif event.key == pygame.K_PAGEDOWN:
                    scroll += rect_visor.height * 0.8
                elif event.key == pygame.K_PAGEUP:
                    scroll -= rect_visor.height * 0.8

            elif event.type == pygame.MOUSEWHEEL:
                scroll -= event.y * 150

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if rect_flecha.collidepoint(mouse_pos):
                    running = False

            elif event.type == pygame.JOYBUTTONDOWN and event.button == 1:
                running = False

            elif event.type == pygame.JOYHATMOTION:
                if event.value[1] < 0:
                    scroll += 120
                elif event.value[1] > 0:
                    scroll -= 120

        if permite_raton:
            teclas = pygame.key.get_pressed()
            if teclas[pygame.K_DOWN]:
                scroll += 520 * dt
            elif teclas[pygame.K_UP]:
                scroll -= 520 * dt
        else:
            joystick = obtener_joystick_solicitante(solicitante)
            if joystick is not None and joystick.get_numaxes() > 1:
                eje_vertical = joystick.get_axis(1)
                if abs(eje_vertical) > 0.35:
                    scroll += eje_vertical * 680 * dt

        scroll = max(0.0, min(scroll, float(scroll_maximo)))

        screen.blit(fondo_origen, (0, 0))
        capa = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 145))
        screen.blit(capa, (0, 0))

        pygame.draw.rect(screen, COLOR_PANEL, rect_panel, border_radius=14)
        pygame.draw.rect(screen, (28, 35, 31), rect_panel, width=4, border_radius=14)
        rect_cabecera = pygame.Rect(rect_panel.left, rect_panel.top, rect_panel.width, alto_cabecera)
        pygame.draw.rect(
            screen,
            COLOR_CABECERA,
            rect_cabecera,
            border_top_left_radius=12,
            border_top_right_radius=12,
        )
        titulo = font_titulo.render("GUÍA DEL JUEGO", True, (255, 255, 255))
        screen.blit(titulo, titulo.get_rect(center=rect_cabecera.center))

        pygame.draw.rect(screen, COLOR_FONDO_LECTURA, rect_visor, border_radius=4)
        clip_anterior = screen.get_clip()
        screen.set_clip(rect_visor)
        for pagina, (inicio, fin) in zip(paginas, posiciones_paginas):
            y = rect_visor.top + inicio - round(scroll)
            if y < rect_visor.bottom and y + pagina.get_height() > rect_visor.top:
                x = rect_visor.centerx - pagina.get_width() // 2
                sombra = pygame.Rect(x + 5, y + 6, pagina.get_width(), pagina.get_height())
                pygame.draw.rect(screen, (112, 116, 112), sombra)
                screen.blit(pagina, (x, y))
        screen.set_clip(clip_anterior)

        if scroll_maximo > 0:
            rect_barra = pygame.Rect(rect_visor.right + 8, rect_visor.top, 10, rect_visor.height)
            pygame.draw.rect(screen, COLOR_BARRA, rect_barra, border_radius=5)
            alto_deslizador = max(42, round(rect_barra.height * rect_visor.height / altura_total))
            recorrido = rect_barra.height - alto_deslizador
            y_deslizador = rect_barra.top + round(recorrido * scroll / scroll_maximo)
            rect_deslizador = pygame.Rect(rect_barra.left, y_deslizador, rect_barra.width, alto_deslizador)
            pygame.draw.rect(screen, COLOR_DESLIZADOR, rect_deslizador, border_radius=5)

        pagina_actual = calcular_pagina_actual(scroll, posiciones_paginas) + 1
        texto_pie = font_pie.render(
            f"Página {pagina_actual} de {len(paginas)}  |  Desplazamiento vertical",
            True,
            (35, 40, 37),
        )
        posicion_pie = (rect_panel.centerx, rect_panel.bottom - alto_pie // 2)
        screen.blit(texto_pie, texto_pie.get_rect(center=posicion_pie))

        if permite_raton and rect_flecha.collidepoint(mouse_pos):
            flecha_hover = pygame.transform.smoothscale(
                flecha,
                (round(flecha.get_width() * 1.1), round(flecha.get_height() * 1.1)),
            )
            screen.blit(flecha_hover, flecha_hover.get_rect(center=rect_flecha.center))
        else:
            screen.blit(flecha, rect_flecha)
        screen.blit(ayuda, rect_ayuda)

        actualizar_cursor_menu()
        pygame.display.flip()
