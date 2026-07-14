import logging
from dotenv import load_dotenv
# Load environment variables at the very beginning of imports
load_dotenv()

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

# 1. Standard Logging Setup (Structured for OTel parity)
class OTelLogFilter(logging.Filter):
    """
    Injects active OpenTelemetry TraceID and SpanID into standard logging records.
    """
    def filter(self, record):
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            ctx = span.get_span_context()
            record.otelTraceID = format(ctx.trace_id, "032x")
            record.otelSpanID = format(ctx.span_id, "016x")
        else:
            record.otelTraceID = "0" * 32
            record.otelSpanID = "0" * 16
        return True

# Create a handler and assign filter + formatter globally
handler = logging.StreamHandler()
handler.addFilter(OTelLogFilter())
handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] [TraceID: %(otelTraceID)s SpanID: %(otelSpanID)s] %(name)s - %(message)s'
))

root_logger = logging.getLogger()
root_logger.handlers = [handler]
root_logger.setLevel(logging.INFO)

logger = logging.getLogger("research-bot")

import os
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Create standard resource attributes (sets the Service Name in Jaeger UI)
resource = Resource.create(attributes={"service.name": "research-bot"})

# 2. Tracing Setup
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer("research-bot-tracer")

# Load environment variables to check for Jaeger OTLP config
jaeger_enabled = os.getenv("JAEGER_ENABLED", "false").lower() == "true"
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

if jaeger_enabled:
    # Use BatchSpanProcessor and OTLPSpanExporter to send spans to Jaeger OTLP collector
    span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
    trace.get_tracer_provider().add_span_processor(span_processor)
    print(f"OpenTelemetry: Sending traces to Jaeger OTLP receiver at {otlp_endpoint}")
else:
    # Console span exporter for verification
    span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
    trace.get_tracer_provider().add_span_processor(span_processor)

# 3. Metrics Setup
prometheus_enabled = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8000"))

if prometheus_enabled:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from prometheus_client import start_http_server
    
    # Start Prometheus scrape client server
    start_http_server(port=prometheus_port)
    metric_reader = PrometheusMetricReader()
    print(f"OpenTelemetry Metrics: Exposing Prometheus scrape endpoint on http://localhost:{prometheus_port}/metrics")
else:
    # Set a low export interval (e.g., 5 seconds) to demonstrate metrics output in local console logs
    metric_reader = PeriodicExportingMetricReader(
        ConsoleMetricExporter(),
        export_interval_millis=5000
    )
    print("OpenTelemetry Metrics: Exporting metrics to console logs")

metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))
meter = metrics.get_meter("research-bot-meter")

# Define OTel Metrics
query_counter = meter.create_counter(
    name="research_queries_total",
    description="Total number of research queries processed",
    unit="1",
)

query_latency = meter.create_histogram(
    name="query_processing_duration_seconds",
    description="Duration of query processing flow in seconds",
    unit="s",
)

search_counter = meter.create_counter(
    name="web_searches_total",
    description="Total number of web searches executed",
    unit="1",
)
