# Sistema de Gestión de Inventario Inteligente (AI-Driven)

Este repositorio contiene la implementación de un sistema de gestión de inventarios basado en **Arquitectura de Agentes**. La aplicación integra un modelo de lenguaje (LLM) capaz de ejecutar herramientas (Function Calling) para administrar bases de datos locales mediante comandos en lenguaje natural.

El sistema está diseñado con una arquitectura modular que separa la lógica de negocio, la interfaz de usuario y la capa de inteligencia artificial, implementando controles de acceso basados en roles (RBAC) para la seguridad operativa.

## Características Técnicas

### 1. Inteligencia Artificial Agéntica
El núcleo del sistema utiliza el modelo **GPT-4o** (vía GitHub Models) configurado como un agente autónomo. Este agente no solo procesa texto, sino que tiene capacidad de decisión para ejecutar funciones específicas del sistema:
* **Function Calling:** El modelo identifica cuándo ejecutar operaciones CRUD (Create, Read, Update, Delete) sobre el inventario.
* **Validación de Argumentos:** Sanitización y verificación de datos antes de la ejecución de cualquier comando crítico.
* **Preprocesamiento Local:** Algoritmos de expresiones regulares (`regex`) para optimizar consultas frecuentes sin consumo de tokens API.

### 2. Seguridad y Control de Acceso (RBAC)
Implementación de un sistema de autenticación y autorización granular. Las capacidades del agente están limitadas por el rol del usuario autenticado:
* **Admin:** Acceso total (Gestión de productos, precios, stock y generación de reportes).
* **Supervisor:** Gestión operativa (Stock y precios).
* **Empleado:** Acceso de solo lectura y consultas.

### 3. Auditoría y Trazabilidad
Sistema de registro inmutable (*logging*) que documenta todas las transacciones críticas. Cada entrada en el historial registra:
* Usuario responsable.
* Acción ejecutada y marca de tiempo.
* Estado anterior y nuevo valor (para control de cambios).

### 4. Interfaz y Visualización
Desarrollado sobre **Streamlit** para ofrecer un panel de control unificado que incluye:
* Chat interactivo con el agente.
* Tablas de datos filtrables en tiempo real.
* Dashboard de métricas (KPIs) y análisis de tendencias.
* Generación automática de reportes en formato PDF.

## Stack Tecnológico

* **Lenguaje:** Python 3.10+
* **Frontend:** Streamlit
* **AI Backend:** OpenAI SDK / GitHub Models (GPT-4o)
* **Persistencia:** JSON (Sistema de archivos local para portabilidad)
* **Entorno:** Gestión de variables mediante `python-dotenv`

## Instalación y Despliegue

### Prerrequisitos
* Python 3.10 o superior.
* Token de acceso a GitHub Models (o OpenAI API Key).

### Pasos de Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/danielfernandezf/inventory-agent-system.git](https://github.com/danielfernandezf/inventory-agent-system.git)
    cd inventory-agent-system
    ```

2.  **Configurar entorno virtual:**
    ```bash
    python -m venv venv
    # En Windows:
    .\venv\Scripts\activate
    # En Unix/MacOS:
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install openai streamlit pandas python-dotenv
    ```

4.  **Configuración de Variables de Entorno:**
    Cree un archivo `.env` en la raíz del proyecto basándose en el archivo `.env.template` proporcionado.
    ```env
    GITHUB_TOKEN=su_token_aqui
    ```

5.  **Ejecución:**
    ```bash
    streamlit run interfaz.py
    ```

## Credenciales de Prueba (Demo)

El sistema incluye una configuración inicial de usuarios para facilitar la evaluación técnica:

| Usuario | Rol | Alcance |
| :--- | :--- | :--- |
| `admin` | Administrator | Control total del sistema y reportes. |
| `supervisor` | Supervisor | Actualización de inventario y precios. |
| `empleado` | Viewer | Consultas de disponibilidad. |

> **Nota de Seguridad:** Las contraseñas en este entorno de demostración no están hashadas para facilitar la revisión del código. En un entorno de producción, se debe implementar hashing (ej. bcrypt).

## Estructura del Proyecto

* `AgenteInventario.py`: Orquestador principal de la lógica del agente y definición de herramientas.
* `interfaz.py`: Punto de entrada de la aplicación y lógica de frontend.
* `tools/`: Módulos auxiliares para manejo de archivos, reportes y lógica de negocio.
* `roles_config.py`: Definición estática de matrices de permisos.
* `data/`: Almacenamiento local (productos, usuarios, historial).

---
Autor: **Daniel Fernández**
