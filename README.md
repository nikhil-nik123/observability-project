# Observability Project

This project demonstrates application observability using **Prometheus**, **Grafana**, **Loki**, **Promtail**, and **Jaeger**. The application exposes metrics, logs, and traces, allowing real-time monitoring and debugging.

## 🛠 Tech Stack
- Python (Flask app)
- Prometheus (Metrics collection)
- Grafana (Dashboard visualization)
- Loki + Promtail (Centralized log collection)
- Jaeger (Distributed tracing)
- Docker & Docker Compose

## 🚀 How to Run
```bash
docker compose up --build
Access the services:

Service	URL
Application	http://localhost:8000

Prometheus	http://localhost:9090

Grafana	        http://localhost:3000

Loki	        http://localhost:3100

Jaeger	        http://localhost:16686

📊 Dashboards & Observability

Application metrics exposed at /metrics

Logs collected from container stdout using Promtail → Loki → Grafana

Traces visualized in Jaeger UI
