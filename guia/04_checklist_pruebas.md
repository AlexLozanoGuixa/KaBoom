# Checklist de pruebas

## Supervivencia ante bombas

- La CPU sale de una bomba simple en linea recta sin quedarse girando.
- La CPU resuelve una salida con varios giros, no solo un paso directo.
- Si esta fuera de una hitbox de bomba, no entra voluntariamente en ella.
- Si esta dentro de una hitbox de bomba y no hay salida caminando, activa escudo si lo tiene disponible.
- Si no tiene escudo pero puede golpear bomba, usa el golpe correctamente.
- Si no tiene escudo ni golpe pero si chute, genera carrerilla y chuta la bomba.
- Si no tiene ninguna salida ni poder, al menos intenta moverse y no queda congelada.
- Tras poner una bomba para atacar o romper, entra inmediatamente en logica de escape.

## Bloques finales / bloques presion

- Con la opcion desactivada, la CPU no genera falsas alarmas.
- Con la opcion activada, la CPU empieza a reaccionar durante el ultimo minuto.
- La hitbox de preaviso aparece antes de la caida real.
- La CPU va tendiendo hacia el centro y evita casillas que van a cerrarse.
- Si ya esta dentro de una casilla condenada, sale aunque eso cambie su objetivo actual.

## Maldiciones

- La CPU evita una calavera visible.
- La CPU evita una lapida visible.
- Si la calavera se mueve por explosion, la capa de maldicion se mueve con ella.
- Si la lapida desaparece, la capa de maldicion desaparece.
- La CPU evita a un jugador maldito mientras ella no este maldita.
- Si la CPU ya esta maldita, no se bloquea y sigue jugando normal.
- Si aparece una maldicion en medio de una ruta de objetivo, cancela esa ruta y recalcula.

## Cazar jugadores

- La CPU solo persigue jugadores vivos y no fantasmas.
- Si hay varios jugadores alcanzables, elige uno de forma aleatoria valida.
- Si el objetivo deja de ser alcanzable, abandona la caza y recalcula.
- Si el objetivo muere, abandona la caza.
- Si el objetivo pasa a ser peligroso por maldicion, aborta la persecucion cuando corresponda.
- La CPU solo planta bomba cuando tiene linea de vision y alcance suficiente.
- La CPU no planta bomba si no tiene escapatoria posterior.

## Buscar powerups / habilidades

- La CPU va a por un powerup bueno si no puede cazar a nadie.
- La CPU no persigue una calavera nunca.
- La CPU revalida que el objeto siga existiendo mientras va hacia el.
- Si otro jugador lo coge antes, la CPU cancela ese objetivo y recalcula.
- La CPU tambien considera habilidades sueltas si el contexto las expone.

## Romper bloques

- La CPU solo elige bloques rompibles realmente alcanzables.
- Va a la casilla adyacente correcta, no a una casilla imposible.
- Planta bomba solo cuando esta bien centrada.
- No planta bomba si la simulacion de salida falla.
- Si el bloque ya no existe al llegar o durante la ruta, recalcula.

## Persistencia de objetivo

- La CPU no cambia de objetivo cada frame cuando todo sigue valido.
- Un objetivo de prioridad 3 no se interrumpe por otro objetivo de prioridad 3.
- Un objetivo de prioridad 3 si se interrumpe por bomba, bloque final o maldicion.

## Integracion con el codigo real

- No se modifica `KaBoom.py` si se sigue la restriccion del pliego.
- Escudo y golpe se disparan desde `IA_CPU.py` de forma efectiva.
- La CPU no intenta atravesar casillas bloqueadas que el jugador real no puede pisar.
- El radio de bomba que usa la IA coincide con `blast_range`.
- No se rompe la logica actual de bombas, poderes, curses ni colisiones.

## Criterio de cierre

La implementacion solo deberia darse por buena cuando:

- supera toda esta checklist,
- respeta la jerarquia del PDF,
- y su comportamiento se percibe natural, estable y coherente en partida real.
