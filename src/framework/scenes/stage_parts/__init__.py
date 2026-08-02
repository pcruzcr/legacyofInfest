"""
Las partes de `StageScene` — AUD-152.

Por qué existe este paquete
============================
`stage_scene.py` llegó a 1.884 líneas. No por descuido: cada fase del proyecto
—luz, clima, ciclo día/noche, estaciones, fantasma de la mejor carrera, buses
de audio, reloj musical— añadió su trozo al mismo sitio, porque el mismo sitio
era donde estaba el estado que necesitaba.

El coste real no es la cifra. Es que un estudiante que abre el archivo para
entender **cómo se dibuja un nivel** tiene que pasar por doscientas líneas de
tablas de bloom y otras doscientas de suscripciones a eventos de sonido antes
de llegar a `update`.

Cómo está partido
------------------
En **mixins**, no en objetos colaboradores. La diferencia importa:

* un colaborador exigiría pasarle media docena de referencias
  (`_lighting`, `_post_processing`, `_stage_data`, `_camera`, `context`…) y
  devolver resultados que `StageScene` volvería a repartir. Eso es más código,
  no menos, y cambia el comportamiento en los bordes;
* un mixin **mueve el texto y no toca nada más**. `self` sigue siendo la misma
  escena, los métodos siguen teniendo los mismos nombres, y las subclases de
  los estudiantes —que sobreescriben `_setup_lighting` o `_subscribe_event_handlers`—
  siguen funcionando sin cambiar una línea.

Es una separación por **lectura**, no por dependencia. Decirlo así evita que
alguien lea esto como una arquitectura que no es: los mixins conocen los
atributos de `StageScene` y no tienen sentido fuera de ella.

Qué vive en cada uno
---------------------
* `ambiente.py` — luz, bloom, viñeta, partículas, estación y hora.
* `senales.py` — todo lo que se suscribe al bus: partículas de golpe, sacudida
  de cámara, destellos y los treinta y ocho sonidos.
* `fantasma.py` — la silueta de tu mejor carrera.
"""
