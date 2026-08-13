"""
Módulo de consulta de APIs expostas encontradas no site do TJSP
"""

import logging
import os
import tempfile
import threading
from pathlib import Path

import requests_cache

logger = logging.getLogger(__name__)


# Variável de thread local
_thread_local = threading.local()


def get_cache_path(project_name: str, cache_filename: str = "tjsp_cache") -> str:
    """
    Cria e retorna o caminho completo para o arquivo de cache
    dentro do diretório temporário do SO.
    """
    # Localiza o diretório temporário do SO (ex: /tmp ou C:\Users\...\AppData\Local\Temp)
    temp_dir = Path(tempfile.gettempdir()) / project_name

    # Garante que a pasta temporária do projeto exista
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Retorna o caminho completo (ex: /tmp/tjsp_unidades/tjsp_cache.sqlite)
    return str(temp_dir / cache_filename)


def get_session() -> requests_cache.CachedSession:
    """
    Retorna uma sessão com cache em disco (SQLite) e isolada por thread.
    """
    if not hasattr(_thread_local, "session"):
        # Caminho do cache: <pasta_temp>/tjsp_unidades/tjsp_cache.sqlite
        cache_path = get_cache_path(
            project_name="tjsp_unidades", cache_filename="tjsp_cache"
        )

        # Cria a sessão com cache
        _thread_local.session = requests_cache.CachedSession(
            # Nome do arquivo SQLite gerado (tjsp_cache.sqlite)
            cache_name=cache_path,
            backend="sqlite",
            expire_after=86400 * 3,  # Duração do cache: 3 dias (em segundos)
            allowable_methods=("GET", "POST"),  # O TJSP usa POST para buscar e detalhar
        )
    return _thread_local.session


def get_default_workers() -> int:
    cpu_count = os.cpu_count() or 1
    # Limita entre 5 e 32 para evitar disparar muitas conexões de uma vez
    return min(32, cpu_count * 5)
