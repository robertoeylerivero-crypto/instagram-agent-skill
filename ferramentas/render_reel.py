"""Gera um Reel vertical 1080x1920 (MP4 H.264) a partir de fotos + textos.

Uso: python3 -I render_reel.py roteiro.json saida.mp4
roteiro.json = {"fotos_dir": "...", "cenas": [{"foto": "x.webp", "titulo": "...", "sub": "...", "dur": 3.0}, ...],
                "cta": {"titulo": "...", "sub": "...", "rodape": "..."}}
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
VERDE, AREIA, OFF, TERRA = (35, 72, 58), (233, 221, 200), (248, 245, 239), (129, 82, 59)
FRAUNCES = "/home/claude/fonts/fraunces.ttf"
INTER_B = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
INTER_R = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"


def fraunces(size, wght=600):
    f = ImageFont.truetype(FRAUNCES, size)
    try:
        f.set_variation_by_axes([min(144, max(9, size)), wght])
    except Exception:
        pass
    return f


def wrap(draw, text, font, maxw):
    if "|" in text:
        out = []
        for part in text.split("|"):
            out += wrap(draw, part.strip(), font, maxw)
        return out
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def cover(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def scene_layers(path):
    im = Image.open(path).convert("RGB")
    bg = cover(im, W // 4, H // 4).filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.LANCZOS)
    bg = Image.blend(bg, Image.new("RGB", (W, H), (20, 30, 25)), 0.45)
    # foto principal: largura total com margem, proporção original (sem esticar)
    fw = W - 96
    fh = int(im.height * fw / im.width)
    if fh > 1100:
        fh = 1100
    fg = cover(im, fw, fh)
    return bg, fg


def draw_text_block(base, titulo, sub, alpha, fh):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * alpha)
    ft, fs = fraunces(84, 600), ImageFont.truetype(INTER_R, 44)
    tl = wrap(d, titulo, ft, W - 160)
    y = (H - fh) // 2 - 70 - len(tl) * 100
    y = max(y, 230)  # fica abaixo da área de interface do Instagram
    for ln in tl:
        tw = d.textlength(ln, font=ft)
        d.text(((W - tw) / 2, y), ln, font=ft, fill=OFF + (a,))
        y += 100
    if sub:
        y2 = (H + fh) // 2 + 60
        for ln in wrap(d, sub, fs, W - 200):
            tw = d.textlength(ln, font=fs)
            pad = 22
            d.rounded_rectangle(((W - tw) / 2 - pad, y2 - 10, (W + tw) / 2 + pad, y2 + 62), 18, fill=AREIA + (int(a * 0.95),))
            d.text(((W - tw) / 2, y2), ln, font=fs, fill=VERDE + (a,))
            y2 += 84
    base.alpha_composite(layer)


def frame_scene(bg, fg, titulo, sub, t, dur):
    p = t / dur
    z = 1.0 + 0.07 * p
    fw, fh = fg.size
    zw, zh = int(fw * z), int(fh * z)
    big = fg.resize((zw, zh), Image.BICUBIC)
    crop = big.crop(((zw - fw) // 2, (zh - fh) // 2, (zw - fw) // 2 + fw, (zh - fh) // 2 + fh))
    out = bg.copy().convert("RGBA")
    mask = Image.new("L", (fw, fh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, fw, fh), 36, fill=255)
    out.paste(crop, ((W - fw) // 2, (H - fh) // 2), mask)
    alpha = min(1.0, t / 0.35)
    draw_text_block(out, titulo, sub, alpha, fh)
    return out.convert("RGB")


def cta_frame(cta, t):
    out = Image.new("RGBA", (W, H), VERDE + (255,))
    d = ImageDraw.Draw(out)
    a = int(255 * min(1.0, t / 0.4))
    ft, fs, fr = fraunces(96, 600), ImageFont.truetype(INTER_B, 52), ImageFont.truetype(INTER_R, 40)
    y = 700
    for ln in wrap(d, cta["titulo"], ft, W - 160):
        tw = d.textlength(ln, font=ft); d.text(((W - tw) / 2, y), ln, font=ft, fill=OFF + (a,)); y += 116
    y += 40
    for ln in wrap(d, cta["sub"], fs, W - 200):
        tw = d.textlength(ln, font=fs)
        d.rounded_rectangle(((W - tw) / 2 - 28, y - 14, (W + tw) / 2 + 28, y + 70), 22, fill=AREIA + (a,))
        d.text(((W - tw) / 2, y), ln, font=fs, fill=TERRA + (a,)); y += 100
    tw = d.textlength(cta["rodape"], font=fr)
    d.text(((W - tw) / 2, 1380), cta["rodape"], font=fr, fill=AREIA + (a,))
    return out.convert("RGB")


def main(spec_path, out_path):
    spec = json.load(open(spec_path))
    fdir = spec["fotos_dir"]
    frames = []  # lista de (gerador, n_frames)
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out_path], stdin=subprocess.PIPE)
    prev_last = None
    XF = int(0.3 * FPS)
    for c in spec["cenas"]:
        bg, fg = scene_layers(os.path.join(fdir, c["foto"]))
        n = int(c.get("dur", 3.0) * FPS)
        for i in range(n):
            fr = frame_scene(bg, fg, c["titulo"], c.get("sub", ""), i / FPS, c.get("dur", 3.0))
            if prev_last is not None and i < XF:
                fr = Image.blend(prev_last, fr, (i + 1) / XF)
            proc.stdin.write(fr.tobytes())
            last = fr
        prev_last = last
    cta = spec["cta"]; n = int(cta.get("dur", 3.5) * FPS)
    for i in range(n):
        fr = cta_frame(cta, i / FPS)
        if i < XF:
            fr = Image.blend(prev_last, fr, (i + 1) / XF)
        proc.stdin.write(fr.tobytes())
    proc.stdin.close(); proc.wait()
    # capa = primeiro quadro com texto completo da cena 1
    c0 = spec["cenas"][0]; bg, fg = scene_layers(os.path.join(fdir, c0["foto"]))
    frame_scene(bg, fg, c0["titulo"], c0.get("sub", ""), 1.0, c0.get("dur", 3.0)).save(out_path.replace(".mp4", "-capa.jpg"), quality=90)
    print("ok", out_path, proc.returncode)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
