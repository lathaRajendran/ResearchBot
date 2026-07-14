import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

# 1. Standard Logging Setup (Structured for OTel parity)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [TraceID: %(otelTraceID)s SpanID: %(otelSpanID)s] %(name)s - %(message)s'
)

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

logger = logging.getLogger("research-bot")
logger.addFilter(OTelLogFilter())

# 2. Tracing Setup
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("research-bot-tracer")

# Console span exporter for verification
span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

# 3. Metrics Setup
# Set a low export interval (e.g., 5 seconds) to demonstrate metrics output in local console logs
metric_reader = PeriodicExportingMetricReader(
    ConsoleMetricExporter(),
    export_interval_millis=5000
)
metrics.set_meter_provider(MeterProvider(metric_readers=[metric_reader]))
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
