"""
OpenTelemetry setup — stubbed in Phase 1, wired fully in Phase 5.
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter


_tracer_provider: TracerProvider | None = None


def configure_telemetry(service_name: str = "org-agent-backend") -> None:
    global _tracer_provider
    provider = TracerProvider()
    # Phase 1: log spans to stdout; Phase 5 replaces with OTLP exporter
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _tracer_provider = provider


def get_tracer(name: str = "org-agent") -> trace.Tracer:
    return trace.get_tracer(name)
