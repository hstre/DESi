# DESi — Advertising site

A bold-but-accurate, single-page advertising site for DESi, in **5 languages**:
English · Deutsch · 中文 · Español · 日本語.

It is deliberately on-brand: punchy typography, real measured numbers, and an
explicit "we report the failures too" section. No forbidden hype terms
(`Breakthrough`, `Revolutionary`, `AGI`, …) — those are shown struck through,
because DESi blocks them at build time.

## Files

- `index.html` — the whole site. Self-contained: CSS + JS + all translations
  embedded, no external dependencies or network calls. The language switcher
  (top right) persists the choice in `localStorage` and falls back to the
  browser language, then English.

## Preview locally

```bash
# from the repo root
python -m http.server 8000 --directory website
# open http://localhost:8000
```

Or just open `website/index.html` directly in a browser.

## Publish via GitHub Pages

A workflow at `.github/workflows/pages.yml` deploys the `website/` folder to
GitHub Pages on every push that touches it. The `configure-pages` step uses
`enablement: true`, so Pages is **enabled automatically** on the first run —
no manual Settings step required.

Each push to `website/**` re-publishes the site. The live URL is shown in the
workflow run summary (and under Settings → Pages), typically
`https://hstre.github.io/DESi/`.

> If auto-enablement is ever blocked by org/account policy, enable it manually:
> Settings → Pages → Build and deployment → Source → **GitHub Actions**.

## Editing copy

All text lives in the `I18N` object inside `index.html`, keyed by language
(`en`, `de`, `zh`, `es`, `ja`). Each visible element references a key via
`data-i18n` (text) or `data-i18n-html` (allows the `<span class="hl">` accent).
To change a headline, edit the value for that key in **every** language block so
the five stay in sync.
