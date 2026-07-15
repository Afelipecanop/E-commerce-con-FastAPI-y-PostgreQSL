---
title: "Incidente: 500 en /layout/?page=home"
tags:
  - incidente
  - backend
  - base-de-datos
aliases:
  - incidente-page-slug-alembic
  - error-500-layout-home
date: 2026-07-14
---

# Incidente: 500 en `/layout/?page=home`

Parte de [[proyecto]]. Afecta a [[rutas-api#Layout de tienda (`/layout`)]] y a la tabla `store_layout` documentada en [[modelo-bd#`store_layout` — `models/layout.py`]].

## Síntoma

`GET /layout/?page=home` devolvía **500 Internal Server Error** en producción. Como este endpoint es público y lo llama la tienda al cargar la página principal, el frontend se quedaba sin bloques de layout (home rota).

## Causa raíz

> [!warning] Causa raíz
> La migración que agregaba `page_slug` a `store_layout` usaba un `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. En producción, esa columna **ya existía** por una migración manual previa (aplicada directamente contra la DB, fuera del historial de Alembic), así que el `IF NOT EXISTS` hizo que la sentencia no hiciera nada — en particular, nunca llegó a aplicar el `NOT NULL` ni el `DEFAULT 'home'` sobre la columna existente.
>
> Como resultado, las filas de `store_layout` creadas antes de esa migración manual quedaron con `page_slug = NULL` ("filas legacy"). Cuando `GET /layout/?page=home` filtraba por `page_slug == "home"`, esas filas legacy no aparecían en el resultado, así que el endpoint interpretaba que la página `home` no tenía bloques y disparaba el **auto-seed** (`DEFAULT_BLOCKS`) para crearlos. Pero los bloques por defecto usan **ids fijos** (`"block-announcement"`, `"block-banner"`, etc.), que ya existían en la tabla como parte de las filas legacy con `page_slug = NULL`. El `INSERT` del seed chocaba entonces contra esos ids ya ocupados — **colisión de primary key** — y la petición terminaba en 500 antes de poder devolver ningún bloque.

## Solución aplicada

1. **Backfill de las filas legacy**: `UPDATE store_layout SET page_slug = 'home' WHERE page_slug IS NULL;` — asigna la página correcta a los bloques que ya existían antes de que la columna tuviera valor.
2. **Corregir la columna a nivel de esquema**:
   - `ALTER TABLE store_layout ALTER COLUMN page_slug SET DEFAULT 'home';`
   - `ALTER TABLE store_layout ALTER COLUMN page_slug SET NOT NULL;`

Con el backfill hecho antes del `SET NOT NULL`, el `ALTER COLUMN` no falla por filas nulas existentes, y a partir de ahí toda fila nueva recibe `'home'` por defecto si no se especifica `page_slug` explícitamente.

## Lección para futuras migraciones

`IF NOT EXISTS` / `IF EXISTS` en DDL son útiles para hacer una migración idempotente frente a *sí misma*, pero no sustituyen verificar el estado real de la columna cuando se sospecha que pudo haberse creado manualmente fuera de Alembic. Si una columna puede haber sido creada por fuera del flujo de migraciones, la migración correctora debe comprobar y forzar explícitamente `DEFAULT`/`NOT NULL` (como se hizo aquí) en lugar de asumir que `ADD COLUMN` ya los dejó configurados.

## Notas relacionadas

- [[proyecto]]
- [[rutas-api]]
- [[modelo-bd]]
