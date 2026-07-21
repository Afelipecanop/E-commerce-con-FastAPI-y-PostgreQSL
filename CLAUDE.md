# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Velonox — an e-commerce store. FastAPI backend (Railway) + PostgreSQL, vanilla HTML/CSS/JS frontend (Cloudflare Pages, `e-commerce-con-fastapi-y-postgreqsl.pages.dev`), no build step or framework on either side.

## Commands

Backend (run from `backend/`):
```
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```
- Create a migration: `alembic revision --autogenerate -m "descripcion"` (from `backend/`, engine must be reachable via `DATABASE_URL`).
- Apply migrations: `alembic upgrade head`.
- Production start command (see `backend/procfile`): `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT`.
- There is no test suite in this repo — do not assume `pytest` or similar is configured.

Frontend: static files under `frontend/`, no build/bundle step. Serve the directory with any static server (e.g. VS Code Live Server on port 5500, matched by the backend's CORS allow-list) and open the `.html` files directly.

## Architecture

### Backend (`backend/`)
Sync SQLAlchemy 2.x (`database.py`) — **do not** introduce async ORM calls without migrating the whole project consistently; this is a deliberate convention, not an oversight.

- `models/` — `User`, `Product`, `Cart`, `Order`, `StoreLayout`, `StoreSetting`, `ProductPage`.
- `routes/` — one router per domain: `auth`, `products`, `categories`, `cart`, `payments`, `layout`, `product_pages`, `metrics`, `settings`, `guest_checkout`. All mounted in `main.py`.
- `schemas/` — Pydantic request/response models per domain.
- `services/` — business logic: `auth.py` (JWT), `bold.py` (payment signatures), `dropi.py` (fulfillment), `email.py`, `settings.py` (TRM/currency).
- `middleware/auth.py` — `get_current_user` / `get_current_admin` dependencies (JWT via `python-jose`, hashing via `bcrypt`).
- `alembic/` — migrations; `versions/` holds one file per revision.

**Payments**: uses **Bold** (Colombian gateway, `services/bold.py`, integrity-signature + webhook HMAC verification) and **Dropi** (`services/dropi.py`, order fulfillment/dropshipping) — Stripe is no longer used (kept commented out in `requirements.txt` for history; ignore README/notes mentions of Stripe, they're stale).

**Currency**: store prices are USD internally; `services/settings.py` / the `/settings/trm` endpoint expose the current USD→COP exchange rate (TRM) so the frontend can render either currency.

**CMS-driven layout**: `models/layout.py` (`store_layout` table) + `routes/layout.py`. Pages are built from configurable "blocks" (`announcement_bar`, `hero_banner`, `content_hero`, `product_grid`, `text_section`, `testimonials`, `categories`, `image_banner`, `footer`, `custom_html`, ...) stored per `page_slug`, editable from `frontend/admin.html` and fetched by public pages via `GET /layout/?page=<slug>`. `routes/layout.py` also has an AI block-generation endpoint (Anthropic API, server-side key only).

**Security pattern to preserve** (see `docs/notes/proyecto.md`): never call external APIs (Bold, Dropi, Anthropic, TRM source) directly from the frontend — always proxy through the backend using the server's own `.env` keys. CORS uses explicit methods/headers, never `["*"]`. Internal errors (DB, payment gateway) are never surfaced verbatim to the client — return generic messages instead.

### Frontend (`frontend/`)
No bundler, no framework — plain `.html` files each with inline `<script>`/`<style>`, plus shared helpers in `frontend/js/`. All internal links and asset references (`href`/`src`) use absolute paths (leading `/`, e.g. `/js/api.js`, `/admin.html`) rather than relative ones — keep this convention when adding pages or scripts:
- `js/api.js` — `API_URL`, auth token helpers, `apiFetch()`, and the currency system: `VX_CURRENCY`/`VX_TRM` (from `localStorage` + `/settings/trm`), `vxPrice(usdAmount)`, `setCurrency()`, `getCurrency()`, `updateCurrencyToggle()`. `setCurrency()` dispatches a `currencyChanged` window event — any code rendering a price must listen for it (or re-render) to stay in sync.
- `js/page-blocks.js` — `initPageBlocks(slug)` / `renderPageBlock()`, the shared CMS-block renderer used by contacto/nosotros/politicas/terminos/categorias/catalogo/tienda. Re-creates `<script>` elements after `innerHTML` injection so inline scripts in `custom_html` blocks actually execute (`<script>` tags inserted via `innerHTML` are otherwise inert).
- `index.html` has its **own** inline block renderer (`renderLayoutBlock()` / `loadLayoutBlocks()`) instead of using `page-blocks.js` — historically a source of drift between the home page and every other content page; check both when touching CMS block rendering.

**Admin panel** (`admin.html`): single large file, tab-based SPA (`switchTab()`: Editor/Productos/Métricas/Categorías/Ajustes). The layout editor has a live preview `<iframe id="preview-frame">` driven by `EDITABLE_PAGES` (page key → backend slug + real frontend filename) and `renderPreview()`: for every editable page (including the home page) it fetches the real page file, injects the in-memory (possibly unsaved) block edits into its `#layout-container`, and loads the result via `iframe.srcdoc` — this keeps the preview byte-identical to production instead of a hand-maintained mock. The preview neutralizes the real page's hidden `#nav-admin` link (it would otherwise be visible, since the iframe shares the admin's login session, and could navigate the iframe into `admin.html` itself). Pages not in `EDITABLE_PAGES` (cart/login/product/checkout, etc.) are "preview-only" and load via real `iframe.src` navigation instead.

**`</script>` escaping gotcha**: several places build HTML strings containing literal `<script>...</script>` inside a JS template literal that itself lives inside another `<script>` block (e.g. `admin.html`'s preview generation). The literal byte sequence `</script>` (case-insensitive) closes the *enclosing* script tag as far as the HTML parser is concerned, regardless of JS string context — always escape as `<\/script>` in these cases (existing precedent throughout `admin.html`).

**Nav-admin pattern**: every public page has a hidden `<a id="nav-admin" href="/admin.html" style="display:none">` shown only when `getMe().is_admin` is true. Keep this consistent (correct `/` path, matching id) across all pages.

## Deployment

Backend: Railway (`backend/procfile` runs migrations then `uvicorn`). Frontend: Cloudflare Pages, static (`frontend/_redirects` has a catch-all 404 rule, no SPA fallback to any page). Cloudflare Web Analytics is embedded in the frontend pages.

## Idiome
Spanish