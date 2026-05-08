# 📊 Sistema de Monitoreo y Observabilidad en la Nube

**Nombre:** Maria Alexandra Rivera Alvarez  
**Código:** 202222703601  
**Repositorio:** https://github.com/Alexandra510R/-Monitoreo-API  
**Video:** [Explicacion breve de monitoreo](https://www.loom.com/share/c583a9f775c045c3a5a508bedad37c1d)

Actividad BONUS — Desarrollo de Aplicaciones en la Nube  
Fundación Universitaria Los Libertadores

---

## 📝 Descripción 

Sistema de monitoreo completo implementado con Docker que incluye una API REST instrumentada con métricas Prometheus, recolección de datos con Prometheus y visualización en tiempo real con Grafana.

## 🧰 Arquitectura

```
Script de tráfico ──► API FastAPI (:3000) ──► GET /metrics
                                                    │
                                         Prometheus (:9090)
                                         scraping cada 5s
                                                    │
                                         Grafana (:3001)
                                         dashboard en tiempo real
```

## 🔢 Estructura del proyecto

```
monitoring-project/
├── api/
│   ├── main.py              # API FastAPI con métricas Prometheus
│   ├── requirements.txt     # Dependencias Python
│   └── Dockerfile           # Imagen de la API
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml    # Datasource automático
│       └── dashboards/
│           ├── dashboard.yml     # Configuración de provisioning
│           └── api-dashboard.json # Dashboard con 8 paneles
├── prometheus/
│   └── prometheus.yml       # Configuración de scraping
├── Script/
│   └── traffic.py           # Generador de tráfico sintético
├── docker-compose.yml
└── README.md
```

## ☑️ Requisitos previos

- Docker Desktop instalado y corriendo
- Python 3.x (solo para el script de tráfico)
- pip install httpx

## ⚒️ Instrucciones de uso

### 1. Clonar el repositorio

```bash
git clone https://github.com/Alexandra510R/-Monitoreo-API
cd monitoring-project
```

### 2. Levantar el stack completo

```bash
docker compose up --build -d
```

Esperar aproximadamente 20 segundos para que todos los servicios inicien.

### 3. Verificar que los servicios estén corriendo

```bash
docker compose ps
```

Deben aparecer tres servicios en estado `running`: `api`, `prometheus` y `grafana`.

### 4. Acceder a los servicios

| Servicio    | URL                           | Credenciales     |
|-------------|-------------------------------|------------------|
| API Docs    | http://localhost:3000/docs    | —                |
| API Metrics | http://localhost:3000/metrics | —                |
| Prometheus  | http://localhost:9090         | —                |
| Grafana     | http://localhost:3001         | admin / admin123 |

En Grafana ir a: **Dashboards → API Monitoring Dashboard**

### 5. Generar tráfico sintético

```bash
# Instalar dependencia
pip install httpx

# Tráfico continuo a 3 requests por segundo
python Script/traffic.py --rps 3

# Tráfico por tiempo limitado (5 minutos)
python Script/traffic.py --rps 5 --duration 300
```

También se puede consumir la API manualmente desde http://localhost:3000/docs usando el botón **Try it out** en cada endpoint.

### 6. Detener el stack

```bash
docker compose down
```

---

## ⚙️ Endpoints de la API

| Método | Endpoint         | Descripción                          |
|--------|------------------|--------------------------------------|
| GET    | `/`              | Endpoint principal, lista servicios  |
| GET    | `/products`      | Lista productos (filtro: ?category=) |
| GET    | `/products/{id}` | Detalle de producto por ID           |
| POST   | `/orders`        | Crear orden (?product_id=&quantity=) |
| GET    | `/orders/stats`  | Estadísticas de órdenes              |
| GET    | `/users/active`  | Usuarios activos (simulado)          |
| POST   | `/users/login`   | Login simulado (?username=)          |
| GET    | `/health`        | Health check con CPU y memoria       |
| GET    | `/metrics`       | Métricas en formato Prometheus       |

---

## 📉 Métricas implementadas

| Métrica                        | Tipo      | Descripción                                  |
|--------------------------------|-----------|----------------------------------------------|
| `api_requests_total`           | Counter   | Total de requests por endpoint y status code |
| `api_request_duration_seconds` | Histogram | Latencia de requests (p50, p95, p99)         |
| `api_active_users`             | Gauge     | Usuarios activos en tiempo real              |
| `api_products_in_stock`        | Gauge     | Stock de productos por categoría             |
| `api_orders_processed_total`   | Counter   | Órdenes procesadas por estado                |
| `api_cpu_usage_percent`        | Gauge     | Uso de CPU del proceso                       |
| `api_memory_usage_bytes`       | Gauge     | Uso de memoria del proceso                   |

---

## 🎛️ Dashboard de Grafana

El dashboard incluye 8 paneles configurados automáticamente:

1. **Requests por segundo (RPS)** — tráfico desglosado por endpoint
2. **Tasa de Errores (%)** — porcentaje de respuestas 5xx con umbrales de color
3. **Latencia P50 / P95 / P99** — percentiles de tiempo de respuesta por endpoint
4. **Usuarios Activos** — valor instantáneo en tiempo real
5. **Órdenes Procesadas** — conteo por estado (success / failed / error)
6. **Requests por Status Code** — distribución en pie chart (200, 404, 500)
7. **Stock por Categoría** — inventario por categoría en bar gauge
8. **Uso de CPU y Memoria** — recursos del proceso API en serie de tiempo

---

## 💡 Queries PromQL utilizadas

```promql
# Requests por segundo por endpoint
sum(rate(api_requests_total[1m])) by (endpoint)

# Tasa de errores en porcentaje
sum(rate(api_requests_total{status_code=~"5.."}[1m])) / sum(rate(api_requests_total[1m])) * 100

# Latencia p95
histogram_quantile(0.95, sum(rate(api_request_duration_seconds_bucket[1m])) by (le, endpoint))

# Total de requests acumulados
api_requests_total

# Usuarios activos
api_active_users
```

---

## 🍴 Componentes técnicos

**API:** Python + FastAPI + prometheus-client  
**Contenedores:** Docker + docker-compose  
**Monitoreo:** Prometheus v2.51.2  
**Visualización:** Grafana v10.4.2  
**Tráfico sintético:** Python + httpx con escenarios ponderados

## ✍🏼 importancia del monitoreo

El monitoreo y la observabilidad son fundamentales en el desarrollo de aplicaciones modernas porque permiten conocer en tiempo real qué está pasando dentro de un sistema. Sin estas herramientas, cuando algo falla en producción, los equipos de desarrollo quedan "ciegos" — saben que hay un problema pero no dónde ni por qué.

La observabilidad va más allá del monitoreo tradicional: no solo alerta cuando algo sale mal, sino que proporciona el contexto necesario para entender la causa raíz. Métricas como la latencia, la tasa de errores y el throughput permiten detectar cuellos de botella antes de que afecten a los usuarios, tomar decisiones informadas sobre escalabilidad, y garantizar que los acuerdos de nivel de servicio (SLAs) se cumplan.

En la industria actual, donde las aplicaciones corren en la nube con arquitecturas de microservicios, la observabilidad dejó de ser opcional — es un requisito. Empresas como Netflix, Google y Amazon invierten enormemente en estas prácticas porque un sistema que no se puede observar, no se puede mejorar ni mantener con confianza.
