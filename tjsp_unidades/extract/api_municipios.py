"""
Módulo de consulta da API "AutoComplete/ListarMunicipios" expostas encontradas no site do TJSP
"""

import concurrent.futures
import logging

import open_geodata as geo
import pandas as pd
from bs4 import BeautifulSoup
from more_itertools import one

from .sss import get_default_workers, get_session

logger = logging.getLogger(__name__)


class ListarMunicipios:
    def __init__(self) -> None:
        """
        *Endpoint* para `ListarMunicipios` do TJSP.
        """
        # ddd
        self.df_municipios_geo = geo.load_dataset(db="sp", name="tab.municipio_nome")

        # Cria Lista com Nomes de Municípios
        self.lista_municipios = list(self.df_municipios_geo["municipio_nome"])

    def get_lista_municipios_tjsp(self, termo: str) -> pd.DataFrame:
        """
        Pesquisa de municípios a partir de alguns caracteres.
        A função sempre retorna 10 itens.
        A cada caractere, o número de registros "afunila" os resultados.

        Exemplo de uso:
        df = get_lista_municipios_tjsp(termo='Sant')

        :param termo: Termo para pesquisa. Deve ser o trecho do nome de um município.
        :raises Exception: _description_
        """
        if len(termo) < 3:
            raise Exception("A pesquisa de município deve ter mais de 3 caracteres")

        # Create Session
        session = get_session()
        r = session.post(
            "https://www.tjsp.jus.br/AutoComplete/ListarMunicipios",
            json={"texto": termo},
            timeout=60,
        )
        if r.json() == "listaVazia":
            return pd.DataFrame()

        else:
            df = pd.DataFrame(r.json())
            df = df.rename(
                mapper={
                    "Codigo": "id_municipio_tjsp",
                    "Descricao": "municipio_tjsp",
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
        return max([len(x) for x in self.lista_municipios])

    @property
    def list_termos(self):
        """
        Cria lista de termos a serem pesquisados

        :return: Lista de termos
        """

        # Cria Lista de Termos a sere pesquisados
        list_termos = []
        for i in range(self.n_caracteres_mun_max)[3:]:
            lista_municipios_temp = list(
                set([mun[:i] for mun in self.lista_municipios if len(mun) >= i])
            )
            for search_text in lista_municipios_temp:
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

        # MAX_THREADS = 5
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_term = {
                executor.submit(self.get_lista_municipios_tjsp, term): term
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
            self.df_municipios_tjsp = pd.concat(results, ignore_index=True)

            # Faz os ajustes na tabela
            self._transform_municipios_tjsp()

            # Corrige nomes de Municípios
            self._fix_names()

        else:
            self.df_municipios_tjsp = pd.DataFrame()

        return self.df_municipios_tjsp

    # def request_aws(self, access_key_id, access_key_secret) -> pd.DataFrame:
    #     # Cria Gateway
    #     gateway = ApiGateway(
    #         site="https://www.tjsp.jus.br",
    #         access_key_id=access_key_id,
    #         access_key_secret=access_key_secret,
    #         regions=["sa-east-1"],
    #         verbose=True,
    #     )
    #     gateway.pool_connections = 5
    #     gateway.pool_maxsize = 5
    #     gateway.start()

    #     try:
    #         # Cria Session
    #         with requests.Session() as session:
    #             session.mount(prefix="https://www.tjsp.jus.br", adapter=gateway)
    #             list_dfs = []
    #             for termo in self.list_termos:
    #                 df_temp = self.get_lista_municipios_tjsp(termo=termo)
    #                 list_dfs.append(df_temp)

    #             self.df_tjsp = pd.concat(objs=list_dfs, ignore_index=True)

    #     except requests.RequestException as e:
    #         # Captura específica para erros de HTTP/Conexão
    #         raise RuntimeError(f"Erro de conexão com o TJSP: {e}") from e

    #     finally:
    #         # Encerra o worker
    #         gateway.shutdown()

    def _transform_municipios_tjsp(self) -> pd.DataFrame:
        """
        Faz ajustes na tabela
        """

        if not isinstance(self.df_municipios_tjsp, pd.DataFrame):
            raise TypeError("Precisa ser uma tabela")

        # Remove Duplicados
        self.df_municipios_tjsp = self.df_municipios_tjsp.drop_duplicates()

        # Ordena a tabela
        self.df_municipios_tjsp = self.df_municipios_tjsp.iloc[
            self.df_municipios_tjsp["municipio_tjsp"].str.normalize("NFKD").argsort()
        ]

        # Reseta Índice
        self.df_municipios_tjsp = self.df_municipios_tjsp.reset_index(drop=True)

        # Aplica strip em tudo
        self.df_municipios_tjsp = self.df_municipios_tjsp.map(
            lambda x: x.strip() if isinstance(x, str) else x
        )

        if len(self.df_municipios_tjsp) != 645:
            raise RuntimeError(
                f"Está faltando município. Temos {len(self.df_municipios_tjsp)} municipíos."
            )

        # Resultados
        return self.df_municipios_tjsp

    def _fix_names(
        self,
        dict_replace={
            # Nome Errado (TJSP): Nome Correto
            "Estrela dOeste": "Estrela d'Oeste",
            "Luís Antônio": "Luiz Antônio",
            "Florínia": "Florínea",
        },
    ) -> pd.DataFrame:
        """
        Ajusto o nome dos municípios de acordo com a tabela existente no projeto [open-geodata](https://github.com/michelmetran/open-geodata).

        :param dict_replace: _description_, defaults to { "Estrela dOeste": "Estrela d'Oeste", "Luís Antônio": "Luiz Antônio", "Florínia": "Florínea", }
        :return: _description_
        """
        # Crio Cópia da Coluna
        self.df_municipios_tjsp["municipio_tjsp_corrigido"] = self.df_municipios_tjsp[
            "municipio_tjsp"
        ]

        # Renomeia Municípios com Dicionário
        self.df_municipios_tjsp["municipio_tjsp_corrigido"] = self.df_municipios_tjsp[
            "municipio_tjsp_corrigido"
        ].replace(dict_replace)

        # Merge
        self.df_municipios_tjsp = pd.merge(
            left=self.df_municipios_geo,
            right=self.df_municipios_tjsp,
            left_on="municipio_nome",
            right_on="municipio_tjsp_corrigido",
            how="left",
        )

        # Deleta Colunas
        self.df_municipios_tjsp = self.df_municipios_tjsp.drop(
            labels="municipio_nome",
            axis="columns",
            inplace=False,
            errors="ignore",
        )
        # Renomeia Colunas
        self.df_municipios_tjsp = self.df_municipios_tjsp.rename(
            {"id_municipio": "id_municipio_ibge"},
            axis="columns",
        )

        # Encontre erros
        mask = self.df_municipios_tjsp["municipio_tjsp"].isnull()
        df_temp = self.df_municipios_tjsp[mask]
        if len(df_temp) > 0:
            print(df_temp)
            raise RuntimeError("Tratar")

        # Reordena
        self.df_municipios_tjsp = self.df_municipios_tjsp[
            [
                "id_municipio_ibge",
                "id_municipio_tjsp",
                # "municipio_nome",
                "municipio_tjsp",
                "municipio_tjsp_corrigido",
            ]
        ]

        return self.df_municipios_tjsp


class ListarUnidades:
    def __init__(
        self,
    ) -> None:

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
                "imoveis": lista_unidades,
            }
        )

    def get_unidades_batch(self, list_id_tjsp: list, max_workers=None) -> pd.DataFrame:
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
            self.df_unidades = pd.concat(
                objs=results,
                ignore_index=True,
            )
            self.df_unidades = self.df_unidades.map(
                lambda x: x.strip() if isinstance(x, str) else x
            )

        else:
            self.df_unidades = pd.DataFrame()

        return self.df_unidades
