# Gerador de Reel (1080x1920 MP4)

1. Fonte: `curl -sS https://auremabooking.com.br/fonts/fraunces-latin.woff2 -o /home/claude/fonts/fraunces.woff2`,
   `pip install --break-system-packages -q fonttools brotli` e converta para `/home/claude/fonts/fraunces.ttf`
   (TTFont(woff2); flavor=None; save). Inter já existe em /usr/share/fonts/opentype/inter/.
2. Baixe as fotos para uma pasta e escreva um roteiro.json como `exemplo-roteiro.json`
   (6 cenas de ~2,8 s + chamada final = ~20 s; título curto, sub até ~35 caracteres).
3. `python3 -I render_reel.py roteiro.json reel.mp4` → gera `reel.mp4` e `reel-capa.jpg`.
4. Extraia 4-5 quadros com ffmpeg e OLHE antes de entregar.
