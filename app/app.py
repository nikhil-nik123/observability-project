# app/app.py
from flask import Flask, request
import time
import logging

# ---- Prometheus metrics ----
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# ---- OpenTelemetry tracing -> Jaeger ----
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# -----------------------------
# Logging (stdout, logfmt style)
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='ts="%(asctime)s" level=%(levelname)s msg="%(message)s"',
)
log = logging.getLogger("sample-app")

def logfmt(**fields) -> str:
    # simple logfmt helper: key=value (spaces replaced with underscores)
    parts = []
    for k, v in fields.items():
        s = str(v).replace(" ", "_")
        parts.append(f"{k}={s}")
    return " ".join(parts)

# -----------------------------
# Prometheus Metrics
# -----------------------------
REQUESTS = Counter(
    "app_requests_total",
    "Total HTTP requests",
    ["path", "method", "status"]
)

REQ_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Request latency in seconds",
    ["path", "method"]
)

# -----------------------------
# Tracing (OpenTelemetry -> Jaeger)
# -----------------------------
resource = Resource.create({SERVICE_NAME: "sample-app"})
provider = TracerProvider(resource=resource)
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",  # docker-compose service name
    agent_port=6831,           # UDP
)
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)  # auto-instrument Flask spans

@app.route("/healthz")
def health():
    return "ok\n", 200

@app.route("/")
def index():
    start = time.time()
    with tracer.start_as_current_span("index-handler"):
        # simulate some work
        time.sleep(0.05)

        # business response
        resp_text = "Hello from sample app!\n"
        status = 200

    # metrics
    REQUESTS.labels(path="/", method="GET", status=str(status)).inc()
    REQ_LATENCY.labels(path="/", method="GET").observe(time.time() - start)

    # logs (logfmt, easy for Loki)
    log.info(logfmt(
        event="request",
        path="/",
        method="GET",
        status=status,
        duration_ms=round((time.time() - start) * 1000, 1),
        client_ip=request.remote_addr,
        user_agent=request.headers.get("User-Agent", "")[:100]
    ))
    return resp_text, status

@app.route("/hello/<name>")
def hello(name):
    start = time.time()
    with tracer.start_as_current_span("hello-handler") as span:
        # add a trace attribute
        span.set_attribute("app.user_name", name)
        time.sleep(0.03)
        resp_text = f"Hello {name}!\n"
        status = 200

    REQUESTS.labels(path="/hello", method="GET", status=str(status)).inc()
    REQ_LATENCY.labels(path="/hello", method="GET").observe(time.time() - start)

    log.info(logfmt(
        event="request",
        path="/hello",
        method="GET",
        status=status,
        name=name,
        duration_ms=round((time.time() - start) * 1000, 1),
        client_ip=request.remote_addr
    ))
    return resp_text, status

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    # Run on 0.0.0.0 so Docker can expose it
    app.run(host="0.0.0.0", port=8000)
