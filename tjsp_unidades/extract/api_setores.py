"""
Módulo de consulta de APIs expostas encontradas no site do TJSP
"""

import concurrent.futures
import logging

import pandas as pd
from bs4 import BeautifulSoup

from .api_municipios import ListarUnidades
from .sss import get_default_workers, get_session

logger = logging.getLogger(__name__)


class ListarSetores:
    def __init__(self, listar_unidades: ListarUnidades):
        self.listar_unidades = listar_unidades

        self.lista_unidade = list(self.listar_unidades.df_unidades["unidades"])

    def get_setores(self, termo: str) -> pd.DataFrame:
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
            "https://www.tjsp.jus.br/AutoComplete/ListarSetores",
            json={"texto": termo},
            timeout=60,
        )
        if r.json() == "listaVazia":
            return pd.DataFrame()

        else:
            df = pd.DataFrame(r.json())
            df = df.rename(
                mapper={
                    "Codigo": "id_setor",
                    "Descricao": "setor_tjsp",
                },
                axis="columns",
            )
            return df

    @property
    def n_caracteres_mun_max(self) -> int:
        """
        Retorna o número de caracteres máximo de um município

        :return: Número de caracteres máximo
        """
        # Número de Caracteres
        return max([len(x) for x in self.lista_unidade])

    @property
    def list_termos(self):
        """
        Cria lista de termos a serem pesquisados

        :return: Lista de termos
        """
        # Cria Lista de Termos a sere pesquisados
        list_termos = []
        for i in range(self.n_caracteres_mun_max)[3:]:
            lista_temp = list(
                set([mun[:i] for mun in self.lista_unidade if len(mun) >= i])
            )
            for search_text in lista_temp:
                list_termos.append(search_text)

        # Aplica strip apenas se o item for string válida e remove itens vazios/None
        list_termos = [
            termo.strip() for termo in list_termos if termo and isinstance(termo, str)
        ]

        list_termos = list(filter(None, set(list_termos)))
        print(f"São {len(list_termos)} termos para pesquisa")
        return list_termos

    def request(self, max_workers=None) -> pd.DataFrame:
        """
        Faz a requisição para a API de todos os termos contidos na lista de termos
        """

        # Se o usuário não passar o parâmetro, calcula o padrão dinâmico
        if max_workers is None:
            max_workers = get_default_workers()

        # dddd
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_term = {
                executor.submit(self.get_setores, term): term
                for term in self.list_termos
            }

            # 3. Processa conforme completam (as_completed) para melhor tratamento de erros
            for future in concurrent.futures.as_completed(future_to_term):
                term = future_to_term[future]
                try:
                    res = future.result()
                    # Valida se o retorno é um DataFrame válido e não-vazio
                    if isinstance(res, pd.DataFrame) and not res.empty:
                        results.append(res)

                except Exception as exc:
                    logger.error(f"Erro ao processar o termo '{term}': {exc}")

        # 4. Concatena apenas DataFrames válidos
        if results:
            self.df_setores = pd.concat(
                objs=results,
                ignore_index=True,
            )

            # Faz os ajustes na tabela
            self._transform_municipios_tjsp()

            # Corrige nomes de Municípios
            # self._fix_names()

        else:
            self.df_setores = pd.DataFrame()

        return self.df_setores

    def _transform_municipios_tjsp(self) -> pd.DataFrame:
        """
        Faz ajustes na tabela
        """

        if not isinstance(self.df_setores, pd.DataFrame):
            raise TypeError("Precisa ser uma tabela")

        # Remove Duplicados
        self.df_setores = self.df_setores.drop_duplicates()
        # Ordena a tabela
        self.df_setores = self.df_setores.iloc[
            self.df_setores["setor_tjsp"].str.normalize("NFKD").argsort()
        ]

        # Reseta Índice
        self.df_setores = self.df_setores.reset_index(drop=True)

        # Aplica strip em tudo
        self.df_setores = self.df_setores.map(
            lambda x: x.strip() if isinstance(x, str) else x
        )

        # Resultados
        return self.df_setores


class SetoresBusca:
    def __init__(self) -> None:
        pass

    def get_setor(self, id_setor: int):

        # Create Session
        session = get_session()

        r = session.post(
            "https://www.tjsp.jus.br/ListaTelefonica/RetornarResultadoBusca",
            json={"parmsEntrada": id_setor, "codigoTipoBusca": 3},
            timeout=60,
        )

        # BS4
        # soup = BeautifulSoup(r.text, "html.parser")
        # text_comarca = soup.find_all("h4")
        # if text_comarca == []:
        #     raise RuntimeError("Erro")
        return r


class SetoresPorImovel:
    def __init__(self) -> None:
        pass

    def get_setores(self, id_imovel: int):

        # Create Session
        session = get_session()

        r = session.post(
            "https://www.tjsp.jus.br/ListaTelefonica/ObterSetoresPorImovel",
            json={"codigo": id_imovel},
            timeout=60,
        )

        # BS4
        # soup = BeautifulSoup(r.text, "html.parser")
        # text_comarca = soup.find_all("h4")
        # if text_comarca == []:
        #     raise RuntimeError("Erro")
        return r
