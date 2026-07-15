---
title: Rutas de la API
tags:
  - proyecto
  - api
  - backend
aliases:
  - API routes
  - Endpoints
---

# Rutas de la API

Parte de [[proyecto]]. Todos los routers se registran en `backend/main.py` y se montan sin prefijo global (cada router trae su propio `prefix`).

| Router | Prefix | Archivo | Auth |
|---|---|---|---|
| Autenticación | `/auth` | `routes/auth.py` | pública / JWT |
| Productos | `/products` | `routes/products.py` | pública (lectura) / admin (escritura) |
| Carrito | `/cart` | `routes/cart.py` | JWT (usuario) |
| Pagos | `/payments` | `routes/payments.py` | JWT / Stripe webhook |
| Layout de tienda | `/layout` | `routes/layout.py` | pública (lectura) / admin (escritura) |
| Páginas de producto | `/product-pages` | `routes/product_pages.py` | pública (lectura) / admin (escritura) |
| Métricas | `/metrics` | `routes/metrics.py` | admin |

Auth por dependencia: `get_current_user` (JWT válido) y `get_current_admin` (JWT + `is_admin=True`), ambas en `middleware/auth.py`.

## Auth (`/auth`)

- **POST `/auth/register`** — Crea un usuario nuevo y le crea automáticamente un carrito vacío (`Cart`) en la misma transacción. Devuelve 400 si el email ya existe.
- **POST `/auth/login`** — Autentica y devuelve un JWT (`Token`).
- **GET `/auth/me`** — Devuelve el usuario autenticado (requiere JWT).

## Productos (`/products`)

- **GET `/products/`** — Lista productos con `is_active == True`. Pública.
- **GET `/products/{product_id}`** — Detalle de un producto activo. Pública. 404 si no existe o está desactivado.
- **POST `/products/`** — Crea producto. Solo admin.
- **PUT `/products/{product_id}`** — Actualiza campos (`exclude_unset`). Solo admin.
- **DELETE `/products/{product_id}`** — *Soft delete*: pone `is_active = False`, no borra la fila. Solo admin.

## Carrito (`/cart`)

- **GET `/cart/`** — Carrito del usuario autenticado + total calculado en Python (`get_cart_total`).
- **POST `/cart/items`** — Agrega producto al carrito; si ya existe el item, suma cantidades. Valida stock antes de agregar.
- **PUT `/cart/items/{item_id}`** — Actualiza cantidad; si `quantity <= 0` borra el item en vez de dejarlo en 0.
- **DELETE `/cart/items/{item_id}`** — Elimina un item del carrito.

> [!warning] No valida stock en update
> `PUT /cart/items/{item_id}` no vuelve a chequear `product.stock` al aumentar la cantidad (solo `POST /cart/items` lo hace). Revisar antes de confiar en esta ruta para evitar overselling.

## Pagos (`/payments`)

- **POST `/payments/checkout`** — Convierte el carrito en una `Order` (`status="pending"`) y crea una sesión de Stripe Checkout. Verifica stock de todos los items antes de crear la orden.
- **POST `/payments/webhook`** — Endpoint que llama Stripe (no el usuario). Verifica la firma con `STRIPE_WEBHOOK_SECRET`. En `checkout.session.completed`: marca la orden `paid`, descuenta stock y vacía el carrito.
- **GET `/payments/orders`** — Historial de órdenes del usuario autenticado, más recientes primero.
- **GET `/payments/orders/{order_id}`** — Detalle de una orden propia.

> [!bug] Errores de Stripe expuestos parcialmente
> El bloque `try/except stripe.StripeError` en `create_checkout` cancela la orden y devuelve un 502 genérico — correcto según el patrón de seguridad del proyecto (ver [[proyecto#Seguridad]]). Si se toca este endpoint, mantener ese patrón y no dejar pasar `stripe.error.*` crudo al cliente.

## Layout de tienda (`/layout`)

Todos los endpoints reciben un query param **`page`** (default `"home"`) que identifica de qué página de la tienda se trata (home, contacto, nosotros, politicas, terminos, etc.), guardado en la columna `StoreLayout.page_slug`.

- **GET `/layout/`** — Devuelve los bloques de una página ordenados por `order_index`. Si no hay bloques en la DB para esa página, los siembra (`seed`) con `DEFAULT_BLOCKS` (para `home`) o `CONTENT_PAGE_BLOCKS[page]` (para páginas de contenido conocidas) y los persiste. Pública.
- **PUT `/layout/`** — Reemplaza *todos* los bloques de esa página (`delete` + `insert`). Solo admin.
- **POST `/layout/blocks`** — Agrega un bloque al final del layout de la página (calcula `order_index` como el máximo actual + 1). Solo admin.
- **DELETE `/layout/blocks/{block_id}`** — Elimina un bloque por id (no filtra por página). Solo admin.
- **POST `/layout/generate-block`** — Genera HTML/CSS con IA (llamada `httpx` async directa a la API de Anthropic usando `ANTHROPIC_API_KEY` del backend). Solo admin.
- **POST `/layout/ai-generate`** — Duplica la función de `generate-block` pero de forma síncrona (`requests`) y con manejo de errores más completo (timeout, request exception, status code). Solo admin.

> [!bug] Endpoints de IA duplicados
> `generate-block` y `ai-generate` hacen esencialmente lo mismo (generar HTML/CSS vía Anthropic). `ai-generate` es la versión más robusta (maneja timeouts y errores de red); `generate-block` es la más antigua y no valida esos casos. Candidato a consolidar — ver si el frontend todavía usa `generate-block` antes de eliminarlo.

> [!bug]- Bug resuelto: columna `page_slug` faltante en producción (jul. 2026)
> Detalle completo en [[incidente-page-slug-alembic]]. Resumen: todo el router `/layout` depende de `StoreLayout.page_slug`, pero la migración que agregaba esa columna nunca se ejecutaba en Railway porque el Procfile solo arrancaba `uvicorn` y no corría `alembic upgrade head`. Resultado: la app funcionaba en local (DB ya migrada a mano) pero fallaba en producción con error de columna inexistente. Se corrigió el Procfile para correr las migraciones antes de levantar el server.

## Páginas de producto (`/product-pages`)

- **GET `/product-pages/{product_id}`** — Configuración de la página de un producto (specs, features, variantes, bloques custom). Si no existe `ProductPage` en la DB, devuelve defaults genéricos de Velonox (`DEFAULT_SPECS` / `DEFAULT_FEATURES`) sin crear nada. Pública.
- **PUT `/product-pages/{product_id}`** — Crea o actualiza la página (upsert). Solo admin.
- **DELETE `/product-pages/{product_id}`** — Borra la configuración custom y vuelve a los defaults. Solo admin.

## Métricas (`/metrics`)

- **GET `/metrics/dashboard`** — Único endpoint. Devuelve KPIs agregados para el panel admin: ventas (histórico, mes, 30d, variación % vs 30-60d), órdenes, usuarios (con la misma lógica de variación %), stock (sin stock / bajo stock), top 5 productos por unidades vendidas, serie de ventas por día (últimos 14 días) y las 8 órdenes más recientes. Solo admin.

> [!info] Cálculo de variación %
> El patrón "variación % vs periodo anterior" se repite para ventas y usuarios: compara los últimos 30 días contra los 30 días previos a esos. Si el periodo anterior es 0, se reporta 100% si hubo actividad reciente, o 0% si no.

## Rutas del sistema (definidas en `main.py`, sin router)

- **GET `/`** — Health básico, mensaje fijo.
- **GET `/health`** — Health check con versión.
- **GET `/db-check`** — Ejecuta `SELECT 1` contra la DB; devuelve `error` genérico si falla (no expone la excepción).

## CORS

`main.py` restringe `allow_origins` a una lista explícita (local, Railway, Netlify, Cloudflare Pages) y limita `allow_methods`/`allow_headers` — ver [[proyecto#Seguridad]].

## Notas relacionadas

- [[proyecto]]
- [[modelo-bd]]
- [[incidente-page-slug-alembic]]
