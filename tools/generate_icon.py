"""Generate the Netwatch application icon.

Run this once to produce `netwatch.ico` in the project root.
If you ever want a different icon, tweak this script and re-run it.
"""

from pathlib import Path
from PIL import Image, ImageDraw

# Output path (project root)
OUTPUT = Path(__file__).resolve().parent.parent / "netwatch.ico"

# We'll draw at 256x256 (Windows' preferred icon size), then save.
SIZE = 256
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# ---- 1. Black circular frame ----
d.ellipse((0, 0, SIZE - 1, SIZE - 1), fill="black")

# ---- 2. Blue globe inside the frame ----
FRAME_PAD = 14
gx0, gy0 = FRAME_PAD, FRAME_PAD
gx1, gy1 = SIZE - FRAME_PAD, SIZE - FRAME_PAD
d.ellipse((gx0, gy0, gx1, gy1), fill="#1e6fa8")   # Ocean blue

# ---- 3. Latitude / longitude lines (faint) ----
LINE_COLOR = "#12507a"
line_width = 2

# Equator
d.line((gx0 + 8, SIZE // 2, gx1 - 8, SIZE // 2), fill=LINE_COLOR, width=line_width)
# Horizontal tropic lines
d.line((gx0 + 20, SIZE // 2 - 30, gx1 - 20, SIZE // 2 - 30), fill=LINE_COLOR, width=1)
d.line((gx0 + 20, SIZE // 2 + 30, gx1 - 20, SIZE // 2 + 30), fill=LINE_COLOR, width=1)
# Vertical meridian
d.line((SIZE // 2, gy0 + 8, SIZE // 2, gy1 - 8), fill=LINE_COLOR, width=line_width)

# ---- 4. Green eye in the center ----
# Eye shape (an almond / football) using an ellipse that's wider than tall
eye_w, eye_h = 130, 70
ex0 = (SIZE - eye_w) // 2
ey0 = (SIZE - eye_h) // 2
ex1 = ex0 + eye_w
ey1 = ey0 + eye_h

# The eye "white" (we use a very pale green for a sci-fi feel)
d.ellipse((ex0, ey0, ex1, ey1), fill="#e6f5e0")

# Green iris (circle)
iris_r = 30
icx, icy = SIZE // 2, SIZE // 2
d.ellipse(
    (icx - iris_r, icy - iris_r, icx + iris_r, icy + iris_r),
    fill="#1a7f37",
)

# Black pupil
pupil_r = 13
d.ellipse(
    (icx - pupil_r, icy - pupil_r, icx + pupil_r, icy + pupil_r),
    fill="black",
)

# White highlight (to give it life)
d.ellipse((icx + 4, icy - 12, icx + 12, icy - 4), fill="white")

# ---- 5. Save as ICO with multiple sizes ----
# Windows likes multi-resolution icons; PIL can generate them from one big image.
img.save(
    OUTPUT,
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)

print(f"Icon saved to: {OUTPUT}")