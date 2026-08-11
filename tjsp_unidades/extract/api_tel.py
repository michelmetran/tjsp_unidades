"""
ListaTelefonica
"""

import concurrent.futures
import logging
import threading

import pandas as pd
import requests
from bs4 import BeautifulSoup
from more_itertools import one

from .api import get_default_workers

# Variável de thread local
_thread_local = threading.local()

logger = logging.getLogger(__name__)


def get_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
        # Adicione retentativas automáticas e headers se necessário
    return _thread_local.session


class ListarUnidades:
    def __init__(
        self,
    ) -> None:
        # self.df_mun = df_mun
        self.df_unidades = None

    def get_unidades(self, id_municipio_tjsp: int) -> pd.DataFrame:
        """
        Pega a lista de unidades (Fóruns) de um determinado Município,
        a partir do Código do Município do TJSP

        :param cod_municipio: _description_
        :return: _description_
        """
        # Requests
        # Create Session
        session = get_session()

        r = session.post(
            "https://www.tjsp.jus.br/ListaTelefonica/RetornarResultadoBusca",
            json={"parmsEntrada": id_municipio_tjsp, "codigoTipoBusca": 1},
            timeout=60,
        )

        # BS4
        soup = BeautifulSoup(r.text, "html.parser")
        text_comarca = soup.find_all("h4")
        if text_comarca == []:
            raise RuntimeError("Erro")

        else:
            text_comarca = one(text_comarca)
            text_comarca = text_comarca.text

            comarca = text_comarca.split(" - ")[0]
            raj = text_comarca.strip().split(" - ")[-1]
            # print(raj)

            # comarca = comarca.split('está jurisdicionado à Comarca ')
            comarca = comarca.replace("Município ", "")
            comarca = comarca.replace("está jurisdicionado à Comarca", " | ")
            comarca = comarca.replace("da Comarca", " | ")
            # print(comarca)

            mun = comarca.strip().split(" | ")[0]
            com = comarca.strip().split(" | ")[-1]

            if mun.strip() == com.strip():
                comarca_sede = 1

            else:
                comarca_sede = 0

            # print(text_comarca)
            # print(text_comcarca.split('jurisdicionado à comarca '))

        lista_unidades = [x.text for x in soup.find_all("span")]

        return pd.DataFrame(
            {
                "id_municipio_tjsp": id_municipio_tjsp,
                "raj": raj.strip(),
                "municipio_tjsp": mun.strip(),
                "comarca_tjsp": com.strip(),
                "comarca_sede": comarca_sede,
                "unidades": lista_unidades,
            }
        )

    def get_unidades_batch(self, list_id_tjsp: list, max_workers) -> pd.DataFrame:
        """
        _summary_

        :param df_mun: _description_
        :type df_mun: _type_
        :return: _description_
        :rtype: pd.DataFrame
        """

        # Se o usuário não passar o parâmetro, calcula o padrão dinâmico
        if max_workers is None:
            max_workers = get_default_workers()

        # Deduplica e remove valores nulos/inválidos da lista de IDs antes de disparar as threads
        ids_limpos = list(filter(None, set(list_id_tjsp)))

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 1. Submete as tarefas mapeando cada Future ao seu id_tjsp correspondente
            future_to_id = {
                executor.submit(self.get_unidades, id_tjsp): id_tjsp
                for id_tjsp in ids_limpos
            }

            # 2. Processa conforme completam (as_completed) para isolar erros
            for future in concurrent.futures.as_completed(future_to_id):
                id_tjsp = future_to_id[future]
                try:
                    res = future.result()
                    # Valida se o retorno é um DataFrame válido e não-vazio
                    if isinstance(res, pd.DataFrame) and not res.empty:
                        results.append(res)

                except Exception as exc:
                    logger.error(f"Erro ao processar o ID '{id_tjsp}': {exc}")

        # Concatena apenas DataFrames válidos
        if results:
            self.df_unidades = pd.concat(results, ignore_index=True)
            self.df_unidades = self.df_unidades.map(
                lambda x: x.strip() if isinstance(x, str) else x
            )

        else:
            self.df_unidades = pd.DataFrame()

        return self.df_unidades
