"""
Módulo de consulta de APIs expostas encontradas no site do TJSP
"""

import concurrent.futures
import logging
import re

import pandas as pd
from bs4 import BeautifulSoup

from .api_municipios import Municipio
from .sss import get_default_workers, get_session

logger = logging.getLogger(__name__)


class Imovel:
    def __init__(self, municipio: Municipio):
        self.municipio = municipio
        self._lista_imovel = list(self.municipio.df_detalhes["imovel"])

    def search(self, termo: str) -> pd.DataFrame:
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
            "https://www.tjsp.jus.br/AutoComplete/ListarImoveis",
            json={"texto": termo},
            timeout=60,
        )
        if r.json() == "listaVazia":
            return pd.DataFrame()

        else:
            df = pd.DataFrame(r.json())
            df = df.rename(
                mapper={
                    "Codigo": "id_imovel",
                    "Descricao": "imovel_tjsp",
                },
                axis="columns",
            )
            df = df.sort_values(by="id_imovel", inplace=False)
            return df

    @property
    def _n_caracteres_mun_max(self) -> int:
        """
        Retorna o número de caracteres máximo de um município

        :return: Número de caracteres máximo
        """
        # Número de Caracteres
        return max([len(x) for x in self._lista_imovel])

    @property
    def _list_termos(self):
        """
        Cria lista de termos a serem pesquisados

        :return: Lista de termos
        """
        # Cria Lista de Termos a serem pesquisados
        list_termos = []
        numero_minimo_caracteres = 4

        # Flattens a lista de "frases" em uma única lista de palavras
        list_imovel = [
            palavra.lower()
            for imovel in self._lista_imovel
            for palavra in imovel.split()
            if len(palavra) > numero_minimo_caracteres
        ]
        list_imovel = list(set(list_imovel))

        for i in range(self._n_caracteres_mun_max)[numero_minimo_caracteres:]:
            lista_temp = list(set([mun[:i] for mun in list_imovel if len(mun) >= i]))
            for search_text in lista_temp:
                list_termos.append(search_text)

        # Aplica strip apenas se o item for string válida e remove itens vazios/None
        list_termos = [
            termo.strip() for termo in list_termos if termo and isinstance(termo, str)
        ]

        list_termos = list(filter(None, set(list_termos)))
        print(f"São {len(list_termos)} termos para pesquisa")
        return list_termos

    def search_batch(self, max_workers=None) -> pd.DataFrame:
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
                executor.submit(self.search, termo): termo
                for termo in self._list_termos
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
            self.df_search = pd.concat(
                objs=results,
                ignore_index=True,
            )

            # Faz os ajustes na tabela
            self._transform_search()

        else:
            self.df_search = pd.DataFrame()

        return self.df_search

    def _transform_search(self) -> pd.DataFrame:
        """
        Faz ajustes na tabela
        """

        if not isinstance(self.df_search, pd.DataFrame):
            raise TypeError("Precisa ser uma tabela")

        # Remove Duplicados
        self.df_search = self.df_search.drop_duplicates()

        # Ordena a tabela
        self.df_search = self.df_search.iloc[
            self.df_search["imovel_tjsp"].str.normalize("NFKD").argsort()
        ]
        self.df_search = self.df_search.sort_values(by="id_imovel", inplace=False)

        # Reseta Índice
        self.df_search = self.df_search.reset_index(drop=True)

        # Aplica strip em tudo
        self.df_search = self.df_search.map(
            lambda x: x.strip() if isinstance(x, str) else x
        )

        # Resultados
        return self.df_search

    def detalhe(self, id_imovel: int):

        # Create Session
        session = get_session()

        r = session.post(
            "https://www.tjsp.jus.br/ListaTelefonica/RetornarResultadoBusca",
            json={"parmsEntrada": id_imovel, "codigoTipoBusca": 2},
            timeout=60,
        )

        # Create Dictionary
        dd = self._tratar_response(response=r, id_imovel=id_imovel)

        # Create Pandas
        return pd.DataFrame([dd])

    def detalhe_batch(self, max_workers=None) -> pd.DataFrame:
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

        list_id_tjsp = list(self.df_search["id_imovel"])

        # ssss
        list_id_tjsp = range(1200)

        # Deduplica e remove valores nulos/inválidos da lista de IDs antes de disparar as threads
        ids_limpos = list(filter(None, set(list_id_tjsp)))

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 1. Submete as tarefas mapeando cada Future ao seu id_tjsp correspondente
            future_to_id = {
                executor.submit(self.detalhe, id_tjsp): id_tjsp
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
            self.df_detalhes = pd.concat(
                objs=results,
                ignore_index=True,
            )

            self._transform_detalhes()

        else:
            self.df_detalhes = pd.DataFrame()

        return self.df_detalhes

    def obter_imovel(self, id_imovel: int):

        # Create Session
        session = get_session()

        r = session.post(
            "https://www.tjsp.jus.br/ListaTelefonica/ObterImovel",
            json={"codigo": id_imovel},
            timeout=60,
        )
        dd = self._tratar_response(response=r, id_imovel=id_imovel)
        return pd.DataFrame([dd])

    def _tratar_response(self, response, id_imovel):

        # BS4
        soup = BeautifulSoup(response.text, "html.parser")

        try:
            imovel = soup.find(name="h3", attrs={"id": "imovelNome"}).text.strip()

        except:
            imovel = "Sem nome"

        endereco = (
            soup.find("dt", string=re.compile(".*Endereço.*", flags=re.DOTALL))
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        telefone = (
            soup.find("dt", string=re.compile(".*Telefone.*", flags=re.DOTALL))
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        fax = (
            soup.find("dt", string=re.compile(".*Fax.*", flags=re.DOTALL))
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        email: str = (
            soup.find("dt", string=re.compile(".*E-mail.*", flags=re.DOTALL))
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        cj: str = (
            soup.find(
                "dt",
                string=re.compile(".*Circunscrição Judiciária.*", flags=re.DOTALL),
            )
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        num_varas_instaladas = (
            soup.find(
                "dt",
                string=re.compile(".*Número de Varas Instaladas.*", flags=re.DOTALL),
            )
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        entrancia = (
            soup.find("dt", string=re.compile(".*Entrância.*", flags=re.DOTALL))
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        # re.compile('.*Comarca.*', flags=re.DOTALL)
        comarca = (
            soup.find("dt", string=re.compile(".*Comarca.*", flags=re.DOTALL))
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        dist_capital = (
            soup.find(
                "dt", string=re.compile(".*Distância da Capital.*", flags=re.DOTALL)
            )
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        tensao_eletrica = (
            soup.find("dt", string=re.compile(".*Tensão Elétrica.*", flags=re.DOTALL))
            .parent.find(name="dd")
            .find(name="span")
            .text.strip()
        )

        tj_dict = {
            "id_imovel": id_imovel,
            "imovel": imovel,
            "endereco": endereco,
            "telefone": telefone,
            "fax": fax,
            "email": email,
            "cj": cj,
            "num_varas_instaladas": num_varas_instaladas,
            "entrancia": entrancia,
            "comarca_tjsp": comarca,
            "dist_capital": dist_capital,
            "tensao_eletrica": tensao_eletrica,
        }
        return tj_dict

    def _transform_detalhes(self) -> pd.DataFrame:
        """
        Faz ajustes na tabela
        """

        if not isinstance(self.df_detalhes, pd.DataFrame):
            raise TypeError("Precisa ser uma tabela")

        # Aplica strip em todo o dataframe
        self.df_detalhes = self.df_detalhes.map(
            lambda x: x.strip() if isinstance(x, str) else x
        )

        # Elimina os Duplicados
        self.df_detalhes = self.df_detalhes.drop_duplicates()

        # Elimina
        mask = (
            (self.df_detalhes["imovel"] == "")
            & (self.df_detalhes["telefone"] == "Não Informado")
            & (self.df_detalhes["fax"] == "Não Informado")
            & (self.df_detalhes["email"] == "Não Informado")
            & (self.df_detalhes["cj"] == "Não Informado")
            & (self.df_detalhes["entrancia"] == "Não Informado")
            & (self.df_detalhes["comarca_tjsp"] == "Não Informado")
            & (self.df_detalhes["dist_capital"] == "Não Informado")
            & (self.df_detalhes["tensao_eletrica"] == "Não Informado")
        )
        self.df_detalhes = self.df_detalhes[~mask]

        # Remove ; do fim da coluna Telefone
        self.df_detalhes["telefone"] = self.df_detalhes["telefone"].str.replace(
            r"\;$", "", regex=True
        )

        # Remove ; do fim da coluna Fax
        self.df_detalhes["fax"] = self.df_detalhes["fax"].str.replace(
            r"\;$", "", regex=True
        )

        self.df_detalhes[["endereco_lougradouro", "endereco_p2"]] = self.df_detalhes[
            "endereco"
        ].str.split(" - CEP ", n=1, expand=True)

        self.df_detalhes[["endereco_cep", "endereco_municipio", "endereco_uf"]] = (
            self.df_detalhes["endereco_p2"].str.split(" - ", n=3, expand=True)
        )

        # Remove Columns
        self.df_detalhes = self.df_detalhes.drop(
            labels=["endereco_p1", "endereco_p2", "endereco"],
            inplace=False,
            errors="ignore",
            axis="columns",
        )

        # Aplica strip em todo o dataframe
        self.df_detalhes = self.df_detalhes.map(
            lambda x: x.strip() if isinstance(x, str) else x
        )

        # Converte para Número
        # self.df_detalhes["dist_capital"] = pd.to_numeric(
        #     self.df_detalhes["dist_capital"].str.replace(" Km", "", regex=False),
        #     errors="coerce",
        # )
        # self.df_detalhes["dist_capital"] = (
        #     self.df_detalhes["dist_capital"]
        #     .str.extract(r"(\d+(?:\.\d+)?)")
        #     .astype(float)
        # )

        # self.df_detalhes["dist_capital"] = self.df_detalhes["dist_capital"].str.replace(
        #     "Não Informado", ""
        # )
        # self.df_detalhes["dist_capital"] = (
        #     self.df_detalhes["dist_capital"]
        #     .astype(str)
        #     .str.replace(r"(?i)\s*km\s*$", "", regex=True)  # remove "Km"
        #     .str.strip()
        #     .replace("", pd.NA)
        #     .astype(float)
        # )
        self.df_detalhes["dist_capital"] = (
            self.df_detalhes["dist_capital"]
            .str.extract(r"(\d+(?:\.\d+)?)")
            .astype(float)
        )

        # Converte para Número
        self.df_detalhes["num_varas_instaladas"] = self.df_detalhes[
            "num_varas_instaladas"
        ].astype(int)

        # Ordena
        self.df_detalhes = self.df_detalhes.sort_values(
            by="id_imovel",
            ascending=True,
        )

        # Reset Index
        self.df_detalhes = self.df_detalhes.reset_index(drop=True, inplace=False)

        # Remove Duplicados
        self.df_detalhes = self.df_detalhes.drop_duplicates()

        return self.df_detalhes
