import pygame
import sys
from PantallaPrincipal import BackgroundAnimation


def pantalla_controles(screen):
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 40)
    font_opciones = pygame.font.SysFont(None, 28)

    bg_anim = BackgroundAnimation(screen.get_width(), screen.get_height())

    texto = font.render("Aprende los controles", True, (255, 255, 255))
    texto_rect = texto.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 260))

    ancho_fondo = 750
    alto_fondo = 450

    fondo_rect = pygame.Rect(
        (screen.get_width() - ancho_fondo) // 2,
        (screen.get_height() - alto_fondo) // 2,
        ancho_fondo,
        alto_fondo
    )

    escala_x = screen.get_width() / 800
    escala_y = screen.get_height() / 600

    flecha_original = pygame.image.load("Media/Menu/Botones/siguiente.png").convert_alpha()
    flecha_rotada = pygame.transform.rotate(flecha_original, 180)
    tamaño_base = (max(40, int(40 * escala_x)), max(40, int(40 * escala_y)))
    tamaño_hover = (max(45, int(44 * escala_x)), max(45, int(44 * escala_y)))
    flecha_img = pygame.transform.scale(flecha_rotada, tamaño_base)
    flecha_rect = flecha_img.get_rect()
    flecha_rect.bottomleft = (max(25, int(30 * escala_x)), screen.get_height() - max(25, int(25 * escala_y)))

    img_izq = pygame.image.load("Media/Menu/Controles/negroizquierda.png").convert_alpha()
    img_der = pygame.image.load("Media/Menu/Controles/negroderecha.png").convert_alpha()

    try:
        ruta_base_controles = "Media/Menu/Controles/"
        img_teclado_menu = pygame.image.load(ruta_base_controles + "tecladomenus.png").convert_alpha()
        img_teclado_combate = pygame.image.load(ruta_base_controles + "tecladocombate.png").convert_alpha()
        img_mando_menu = pygame.image.load(ruta_base_controles + "mandomenus.png").convert_alpha()
        img_mando_combate = pygame.image.load(ruta_base_controles + "mandocombate.png").convert_alpha()
    except pygame.error as e:
        print(f"Error al cargar una o más imágenes de controles: {e}")
        img_teclado_menu, img_teclado_combate, img_mando_menu, img_mando_combate = [pygame.Surface((1, 1)) for _ in
                                                                                    range(4)]

    try:
        fondo_controles_img = pygame.transform.scale(
            pygame.image.load("Media/Menu/Controles/menucontroles.png").convert_alpha(),
            (ancho_fondo, alto_fondo)
        )
    except pygame.error as e:
        print(f"Error al cargar 'menucontroles.png': {e}. Se usará un color sólido.")
        fondo_controles_img = None

    opciones_fila1 = ["Configuración de teclado", "Configuración de mando"]
    indice_fila1 = 0

    opciones_fila2 = ["Controles Menú", "Controles Combate"]
    indice_fila2 = 0

    fila_activa = 0

    flecha1_izq_pos = (fondo_rect.left + 165, fondo_rect.top + 30)
    flecha1_izq_size = (30, 20)
    flecha1_izq_hover_size = (35, 25)
    flecha1_der_pos = (fondo_rect.left + 555, fondo_rect.top + 30)
    flecha1_der_size = (30, 20)
    flecha1_der_hover_size = (35, 25)
    flecha2_izq_pos = (fondo_rect.left + 165, fondo_rect.top + 70)
    flecha2_izq_size = (30, 20)
    flecha2_izq_hover_size = (35, 25)
    flecha2_der_pos = (fondo_rect.left + 555, fondo_rect.top + 70)
    flecha2_der_size = (30, 20)
    flecha2_der_hover_size = (35, 25)

    flecha1_izq_img_base = pygame.transform.scale(img_izq, flecha1_izq_size)
    flecha1_izq_img_hover = pygame.transform.scale(img_izq, flecha1_izq_hover_size)
    flecha1_der_img_base = pygame.transform.scale(img_der, flecha1_der_size)
    flecha1_der_img_hover = pygame.transform.scale(img_der, flecha1_der_hover_size)
    flecha2_izq_img_base = pygame.transform.scale(img_izq, flecha2_izq_size)
    flecha2_izq_img_hover = pygame.transform.scale(img_izq, flecha2_izq_hover_size)
    flecha2_der_img_base = pygame.transform.scale(img_der, flecha2_der_size)
    flecha2_der_img_hover = pygame.transform.scale(img_der, flecha2_der_hover_size)

    flecha1_izq_rect = flecha1_izq_img_base.get_rect(topleft=flecha1_izq_pos)
    flecha1_der_rect = flecha1_der_img_base.get_rect(topleft=flecha1_der_pos)
    flecha2_izq_rect = flecha2_izq_img_base.get_rect(topleft=flecha2_izq_pos)
    flecha2_der_rect = flecha2_der_img_base.get_rect(topleft=flecha2_der_pos)

    joystick_threshold = 0.5
    joystick_timer = 0
    joystick_cooldown = 200

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        dt = clock.tick(60)
        joystick_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    fila_activa = 1 - fila_activa
                elif event.key == pygame.K_LEFT:
                    if fila_activa == 0:
                        indice_fila1 = (indice_fila1 - 1) % len(opciones_fila1)
                    elif fila_activa == 1:
                        indice_fila2 = (indice_fila2 - 1) % len(opciones_fila2)
                elif event.key == pygame.K_RIGHT:
                    if fila_activa == 0:
                        indice_fila1 = (indice_fila1 + 1) % len(opciones_fila1)
                    elif fila_activa == 1:
                        indice_fila2 = (indice_fila2 + 1) % len(opciones_fila2)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if flecha_rect.collidepoint(mouse_pos):
                        running = False
                    elif flecha1_izq_rect.collidepoint(mouse_pos):
                        fila_activa = 0
                        indice_fila1 = (indice_fila1 - 1) % len(opciones_fila1)
                    elif flecha1_der_rect.collidepoint(mouse_pos):
                        fila_activa = 0
                        indice_fila1 = (indice_fila1 + 1) % len(opciones_fila1)
                    elif flecha2_izq_rect.collidepoint(mouse_pos):
                        fila_activa = 1
                        indice_fila2 = (indice_fila2 - 1) % len(opciones_fila2)
                    elif flecha2_der_rect.collidepoint(mouse_pos):
                        fila_activa = 1
                        indice_fila2 = (indice_fila2 + 1) % len(opciones_fila2)

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1:
                    return
            elif event.type == pygame.JOYHATMOTION:
                if event.value[1] == 1 or event.value[1] == -1:
                    fila_activa = 1 - fila_activa
                elif event.value[0] == -1:
                    if fila_activa == 0:
                        indice_fila1 = (indice_fila1 - 1) % len(opciones_fila1)
                    elif fila_activa == 1:
                        indice_fila2 = (indice_fila2 - 1) % len(opciones_fila2)
                elif event.value[0] == 1:
                    if fila_activa == 0:
                        indice_fila1 = (indice_fila1 + 1) % len(opciones_fila1)
                    elif fila_activa == 1:
                        indice_fila2 = (indice_fila2 + 1) % len(opciones_fila2)

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            axis_x = joystick.get_axis(0)
            axis_y = joystick.get_axis(1)

            if joystick_timer >= joystick_cooldown:
                if axis_y < -joystick_threshold or axis_y > joystick_threshold:
                    fila_activa = 1 - fila_activa
                    joystick_timer = 0
                elif axis_x < -joystick_threshold:
                    if fila_activa == 0:
                        indice_fila1 = (indice_fila1 - 1) % len(opciones_fila1)
                    elif fila_activa == 1:
                        indice_fila2 = (indice_fila2 - 1) % len(opciones_fila2)
                    joystick_timer = 0
                elif axis_x > joystick_threshold:
                    if fila_activa == 0:
                        indice_fila1 = (indice_fila1 + 1) % len(opciones_fila1)
                    elif fila_activa == 1:
                        indice_fila2 = (indice_fila2 + 1) % len(opciones_fila2)
                    joystick_timer = 0

        bg_anim.update()
        bg_anim.draw(screen)


        if fondo_controles_img:
            screen.blit(fondo_controles_img, fondo_rect)
        else:
            pygame.draw.rect(screen, (30, 30, 150), fondo_rect, border_radius=20)

        screen.blit(texto, texto_rect)

        if flecha1_izq_rect.collidepoint(mouse_pos):
            screen.blit(flecha1_izq_img_hover, flecha1_izq_img_hover.get_rect(center=flecha1_izq_rect.center))
        else:
            screen.blit(flecha1_izq_img_base, flecha1_izq_rect)
        if flecha1_der_rect.collidepoint(mouse_pos):
            screen.blit(flecha1_der_img_hover, flecha1_der_img_hover.get_rect(center=flecha1_der_rect.center))
        else:
            screen.blit(flecha1_der_img_base, flecha1_der_rect)
        if flecha2_izq_rect.collidepoint(mouse_pos):
            screen.blit(flecha2_izq_img_hover, flecha2_izq_img_hover.get_rect(center=flecha2_izq_rect.center))
        else:
            screen.blit(flecha2_izq_img_base, flecha2_izq_rect)
        if flecha2_der_rect.collidepoint(mouse_pos):
            screen.blit(flecha2_der_img_hover, flecha2_der_img_hover.get_rect(center=flecha2_der_rect.center))
        else:
            screen.blit(flecha2_der_img_base, flecha2_der_rect)

        texto_opcion_fila1 = font_opciones.render(opciones_fila1[indice_fila1], True, (255, 255, 255))
        centro_x_f1 = flecha1_izq_rect.right + (flecha1_der_rect.left - flecha1_izq_rect.right) // 2
        texto_opcion_rect_f1 = texto_opcion_fila1.get_rect(center=(centro_x_f1, flecha1_izq_rect.centery))
        screen.blit(texto_opcion_fila1, texto_opcion_rect_f1)

        texto_opcion_fila2 = font_opciones.render(opciones_fila2[indice_fila2], True, (255, 255, 255))
        centro_x_f2 = flecha2_izq_rect.right + (flecha2_der_rect.left - flecha2_izq_rect.right) // 2
        texto_opcion_rect_f2 = texto_opcion_fila2.get_rect(center=(centro_x_f2, flecha2_izq_rect.centery))
        screen.blit(texto_opcion_fila2, texto_opcion_rect_f2)

        padding = 10
        color_seleccion = (50, 150, 255)
        if fila_activa == 0:
            rect_seleccion_x = flecha1_izq_rect.left - padding
            rect_seleccion_y = flecha1_izq_rect.top - padding
            rect_seleccion_w = flecha1_der_rect.right - rect_seleccion_x + padding
            rect_seleccion_h = flecha1_izq_rect.height + 2 * padding
            pygame.draw.rect(screen, color_seleccion,
                             (rect_seleccion_x, rect_seleccion_y, rect_seleccion_w, rect_seleccion_h), 3,
                             border_radius=8)

        elif fila_activa == 1:
            rect_seleccion_x = flecha2_izq_rect.left - padding
            rect_seleccion_y = flecha2_izq_rect.top - padding
            rect_seleccion_w = flecha2_der_rect.right - rect_seleccion_x + padding
            rect_seleccion_h = flecha2_izq_rect.height + 2 * padding
            pygame.draw.rect(screen, color_seleccion,
                             (rect_seleccion_x, rect_seleccion_y, rect_seleccion_w, rect_seleccion_h), 3,
                             border_radius=8)

        imagen_a_mostrar = None
        if indice_fila1 == 0:
            if indice_fila2 == 0:
                imagen_a_mostrar = img_teclado_menu
            else:
                imagen_a_mostrar = img_teclado_combate
        else:
            if indice_fila2 == 0:
                imagen_a_mostrar = img_mando_menu
            else:
                imagen_a_mostrar = img_mando_combate

        if imagen_a_mostrar:
            imagen_scaled = pygame.transform.scale(imagen_a_mostrar, (580, 350))
            offset_vertical = 50
            imagen_rect = imagen_scaled.get_rect(center=(fondo_rect.centerx, fondo_rect.centery + offset_vertical))
            screen.blit(imagen_scaled, imagen_rect)

        if flecha_rect.collidepoint(mouse_pos):
            flecha_img = pygame.transform.scale(flecha_rotada, tamaño_hover)
            flecha_rect = flecha_img.get_rect(topleft=flecha_rect.topleft)
        else:
            flecha_img = pygame.transform.scale(flecha_rotada, tamaño_base)
            flecha_rect = flecha_img.get_rect(topleft=flecha_rect.topleft)

        screen.blit(flecha_img, flecha_rect)

        pygame.display.flip()

    return
