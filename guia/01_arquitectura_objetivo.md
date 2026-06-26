# Arquitectura objetivo

## 1. Objetivo tecnico

La CPU debe convertirse en un sistema de decision por capas:

1. captura del estado real del mundo,
2. construccion de mapas de movilidad y peligro,
3. resolucion de supervivencia,
4. aplicacion de restricciones,
5. seleccion y ejecucion de objetivo.

Todo eso debe vivir en `IA_CPU.py`.

## 2. Contexto que la IA necesita en cada tick

La IA ya recibe `player`, `grid`, `bombs` y `players`, pero para cumplir el pliego tambien necesita leer:

- `powerups`,
- `lapidas`,
- `dropped_abilities`,
- `remaining_time`,
- `bloques_finales_activados`,
- `ruta_espiral`,
- `proximo_bloque_idx`,
- `final_blocks`.

Como el PDF pide no tocar `KaBoom.py`, la forma mas compatible es consolidar en `IA_CPU.py` un helper tipo `capturar_contexto_caller()` usando `sys._getframe(1).f_locals`, en vez de leer solo `powerups` y `lapidas` de manera parcial.

## 3. Modelo del mapa

La IA no debe trabajar solo con el `grid` bruto. Debe separar:

### Bloqueo fijo

- limites del mapa,
- bloques irrompibles,
- cualquier casilla que el jugador vivo no puede atravesar nunca.

### Bloqueo dinamico

- bloques rompibles que siguen presentes,
- bloques finales ya caidos,
- bombas ocupando casilla,
- casillas anuladas temporalmente por una prioridad superior.

### Zona de movilidad real

La zona de movilidad no es "todas las casillas libres del tablero", sino solo las casillas conectadas con la posicion actual del jugador sin atravesar bloqueos.

Eso implica:

- BFS/DFS desde la casilla actual,
- conexion solo por arriba/abajo/izquierda/derecha,
- nada de diagonales,
- nada de "teletransportarse" a otra region libre no conectada.

## 4. Capas de hitbox invisibles

El pliego habla constantemente de hitboxes invisibles. En la implementacion conviene modelarlas como capas de casillas:

### 4.1. Hitbox de bomba

Debe cubrir:

- la casilla de la bomba,
- el rango futuro de explosion desde el momento en que la bomba se coloca,
- el fuego mientras la explosion sigue viva.

Importante: en el codigo actual de `KaBoom.py`, el dato correcto del alcance es `blast_range`, no `timer`.

### 4.2. Hitbox de bloque final

Debe cubrir dos fases:

- aviso 10 segundos antes de caer el bloque,
- permanencia total una vez la casilla ya fue anulada.

Ademas, durante el ultimo minuto la IA debe tender hacia el centro del mapa.

### 4.3. Hitbox de maldicion

Debe cubrir:

- calaveras visibles,
- lapidas visibles,
- jugadores malditos si la CPU aun no esta maldita.

Si la CPU ya esta maldita, deja de tener sentido evitar contagiarse y esa capa debe relajarse frente a jugadores malditos.

## 5. Prioridades separadas, no mezcladas

No conviene meter todo en un unico `zonas_peligro`.
La arquitectura correcta es tener, como minimo:

- `peligro_bombas`,
- `peligro_bloques_finales`,
- `peligro_maldicion`.

Luego se decide segun prioridad:

1. Bombas.
2. Bloques finales.
3. Maldicion.

Esto permite cumplir la regla del PDF de "si estas dentro, sales aunque tengas que pasar por otra hitbox de menor prioridad".

## 6. Regla inside / outside

Cada capa debe saber responder dos preguntas:

- `esta_dentro_de_esta_capa?`
- `si estoy_fuera, este_camino_me_hace_entrar?`

Ese matiz es obligatorio porque el pliego distingue claramente:

- salir de una hitbox,
- no entrar en una hitbox.

## 7. Maquina de estados recomendada

La IA actual ya usa `estado`. Conviene formalizarlo mejor:

- `ESCAPAR_BOMBA`
- `ESCAPAR_BLOQUE_FINAL`
- `EVITAR_MALDICION`
- `CAZAR`
- `POWERUP`
- `ROMPER`
- `IDLE`

Y separar tambien la memoria:

- `objetivo_coord`
- `objetivo_entidad`
- `ruta_actual`
- `timestamp_ultimo_fijado`
- `motivo_interrupcion`

## 8. Regla de compromiso de objetivos

Cuando la CPU elige un objetivo de prioridad 3:

- debe mantenerlo,
- no debe cambiarlo cada frame,
- solo debe abandonarlo si el objetivo desaparece, deja de ser alcanzable o surge una amenaza de prioridad superior.

Esto ya existe en parte en la IA actual y hay que conservarlo.

## 9. Implementacion de poderes sin tocar KaBoom.py

Esto es importante.

En el bucle de juego actual, la rama CPU solo consume:

- movimiento,
- bomba.

Los campos `hit` y `escudo` que hoy devuelve `IA_CPU.py` no se ejecutan desde `KaBoom.py`.

Si se quiere respetar la norma de "modificar solo IA_CPU.py", entonces:

- el escudo debe activarse llamando directamente a `player.activate_escudo()` desde la propia IA,
- el golpe de bomba debe llamar desde la IA a `bomb.hit_by_player(...)` con la direccion actual,
- el chute puede seguir resolviendose via movimiento porque el propio `Player.move_in_small_steps()` ya empuja bombas cuando `push_bomb_available` esta activo.

## 10. Seleccion de objetivos

### Cazar jugador

Solo si:

- el jugador rival esta vivo,
- no es fantasma,
- existe camino valido,
- no obliga a atravesar hitboxes de prioridad superior,
- y no obliga a acercarse a un jugador maldito si la CPU no esta maldita.

La persecucion no puede ser a coordenada fija permanente. Debe refrescar la posicion fijada cada poco tiempo.

### Ir a por powerup

Solo deben entrar aqui:

- mejoras buenas,
- poderes buenos,
- habilidades soltadas o visibles utiles.

Nunca deben entrar:

- `calavera`,
- elementos de maldicion,
- objetivos que desaparecieron o ya los cogio otro jugador.

### Romper bloque

Solo deben considerarse bloques rompibles que:

- sean alcanzables,
- tengan una casilla adyacente accesible,
- permitan poner bomba con salida segura posterior.

## 11. Bucle maestro recomendado

```text
capturar_contexto()
generar_capas()
calcular_zona_movilidad()

si estoy en peligro de bomba:
    resolver escape de bomba
    salir

si estoy en peligro de bloque final:
    resolver escape de bloque final
    salir

si estoy en trayectoria de maldicion:
    rehacer ruta evitando maldicion
    salir

si tengo estado activo:
    revalidar estado
    ejecutar estado si sigue vivo
    si deja de ser valido -> borrar estado

si no tengo estado:
    seleccionar nuevo estado segun prioridad:
        CAZAR > POWERUP > ROMPER

ejecutar siguiente paso
```

## 12. Lo que ya existe y merece conservarse

La IA actual ya tiene varias piezas utiles:

- uso de `estado`,
- `buscar_camino_estable`,
- simulacion anti suicidio al plantar bomba,
- movimiento milimetrico,
- fijacion temporal del objetivo de caza,
- idea de fronteras para romper mapa.

La guia no propone tirar eso, sino reorganizarlo para cumplir el pliego entero.
