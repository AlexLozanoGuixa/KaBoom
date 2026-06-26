# Segunda guia de implementacion

## Fuente real del encargo

El archivo `Segundo_Prompt_para_la_cpu.md` tampoco es un Markdown normal: realmente contiene un PDF embebido. Esta carpeta reorganiza ese contenido en una segunda guia de trabajo, aterrizada sobre el `IA_CPU.py` actual.

La lectura de esta guia debe hacerse junto con la carpeta madre `guia`, porque esta segunda pasada no sustituye al primer pliego: lo refina.

## Idea central de esta segunda modificacion

El segundo prompt no pide rehacer la IA desde cero. Pide una segunda pasada quirurgica sobre `IA_CPU.py`, conservando lo que ya esta funcionando y corrigiendo solo unos comportamientos concretos.

## Lo que el segundo prompt da por correcto

- La base de analisis de zona de movilidad.
- La restriccion de bloques de presion / bloques finales.
- La idea general del movimiento `ROMPER`.

## Lo que el segundo prompt exige pulir

- Que la hitbox de bomba dure exactamente lo mismo que la explosion real.
- Que la restriccion de maldicion si se cumpla de verdad.
- Que `CAZAR` y `POWERUP` pasen de existir en teoria a ejecutarse bien en partida.
- Que un movimiento elegido no sea interrumpido por otro movimiento.
- Que `ROMPER` no se de por completado hasta colocar la bomba de verdad.
- Que la CPU reaccione mas rapido cuando sale de un peligro.

## Regla de oro de esta carpeta

- Cambios solo en `IA_CPU.py`.
- No tocar `KaBoom.py`.
- No rehacer bloques enteros que ya funcionan.
- Ajustar solo las funciones necesarias para cumplir el segundo prompt "a rajatabla".

## Documentos de esta carpeta

- `01_lo_que_no_se_debe_tocar.md`: que partes deben quedarse estables.
- `02_detalles_a_pulir_del_segundo_prompt.md`: lectura tecnica del segundo prompt aplicada al codigo actual.
- `03_plan_de_segunda_pasada_en_IA_CPU.md`: orden recomendado de cambios dentro de `IA_CPU.py`.
- `04_checklist_de_validacion.md`: pruebas concretas para verificar esta segunda modificacion.
