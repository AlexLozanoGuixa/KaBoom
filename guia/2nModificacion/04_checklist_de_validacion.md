# Checklist de validacion de la segunda modificacion

## Bombas

- La CPU sale de la cruz de una bomba propia y no vuelve a entrar mientras la explosion sigue visible.
- La CPU sale de la cruz de una bomba ajena y no reentra antes de tiempo.
- Si una parte del cuerpo del jugador sigue tocando fuego, la CPU sigue considerandose en peligro.
- Si esta fuera del peligro de bomba, no cruza voluntariamente esa zona para perseguir, recoger o romper.
- Tras plantar una bomba para atacar o abrir mapa, la prioridad de supervivencia toma el control de inmediato.

## Maldiciones

- La CPU evita una calavera visible si no esta obligada por bomba o bloque final.
- La CPU evita una lapida visible si no esta obligada por una prioridad superior.
- La CPU evita acercarse a un jugador maldito cuando ella no esta maldita.
- Si ya esta dentro de una casilla de maldicion y puede salir, la abandona.
- Si la propia CPU esta maldita, no se queda bloqueada por esta capa.

## Persistencia de movimiento

- Si empieza `CAZAR`, no cambia a `POWERUP` ni a `ROMPER` mientras el objetivo siga siendo valido.
- Si empieza `POWERUP`, no cambia a `ROMPER` por ruido de frame.
- Si empieza `ROMPER`, no cambia a otro objetivo hasta poner la bomba o quedar interrumpida por peligro.
- Una restriccion superior si puede cortar cualquier movimiento.

## Cazar jugadores

- Si existe un jugador vivo, alcanzable y no prohibido por maldicion, la CPU intenta perseguirlo.
- Si hay varios jugadores validos, la eleccion sigue siendo aleatoria entre opciones correctas.
- Si el objetivo muere o se vuelve fantasma, la persecucion se cancela.
- Si el objetivo se vuelve maldito y la CPU no lo esta, la persecucion se aborta.
- La bomba para matar solo se coloca cuando hay misma fila o columna, alcance real y salida segura.

## Powerups y poderes

- Si no procede `CAZAR`, la CPU intenta ir a por un objeto beneficioso visible.
- Nunca considera una calavera como objetivo de `POWERUP`.
- Si otro jugador recoge el objeto antes, la CPU abandona ese objetivo.
- Durante `POWERUP` no planta bombas.

## Romper bloques

- La CPU sigue yendo a una frontera valida para abrir mapa.
- Si aun no puede plantar por limite de bombas activas, espera sin perder el objetivo.
- El movimiento `ROMPER` solo se da por completado cuando la bomba queda plantada de verdad.

## Fluidez

- Despues de salir de una hitbox, la CPU elige un nuevo movimiento rapidamente.
- No se queda quieta varios instantes sin motivo cuando ya esta a salvo.

## Criterio de cierre

La segunda modificacion solo deberia darse por buena cuando:

- no rompe lo ya correcto,
- corrige la duracion real del peligro de bomba,
- activa de verdad la restriccion de maldicion,
- y hace visibles en partida `CAZAR` y `POWERUP` como prioridades reales.
