# Plan de implementacion paso a paso

## Paso 1. Crear un snapshot unico del mundo

Objetivo:

- dejar de leer datos dispersos,
- tener una sola estructura de contexto por tick.

Que hacer:

- crear un helper `capturar_contexto(...)`,
- leer desde `player`, parametros directos y `sys._getframe(1).f_locals`,
- incluir `powerups`, `lapidas`, `dropped_abilities`, tiempo restante y bloques finales.

Resultado esperado:

- `pensar()` arranca siempre con un `contexto` completo y coherente.

## Paso 2. Normalizar el mapa de colisiones

Objetivo:

- que la IA vea el mismo mapa bloqueante que ve el jugador real.

Que hacer:

- revisar que casillas del `grid` bloquean de verdad al jugador vivo,
- separar `muros_fijos`, `bloques_rompibles`, `bloques_finales`, `bombas`.

Detalle importante:

- en `KaBoom.py`, el jugador colisiona con `grid[cell_y][cell_x] in (1, 2, 3, 4)`.
- la IA actual no refleja eso del todo.

## Paso 3. Separar capas de peligro por prioridad

Objetivo:

- dejar de tratar bombas, bloques finales y maldiciones como si pesaran igual.

Que hacer:

- construir `peligro_bombas`,
- construir `peligro_bloques_finales`,
- construir `peligro_maldicion`.

No mezclar aun las capas.

## Paso 4. Corregir la lectura del radio de bomba

Objetivo:

- que la hitbox de bomba coincida con el juego real.

Que hacer:

- dejar de usar `radius/timer`,
- usar `bomb.blast_range`,
- mantener tambien la casilla central de la bomba y el fuego vivo.

Esto es obligatorio para que la supervivencia sea fiable.

## Paso 5. Rehacer la zona de movilidad real

Objetivo:

- que la CPU se mueva solo dentro de su region conectada del tablero.

Que hacer:

- BFS desde la casilla actual,
- sin atravesar muros,
- sin atravesar bloques rompibles,
- sin salir de limites,
- sin asumir acceso a regiones libres no conectadas.

Este paso es la base de todo el PDF.

## Paso 6. Implementar la logica inside / outside

Objetivo:

- cumplir exactamente la distincion central del pliego.

Que hacer:

- si el jugador esta fuera de una capa, los caminos deben evitarla,
- si el jugador esta dentro, el pathfinding de escape puede tolerar atravesar otras capas de menor prioridad si eso es necesario para salir.

Orden recomendado:

1. escapar de bomba,
2. escapar de bloque final,
3. evitar maldicion.

## Paso 7. Resolver supervivencia ante bombas

Objetivo:

- convertir la bomba en la prioridad maxima real.

Que hacer:

- detectar si cualquier casilla ocupada por la hitbox del jugador toca `peligro_bombas`,
- buscar salida segura con movimiento multigiro,
- si no hay salida caminando, evaluar poderes en este orden:
  - escudo,
  - golpe de bomba,
  - chute de bomba.

Importante:

- como `KaBoom.py` no consume `inputs["escudo"]` ni `inputs["hit"]` para CPU, estas acciones deben dispararse directamente desde `IA_CPU.py` si se quiere respetar el requisito de no tocar el resto del juego.

## Paso 8. Resolver bloques finales

Objetivo:

- cumplir la restriccion del ultimo minuto y los 10 segundos de aviso.

Que hacer:

- leer el estado real del final de partida,
- predecir las casillas que van a cerrarse antes de que caigan,
- convertirlas en capa de peligro de prioridad 2,
- sesgar la IA hacia el centro.

## Paso 9. Resolver maldiciones

Objetivo:

- evitar contagios sin colapsar la IA.

Que hacer:

- marcar calaveras visibles,
- marcar lapidas visibles,
- marcar jugadores malditos si la CPU no esta maldita.

Regla obligatoria del PDF:

- si la CPU cae en maldicion, no debe quedarse bloqueada ni entrar en panico;
- solo debe seguir jugando normal, pero desde ese momento cambia el criterio de evitacion frente a otros jugadores malditos.

## Paso 10. Filtrar correctamente objetivos de powerup

Objetivo:

- no confundir recompensas con maldiciones.

Que hacer:

- excluir `calavera`,
- incluir mejoras normales,
- incluir habilidades soltadas por muerte o perdida de habilidades,
- revalidar que el objeto siga existiendo antes de cada tramo.

## Paso 11. Reforzar el objetivo CAZAR

Objetivo:

- que la persecucion siga al jugador y no a una coordenada muerta.

Que hacer:

- refrescar la posicion fijada cada ventana corta,
- abortar si deja de ser alcanzable,
- abortar si el objetivo muere o se vuelve fantasma,
- abortar si pasa a estar maldito y la CPU aun no esta maldita.

Condicion para plantar bomba:

- misma fila o columna,
- alcance suficiente,
- linea de vision limpia,
- salida segura garantizada.

## Paso 12. Reforzar el objetivo ROMPER

Objetivo:

- abrir mapa de manera util y sin suicidios.

Que hacer:

- elegir solo fronteras validas,
- comprobar que el bloque sigue existiendo,
- centrar al jugador en la casilla correcta,
- poner bomba solo si `puede_escapar_si_pone_bomba(...)` da verdadero.

## Paso 13. Mantener el compromiso de objetivo

Objetivo:

- evitar que la CPU cambie de idea cada frame.

Que hacer:

- conservar `estado` mientras siga siendo valido,
- no saltar entre dos powerups o dos bloques por ruido de frame,
- solo cortar por prioridad superior o invalidez objetiva del objetivo.

## Paso 14. Ajustar aleatoriedad sin romper la logica

Objetivo:

- que la IA no parezca robotica ni absurda.

Que hacer:

- aleatoriedad solo entre opciones validas,
- nunca elegir rutas imposibles,
- nunca elegir acciones que contradigan la prioridad vigente.

Donde si conviene aleatoriedad:

- escoger victima entre varias validas,
- escoger powerup entre varios validos,
- escoger frontera entre varias validas,
- escoger salida entre varias rutas seguras equivalentes.

## Paso 15. Validacion final

Objetivo:

- no dar por buena la IA solo porque "parece funcionar".

Que hacer:

- ejecutar la checklist completa de `04_checklist_pruebas.md`,
- validar que no se haya tocado `KaBoom.py`,
- comprobar que la CPU usa bien escudo, golpe y chute sin romper la mecanica real.
