import random
import sys
import time
from collections import deque


class CerebroCPU:
    DIRECCIONES = [
        (0, -1, "up"),
        (-1, 0, "left"),
        (1, 0, "right"),
        (0, 1, "down"),
    ]

    TIPOS_MALDICION = {
        "calavera",
        "reset",
        "no_ability",
        "no_bomb",
        "auto_bomb",
        "inverted",
        "hyper_speed",
        "slow_speed",
    }

    def __init__(self, id_jugador):
        self.id_jugador = id_jugador
        semilla_id = id_jugador if isinstance(id_jugador, int) else hash(id_jugador)
        self.rng = random.Random(time.time_ns() ^ ((semilla_id + 1) * 1000003))
        self.direcciones_preferidas = list(self.DIRECCIONES)
        self.rng.shuffle(self.direcciones_preferidas)
        self.TILE_SIZE = 40
        self.DURACION_FUEGO = 0.2
        self.EXTRA_SEGURIDAD_FUEGO = 0.5
        self.REFRESCO_CAZA = 0.2
        self.estado = None
        self.objetivo_coord = None
        self.objetivo_entidad = None
        self.coord_fijada_caza = None
        self.tiempo_fijado_caza = 0.0
        self.plan_patada = None
        self.bombas_vistas = {}
        self.explosiones_activas = {}
        self.fuego_real_reciente = {}

    def inputs_vacios(self):
        return {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "bomb": False,
            "hit": False,
            "escudo": False,
        }

    def tiene_inputs_activos(self, inputs):
        return any(inputs.values())

    def limpiar_estado(self):
        self.estado = None
        self.objetivo_coord = None
        self.objetivo_entidad = None
        self.coord_fijada_caza = None
        self.tiempo_fijado_caza = 0.0

    def limpiar_plan_patada(self):
        self.plan_patada = None

    def in_bounds(self, x, y, grid):
        return 0 <= y < len(grid) and 0 <= x < len(grid[0])

    def vecinos(self, x, y, grid):
        for dx, dy, _ in self.direcciones_preferidas:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny, grid):
                yield nx, ny

    def distancia_centro(self, x, y, grid):
        centro_x = len(grid[0]) // 2
        centro_y = len(grid) // 2
        return abs(x - centro_x) + abs(y - centro_y)

    def obtener_casillas_ocupadas(self, player, margen=0):
        try:
            caja = player.get_hitbox()
            min_col = (caja.left - margen) // self.TILE_SIZE
            max_col = (caja.right - 1 + margen) // self.TILE_SIZE
            min_row = (caja.top - margen) // self.TILE_SIZE
            max_row = (caja.bottom - 1 + margen) // self.TILE_SIZE
            casillas = set()
            for c in range(int(min_col), int(max_col) + 1):
                for r in range(int(min_row), int(max_row) + 1):
                    casillas.add((c, r))
            return casillas
        except AttributeError:
            return {player.get_center_tile()}

    def obtener_casillas_hitbox_virtual(self, player, tx, ty, margen=0):
        try:
            caja = player.get_hitbox()
            ancho = max(1, int(caja.width))
            alto = max(1, int(caja.height))
        except AttributeError:
            return {(tx, ty)}

        centro_x = tx * self.TILE_SIZE + (self.TILE_SIZE // 2)
        centro_y = ty * self.TILE_SIZE + (self.TILE_SIZE // 2)
        left = centro_x - (ancho / 2) - margen
        right = centro_x + (ancho / 2) + margen
        top = centro_y - (alto / 2) - margen
        bottom = centro_y + (alto / 2) + margen

        min_col = int(left // self.TILE_SIZE)
        max_col = int((right - 1) // self.TILE_SIZE)
        min_row = int(top // self.TILE_SIZE)
        max_row = int((bottom - 1) // self.TILE_SIZE)

        casillas = set()
        for c in range(min_col, max_col + 1):
            for r in range(min_row, max_row + 1):
                casillas.add((c, r))
        return casillas

    def hitbox_virtual_toca_capa(self, player, tx, ty, capa, margen=0):
        return any(
            casilla in capa
            for casilla in self.obtener_casillas_hitbox_virtual(player, tx, ty, margen)
        )

    def capturar_contexto_extra(self):
        contexto = {
            "powerups": [],
            "lapidas": [],
            "dropped_abilities": [],
            "explosions": None,
            "remaining_time": None,
            "bloques_finales_activados": False,
            "ruta_espiral": [],
            "proximo_bloque_idx": 0,
            "final_blocks": [],
        }
        try:
            frame = sys._getframe(1)
            profundidad = 0
            while frame is not None and profundidad < 6:
                for origen in (frame.f_locals, frame.f_globals):
                    for clave in contexto:
                        if clave in origen:
                            contexto[clave] = origen[clave]
                frame = frame.f_back
                profundidad += 1
        except Exception:
            pass
        return contexto

    def generar_mapas_fisicos(self, grid):
        muros_fijos = set()
        muros_rompibles = set()
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                valor = grid[y][x]
                if valor == 1:
                    muros_rompibles.add((x, y))
                elif valor in (2, 3, 4):
                    muros_fijos.add((x, y))
        return muros_fijos, muros_rompibles

    def obtener_casillas_bombas(self, bombs):
        casillas = set()
        for bomba in bombs:
            if getattr(bomba, "exploded", False):
                continue
            casillas.add((int(getattr(bomba, "tile_x", 0)), int(getattr(bomba, "tile_y", 0))))
        return casillas

    def construir_bloqueos(self, inicio, muros_fijos, muros_rompibles, casillas_bombas):
        bloqueadas = set(muros_fijos)
        bloqueadas.update(muros_rompibles)
        bloqueadas.update(casillas_bombas)
        bloqueadas.discard(inicio)
        return bloqueadas

    def agregar_cruz_fuego(self, zonas, bx, by, radio, grid, muros_fijos, muros_rompibles):
        zonas.add((bx, by))
        for dx, dy, _ in self.DIRECCIONES:
            for i in range(1, int(radio) + 1):
                nx, ny = bx + dx * i, by + dy * i
                if not self.in_bounds(nx, ny, grid):
                    break
                if (nx, ny) in muros_fijos:
                    break
                zonas.add((nx, ny))
                if (nx, ny) in muros_rompibles:
                    break

    def actualizar_explosiones_activas(self, bombs, usar_respaldo=True):
        ahora = time.time()
        bombas_actuales = {}
        for bomba in bombs:
            if getattr(bomba, "exploded", False):
                continue
            coord = (int(getattr(bomba, "tile_x", 0)), int(getattr(bomba, "tile_y", 0)))
            radio = int(getattr(bomba, "blast_range", 1))
            bombas_actuales[coord] = radio

        if usar_respaldo:
            for coord, radio in self.bombas_vistas.items():
                if coord not in bombas_actuales:
                    self.explosiones_activas[coord] = (radio, ahora)
        else:
            self.explosiones_activas.clear()
        self.bombas_vistas = bombas_actuales

        caducadas = []
        for coord, (_, timestamp) in self.explosiones_activas.items():
            if ahora - timestamp > self.DURACION_FUEGO:
                caducadas.append(coord)
        for coord in caducadas:
            del self.explosiones_activas[coord]

    def obtener_casillas_explosiones_reales(self, contexto):
        ahora = time.time()
        casillas = set()
        explosiones = contexto.get("explosions")
        if explosiones is None:
            caducadas = [
                casilla for casilla, timestamp in self.fuego_real_reciente.items()
                if ahora - timestamp > self.EXTRA_SEGURIDAD_FUEGO
            ]
            for casilla in caducadas:
                del self.fuego_real_reciente[casilla]
            return None
        for explosion in explosiones:
            if getattr(explosion, "finished", False):
                continue
            casilla = (int(getattr(explosion, "tile_x", 0)), int(getattr(explosion, "tile_y", 0)))
            casillas.add(casilla)
            self.fuego_real_reciente[casilla] = ahora

        caducadas = [
            casilla for casilla, timestamp in self.fuego_real_reciente.items()
            if ahora - timestamp > self.EXTRA_SEGURIDAD_FUEGO
        ]
        for casilla in caducadas:
            del self.fuego_real_reciente[casilla]

        return set(self.fuego_real_reciente.keys())

    def calcular_peligro_bombas(self, grid, bombs, muros_fijos, muros_rompibles, contexto):
        peligro = set()

        # 1. Proyectar cruces de bombas a punto de explotar
        for bomba in bombs:
            if getattr(bomba, "exploded", False):
                continue
            bx = int(getattr(bomba, "tile_x", getattr(bomba, "x", 0)))
            by = int(getattr(bomba, "tile_y", getattr(bomba, "y", 0)))
            radio = int(
                getattr(bomba, "blast_range", getattr(bomba, "explosion_radius", getattr(bomba, "timer", 3))))
            self.agregar_cruz_fuego(peligro, bx, by, radio, grid, muros_fijos, muros_rompibles)

        casillas_explosion_real = self.obtener_casillas_explosiones_reales(contexto)
        if casillas_explosion_real is not None:
            peligro.update(casillas_explosion_real)
            self.actualizar_explosiones_activas(bombs, usar_respaldo=False)
            return peligro

        # 2. Memoria de seguridad para no volver a entrar antes de que termine la explosión.
        self.actualizar_explosiones_activas(bombs, usar_respaldo=True)
        for coord, (radio, _) in self.explosiones_activas.items():
            self.agregar_cruz_fuego(peligro, coord[0], coord[1], radio, grid, muros_fijos, muros_rompibles)

        # 3. Sumar las explosiones reales del motor (doble validación)
        explosiones = contexto.get("explosions")
        if explosiones is not None:
            for exp in explosiones:
                if not getattr(exp, "finished", False):
                    bx = int(getattr(exp, "tile_x", getattr(exp, "x", 0)))
                    by = int(getattr(exp, "tile_y", getattr(exp, "y", 0)))
                    radio = int(getattr(exp, "blast_range", getattr(exp, "radius", 3)))
                    self.agregar_cruz_fuego(peligro, bx, by, radio, grid, muros_fijos, muros_rompibles)

        return peligro

    def calcular_peligro_bloques_finales(self, grid, contexto):
        peligro = set()
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] == 4:
                    peligro.add((x, y))

        for bloque in contexto["final_blocks"]:
            peligro.add((int(getattr(bloque, "tile_x", 0)), int(getattr(bloque, "tile_y", 0))))

        if not contexto["bloques_finales_activados"]:
            return peligro

        remaining_time = contexto["remaining_time"]
        ruta_espiral = contexto["ruta_espiral"] or []
        if remaining_time is None or not ruta_espiral or remaining_time > 60:
            return peligro

        tiempo_por_bloque = 55.0 / len(ruta_espiral)
        for idx, (tx, ty) in enumerate(ruta_espiral):
            if not self.in_bounds(tx, ty, grid) or grid[ty][tx] == 4:
                continue
            tiempo_caida_restante = 55.0 - idx * tiempo_por_bloque
            if remaining_time <= tiempo_caida_restante + 10 and remaining_time > tiempo_caida_restante:
                peligro.add((tx, ty))
        return peligro

    def calcular_peligro_maldicion(self, grid, contexto, players, yo):
        peligro = set()

        for powerup in contexto["powerups"] or []:
            if not getattr(powerup, "visible", False):
                continue
            if getattr(powerup, "disappearing", False):
                continue
            if getattr(powerup, "type", None) in self.TIPOS_MALDICION:
                peligro.add((int(getattr(powerup, "x", 0)), int(getattr(powerup, "y", 0))))

        for lapida in contexto["lapidas"] or []:
            if getattr(lapida, "is_finished", None) and lapida.is_finished():
                continue
            peligro.add((int(getattr(lapida, "tile_x", 0)), int(getattr(lapida, "tile_y", 0))))

        if getattr(yo, "active_curse", None):
            return peligro

        for jugador in players:
            if jugador == yo or getattr(jugador, "is_eliminated", False) or getattr(jugador, "is_ghost", False):
                continue
            if not getattr(jugador, "active_curse", None):
                continue
            jx, jy = jugador.get_center_tile()
            peligro.add((jx, jy))
            for nx, ny in self.vecinos(jx, jy, grid):
                peligro.add((nx, ny))
        return peligro
    def buscar_camino_estable(self, inicio, condicion_objetivo, grid, bloqueadas, zonas_prohibidas=None):
        zonas_prohibidas = zonas_prohibidas or set()
        cola = deque([(inicio, [inicio])])
        visitados = {inicio}

        while cola:
            (cx, cy), camino = cola.popleft()
            if condicion_objetivo(cx, cy):
                return camino
            for dx, dy, _ in self.direcciones_preferidas:
                nx, ny = cx + dx, cy + dy
                siguiente = (nx, ny)
                if not self.in_bounds(nx, ny, grid):
                    continue
                if siguiente in visitados or siguiente in bloqueadas or siguiente in zonas_prohibidas:
                    continue
                visitados.add(siguiente)
                cola.append((siguiente, camino + [siguiente]))
        return None

    def obtener_zona_movilidad(self, inicio, grid, bloqueadas, zonas_prohibidas=None):
        zonas_prohibidas = zonas_prohibidas or set()
        reachable = set()
        cola = deque([inicio])
        visitados = {inicio}

        while cola:
            cx, cy = cola.popleft()
            reachable.add((cx, cy))
            for dx, dy, _ in self.direcciones_preferidas:
                nx, ny = cx + dx, cy + dy
                siguiente = (nx, ny)
                if not self.in_bounds(nx, ny, grid):
                    continue
                if siguiente in visitados or siguiente in bloqueadas or siguiente in zonas_prohibidas:
                    continue
                visitados.add(siguiente)
                cola.append(siguiente)
        return reachable

    def buscar_escape_prioritario(self, inicio, grid, bloqueadas, capa_critica, capas_secundarias=None,
                                  prohibidas_duras=None, salida_valida_fn=None):
        capas_secundarias = capas_secundarias or []
        prohibidas_duras = prohibidas_duras or set()
        cola = deque([(inicio, [inicio])])
        visitados = {inicio}
        mejor_camino = None
        mejor_score = None

        while cola:
            (cx, cy), camino = cola.popleft()
            actual = (cx, cy)
            if actual not in capa_critica and actual not in prohibidas_duras:
                if salida_valida_fn is None or salida_valida_fn(actual):
                    score = (
                        sum(1 for capa in capas_secundarias if actual in capa),
                        len(camino),
                        self.distancia_centro(cx, cy, grid),
                        self.rng.random(),
                    )
                    if mejor_score is None or score < mejor_score:
                        mejor_score = score
                        mejor_camino = camino

            for dx, dy, _ in self.direcciones_preferidas:
                nx, ny = cx + dx, cy + dy
                siguiente = (nx, ny)
                if not self.in_bounds(nx, ny, grid):
                    continue
                if siguiente in visitados or siguiente in bloqueadas or siguiente in prohibidas_duras:
                    continue
                visitados.add(siguiente)
                cola.append((siguiente, camino + [siguiente]))

        return mejor_camino

    def obtener_fronteras(self, zona_movilidad, muros_rompibles, grid):
        fronteras = []
        for cx, cy in zona_movilidad:
            for nx, ny in self.vecinos(cx, cy, grid):
                if (nx, ny) in muros_rompibles:
                    fronteras.append((cx, cy))
                    break
        return fronteras

    def centrarse_en_casilla(self, player, tx, ty):
        inputs = self.inputs_vacios()
        try:
            caja = player.get_hitbox()
            centro_x, centro_y = caja.centerx, caja.centery
        except AttributeError:
            return inputs

        ideal_x = tx * self.TILE_SIZE + (self.TILE_SIZE // 2)
        ideal_y = ty * self.TILE_SIZE + (self.TILE_SIZE // 2)
        tolerancia = 2

        if centro_x < ideal_x - tolerancia:
            inputs["right"] = True
        elif centro_x > ideal_x + tolerancia:
            inputs["left"] = True
        if centro_y < ideal_y - tolerancia:
            inputs["down"] = True
        elif centro_y > ideal_y + tolerancia:
            inputs["up"] = True
        return inputs

    def esta_centrado_en_casilla(self, player, tx, ty, tolerancia=2):
        try:
            caja = player.get_hitbox()
        except AttributeError:
            return True

        ideal_x = tx * self.TILE_SIZE + (self.TILE_SIZE // 2)
        ideal_y = ty * self.TILE_SIZE + (self.TILE_SIZE // 2)
        return (
            abs(caja.centerx - ideal_x) <= tolerancia
            and abs(caja.centery - ideal_y) <= tolerancia
        )

    def mover_milimetrico(self, player, px, py, tx, ty):
        inputs = self.inputs_vacios()
        if px == tx and py == ty:
            return self.centrarse_en_casilla(player, px, py)

        try:
            caja = player.get_hitbox()
            centro_x, centro_y = caja.centerx, caja.centery
        except AttributeError:
            centro_x = px * self.TILE_SIZE + (self.TILE_SIZE // 2)
            centro_y = py * self.TILE_SIZE + (self.TILE_SIZE // 2)

        ideal_x = px * self.TILE_SIZE + (self.TILE_SIZE // 2)
        ideal_y = py * self.TILE_SIZE + (self.TILE_SIZE // 2)
        tolerancia = 4

        if tx != px:
            if centro_y < ideal_y - tolerancia:
                inputs["down"] = True
            elif centro_y > ideal_y + tolerancia:
                inputs["up"] = True
            else:
                inputs["right" if tx > px else "left"] = True
        elif ty != py:
            if centro_x < ideal_x - tolerancia:
                inputs["right"] = True
            elif centro_x > ideal_x + tolerancia:
                inputs["left"] = True
            else:
                inputs["down" if ty > py else "up"] = True
        return inputs

    def convertir_inputs_a_direccion(self, inputs):
        if inputs.get("up"):
            return "up"
        if inputs.get("down"):
            return "down"
        if inputs.get("left"):
            return "left"
        if inputs.get("right"):
            return "right"
        return None

    def elegir_casilla_adyacente(self, px, py, grid, bloqueadas, peligro_bombas, peligro_final, peligro_maldicion):
        mejor = None
        mejor_score = None
        for dx, dy, _ in self.direcciones_preferidas:
            nx, ny = px + dx, py + dy
            siguiente = (nx, ny)
            if not self.in_bounds(nx, ny, grid) or siguiente in bloqueadas:
                continue
            score = (
                siguiente in peligro_bombas,
                siguiente in peligro_final,
                siguiente in peligro_maldicion,
                self.distancia_centro(nx, ny, grid),
            )
            if mejor_score is None or score < mejor_score:
                mejor_score = score
                mejor = siguiente
        return mejor

    def linea_de_vision_despejada(self, ax, ay, bx, by, grid, casillas_bombas):
        if ax != bx and ay != by:
            return False

        if ax == bx:
            paso = 1 if by > ay else -1
            for y in range(ay + paso, by, paso):
                if grid[y][ax] in (1, 2, 3, 4) or (ax, y) in casillas_bombas:
                    return False
            return True

        paso = 1 if bx > ax else -1
        for x in range(ax + paso, bx, paso):
            if grid[ay][x] in (1, 2, 3, 4) or (x, ay) in casillas_bombas:
                return False
        return True

    def linea_de_vision_fantasma(self, ax, ay, bx, by, grid):
        if ax != bx and ay != by:
            return False

        if ax == bx:
            paso = 1 if by > ay else -1
            for y in range(ay + paso, by, paso):
                if grid[y][ax] in (1, 2, 3, 4):
                    return False
            return True

        paso = 1 if bx > ax else -1
        for x in range(ax + paso, bx, paso):
            if grid[ay][x] in (1, 2, 3, 4):
                return False
        return True

    def construir_bloqueos_fantasma(self, grid):
        bloqueadas = set()
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] in (2, 3, 4):
                    bloqueadas.add((x, y))
        return bloqueadas

    def puede_colocar_bomba_fantasma(self, player, px, py, grid, bombs):
        if not getattr(player, "is_ghost", False):
            return False
        if not self.in_bounds(px, py, grid) or grid[py][px] in (1, 2, 3, 4):
            return False
        if time.time() - getattr(player, "last_bomb_placed_time", 0) < getattr(player, "ghost_bomb_cooldown", 30.0):
            return False
        return not any(
            int(getattr(bomba, "tile_x", -1)) == px
            and int(getattr(bomba, "tile_y", -1)) == py
            and not getattr(bomba, "exploded", False)
            for bomba in bombs
        )

    def elegir_objetivo_fantasma(self, player, px, py, grid, players, bloqueadas):
        candidatos = []
        for victima in players:
            if victima == player:
                continue
            if getattr(victima, "is_eliminated", False) or getattr(victima, "is_ghost", False):
                continue
            vx, vy = victima.get_center_tile()
            if not self.in_bounds(vx, vy, grid) or (vx, vy) in bloqueadas:
                continue
            ruta = self.buscar_camino_estable(
                (px, py),
                lambda cx, cy, tx=vx, ty=vy: (cx, cy) == (tx, ty),
                grid,
                bloqueadas,
            )
            if ruta:
                candidatos.append((len(ruta), abs(px - vx) + abs(py - vy), self.rng.random(), victima, ruta))

        if not candidatos:
            return None, None

        candidatos.sort(key=lambda item: (item[0], item[1], item[2]))
        _, _, _, victima, ruta = candidatos[0]
        return victima, ruta

    def pensar_fantasma(self, player, grid, bombs, players):
        inputs = self.inputs_vacios()
        self.limpiar_estado()
        self.limpiar_plan_patada()

        px, py = player.get_center_tile()
        bloqueadas = self.construir_bloqueos_fantasma(grid)
        victima, ruta = self.elegir_objetivo_fantasma(player, px, py, grid, players, bloqueadas)
        if victima is None:
            return inputs

        vx, vy = victima.get_center_tile()
        radio_bomba = int(getattr(player, "bomb_range", 1))
        puede_alcanzar = (
            abs(px - vx) + abs(py - vy) <= radio_bomba
            and self.linea_de_vision_fantasma(px, py, vx, vy, grid)
        )

        if puede_alcanzar and self.puede_colocar_bomba_fantasma(player, px, py, grid, bombs):
            inputs.update(self.centrarse_en_casilla(player, px, py))
            if self.tiene_inputs_activos(inputs):
                return inputs
            inputs["bomb"] = True
            return inputs

        if ruta and len(ruta) > 1:
            siguiente = ruta[1]
            inputs.update(self.mover_milimetrico(player, px, py, siguiente[0], siguiente[1]))
        elif ruta and len(ruta) == 1:
            inputs.update(self.centrarse_en_casilla(player, px, py))
        return inputs

    def puede_escapar_si_pone_bomba(self, player, inicio, grid, muros_fijos, muros_rompibles, casillas_bombas, radio,
                                    peligro_bombas, peligro_final, peligro_maldicion):
        peligro_simulado = set(peligro_bombas)
        self.agregar_cruz_fuego(peligro_simulado, inicio[0], inicio[1], radio, grid, muros_fijos, muros_rompibles)
        bloqueadas = self.construir_bloqueos(inicio, muros_fijos, muros_rompibles, casillas_bombas)
        ruta = self.buscar_escape_prioritario(
            inicio,
            grid,
            bloqueadas,
            peligro_simulado,
            capas_secundarias=[peligro_final, peligro_maldicion],
            salida_valida_fn=lambda casilla: not self.hitbox_virtual_toca_capa(
                player, casilla[0], casilla[1], peligro_simulado, margen=2
            ),
        )
        return bool(ruta)

    def activar_escudo_directo(self, player):
        if not getattr(player, "escudo_available", False):
            return False
        if getattr(player, "escudo_active", False):
            return True
        try:
            player.activate_escudo()
            return getattr(player, "escudo_active", False)
        except Exception:
            return False

    def obtener_bombas_adyacentes(self, px, py, bombs):
        candidatas = []
        for bomba in bombs:
            if getattr(bomba, "exploded", False):
                continue
            if getattr(bomba, "sliding", False) or getattr(bomba, "hit_bouncing", False):
                continue
            bx = int(getattr(bomba, "tile_x", 0))
            by = int(getattr(bomba, "tile_y", 0))
            dist = abs(bx - px) + abs(by - py)
            if dist <= 1:
                candidatas.append((dist, bomba))
        candidatas.sort(key=lambda item: item[0])
        return [bomba for _, bomba in candidatas]

    def golpear_bomba_directo(self, player, px, py, bombs, grid, players, powerups, bloqueadas, peligro_bombas,
                              peligro_final, peligro_maldicion):
        if not getattr(player, "hit_bomb_available", False):
            return False

        for bomba in self.obtener_bombas_adyacentes(px, py, bombs):
            bx = int(getattr(bomba, "tile_x", 0))
            by = int(getattr(bomba, "tile_y", 0))
            if bx == px and by == py:
                salida = self.elegir_casilla_adyacente(px, py, grid, bloqueadas, peligro_bombas, peligro_final,
                                                       peligro_maldicion)
                if salida is None:
                    continue
                dx = salida[0] - px
                dy = salida[1] - py
            else:
                dx = bx - px
                dy = by - py

            if dx > 0:
                player.current_direction = "right"
            elif dx < 0:
                player.current_direction = "left"
            elif dy > 0:
                player.current_direction = "down"
            else:
                player.current_direction = "up"

            try:
                bomba.hit_by_player(dx, dy, grid, bombs, powerups, players)
                return True
            except Exception:
                continue
        return False

    def puede_colocar_bomba_ahora(self, player, px, py, bombs):
        if getattr(player, "is_ghost", False):
            return False
        if getattr(player, "auto_bombing", False):
            return False
        if not getattr(player, "can_place_bombs", True):
            return False

        bombas_activas = [
            bomba for bomba in bombs
            if getattr(bomba, "owner", None) == player and not getattr(bomba, "exploded", False)
        ]
        if len(bombas_activas) >= int(getattr(player, "bomb_limit", 1)):
            return False

        return not any(
            int(getattr(bomba, "tile_x", -1)) == px
            and int(getattr(bomba, "tile_y", -1)) == py
            and not getattr(bomba, "exploded", False)
            for bomba in bombs
        )

    def ejecutar_plan_patada(self, player, px, py, bombs, grid, bloqueadas, peligro_bombas, peligro_final,
                             peligro_maldicion):
        if not getattr(player, "push_bomb_available", False):
            self.limpiar_plan_patada()
            return None

        ahora = time.time()
        if self.plan_patada:
            if ahora > self.plan_patada["caduca"]:
                self.limpiar_plan_patada()
            else:
                bx, by = self.plan_patada["bomba"]
                bomba_sigue = any(
                    not getattr(bomba, "exploded", False)
                    and int(getattr(bomba, "tile_x", 0)) == bx
                    and int(getattr(bomba, "tile_y", 0)) == by
                    for bomba in bombs
                )
                if not bomba_sigue:
                    self.limpiar_plan_patada()

        if self.plan_patada:
            bx, by = self.plan_patada["bomba"]
            if self.plan_patada["fase"] == "SALIR":
                if (px, py) != (bx, by):
                    self.plan_patada["fase"] = "VOLVER"
                else:
                    sx, sy = self.plan_patada["salida"]
                    return self.mover_milimetrico(player, px, py, sx, sy)

            if self.plan_patada and self.plan_patada["fase"] == "VOLVER":
                if abs(px - bx) + abs(py - by) == 1:
                    return self.mover_milimetrico(player, px, py, bx, by)
                self.limpiar_plan_patada()

        for bomba in self.obtener_bombas_adyacentes(px, py, bombs):
            bx = int(getattr(bomba, "tile_x", 0))
            by = int(getattr(bomba, "tile_y", 0))
            if (bx, by) == (px, py):
                salida = self.elegir_casilla_adyacente(px, py, grid, bloqueadas, peligro_bombas, peligro_final,
                                                       peligro_maldicion)
                if salida is None:
                    continue
                self.plan_patada = {
                    "bomba": (bx, by),
                    "fase": "SALIR",
                    "salida": salida,
                    "caduca": ahora + 1.2,
                }
                return self.mover_milimetrico(player, px, py, salida[0], salida[1])
            return self.mover_milimetrico(player, px, py, bx, by)
        return None

    def obtener_powerups_buenos(self, powerups):
        buenos = []
        for powerup in powerups or []:
            if not getattr(powerup, "visible", False):
                continue
            if getattr(powerup, "disappearing", False):
                continue
            if getattr(powerup, "bouncing", False):
                continue
            if getattr(powerup, "type", None) in self.TIPOS_MALDICION:
                continue
            buenos.append(powerup)
        return buenos
    def elegir_objetivo(self, player, px, py, grid, bloqueadas, peligro_total, muros_rompibles, players, contexto,
                        ahora):
        zona_segura = self.obtener_zona_movilidad((px, py), grid, bloqueadas, peligro_total)

        posibles_victimas = []
        for victima in players:
            if victima == player:
                continue
            if getattr(victima, "is_eliminated", False) or getattr(victima, "is_ghost", False):
                continue
            if getattr(victima, "active_curse", None) and not getattr(player, "active_curse", None):
                continue
            vx, vy = victima.get_center_tile()
            if (vx, vy) not in zona_segura:
                continue
            ruta = self.buscar_camino_estable(
                (px, py),
                lambda cx, cy, tx=vx, ty=vy: (cx, cy) == (tx, ty),
                grid,
                bloqueadas,
                peligro_total,
            )
            if ruta:
                posibles_victimas.append(victima)

        if posibles_victimas:
            victima = self.rng.choice(posibles_victimas)
            self.estado = "CAZAR"
            self.objetivo_entidad = victima
            self.coord_fijada_caza = victima.get_center_tile()
            self.objetivo_coord = self.coord_fijada_caza
            self.tiempo_fijado_caza = ahora
            return

        powerups_buenos = []
        for powerup in self.obtener_powerups_buenos(contexto["powerups"]):
            coord = (int(getattr(powerup, "x", 0)), int(getattr(powerup, "y", 0)))
            if coord in zona_segura:
                powerups_buenos.append(coord)

        if powerups_buenos:
            self.estado = "POWERUP"
            self.objetivo_coord = self.rng.choice(powerups_buenos)
            return

        fronteras = self.obtener_fronteras(zona_segura, muros_rompibles, grid)
        if fronteras:
            self.estado = "ROMPER"
            self.objetivo_coord = self.rng.choice(fronteras)

    def ejecutar_romper(self, player, px, py, grid, bloqueadas, peligro_total, bombs, muros_rompibles, muros_fijos,
                        casillas_bombas, peligro_bombas, peligro_final, peligro_maldicion):
        inputs = self.inputs_vacios()
        tx, ty = self.objetivo_coord

        # 1. Verificar que la frontera sigue siendo válida
        es_frontera_valida = False
        for dx, dy, _ in self.direcciones_preferidas:
            nx, ny = tx + dx, ty + dy
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and (nx, ny) in muros_rompibles:
                es_frontera_valida = True
                break

        if not es_frontera_valida:
            self.limpiar_estado()
            return inputs

        # 2. Si ya estamos en la casilla objetivo
        if px == tx and py == ty:
            inputs.update(self.centrarse_en_casilla(player, px, py))
            if self.tiene_inputs_activos(inputs):
                return inputs

            if not self.puede_colocar_bomba_ahora(player, px, py, bombs):
                return inputs  # Espera hasta que el motor permita colocar otra bomba.

            radio_bomba = int(getattr(player, "bomb_range", getattr(player, "explosion_radius", 3)))

            # Comprobar si puede escapar antes de ponerla
            if self.puede_escapar_si_pone_bomba(player, (px, py), grid, muros_fijos, muros_rompibles, casillas_bombas,
                                                radio_bomba, peligro_bombas, peligro_final, peligro_maldicion):
                inputs["bomb"] = True
                # La tarea sigue activa hasta que la bomba aparece físicamente bajo el jugador.
                bomba_aqui = any(int(getattr(b, "tile_x", getattr(b, "x", -1))) == px and int(
                    getattr(b, "tile_y", getattr(b, "y", -1))) == py and not getattr(b, "exploded", False) for b in
                                 bombs)
                if bomba_aqui:
                    self.limpiar_estado()
            else:
                self.limpiar_estado()  # Cancela la acción si no existe salida segura.
        else:
            # 3. Avanzar hacia la casilla desde la que se puede romper el bloque.
            ruta = self.buscar_camino_estable((px, py), lambda cx, cy: cx == tx and cy == ty, grid, bloqueadas,
                                              peligro_total)
            if ruta and len(ruta) > 1:
                inputs.update(self.mover_milimetrico(player, px, py, ruta[1][0], ruta[1][1]))
            else:
                self.limpiar_estado()

        return inputs

    def ejecutar_caza(self, player, px, py, grid, bloqueadas, peligro_total, bombs, casillas_bombas, muros_fijos,
                      muros_rompibles, peligro_bombas, peligro_final, peligro_maldicion):
        inputs = self.inputs_vacios()
        ahora = time.time()

        # Actualiza la posición objetivo mientras el rival sigue siendo alcanzable.
        if ahora - self.tiempo_fijado_caza > self.REFRESCO_CAZA:
            vx, vy = self.objetivo_entidad.get_center_tile()
            if (vx, vy) not in peligro_total:
                self.coord_fijada_caza = (vx, vy)
                self.objetivo_coord = self.coord_fijada_caza
            else:
                self.limpiar_estado()
                return inputs
            self.tiempo_fijado_caza = ahora

        fx, fy = self.coord_fijada_caza
        # La persecución respeta bloqueos y zonas peligrosas recalculadas.
        ruta = self.buscar_camino_estable((px, py), lambda cx, cy: cx == fx and cy == fy, grid, bloqueadas,
                                          peligro_total)
        if ruta and len(ruta) > 1:
            inputs.update(self.mover_milimetrico(player, px, py, ruta[1][0], ruta[1][1]))

        vx, vy = self.objetivo_entidad.get_center_tile()
        radio_bomba = int(getattr(player, "bomb_range", getattr(player, "explosion_radius", 3)))

        # Si está a rango y en línea recta
        if abs(px - vx) + abs(py - vy) <= radio_bomba and self.linea_de_vision_despejada(px, py, vx, vy, grid,
                                                                                         casillas_bombas):
            if self.puede_escapar_si_pone_bomba(player, (px, py), grid, muros_fijos, muros_rompibles, casillas_bombas,
                                                radio_bomba, peligro_bombas, peligro_final, peligro_maldicion):
                inputs.update(self.centrarse_en_casilla(player, px, py))
                if self.tiene_inputs_activos(inputs):
                    return inputs
                if self.puede_colocar_bomba_ahora(player, px, py, bombs):
                    inputs["bomb"] = True
                    bomba_aqui = any(int(getattr(b, "tile_x", getattr(b, "x", -1))) == px and int(
                        getattr(b, "tile_y", getattr(b, "y", -1))) == py and not getattr(b, "exploded", False) for b in
                                     bombs)
                    if bomba_aqui:
                        self.limpiar_estado()

        return inputs
    def ejecutar_powerup(self, player, px, py, grid, bloqueadas, peligro_total, contexto):
        inputs = self.inputs_vacios()
        if self.objetivo_coord is None:
            self.limpiar_estado()
            return inputs

        objetivo_sigue = False
        for powerup in self.obtener_powerups_buenos(contexto["powerups"]):
            coord = (int(getattr(powerup, "x", 0)), int(getattr(powerup, "y", 0)))
            if coord == self.objetivo_coord:
                objetivo_sigue = True
                break
        if not objetivo_sigue:
            self.limpiar_estado()
            return inputs

        tx, ty = self.objetivo_coord
        ruta = self.buscar_camino_estable(
            (px, py),
            lambda cx, cy: (cx, cy) == (tx, ty),
            grid,
            bloqueadas,
            peligro_total,
        )
        if not ruta:
            self.limpiar_estado()
            return inputs
        if len(ruta) == 1:
            inputs.update(self.centrarse_en_casilla(player, tx, ty))
            return inputs
        if len(ruta) > 1:
            siguiente = ruta[1]
            inputs.update(self.mover_milimetrico(player, px, py, siguiente[0], siguiente[1]))
        return inputs

    def pensar(self, player, grid, bombs, players, *args, **kwargs):
        inputs = self.inputs_vacios()

        if getattr(player, "is_ghost", False):
            return self.pensar_fantasma(player, grid, bombs, players)

        contexto = self.capturar_contexto_extra()

        px, py = player.get_center_tile()
        inicio = (px, py)
        casillas_ocupadas = self.obtener_casillas_ocupadas(player)
        casillas_ocupadas_bomba = self.obtener_casillas_ocupadas(player, margen=2)
        muros_fijos, muros_rompibles = self.generar_mapas_fisicos(grid)
        casillas_bombas = self.obtener_casillas_bombas(bombs)
        bloqueadas = self.construir_bloqueos(inicio, muros_fijos, muros_rompibles, casillas_bombas)

        peligro_bombas = self.calcular_peligro_bombas(grid, bombs, muros_fijos, muros_rompibles, contexto)
        peligro_final = self.calcular_peligro_bloques_finales(grid, contexto)
        peligro_maldicion = self.calcular_peligro_maldicion(grid, contexto, players, player)
        peligro_total = set(peligro_bombas)
        peligro_total.update(peligro_final)
        peligro_total.update(peligro_maldicion)

        invencible = getattr(player, "escudo_active", False) or getattr(player, "is_invulnerable", False)
        en_bomba = False if invencible else any(casilla in peligro_bombas for casilla in casillas_ocupadas_bomba)
        en_final = any(casilla in peligro_final for casilla in casillas_ocupadas)
        en_maldicion = any(casilla in peligro_maldicion for casilla in casillas_ocupadas)

        if not en_bomba:
            self.limpiar_plan_patada()

        if en_bomba:
            self.limpiar_estado()
            ruta_escape = self.buscar_escape_prioritario(
                inicio,
                grid,
                bloqueadas,
                peligro_bombas,
                capas_secundarias=[peligro_final, peligro_maldicion],
                salida_valida_fn=lambda casilla: not self.hitbox_virtual_toca_capa(
                    player, casilla[0], casilla[1], peligro_bombas, margen=2
                ),
            )
            if ruta_escape and len(ruta_escape) > 1:
                siguiente = ruta_escape[1]
                return self.mover_milimetrico(player, px, py, siguiente[0], siguiente[1])
            if ruta_escape and len(ruta_escape) == 1:
                return self.centrarse_en_casilla(player, px, py)
            if self.activar_escudo_directo(player):
                inputs["escudo"] = True
                return inputs
            if self.golpear_bomba_directo(
                player,
                px,
                py,
                bombs,
                grid,
                players,
                contexto["powerups"],
                bloqueadas,
                peligro_bombas,
                peligro_final,
                peligro_maldicion,
            ):
                inputs["hit"] = True
                return inputs
            inputs_patada = self.ejecutar_plan_patada(
                player,
                px,
                py,
                bombs,
                grid,
                bloqueadas,
                peligro_bombas,
                peligro_final,
                peligro_maldicion,
            )
            if inputs_patada:
                return inputs_patada
            return inputs

        if en_final:
            self.limpiar_estado()
            ruta_escape = self.buscar_escape_prioritario(
                inicio,
                grid,
                bloqueadas,
                peligro_final,
                capas_secundarias=[peligro_maldicion],
                prohibidas_duras=peligro_bombas,
            )
            if ruta_escape and len(ruta_escape) > 1:
                siguiente = ruta_escape[1]
                return self.mover_milimetrico(player, px, py, siguiente[0], siguiente[1])
            if ruta_escape and len(ruta_escape) == 1:
                return self.centrarse_en_casilla(player, px, py)
            return inputs

        if en_maldicion and not getattr(player, "active_curse", None):
            self.limpiar_estado()
            ruta_escape = self.buscar_escape_prioritario(
                inicio,
                grid,
                bloqueadas,
                peligro_maldicion,
                prohibidas_duras=set(peligro_bombas) | set(peligro_final),
            )
            if ruta_escape and len(ruta_escape) > 1:
                siguiente = ruta_escape[1]
                return self.mover_milimetrico(player, px, py, siguiente[0], siguiente[1])
            if ruta_escape and len(ruta_escape) == 1:
                return self.centrarse_en_casilla(player, px, py)
            return inputs

        if self.estado == "CAZAR":
            estado_actual = self.estado
            inputs = self.ejecutar_caza(
                player,
                px,
                py,
                grid,
                bloqueadas,
                peligro_total,
                bombs,
                casillas_bombas,
                muros_fijos,
                muros_rompibles,
                peligro_bombas,
                peligro_final,
                peligro_maldicion,
            )
            if self.tiene_inputs_activos(inputs) or self.estado == estado_actual:
                return inputs

        elif self.estado == "POWERUP":
            estado_actual = self.estado
            inputs = self.ejecutar_powerup(player, px, py, grid, bloqueadas, peligro_total, contexto)
            if self.tiene_inputs_activos(inputs) or self.estado == estado_actual:
                return inputs

        elif self.estado == "ROMPER":
            estado_actual = self.estado
            inputs = self.ejecutar_romper(
                player,
                px,
                py,
                grid,
                bloqueadas,
                peligro_total,
                bombs,
                muros_rompibles,
                muros_fijos,
                casillas_bombas,
                peligro_bombas,
                peligro_final,
                peligro_maldicion,
            )
            if self.tiene_inputs_activos(inputs) or self.estado == estado_actual:
                return inputs

        self.limpiar_estado()
        ahora = time.time()
        self.elegir_objetivo(
            player,
            px,
            py,
            grid,
            bloqueadas,
            peligro_total,
            muros_rompibles,
            players,
            contexto,
            ahora,
        )

        if self.estado == "CAZAR":
            return self.ejecutar_caza(
                player,
                px,
                py,
                grid,
                bloqueadas,
                peligro_total,
                bombs,
                casillas_bombas,
                muros_fijos,
                muros_rompibles,
                peligro_bombas,
                peligro_final,
                peligro_maldicion,
            )
        if self.estado == "POWERUP":
            return self.ejecutar_powerup(player, px, py, grid, bloqueadas, peligro_total, contexto)
        if self.estado == "ROMPER":
            return self.ejecutar_romper(
                player,
                px,
                py,
                grid,
                bloqueadas,
                peligro_total,
                bombs,
                muros_rompibles,
                muros_fijos,
                casillas_bombas,
                peligro_bombas,
                peligro_final,
                peligro_maldicion,
            )
        return inputs
