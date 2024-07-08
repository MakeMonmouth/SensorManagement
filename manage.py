#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from dotenv import load_dotenv

from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor


def main():
    """Run administrative tasks."""
    load_dotenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensors.settings")
    DjangoInstrumentor().instrument()
    Psycopg2Instrumentor().instrument(enable_commenter=True, commenter_options={})
    LoggingInstrumentor().instrument(set_logging_format=True)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
