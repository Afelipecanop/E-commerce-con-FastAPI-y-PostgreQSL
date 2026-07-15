---
title: Proyecto E-commerce FastAPI + PostgreSQL
tags:
  - proyecto
  - arquitectura
aliases:
  - E-commerce FastAPI
---

# Proyecto E-commerce FastAPI + PostgreSQL

Tienda online con backend en **FastAPI** y frontend en **HTML/JS vanilla**. Proyecto de aprendizaje/producción.

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.x (patrón síncrono), PostgreSQL vía `psycopg2`, Alembic para migraciones, JWT (`python-jose`) + `bcrypt` para autenticación, Stripe para pagos.
- **Frontend:** HTML/JS vanilla puro en `frontend/`, incluyendo un panel de administración en `frontend/admin.html`.
- **Despliegue:** backend en Railway, frontend en Netlify.

> [!warning] Convención del proyecto
> El ORM usa el patrón síncrono de SQLAlchemy. No introducir async ORM sin migrar todo el proyecto de forma consistente.

## Estructura del backend

```
backend/
├── main.py
├── database.py
├── procfile
├── models/          # User, Product, Cart, Order, StoreLayout, StoreSetting, ProductPage
├── routes/          # auth, products, cart, payments, layout, product_pages, metrics
├── schemas/         # Pydantic schemas por dominio
├── services/        # lógica de negocio (auth, etc.)
├── middleware/       # auth middleware
└── alembic/          # migraciones (env.py + versions/)
```

## Módulos principales

- **Autenticación:** `routes/auth.py` + `services/auth.py` + `middleware/auth.py`. JWT con `python-jose`, hashing con `bcrypt`.
- **Catálogo:** `models/product.py`, `routes/products.py`, más `models/product_page.py` / `routes/product_pages.py` para páginas de producto enriquecidas (specs, features, relacionados).
- **Carrito y pedidos:** `models/cart.py`, `models/order.py`, `routes/cart.py`.
- **Pagos:** `routes/payments.py` integrado con Stripe.
- **Layout de tienda:** `models/layout.py` (tabla `store_layout`) + `routes/layout.py` — bloques configurables de la página, con soporte multi-página vía `page_slug` (ver [[incidente-page-slug-alembic]]).
- **Configuración de tienda:** `models/settings.py`.
- **Métricas:** `routes/metrics.py` — endpoints de KPIs de negocio, consumidos por un dashboard en el panel admin (gráfico y órdenes recientes).
- **Analítica:** Cloudflare Web Analytics integrado en el frontend.

Ver el detalle de endpoints en [[rutas-api]] y el detalle de tablas/modelos en [[modelo-bd]].

## Seguridad

> [!info] Patrones de seguridad a mantener
> - Ninguna API externa se llama directo desde el frontend — siempre vía proxy en el backend usando la API key del `.env` del servidor.
> - CORS con métodos y headers explícitos (no `["*"]`).
> - Errores internos (Stripe, DB) nunca se exponen tal cual al cliente; se devuelven mensajes genéricos.

## Notas relacionadas

- [[rutas-api]]
- [[modelo-bd]]
- [[incidente-page-slug-alembic]]
