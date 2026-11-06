"""OpenTelemetry distributed tracing setup and ADK telemetry plugins."""

import logging
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.adk.plugins.auto_tracing_plugin import AutoTracingPlugin
from .hipaa_sanitizer import sanitize_phi_dict
from ...config.settings import settings

logger = logging.getLogger("patient_onboarding.telemetry")


def setup_telemetry(service_name: Optional[str] = None) -> trace.Tracer:
    """Initialize OpenTelemetry tracer provider and exporter."""
    svc_name = service_name or settings.otel_service_name
    resource = Resource.create({SERVICE_NAME: svc_name})
    provider = TracerProvider(resource=resource)

    # In development/test mode, export spans to Console or in-memory
    if settings.enable_console_tracing:
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    return trace.get_tracer(svc_name)


def get_adk_telemetry_plugins() -> list:
    """Return standard ADK observability and logging plugins."""
    plugins = [
        LoggingPlugin(),
        AutoTracingPlugin(
            name="HospitalOnboardingTracing",
            extra_scope_prefixes=("src.tools", "src.workflow", "src.agents")
        ),
    ]
    return plugins


class TraceContextManager:
    """Helper context manager to record custom clinical execution spans."""

    def __init__(self, tracer: trace.Tracer, span_name: str, attributes: Optional[dict] = None) -> None:
        self.tracer = tracer
        self.span_name = span_name
        self.attributes = sanitize_phi_dict(attributes or {})

    def __enter__(self):
        self.span = self.tracer.start_span(self.span_name)
        for k, v in self.attributes.items():
            self.span.set_attribute(str(k), str(v))
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.span.record_exception(exc_val)
            self.span.set_status(trace.StatusCode.ERROR, str(exc_val))
        else:
            self.span.set_status(trace.StatusCode.OK)
        self.span.end()
