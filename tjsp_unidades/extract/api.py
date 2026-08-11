"""
Módulo de consulta de APIs expostas encontradas no site do TJSP
"""

import concurrent.futures
import logging
import os
import threading

import open_geodata as geo
import pandas as pd
import requests
from requests_ip_rotator import ApiGateway

logger = logging.getLogger(__name__)


# Variável de thread local
_thread_local = threading.local()


def get_default_workers() -> int:
    cpu_count = os.cpu_count() or 1
    # Limita entre 5 e 32 para evitar disparar muitas conexões de uma vez
    return min(32, cpu_count * 5)


def get_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
        # Adicione retentativas automáticas e headers se necessário
    return _thread_local.session


class ListarMunicipios:
    def __init__(self) -> None:
        """
        *Endpoint* para `ListarMunicipios` do TJSP.
        """

        self.df_municipios_geo = geo.load_dataset(db="sp", name="tab.municipio_nome")

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
        # Cria Lista com Nomes de Municípios
        lista_municipios = list(self.df_municipios_geo["municipio_nome"])

        # Número de Caracteres
        n_caracteres_mun_max = max([len(x) for x in lista_municipios])
        return n_caracteres_mun_max

    @property
    def list_termos(self):
        """
        Cria lista de termos a serem pesquisados

        :return: Lista de termos
        """
        # Cria Lista com Nomes de Municípios
        lista_municipios = list(self.df_municipios_geo["municipio_nome"])

        # Cria Lista de Termos a sere pesquisados
        list_termos = []
        for i in range(self.n_caracteres_mun_max)[3:]:
            lista_municipios_temp = list(
                set([mun[:i] for mun in lista_municipios if len(mun) >= i])
            )
            for search_text in lista_municipios_temp:
                list_termos.append(search_text)

        list_termos = list(filter(None, set(list_termos)))
        print(f"São {len(list_termos)} termos para pesquisa")
        return list_termos

    def request(self, max_workers) -> pd.DataFrame:
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
