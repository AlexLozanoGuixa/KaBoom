# Lo que no se debe tocar

## 1. La base de movilidad

El segundo prompt deja claro que la CPU ya entiende bastante bien su zona de movilidad. Eso significa que no se debe rehacer la logica base que determina:

- por que casillas puede avanzar,
- que casillas estan realmente conectadas con su posicion,
- y como encuentra rutas dentro de esa region.

En el `IA_CPU.py` actual esto afecta sobre todo a la idea general que ya forman:

- `generar_mapas_fisicos(...)`,
- `buscar_camino_estable(...)`,
- `obtener_zona_movilidad(...)`,
- `mover_milimetrico(...)`.

Se pueden hacer pequenos ajustes de integracion si alguna capa de peligro necesita entrar mejor en esas funciones, pero no se debe cambiar su filosofia ni rehacer el BFS.

## 2. La restriccion de bloques finales

El segundo prompt dice expresamente que la restriccion encargada de huir de los bloques de presion esta bien programada y no se debe modificar en absoluto de momento.

Por tanto:

- no se debe cambiar la prioridad de `peligro_final`,
- no se debe bajar su peso por debajo de maldicion,
- no se debe rehacer `calcular_peligro_bloques_finales(...)`,
- y no se debe reordenar el bloque de `pensar()` que escapa de esta capa.

Lo unico admisible es asegurarse de que la prioridad de bomba siga por encima, tal y como pide el pliego.

## 3. La estructura base del movimiento ROMPER

El segundo prompt tambien considera correcta la ultima prioridad de movimiento: ir a una frontera alcanzable, ponerse en la casilla adecuada y preparar una bomba para abrir mapa.

Eso implica que no se debe rehacer:

- `obtener_fronteras(...)`,
- la idea de `estado == "ROMPER"`,
- ni la comprobacion de salida segura antes de plantar.

El unico retoque pedido aqui es semantico:

- el movimiento no debe darse por finalizado hasta que la bomba se coloque de verdad.

## 4. La jerarquia general ya existente

La arquitectura de alto nivel actual ya esta bien orientada:

1. Bomba.
2. Bloques finales.
3. Maldicion.
4. Movimientos de objetivo.

No hay que romper esa estructura. La segunda pasada debe refinarla, no sustituirla.

## 5. Limite de alcance de los cambios

Esta segunda modificacion debe seguir una norma muy estricta:

- editar solo `IA_CPU.py`,
- no tocar la logica del motor,
- no introducir efectos secundarios en `KaBoom.py`,
- no cambiar mecanicas de mapa, bombas o colisiones fuera de la CPU.

En resumen: la consigna no es "hacer una IA nueva", sino "pulir la IA actual sin cargarse lo que ya funciona".
