# Velonox Store

Proyecto e-commerce en desarrollo activo, construido con FastAPI en el backend, PostgreSQL como base de datos y un frontend estático en HTML, CSS y JavaScript vanilla.

Este repositorio reúne la lógica de negocio de una tienda online con un enfoque comercial completo: autenticación de usuarios, catálogo de productos, categorías, carrito de compras, checkout, pagos, checkout invitado, panel administrativo, edición visual del layout, páginas de producto personalizadas, ajustes de tienda y métricas de negocio.

## Estado actual

El proyecto ya cuenta con una base funcional sólida y varios módulos operativos.

- Backend con rutas para autenticación, productos, categorías, carrito, pagos, checkout invitado, layout, páginas de producto, métricas y ajustes de tienda.
- Frontend público con home, catálogo, categorías, detalle de producto, carrito, checkout, páginas institucionales, contacto, regalos, sets y políticas legales.
- Panel administrativo para gestionar productos, categorías, bloques visuales, ajustes de tienda y métricas del negocio.
- Integraciones con Stripe, IA para generación de bloques visuales y analítica web.
- Se siguen incorporando mejoras de experiencia, estabilidad, diseño, documentación y despliegue.

## Características implementadas

### Frontend
- Página de inicio con catálogo destacado y contenido visual de la tienda.
- Página de detalle de producto con descripción, especificaciones, características, reseñas de referencia y productos relacionados.
- Carrito de compras con actualización de cantidades y eliminación de elementos.
- Flujo de checkout y página de resultado de pago.
- Checkout invitado para pedidos sin registro previo.
- Panel administrativo para edición visual del layout, gestión de productos, categorías, ajustes de marca y métricas.
- Páginas institucionales, de contacto, políticas y contenido temático como regalos y sets.

### Backend
- API REST con FastAPI.
- Autenticación y autorización basada en JWT.
- Gestión de usuarios, productos, categorías, carritos, órdenes y páginas de producto.
- Integración con pagos y webhooks de Stripe.
- Gestión dinámica del layout de la tienda con bloques configurables y generación asistida por IA.
- Endpoints para métricas de negocio, checkout invitado y ajustes de configuración de la tienda.
- Estructura preparada para extender la plataforma con nuevas funcionalidades y servicios adicionales.

## Stack técnico

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL
- Alembic
- HTML / CSS / JavaScript vanilla
- Stripe
- API de IA para generación de contenido visual
- Cloudflare Web Analytics

## Estructura del proyecto

- backend/: lógica del servidor, rutas, modelos, esquemas, servicios, middleware y configuración.
- frontend/: páginas HTML, estilos y scripts del lado del cliente.
- alembic/: migraciones de base de datos.
- docs/: documentación técnica y de negocio del proyecto.
- INFORME_PROYECTO.txt: documento de seguimiento del proyecto.

## Requisitos

- Python 3.10+
- PostgreSQL
- Entorno virtual recomendado
- Dependencias del backend instaladas desde backend/requirements.txt

## Instalación rápida

1. Crear y activar un entorno virtual.
2. Instalar dependencias del backend con pip install -r backend/requirements.txt.
3. Configurar las variables de entorno necesarias.
4. Ejecutar las migraciones de base de datos con alembic upgrade head.
5. Levantar la API localmente desde la carpeta backend con uvicorn main:app --reload.
6. Abrir el frontend desde un servidor estático o desde el navegador.

## Variables de entorno

Se recomienda configurar variables como:

- DATABASE_URL
- SECRET_KEY
- STRIPE_SECRET_KEY
- STRIPE_WEBHOOK_SECRET
- FRONTEND_URL
- ANTHROPIC_API_KEY
- SMTP_HOST
- SMTP_PORT
- SMTP_USER
- SMTP_PASSWORD
- SMTP_FROM

No se incluyen credenciales ni secretos en este archivo.

## Uso

Una vez levantado el proyecto, se puede:

- Registrarse o iniciar sesión.
- Explorar productos y categorías.
- Agregar productos al carrito.
- Completar el proceso de compra.
- Usar el checkout invitado para pedidos sin crear cuenta.
- Acceder al panel administrativo para gestionar la tienda.
- Revisar métricas, ajustes visuales y contenido asociado a la experiencia comercial.

## Roadmap

- Mejorar la experiencia del panel administrativo.
- Añadir más validaciones y manejo de errores.
- Ampliar pruebas automatizadas y cobertura.
- Mejorar la documentación técnica y de uso.
- Seguir refinando la experiencia visual y la usabilidad.
- Fortalecer el despliegue, la observabilidad y la infraestructura del sistema.

## Nota

Este proyecto está en desarrollo continuo y su finalidad es evolucionar hacia una plataforma más completa, escalable y preparada para producción.
