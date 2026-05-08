#!/usr/bin/env python3
"""
Script de tráfico sintético
Genera requests automáticos a la API para poblar las métricas en Grafana.
"""

import httpx
import time
import random
import argparse
from datetime import datetime

API_BASE = "http://localhost:3000"

SCENARIOS = [
    # (weight, method, path_fn, kwargs_fn)
    (30, "GET",  lambda: "/products",                    lambda: {}),
    (15, "GET",  lambda: f"/products/{random.randint(1,5)}", lambda: {}),
    (10, "GET",  lambda: "/products",                    lambda: {"params": {"category": random.choice(["electronics","clothing","accessories"])}}),
    (20, "POST", lambda: "/orders",                      lambda: {"params": {"product_id": random.randint(1,5), "quantity": random.randint(1,3)}}),
    (10, "GET",  lambda: "/orders/stats",                lambda: {}),
    (10, "GET",  lambda: "/users/active",                lambda: {}),
    (5,  "POST", lambda: "/users/login",                 lambda: {"params": {"username": f"user_{random.randint(1,100)}"}}),
    (5,  "GET",  lambda: "/health",                      lambda: {}),
    # Tráfico de error para métricas de errores
    (3,  "GET",  lambda: "/products/999",                lambda: {}),
    (2,  "POST", lambda: "/orders",                      lambda: {"params": {"product_id": 999, "quantity": 1}}),
]

WEIGHTS = [s[0] for s in SCENARIOS]
TOTAL_WEIGHT = sum(WEIGHTS)


def pick_scenario():
    r = random.uniform(0, TOTAL_WEIGHT)
    acc = 0
    for s in SCENARIOS:
        acc += s[0]
        if r <= acc:
            return s
    return SCENARIOS[0]


def run(rps: float, duration: int):
    delay = 1.0 / rps
    end_time = time.time() + duration if duration > 0 else float("inf")
    req_count = 0
    error_count = 0

    print(f"🚀 Iniciando tráfico sintético → {API_BASE}")
    print(f"   RPS objetivo: {rps} | Duración: {'∞' if duration == 0 else f'{duration}s'}")
    print("-" * 60)

    with httpx.Client(base_url=API_BASE, timeout=5.0) as client:
        while time.time() < end_time:
            _, method, path_fn, kwargs_fn = pick_scenario()
            path = path_fn()
            kwargs = kwargs_fn()

            try:
                t0 = time.time()
                if method == "GET":
                    resp = client.get(path, **kwargs)
                else:
                    resp = client.post(path, **kwargs)
                elapsed = (time.time() - t0) * 1000

                req_count += 1
                status = resp.status_code
                icon = "✅" if status < 400 else ("⚠️ " if status < 500 else "❌")

                if status >= 400:
                    error_count += 1

                if req_count % 20 == 0:
                    ts = datetime.now().strftime("%H:%M:%S")
                    err_rate = error_count / req_count * 100
                    print(f"[{ts}] {icon} #{req_count:4d} | {method:4s} {path:25s} | {status} | {elapsed:6.1f}ms | errores: {err_rate:.1f}%")

            except Exception as e:
                error_count += 1
                print(f"❌ Error en {method} {path}: {e}")

            time.sleep(delay)

    print(f"\n✅ Finalizado: {req_count} requests, {error_count} errores ({error_count/max(req_count,1)*100:.1f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de tráfico sintético para la API")
    parser.add_argument("--rps",      type=float, default=2.0,  help="Requests por segundo (default: 2)")
    parser.add_argument("--duration", type=int,   default=0,    help="Duración en segundos (0 = infinito)")
    parser.add_argument("--url",      type=str,   default=None, help="URL base de la API")
    args = parser.parse_args()

    if args.url:
        API_BASE = args.url

    run(rps=args.rps, duration=args.duration)
