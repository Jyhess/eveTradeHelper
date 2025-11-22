"""
Setup OpenTelemetry tracing with Zipkin exporter
"""

import logging
import os

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logger.warning("OpenTelemetry not available. Install opentelemetry packages to enable tracing.")


def setup_tracing(service_name: str = "eve-trade-helper", app=None) -> None:
    """
    Setup OpenTelemetry tracing with Zipkin exporter

    Args:
        service_name: Name of the service for tracing
        app: FastAPI application instance (optional, will instrument all FastAPI apps if None)
    """
    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not available. Tracing disabled.")
        return

    zipkin_endpoint = os.getenv("ZIPKIN_ENDPOINT", "http://zipkin:9411/api/v2/spans")
    logger.info(f"ZIPKIN_ENDPOINT: {zipkin_endpoint}")

    resource = Resource.create({"service.name": service_name})

    trace.set_tracer_provider(TracerProvider(resource=resource))

    zipkin_exporter = ZipkinExporter(endpoint=zipkin_endpoint)

    span_processor = BatchSpanProcessor(zipkin_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    if app:
        FastAPIInstrumentor().instrument_app(app)
    else:
        FastAPIInstrumentor().instrument()

    HTTPXClientInstrumentor().instrument()

    logger.info(f"OpenTelemetry tracing configured with Zipkin at {zipkin_endpoint}")
