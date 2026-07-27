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


bloom_frag = """
#version 330
uniform sampler2D scene;
uniform float threshold;
uniform float intensity;
in vec2 uv;
out vec4 fragColor;

vec3 gaussianBlur(sampler2D tex, vec2 u, vec2 texel) {
    vec3 col = vec3(0.0);
    float weight = 0.0;
    for (int x = -4; x <= 4; x++) {
        for (int y = -4; y <= 4; y++) {
            vec2 off = vec2(float(x), float(y)) * texel;
            float w = exp(-0.5 * (float(x*x + y*y)) / 9.0);
            col += texture(tex, u + off).rgb * w;
            weight += w;
        }
    }
    return col / weight;
}

void main() {
    vec3 color = texture(scene, uv).rgb;
    float lum = dot(color, vec3(0.2126, 0.7152, 0.0722));
    vec3 bright = max(color - threshold, 0.0);
    vec3 blurred = gaussianBlur(scene, uv, 1.0 / textureSize(scene, 0));
    vec3 bloom = mix(color, color + blurred * bright, intensity);
    fragColor = vec4(bloom, 1.0);
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
