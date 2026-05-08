from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
import random
import psutil

app = FastAPI(title="API Monitoreada", version="1.0.0")

# ── Métricas Prometheus ──────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "api_requests_total",
    "Total de requests HTTP",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "api_request_duration_seconds",
    "Latencia de requests en segundos",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

ACTIVE_USERS = Gauge(
    "api_active_users",
    "Usuarios activos simulados"
)

PRODUCTS_IN_STOCK = Gauge(
    "api_products_in_stock",
    "Cantidad de productos en inventario",
    ["category"]
)

ORDERS_PROCESSED = Counter(
    "api_orders_processed_total",
    "Total de órdenes procesadas",
    ["status"]
)

CPU_USAGE = Gauge("api_cpu_usage_percent", "Uso de CPU del proceso")
MEMORY_USAGE = Gauge("api_memory_usage_bytes", "Uso de memoria del proceso")

# ── Middleware para métricas automáticas ─────────────────────────────────────
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    if request.url.path != "/metrics":
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)

    return response

# ── Endpoint 1: Productos ────────────────────────────────────────────────────
FAKE_PRODUCTS = [
    {"id": 1, "name": "Laptop Pro",     "price": 1299.99, "category": "electronics", "stock": 15},
    {"id": 2, "name": "Mouse Inalámbrico", "price": 29.99, "category": "electronics", "stock": 80},
    {"id": 3, "name": "Teclado Mecánico", "price": 89.99, "category": "electronics", "stock": 45},
    {"id": 4, "name": "Camiseta Dev",   "price": 19.99, "category": "clothing",     "stock": 200},
    {"id": 5, "name": "Mochila Urbana", "price": 49.99, "category": "accessories",  "stock": 60},
]

@app.get("/products", tags=["Productos"])
def get_products(category: str = None):
    """Lista todos los productos, opcionalmente filtrados por categoría."""
    # Actualizar gauge de stock por categoría
    from collections import defaultdict
    stock_by_cat = defaultdict(int)
    for p in FAKE_PRODUCTS:
        stock_by_cat[p["category"]] += p["stock"]
    for cat, qty in stock_by_cat.items():
        PRODUCTS_IN_STOCK.labels(category=cat).set(qty)

    result = FAKE_PRODUCTS
    if category:
        result = [p for p in FAKE_PRODUCTS if p["category"] == category]
        if not result:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    # Simular latencia variable
    time.sleep(random.uniform(0.01, 0.15))
    return {"products": result, "total": len(result)}

@app.get("/products/{product_id}", tags=["Productos"])
def get_product(product_id: int):
    """Obtiene un producto por ID."""
    time.sleep(random.uniform(0.005, 0.08))
    product = next((p for p in FAKE_PRODUCTS if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

# ── Endpoint 2: Órdenes ──────────────────────────────────────────────────────
@app.post("/orders", tags=["Órdenes"])
def create_order(product_id: int, quantity: int = 1):
    """Crea una nueva orden de compra."""
    time.sleep(random.uniform(0.05, 0.4))  # más lento: simula DB write

    product = next((p for p in FAKE_PRODUCTS if p["id"] == product_id), None)
    if not product:
        ORDERS_PROCESSED.labels(status="failed").inc()
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if quantity > product["stock"]:
        ORDERS_PROCESSED.labels(status="rejected").inc()
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    # Simular fallo aleatorio (5%)
    if random.random() < 0.05:
        ORDERS_PROCESSED.labels(status="error").inc()
        raise HTTPException(status_code=500, detail="Error interno al procesar la orden")

    order_id = random.randint(10000, 99999)
    ORDERS_PROCESSED.labels(status="success").inc()
    return {
        "order_id": order_id,
        "product": product["name"],
        "quantity": quantity,
        "total": round(product["price"] * quantity, 2),
        "status": "confirmed"
    }

@app.get("/orders/stats", tags=["Órdenes"])
def order_stats():
    """Estadísticas generales de órdenes."""
    time.sleep(random.uniform(0.02, 0.1))
    return {
        "message": "Consulta las métricas reales en /metrics o en Grafana",
        "hint": "Métrica: api_orders_processed_total"
    }

# ── Endpoint 3: Usuarios ─────────────────────────────────────────────────────
@app.get("/users/active", tags=["Usuarios"])
def get_active_users():
    """Retorna la cantidad de usuarios activos (simulado)."""
    time.sleep(random.uniform(0.005, 0.05))
    count = random.randint(10, 500)
    ACTIVE_USERS.set(count)
    return {"active_users": count, "timestamp": time.time()}

@app.post("/users/login", tags=["Usuarios"])
def user_login(username: str = "demo"):
    """Simula un login de usuario."""
    time.sleep(random.uniform(0.1, 0.3))
    if random.random() < 0.1:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    ACTIVE_USERS.inc()
    return {"status": "ok", "user": username, "token": f"tok_{random.randint(1000,9999)}"}

# ── Endpoint 4: Sistema ──────────────────────────────────────────────────────
@app.get("/health", tags=["Sistema"])
def health():
    """Health check del servicio."""
    process = psutil.Process()
    cpu = process.cpu_percent(interval=0.1)
    mem = process.memory_info().rss
    CPU_USAGE.set(cpu)
    MEMORY_USAGE.set(mem)
    return {"status": "healthy", "cpu_percent": cpu, "memory_mb": round(mem / 1024 / 1024, 2)}

@app.get("/metrics", tags=["Sistema"])
def metrics():
    """Endpoint de métricas para Prometheus."""
    process = psutil.Process()
    CPU_USAGE.set(process.cpu_percent(interval=0.1))
    MEMORY_USAGE.set(process.memory_info().rss)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/", tags=["Sistema"])
def root():
    return {
        "service": "API Monitoreada",
        "endpoints": ["/products", "/orders", "/users/active", "/health", "/metrics"],
        "docs": "/docs"
    }
