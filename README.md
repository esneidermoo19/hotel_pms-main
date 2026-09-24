# 🏨 Hotel PMS - System Management Solution

![Build Status](https://github.com/esneidermoo19/hotel_pms_main/workflows/Pytest/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Flask Version](https://img.shields.io/badge/flask-3.x-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Un sistema de gestión hotelera (PMS) modular y escalable construido con **Flask**, diseñado para administrar reservas, habitaciones, recepción, facturación, puntos de venta (POS) y personal.

---

## 📌 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Stack Tecnológico](#-stack-tecnológico)
- [Arquitectura del Proyecto](#-arquitectura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Configuración](#-instalación-y-configuración)
  - [Opción 1: Desarrollo Local (Entorno Virtual)](#opción-1-desarrollo-local-entorno-virtual)
  - [Opción 2: Despliegue con Docker](#opción-2-despliegue-con-docker)
- [Variables de Entorno](#-variables-de-entorno)
- [Ejecución de Pruebas Unitarias](#-ejecución-de-pruebas-unitarias)
- [Licencia](#-licencia)

---

## ✨ Características Principales

- **🔐 Autenticación y RBAC:** Control de acceso basado en roles (Administrador, Recepcionista, Empleado).
- **🛎️ Recepción en Tiempo Real:** Gestión de Check-in, Check-out y mapa interactivo de estado de habitaciones.
- **📅 Reservaciones:** Registro, filtrado y seguimiento de reservas de clientes.
- **💳 Facturación y Pagos:** Cálculo automático de tarifas, servicios adicionales y emisión de facturas.
- **🍽️ Punto de Venta (POS):** Control de consumos adicionales dentro del hotel (restaurante, minibar, spa).
- **📊 Reportes:** Generación de estadísticas operativas y financieras.
- **🛡️ Auditoría:** Módulo de logs e historial de acciones ejecutadas por los usuarios.

---

## 🛠️ Stack Tecnológico

- **Backend:** Python, Flask (Blueprints, Jinja2 Templates)
- **Base de Datos:** PostgreSQL / SQLite (vía SQLAlchemy ORM)
- **Seguridad & RBAC:** Werkzeug Security, Flask Login / JWT, Decoradores personalizados
- **Testing & CI/CD:** Pytest, GitHub Actions (`pytest.yml`)
- **Contenedorización:** Docker, Dockerfile

---

## 📂 Arquitectura del Proyecto

```text
├── .github/workflows/   # Integración continua (GitHub Actions)
├── app/
│   ├── core/            # Configuración global y filtros
│   ├── models/          # Modelos de datos de SQLAlchemy
│   ├── routes/          # Rutas organizadas por Blueprints (auth, admin, recep, etc.)
│   ├── services/        # Lógica de negocio (facturación, envío de mails)
│   ├── helpers/         # Utilidades, decoradores y RBAC
│   ├── static/          # Recursos estáticos (CSS, JS, Imágenes)
│   └── templates/       # Vistas HTML (Jinja2)
├── Dockerfile           # Configuración de Docker
├── config.py            # Manejo de configuraciones por entorno
├── requirements.txt     # Dependencias de Python
└── run.py               # Punto de entrada de la aplicación
