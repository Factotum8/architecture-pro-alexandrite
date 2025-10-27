from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# --- OpenTelemetry setup ---
resource = Resource.create({"service.name": "service-b"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces"))
)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI(title="service-b")
FastAPIInstrumentor.instrument_app(app)  # авто-спаны по HTTP серверу

@app.get("/quote")
def quote():
    with tracer.start_as_current_span("build-quote") as span:
        msg = "Here is a quote from service-b"
        span.set_attribute("custom.msg_len", len(msg))
        return {"quote": msg}
