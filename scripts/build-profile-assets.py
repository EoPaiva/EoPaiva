"""Gera os SVGs animados do README de perfil (preto e branco).

Uso:  python3 scripts/build-profile-assets.py
Requisitos: fonttools + brotli (pip install fonttools brotli) e a família Inter
instalada no sistema (Inter e Inter Display). As fontes entram no próprio SVG,
recortadas só com os caracteres usados, então o visual é o mesmo em qualquer
máquina e o GitHub não precisa carregar nada de fora.
"""

import base64
import io
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


def arrow(x, y, size, stroke, width=1.6, cls=""):
    """Seta diagonal ↗ desenhada em path (mais nítida que o glifo)."""
    s = size
    c = f' class="{cls}"' if cls else ""
    return (
        f'<g{c}><path d="M{x} {y + s} L{x + s} {y} M{x + s * 0.28} {y} H{x + s} V{y + s * 0.72}" '
        f'fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="square"/></g>'
    )


def phase(total, start, dur, hold_until=None, fade=0.5):
    """Percentuais de um elemento que entra em `start`, fica até `hold_until` e some."""
    end = hold_until if hold_until is not None else total - fade
    pct = lambda t: f"{max(0.0, min(100.0, t / total * 100)):.2f}%"
    return pct(start), pct(start + dur), pct(end), pct(min(total, end + fade))


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


# ---------------------------------------------------------------- botões


def button(name, label, dark):
    size, spacing = 13, 3.2
    tw = text_width(label, "M", size, spacing) - spacing
    W, H = int(tw + 48 + 44), 60
    s = Svg(W, H, label, panel=False)
    fg, bg = ("#fff", "#000") if dark else ("#000", "#fff")
    s.defs.append(f'<clipPath id="ac"><rect x="{W - 48}" y="18" width="24" height="24"/></clipPath>')
    s.css += [
        keyframes(
            "go",
            [
                ("0%,58%", "transform:translate(0,0)"),
                ("78%", "transform:translate(16px,-16px)"),
                ("78.01%", "transform:translate(-16px,16px)"),
                ("100%", "transform:translate(0,0)"),
            ],
        ),
        ".go{animation:go 3s cubic-bezier(.7,0,.3,1) infinite}",
    ]
    s.add(
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="{(H - 2) / 2}" fill="{bg}" stroke="#000" stroke-width="1.5"/>',
        s.text(26, 35, label, "M", size, fg, spacing),
        f'<g clip-path="url(#ac)">{arrow(W - 42, 24, 11, fg, 1.7, "go")}</g>',
    )
    s.save(name)


# ---------------------------------------------------------------- cabeçalho de seção


def section(name, index, title, tag):
    W, H = 1280, 116
    s = Svg(W, H, f"{index} — {title}")
    tx = 128
    t_end = tx + text_width(title, "D", 38, -0.8)
    tag_w = text_width(tag, "M", 11.5, 3.4)
    a, b = t_end + 36, 1232 - tag_w - 28
    s.css += [
        keyframes("draw", [("0%", "transform:scaleX(0)"), ("100%", "transform:scaleX(1)")]),
        ".dr{animation:draw 1.8s cubic-bezier(.65,0,.35,1) .2s both}",
        keyframes("trip", [("0%", f"transform:translateX(0);opacity:0"), ("10%", "opacity:1"), ("90%", "opacity:1"),
                           ("100%", f"transform:translateX({b - a:.0f}px);opacity:0")]),
        ".tp{animation:trip 4.2s cubic-bezier(.6,0,.4,1) 2s infinite both}",
    ]
    s.add(
        s.text(48, 68, index, "M", 12.5, DIM, 3),
        s.text(tx, 72, title, "D", 38, INK, -0.8),
        f'<rect class="fl dr" x="{a:.1f}" y="60" width="{b - a:.1f}" height="1" fill="#2a2a2a"/>',
        f'<circle class="tp" cx="{a:.1f}" cy="60.5" r="3" fill="#fff"/>',
        s.text(1232, 65, tag, "M", 11.5, DIM, 3.4, anchor="end"),
    )
    s.save(name)


# ---------------------------------------------------------------- cartões de projeto

CW, CH = 640, 470


def card_frame(s, index, category, status, live, title, desc, stack):
    s.css += [
        keyframes("pulse", [("0%", "transform:scale(1);opacity:.8"), ("100%", "transform:scale(3);opacity:0")]),
        ".pl{animation:pulse 2s cubic-bezier(.2,.6,.3,1) infinite}",
    ]
    s.add(s.text(40, 58, f"{index}   {category}", "M", 11, DIM, 2.8))
    sw = text_width(status, "M", 10, 2.4) - 2.4
    pw = sw + 42
    px = CW - 40 - pw
    dot = f'<circle cx="{px + 17:.1f}" cy="50" r="3.2" fill="{"#fff" if live else "#6a6a6a"}"/>'
    if live:
        dot = f'<circle class="fb pl" cx="{px + 17:.1f}" cy="50" r="3.2" fill="#fff"/>' + dot
    s.add(
        f'<rect x="{px:.1f}" y="36.5" width="{pw:.1f}" height="27" rx="13.5" fill="none" stroke="#2e2e2e"/>',
        dot,
        s.text(px + 29, 53.6, status, "M", 10, "#cfcfcf" if live else MUTED, 2.4),
    )
    s.add(
        s.text(40, 360, title, "D", 42, INK, -1.1),
        s.text(40, 392, desc, "R", 15, MUTED, 0),
        f'<rect x="40" y="414" width="{CW - 80}" height="1" fill="{LINE}"/>',
        arrow(CW - 54, 432, 13, "#ffffff", 1.5),
    )
    # stack em pílulas
    px = 40
    for item in stack.split(" · "):
        w = text_width(item, "M", 9, 1.8) - 1.8 + 26
        s.add(f'<rect x="{px:.1f}" y="429.5" width="{w:.1f}" height="25" rx="12.5" fill="#0c0c0c" stroke="#2a2a2a"/>',
              s.text(px + w / 2, 445.6, item, "M", 9, "#bdbdbd", 1.8, anchor="middle"))
        px += w + 8
    assert px < CW - 80, stack
    assert text_width(desc, "R", 15) < CW - 80, desc
    assert text_width(title, "D", 42, -1.1) < CW - 80, title


def card_azv():
    s = Svg(CW, CH, "AZV Lançamentos — vitrine de lançamentos imobiliários")
    card_frame(s, "01", "IMOBILIÁRIO", "NO AR", True, "AZV Lançamentos",
               "Vitrine de lançamentos imobiliários da AZV Imóveis.", "NEXT.JS · GSAP · LENIS · TYPESCRIPT")
    # parede de cobogó que gira como brise e revela o prédio atrás
    cols, rows, cw, ch, gap = 10, 4, 40, 40, 8
    gw = cols * cw + (cols - 1) * gap
    x0, y0 = (CW - gw) / 2, 108
    s.defs.append(
        '<linearGradient id="face" x1="0" x2="1"><stop offset="0" stop-color="#e6e6e6"/>'
        '<stop offset=".5" stop-color="#8f8f8f"/><stop offset="1" stop-color="#262626"/></linearGradient>'
    )
    s.css += [
        keyframes("brise", [("0%,30%", "transform:scaleX(1)"), ("50%,72%", "transform:scaleX(.07)"), ("92%,100%", "transform:scaleX(1)")]),
        ".lv{animation:brise 5.4s cubic-bezier(.65,0,.35,1) infinite both}",
    ]
    # skyline por trás, que aparece quando as aletas fecham
    ground = y0 + rows * (ch + gap) - gap
    building = []
    for bx, top, bw in ((x0 + 18, 150, 118), (x0 + 160, 100, 132), (x0 + 318, 168, 118)):
        building.append(f'<rect x="{bx:.1f}" y="{top}" width="{bw}" height="{ground - top}" fill="#0a0a0a" stroke="#4a4a4a"/>')
        for y in range(top + 14, int(ground), 14):
            building.append(f'<path d="M{bx + 10:.1f} {y} H{bx + bw - 10:.1f}" stroke="#2a2a2a"/>')
    building.append(f'<path d="M{x0 - 10:.1f} {ground} H{x0 + gw + 10:.1f}" stroke="#5a5a5a"/>')
    s.add("".join(building))
    cells = []
    for r in range(rows):
        for c in range(cols):
            x, y = x0 + c * (cw + gap), y0 + r * (ch + gap)
            delay = (c + r) * 0.09
            cells.append(
                f'<rect class="fb lv" style="animation-delay:{delay:.2f}s" x="{x:.1f}" y="{y}" width="{cw}" '
                f'height="{ch}" rx="1.5" fill="url(#face)"/>'
            )
    s.add("".join(cells))
    s.save("card-azv.svg")


def card_upaiva():
    s = Svg(CW, CH, "upaiva.dev — portfólio com partículas, guias de IA e terminal Ctrl K")
    card_frame(s, "02", "IDENTIDADE DIGITAL", "NO AR", True, "upaiva.dev",
               "Portfólio com partículas, guias de IA e terminal Ctrl K.", "HTML · CSS · JAVASCRIPT · GSAP")
    x, y, w, h = 120, 92, 400, 212
    s.add(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#0b0b0b" stroke="#2a2a2a"/>',
        f'<path d="M{x} {y + 34} H{x + w}" stroke="#1f1f1f"/>',
        *[f'<circle cx="{x + 20 + i * 14}" cy="{y + 17}" r="3.5" fill="#2e2e2e"/>' for i in range(3)],
        f'<rect x="{x + w / 2 - 62}" y="{y + 8}" width="124" height="18" rx="9" fill="#141414"/>',
        s.text(x + w / 2, y + 21, "upaiva.dev", "R", 10.5, MUTED, 0.3, anchor="middle"),
    )
    tabs = ["TRABALHO", "GUIAS", "CTRL K"]
    total = 9.0
    tx = x + 28
    positions = []
    for t in tabs:
        positions.append((tx, text_width(t, "M", 10, 2.2) - 2.2))
        tx += positions[-1][1] + 26
    heads = ["Projetos reais, no ar", "Entenda a IA em 9 guias", "› abrir trabalho"]
    bars = [[300, 236, 270], [250, 300, 190], [280, 210, 320]]
    for i, t in enumerate(tabs):
        a, b = i / 3 * 100, (i + 1) / 3 * 100
        on = f"{a + 2:.1f}%,{b - 2:.1f}%"
        frames = [("0%,100%", "opacity:0")]
        frames = [(f"{max(a - 0.01, 0):.2f}%", "opacity:0"), (on, "opacity:1"), (f"{min(b, 100):.2f}%", "opacity:0")]
        if i == 0:
            frames = [("0%", "opacity:0"), (f"2%,{b - 2:.1f}%", "opacity:1"), (f"{b:.2f}%,100%", "opacity:0")]
        elif i == 2:
            frames = [(f"0%,{a:.2f}%", "opacity:0"), (f"{a + 2:.1f}%,98%", "opacity:1"), ("100%", "opacity:0")]
        else:
            frames = [(f"0%,{a:.2f}%", "opacity:0"), (on, "opacity:1"), (f"{b:.2f}%,100%", "opacity:0")]
        s.css.append(keyframes(f"m{i}", frames) + f".m{i}{{animation:m{i} {total}s ease infinite}}")
        px, pw = positions[i]
        s.add(
            s.text(px, y + 64, t, "M", 10, "#4a4a4a", 2.2),
            f'<g class="m{i}">{s.text(px, y + 64, t, "M", 10, "#fff", 2.2)}'
            f'<rect x="{px}" y="{y + 71}" width="{pw:.1f}" height="1.5" fill="#fff"/>'
            f'{s.text(x + 28, y + 112, heads[i], "D", 25, INK, -0.5)}'
            + "".join(f'<rect x="{x + 28}" y="{y + 130 + k * 14}" width="{bw}" height="6" rx="3" fill="#1f1f1f"/>' for k, bw in enumerate(bars[i]))
            + f'<rect x="{x + 28}" y="{y + 176}" width="92" height="22" rx="11" fill="#fff"/>'
            + s.text(x + 74, y + 191, "VER MAIS", "M", 8.5, "#000", 1.8, anchor="middle")
            + "</g>",
        )
    s.save("card-upaiva.svg")


def card_humanreply():
    s = Svg(CW, CH, "HumanReply AI — IA que reescreve conversas no tom certo")
    card_frame(s, "03", "INTELIGÊNCIA ARTIFICIAL", "EM VALIDAÇÃO", True, "HumanReply AI",
               "IA que transforma conversas em respostas no tom certo.", "TANSTACK START · TYPESCRIPT · LLMS · B2B")
    total = 8.0
    left = 104

    def anim(cls, start, dur=0.6):
        a, b, c, d = phase(total, start, dur, hold_until=total - 0.9, fade=0.5)
        s.css.append(
            keyframes(cls, [(f"0%,{a}", "opacity:0;transform:translateY(10px)"), (f"{b},{c}", "opacity:1;transform:translateY(0)"),
                            (f"{d},100%", "opacity:0;transform:translateY(0)")])
            + f".{cls}{{animation:{cls} {total}s cubic-bezier(.16,1,.3,1) infinite}}"
        )

    msg = "Quero cancelar. O atendimento foi péssimo."
    mw = text_width(msg, "R", 13) + 36
    anim("b1", 0.3)
    s.add(f'<g class="b1"><rect x="{left}" y="92" width="{mw:.1f}" height="40" rx="20" fill="none" stroke="#353535"/>'
          + s.text(left + 18, 116.5, msg, "R", 13, "#cfcfcf") + "</g>")

    # analisando tom + pontinhos digitando
    a, b, c, d = phase(total, 1.2, 0.4, hold_until=2.6, fade=0.3)
    s.css.append(keyframes("an", [(f"0%,{a}", "opacity:0"), (f"{b},{c}", "opacity:1"), (f"{d},100%", "opacity:0")])
                 + f".an{{animation:an {total}s ease infinite}}")
    s.css.append(keyframes("bob", [("0%,60%,100%", "transform:translateY(0);opacity:.35"), ("30%", "transform:translateY(-4px);opacity:1")])
                 + ".bob{animation:bob 1s ease-in-out infinite}")
    s.add('<g class="an">' + "".join(
        f'<circle class="bob" style="animation-delay:{i * 0.15}s" cx="{left + 14 + i * 11}" cy="160" r="3" fill="#fff"/>' for i in range(3))
        + s.text(left + 56, 164, "ANALISANDO TOM  ·  FRUSTRAÇÃO 82%", "M", 9.5, DIM, 2.2) + "</g>")

    r1, r2 = "Sinto muito pela experiência.", "Já estou resolvendo isso para você."
    rw = max(text_width(r1, "R", 13), text_width(r2, "R", 13)) + 40
    rx = CW - left - rw
    anim("b2", 2.8)
    s.add(f'<g class="b2"><rect x="{rx:.1f}" y="184" width="{rw:.1f}" height="62" rx="20" fill="#fff"/>'
          + s.text(rx + 20, 210, r1, "R", 13, "#000") + s.text(rx + 20, 229, r2, "R", 13, "#000") + "</g>")
    anim("b3", 3.6)
    chip = "TOM: EMPÁTICO   ·   CONTEXTO: RETENÇÃO"
    s.add(f'<g class="b3">' + s.text(CW - left, 272, chip, "M", 9.5, MUTED, 2.2, anchor="end") + "</g>")
    s.save("card-humanreply.svg")


def card_studiojm():
    s = Svg(CW, CH, "Studio JM — portfólio de arquitetura com painel de gestão")
    card_frame(s, "04", "ARQUITETURA · GESTÃO", "NO AR", True, "Studio JM",
               "Portfólio de arquitetura com briefing e painel admin.", "HTML · TAILWIND · JAVASCRIPT · SUPABASE")
    total = 9.0
    lines = [
        "M120 282 H520",  # chão
        "M196 282 V176 H404 V282",  # volume térreo
        "M252 176 V118 H478 V176 H404",  # balanço superior
        "M462 176 V282",  # pilar
        "M218 282 V200 H310 V282",  # pano de vidro
        "M264 200 V282",
        "M274 134 H458 V156 H274 Z",  # janela em fita
        "M338 282 V222 H368 V282",  # porta
        "M156 282 V262",  # árvore
        "M156 262 a18 18 0 1 1 0.01 0",
        "M196 300 H404 M196 295 V305 M404 295 V305",  # cota
    ]
    paths = []
    for i, d in enumerate(lines):
        start = 0.2 + i * 0.22
        a, b, c, e = phase(total, start, 1.3, hold_until=total - 1.0, fade=0.6)
        name = f"p{i}"
        s.css.append(keyframes(name, [(f"0%,{a}", "stroke-dashoffset:1;opacity:1"), (f"{b},{c}", "stroke-dashoffset:0;opacity:1"),
                                      (f"{e},100%", "stroke-dashoffset:0;opacity:0")])
                     + f".{name}{{animation:{name} {total}s cubic-bezier(.65,0,.35,1) infinite}}")
        color = "#5a5a5a" if i == len(lines) - 1 else "#fff"
        paths.append(f'<path class="{name}" pathLength="1" stroke-dasharray="1" d="{d}" fill="none" '
                     f'stroke="{color}" stroke-width="1.3" stroke-linejoin="round"/>')
    s.add("".join(paths))
    # vidro acende depois do traço
    a, b, c, e = phase(total, 3.4, 0.9, hold_until=total - 1.0, fade=0.6)
    s.css.append(keyframes("gl", [(f"0%,{a}", "opacity:0"), (f"{b},{c}", "opacity:1"), (f"{e},100%", "opacity:0")])
                 + f".gl{{animation:gl {total}s ease infinite}}")
    s.add('<g class="gl"><rect x="218" y="200" width="92" height="82" fill="#fff" fill-opacity=".07"/>'
          '<rect x="274" y="134" width="184" height="22" fill="#fff" fill-opacity=".12"/>'
          '<rect x="252" y="176" width="210" height="6" fill="#fff" fill-opacity=".05"/></g>')
    a, b, c, e = phase(total, 3.0, 0.6, hold_until=total - 1.0, fade=0.6)
    s.css.append(keyframes("lb", [(f"0%,{a}", "opacity:0"), (f"{b},{c}", "opacity:1"), (f"{e},100%", "opacity:0")])
                 + f".lb{{animation:lb {total}s ease infinite}}")
    s.add('<g class="lb">' + s.text(300, 318, "21,00 m", "M", 9, DIM, 2, anchor="middle")
          + s.text(486, 112, "JM", "M", 10, MUTED, 3) + "</g>")
    s.save("card-studiojm.svg")


# ---------------------------------------------------------------- stack em movimento


def stack():
    W, H = 1280, 232
    s = Svg(W, H, "Stack: TypeScript, React, Next.js, Node.js, Supabase, IA aplicada e automação")
    rows = [
        (["TypeScript", "React", "Next.js", "Node.js", "Supabase", "PostgreSQL", "Tailwind", "GSAP", "Framer Motion", "TanStack"], INK, 48, False),
        (["Claude", "OpenAI", "Gemini", "RAG", "MCP", "Vercel AI SDK", "LangChain", "n8n", "NestJS", "Prisma", "Python", "Docker", "Vercel"], "#6b6b6b", 48, True),
    ]
    s.defs.append(
        '<linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".12" stop-color="#fff"/><stop offset=".88" stop-color="#fff"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<mask id="me"><rect width="{W}" height="{H}" fill="url(#edge)"/></mask>'
    )
    out = ['<g mask="url(#me)">']
    sep = "   /   "
    for i, (items, color, size, reverse) in enumerate(rows):
        seq = sep.join(items) + sep
        width = text_width(seq, "D", size, -1.0)
        y = 98 + i * 76
        speed = width / 38
        frm, to = (f"-{width:.1f}px", "0px") if reverse else ("0px", f"-{width:.1f}px")
        s.css.append(keyframes(f"mq{i}", [("0%", f"transform:translateX({frm})"), ("100%", f"transform:translateX({to})")])
                     + f".mq{i}{{animation:mq{i} {speed:.1f}s linear infinite}}")
        parts = []
        for copy in range(3):
            x = 0 + copy * width
            spans = []
            for j, item in enumerate(items):
                spans.append(f'<tspan fill="{color}">{escape(item)}</tspan><tspan fill="#2a2a2a">{escape(sep)}</tspan>')
            s.used["D"].update(seq)
            parts.append(f'<text x="{x:.1f}" y="{y}" font-family="D,{FALLBACK}" font-size="{size}" letter-spacing="-1" '
                         f'xml:space="preserve">{"".join(spans)}</text>')
        out.append(f'<g class="mq{i}">{"".join(parts)}</g>')
    out.append("</g>")
    s.add("".join(out))
    s.save("stack.svg")


# ---------------------------------------------------------------- encerramento


def outro():
    W, H = 1280, 420
    s = Svg(W, H, "Vamos construir algo que marque.")
    s.defs.append(
        '<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    )
    s.css += [
        keyframes("sweep", [("0%,50%", "transform:translateX(-420px)"), ("100%", "transform:translateX(1300px)")]),
        ".sw{animation:sweep 6.5s cubic-bezier(.6,0,.3,1) infinite}",
        keyframes("blink", [("0%,49%", "opacity:1"), ("50%,100%", "opacity:0")]),
        ".cur{animation:blink 1.05s steps(1) infinite}",
        keyframes("spin", [("0%", "transform:rotate(0)"), ("100%", "transform:rotate(360deg)")]),
        ".rot{transform-origin:1096px 170px;animation:spin 40s linear infinite}",
    ]
    l1, l2 = "Vamos construir algo", "que marque."
    s.add(
        s.text(64, 92, "05   CONTATO", "M", 12.5, DIM, 3),
        s.text(60, 196, l1, "D", 76, INK, -2.4),
        s.text(60, 282, l2, "D", 76, "#4d4d4d", -2.4),
    )
    s.defs.append(f'<clipPath id="t2">{s.text(60, 282, l2, "D", 76, INK, -2.4)}</clipPath>')
    s.add('<g clip-path="url(#t2)"><rect class="sw" x="0" y="200" width="360" height="100" fill="url(#shine)"/></g>')
    # selo girando com texto em círculo
    ring = "CÓDIGO · PRODUTO · IA APLICADA · DESIGN · "
    s.defs.append('<path id="circ" d="M1096 170 m-78 0 a78 78 0 1 1 156 0 a78 78 0 1 1 -156 0"/>')
    s.used["M"].update(ring)
    s.add(
        f'<g class="rot"><text font-family="M,{FALLBACK}" font-size="11" letter-spacing="3.9" fill="{MUTED}">'
        f'<textPath href="#circ">{escape(ring)}</textPath></text></g>',
        '<circle cx="1096" cy="170" r="54" fill="none" stroke="#262626"/>',
        arrow(1084, 158, 24, "#fff", 1.6),
    )
    s.add(
        f'<rect x="64" y="338" width="1152" height="1" fill="{LINE}"/>',
        s.text(64, 378, "mPaiva", "D", 22, INK, -0.4),
        f'<rect class="cur" x="{64 + text_width("mPaiva", "D", 22, -0.4) + 3:.1f}" y="375" width="11" height="2" fill="#fff"/>',
        s.text(1216, 377, "© 2026  ·  FEITO À MÃO EM SVG", "M", 11, DIM, 3, anchor="end"),
    )
    s.save("outro.svg")


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
        spans, cur = [], None
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


def feature(name, idx, category, status, title, lead, desc, numbers, art, foot_l, foot_r):
    W, H = 1280, 640
    s = Svg(W, H, f"{title} — {lead}")
    s.css += [
        keyframes("pulse", [("0%", "transform:scale(1);opacity:.8"), ("100%", "transform:scale(3);opacity:0")]),
        ".pl{animation:pulse 2s cubic-bezier(.2,.6,.3,1) infinite}",
        keyframes("up", [("0%", "opacity:0;transform:translateY(18px)"), ("100%", "opacity:1;transform:translateY(0)")]),
        ".u1{animation:up 1s cubic-bezier(.16,1,.3,1) .1s both}.u2{animation:up 1s cubic-bezier(.16,1,.3,1) .25s both}"
        ".u3{animation:up 1s cubic-bezier(.16,1,.3,1) .4s both}.u4{animation:up 1s cubic-bezier(.16,1,.3,1) .6s both}"
        ".u5{animation:up 1.2s cubic-bezier(.16,1,.3,1) .3s both}",
        keyframes("draw", [("0%", "transform:scaleX(0)"), ("100%", "transform:scaleX(1)")]),
        ".dr{animation:draw 1.6s cubic-bezier(.65,0,.35,1) .1s both}",
        keyframes("sweep", [("0%,60%", "transform:translateX(-300px)"), ("100%", "transform:translateX(900px)")]),
        ".sw{animation:sweep 7s cubic-bezier(.6,0,.3,1) 1.2s infinite both}",
    ]
    s.add(s.text(64, 84, f"{idx}   {category}", "M", 11.5, DIM, 3))
    sw = text_width(status, "M", 10, 2.4) - 2.4
    pw = sw + 42
    px = W - 64 - pw
    s.add(f'<rect x="{px:.1f}" y="62.5" width="{pw:.1f}" height="29" rx="14.5" fill="none" stroke="#2e2e2e"/>',
          f'<circle class="fb pl" cx="{px + 17:.1f}" cy="77" r="3.2" fill="#fff"/><circle cx="{px + 17:.1f}" cy="77" r="3.2" fill="#fff"/>',
          s.text(px + 29, 80.6, status, "M", 10, "#cfcfcf", 2.4))
    s.add(f'<rect class="fl dr" x="64" y="112" width="1152" height="1" fill="{LINE}"/>')

    size = 72
    while text_width(title, "D", size, -2.2) > 500:
        size -= 2
    s.add(f'<g class="u1">{s.text(60, 200, title, "D", size, INK, -2.2)}</g>')
    s.defs.append(f'<clipPath id="tt">{s.text(60, 200, title, "D", size, INK, -2.2)}</clipPath>')
    s.defs.append('<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/>'
                  '<stop offset=".5" stop-color="#000" stop-opacity=".55"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>')
    s.add('<g clip-path="url(#tt)"><rect class="sw" x="0" y="120" width="240" height="100" fill="url(#shine)"/></g>')
    s.add(f'<g class="u2">{s.text(64, 240, lead, "D", 24, "#5a5a5a", -0.5)}</g>')
    body = []
    for i, line in enumerate(desc):
        assert text_width(line, "R", 15) < 500, line
        body.append(s.text(64, 290 + i * 25, line, "R", 15, MUTED))
    s.add(f'<g class="u3">{"".join(body)}</g>')
    nums = []
    for i, (big, label) in enumerate(numbers):
        x, y = 64 + (i % 2) * 250, 438 + (i // 2) * 76
        nums.append(f'<rect x="{x}" y="{y - 40}" width="1" height="52" fill="#262626"/>')
        nums.append(s.text(x + 16, y, big, "T", 40, INK, -1))
        nums.append(s.text(x + 18, y + 20, label, "M", 9.5, DIM, 2.2))
    s.add(f'<g class="u4">{"".join(nums)}</g>')
    s.add(f'<g class="u5"><g transform="translate(596 196) scale(1.19)">{art(s, 0, 0)}</g></g>')
    s.add(f'<rect class="fl dr" x="64" y="578" width="1152" height="1" fill="{LINE}"/>',
          s.text(64, 612, foot_l, "M", 10.5, MUTED, 2.6),
          s.text(1190, 612, foot_r, "M", 10.5, MUTED, 2.6, anchor="end"),
          arrow(1200, 600, 12, "#fff", 1.5))
    s.save(name)


GLYPHS = {
    "window": '<rect x="1" y="3" width="22" height="18" rx="3"/><path d="M1 8 H23"/><circle cx="4.5" cy="5.5" r=".6"/>',
    "code": '<path d="M8 6 L2 12 L8 18 M16 6 L22 12 L16 18 M14 4 L10 20"/>',
    "layers": '<path d="M12 3 L22 8 L12 13 L2 8 Z M2 12 L12 17 L22 12 M2 16 L12 21 L22 16"/>',
    "term": '<rect x="1" y="3" width="22" height="18" rx="3"/><path d="M5 9 L9 12 L5 15"/><path class="gb" d="M11 16 H17"/>',
    "box": '<path d="M12 2 L22 7 V17 L12 22 L2 17 V7 Z M2 7 L12 12 L22 7 M12 12 V22"/>',
    "chip": '<rect x="5" y="5" width="14" height="14" rx="2"/><path d="M9 1 V5 M15 1 V5 M9 19 V23 M15 19 V23 M1 9 H5 M1 15 H5 M19 9 H23 M19 15 H23"/>',
    "type": '<path d="M2 20 L8 4 L14 20 M4.3 14 H11.7"/><circle cx="19" cy="16.5" r="3.5"/><path d="M22.5 13 V20"/>',
    "planet": '<circle cx="12" cy="12" r="6"/><g class="gr"><ellipse cx="12" cy="12" rx="11" ry="3.6" transform="rotate(-18 12 12)"/></g>',
    "puzzle": '<path d="M4 7 H9 a3 3 0 1 1 6 0 H20 V12 a3 3 0 1 0 0 6 V21 H4 Z"/>',
    "db": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5 V19 a9 3 0 0 0 18 0 V5 M3 12 a9 3 0 0 0 18 0"/>',
    "spark": '<path class="gp" d="M12 2 C13 9 15 11 22 12 C15 13 13 15 12 22 C11 15 9 13 2 12 C9 11 11 9 12 2 Z"/>',
    "lock": '<rect x="4" y="10" width="16" height="12" rx="2"/><path d="M8 10 V7 a4 4 0 0 1 8 0 V10 M12 15 V17"/>',
    "log": '<path d="M7 6 H22 M7 12 H22 M7 18 H16"/><circle cx="3" cy="6" r="1"/><circle cx="3" cy="12" r="1"/><circle cx="3" cy="18" r="1"/>',
}


def stack_cards(name, title, items):
    """Cards da stack: camada, tecnologia e o porquê, com entrada em cascata e um brilho que atravessa."""
    W, cols, gap, th = 1280, 4, 16, 140
    tw = (W - gap * (cols - 1)) / cols
    rows = (len(items) + cols - 1) // cols
    H = rows * th + (rows - 1) * gap
    s = Svg(W, H, title, panel=False)
    s.css += [
        keyframes("cin", [("0%", "opacity:0;transform:translateY(14px)"), ("100%", "opacity:1;transform:translateY(0)")]),
        ".ci{animation:cin .9s cubic-bezier(.16,1,.3,1) both}",
        keyframes("top", [("0%", "transform:scaleX(0)"), ("100%", "transform:scaleX(1)")]),
        ".tl{animation:top 1.4s cubic-bezier(.65,0,.35,1) both}",
        keyframes("sh", [("0%,62%", "transform:translateX(-500px)"), ("100%", "transform:translateX(1800px)")]),
        ".sh{animation:sh 8s cubic-bezier(.6,0,.3,1) 1.6s infinite both}",
        keyframes("gb", [("0%,49%", "opacity:1"), ("50%,100%", "opacity:0")]), ".gb{animation:gb 1.05s steps(1) infinite}",
        keyframes("gr", [("0%", "transform:rotate(0)"), ("100%", "transform:rotate(360deg)")]),
        ".gr{transform-box:fill-box;transform-origin:center;animation:gr 9s linear infinite}",
        keyframes("gp", [("0%,100%", "transform:scale(.82);opacity:.6"), ("50%", "transform:scale(1);opacity:1")]),
        ".gp{transform-box:fill-box;transform-origin:center;animation:gp 2.6s ease-in-out infinite}",
    ]
    s.defs.append('<linearGradient id="tg" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                  '<linearGradient id="sg" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  '<stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    clip = []
    for i, (layer, tech, why, glyph) in enumerate(items):
        x, y = (i % cols) * (tw + gap), (i // cols) * (th + gap)
        clip.append(f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="{th}" rx="18"/>')
        size = 25
        while text_width(tech, "D", size, -0.5) > tw - 48:
            size -= 1
        assert text_width(why, "R", 12.5) < tw - 44, why
        d = 0.08 * i
        s.add(
            f'<g class="ci" style="animation-delay:{d:.2f}s">'
            f'<rect x="{x + .5:.1f}" y="{y + .5}" width="{tw - 1:.1f}" height="{th - 1}" rx="17.5" fill="{PANEL}" stroke="{LINE}"/>'
            f'<rect class="fl tl" style="animation-delay:{d + .2:.2f}s" x="{x + 24:.1f}" y="{y}" width="{tw - 48:.1f}" height="1" fill="url(#tg)"/>'
            + s.text(x + 24, y + 38, f"{i + 1:02d} · {layer}", "M", 9.5, DIM, 2.4)
            + f'<g transform="translate({x + tw - 46:.1f} {y + 20})" fill="none" stroke="#fff" stroke-opacity=".75" '
              f'stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[glyph]}</g>'
            + s.text(x + 24, y + 90, tech, "D", size, INK, -0.5)
            + s.text(x + 24, y + 116, why, "R", 12.5, MUTED)
            + "</g>"
        )
    s.defs.append(f'<clipPath id="cc">{"".join(clip)}</clipPath>')
    s.add(f'<g clip-path="url(#cc)"><rect class="sh" x="0" y="0" width="420" height="{H}" fill="url(#sg)" '
          f'transform="skewX(-18)"/></g>')
    s.save(name)


def recent():
    feature(
        "feature-wintoolkit.svg", "01", "WINDOWS  ·  DESKTOP", "V1.5  ·  EM TESTES", "win-toolkit",
        "Do Windows formatado ao PC pronto.",
        ["Programas, dependências, drivers, análise de segurança e",
         "otimização em um único app, com o comando real de cada etapa",
         "à vista. Retoma de onde parou, simula antes de aplicar e nunca",
         "desliga Defender, Firewall ou Windows Update."],
        [("106 KB", "UM .EXE, SEM RUNTIME EXTRA"), ("102", "ITENS NO CATÁLOGO"),
         ("170+", "AÇÕES EM 4 NÍVEIS"), ("4×", "INSTALAÇÕES EM PARALELO")],
        art_wintoolkit, "GITHUB.COM/EOPAIVA/WIN-TOOLKIT", "WPF  ·  C#  ·  POWERSHELL",
    )
    stack_cards("stack-wintoolkit.svg", "Stack do win-toolkit", [
        ("INTERFACE", "WPF · XAML", "Nativo, renderizado por hardware", "window"),
        ("LINGUAGEM", "C# 5", "Compila com o csc.exe do Windows", "code"),
        ("RUNTIME", ".NET Framework 4.8", "Já vem no Windows 11", "layers"),
        ("MOTOR", "PowerShell 5.1", "O shell garantido no PC novo", "term"),
        ("PACOTES", "winget · npm · uv", "Sempre a versão mais nova", "box"),
        ("DRIVERS", "Windows Update Agent", "Fonte oficial da Microsoft", "chip"),
        ("TIPOGRAFIA", "Inter · Cascadia", "A identidade do upaiva.dev", "type"),
        ("GRÁFICOS", "DrawingContext", "Planeta de partículas, sem libs", "planet"),
    ])
    feature(
        "feature-instagram.svg", "02", "EXTENSÃO CHROME  ·  IA", "V3.1.3  ·  USO LOCAL", "Instagram Fluxo",
        "Sua fila, perfil por perfil.",
        ["Segue perfis a partir de três referências e para de seguir em",
         "fila, um perfil por vez, com intervalos, pausas e conferência",
         "de cada resultado. Fila e histórico ficam no seu navegador,",
         "e o agente de IA é opcional, com a sua própria chave."],
        [("3", "REFERÊNCIAS CONFIGURÁVEIS"), ("4", "PROVEDORES DE IA"),
         ("0", "SERVIDORES PRÓPRIOS"), ("MV3", "MANIFEST DO CHROME")],
        art_instagram, "GITHUB.COM/EOPAIVA/INSTAGRAM-FLUXO", "JAVASCRIPT  ·  MV3  ·  PYTHON",
    )
    stack_cards("stack-instagram.svg", "Stack do Instagram Fluxo", [
        ("PLATAFORMA", "Chrome MV3", "Service worker e permissões sob demanda", "puzzle"),
        ("LINGUAGEM", "JavaScript", "Sem framework e sem build", "code"),
        ("INTERFACE", "HTML · CSS", "Painel, carrossel e cards", "window"),
        ("DADOS", "chrome.storage", "Fila, tentativas e histórico locais", "db"),
        ("IA OPCIONAL", "OpenAI · Claude · Gemini", "BYOK com fallback e OpenRouter", "spark"),
        ("COFRE", "AES-GCM · PBKDF2", "Chaves cifradas no navegador", "lock"),
        ("COLETOR", "Python · SQLite", "Native messaging e logs JSONL", "log"),
        ("INSTALAÇÃO", "PowerShell", "Registra o coletor no Windows", "term"),
    ])


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
    button("btn-projetos.svg", "EXPLORAR PROJETOS", dark=True)
    button("btn-contato.svg", "CONTATO", dark=False)
    button("btn-site.svg", "UPAIVA.DEV", dark=True)
    button("btn-linkedin.svg", "LINKEDIN", dark=False)
    button("btn-email.svg", "E-MAIL", dark=False)
    section("sec-recentes.svg", "01", "Lançamentos recentes", "NEW RELEASES")
    section("sec-projetos.svg", "02", "Projetos selecionados", "SELECTED WORK")
    section("sec-stack.svg", "03", "Stack & ferramentas", "TOOLKIT")
    section("sec-numeros.svg", "04", "Código em produção", "LIVE DATA")
    recent()
    card_azv()
    card_upaiva()
    card_humanreply()
    card_studiojm()
    stack()
    outro()
    dashboard_fonts()
