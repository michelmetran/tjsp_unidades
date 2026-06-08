"""
_summary_

:raises Exception: _description_
:return: _description_
:rtype: _type_
"""

import open_geodata as geo
import pandas as pd
import requests
from requests_ip_rotator import ApiGateway


class ListarMunicipios:
    def __init__(self) -> None:
        pass

    def get_lista_municipios_tjsp(self, municipio) -> pd.DataFrame:
        """
        Pesquisa de municípios a partir de alguns caracteres.
        A função sempre retorna 10 itens.
        A cada caractere, o número de registros afunila!

        Exemplo de uso:
        df = get_lista_municipios_tjsp('Santos')

        :param municipio: _description_
        :type municipio: _type_
        :raises Exception: _description_
        """
        if len(municipio) < 3:
            raise Exception("A pesquisa de município deve ter mais de 3 caracteres")

        #
        r = requests.post(
            "https://www.tjsp.jus.br/AutoComplete/ListarMunicipios",
            json={"texto": municipio},
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
    def lista_municipios(self) -> list:
        """
        _summary_
        """
        # Cria Lista
        df_geo_mun = geo.load_dataset(db="sp", name="tab.municipio_nome")
        lista_municipios = list(df_geo_mun["municipio_nome"])
        return lista_municipios

    @property
    def n_caracteres_mun_max(self) -> int:
        n_caracteres_mun_max = max([len(x) for x in self.lista_municipios])
        return n_caracteres_mun_max

    @property
    def list_termos(self):
        # list_dfs = []
        list_termos = []
        for i in range(self.n_caracteres_mun_max)[3:]:
            lista_municipios_temp = list(
                set([mun[:i] for mun in self.lista_municipios if len(mun) >= i])
            )
            for search_text in lista_municipios_temp:
                list_termos.append(search_text)

        list_termos = list(set(list_termos))
        print(f"São {len(list_termos)} termos para pesquisa")
        return list_termos

    def request(self, access_key_id, access_key_secret) -> pd.DataFrame:
        # Cria Gateway
        gateway = ApiGateway(
            site="https://www.tjsp.jus.br",
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            regions=["sa-east-1"],
            verbose=True,
        )
        gateway.pool_connections = 5
        gateway.pool_maxsize = 5
        gateway.start()

        list_dfs = []

        try:
            # Cria Session
            session = requests.Session()
            session.mount(prefix="https://www.tjsp.jus.br", adapter=gateway)

            # Em 23.01.2025 tentei o uso do API
            for term in self.list_termos:
                df_temp = self.get_lista_municipios_tjsp(municipio=term)
                list_dfs.append(df_temp)

            # Crio a tabela
            df = pd.concat(
                objs=list_dfs,
                ignore_index=True,
            )

        except Exception as e:
            print(e)

        finally:
            # Encerra o worker
            gateway.shutdown()

        self.df_tjsp = df

    @property
    def municipios_tjsp(self) -> pd.DataFrame:

        if not isinstance(self.df_tjsp, pd.DataFrame):
            raise Exception("Precisa ser uma tabela")

        #
        df = self.df_tjsp

        # Ajusta a tabela
        df = df.drop_duplicates()
        df = df.sort_values(by="municipio_tjsp")
        df = df.iloc[df["municipio_tjsp"].str.normalize("NFKD").argsort()]
        df = df.reset_index(drop=True)

        if len(df) != 645:
            raise Exception("Falta Município!")

        # Resultados
        return df


class MunicipiosTJSP:
    def __init__(self, df_municipios) -> None:
        self.df_municipios = df_municipios

    @property
    def nomes_corretos(self):
        """
        _summary_

        :return: _description_
        :rtype: _type_
        """
        df_geo_mun = geo.load_dataset(db="sp", name="tab.municipio_nome")

        # Results
        return df_geo_mun

    def agrega_nomes_corretos(
        self,
        dict_replace={
            "Estrela dOeste": "Estrela d'Oeste",
            "Luís Antônio": "Luiz Antônio",
            "Florínia": "Florínea",
        },
    ):
        """
        _summary_

        :param dict_replace: _description_, defaults to { "Estrela dOeste": "Estrela d'Oeste", "Luís Antônio": "Luiz Antônio", "Florínia": "Florínea", }
        :type dict_replace: dict, optional
        :raises Exception: _description_
        :raises Exception: _description_
        """
        # Checa se temos uma tabela
        if not isinstance(self.nomes_corretos, pd.DataFrame):
            raise Exception("Precisa chamar tabela antes")

        # Crio Cópia da Coluna
        self.df_municipios["municipio_tjsp_corrigido"] = self.df_municipios[
            "municipio_tjsp"
        ]

        # Renomeia Municípios com Dicionário
        self.df_municipios["municipio_tjsp_corrigido"] = self.df_municipios[
            "municipio_tjsp_corrigido"
        ].replace(dict_replace)

        # Merge
        df_municipios = pd.merge(
            left=self.nomes_corretos,
            right=self.df_municipios,
            left_on="municipio_nome",
            right_on="municipio_tjsp_corrigido",
            how="left",
        )

        # Encontre erros
        df_temp = df_municipios[df_municipios["municipio_tjsp"].isnull()]
        if len(df_temp) > 0:
            print(df_temp)
            raise Exception("tratar")

        self.df_municipios = df_municipios

    @property
    def municipios(self):
        """
        Função para criar a tabela, tratando os dados

        :return: _description_
        :rtype: _type_
        """
        # Deleta Colunas
        df_municipios = self.df_municipios.drop(
            labels="municipio_nome",
            axis="columns",
            inplace=False,
            errors="ignore",
        )

        # Reordena
        df_municipios = df_municipios[
            [
                "id_municipio",
                "id_municipio_tjsp",
                "municipio_nome",
                "municipio_tjsp",
                "municipio_tjsp_corrigido",
            ]
        ]
        return df_municipios
