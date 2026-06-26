# Detalles a pulir del segundo prompt

## 1. Bomba: la hitbox debe durar exactamente lo que dura la explosion real

Este es el punto mas critico de todo el segundo prompt.

El problema descrito por el usuario no es que la CPU no vea la bomba antes de explotar. El problema es que, una vez la bomba explota, la CPU cree demasiado pronto que la zona vuelve a ser segura y se mete otra vez en la cruz de fuego mientras la animacion sigue activa.

Traducido al `IA_CPU.py` actual, el foco esta en:

- `capturar_contexto_extra(...)`,
- `actualizar_explosiones_activas(...)`,
- `calcular_peligro_bombas(...)`,
- y la deteccion `en_bomba` dentro de `pensar()`.

Que exige exactamente el segundo prompt:

- Si la CPU esta fuera de la hitbox de bomba, no debe entrar.
- Si la CPU esta dentro de la hitbox de bomba, debe salir cuanto antes.
- Una vez ha salido, no debe volver a entrar hasta que la explosion haya terminado de verdad.
- La comprobacion de peligro debe respetar la hitbox real del jugador, no solo su centro.

Implicacion practica para la segunda pasada:

- la duracion del peligro post-explosion no debe depender solo de una constante aproximada si el juego ya expone explosiones reales activas;
- la capa `peligro_bombas` debe alimentarse de la mejor fuente disponible del gameplay real;
- el respaldo temporal interno solo deberia existir como red de seguridad, no como unica verdad;
- `obtener_casillas_ocupadas(...)` debe seguir siendo la referencia para saber si el cuerpo del jugador sigue tocando una zona peligrosa.

## 2. Maldicion: debe funcionar como una restriccion real

El segundo prompt deja claro que la CPU sigue pisando calaveras, lapidas y zonas de contagio como si no existieran.

Por tanto la capa de maldicion debe comportarse como una hitbox invisible para la CPU:

- fuera de ella, la CPU no debe entrar;
- dentro de ella, la CPU debe salir si puede hacerlo sin violar una prioridad superior;
- si para salvarse de una bomba o de un bloque final necesita atravesarla, entonces si puede hacerlo.

Fuentes de maldicion que la IA debe considerar:

- calaveras visibles,
- lapidas activas,
- jugadores malditos,
- y el radio de contagio que el juego haga relevante alrededor de esos jugadores.

Matiz importante del prompt:

- si la propia CPU ya esta maldita, no debe bloquearse por ello;
- la evitacion fuerte aplica especialmente cuando la CPU aun no esta maldita.

## 3. Regla inside / outside para todas las hitbox invisibles

El segundo prompt insiste mucho en esta distincion y hay que reflejarla en la guia porque es el criterio que decide si una ruta es valida o no.

Situacion A:

- la CPU esta fuera de una hitbox;
- en ese caso el requisito es no entrar.

Situacion B:

- la CPU esta dentro de una hitbox;
- en ese caso el requisito es salir como sea;
- incluso puede cruzar una capa peor o secundaria durante el escape si eso le permite llegar a una zona finalmente segura.

Esto ya esta bastante bien encaminado en `buscar_escape_prioritario(...)`, asi que la segunda pasada debe apoyarse ahi en vez de inventar otra cosa.

## 4. Persistencia de movimientos

El segundo prompt deja una norma muy clara:

- las restricciones si pueden interrumpir un movimiento;
- los movimientos entre si no deben interrumpirse.

Eso significa que, una vez elegido uno de estos estados:

- `CAZAR`,
- `POWERUP`,
- `ROMPER`,

la CPU debe mantenerse en el mismo hasta que:

- el objetivo se complete,
- el objetivo deje de existir,
- el objetivo deje de ser alcanzable,
- o aparezca una prioridad superior como bomba, bloque final o maldicion.

El punto delicado del `IA_CPU.py` actual esta en `pensar()`: si el ejecutor del estado devuelve inputs vacios, el codigo limpia estado y vuelve a elegir objetivo demasiado pronto. Ese comportamiento es precisamente uno de los que el segundo prompt quiere corregir.

## 5. Movimiento CAZAR

El documento dice que este deberia ser el movimiento principal y que ahora mismo no se esta viendo bien en partida.

La traduccion del prompt al codigo actual es:

- elegir una victima viva, no fantasma y alcanzable;
- descartar objetivos malditos si la CPU no esta maldita;
- escoger aleatoriamente entre varias victimas validas;
- fijar una posicion por una ventana corta;
- refrescar esa fijacion con mucha frecuencia;
- perseguir la posicion fijada mientras siga siendo alcanzable;
- plantar bomba solo cuando la explosion pueda alcanzar al objetivo de forma realista;
- y, tras plantar, dejar que la prioridad maxima de bomba tome el control.

El `IA_CPU.py` actual ya tiene la base de esto en `elegir_objetivo(...)` y `ejecutar_caza(...)`, por lo que la segunda pasada debe perfeccionarlo, no sustituirlo.

## 6. Movimiento POWERUP

El segundo prompt insiste en que la CPU no debe tratar los powerups como algo que recoge "si pasa por ahi". Debe ir a por ellos como segundo movimiento de prioridad.

Requisitos concretos:

- se activa solo cuando no procede `CAZAR`;
- debe elegir entre powerups, habilidades y poderes visibles y alcanzables;
- debe excluir cualquier fuente de maldicion;
- no debe poner bombas durante este movimiento;
- debe verificar que el objetivo sigue existiendo mientras va hacia el;
- y debe escoger aleatoriamente si hay varios validos.

En el codigo actual esto aterriza sobre:

- `obtener_powerups_buenos(...)`,
- `elegir_objetivo(...)`,
- `ejecutar_powerup(...)`,
- y posiblemente el propio `capturar_contexto_extra(...)` si faltan objetos visibles del gameplay real.

## 7. Movimiento ROMPER: solo un pulido fino

Aqui el prompt no pide una reescritura. Solo pide que la CPU no de por terminado el movimiento hasta que la bomba quede colocada de verdad.

En la practica:

- si llega a la frontera correcta pero no puede plantar aun porque ha agotado su cupo de bombas activas,
- entonces debe quedarse comprometida con ese objetivo,
- esperar,
- y completar el movimiento solo cuando la bomba se haya plantado o cuando una prioridad superior la obligue a marcharse.

## 8. Menos tiempo muerto tras salir del peligro

El segundo prompt tambien se queja de que la CPU se queda demasiado quieta tras ponerse a salvo.

Eso no obliga necesariamente a rehacer toda la IA. Puede resolverse afinando:

- el refresco de fijacion de caza,
- el mantenimiento del estado,
- y la velocidad con la que `pensar()` vuelve a escoger un nuevo objetivo cuando ya no esta en ninguna hitbox peligrosa.

La idea es que, una vez fuera de peligro, la CPU no se quede "pensando" varios frames si ya tiene informacion suficiente para actuar.
