# Velonox Store

Proyecto e-commerce en desarrollo activo, construido con FastAPI en el backend, PostgreSQL como base de datos y un frontend en HTML, CSS y JavaScript vanilla.

Este repositorio reúne la lógica de negocio de una tienda online, incluyendo autenticación de usuarios, catálogo de productos, carrito de compras, pagos, panel administrativo y edición visual del layout de la tienda.

## Estado actual

El proyecto sigue en etapa de desarrollo, pero ya cuenta con una base funcional y varios módulos operativos.

- Backend funcionando con rutas para autenticación, productos, carrito, pagos y layout.
- Frontend público con catálogo, carrito, checkout y página de detalle de producto.
- Panel administrativo para gestionar productos y bloques visuales de la tienda.
- Integración con pagos y generación de contenido visual asistida por IA.
- Se siguen incorporando mejoras de experiencia, estabilidad y diseño.

## Características implementadas

### Frontend
- Página de inicio con catálogo de productos.
- Página de detalle de producto con descripción, especificaciones, características y productos relacionados.
- Carrito de compras con actualización de cantidades y eliminación de elementos.
- Flujo de checkout y página de resultado de pago.
- Panel administrativo para edición visual del layout y gestión de productos.

### Backend
- API REST con FastAPI.
- Autenticación y autorización basada en JWT.
- Gestión de usuarios, productos, carritos y órdenes.
- Integración con pagos.
- Gestión dinámica del layout de la tienda.
- Endpoints preparados para extender la plataforma con nuevas funcionalidades.

## Stack técnico

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- HTML / CSS / JavaScript vanilla
- Stripe
- IA para generación de contenido visual

## Estructura del proyecto

- backend/: lógica del servidor, rutas, modelos, esquemas y servicios.
- frontend/: páginas HTML, estilos y scripts del lado del cliente.
- alembic/: migraciones de base de datos.
- INFORME_PROYECTO.txt: documento de seguimiento del proyecto.

## Requisitos

- Python 3.10+
- PostgreSQL
- Entorno virtual recomendado

## Instalación rápida

1. Crear y activar un entorno virtual.
2. Instalar dependencias del backend.
3. Configurar las variables de entorno necesarias.
4. Ejecutar la API localmente.
5. Abrir el frontend desde un servidor estático o desde el navegador.

## Variables de entorno

Se recomienda configurar variables como:

- DATABASE_URL
- SECRET_KEY
- STRIPE_SECRET_KEY
- STRIPE_WEBHOOK_SECRET
- FRONTEND_URL
- ANTHROPIC_API_KEY

No se incluyen credenciales ni secretos en este archivo.

## Uso

Una vez levantado el proyecto, se puede:

- Registrarse o iniciar sesión.
- Explorar productos.
- Agregar productos al carrito.
- Completar el proceso de compra.
- Acceder al panel administrativo para gestionar la tienda.

## Roadmap

- Mejorar la experiencia del panel administrativo.
- Añadir más validaciones y manejo de errores.
- Ampliar pruebas y cobertura.
- Mejorar la documentación de la API.
- Seguir refinando la experiencia visual y la usabilidad.

## Nota

Este proyecto está en desarrollo continuo y su finalidad es evolucionar hacia una plataforma más completa, escalable y preparada para producción.
