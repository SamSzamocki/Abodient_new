"""
OpenTelemetry configuration for Langfuse tracing.
This provides automatic instrumentation of LangChain agents.
"""
import os
import base64
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from openinference.instrumentation.langchain import LangChainInstrumentor

def setup_telemetry():
    """
    Set up OpenTelemetry instrumentation to send traces to Langfuse.
    This automatically instruments all LangChain operations.
    """
    # Get Langfuse credentials
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-d9a88b84-cdab-44eb-bada-98f2c8567ab7")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-06a5516a-d683-44d4-b2b2-418ad43429f3")
    
    # Create authentication string for Langfuse
    LANGFUSE_AUTH = base64.b64encode(f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()).decode()
    
    # Set up OpenTelemetry environment variables
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://cloud.langfuse.com/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"
    
    # Create tracer provider and span processor
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
    
    # Instrument LangChain to automatically trace all operations
    LangChainInstrumentor().instrument(tracer_provider=trace_provider)
    
    print("[OTEL CONFIG] OpenTelemetry instrumentation initialized")
    print(f"[OTEL CONFIG] Sending traces to Langfuse with public key: {LANGFUSE_PUBLIC_KEY[:20]}...")
    
    return trace_provider
