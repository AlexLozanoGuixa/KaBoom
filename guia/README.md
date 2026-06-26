# Guia de implementacion de la CPU

## Fuente real del enunciado

El archivo `programacion_CPU.md` no era un Markdown normal: en realidad era un PDF embebido con 13 paginas. Esta carpeta reorganiza ese contenido en una guia de trabajo para implementar la IA de forma ordenada y fiel al pliego.

## Regla principal del encargo

- No tocar la logica estable del juego.
- Priorizar cambios solo en `IA_CPU.py`.
- Usar `KaBoom.py` como fuente de verdad para leer mecanicas ya existentes.
- No romper la logica actual de bombas, poderes, maldiciones, colisiones ni mapa.

## Idea central del documento

La CPU no debe ser solo un bot que huye de bombas. Debe:

- reconstruir continuamente su zona real de movilidad,
- mantenerse a salvo con prioridades estrictas,
- respetar restricciones de mapa y maldiciones,
- y, solo cuando esta segura, elegir un objetivo con una jerarquia fija.

## Jerarquia global de prioridades

### Prioridad base

Antes de cualquier decision, la CPU debe recalcular el mapa y su zona de movilidad real:

- limites del mapa,
- bloques irrompibles,
- bloques rompibles que sigan vivos,
- bloques finales que ya existen,
- bombas y peligros temporales,
- maldiciones visibles,
- jugadores malditos si la propia CPU no esta maldita.

### Prioridad 1

Permanecer fuera de la hitbox de bombas y explosiones.

Si ya esta dentro, salir de inmediato.
Si esta fuera, no entrar.

### Prioridad 2

Restricciones de movimiento:

1. Evitar bloques finales / bloques presion.
2. Evitar maldiciones.

### Prioridad 3

Objetivos de la CPU:

1. Ir a por un jugador para matarlo.
2. Ir a por un powerup / habilidad / poder.
3. Ir a por un bloque rompible para abrir mapa.

## Regla de interrupcion

- Una restriccion o peligro de prioridad superior puede cortar cualquier objetivo en seco.
- Un objetivo de prioridad 3 no puede cortar a otro objetivo de prioridad 3 una vez ya fue elegido.
- La unica excepcion es que aparezca una amenaza superior en el trayecto.

## Regla inside / outside hitbox

Hay que tratar siempre dos situaciones distintas:

- Si la CPU esta fuera de una hitbox: debe evitar entrar.
- Si la CPU esta dentro de una hitbox: debe salir como sea, incluso si para ello tiene que atravesar otra zona menos mala durante el escape.

## Poderes que la CPU debe saber usar

Solo cuando no exista salida caminando:

1. Escudo.
2. Golpear bomba.
3. Chutar bomba.

Siempre con ese orden.

## Documentos de esta carpeta

- `01_arquitectura_objetivo.md`: como debe quedar la IA a nivel de capas, estados y fuentes de datos.
- `02_plan_implementacion_paso_a_paso.md`: orden recomendado de implementacion dentro de `IA_CPU.py`.
- `03_gaps_detectados_en_codigo_actual.md`: diferencias entre el pliego y la IA actual.
- `04_checklist_pruebas.md`: bateria de pruebas para validar que la IA cumple el PDF.
