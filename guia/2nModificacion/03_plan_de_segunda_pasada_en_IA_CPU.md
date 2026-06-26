# Plan de segunda pasada en IA_CPU

## Paso 1. Congelar el alcance del cambio

Antes de tocar nada, asumir esta frontera:

- archivo unico a editar: `IA_CPU.py`;
- no tocar `KaBoom.py`;
- no rehacer movilidad;
- no rehacer bloques finales;
- no rehacer el esqueleto de `ROMPER`.

Este paso es importante para no repetir el error de meter cambios demasiado amplios.

## Paso 2. Mejorar el snapshot del mundo

Objetivo:

- que `pensar()` vea exactamente las capas temporales que el juego real esta mostrando.

Que revisar:

- `capturar_contexto_extra(...)`.

Que debe incluir como minimo:

- `powerups`,
- `lapidas`,
- `dropped_abilities`,
- `remaining_time`,
- `bloques_finales_activados`,
- `ruta_espiral`,
- `proximo_bloque_idx`,
- `final_blocks`,
- y, si el bucle real lo expone, `explosions`.

La razon es simple: la bomba no puede sincronizarse con la animacion real si la IA no ve las explosiones reales.

## Paso 3. Corregir la capa de peligro de bombas sin tocar el resto

Objetivo:

- que `peligro_bombas` viva exactamente mientras la explosion es real.

Funciones a revisar:

- `actualizar_explosiones_activas(...)`,
- `calcular_peligro_bombas(...)`,
- comprobacion `en_bomba` dentro de `pensar()`.

Regla de implementacion:

- primero confiar en la informacion real de explosiones activas si existe;
- despues usar una retencion interna conservadora como respaldo;
- nunca liberar una casilla antes de tiempo si el gameplay real sigue mostrando fuego ahi.

## Paso 4. Formalizar la capa de maldicion

Objetivo:

- que la restriccion de maldicion pase de teoria a comportamiento visible.

Funciones a revisar:

- `calcular_peligro_maldicion(...)`,
- y su uso dentro de `pensar()`.

Que debe reflejar:

- calaveras visibles,
- lapidas activas,
- jugadores malditos,
- zonas de contagio relevantes,
- y excepcion cuando la propia CPU ya esta maldita.

## Paso 5. Hacer que el estado persista de verdad

Objetivo:

- que un movimiento elegido no se corte por otro movimiento.

Funcion clave:

- `pensar()`.

Que hay que conseguir:

- si `estado` sigue siendo valido, mantenerlo;
- solo limpiarlo por invalidez objetiva o por irrupcion de una restriccion superior;
- evitar que inputs momentaneamente vacios provoquen replanificacion prematura.

## Paso 6. Refinar CAZAR sin cambiar su arquitectura

Objetivo:

- que la CPU persiga jugadores de forma consistente y no solo ocasional.

Funciones a revisar:

- `elegir_objetivo(...)`,
- `ejecutar_caza(...)`.

Subtareas:

- validar mejor victimas alcanzables;
- refrescar la coordenada fijada con un intervalo corto;
- asegurar la cancelacion correcta si el objetivo muere, desaparece o se vuelve peligroso por maldicion;
- y plantar bomba solo cuando haya alcance, linea limpia y salida posterior.

## Paso 7. Refinar POWERUP sin romper prioridades

Objetivo:

- que el movimiento `POWERUP` se vea realmente en partida.

Funciones a revisar:

- `obtener_powerups_buenos(...)`,
- `elegir_objetivo(...)`,
- `ejecutar_powerup(...)`.

Subtareas:

- incluir todos los objetos beneficiosos visibles;
- excluir calaveras y equivalentes;
- mantener el objetivo mientras siga existiendo;
- no colocar bombas durante este movimiento.

## Paso 8. Pulir ROMPER solo en su condicion de cierre

Objetivo:

- que `ROMPER` no se marque como completado antes de tiempo.

Funcion a revisar:

- `ejecutar_romper(...)`.

Cambio esperado:

- si la CPU esta en la frontera correcta pero no puede plantar aun, debe esperar conservando el estado;
- solo al plantar realmente la bomba se considera completado el objetivo.

## Paso 9. Reducir el tiempo muerto de reaccion

Objetivo:

- que, al salir de una hitbox, la CPU vuelva a actuar enseguida.

Donde tocar:

- la persistencia de estado en `pensar()`,
- el refresco de `CAZAR`,
- y cualquier temporizacion que este dejando a la CPU demasiado quieta.

La meta no es hacerla nerviosa, sino fluida.

## Paso 10. Validar con escenarios cerrados

No dar por buena la segunda pasada hasta comprobar:

- bomba propia,
- bomba ajena,
- reentrada en fuego,
- calavera visible,
- lapida visible,
- jugador maldito,
- persecucion valida,
- powerup alcanzable,
- espera correcta para plantar en `ROMPER`.
