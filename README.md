# The Body Explained

Blog en inglés (Astro) sobre bienestar y "cómo funciona el cuerpo", con publicación diaria automática.

## Estructura
- `src/content/articles/` — un archivo `.md` por artículo.
- `data/articles-registry.xlsx` — registro de todas las publicaciones (se regenera en cada publicación).
- `data/topic-backlog.md` — cola de temas para el agente.
- `AGENT.md` — instrucciones y reglas de calidad del agente diario.
- `scripts/site_tools.py` — control de calidad (`check`) y generador del registro (`registry`).

## Comandos
```bash
npm install
npm run dev        # vista local en http://localhost:4321
npm run build      # genera /dist
pip install -r requirements.txt
python3 scripts/site_tools.py check-all
python3 scripts/site_tools.py registry
```

## Despliegue
Netlify lee `netlify.toml` (build: `npm run build`, publish: `dist`).
Cuando tengas dominio propio: añade la variable de entorno `SITE_URL=https://tudominio.com` en Netlify
y actualiza la línea `Sitemap:` de `public/robots.txt`.

## Antes de pedir AdSense
- Cambia `contactEmail` en `src/site.config.ts` por un correo real.
- Pega el script de AdSense donde dice `ADSENSE` en `src/layouts/Base.astro`.
