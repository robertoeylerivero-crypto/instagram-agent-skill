"""Extensão do render_reel.py: cenas "tela" = gravação de tela (rolagem) do site dentro de um celular."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_reel as R
_wrap = R.wrap
def _wrap2(draw, text, font, maxw):
    out = []
    for part in text.split("|"):
        out += _wrap(draw, part.strip(), font, maxw)
    return out
R.wrap = _wrap2
from PIL import Image, ImageDraw

SW, SH, BZ = 600, 1021, 16  # tela do celular e borda
PW, PH = SW + 2 * BZ, SH + 2 * BZ
CARVAO = (37, 37, 34)

def ease(p):
    return p * p * (3 - 2 * p)

def tela_bg(path):
    im = Image.open(path).convert("RGB")
    top = im.crop((0, 0, im.width, int(im.width * 1992 / 1170)))
    bg = R.cover(top, R.W // 4, R.H // 4).filter(R.ImageFilter.GaussianBlur(8)).resize((R.W, R.H), Image.LANCZOS)
    return Image.blend(bg, Image.new("RGB", (R.W, R.H), (20, 30, 25)), 0.55), im

def frame_tela(bg, src, c, t, dur):
    p = ease(min(1.0, t / dur))
    y = int(c["y0"] + (c["y1"] - c["y0"]) * p)
    vh = int(src.width * SH / SW)
    y = max(0, min(y, src.height - vh))
    scr = src.crop((0, y, src.width, y + vh)).resize((SW, SH), Image.LANCZOS)
    out = bg.copy().convert("RGBA")
    x0, y0 = (R.W - PW) // 2, (R.H - PH) // 2
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((x0 - 4, y0 - 4, x0 + PW + 4, y0 + PH + 4), 64, fill=(90, 90, 85, 255))
    d.rounded_rectangle((x0, y0, x0 + PW, y0 + PH), 60, fill=CARVAO + (255,))
    m = Image.new("L", (SW, SH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, SW, SH), 46, fill=255)
    out.paste(scr, (x0 + BZ, y0 + BZ), m)
    R.draw_text_block(out, c["titulo"], c.get("sub", ""), min(1.0, t / 0.35), PH)
    return out.convert("RGB")

def main(spec_path, out_path):
    spec = json.load(open(spec_path)); fdir = spec["fotos_dir"]; FPS = R.FPS
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{R.W}x{R.H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out_path], stdin=subprocess.PIPE)
    prev, XF = None, int(0.3 * FPS)
    for c in spec["cenas"]:
        dur = c.get("dur", 3.0); n = int(dur * FPS)
        if "tela" in c:
            bg, src = tela_bg(c["tela"]); f = lambda t: frame_tela(bg, src, c, t, dur)
        else:
            bg, fg = R.scene_layers(os.path.join(fdir, c["foto"])); f = lambda t: R.frame_scene(bg, fg, c["titulo"], c.get("sub", ""), t, dur)
        for i in range(n):
            fr = f(i / FPS)
            if prev is not None and i < XF:
                fr = Image.blend(prev, fr, (i + 1) / XF)
            proc.stdin.write(fr.tobytes()); last = fr
        prev = last
    cta = spec["cta"]; n = int(cta.get("dur", 3.5) * FPS)
    for i in range(n):
        fr = R.cta_frame(cta, i / FPS)
        if i < XF: fr = Image.blend(prev, fr, (i + 1) / XF)
        proc.stdin.write(fr.tobytes())
    proc.stdin.close(); proc.wait()
    c0 = spec["cenas"][0]; bg, fg = R.scene_layers(os.path.join(fdir, c0["foto"]))
    R.frame_scene(bg, fg, c0["titulo"], c0.get("sub", ""), 1.0, c0.get("dur", 3.0)).save(out_path.replace(".mp4", "-capa.jpg"), quality=90)
    print("ok", out_path, proc.returncode)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
