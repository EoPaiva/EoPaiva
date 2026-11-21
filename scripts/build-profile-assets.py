"""Gera os SVGs animados do README de perfil (preto e branco).

Uso:  python3 scripts/build-profile-assets.py
Requisitos: fonttools + brotli (pip install fonttools brotli) e a família Inter
instalada no sistema (Inter e Inter Display). As fontes entram no próprio SVG,
recortadas só com os caracteres usados, então o visual é o mesmo em qualquer
máquina e o GitHub não precisa carregar nada de fora.
"""

import base64
import io
import math
import os
from html import escape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "profile")
FONT_OUT = os.path.join(ROOT, "assets", "fonts")
FONT_DIRS = ["/usr/share/fonts/opentype/inter", os.path.expanduser("~/.fonts"), "/Library/Fonts"]

FONTS = {
    "D": "InterDisplay-Light.otf",  # títulos
    "T": "InterDisplay-Thin.otf",  # números grandes
    "M": "Inter-Medium.otf",  # rótulos em caixa alta
    "R": "Inter-Regular.otf",  # textos corridos
}

INK = "#ffffff"
BG = "#000000"
PANEL = "#050505"
LINE = "#1d1d1d"
MUTED = "#8c8c8c"
DIM = "#5c5c5c"
FALLBACK = "'Helvetica Neue',Helvetica,Arial,sans-serif"


def find_font(name):
    for folder in FONT_DIRS:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return path
    raise SystemExit(f"Fonte não encontrada: {name}")


_ttf = {}


def ttf(key):
    if key not in _ttf:
        _ttf[key] = TTFont(find_font(FONTS[key]))
    return _ttf[key]


def text_width(s, key, size, spacing=0.0):
    font = ttf(key)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    total = sum(hmtx[cmap.get(ord(ch), cmap[32])][0] for ch in s)
    return total * size / upm + spacing * len(s)


def woff2(key, chars):
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "liga", "calt"]
    options.name_IDs = []
    options.notdef_outline = True
    font = TTFont(find_font(FONTS[key]))
    sub = subset.Subsetter(options)
    sub.populate(text="".join(sorted(set(chars))) + " ")
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return buf.getvalue()


class Svg:
    """Acumula elementos, CSS e o texto usado por fonte para embutir só o necessário."""

    def __init__(self, w, h, title, panel=True):
        self.w, self.h, self.title = w, h, title
        self.defs, self.body, self.css = [], [], []
        self.used = {k: set() for k in FONTS}
        self.panel = panel

    def text(self, x, y, s, key="R", size=14, fill=INK, spacing=0, anchor="start", cls="", extra=""):
        self.used[key].update(s)
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        c = f' class="{cls}"' if cls else ""
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{key},{FALLBACK}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}{c}{extra}>{escape(s)}</text>'
        )

    def add(self, *items):
        self.body.extend(items)

    def render(self):
        faces = []
        for key, chars in self.used.items():
            if not chars:
                continue
            data = base64.b64encode(woff2(key, chars)).decode()
            faces.append(f"@font-face{{font-family:'{key}';src:url(data:font/woff2;base64,{data}) format('woff2');}}")
        css = "\n".join(
            faces
            + [
                "text{font-kerning:normal}",
                ".fb{transform-box:fill-box;transform-origin:center}",
                ".fl{transform-box:fill-box;transform-origin:left center}",
            ]
            + self.css
            + ["@media (prefers-reduced-motion:reduce){*{animation:none!important}}"]
        )
        bg = ""
        if self.panel:
            bg = (
                f'<rect width="{self.w}" height="{self.h}" rx="22" fill="{PANEL}"/>'
                f'<rect x=".5" y=".5" width="{self.w - 1}" height="{self.h - 1}" rx="21.5" fill="none" stroke="{LINE}"/>'
            )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.title)}">'
            f"<title>{escape(self.title)}</title><style>{css}</style>"
            f'<defs>{"".join(self.defs)}</defs>{bg}{"".join(self.body)}</svg>'
        )

    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.render())
        print(f"{name}: {os.path.getsize(path) / 1024:.1f} KB")


def keyframes(name, frames):
    body = " ".join(f"{p}{{{v}}}" for p, v in frames)
    return f"@keyframes {name}{{{body}}}"


# ---------------------------------------------------------------- hero


def hero():
    W, H = 1280, 640
    s = Svg(W, H, "mPaiva_ — Código, produto. Experiências que marcam.")

    # campo de pontos com uma faixa de luz que varre a matriz
    s.defs.append(
        '<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse">'
        '<circle cx="2" cy="2" r="1.15" fill="#fff"/></pattern>'
        '<radialGradient id="fade" cx="76%" cy="46%" r="46%">'
        '<stop offset="0" stop-color="#fff"/><stop offset=".6" stop-color="#fff" stop-opacity=".55"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        '<mask id="mfade"><rect width="1280" height="640" fill="url(#fade)"/></mask>'
        '<linearGradient id="band" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<mask id="mband"><rect class="band" x="-260" y="-200" width="260" height="1040" fill="url(#band)" '
        'transform="rotate(16 640 320)"/></mask>'
        '<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        '<clipPath id="c1"><rect x="0" y="196" width="1280" height="118"/></clipPath>'
        '<clipPath id="c2"><rect x="0" y="314" width="1280" height="118"/></clipPath>'
    )
    s.css += [
        keyframes("band", [("0%", "transform:translateX(0)"), ("100%", "transform:translateX(1900px)")]),
        ".band{animation:band 7s cubic-bezier(.55,.1,.45,.9) infinite}",
        keyframes("rise", [("0%", "transform:translateY(120px)"), ("100%", "transform:translateY(0)")]),
        ".r1{animation:rise 1.25s cubic-bezier(.16,1,.3,1) .25s both}",
        ".r2{animation:rise 1.25s cubic-bezier(.16,1,.3,1) .45s both}",
        keyframes("in", [("0%", "opacity:0"), ("100%", "opacity:1")]),
        ".f1{animation:in 1s ease 1.1s both}.f2{animation:in 1s ease 1.4s both}",
        keyframes("draw", [("0%", "transform:scaleX(0)"), ("100%", "transform:scaleX(1)")]),
        ".dr{animation:draw 1.6s cubic-bezier(.65,0,.35,1) .1s both}",
        keyframes("blink", [("0%,49%", "opacity:1"), ("50%,100%", "opacity:0")]),
        ".cur{animation:blink 1.05s steps(1) infinite}",
        keyframes("sweep", [("0%,55%", "transform:translateX(-420px)"), ("100%", "transform:translateX(1300px)")]),
        ".sw{animation:sweep 6s cubic-bezier(.6,0,.3,1) 1.6s infinite both}",
        keyframes("spin", [("0%", "transform:rotate(0)"), ("100%", "transform:rotate(360deg)")]),
        ".orb{transform-origin:972px 300px;animation:spin 18s linear infinite}",
        ".orb2{transform-origin:972px 300px;animation:spin 70s linear infinite reverse}",
        keyframes("pulse", [("0%", "transform:scale(1);opacity:.7"), ("100%", "transform:scale(3.2);opacity:0")]),
        ".pl{animation:pulse 2.2s cubic-bezier(.2,.6,.3,1) infinite}",
    ]

    s.add(
        f'<rect width="{W}" height="{H}" rx="22" fill="{BG}"/>',
        '<g mask="url(#mfade)"><rect width="1280" height="640" fill="url(#dots)" opacity=".10"/>'
        '<g mask="url(#mband)"><rect width="1280" height="640" fill="url(#dots)" opacity=".85"/></g></g>',
        # órbitas
        '<circle cx="972" cy="300" r="214" fill="none" stroke="#fff" stroke-opacity=".10"/>',
        '<g class="orb2"><circle cx="972" cy="300" r="262" fill="none" stroke="#fff" stroke-opacity=".22" '
        'stroke-dasharray="1 9"/></g>',
        '<g class="orb"><circle cx="1186" cy="300" r="4" fill="#fff"/>'
        '<circle cx="1186" cy="300" r="12" fill="none" stroke="#fff" stroke-opacity=".25"/></g>',
    )

    # barra superior
    s.add(
        s.text(64, 92, "mPaiva", "D", 34, INK, -0.6, cls="f1"),
        f'<rect class="cur" x="{64 + text_width("mPaiva", "D", 34, -0.6) + 4:.1f}" y="88" width="17" height="3" fill="#fff"/>',
        s.text(1216, 90, "PORTFOLIO / 2026", "M", 12.5, MUTED, 3.5, anchor="end", cls="f1"),
        f'<rect class="fl dr" x="64" y="124" width="1152" height="1" fill="{LINE}"/>',
    )

    # título em duas linhas, revelado por máscara
    size = 96
    l1, l2 = "Código, produto.", "Experiências que marcam."
    s.add(
        f'<g clip-path="url(#c1)"><g class="r1">{s.text(60, 290, l1, "D", size, INK, -3)}</g></g>',
        f'<g clip-path="url(#c2)"><g class="r2">{s.text(60, 408, l2, "D", size, "#4d4d4d", -3)}</g></g>',
    )
    # brilho que atravessa a segunda linha
    s.defs.append(f'<clipPath id="t2">{s.text(60, 408, l2, "D", size, INK, -3)}</clipPath>')
    s.add('<g clip-path="url(#t2)"><rect class="sw" x="0" y="314" width="360" height="118" fill="url(#shine)"/></g>')

    s.add(
        s.text(64, 474, "FULL STACK DEVELOPMENT  —  AI ENGINEERING  —  DIGITAL PRODUCTS", "M", 13, "#a3a3a3", 3.6, cls="f2"),
        f'<rect class="fl dr" x="64" y="548" width="1152" height="1" fill="{LINE}"/>',
        s.text(64, 590, "São José dos Campos — SP, Brasil", "R", 14, DIM, 0.2, cls="f2"),
    )
    label = "Disponível para novos projetos"
    lx = 1216 - text_width(label, "R", 14, 0.2)
    s.add(
        s.text(1216, 590, label, "R", 14, "#d4d4d4", 0.2, anchor="end", cls="f2"),
        f'<circle class="fb pl" cx="{lx - 16:.1f}" cy="585" r="4" fill="#fff"/>',
        f'<circle cx="{lx - 16:.1f}" cy="585" r="4" fill="#fff"/>',
    )
    s.save("hero.svg")




# ---------------------------------------------------------------- lançamentos recentes


def vis(s, name, total, start, end, fade=0.25, frm="opacity:0", to="opacity:1", ease="ease"):
    """Elemento visível de `start` a `end` (segundos) dentro de um laço de `total` segundos."""
    pct = lambda t: f"{max(0.0, min(100.0, t / total * 100)):.2f}%"
    a, b, c, d = pct(start), pct(start + fade), pct(end), pct(min(total, end + fade))
    s.css.append(
        keyframes(name, [(f"0%,{a}", frm), (f"{b},{c}", to), (f"{d},100%", frm)])
        + f".{name}{{animation:{name} {total}s {ease} infinite}}"
    )
    return name


def art_wintoolkit(s, ox, oy, p="w"):
    """Janela do app: fila em paralelo, planeta cuja órbita acende com o progresso e terminal real."""
    T = 10.0
    g = [f'<g transform="translate({ox} {oy})">']
    g.append('<rect width="520" height="250" rx="14" fill="#0a0a0a" stroke="#2a2a2a"/>')
    g.append(s.text(18, 25, "upaiva.dev", "R", 11.5, INK, -0.2))
    tx = 168
    for i, tab in enumerate(["INSTALAR", "DRIVERS", "ANALISAR", "OTIMIZAR"]):
        g.append(s.text(tx, 24.5, tab, "M", 7.5, "#fff" if i == 0 else "#4a4a4a", 1.8))
        if i == 0:
            g.append(f'<rect x="{tx}" y="30" width="{text_width(tab, "M", 7.5, 1.8) - 1.8:.1f}" height="1.2" fill="#fff"/>')
        tx += text_width(tab, "M", 7.5, 1.8) + 14
    g.append('<rect x="452" y="13" width="52" height="17" rx="8.5" fill="none" stroke="#2e2e2e"/>')
    g.append(s.text(478, 24.5, "CTRL K", "M", 7, MUTED, 1.4, anchor="middle"))
    g.append('<path d="M0 40 H520" stroke="#1c1c1c"/>')

    # fila com instalação simultânea; o último é MSI e espera a vez
    g.append(s.text(18, 60, "FILA  ·  4 EM PARALELO", "M", 7.5, DIM, 1.8))
    rows = [("Visual C++ 2015+ x64", 0.5, 3.4), ("Git", 0.6, 2.2), ("Node.js LTS", 0.7, 4.6),
            ("Claude Code", 0.8, 3.0), ("Office · MSI", 4.9, 2.6)]
    for i, (name, start, dur) in enumerate(rows):
        y = 84 + i * 24
        done = start + dur
        g.append(s.text(18, y, name, "R", 10.5, "#cfcfcf"))
        g.append(f'<rect x="150" y="{y - 5}" width="82" height="2.5" rx="1.25" fill="#1d1d1d"/>')
        a, b = start / T * 100, done / T * 100
        s.css.append(keyframes(f"{p}q{i}", [(f"0%,{a:.2f}%", "transform:scaleX(0)"), (f"{b:.2f}%,94%", "transform:scaleX(1)"),
                                            ("97%,100%", "transform:scaleX(0)")])
                     + f".{p}q{i}{{animation:{p}q{i} {T}s cubic-bezier(.5,0,.3,1) infinite}}")
        g.append(f'<rect class="fl {p}q{i}" x="150" y="{y - 5}" width="82" height="2.5" rx="1.25" fill="#fff"/>')
        wait = "NA FILA" if i == 4 else "AGUARDA"
        g.append(f'<g class="{vis(s, f"{p}w{i}", T, 0, start - 0.2)}">{s.text(300, y, wait, "M", 7, "#4a4a4a", 1.4, anchor="end")}</g>')
        g.append(f'<g class="{vis(s, f"{p}r{i}", T, start, done - 0.15)}">{s.text(300, y, "INSTALANDO", "M", 7, MUTED, 1.4, anchor="end")}</g>')
        g.append(f'<g class="{vis(s, f"{p}k{i}", T, done, 9.3)}">{s.text(300, y, "OK", "M", 7, "#fff", 1.4, anchor="end")}</g>')

    # terminal com o comando real de cada etapa, digitado
    g.append('<rect x="18" y="196" width="282" height="38" rx="7" fill="#050505" stroke="#1c1c1c"/>')
    lines = [("› winget install Git.Git", "pid 4812 · exit 0 · 2,1 s", 0.3, 3.2),
             ("› winget install OpenJS.NodeJS.LTS", "pid 5120 · exit 0 · 4,6 s", 3.3, 6.4),
             ("› npm i -g @anthropic-ai/claude-code", "pid 6044 · exit 0 · 3,0 s", 6.5, 9.4)]
    for i, (cmd, meta, a, b) in enumerate(lines):
        s.defs.append(f'<clipPath id="{p}tc{i}"><rect class="fl {p}ty{i}" x="28" y="200" width="264" height="14"/></clipPath>')
        aa, bb = a / T * 100, (a + 1.1) / T * 100
        s.css.append(keyframes(f"{p}ty{i}", [(f"0%,{aa:.2f}%", "transform:scaleX(0)"), (f"{bb:.2f}%,100%", "transform:scaleX(1)")])
                     + f".{p}ty{i}{{animation:{p}ty{i} {T}s steps(18) infinite}}")
        g.append(f'<g class="{vis(s, f"{p}tl{i}", T, a, b, 0.15)}"><g clip-path="url(#{p}tc{i})">'
                 + s.text(28, 211, cmd, "M", 7.5, "#e6e6e6", 0.4) + "</g>"
                 + s.text(28, 226, meta, "M", 7, "#5a5a5a", 0.8) + "</g>")

    # planeta de partículas com a órbita acendendo junto com o progresso
    cx, cy, r = 412, 112, 46
    s.defs.append(
        f'<pattern id="{p}dt" width="5.5" height="5.5" patternUnits="userSpaceOnUse">'
        '<circle cx="1.4" cy="1.4" r=".9" fill="#fff"/></pattern>'
        f'<radialGradient id="{p}sh" cx="36%" cy="32%" r="70%"><stop offset="0" stop-color="#fff"/>'
        '<stop offset=".55" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        f'<mask id="{p}pm"><circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{p}sh)"/></mask>'
    )
    s.css += [
        keyframes(f"{p}spin", [("0%", "transform:translateX(0)"), ("100%", "transform:translateX(-11px)")]),
        f".{p}sp{{animation:{p}spin 1.6s linear infinite}}",
        keyframes(f"{p}orb", [("0%,4%", "stroke-dashoffset:1"), ("74%,93%", "stroke-dashoffset:0"), ("97%,100%", "stroke-dashoffset:1")]),
        f".{p}ob{{animation:{p}orb {T}s cubic-bezier(.45,0,.4,1) infinite}}",
    ]
    ring = f"M{cx - 84} {cy} a84 19 0 1 0 168 0 a84 19 0 1 0 -168 0"
    g.append(f'<g transform="rotate(-14 {cx} {cy})">'
             f'<path d="{ring}" fill="none" stroke="#fff" stroke-opacity=".16" stroke-dasharray="1 4"/></g>')
    g.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#0a0a0a"/>')
    g.append(f'<g mask="url(#{p}pm)"><rect class="{p}sp" x="{cx - r - 12}" y="{cy - r}" width="{2 * r + 24}" height="{2 * r}" fill="url(#{p}dt)"/></g>')
    g.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".08"/>')
    g.append(f'<g transform="rotate(-14 {cx} {cy})"><path class="{p}ob" d="{ring}" pathLength="1" stroke-dasharray="1" '
             f'fill="none" stroke="#fff" stroke-width="1.3" stroke-linecap="round"/>'
             f'<circle r="2.6" fill="#fff"><animateMotion dur="{T}s" repeatCount="indefinite" keyPoints="0;0;1;1;0" '
             f'keyTimes="0;.04;.74;.97;1" calcMode="linear" path="{ring}"/></circle></g>')
    # porcentagem ponderada
    steps = [("0%", 0, 1.2), ("18%", 1.2, 2.4), ("41%", 2.4, 3.6), ("63%", 3.6, 5.0), ("86%", 5.0, 6.6), ("100%", 6.6, 9.3)]
    for i, (val, a, b) in enumerate(steps):
        g.append(f'<g class="{vis(s, f"{p}pc{i}", T, a, b, 0.12)}">{s.text(cx, 192, val, "T", 26, INK, -0.6, anchor="middle")}</g>')
    g.append(s.text(cx, 208, "PROGRESSO PONDERADO", "M", 6.8, DIM, 1.8, anchor="middle"))
    g.append(s.text(502, 231, "cpu 19%   ram 52%   net 48 Mbps", "M", 6.8, "#4a4a4a", 0.8, anchor="end"))
    g.append("</g>")
    return "".join(g)


def art_instagram(s, ox, oy, p="i"):
    """Painel da extensão: a fila percorre seis perfis, confirma, pula e pausa para conferir."""
    T = 10.5
    g = [f'<g transform="translate({ox} {oy})">']
    g.append('<rect width="520" height="250" rx="14" fill="#0a0a0a" stroke="#2a2a2a"/>')
    # logo orbital
    g.append('<circle cx="27" cy="21" r="8" fill="none" stroke="#fff" stroke-opacity=".9"/>'
             '<ellipse cx="27" cy="21" rx="13" ry="3.4" transform="rotate(-18 27 21)" fill="none" stroke="#fff" stroke-opacity=".45"/>')
    g.append(s.text(46, 25, "Instagram Fluxo", "R", 11.5, INK, -0.2))
    g.append(s.text(502, 24.5, "SEGUIR  ·  REFERÊNCIAS", "M", 7, DIM, 1.6, anchor="end"))
    g.append('<path d="M0 40 H520" stroke="#1c1c1c"/>')
    g.append(s.text(18, 70, "Sua fila, perfil por perfil.", "D", 21, INK, -0.5))
    g.append(s.text(18, 90, "6 perfis na fila", "R", 10, "#cfcfcf"))

    tw, gap, x0, y0, th = 74, 8, 18, 102, 54
    order = ["ok", "ok", "skip", "ok", "ok", "check"]
    step, first = 1.15, 0.6
    resolve = [first + i * step + 0.75 for i in range(6)]
    status = [("Seguindo @referência_1", 0.0, resolve[2] - 0.05), ("Aguardando intervalo · 38 s", resolve[2], resolve[5] - 0.05),
              ("Pausada para conferência", resolve[5], 9.9)]
    for i, (txt, a, b) in enumerate(status):
        g.append(f'<g class="{vis(s, f"{p}st{i}", T, a, b, 0.2)}">{s.text(502, 90, txt, "R", 10, "#d9d9d9" if i < 2 else "#fff", 0, anchor="end")}</g>')

    for i, kind in enumerate(order):
        x = x0 + i * (tw + gap)
        cx = x + tw / 2
        g.append(f'<rect x="{x}" y="{y0}" width="{tw}" height="{th}" rx="9" fill="#0f0f0f" stroke="#242424"/>'
                 f'<circle cx="{cx}" cy="{y0 + 22}" r="7" fill="#2a2a2a"/>'
                 f'<path d="M{cx - 12} {y0 + 42} a12 10 0 0 1 24 0" fill="#2a2a2a"/>')
        t = resolve[i]
        if kind == "ok":
            body = (f'<rect x="{x}" y="{y0}" width="{tw}" height="{th}" rx="9" fill="#fff"/>'
                    f'<path d="M{cx - 9} {y0 + 27} l6 6 l12 -13" fill="none" stroke="#000" stroke-width="2.2" '
                    'stroke-linecap="round" stroke-linejoin="round"/>')
        elif kind == "skip":
            body = (f'<rect x="{x}" y="{y0}" width="{tw}" height="{th}" rx="9" fill="#262626"/>'
                    f'<path d="M{cx - 8} {y0 + 27} H{cx + 8}" stroke="#9a9a9a" stroke-width="2.2" stroke-linecap="round"/>')
        else:
            body = (f'<rect x="{x + .5}" y="{y0 + .5}" width="{tw - 1}" height="{th - 1}" rx="8.5" fill="#0f0f0f" stroke="#fff" stroke-dasharray="3 3"/>'
                    + s.text(cx, y0 + 33, "?", "D", 20, INK, 0, anchor="middle"))
        name = vis(s, f"{p}t{i}", T, t, 9.9, 0.3, "opacity:0;transform:scale(.86)", "opacity:1;transform:scale(1)",
                   "cubic-bezier(.16,1,.3,1)")
        g.append(f'<g class="fb {name}">{body}</g>')

    # foco que caminha de perfil em perfil
    frames = [("0%", "transform:translateX(0);opacity:0")]
    for i in range(6):
        a = (first + i * step) / T * 100
        frames.append((f"{a:.2f}%,{a + 6:.2f}%", f"transform:translateX({i * (tw + gap)}px);opacity:1"))
    end = (resolve[5] + 0.4) / T * 100
    frames.append((f"{end:.2f}%,100%", f"transform:translateX({5 * (tw + gap)}px);opacity:0"))
    s.css.append(keyframes(f"{p}fc", frames) + f".{p}fc{{animation:{p}fc {T}s cubic-bezier(.7,0,.25,1) infinite}}")
    g.append(f'<rect class="{p}fc" x="{x0 - 4}" y="{y0 - 4}" width="{tw + 8}" height="{th + 8}" rx="12" fill="none" stroke="#fff" stroke-opacity=".55"/>')

    # intervalo entre ações: a linha esvazia antes de cada passo
    s.css.append(keyframes(f"{p}iv", [("0%", "transform:scaleX(1)"), ("100%", "transform:scaleX(0)")])
                 + f".{p}iv{{animation:{p}iv {step}s linear infinite}}")
    g.append(f'<rect x="{x0}" y="{y0 + th + 12}" width="484" height="1" fill="#1d1d1d"/>'
             f'<rect class="fl {p}iv" x="{x0}" y="{y0 + th + 12}" width="484" height="1" fill="#fff" fill-opacity=".6"/>')

    # contadores
    counts = {
        "Confirmados": [0, 1, 2, 2, 3, 4, 4],
        "Para conferir": [0, 0, 0, 0, 0, 0, 1],
        "Pendentes": [6, 5, 4, 3, 2, 1, 0],
        "Pulados": [0, 0, 0, 1, 1, 1, 1],
    }
    marks = {
        "Confirmados": '<rect width="9" height="9" rx="2" fill="#fff"/>',
        "Para conferir": '<rect x=".5" y=".5" width="8" height="8" rx="2" fill="none" stroke="#fff" stroke-dasharray="2 1.5"/>',
        "Pendentes": '<rect width="9" height="9" rx="2" fill="#1f1f1f"/>',
        "Pulados": '<rect width="9" height="9" rx="2" fill="#5a5a5a"/>',
    }
    times = [0] + resolve + [9.9]
    for k, (label, vals) in enumerate(counts.items()):
        col, row = k % 2, k // 2
        x, y = 18 + col * 252, 194 + row * 26
        g.append(f'<g transform="translate({x} {y - 8.5})">{marks[label]}</g>')
        g.append(s.text(x + 16, y, label, "R", 10.5, "#cfcfcf"))
        g.append(f'<path d="M{x} {y + 9} H{x + 232}" stroke="#1a1a1a"/>')
        # cada valor fica visível entre duas resoluções; valores repetidos se fundem
        spans = []
        for j, v in enumerate(vals):
            a, b = times[j], times[j + 1]
            if spans and spans[-1][0] == v:
                spans[-1][2] = b
            else:
                spans.append([v, a, b])
        for j, (v, a, b) in enumerate(spans):
            last = j == len(spans) - 1
            g.append(f'<g class="{vis(s, f"{p}c{k}{j}", T, a, b if not last else 9.9, 0.12)}">'
                     + s.text(x + 232, y + 1, str(v), "T", 17, INK, 0, anchor="end") + "</g>")
    g.append("</g>")
    return "".join(g)


def art_choque(s, ox, oy, p="c"):
    """Centro de comando: ponto por voz com estados reais, prova cronometrada e auditoria append-only."""
    T = 10.0
    g = [f'<g transform="translate({ox} {oy})">']
    g.append('<rect width="520" height="250" rx="14" fill="#0a0a0a" stroke="#2a2a2a"/>')
    g.append(s.text(18, 25, "CHOQUE BGR", "M", 10, INK, 2.2))
    tx = 168
    for i, tab in enumerate(["PONTO", "CARREIRA", "DISCIPLINA", "RECRUTAMENTO"]):
        g.append(s.text(tx, 24.5, tab, "M", 7.5, "#fff" if i == 0 else "#4a4a4a", 1.8))
        if i == 0:
            g.append(f'<rect x="{tx}" y="30" width="{text_width(tab, "M", 7.5, 1.8) - 1.8:.1f}" height="1.2" fill="#fff"/>')
        tx += text_width(tab, "M", 7.5, 1.8) + 14
    g.append('<path d="M0 40 H520" stroke="#1c1c1c"/>')

    # ponto por voz
    g.append(s.text(18, 60, "PONTO POR VOZ  ·  CALL OPERACIONAL", "M", 7.5, DIM, 1.8))
    s.css += [keyframes(f"{p}pl", [("0%", "transform:scale(1);opacity:.8"), ("100%", "transform:scale(2.8);opacity:0")]),
              f".{p}pl{{animation:{p}pl 1.8s cubic-bezier(.2,.6,.3,1) infinite}}"]
    g.append(f'<circle class="fb {p}pl" cx="292" cy="57.5" r="2.6" fill="#fff"/><circle cx="292" cy="57.5" r="2.6" fill="#fff"/>')
    g.append(s.text(286, 60, "AO VIVO", "M", 7, "#cfcfcf", 1.6, anchor="end"))
    roster = [("CMD", 92), ("SGT", 78), ("CB", 64), ("SD", 56)]
    # estados por linha: (texto, início, fim, cor)
    states = [
        [("ACTIVE", 0, 9.9, "#fff")],
        [("ACTIVE", 0, 9.9, "#fff")],
        [("ACTIVE", 0, 2.4, "#fff"), ("GRACE", 2.4, 6.0, MUTED), ("ACTIVE", 6.0, 9.9, "#fff")],
        [("ACTIVE", 0, 4.2, "#fff"), ("GRACE", 4.2, 7.0, MUTED), ("REVIEW", 7.0, 9.9, "#8c8c8c")],
    ]
    clocks = [["2:14:08", "2:14:13", "2:14:18"], ["1:47:52", "1:47:57", "1:48:02"],
              ["0:38:11", "0:38:11", "0:38:16"], ["0:21:40", "0:21:43", "0:21:43"]]
    for i, (rank, nw) in enumerate(roster):
        y = 84 + i * 26
        rw = text_width(rank, "M", 7.5, 1.6) - 1.6 + 16
        g.append(f'<rect x="18" y="{y - 11}" width="{rw:.1f}" height="16" rx="8" fill="none" stroke="#333"/>'
                 + s.text(18 + rw / 2, y - 0.5, rank, "M", 7.5, "#cfcfcf", 1.6, anchor="middle"))
        g.append(f'<rect x="64" y="{y - 5.5}" width="{nw}" height="5" rx="2.5" fill="#262626"/>')
        for j, (txt, a, b, col) in enumerate(states[i]):
            g.append(f'<g class="{vis(s, f"{p}s{i}{j}", T, a, b, 0.2)}">{s.text(300, y, txt, "M", 7, col, 1.6, anchor="end")}</g>')
            if txt == "GRACE":
                s.css.append(keyframes(f"{p}gr{i}", [(f"0%,{a / T * 100:.2f}%", "transform:scaleX(1)"), (f"{b / T * 100:.2f}%,100%", "transform:scaleX(0)")])
                             + f".{p}gr{i}{{animation:{p}gr{i} {T}s linear infinite}}")
                g.append(f'<g class="{p}s{i}{j}"><rect class="fl {p}gr{i}" x="166" y="{y - 4}" width="34" height="2" rx="1" fill="#8c8c8c"/></g>')
        for j, c in enumerate(clocks[i]):
            a, b = j * 3.3, (j + 1) * 3.3 if j < 2 else 9.9
            g.append(f'<g class="{vis(s, f"{p}k{i}{j}", T, a, b, 0.1)}">{s.text(244, y, c, "M", 7.5, "#5a5a5a", 0.6, anchor="end")}</g>')

    # auditoria append-only digitando
    g.append('<rect x="18" y="196" width="282" height="38" rx="7" fill="#050505" stroke="#1c1c1c"/>')
    logs = [("audit · ponto CB → GRACE · tolerância 5 min", "append-only · outbox ok", 2.4, 5.9),
            ("audit · promoção SD → CB · confirmada", "cargo e apelido sincronizados", 0.2, 2.3),
            ("audit · ponto SD → REVIEW_REQUIRED", "aguarda decisão humana", 7.0, 9.8)]
    for i, (cmd, meta, a, b) in enumerate(logs):
        s.defs.append(f'<clipPath id="{p}tc{i}"><rect class="fl {p}ty{i}" x="28" y="200" width="264" height="14"/></clipPath>')
        aa, bb = a / T * 100, (a + 1.0) / T * 100
        s.css.append(keyframes(f"{p}ty{i}", [(f"0%,{aa:.2f}%", "transform:scaleX(0)"), (f"{bb:.2f}%,100%", "transform:scaleX(1)")])
                     + f".{p}ty{i}{{animation:{p}ty{i} {T}s steps(18) infinite}}")
        g.append(f'<g class="{vis(s, f"{p}tl{i}", T, a, b, 0.15)}"><g clip-path="url(#{p}tc{i})">'
                 + s.text(28, 211, cmd, "M", 7.5, "#e6e6e6", 0.4) + "</g>"
                 + s.text(28, 226, meta, "M", 7, "#5a5a5a", 0.8) + "</g>")

    # prova de recrutamento com timer no servidor
    cx, cy, r = 412, 112, 44
    g.append(s.text(cx, 60, "RECRUTAMENTO  ·  PROVA", "M", 7, DIM, 1.6, anchor="middle"))
    s.css.append(keyframes(f"{p}tm", [("0%", "stroke-dashoffset:0"), ("94%", "stroke-dashoffset:.96"), ("100%", "stroke-dashoffset:0")])
                 + f".{p}tm{{animation:{p}tm {T}s linear infinite}}")
    g.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1f1f1f" stroke-width="2"/>'
             f'<circle class="{p}tm" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-width="2" pathLength="1" '
             f'stroke-dasharray="1" stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>')
    mins = ["29:58", "27:12", "24:36", "21:50"]
    for j, m in enumerate(mins):
        a, b = j * 2.5, (j + 1) * 2.5 if j < 3 else 9.9
        g.append(f'<g class="{vis(s, f"{p}m{j}", T, a, b, 0.15)}">{s.text(cx, cy + 8, m, "T", 22, INK, -0.4, anchor="middle")}</g>')
    g.append(s.text(cx, cy + 60, "TIMER NO SERVIDOR", "M", 5.8, "#5a5a5a", 1.4, anchor="middle"))
    # 24 questões, respondidas uma a uma com autosave
    for q in range(24):
        col, row = q % 12, q // 12
        x, y = cx - 66 + col * 12, 184 + row * 12
        g.append(f'<rect x="{x}" y="{y}" width="8" height="8" rx="2" fill="#1f1f1f"/>')
        t = 0.3 + q * 0.36
        g.append(f'<rect class="{vis(s, f"{p}q{q}", T, t, 9.6, 0.15)}" x="{x}" y="{y}" width="8" height="8" rx="2" fill="#fff"/>')
    g.append(s.text(cx, 225, "24 QUESTÕES  ·  AUTOSAVE", "M", 6.5, DIM, 1.6, anchor="middle"))
    g.append(s.text(502, 238, "decisão final humana", "M", 6.8, "#4a4a4a", 0.8, anchor="end"))
    g.append("</g>")
    return "".join(g)


def anim(s, name, T, frames, ease="ease", extra=""):
    """Animação num laço de T segundos com quadros em segundos: [(t ou (t1, t2), css), ...]."""
    pct = lambda t: f"{max(0.0, min(100.0, t / T * 100)):.2f}%"
    body = []
    for t, css in frames:
        ts = t if isinstance(t, tuple) else (t,)
        body.append((",".join(pct(x) for x in ts), css))
    s.css.append(keyframes(name, body) + f".{name}{{{extra}animation:{name} {T}s {ease} infinite}}")
    return name


def wrap(text, key, size, maxw, spacing=0.0):
    lines, cur = [], ""
    for word in text.split():
        cand = f"{cur} {word}".strip()
        if cur and text_width(cand, key, size, spacing) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def azv_city(s, p, T, t0, t1):
    """A maquete 3D da cidade dentro da janela 520 x 250: relevo, ruas, rio, casas e as torres da AZV subindo em t0."""
    import random
    rnd = random.Random(7)
    K = 0.8
    CX, CY = 262, 180

    def P(x, y, z=0.0):
        return CX + (x - y) * 0.866 * K, CY + (x + y) * 0.5 * K - z * K

    def poly(pts, fill):
        return f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="{fill}"/>'

    g = []
    for k in range(7):
        pts = []
        for i in range(0, 41):
            x = -160 + i * 8
            yy = -150 + k * 9
            z = 8 + 26 * math.exp(-((x + 40) / 70) ** 2) + 14 * math.exp(-((x - 90) / 45) ** 2) - k * 4
            pts.append(P(x, yy, max(z, 0)))
        d = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts)
        g.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-opacity="{0.05 + k * 0.018:.3f}" stroke-width=".8"/>')
    for v in range(-120, 121, 30):
        a, b = P(v, -125), P(v, 125)
        c, d = P(-125, v), P(125, v)
        g.append(f'<path d="M{a[0]:.1f} {a[1]:.1f} L{b[0]:.1f} {b[1]:.1f} M{c[0]:.1f} {c[1]:.1f} L{d[0]:.1f} {d[1]:.1f}" stroke="#1d1d1d" stroke-width=".8"/>')
    river = [P(-150, 70), P(-95, 52), P(-40, 64), P(10, 40), P(60, 58), P(120, 30), P(170, 44)]
    d = f"M{river[0][0]:.1f} {river[0][1]:.1f} " + " ".join(
        f"Q{river[i][0]:.1f} {river[i][1]:.1f} {(river[i][0] + river[i + 1][0]) / 2:.1f} {(river[i][1] + river[i + 1][1]) / 2:.1f}"
        for i in range(1, len(river) - 1)) + f" T{river[-1][0]:.1f} {river[-1][1]:.1f}"
    s.css.append(keyframes(f"{p}rv", [("0%", "stroke-dashoffset:0"), ("100%", "stroke-dashoffset:-40")])
                 + f".{p}rv{{animation:{p}rv 3s linear infinite}}")
    g.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-opacity=".10" stroke-width="7" stroke-linecap="round"/>'
             f'<path class="{p}rv" d="{d}" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="1.1" stroke-dasharray="14 6"/>')
    towers = [("Ares", -55, -55, 62), ("Senses", 5, -100, 48), ("Neori", 80, -60, 40), ("Altus", 95, 20, 56),
              ("Martim", -100, 30, 44), ("Riza", -40, 45, 52), ("Serena", 25, 50, 34)]
    houses = []
    for _ in range(150):
        x, y = rnd.uniform(-125, 125), rnd.uniform(-125, 110)
        if any(abs(x - tx_) < 14 and abs(y - ty_) < 14 for _, tx_, ty_, _ in towers):
            continue
        if 30 < y < 75 and -150 < x < 170 and abs(y - (55 - x * 0.08)) < 12:
            continue
        houses.append((x, y, rnd.choice([2, 2, 3, 4, 6, 9]), rnd.uniform(2.2, 3.6)))
    houses.sort(key=lambda h: h[0] + h[1])
    for x, y, h, a in houses:
        top = [P(x - a, y - a, h), P(x + a, y - a, h), P(x + a, y + a, h), P(x - a, y + a, h)]
        left = [P(x - a, y + a, 0), P(x + a, y + a, 0), P(x + a, y + a, h), P(x - a, y + a, h)]
        right = [P(x + a, y + a, 0), P(x + a, y - a, 0), P(x + a, y - a, h), P(x + a, y + a, h)]
        g.append(poly(left, "#161616") + poly(right, "#222") + poly(top, "#2e2e2e"))
    s.defs.append(f'<linearGradient id="{p}fr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/>'
                  f'<stop offset="1" stop-color="#bdbdbd"/></linearGradient>'
                  f'<linearGradient id="{p}fl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8a8a8a"/>'
                  f'<stop offset="1" stop-color="#4a4a4a"/></linearGradient>'
                  f'<linearGradient id="{p}bm" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity=".55"/>'
                  f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    order = sorted(range(len(towers)), key=lambda i: towers[i][3])
    a = 6.0
    for i in sorted(range(len(towers)), key=lambda i: towers[i][1] + towers[i][2]):
        name, x, y, h = towers[i]
        cx_, cy_ = P(x, y)
        slot = order.index(i)
        r0 = t0 + 0.15 + slot * 0.16
        anim(s, f"{p}u{i}", T, [((0, r0), "transform:scaleY(0)"), ((r0 + 1.0, t1), "transform:scaleY(1)"),
                                 ((min(T, t1 + 0.3), T), "transform:scaleY(0)")],
             "cubic-bezier(.16,1,.3,1)", "transform-box:fill-box;transform-origin:50% 100%;")

        def L(xx, yy, zz):
            return ((xx - yy) * 0.866 * K, (xx + yy) * 0.5 * K - zz * K)

        left = [L(-a, a, 0), L(a, a, 0), L(a, a, h), L(-a, a, h)]
        right = [L(a, a, 0), L(a, -a, 0), L(a, -a, h), L(a, a, h)]
        top = [L(-a, -a, h), L(a, -a, h), L(a, a, h), L(-a, a, h)]
        floors = []
        for z in range(5, int(h) - 1, 4):
            p1, p2, p3 = L(-a, a, z), L(a, a, z), L(a, -a, z)
            floors.append(f"M{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f} L{p3[0]:.1f} {p3[1]:.1f}")
        body = (poly(left, f"url(#{p}fl)") + poly(right, f"url(#{p}fr)") + poly(top, "#fff")
                + f'<path d="{" ".join(floors)}" fill="none" stroke="#000" stroke-opacity=".28" stroke-width=".6"/>')
        tt = L(0, 0, h)
        lbl_y = tt[1] - (30 if slot % 2 == 0 else 44)
        lab = vis(s, f"{p}l{i}", T, r0 + 0.9, t1 - 0.1, 0.3)
        g.append(f'<g transform="translate({cx_:.1f} {cy_:.1f})"><g class="{p}u{i}">{body}</g>'
                 f'<g class="{lab}"><rect x="-0.6" y="{lbl_y + 6:.1f}" width="1.2" height="{tt[1] - lbl_y - 6:.1f}" fill="url(#{p}bm)"/>'
                 f'<circle cx="0" cy="{lbl_y + 6:.1f}" r="1.6" fill="#fff"/>'
                 + s.text(0, lbl_y, name.upper(), "M", 6.4, "#e6e6e6", 1.2, anchor="middle") + "</g></g>")
    return "".join(g)


def art_azv(s, ox, oy, p="a"):
    """O site da AZV inteiro numa janela: vitrine, revista, maquete 3D e painel com SEO, uma cena por vez."""
    T = 16.0
    SC = [("VITRINE", 0.0, 4.0), ("REVISTA", 4.0, 8.0), ("MAQUETE 3D", 8.0, 12.0), ("PAINEL E SEO", 12.0, 16.0)]
    g = [f'<g transform="translate({ox} {oy})">']
    g.append('<rect width="520" height="250" rx="14" fill="#0a0a0a" stroke="#2a2a2a"/>')
    # barra do navegador
    g.append('<rect x="14" y="11" width="146" height="18" rx="9" fill="#111" stroke="#222"/>'
             '<rect x="22.5" y="18.6" width="6" height="5" rx="1" fill="none" stroke="#8a8a8a" stroke-width=".8"/>'
             '<path d="M24 18.6 V17.2 a1.5 1.5 0 0 1 3 0 V18.6" fill="none" stroke="#8a8a8a" stroke-width=".8"/>')
    g.append(s.text(33, 23.2, "azvlancamentos.com.br", "R", 7.4, "#bdbdbd"))
    widths = [text_width(t, "M", 6.6, 1.5) - 1.5 for t, _, _ in SC]
    tx = 504 - sum(widths) - 14 * (len(SC) - 1)
    for i, (tab, a, b) in enumerate(SC):
        w = widths[i]
        g.append(s.text(tx, 23.4, tab, "M", 6.6, "#4a4a4a", 1.5))
        g.append(f'<g class="{vis(s, f"{p}tb{i}", T, a, b - 0.25, 0.25)}">{s.text(tx, 23.4, tab, "M", 6.6, "#fff", 1.5)}'
                 f'<rect x="{tx:.1f}" y="29.5" width="{w:.1f}" height="1.2" fill="#fff"/></g>')
        tx += w + 14
    g.append('<path d="M0 40 H520" stroke="#1c1c1c"/>')
    s.defs.append(f'<clipPath id="{p}cl"><rect x="1" y="41" width="518" height="208" rx="13"/></clipPath>')
    g.append(f'<g clip-path="url(#{p}cl)">')

    def scene(i):
        _, a, b = SC[i]
        return vis(s, f"{p}sc{i}", T, a, b - 0.3, 0.3)

    up = "opacity:0;transform:translateY(7px)"
    on = "opacity:1;transform:translateY(0)"

    # 1. vitrine: a abertura da home passando pelos destaques, as estações da página e as páginas por bairro
    v = []
    names = ["Senses", "Albor América", "Reserva Costa Verde", "Martim"]
    seg = (238 - 18 - 3 * 4) / 4
    for i in range(4):
        x = 18 + i * (seg + 4)
        t_a, t_b = 0.25 + i * 0.9, 0.25 + (i + 1) * 0.9
        v.append(f'<rect x="{x:.1f}" y="52" width="{seg:.1f}" height="1.6" rx=".8" fill="#262626"/>')
        cls = anim(s, f"{p}sb{i}", T, [((0, t_a), "transform:scaleX(0)"), ((t_b, 3.75), "transform:scaleX(1)"),
                                        ((4.0, T), "transform:scaleX(0)")], "linear", "transform-box:fill-box;transform-origin:left center;")
        v.append(f'<rect class="{cls}" x="{x:.1f}" y="52" width="{seg:.1f}" height="1.6" rx=".8" fill="#fff"/>')
        size = 24
        while text_width(names[i], "D", size, -0.4) > 222:
            size -= 1
        end = t_b if i < 3 else 3.7
        c1 = vis(s, f"{p}nm{i}", T, t_a, end - 0.15, 0.2, up, on, "cubic-bezier(.16,1,.3,1)")
        v.append(f'<g class="{c1}">{s.text(18, 110, names[i], "D", size, INK, -0.4)}'
                 f'{s.text(238, 68, f"0{i + 1} / 04", "M", 6.2, "#8a8a8a", 1.4, anchor="end")}</g>')
    v.append(s.text(18, 68, "IMÓVEIS NA PLANTA  ·  SJC", "M", 6.2, "#6a6a6a", 1.4))
    st = ["FACHADA", "APARTAMENTO", "LAZER", "PLANTAS", "LOCAL", "CONTATO"]
    sx = 18
    for i, w_ in enumerate(st):
        ww = text_width(w_, "M", 5.4, 1.1) - 1.1
        v.append(s.text(sx, 134, w_, "M", 5.4, "#4a4a4a", 1.1))
        c2 = vis(s, f"{p}st{i}", T, 0.35 + i * 0.55, 0.35 + (i + 1) * 0.55 - 0.14, 0.12)
        v.append(f'<g class="{c2}">{s.text(sx, 134, w_, "M", 5.4, "#fff", 1.1)}<rect x="{sx:.1f}" y="138" width="{ww:.1f}" height="1" fill="#fff"/></g>')
        sx += ww + 7
    assert sx - 7 < 256, sx
    cta = "FALAR COM A TATIANE"
    cw = text_width(cta, "M", 6, 1.2) - 1.2 + 30
    v.append(f'<rect x="18" y="152" width="{cw:.1f}" height="18" rx="9" fill="#fff"/>'
             f'<circle cx="29" cy="161" r="2.6" fill="none" stroke="#0a0a0a" stroke-width="1"/>'
             + s.text(36, 163.2, cta, "M", 6, "#0a0a0a", 1.2))
    # a imagem do prédio, que abre por uma cortina
    PX, PY, PW, PH = 262, 52, 240, 122
    v.append(f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="6" fill="#0f0f0f" stroke="#1e1e1e"/>')
    s.defs.append(f'<radialGradient id="{p}sky" cx="50%" cy="35%" r="70%"><stop offset="0" stop-color="#1d1d1d"/>'
                  f'<stop offset="1" stop-color="#0c0c0c"/></radialGradient>'
                  f'<clipPath id="{p}ph"><rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" rx="6"/></clipPath>')
    zoom = anim(s, f"{p}zm", T, [(0, "transform:scale(1.1)"), ((3.9, T), "transform:scale(1)")], "cubic-bezier(.2,.6,.3,1)",
                "transform-box:fill-box;transform-origin:50% 80%;")
    K2, CX2, CY2 = 1.05, 382, 160

    def I(x, y, z=0.0):
        return CX2 + (x - y) * 0.866 * K2, CY2 + (x + y) * 0.5 * K2 - z * K2

    def pg(pts, fill, extra=""):
        return f'<polygon points="{" ".join(f"{u:.1f},{w:.1f}" for u, w in pts)}" fill="{fill}"{extra}/>'

    def box(x0, x1, y0, y1, z0, z1, cl, cr, ct, lines=0):
        out = (pg([I(x0, y1, z0), I(x1, y1, z0), I(x1, y1, z1), I(x0, y1, z1)], cl)
               + pg([I(x1, y1, z0), I(x1, y0, z0), I(x1, y0, z1), I(x1, y1, z1)], cr)
               + pg([I(x0, y0, z1), I(x1, y0, z1), I(x1, y1, z1), I(x0, y1, z1)], ct))
        if lines:
            ds = []
            for z in range(int(z0) + lines, int(z1) - 1, lines):
                a1, a2, a3 = I(x0, y1, z), I(x1, y1, z), I(x1, y0, z)
                ds.append(f"M{a1[0]:.1f} {a1[1]:.1f} L{a2[0]:.1f} {a2[1]:.1f} L{a3[0]:.1f} {a3[1]:.1f}")
            out += f'<path d="{" ".join(ds)}" fill="none" stroke="#000" stroke-opacity=".25" stroke-width=".6"/>'
        return out

    ph = [f'<rect x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="url(#{p}sky)"/>']
    ph.append(pg([I(-60, -60), I(60, -60), I(60, 60), I(-60, 60)], "#121212", ' stroke="#1f1f1f" stroke-width=".8"'))
    for k in range(-60, 61, 20):
        a1, a2, b1, b2 = I(k, -60), I(k, 60), I(-60, k), I(60, k)
        ph.append(f'<path d="M{a1[0]:.1f} {a1[1]:.1f} L{a2[0]:.1f} {a2[1]:.1f} M{b1[0]:.1f} {b1[1]:.1f} L{b2[0]:.1f} {b2[1]:.1f}" stroke="#181818" stroke-width=".6"/>')
    ph.append(box(-40, -22, 18, 40, 0, 14, "#1c1c1c", "#262626", "#303030"))
    ph.append(box(22, 44, -40, -18, 0, 22, "#1c1c1c", "#262626", "#303030"))
    ph.append(box(-26, 26, -26, 26, 0, 9, "#3a3a3a", "#5c5c5c", "#7a7a7a"))
    ph.append(box(-12, 12, -12, 12, 9, 84, f"url(#{p}fl)", f"url(#{p}fr)", "#fff", 4))
    ph.append(box(-14, 14, -14, 14, 84, 87, "#9a9a9a", "#cfcfcf", "#f2f2f2"))
    cur = anim(s, f"{p}ct", T, [((0, 0.2), "transform:scaleY(1)"), ((1.1, T), "transform:scaleY(0)")],
               "cubic-bezier(.7,0,.2,1)", "transform-box:fill-box;transform-origin:50% 0;")
    v.append(f'<g clip-path="url(#{p}ph)"><g class="{zoom}">{"".join(ph)}</g>'
             f'<rect class="{cur}" x="{PX}" y="{PY}" width="{PW}" height="{PH}" fill="#0f0f0f"/></g>')
    v.append(s.text(PX, 186, "TIPOLOGIAS · LAZER · PLANTAS · VÍDEOS · BOOKS", "M", 5.2, "#6a6a6a", 1))
    v.append(s.text(18, 198, "PÁGINAS POR BAIRRO E POR TAMANHO", "M", 5.6, "#5a5a5a", 1.3))
    cols = ["JARDIM AQUARIUS", "VILA EMA", "JARDIM AMÉRICA", "ZONA SUL", "CARAGUATATUBA", "STUDIOS E 1 DORM.", "3 DORMITÓRIOS"]
    cx = 18
    for i, c in enumerate(cols):
        cw2 = text_width(c, "M", 5.2, 0.8) - 0.8 + 13
        v.append(f'<rect x="{cx:.1f}" y="206" width="{cw2:.1f}" height="15" rx="7.5" fill="none" stroke="#2a2a2a"/>'
                 + s.text(cx + 6.5, 215.7, c, "M", 5.2, "#8a8a8a", 0.8))
        c3 = vis(s, f"{p}co{i}", T, 0.6 + i * 0.45, 0.6 + (i + 1) * 0.45 - 0.12, 0.12)
        v.append(f'<g class="{c3}"><rect x="{cx:.1f}" y="206" width="{cw2:.1f}" height="15" rx="7.5" fill="#fff"/>'
                 + s.text(cx + 6.5, 215.7, c, "M", 5.2, "#0a0a0a", 0.8) + "</g>")
        cx += cw2 + 4.5
    assert cx < 506, cx
    g.append(f'<g class="{scene(0)}">{"".join(v)}</g>')

    # 2. revista: o nome subindo letra por letra e o índice das matérias
    r = []
    for li, (word, color, y) in enumerate([("Revista", INK, 104), ("AZV", "#5a5a5a", 140)]):
        x = 18
        for k, ch in enumerate(word):
            t = 4.2 + (li * 7 + k) * 0.06
            c = vis(s, f"{p}rl{li}{k}", T, t, 7.7, 0.35, "opacity:0;transform:translateY(12px)", on, "cubic-bezier(.16,1,.3,1)")
            r.append(f'<g class="{c}">{s.text(x, y, ch, "D", 36, color, -0.6)}</g>')
            x += text_width(ch, "D", 36, -0.6)
    r.append(s.text(18, 164, "17 MATÉRIAS  ·  PORTUGUÊS E INGLÊS", "M", 6, "#6a6a6a", 1.4))
    r.append(s.text(18, 178, "GUIAS DE BAIRRO, COMPRA NA PLANTA E LAZER", "M", 5.4, "#4a4a4a", 1.2))
    rd = anim(s, f"{p}rd", T, [((0, 4.3), "transform:scaleX(0)"), ((7.7, T), "transform:scaleX(1)")], "linear",
              "transform-box:fill-box;transform-origin:left center;")
    r.append(f'<rect x="18" y="222" width="220" height="1" fill="#222"/><rect class="{rd}" x="18" y="222" width="220" height="1" fill="#fff"/>')
    r.append(s.text(258, 62, "TODAS AS MATÉRIAS", "M", 6, "#5a5a5a", 1.4))
    r.append(s.text(502, 62, "PT  ·  EN", "M", 6, "#5a5a5a", 1.4, anchor="end"))
    arts = ["Guia do Jardim Aquarius", "Como ler a planta de um apartamento", "Comprar apartamento na planta: o passo a passo",
            "O lazer subiu: os rooftops dos lançamentos", "Do Vale ao mar: o guia de Caraguatatuba", "Apartamento com pet"]
    for k, title in enumerate(arts):
        y = 78 + k * 25
        t = 4.35 + k * 0.12
        size = 8.4
        while text_width(title, "R", size) > 222:
            size -= 0.2
        c = vis(s, f"{p}ra{k}", T, t, 7.7, 0.4, "opacity:0;transform:translateX(10px)", "opacity:1;transform:translateX(0)", "cubic-bezier(.16,1,.3,1)")
        hi = vis(s, f"{p}rh{k}", T, 4.9 + k * 0.45, 4.9 + (k + 1) * 0.45 - 0.15, 0.15)
        r.append(f'<g class="{c}"><path d="M258 {y - 9} H502" stroke="#1c1c1c"/>'
                 f'<circle cx="262" cy="{y + 3.5}" r="1.4" fill="#4a4a4a"/>'
                 + s.text(270, y + 6, title, "R", size, "#bdbdbd")
                 + f'<g class="{hi}"><rect x="258" y="{y - 8.5}" width="244" height="24" fill="#fff" fill-opacity=".05"/>'
                 f'<rect x="258" y="{y - 8.5}" width="1.4" height="24" fill="#fff"/>'
                 + s.text(270, y + 6, title, "R", size, INK)
                 + s.text(500, y + 6, "→", "R", 8, INK, anchor="end") + "</g></g>")
    g.append(f'<g class="{scene(1)}">{"".join(r)}</g>')

    # 3. maquete 3D da cidade
    m = [azv_city(s, p, T, 8.0, 11.7)]
    m.append(s.text(18, 58, "MAQUETE 3D  ·  A CIDADE INTEIRA", "M", 6.2, "#bdbdbd", 1.4))
    m.append(s.text(18, 238, "SÃO JOSÉ DOS CAMPOS E LITORAL  ·  RELEVO REAL", "M", 5.8, "#5a5a5a", 1.3))
    m.append(s.text(502, 238, "≈ 320 MIL CASAS  ·  THREE.JS", "M", 5.8, "#5a5a5a", 1.3, anchor="end"))
    g.append(f'<g class="{scene(2)}">{"".join(m)}</g>')

    # 4. painel e SEO: o resultado na busca, o que o Google recebe e o painel próprio
    q = []
    q.append('<rect x="18" y="52" width="232" height="58" rx="6" fill="#0f0f0f" stroke="#1e1e1e"/>'
             '<circle cx="31" cy="64" r="4.5" fill="#1e1e1e" stroke="#333"/>')
    q.append(s.text(41, 66.4, "azvlancamentos.com.br", "R", 6.4, "#8a8a8a"))
    title = "Imóveis na planta em São José dos Campos | AZV Lançamentos"
    size = 9
    while text_width(title, "R", size) > 214:
        size -= 0.2
    q.append(s.text(27, 83, title, "R", size, "#e6e6e6"))
    q.append('<rect x="27" y="91" width="200" height="3" rx="1.5" fill="#262626"/><rect x="27" y="99" width="150" height="3" rx="1.5" fill="#262626"/>')
    rows = [("SITEMAP", "92 páginas e as fotos"), ("HREFLANG", "pt-BR e en"), ("JSON-LD", "RealEstateAgent · FAQPage"),
            ("INDEXNOW", "a cada publicação"), ("LCP NO CELULAR", "0,8 s"), ("CLS", "0")]
    for k, (lab, val) in enumerate(rows):
        y = 128 + k * 16
        c = vis(s, f"{p}sq{k}", T, 12.25 + k * 0.18, 15.7, 0.3, up, on, "cubic-bezier(.16,1,.3,1)")
        q.append(f'<g class="{c}"><path d="M18 {y + 5} H250" stroke="#191919"/>'
                 + s.text(18, y, lab, "M", 5.6, "#6a6a6a", 1.2)
                 + s.text(238, y, val, "R", 7, "#e6e6e6", anchor="end")
                 + f'<path d="M242 {y - 3} l2 2 l4 -4.5" fill="none" stroke="#fff" stroke-width="1"/></g>')
    q.append(s.text(270, 62, "PAINEL PRÓPRIO  ·  SEM COOKIES DE TERCEIROS", "M", 5.6, "#8a8a8a", 1.2))
    q.append(f'<circle class="fb {p}pp" cx="498" cy="60" r="2.2" fill="#fff"/>')
    s.css.append(keyframes(f"{p}pp", [("0%,100%", "opacity:.3"), ("50%", "opacity:1")]) + f".{p}pp{{animation:{p}pp 1.6s ease-in-out infinite}}")
    for k in range(4):
        q.append(f'<path d="M270 {80 + k * 20} H502" stroke="#161616"/>')
    pts = [(270, 122), (299, 110), (328, 124), (357, 106), (386, 118), (415, 102), (444, 116), (473, 104), (502, 112)]
    d = "M" + " L".join(f"{x} {y}" for x, y in pts)
    ln = anim(s, f"{p}ln", T, [((0, 12.3), "stroke-dashoffset:300"), ((14.2, T), "stroke-dashoffset:0")], "cubic-bezier(.65,0,.35,1)")
    area = d + " L502 140 L270 140 Z"
    s.defs.append(f'<linearGradient id="{p}ar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".10"/>'
                  f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    q.append(f'<g class="{vis(s, f"{p}af", T, 13.2, 15.7, 0.6)}"><path d="{area}" fill="url(#{p}ar)"/></g>'
             f'<path class="{ln}" d="{d}" fill="none" stroke="#fff" stroke-width="1.2" stroke-dasharray="300"/>')
    for row, (label, items, y, t0) in enumerate([("ORIGEM DAS VISITAS", ["GOOGLE", "BING", "IA", "WHATSAPP", "DIRETO"], 156, 12.4),
                                                ("O QUE O PAINEL MOSTRA", ["JORNADAS", "SEÇÕES VISTAS", "CONTATOS", "REVISTA"], 192, 13.4)]):
        q.append(s.text(270, y, label, "M", 5.6, "#5a5a5a", 1.2))
        cx = 270
        for k, it in enumerate(items):
            cw = text_width(it, "M", 5.2, 1) - 1 + 14
            q.append(f'<rect x="{cx:.1f}" y="{y + 6}" width="{cw:.1f}" height="14" rx="7" fill="none" stroke="#2a2a2a"/>'
                     + s.text(cx + 7, y + 15.4, it, "M", 5.2, "#8a8a8a", 1))
            c = vis(s, f"{p}pc{row}{k}", T, t0 + k * 0.35, 15.7, 0.25)
            q.append(f'<g class="{c}"><rect x="{cx:.1f}" y="{y + 6}" width="{cw:.1f}" height="14" rx="7" fill="#fff"/>'
                     + s.text(cx + 7, y + 15.4, it, "M", 5.2, "#0a0a0a", 1) + "</g>")
            cx += cw + 5
        assert cx < 508, (label, cx)
    q.append(s.text(270, 236, "SEARCH CONSOLE  ·  PAGESPEED  ·  QR CODE", "M", 5.2, "#4a4a4a", 1.1))
    g.append(f'<g class="{scene(3)}">{"".join(q)}</g>')

    g.append("</g></g>")
    return "".join(g)


def load_icons():
    import json
    return json.load(open(os.path.join(ROOT, "scripts", "stack-icons.json"), encoding="utf-8"))["icones"]


def stack_chips(name, title, groups, W=1012, label_w=0):
    """Stack em chips pequenos e discretos, com a logo de cada tecnologia (simple-icons, CC0) quando existe.

    groups: [(rótulo ou None, [(nome, slug do ícone ou None), ...]), ...]
    """
    icons = load_icons()
    CH, GAP, ROWGAP, GROUPGAP = 28, 8, 8, 14
    FS = 12.5
    items, y = [], 0
    for label, techs in groups:
        x = label_w
        if label:
            items.append(("label", label, y))
        for tech, icon in techs:
            has = bool(icon) and icon in icons
            w = text_width(tech, "R", FS) + (12 + 14 + 7 if has else 12 + 4 + 8) + 12
            if x + w > W and x > label_w:
                x = label_w
                y += CH + ROWGAP
            items.append(("chip", tech, icon if has else None, x, y, w))
            x += w + GAP
        y += CH + GROUPGAP
    H = int(y - GROUPGAP + 2)
    s = Svg(W, H, title + ": " + ", ".join(t for _, ts in groups for t, _ in ts), panel=False)
    s.css += [
        keyframes("cin", [("0%", "opacity:0;transform:translateY(6px)"), ("100%", "opacity:1;transform:translateY(0)")]),
        ".ci{animation:cin .7s cubic-bezier(.16,1,.3,1) both}",
    ]
    n = 0
    for it in items:
        if it[0] == "label":
            _, label, yy = it
            s.add(s.text(0, yy + 18, label, "M", 10, MUTED, 2.4))
            continue
        _, tech, icon, x, yy, w = it
        parts = [f'<rect x="{x + .5:.1f}" y="{yy + .5}" width="{w - 1:.1f}" height="{CH - 1}" rx="{(CH - 1) / 2}" fill="#0b0b0b" stroke="#242424"/>']
        if icon:
            parts.append(f'<g transform="translate({x + 12:.1f} {yy + (CH - 14) / 2}) scale({14 / 24:.4f})">'
                         f'<path d="{icons[icon]}" fill="#fff" fill-opacity=".88"/></g>')
            tx = x + 12 + 14 + 7
        else:
            parts.append(f'<circle cx="{x + 14:.1f}" cy="{yy + CH / 2}" r="2.2" fill="#6a6a6a"/>')
            tx = x + 12 + 4 + 8
        parts.append(s.text(tx, yy + CH / 2 + FS * 0.35, tech, "R", FS, "#d4d4d4"))
        s.add(f'<g class="ci" style="animation-delay:{0.025 * n:.3f}s">{"".join(parts)}</g>')
        n += 1
    s.save(name)


def stack_geral():
    stack_chips("stack-geral.svg", "Stack", [
        ("FRONTEND", [("TypeScript", "typescript"), ("JavaScript", "javascript"), ("React", "react"),
                      ("Next.js", "nextdotjs"), ("TanStack", "tanstack"), ("Tailwind CSS", "tailwindcss")]),
        ("3D E MOVIMENTO", [("Three.js", "threedotjs"), ("WebGL", "webgl"), ("GSAP", "gsap"),
                            ("Framer Motion", "framer"), ("ECharts", "apacheecharts"), ("HTML e CSS", "html5")]),
        ("BACKEND E DADOS", [("Node.js", "nodedotjs"), ("NestJS", "nestjs"), ("Python", "python"),
                             ("FastAPI", "fastapi"), ("Supabase", "supabase"), ("PostgreSQL", "postgresql")]),
        ("IA APLICADA", [("Claude", "claude"), ("OpenAI", None), ("Gemini", "googlegemini"),
                         ("LangChain", "langchain"), ("MCP", "modelcontextprotocol"), ("RAG e agentes", None)]),
        ("AUTOMAÇÃO", [("n8n", "n8n"), ("discord.py", "discord"), ("Extensões Chrome", "googlechrome"),
                       ("C# e WPF", "dotnet"), ("PowerShell", None)]),
        ("INFRA E QUALIDADE", [("Vercel", "vercel"), ("Docker", "docker"), ("GitHub Actions", "githubactions"),
                               ("Playwright", None), ("Vitest", "vitest"), ("Pytest", "pytest")]),
    ], label_w=196)


# ---------------------------------------------------------------- também no ar


def art_upaiva(s, ox, oy, p="u"):
    """Planeta de partículas com órbita e o terminal do Ctrl K."""
    g = [f'<g transform="translate({ox} {oy})">']
    cx, cy, R = 214, 92, 52
    dots = []
    N = 260
    for i in range(N):
        yv = 1 - (i / (N - 1)) * 2
        rr = math.sqrt(max(0.0, 1 - yv * yv))
        th = math.pi * (3 - math.sqrt(5)) * i
        xv, zv = math.cos(th) * rr, math.sin(th) * rr
        if zv < -0.15:
            continue
        lx = (xv * -0.5 + yv * -0.6 + zv * 0.62)
        op = 0.18 + 0.75 * max(0.0, lx)
        dots.append(f'<circle cx="{cx + xv * R:.1f}" cy="{cy + yv * R:.1f}" r="{0.7 + 0.6 * max(zv, 0):.2f}" fill="#fff" fill-opacity="{op:.2f}"/>')
    s.css.append(keyframes(f"{p}sp", [("0%", "transform:rotate(0deg)"), ("100%", "transform:rotate(360deg)")])
                 + f".{p}sp{{transform-box:fill-box;transform-origin:center;animation:{p}sp 60s linear infinite}}")
    g.append(f'<circle cx="{cx}" cy="{cy}" r="{R + 30}" fill="url(#{p}gl)"/>')
    s.defs.append(f'<radialGradient id="{p}gl"><stop offset="0" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>')
    g.append(f'<g class="{p}sp">{"".join(dots)}</g>')
    orbit = f"M{cx - 84} {cy + 6} A84 20 -14 1 0 {cx + 84} {cy - 6} A84 20 -14 1 0 {cx - 84} {cy + 6}"
    g.append(f'<path d="{orbit}" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width=".8" stroke-dasharray="1.5 3"/>')
    g.append(f'<circle r="3" fill="#fff"><animateMotion dur="7s" repeatCount="indefinite" path="{orbit}"/></circle>')
    g.append(s.text(18, 44, "PORTFÓLIO / 2026", "M", 7, "#6a6a6a", 1.8))
    g.append(s.text(18, 70, "Código,", "D", 20, INK, -0.4))
    g.append(s.text(18, 92, "produto.", "D", 20, INK, -0.4))
    cmd = "guias --ia"
    g.append('<rect x="18" y="122" width="120" height="24" rx="6" fill="#0f0f0f" stroke="#262626"/>')
    g.append(s.text(27, 137.6, "Ctrl K", "M", 7, "#6a6a6a", 1))
    tx = 27 + text_width("Ctrl K", "M", 7, 1) + 8
    T = 6.0
    xs = tx
    for k, ch in enumerate(cmd):
        c = vis(s, f"{p}ty{k}", T, 0.4 + k * 0.12, 5.2, 0.05)
        g.append(f'<g class="{c}">{s.text(xs, 137.6, ch, "R", 8.5, "#e6e6e6")}</g>')
        xs += text_width(ch, "R", 8.5)
    s.css.append(keyframes(f"{p}cu", [("0%,49%", "opacity:1"), ("50%,100%", "opacity:0")]) + f".{p}cu{{animation:{p}cu 1s steps(1) infinite}}")
    g.append(f'<rect class="{p}cu" x="{xs + 1:.1f}" y="130" width="4.5" height="9" fill="#fff"/>')
    g.append("</g>")
    return "".join(g)


def art_humanreply(s, ox, oy, p="h"):
    """A mensagem do cliente chega, a resposta crua é reescrita no tom da empresa."""
    T = 9.0
    g = [f'<g transform="translate({ox} {oy})">']
    msg = "Quero cancelar. O atendimento foi péssimo."
    w = text_width(msg, "R", 8.6) + 22
    c0 = vis(s, f"{p}m0", T, 0.2, 8.6, 0.35, "opacity:0;transform:translateY(6px)", "opacity:1;transform:translateY(0)")
    g.append(f'<g class="{c0}"><rect x="18" y="30" width="{w:.1f}" height="24" rx="12" fill="none" stroke="#3a3a3a"/>'
             + s.text(29, 45.4, msg, "R", 8.6, "#9a9a9a") + "</g>")
    # rascunho cru, riscado
    draft = "Ok. Vou ver isso."
    dw = text_width(draft, "R", 8.6) + 22
    x0 = 310 - dw
    c1 = vis(s, f"{p}d0", T, 1.3, 3.6, 0.3)
    strike = anim(s, f"{p}sk", T, [((0, 2.3), "transform:scaleX(0)"), ((2.8, T), "transform:scaleX(1)")], "cubic-bezier(.65,0,.35,1)",
                  "transform-box:fill-box;transform-origin:left center;")
    g.append(f'<g class="{c1}"><rect x="{x0:.1f}" y="66" width="{dw:.1f}" height="24" rx="12" fill="#151515"/>'
             + s.text(x0 + 11, 81.4, draft, "R", 8.6, "#8a8a8a")
             + f'<rect class="{strike}" x="{x0 + 10:.1f}" y="78" width="{dw - 20:.1f}" height="1" fill="#bdbdbd"/></g>')
    # reescrita no tom da empresa
    lines = ["Sinto muito pela experiência.", "Já estou resolvendo isso para você."]
    lw = max(text_width(l, "R", 8.6) for l in lines) + 22
    x1 = 310 - lw
    c2 = vis(s, f"{p}r0", T, 3.7, 8.6, 0.4, "opacity:0;transform:translateY(6px)", "opacity:1;transform:translateY(0)", "cubic-bezier(.16,1,.3,1)")
    g.append(f'<g class="{c2}"><rect x="{x1:.1f}" y="64" width="{lw:.1f}" height="38" rx="12" fill="#fff"/>'
             + s.text(x1 + 11, 79.4, lines[0], "R", 8.6, "#0a0a0a") + s.text(x1 + 11, 92.4, lines[1], "R", 8.6, "#0a0a0a") + "</g>")
    c3 = vis(s, f"{p}tg", T, 4.3, 8.6, 0.4)
    g.append(f'<g class="{c3}">' + s.text(310, 120, "TOM: EMPÁTICO  ·  CONTEXTO: RETENÇÃO", "M", 6.4, "#8a8a8a", 1.4, anchor="end") + "</g>")
    # digitando
    dots = []
    for k in range(3):
        c = anim(s, f"{p}dt{k}", T, [((0, 0.9 + k * 0.1), "opacity:.2"), (1.05 + k * 0.1, "opacity:1"), ((1.2 + k * 0.1, T), "opacity:.2")])
        dots.append(f'<circle class="{c}" cx="{282 + k * 7}" cy="78" r="2" fill="#bdbdbd"/>')
    g.append(f'<g class="{vis(s, f"{p}tp", T, 0.7, 1.3, 0.15)}"><rect x="272" y="66" width="38" height="24" rx="12" fill="#151515"/>{"".join(dots)}</g>')
    g.append(f'<g class="{vis(s, f"{p}tp2", T, 3.0, 3.7, 0.15)}"><rect x="272" y="66" width="38" height="24" rx="12" fill="#151515"/>'
             + "".join(d.replace(f"{p}dt", f"{p}dt") for d in dots) + "</g>")
    g.append(s.text(18, 168, "REESCRITO NO TOM DA EMPRESA", "M", 6.4, "#4a4a4a", 1.4))
    g.append("</g>")
    return "".join(g)


def art_studiojm(s, ox, oy, p="j"):
    """A planta de um projeto se desenhando, com cotas, ambientes e a assinatura do estúdio."""
    T = 8.0
    g = [f'<g transform="translate({ox + 4} {oy + 6})">']
    walls = [
        "M40 30 H260 V140 H40 Z",
        "M140 30 V96", "M140 112 V140", "M200 30 V70", "M200 86 V140", "M40 92 H112", "M200 96 H260",
    ]
    for k, d in enumerate(walls):
        c = anim(s, f"{p}w{k}", T, [((0, 0.2 + k * 0.25), "stroke-dashoffset:700"), ((1.6 + k * 0.25, 7.4), "stroke-dashoffset:0"),
                                    ((7.9, T), "stroke-dashoffset:700")], "cubic-bezier(.65,0,.35,1)")
        g.append(f'<path class="{c}" d="{d}" fill="none" stroke="#e6e6e6" stroke-width="{2.2 if k == 0 else 1.4}" stroke-dasharray="700"/>')
    # portas
    for k, (x, y, r, a0) in enumerate([(140, 96, 16, 0), (200, 70, 16, 1)]):
        c = vis(s, f"{p}dr{k}", T, 2.4 + k * 0.2, 7.4, 0.4)
        arc = f"M{x} {y} A{r} {r} 0 0 1 {x + r} {y + r}" if a0 == 0 else f"M{x} {y} A{r} {r} 0 0 0 {x - r} {y + r}"
        g.append(f'<path class="{c}" d="{arc}" fill="none" stroke="#6a6a6a" stroke-width=".8" stroke-dasharray="2 2"/>')
    rooms = [(90, 66, "ESTAR"), (90, 120, "COZINHA"), (170, 56, "SUÍTE"), (230, 56, "BANHO"), (230, 122, "VARANDA"), (170, 122, "HALL")]
    for k, (x, y, t) in enumerate(rooms):
        c = vis(s, f"{p}rm{k}", T, 2.8 + k * 0.15, 7.4, 0.35)
        g.append(f'<g class="{c}">' + s.text(x, y, t, "M", 6, "#8a8a8a", 1.4, anchor="middle") + "</g>")
    c = vis(s, f"{p}dm", T, 3.6, 7.4, 0.4)
    g.append(f'<g class="{c}"><path d="M40 158 H260 M40 154 V162 M260 154 V162" stroke="#6a6a6a" stroke-width=".8"/>'
             + s.text(150, 172, "21,00 m", "M", 6.6, "#8a8a8a", 1.4, anchor="middle") + "</g>")
    g.append(s.text(306, 166, "JM", "D", 18, INK, 1, anchor="end"))
    g.append(s.text(306, 177, "ARQUITETURA", "M", 5.2, "#5a5a5a", 1.3, anchor="end"))
    g.append("</g>")
    return "".join(g)


def also_live():
    """Também no ar: três cards com arte animada, nome, uma linha e a stack, e as extensões publicadas."""
    W = 1012
    gap = 16
    cw = (W - 2 * gap) / 3
    ART_H = 186
    H = 362
    cards = [
        ("upaiva.dev", "PORTFÓLIO", "NO AR", "Meu portfólio, com partículas em canvas, nove guias públicos sobre IA e um terminal no Ctrl K.",
         ["HTML", "CSS", "JavaScript", "GSAP"], art_upaiva),
        ("HumanReply AI", "IA PARA ATENDIMENTO", "EM VALIDAÇÃO",
         "IA para atendimento B2B que reescreve respostas no tom da empresa e guarda o contexto de cada conversa.",
         ["TanStack Start", "TypeScript", "LLMs"], art_humanreply),
        ("Studio JM", "ARQUITETURA", "NO AR",
         "Plataforma para estúdio de arquitetura, com portfólio, briefing com referências e painel administrativo.",
         ["HTML", "Tailwind", "Supabase"], art_studiojm),
    ]
    s = Svg(W, H + 58, "Também no ar: upaiva.dev, HumanReply AI e Studio JM, e extensões na Chrome Web Store", panel=False)
    s.css += [
        keyframes("cin", [("0%", "opacity:0;transform:translateY(10px)"), ("100%", "opacity:1;transform:translateY(0)")]),
        ".ci{animation:cin .9s cubic-bezier(.16,1,.3,1) both}",
        keyframes("pulse", [("0%", "transform:scale(1);opacity:.8"), ("100%", "transform:scale(3);opacity:0")]),
        ".pl{animation:pulse 2s cubic-bezier(.2,.6,.3,1) infinite}",
    ]
    for i, (title, cat, status, desc, tags, art) in enumerate(cards):
        x = i * (cw + gap)
        p = "abc"[i]
        s.defs.append(f'<clipPath id="ca{p}"><rect x="{x + 1:.1f}" y="1" width="{cw - 2:.1f}" height="{ART_H}" rx="15"/></clipPath>')
        body = [f'<rect x="{x + .5:.1f}" y=".5" width="{cw - 1:.1f}" height="{H - 1}" rx="16" fill="#060606" stroke="#1f1f1f"/>',
                f'<g clip-path="url(#ca{p})"><rect x="{x:.1f}" y="0" width="{cw:.1f}" height="{ART_H}" fill="#0a0a0a"/>'
                f'{art(s, x, 0, "t" + p)}</g>',
                f'<path d="M{x:.1f} {ART_H + .5} H{x + cw:.1f}" stroke="#1c1c1c"/>']
        sw = text_width(status, "M", 7, 1.6) - 1.6
        px = x + cw - 18 - sw - 22
        body.append(f'<rect x="{px:.1f}" y="14" width="{sw + 22:.1f}" height="18" rx="9" fill="#0a0a0a" stroke="#2a2a2a"/>'
                    f'<circle class="fb pl" cx="{px + 10:.1f}" cy="23" r="2.2" fill="#fff"/><circle cx="{px + 10:.1f}" cy="23" r="2.2" fill="#fff"/>'
                    + s.text(px + 17, 25.6, status, "M", 7, "#cfcfcf", 1.6))
        ty = ART_H + 30
        body.append(s.text(x + 20, ty, cat, "M", 8, DIM, 2))
        body.append(s.text(x + 20, ty + 32, title, "D", 26, INK, -0.5))
        for k, line in enumerate(wrap(desc, "R", 12.5, cw - 40)[:3]):
            body.append(s.text(x + 20, ty + 58 + k * 18, line, "R", 12.5, "#9a9a9a"))
        tx = x + 20
        for t in tags:
            tw = text_width(t, "M", 7.4, 1) - 1 + 18
            body.append(f'<rect x="{tx:.1f}" y="{H - 40}" width="{tw:.1f}" height="20" rx="10" fill="none" stroke="#2a2a2a"/>'
                        + s.text(tx + 9, H - 27, t, "M", 7.4, "#9a9a9a", 1))
            tx += tw + 6
        s.add(f'<g class="ci" style="animation-delay:{0.12 * i:.2f}s">{"".join(body)}</g>')
    # extensões publicadas
    y = H + 22
    lab = "EXTENSÕES NA CHROME WEB STORE"
    s.add(s.text(0, y + 14, lab, "M", 8.5, MUTED, 2.2))
    x = text_width(lab, "M", 8.5, 2.2) + 20
    icons = load_icons()
    for t in ["Não Seguidores", "InstaGrowth IA", "Calc Impostos BR"]:
        w = text_width(t, "R", 12) + 12 + 14 + 7 + 14
        s.add(f'<g class="ci" style="animation-delay:.5s"><rect x="{x + .5:.1f}" y="{y + .5}" width="{w - 1:.1f}" height="27" rx="13.5" fill="#0b0b0b" stroke="#242424"/>'
              f'<g transform="translate({x + 12:.1f} {y + 7}) scale({14 / 24:.4f})"><path d="{icons["googlechrome"]}" fill="#fff" fill-opacity=".85"/></g>'
              + s.text(x + 33, y + 18.2, t, "R", 12, "#d4d4d4") + "</g>")
        x += w + 8
    s.save("also-live.svg")


def showcase(name, idx, title, category, status, numbers, art):
    """Vitrine visual de um projeto: a arte animada em destaque e os números embaixo. O texto fica no README."""
    W, H = 1280, 660
    s = Svg(W, H, f"{title} — {category.title()}")
    s.css += [
        keyframes("pulse", [("0%", "transform:scale(1);opacity:.8"), ("100%", "transform:scale(3);opacity:0")]),
        ".pl{animation:pulse 2s cubic-bezier(.2,.6,.3,1) infinite}",
        keyframes("up", [("0%", "opacity:0;transform:translateY(18px)"), ("100%", "opacity:1;transform:translateY(0)")]),
        ".u4{animation:up 1s cubic-bezier(.16,1,.3,1) .6s both}.u5{animation:up 1.2s cubic-bezier(.16,1,.3,1) .2s both}",
        keyframes("draw", [("0%", "transform:scaleX(0)"), ("100%", "transform:scaleX(1)")]),
        ".dr{animation:draw 1.6s cubic-bezier(.65,0,.35,1) .1s both}",
    ]
    s.defs.append('<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#fff" stop-opacity=".07"/>'
                  '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>')
    s.add('<ellipse cx="640" cy="330" rx="560" ry="250" fill="url(#glow)"/>')
    head = f"{idx}   {title.upper()}"
    s.add(s.text(64, 84, head, "M", 11.5, "#d9d9d9", 3),
          s.text(64 + text_width(head, "M", 11.5, 3) + 18, 84, f"·   {category}", "M", 11.5, DIM, 3))
    sw = text_width(status, "M", 10, 2.4) - 2.4
    pw = sw + 42
    px = W - 64 - pw
    s.add(f'<rect x="{px:.1f}" y="62.5" width="{pw:.1f}" height="29" rx="14.5" fill="none" stroke="#2e2e2e"/>',
          f'<circle class="fb pl" cx="{px + 17:.1f}" cy="77" r="3.2" fill="#fff"/><circle cx="{px + 17:.1f}" cy="77" r="3.2" fill="#fff"/>',
          s.text(px + 29, 80.6, status, "M", 10, "#cfcfcf", 2.4))
    s.add(f'<rect class="fl dr" x="64" y="112" width="1152" height="1" fill="{LINE}"/>')
    s.add(f'<g class="u5"><g transform="translate(250 142) scale(1.5)">{art(s, 0, 0)}</g></g>')
    s.add(f'<rect class="fl dr" x="64" y="548" width="1152" height="1" fill="{LINE}"/>')
    nums = []
    for i, (big, label) in enumerate(numbers):
        x = 64 + i * 292
        nums.append(s.text(x, 604, big, "T", 38, INK, -1))
        nums.append(s.text(x + 2, 628, label, "M", 9.5, DIM, 2.2))
        assert text_width(label, "M", 9.5, 2.2) < 270, label
    s.add(f'<g class="u4">{"".join(nums)}</g>')
    s.save(name)


def recent():
    showcase("feature-azv.svg", "01", "AZV Lançamentos", "PLATAFORMA IMOBILIÁRIA", "NO AR",
             [("17", "EMPREENDIMENTOS"), ("92", "PÁGINAS EM PORTUGUÊS E INGLÊS"),
              ("17", "MATÉRIAS NA REVISTA"), ("5", "MAQUETES 3D EM THREE.JS")], art_azv)
    stack_chips("stack-azv.svg", "Stack da AZV Lançamentos", [(None, [
        ("Next.js 16", "nextdotjs"), ("React 19", "react"), ("TypeScript", "typescript"), ("GSAP", "gsap"), ("Lenis", None),
        ("Three.js", "threedotjs"), ("WebGL", "webgl"), ("Supabase", "supabase"), ("ECharts", "apacheecharts"),
        ("Python", "python"), ("Sentinel-2", None), ("OpenStreetMap", "openstreetmap"), ("Search Console", "googlesearchconsole"),
        ("IndexNow", None), ("Vercel", "vercel")])])
    showcase("feature-choque.svg", "02", "CHOQUE BGR", "SISTEMA DE GESTÃO", "NO AR",
             [("1.036", "TESTES AUTOMATIZADOS"), ("24", "QUESTÕES NA PROVA"),
              ("5", "PERFIS DE ACESSO (RBAC)"), ("0", "COMANDOS DE TEXTO")], art_choque)
    stack_chips("stack-choque.svg", "Stack do CHOQUE BGR", [(None, [
        ("discord.py 2.7", "discord"), ("Python 3.12", "python"), ("FastAPI", "fastapi"), ("Uvicorn", None),
        ("SQLite em WAL", "sqlite"), ("Next.js 16", "nextdotjs"), ("React 19", "react"), ("Auth.js", None),
        ("Tailwind 4", "tailwindcss"), ("Zod", "zod"), ("Pytest", "pytest"), ("Vitest", "vitest"), ("Playwright", None), ("Ruff", "ruff")])])
    showcase("feature-wintoolkit.svg", "03", "win-toolkit", "WINDOWS  ·  DESKTOP", "V1.5  ·  EM TESTES",
             [("106 KB", "UM .EXE, SEM RUNTIME EXTRA"), ("102", "ITENS NO CATÁLOGO"),
              ("170+", "AÇÕES EM 4 NÍVEIS"), ("4×", "INSTALAÇÕES EM PARALELO")], art_wintoolkit)
    stack_chips("stack-wintoolkit.svg", "Stack do win-toolkit", [(None, [
        ("WPF e XAML", "dotnet"), ("C# 5", None), (".NET Framework 4.8", None), ("PowerShell 5.1", None),
        ("winget", None), ("npm", "npm"), ("uv", "uv"), ("Windows Update Agent", None),
        ("Inter e Cascadia", None), ("DrawingContext", None)])])
    showcase("feature-instagram.svg", "04", "Instagram Fluxo", "EXTENSÃO CHROME  ·  IA", "V3.1.3  ·  USO LOCAL",
             [("3", "REFERÊNCIAS CONFIGURÁVEIS"), ("4", "PROVEDORES DE IA"),
              ("0", "SERVIDORES PRÓPRIOS"), ("MV3", "MANIFEST DO CHROME")], art_instagram)
    stack_chips("stack-instagram.svg", "Stack do Instagram Fluxo", [(None, [
        ("Chrome MV3", "googlechrome"), ("JavaScript", "javascript"), ("HTML e CSS", "html5"), ("chrome.storage", None),
        ("OpenAI", None), ("Claude", "claude"), ("Gemini", "googlegemini"), ("OpenRouter", "openrouter"),
        ("AES-GCM e PBKDF2", None), ("Python", "python"), ("SQLite", "sqlite"), ("PowerShell", None)])])


def site_card(path, title, art):
    """Mesma arte, recortada para os cards do upaiva.dev (1040 x 500, viewBox 60 80 520 250)."""
    s = Svg(520, 250, title, panel=False)
    s.add(art(s, 60, 80))
    svg = s.render().replace('width="520" height="250" viewBox="0 0 520 250"', 'width="1040" height="500" viewBox="60 80 520 250"', 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{os.path.basename(path)}: {os.path.getsize(path) / 1024:.1f} KB")


# ---------------------------------------------------------------- fontes para o painel automático


def dashboard_fonts():
    os.makedirs(FONT_OUT, exist_ok=True)
    chars = "".join(chr(c) for c in range(32, 127)) + "".join(chr(c) for c in range(160, 256)) + "•·—–↗"
    for key, name in (("T", "inter-display-thin"), ("M", "inter-medium"), ("R", "inter-regular")):
        data = woff2(key, chars)
        with open(os.path.join(FONT_OUT, f"{name}.woff2"), "wb") as f:
            f.write(data)
        print(f"fonts/{name}.woff2: {len(data) / 1024:.1f} KB")


if __name__ == "__main__":
    hero()
    recent()
    stack_geral()
    also_live()
    dashboard_fonts()
