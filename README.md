# Velonox Store

Proyecto e-commerce en desarrollo activo, construido con FastAPI en el backend, PostgreSQL como base de datos y un frontend en HTML, CSS y JavaScript vanilla.

Este repositorio reúne la lógica de negocio de una tienda online, incluyendo autenticación de usuarios, catálogo de productos, carrito de compras, checkout, pagos, panel administrativo, edición visual del layout, páginas de producto personalizadas y métricas de negocio.

## Estado actual

El proyecto sigue en etapa de desarrollo, pero ya cuenta con una base funcional y varios módulos operativos.

- Backend funcionando con rutas para autenticación, productos, carrito, pagos, layout, páginas de producto y métricas.
- Frontend público con catálogo, detalle de producto, carrito, checkout, página institucional y contacto.
- Panel administrativo para gestionar productos y bloques visuales de la tienda.
- Integración con pagos y generación de contenido visual asistida por IA.
- Se siguen incorporando mejoras de experiencia, estabilidad, diseño y documentación.

## Características implementadas

### Frontend
- Página de inicio con catálogo de productos.
- Página de detalle de producto con descripción, especificaciones, características, reseñas de referencia y productos relacionados.
- Carrito de compras con actualización de cantidades y eliminación de elementos.
- Flujo de checkout y página de resultado de pago.
- Panel administrativo para edición visual del layout y gestión de productos.
- Páginas institucionales y de contacto para complementar la experiencia de marca.

### Backend
- API REST con FastAPI.
- Autenticación y autorización basada en JWT.
- Gestión de usuarios, productos, carritos, órdenes y páginas de producto.
- Integración con pagos y webhooks de Stripe.
- Gestión dinámica del layout de la tienda.
- Endpoints para métricas y generación de contenido visual con IA.
- Estructura preparada para extender la plataforma con nuevas funcionalidades.

## Stack técnico

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL
- Alembic
- HTML / CSS / JavaScript vanilla
- Stripe
- IA para generación de contenido visual

## Estructura del proyecto

- backend/: lógica del servidor, rutas, modelos, esquemas, servicios y configuración.
- frontend/: páginas HTML, estilos y scripts del lado del cliente.
- alembic/: migraciones de base de datos.
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
4. Ejecutar la API localmente desde la carpeta backend con uvicorn main:app --reload.
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
- Revisar métricas y contenido visual asociado a la experiencia comercial.

## Roadmap

- Mejorar la experiencia del panel administrativo.
- Añadir más validaciones y manejo de errores.
- Ampliar pruebas y cobertura.
- Mejorar la documentación de la API.
- Seguir refinando la experiencia visual y la usabilidad.
- Fortalecer el despliegue y la observabilidad del sistema.

## Nota

Este proyecto está en desarrollo continuo y su finalidad es evolucionar hacia una plataforma más completa, escalable y preparada para producción.
