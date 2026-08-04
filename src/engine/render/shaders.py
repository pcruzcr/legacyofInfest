"""GLSL shader sources for the ModernGL rendering pipeline."""


default_vert = """
#version 330
in vec2 in_position;
in vec2 in_texcoord;
out vec2 uv;
void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    uv = in_texcoord;
}
"""

passthrough_frag = """
#version 330
uniform sampler2D scene;
in vec2 uv;
out vec4 fragColor;
void main() {
    fragColor = texture(scene, uv);
}
"""


# AUD-224 / AUD-230 — el bloom, en dos pasadas y a media resolución.
#
# Extraer lo brillante y difuminarlo es lo caro: 81 lecturas de textura por
# píxel. Hacerlo a resolución completa costaba **3,39 ms** medidos en una
# Intel HD 530 — más que los 2,53 ms del bloom por CPU al que sustituye, o sea
# que delegarlo salía perdiendo.
#
# Se hace en el FBO de media resolución que la tubería **ya reservaba y no
# usaba nunca** (`_bloom_fbo`, w/2 x h/2, creado desde el primer día). A un
# cuarto de píxeles, el mismo kernel cuesta un cuarto. Y sale gratis un halo
# más suave: al recomponer, el filtrado bilineal de la GPU interpola el halo
# de vuelta a tamaño completo, que es exactamente lo que hace la tubería de
# CPU reduciendo y ampliando con `smoothscale`.
#
# `spread` está en píxeles de la TEXTURA DE ORIGEN, que es la de resolución
# completa: el radio real del halo es 4*spread píxeles de pantalla.
bloom_extract_frag = """
#version 330
uniform sampler2D scene;
uniform float threshold;
uniform float spread;
in vec2 uv;
out vec4 fragColor;

// AUD-224 — se extrae lo brillante DENTRO del bucle y se difumina eso.
//
// El orden importa y es lo que estaba mal. Difuminar primero y aplicar el
// umbral despues (`max(blur(color) - threshold, 0)`) destruye el halo: la
// media de un vecindario que mezcla una lampara con el fondo oscuro cae por
// debajo del umbral en cuanto te separas un poco de la fuente, justo donde el
// halo tiene que estar. Extrayendo primero, cada muestra aporta su exceso de
// brillo y el desenfoque lo reparte.
void main() {
    vec2 texel = 1.0 / vec2(textureSize(scene, 0));
    vec3 col = vec3(0.0);
    float weight = 0.0;
    for (int x = -4; x <= 4; x++) {
        for (int y = -4; y <= 4; y++) {
            vec2 off = vec2(float(x), float(y)) * texel * spread;
            float w = exp(-0.5 * (float(x*x + y*y)) / 9.0);
            col += max(texture(scene, uv + off).rgb - threshold, 0.0) * w;
            weight += w;
        }
    }
    fragColor = vec4(col / weight, 1.0);
}
"""

bloom_frag = """
#version 330
uniform sampler2D scene;
uniform sampler2D halo;
uniform float intensity;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec3 color = texture(scene, uv).rgb;
    // El factor de 7 calibra este halo contra el que produce la tuberia de
    // CPU (`PostProcessing._apply_bloom`), para que delegar el bloom no
    // cambie lo que ve el jugador. Medido en una Intel HD 530, diferencia
    // media contra la escena sin bloom, a intensidad 0,25 / 0,50 / 0,80:
    //
    //     CPU   5,44   7,01   8,81      (pico  45   52   86)
    //     GPU   1,79   3,38   5,28      (pico  39   79  126)
    //
    // Mismo orden de magnitud y responde a la intensidad, que es lo que hay
    // que conservar. Antes de AUD-224 la columna de GPU era 0,21 / 0,23 / 0,25:
    // plana e invisible, o sea que delegar el bloom lo habria apagado de hecho.
    fragColor = vec4(color + texture(halo, uv).rgb * intensity * 7.0, 1.0);
}
"""


color_grading_frag = """
#version 330
uniform sampler2D scene;
uniform mat3 colorMatrix;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec3 color = texture(scene, uv).rgb;
    color = colorMatrix * color;
    color = clamp(color, 0.0, 1.0);
    fragColor = vec4(color, 1.0);
}
"""


vignette_frag = """
#version 330
uniform sampler2D scene;
uniform float strength;
uniform float radius;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec3 color = texture(scene, uv).rgb;
    vec2 center = uv - 0.5;
    float dist = length(center);
    float vignette = smoothstep(radius, radius - strength, dist);
    fragColor = vec4(color * vignette, 1.0);
}
"""


motion_blur_frag = """
#version 330
uniform sampler2D scene;
uniform sampler2D prevFrame;
uniform float blendFactor;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec3 current = texture(scene, uv).rgb;
    vec3 previous = texture(prevFrame, uv).rgb;
    fragColor = vec4(mix(current, previous, blendFactor), 1.0);
}
"""


lighting_frag = """
#version 330
uniform sampler2D scene;
uniform sampler2D lightMap;
in vec2 uv;
out vec4 fragColor;

void main() {
    vec3 color = texture(scene, uv).rgb;
    vec3 light = texture(lightMap, uv).rgb;
    fragColor = vec4(color * light, 1.0);
}
"""


# AUD-215: aberracion cromatica para los impactos fuertes.
#
# `strength` llega en 0..1 y NO es un desplazamiento en uv: si lo fuera, un 1.0
# separaria los canales media pantalla. Se escala por MAX_SHIFT, el
# desplazamiento en uv que alcanzan las esquinas con intensidad maxima.
#
# El desplazamiento es radial (crece con la distancia al centro) porque asi se
# comporta una lente real: en el centro optico no hay separacion y el borde es
# donde mas dispersa. Un desplazamiento constante se veria como un doble
# expuesto plano, no como un golpe.
#
# El clamp de las coordenadas no es decorativo: las texturas de la tuberia se
# crean con el modo de repeticion por defecto de moderngl, asi que sin el las
# muestras que se salen por un borde entrarian por el contrario y pintarian una
# franja de color del lado opuesto de la pantalla.
chromatic_aberration_frag = """
#version 330
uniform sampler2D scene;
uniform float strength;
in vec2 uv;
out vec4 fragColor;

// Desplazamiento maximo en uv, en las esquinas, con strength = 1.0.
const float MAX_SHIFT = 0.04;

void main() {
    vec2 fromCenter = uv - 0.5;
    vec2 offset = fromCenter * strength * MAX_SHIFT;

    // El verde se queda en su sitio y hace de referencia: separar los tres
    // canales desdibujaria la imagen en vez de teñirle los bordes.
    vec4 center = texture(scene, uv);
    float r = texture(scene, clamp(uv - offset, 0.0, 1.0)).r;
    float b = texture(scene, clamp(uv + offset, 0.0, 1.0)).b;

    fragColor = vec4(r, center.g, b, center.a);
}
"""


refraction_frag = """
#version 330
uniform sampler2D scene;
// AUD-216 — región de agua en UV de la TEXTURA (origen abajo-izquierda), no
// en píxeles de pygame (origen arriba-izquierda). La tubería sube la escena
// con `pygame.image.tostring(..., True)`, o sea volteada en Y, así que la
// conversión la hace `region_to_gl_uv` en la CPU y aquí ya llega corregida.
// (u0, v0) es la esquina inferior-izquierda; (u1, v1) la superior-derecha.
uniform vec4 region;
uniform float time;        // segundos ya escalados por refraction_speed
uniform float amplitude;   // desplazamiento máximo, en unidades UV
uniform float frequency;   // ondas por unidad UV
uniform vec3 tint;         // multiplicador de color del agua
uniform float tintStrength;
uniform float edgeFade;    // ancho del desvanecido en el borde, en UV
in vec2 uv;
out vec4 fragColor;

void main() {
    // Fuera del agua no se toca nada: es lo que hace que la pasada cueste
    // sólo el fragmento cuando el agua ocupa una franja del mapa.
    if (uv.x < region.x || uv.x > region.z || uv.y < region.y || uv.y > region.w) {
        fragColor = texture(scene, uv);
        return;
    }

    // Sin este desvanecido el borde del agua es un corte recto de un píxel:
    // se ve la costura del rectángulo, que es justo lo que delata el truco.
    vec2 borde = min(uv - region.xy, region.zw - uv);
    float fade = edgeFade > 0.0 ? clamp(min(borde.x, borde.y) / edgeFade, 0.0, 1.0) : 1.0;

    // Dos senos de periodo distinto para que la onda no se lea como periódica.
    float onda = sin(uv.y * frequency + time)
               + 0.5 * sin(uv.x * frequency * 0.7 - time * 1.3);
    vec2 desplazada = uv + vec2(onda * amplitude * fade, 0.0);

    // Se muestrea SÓLO dentro del agua: si la onda empuja la coordenada
    // fuera de la región, arrastraría cielo o roca dentro del estanque.
    desplazada = clamp(desplazada, region.xy, region.zw);

    vec3 color = texture(scene, desplazada).rgb;
    color = mix(color, color * tint, tintStrength * fade);
    fragColor = vec4(color, 1.0);
}
"""


#: Muestras por píxel del abanico radial de `godray_frag`.
#:
#: AUD-226. Una dispersión radial cuesta N lecturas de textura por píxel, así
#: que el número se elige por geometría, no por gusto. A 800x600 y con
#: `godray_density = 0.6`, el píxel más lejano de un foco centrado recorre
#: ~300 px de rayo; con 32 muestras el paso es de ~9 px. La fuente que se
#: muestrea no es la escena sino el mapa de luz —discos degradados de radio
#: 80-280 px—, cuya derivada es suave: 9 px cambian el valor un 3-11 %, por
#: debajo del umbral en que el bandeo se ve. Duplicar a 64 duplica el coste
#: sin ganar nada visible sobre un degradado.
#:
#: Para comparar: `bloom_frag` hace 9x9 = 81 lecturas por píxel. Con 32
#: muestras esta pasada son 33, o sea que NO es la pasada más cara de la
#: tubería — el bloom sigue costando 2,5 veces más.
def upload_frag(swap_rb: bool) -> str:
    """Copia la escena recién subida al primer FBO, colocándola bien.

    AUD-229 — existe para poder subir la superficie **sin convertirla**.

    La tubería subía cada fotograma con
    ``pygame.image.tostring(superficie, "RGBA", True)``, que hace dos cosas:
    reordena los canales al orden que espera OpenGL y voltea la imagen en
    vertical. Las dos cuestan una pasada por los 480.000 píxeles en Python, y
    el `bytes` que devuelve obliga además a moderngl a copiarlo otra vez.
    Medido en la máquina de auditoría, a 800x600:

        pygame.image.tostring(RGBA, flip=True)   3,458 ms
        texture.write(bytes)                     7,517 ms
        texture.write(memoryview de la surface)  0,200 ms

    O sea que **subir el fotograma costaba más que dibujarlo**. Escribiendo el
    búfer de la superficie tal cual no hay conversión ni copia — pero entonces
    llegan los píxeles como los guarda pygame: sin voltear, y con los canales
    en el orden de la máquina.

    Arreglar eso aquí es gratis: esta pasada ya existía (era el `passthrough`
    de la pasada 1) y ya recorría todos los píxeles. Voltear es negar la
    coordenada y, e intercambiar rojo y azul es un swizzle; las dos las hace la
    GPU sin coste medible frente a la copia que ya hacía.

    `swap_rb` lo decide `GLRenderer` mirando las máscaras de la superficie, no
    se asume: en Windows pygame entrega BGRA y en otras plataformas puede ser
    RGBA. Si el formato no es ninguno de los dos conocidos, el renderizador no
    usa este camino y vuelve al de `tostring`, que funciona en cualquier sitio.
    """
    canales = "bgr" if swap_rb else "rgb"
    return f"""
#version 330
uniform sampler2D scene;
in vec2 uv;
out vec4 fragColor;
void main() {{
    // El volteo que hacía `tostring(..., True)`: OpenGL numera las filas de
    // abajo arriba y pygame de arriba abajo.
    //
    // Y el alfa se fuerza a 1. Una `Surface` creada sin `SRCALPHA` —que es la
    // superficie interna del juego— tiene la máscara de alfa a cero, así que
    // su cuarto byte vale **0** en memoria. `tostring(..., "RGBA")` lo repone
    // a 255 al convertir; el búfer crudo no. Con `GL_BLEND` activo y
    // `SRC_ALPHA, ONE_MINUS_SRC_ALPHA`, un fragmento con alfa 0 no escribe
    // nada: la pantalla salía entera del color de limpieza. La tubería
    // trabaja en RGB opaco de principio a fin —todas las demás pasadas
    // escriben `vec4(color, 1.0)`—, así que aquí no se pierde información.
    fragColor = vec4(texture(scene, vec2(uv.x, 1.0 - uv.y)).{canales}, 1.0);
}}
"""


GODRAY_DEFAULT_SAMPLES = 32


def godray_frag(samples: int = GODRAY_DEFAULT_SAMPLES) -> str:
    """Dispersión radial de luz (rayos crepusculares) desde un foco.

    AUD-226. Es el algoritmo clásico de *volumetric light scattering* en
    espacio de pantalla: desde cada píxel se marcha hacia `lightOrigin`
    acumulando la emisión del mapa de luz, con una atenuación geométrica por
    paso. No simula el medio; aproxima lo que se ve cuando la luz atraviesa
    follaje o una ventana.

    Tres decisiones que no son evidentes leyendo el bucle:

    * **La emisión se lee del `lightMap`, no de la escena.** El mapa de luz ya
      está en GPU (lo sube la pasada de iluminación) y contiene exactamente lo
      que debe emitir: dónde hay foco y con cuánta fuerza.
    * **Se resta `emissionThreshold` antes de acumular.** `LightSystem` tiene
      un suelo de luz ambiental (0.3 por defecto) que cubre la pantalla
      entera. Sin restarlo, cada una de las N muestras suma ese suelo y el
      abanico se convierte en una neblina aditiva plana.
    * **La acumulación se divide por `SAMPLES`.** Así el número de muestras es
      un mando de *calidad* y no de *brillo*: subirlo afina el rayo sin
      obligar a retocar `exposure`.

    El número de muestras se hornea como constante en vez de pasarse por
    uniform. Un `for` con límite variable es legal en GLSL 330, pero impide al
    compilador desenrollar el bucle. El precio de hornearlo es que cambiar la
    cuenta obliga a recompilar el programa, cosa que sólo ocurre en
    ``GLRenderer.init()``.
    """
    return f"""
#version 330
uniform sampler2D scene;
uniform sampler2D lightMap;
uniform vec2 lightOrigin;
uniform float density;
uniform float weight;
uniform float decay;
uniform float exposure;
uniform float emissionThreshold;
in vec2 uv;
out vec4 fragColor;

const int SAMPLES = {int(samples)};

void main() {{
    vec3 color = texture(scene, uv).rgb;

    // Paso del recorrido: la fracción `density` del vector que separa este
    // píxel del foco, repartida entre todas las muestras.
    vec2 delta = (uv - lightOrigin) * (density / float(SAMPLES));

    vec2 coord = uv;
    float illumination = 1.0;
    vec3 shafts = vec3(0.0);

    for (int i = 0; i < SAMPLES; i++) {{
        coord -= delta;
        vec3 emission = max(texture(lightMap, coord).rgb - emissionThreshold, 0.0);
        shafts += emission * illumination * weight;
        illumination *= decay;
    }}

    // Aditivo: un rayo añade luz, nunca oscurece lo que cruza.
    fragColor = vec4(color + shafts * (exposure / float(SAMPLES)), 1.0);
}}
"""


colorblind_frag = """
#version 330
uniform sampler2D scene;
uniform int mode; // 0=off, 1=protanopia, 2=deuteranopia, 3=tritanopia
in vec2 uv;
out vec4 fragColor;

const mat3 PROTANOPIA = mat3(
    0.567, 0.433, 0.0,
    0.558, 0.442, 0.0,
    0.0,   0.242, 0.758
);

const mat3 DEUTERANOPIA = mat3(
    0.625, 0.375, 0.0,
    0.7,   0.3,   0.0,
    0.0,   0.3,   0.7
);

const mat3 TRITANOPIA = mat3(
    0.95,  0.05,  0.0,
    0.0,   0.433, 0.567,
    0.0,   0.475, 0.525
);

void main() {
    vec3 color = texture(scene, uv).rgb;
    if (mode == 1) color = PROTANOPIA * color;
    else if (mode == 2) color = DEUTERANOPIA * color;
    else if (mode == 3) color = TRITANOPIA * color;
    fragColor = vec4(clamp(color, 0.0, 1.0), 1.0);
}
"""
