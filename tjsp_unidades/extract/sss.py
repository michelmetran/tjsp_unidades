"""
Módulo de consulta de APIs expostas encontradas no site do TJSP
"""

import logging
import os
import threading

import requests

logger = logging.getLogger(__name__)


# Variável de thread local
_thread_local = threading.local()


def get_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
        # Adicione retentativas automáticas e headers se necessário
    return _thread_local.session


def get_default_workers() -> int:
    cpu_count = os.cpu_count() or 1
    # Limita entre 5 e 32 para evitar disparar muitas conexões de uma vez
    return min(32, cpu_count * 5)
