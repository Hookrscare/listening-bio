# Deploy — Listening.bio static site (Bono Host)

This folder (`web-static/`) builds to **fully static files** (HTML/CSS/JS +
demo assets). No server runtime is required; it runs on Bono Host shared hosting.

## Build

```bash
cd web-static
npm install
npm run build          # outputs ./dist
npm run test           # 13 vitest tests (exports, capability tiers, demo data, render)
npm run lint           # eslint (typescript-eslint)
```

Set the contact-form API base at build time (the FastAPI backend on the VPS):

```bash
VITE_API_BASE=https://api.listening.bio npm run build
```

If omitted, the form defaults to `https://api.listening.bio` and degrades to a
mailto fallback when the server is unreachable.

## Upload to Bono Host (cPanel)

1. In cPanel → **File Manager**, open `public_html` (or a subfolder if serving
   from a subdomain/path).
2. Upload the **contents** of `web-static/dist/` (not the folder itself):
   `index.html`, `assets/`, `demo/`.
3. Or via FTP/SFTP to the same docroot.
4. Because `base: "./"` is set, relative paths work from any docroot or
   subfolder.

### SPA note
This is a single page (no client routes), so no rewrite rules are needed.

## Cache headers (recommended)
In cPanel → **Optimize Website / .htaccess**, add long-cache for hashed assets:

```apache
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType text/css "access plus 1 week"
  ExpiresByType application/javascript "access plus 1 week"
  ExpiresByType image/svg+xml "access plus 1 month"
  ExpiresByType audio/mpeg "access plus 1 month"
</IfModule>
```

## Backend / contact form (separate deploy)
The form POSTs to `${VITE_API_BASE}/contact-enquiries` (FastAPI on the Hostinger
VPS). The repo's `backend/` must be deployed there with a new `POST
/contact-enquiries` route and **CORS allowing `https://listening.bio`** (current
FastAPI CORS only allows localhost — update before production). Until that exists,
the form shows a recoverable error with a mailto fallback.

## Demo assets (licensing)
- `demo/xc364638-american-robin.mp3` — Xeno-canto **XC364638** (American Robin),
  recordist Ted Floyd, **CC BY-NC-SA 4.0**.
- `demo/xc364638-spectrogram.svg` — generated representative spectrogram of that
  clip.
- All detections are flagged `demonstrationOnly`. Keep the attribution visible on
  the Evidence page.

## Verification checklist before going live
- `npm run build` succeeds; `dist/` is static and self-contained.
- `npm run test` green.
- Lighthouse: LCP < 2.5s, INP < 200ms, CLS < 0.1.
- `three`/`@react-three/fiber` is in the `webgl` lazy chunk (not the initial JS).
- Viewports 320 / 768 / 1280 / 1920 render correctly.
- Reduced-motion / quiet mode shows the 2D fallback (no WebGL canvas).
- Contact form submit reaches the VPS and CORS is configured.

## Domains / DNS
- `listening.bio` and `www.listening.bio` → Bono Host docroot (A record / CNAME
  per Bono Host's instructions).
- `api.listening.bio` → Hostinger VPS (separate A record), proxied by Nginx.
