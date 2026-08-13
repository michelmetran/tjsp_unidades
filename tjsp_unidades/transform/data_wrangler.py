"""
_summary_
"""

import duckdb

from tjsp_unidades.extract.api_imovel import Imovel
from tjsp_unidades.extract.api_municipios import Municipio
from tjsp_unidades.extract.pagina import QuemSomos


class Transform:
    def __init__(
        self,
        quem_somos: QuemSomos,
        municipios: Municipio,
        imovel: Imovel,
    ) -> None:
        # Parâmetros
        self.quem_somos = quem_somos
        self.municipios = municipios
        self.imovel = imovel

        self.con = duckdb.connect()

        # Quem Somos
        self.con.register("raj", self.quem_somos.rajs)
        self.con.register("cj", self.quem_somos.cjs)
        self.con.register("comarcas", self.quem_somos.comarcas)

        # Município
        self.con.register("municipio_search", self.municipios.df_search)
        self.con.register("municipio_detalhes", self.municipios.df_detalhes)

        # Imóvel
        # self.con.register("imovel_search", self.imovel.df_search)
        self.con.register("imovel_detalhes", self.imovel.df_detalhes)

    @property
    def df_imovel(self):

        stmt = """
            SELECT
                -- Identificador
                id_imovel,
                municipio_search.id_municipio_ibge,
                municipio_search.id_municipio_tjsp,
                imovel,

                -- Contato
                telefone,
                fax,
                email,

                --cj,
                --entrancia, -- Acho que é atributo da Comarca
                --comarca_tjsp,

                -- Atributos
                dist_capital,
                tensao_eletrica,

                -- Endereço
                endereco_lougradouro AS lougradouro,
                endereco_cep AS cep,
                --endereco_municipio,
                municipio_search.municipio_tjsp_corrigido AS municipio_tjsp_corrigido,
                endereco_uf AS uf,

                -- Setores
                num_varas_instaladas

            FROM imovel_detalhes
            LEFT JOIN municipio_search
            ON municipio_search.municipio_tjsp = imovel_detalhes.endereco_municipio

            WHERE 1=1
                -- Confiro que o JOIN é perfeito...
                --AND municipio_search.id_municipio_ibge IS NULL
        """

        # Faz a consulta
        df_imoveis = self.con.sql(stmt).df()

        # Results
        df_imoveis.info()
        df_imoveis.head()
        return df_imoveis

    @property
    def df_municipio(self):

        stmt = """
            SELECT
                DISTINCT
                -- Identificadores
                municipio_search.id_municipio_ibge,
                municipio_detalhes.id_municipio_tjsp,
                temp.id_comarca_ibge,

                -- Outros
                municipio_detalhes.municipio_tjsp,
                municipio_search.municipio_tjsp_corrigido,
                municipio_detalhes.comarca_tjsp,
                temp.comarca_tjsp_corrigido,
                municipio_detalhes.comarca_sede

            FROM municipio_detalhes

            LEFT JOIN municipio_search
            ON municipio_search.id_municipio_tjsp = municipio_detalhes.id_municipio_tjsp

            LEFT JOIN (
            SELECT
                DISTINCT
                -- Identificadores
                municipio_search.id_municipio_ibge AS id_comarca_ibge,
                municipio_detalhes.comarca_tjsp,

                -- Outros
                municipio_search.municipio_tjsp_corrigido AS comarca_tjsp_corrigido

            FROM municipio_detalhes

            LEFT JOIN municipio_search
            ON municipio_search.id_municipio_tjsp = municipio_detalhes.id_municipio_tjsp

            WHERE 1=1
                AND municipio_detalhes.comarca_sede = 1
                --AND municipio_detalhes.comarca_tjsp != municipio_search.municipio_tjsp_corrigido
            ) AS temp
            ON temp.comarca_tjsp = municipio_detalhes.comarca_tjsp

            WHERE 1=1

            ORDER BY temp.id_comarca_ibge
        """

        # Faz a consulta
        df_municipios = self.con.sql(stmt).df()

        # Results
        df_municipios.info()
        df_municipios.head()

        return df_municipios

    @property
    def df_comarca(self):
        # Tabela de Comarca
        stmt = """
            SELECT
                DISTINCT
                -- Identificadores
                municipio_search.id_municipio_ibge AS id_comarca_ibge,
                comarcas.id_cj,

                -- Comarca
                municipio_detalhes.comarca_tjsp,
                municipio_search.municipio_tjsp_corrigido AS comarca_tjsp_corrigido

            FROM municipio_detalhes

            LEFT JOIN municipio_search
            ON municipio_search.id_municipio_tjsp = municipio_detalhes.id_municipio_tjsp

            LEFT JOIN comarcas
            ON comarcas.comarca_tjsp = municipio_detalhes.comarca_tjsp

            WHERE 1=1
                AND municipio_detalhes.comarca_sede = 1
                --AND municipio_detalhes.comarca_tjsp != municipio_search.municipio_tjsp_corrigido

                -- Circunscrição Judiciária é Nula
                --AND comarcas.id_cj IS NULL
        """

        # Faz a consulta
        df_comarcas = self.con.sql(stmt).df()

        # Results
        df_comarcas.info()
        df_comarcas.head()

        return df_comarcas

    @property
    def df_cj(self):
        stmt = """
            SELECT
                *
            FROM cj
            WHERE 1=1
        """

        # Faz a consulta
        df_cjs = self.con.sql(stmt).df()

        # Results
        df_cjs.info()
        df_cjs.head()

        return df_cjs

    @property
    def df_raj(self):
        stmt = """
            SELECT
                *
            FROM raj
            WHERE 1=1
        """

        # Faz a consulta
        df_raj = self.con.sql(stmt).df()

        # Results
        df_raj.info()
        df_raj.head()

        return df_raj
