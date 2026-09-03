"""Black-on-white convert flowchart. GUBERNATIO is the entry gate."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

W, H = 11.0, 18.5
fig, ax = plt.subplots(figsize=(W, H), dpi=170)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
ax.add_patch(Rectangle((1.05, 1.05), 97.9, 97.9, fill=False, linewidth=2.4, edgecolor="black"))

BLACK = "black"
WHITE = "white"


def wrap(text, width):
    out = []
    for raw in text.split("\n"):
        words = raw.split()
        if not words:
            out.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            if len(cur) + 1 + len(w) <= width:
                cur += " " + w
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return "\n".join(out)


def box(cx, cy, w, h, text, *, fs=7.8, tw=28):
    x, y = cx - w / 2, cy - h / 2
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.16,rounding_size=0.65",
            linewidth=1.7, edgecolor=BLACK, facecolor=WHITE,
        )
    )
    ax.text(
        cx, cy, wrap(text, tw), ha="center", va="center",
        fontsize=fs, color=BLACK, fontname="DejaVu Sans", linespacing=1.25,
    )
    return dict(cx=cx, cy=cy, w=w, h=h)


def diamond(cx, cy, w, h, text):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, linewidth=1.7, edgecolor=BLACK, facecolor=WHITE))
    ax.text(
        cx, cy, wrap(text, 22), ha="center", va="center",
        fontsize=7.1, color=BLACK, fontname="DejaVu Sans", linespacing=1.18,
    )
    return dict(cx=cx, cy=cy, w=w, h=h)


def vline(x, y1, y2):
    ax.plot([x, x], [y1, y2], color=BLACK, lw=1.35, solid_capstyle="butt")


def hline(x1, x2, y):
    ax.plot([x1, x2], [y, y], color=BLACK, lw=1.35, solid_capstyle="butt")


def down_arrow(x, y):
    ax.annotate(
        "", xy=(x, y), xytext=(x, y + 0.7),
        arrowprops=dict(arrowstyle="-|>", color=BLACK, lw=1.35, mutation_scale=11),
    )


def connect_down(a, b):
    y1 = a["cy"] - a["h"] / 2
    y2 = b["cy"] + b["h"] / 2
    vline(a["cx"], y1, y2 + 0.12)
    down_arrow(a["cx"], y2)


def elbow_down(from_x, from_y, to_cx, top_y):
    hline(from_x, to_cx, from_y)
    vline(to_cx, from_y, top_y + 0.12)
    down_arrow(to_cx, top_y)


ax.text(
    50, 97.15, "Satyagraha Law Group  ·  PDF to Markdown",
    ha="center", va="center", fontsize=11.6, color=BLACK,
    fontname="DejaVu Sans", fontweight="bold",
)
ax.text(
    50, 95.15, "GUBERNATIO is the entry gate  ·  registry is secondary",
    ha="center", va="center", fontsize=8.3, color=BLACK, fontname="DejaVu Sans",
)

raw = box(50, 90.7, 44, 4.6, "RAW: whole source PDF\n0_01_RAW_PDF", fs=8.0, tw=34)
hsh = box(50, 84.0, 44, 4.6, "Hash SHA-256\n(filename is not identity)", fs=8.0, tw=34)
gub = diamond(50, 74.6, 42, 8.8, "Already in GUBERNATIO\nas DONE?")

dups = box(18, 63.4, 30, 7.4, "Update registry (secondary)\nMOVE whole file to\nDUPLICATES / date", fs=7.1, tw=24)
lease = diamond(74, 63.4, 36, 8.4, "Same Mistral key\nalready RUNNING?")

halt = box(42, 52.2, 28, 5.4, "HALT. Do not convert.\nKey lease is held.", fs=7.2, tw=22)
ready = box(80, 52.2, 30, 5.6, "Mistral: take key lease\nMOVE to READY / date / Stem", fs=7.0, tw=24)

insp = diamond(80, 41.6, 32, 8.0, "Pages over 100\nor size over 100 MB?")

one = box(52, 31.0, 26, 5.4, "Convert this one PDF\n(never over the cap)", fs=7.0, tw=22)
split = box(86, 31.0, 22, 5.6, "Write parts into\nStem / parts /", fs=7.0, tw=18)

conv = box(86, 22.8, 22, 5.2, "Convert each part.\nNever convert original.", fs=6.8, tw=18)
merge = box(86, 15.2, 22, 5.4, "Merge ONE markdown\nDelete part PDFs", fs=6.8, tw=18)
md = box(52, 15.2, 26, 5.4, "ONE markdown in\nCLEAN_MARKDOWN", fs=7.0, tw=20)

proc = box(50, 6.2, 58, 6.2, "MOVE original to PROCESSED / date / Stem\nUpdate GUBERNATIO (primary) and registry (secondary)\nRelease Mistral key lease", fs=7.2, tw=50)

connect_down(raw, hsh)
connect_down(hsh, gub)

elbow_down(gub["cx"] - gub["w"] / 2, gub["cy"], dups["cx"], dups["cy"] + dups["h"] / 2)
ax.text(27.8, 74.6, "yes", fontsize=7.1, color=BLACK, fontstyle="italic", fontname="DejaVu Sans")

elbow_down(gub["cx"] + gub["w"] / 2, gub["cy"], lease["cx"], lease["cy"] + lease["h"] / 2)
ax.text(66.2, 74.6, "no", fontsize=7.1, color=BLACK, fontstyle="italic", fontname="DejaVu Sans")

elbow_down(lease["cx"] - lease["w"] / 2, lease["cy"], halt["cx"], halt["cy"] + halt["h"] / 2)
ax.text(54.8, 63.4, "yes", fontsize=7.1, color=BLACK, fontstyle="italic", fontname="DejaVu Sans")

elbow_down(lease["cx"] + lease["w"] / 2, lease["cy"], ready["cx"], ready["cy"] + ready["h"] / 2)
ax.text(93.4, 63.4, "no", fontsize=7.1, color=BLACK, fontstyle="italic", fontname="DejaVu Sans")

connect_down(ready, insp)

elbow_down(insp["cx"] - insp["w"] / 2, insp["cy"], one["cx"], one["cy"] + one["h"] / 2)
ax.text(61.6, 41.6, "no", fontsize=7.1, color=BLACK, fontstyle="italic", fontname="DejaVu Sans")

elbow_down(insp["cx"] + insp["w"] / 2, insp["cy"], split["cx"], split["cy"] + split["h"] / 2)
ax.text(95.0, 41.6, "yes", fontsize=7.1, color=BLACK, fontstyle="italic", fontname="DejaVu Sans")

connect_down(split, conv)
connect_down(conv, merge)
connect_down(one, md)

top_proc = proc["cy"] + proc["h"] / 2
vline(md["cx"], md["cy"] - md["h"] / 2, top_proc)
vline(merge["cx"], merge["cy"] - merge["h"] / 2, top_proc)
hline(md["cx"], merge["cx"], top_proc)
down_arrow(proc["cx"], top_proc)

ax.text(
    50, 2.15,
    "GUBERNATIO is master governance. Registry is identity only. Never store the raw API key.",
    ha="center", va="center", fontsize=6.6, color=BLACK, fontname="DejaVu Sans",
)

out = Path("/workspace/docs_src/Convert-Pipeline-Flowchart-v1-03-09-2026-06-48-52.png")
fig.savefig(out, facecolor="white", edgecolor="white", bbox_inches="tight", pad_inches=0.2)
plt.close()
print("wrote", out, out.stat().st_size)
