# Gaps detectados en el codigo actual

Este documento aterriza el pliego contra la IA que existe hoy en `IA_CPU.py`.

## 1. El alcance de bomba esta mal leido

Estado actual:

- `calcular_peligros()` intenta leer `radius` y si no existe usa `timer`.

Problema:

- en `KaBoom.py`, la bomba real usa `blast_range`.
- usar `timer` como radio rompe la hitbox real.

Impacto:

- la CPU puede creer que una zona es segura cuando no lo es, o al reves.

## 2. La movilidad no replica del todo las colisiones reales del juego

Estado actual:

- `generar_mapas_fisicos()` solo distingue `1` y `2`.

Problema:

- el jugador vivo colisiona con `1`, `2`, `3` y `4`.

Impacto:

- la IA puede planificar rutas por casillas que en juego real estan bloqueadas.

## 3. Todas las amenazas estan mezcladas en una sola bolsa

Estado actual:

- `calcular_peligros()` devuelve un unico `zonas_peligro`.

Problema:

- el PDF exige prioridades distintas: bomba > bloque final > maldicion.

Impacto:

- no se puede modelar correctamente la regla de "sal de una hitbox aunque tengas que pasar por otra de menor prioridad".

## 4. No existe la prealerta de bloques finales

Estado actual:

- solo se marca `grid == 4`.

Problema:

- el pliego pide que la hitbox aparezca 10 segundos antes de que caiga el bloque.

Impacto:

- la CPU reaccionara demasiado tarde y no tendera al centro del mapa como pide el documento.

## 5. La IA no evita todas las maldiciones del pliego

Estado actual:

- marca lapidas,
- marca jugadores malditos cercanos,
- pero no trata las calaveras como capa separada de maldicion.

Problema:

- el PDF pide evitar cualquier fuente visible de maldicion sin distinguir origen.

Impacto:

- la CPU puede perseguir o pisar una calavera.

## 6. La prioridad POWERUP puede romper el pliego

Estado actual:

- la IA busca cualquier elemento de `powerups` alcanzable.

Problema:

- dentro de `powerups` tambien puede haber `calavera`.

Impacto:

- la CPU puede ir voluntariamente a por una maldicion.

## 7. Las habilidades soltadas no entran en la toma de decisiones

Estado actual:

- `pensar()` intenta leer `powerups` y `lapidas`, pero no `dropped_abilities`.

Problema:

- el pliego dice que tambien hay que ir a por habilidades / poderes visibles que queden libres en el mapa.

Impacto:

- la CPU ignora parte del botin util.

## 8. La CPU devuelve `hit` y `escudo`, pero el juego no los consume para CPU

Estado actual:

- la IA ya pone `inputs["hit"]` y `inputs["escudo"]`,
- pero la rama CPU de `KaBoom.py` solo aplica movimiento y bomba.

Problema:

- el comportamiento existe en la IA pero no llega al gameplay.

Impacto:

- en la practica, la CPU no usa ni escudo ni golpe de bomba.

Solucion compatible con el pliego:

- activar ambas acciones directamente desde `IA_CPU.py`.

## 9. Falta una regla clara de inside / outside hitbox

Estado actual:

- la IA sabe huir,
- pero no tiene la logica completa de "si estoy fuera, no entro; si estoy dentro, salgo aunque pase por otra capa menor".

Impacto:

- la CPU no sigue exactamente la semantica descrita en el PDF.

## 10. La restriccion de maldicion no se aplica como capa de interrupcion completa

Estado actual:

- algunas rutas se descartan por `zonas_peligro`,
- pero no hay una fase explicita de "interrumpir objetivo actual porque aparecio maldicion en el camino".

Impacto:

- puede seguir persiguiendo un objetivo cuando ya deberia replanificar.

## 11. El objetivo CAZAR esta razonablemente encaminado, pero no completo

Lo bueno:

- ya hay `estado`,
- ya hay fijacion temporal de coordenada,
- ya hay verificacion de linea de vision y salida tras plantar bomba.

Lo que falta:

- separar amenazas por prioridad,
- revisar cancelacion por maldicion,
- revalidar mejor al objetivo cuando cambia el contexto,
- ajustar la persecucion para que no dependa solo de zona segura simple.

## 12. El objetivo ROMPER es la parte mas cercana al pliego

Lo bueno:

- ya usa fronteras,
- ya exige salida segura antes de poner bomba,
- ya mantiene un `estado` estable.

Lo que falta:

- integrarlo con capas de prioridad reales,
- asegurar que la casilla de frontera elegida sigue siendo valida bajo las nuevas restricciones.

## 13. La base existe, pero aun no cumple el PDF "a rajatabla"

Resumen honesto:

- la IA actual ya tiene buenas piezas reutilizables,
- pero todavia no implementa completamente la jerarquia del pliego,
- ni la prealerta de bloques finales,
- ni la evitacion total de maldiciones,
- ni el uso efectivo de escudo / golpe,
- ni la separacion formal de prioridades.

La buena noticia es que casi todo puede corregirse desde `IA_CPU.py` sin reescribir la arquitectura del juego.
