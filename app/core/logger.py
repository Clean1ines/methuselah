import logging
import structlog

def get_logger(name: str) -> structlog.BoundLogger:
    """
    Initializes and returns a structlog logger for explainable and structured telemetry.
    Replaces basic logging to satisfy debuggability requirements.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(name)

logger = get_logger("mafusail")
