import requests
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# --- OpenTelemetry setup ---
resource = Resource.create({"service.name": "service-a"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces"))
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI(title="service-a")
FastAPIInstrumentor.instrument_app(app)      # авто-спаны по HTTP серверу
RequestsInstrumentor().instrument()          # ВАЖНО: чтобы прокидывался tracecontext в запросы

@app.get("/work")
def work():
    with tracer.start_as_current_span("call-service-b") as span:
        resp = requests.get("http://service-b:8081/quote", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        span.set_attribute("downstream.ok", True)
        return {"service_a": "hello", "from_b": data}
