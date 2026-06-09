"""
_summary_
"""

import concurrent.futures

import pandas as pd
import requests
from bs4 import BeautifulSoup
from more_itertools import one

from .small_functions import adjust_columns


class ListarUnidades:
    def __init__(
        self,
    ) -> None:
        # self.df_mun = df_mun
        self.df_com = None

    def get_lista_unidades_tjsp(self, id_municipio_tjsp: int):
        """
        Pega a lista de unidades (Fóruns) de um determinado Município,
        a partir do Código do Município do TJSP
        :param cod_municipio: _description_
        :type cod_municipio: _type_
        :return: _description_
        """
        # Requests
        r: requests.Response = requests.post(
            "https://www.tjsp.jus.br/ListaTelefonica/RetornarResultadoBusca",
            json={"parmsEntrada": id_municipio_tjsp, "codigoTipoBusca": 1},
            timeout=60,
        )

        # BS4
        soup = BeautifulSoup(r.text, "html.parser")
        text_comarca = soup.find_all("h4")
        if text_comarca == []:
            raise Exception("Erro")

        else:
            text_comarca = one(text_comarca)
            text_comarca = text_comarca.text

            #
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

    def get_comarcas(self, df_mun: pd.DataFrame) -> pd.DataFrame:
        """
        _summary_

        :param df_mun: _description_
        :type df_mun: _type_
        :return: _description_
        :rtype: pd.DataFrame
        """

        self.df_mun = df_mun

        # Lista Municípios
        list_id_tjsp = list(df_mun["id_municipio_tjsp"])

        if self.df_com is None:

            MAX_THREADS = 5
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_THREADS
            ) as executor:
                temp = executor.map(self.get_lista_unidades_tjsp, list_id_tjsp)
                df_com = pd.concat(objs=list(temp), ignore_index=True)

            # Results
            self.df_com = df_com

        else:
            pass

        return self.df_com

    @property
    def unidades(self) -> pd.DataFrame:
        if self.df_com is None:
            raise Exception("sdsds")

        # Merge
        df_unidades = pd.merge(
            left=self.df_mun,
            right=self.df_com,
            left_on="id_municipio_tjsp",
            right_on="id_municipio_tjsp",
            how="inner",
            suffixes=["", "_copy"],
        )

        df_unidades = df_unidades.drop(
            labels=["municipio_tjsp_copy"],
            axis="columns",
            errors="ignore",
        )

        # Aplica strip em todo o dataframe
        df_unidades = df_unidades.map(lambda x: x.strip() if isinstance(x, str) else x)
        return df_unidades

    @property
    def municipios_comarcas(self) -> pd.DataFrame:
        df_tjsp = self.unidades

        # Filtra Colunas
        df_tjsp = df_tjsp.drop(
            labels=[
                "unidades",
                "raj",
                #'id_municipio_tjsp'
            ],
            axis="columns",
            errors="ignore",
        )

        # Deleta Duplicados
        df_tjsp = df_tjsp.drop_duplicates()
        return df_tjsp.copy()

    @property
    def comarcas(self) -> pd.DataFrame:
        df_tjsp = self.unidades

        # Comarca
        df_tjsp_com = df_tjsp[df_tjsp["comarca_sede"] == 1]

        # Filtra Colunas
        df_tjsp_com = df_tjsp_com.drop(
            labels=["comarca_sede"],
            axis="columns",
            errors="ignore",
        )

        # Deleta Duplicados
        df_tjsp_com = df_tjsp_com.drop_duplicates()

        # Renomeia Colunas
        df_tjsp_com = df_tjsp_com.rename(
            {
                "municipio_tjsp_corrigido": "comarca_tjsp_corrigido",
                "id_municipio": "id_comarca",
            },
            axis="columns",
        )

        # Deleta
        df_tjsp_com = df_tjsp_com.drop(
            labels=["municipio_tjsp"],
            axis="columns",
            errors="ignore",
        )

        # Bata Bater
        df_tjsp_com2 = adjust_columns(
            df=df_tjsp_com,
            column_ajust="comarca_tjsp",
        )

        return df_tjsp_com2

    def analisa_comarcas(self):
        df_tjsp = self.comarcas

        # Filtra Colunas
        df_tjsp = df_tjsp.drop(
            labels=[
                "unidades",
                "raj",
                #'id_municipio_tjsp'
            ],
            axis="columns",
            errors="ignore",
        )

        df_tjsp = df_tjsp.drop_duplicates()
        df_tjsp_mun = df_tjsp.copy()

        # Results
        df_tjsp_mun.info()
        df_tjsp_mun.head()

        # Comarca
        df_tjsp_com = df_tjsp[df_tjsp["comarca_sede"] == 1]

        # Filtra Colunas
        df_tjsp_com = df_tjsp_com.drop(
            labels=["comarca_sede"],
            axis="columns",
            errors="ignore",
        )

        #
        df_tjsp_com = df_tjsp_com.drop_duplicates()

        # Renomeia
        df_tjsp_com = df_tjsp_com.rename(
            {
                "municipio_tjsp_corrigido": "comarca_tjsp_corrigido",
                "id_municipio": "id_comarca",
            },
            axis="columns",
        )

        # Deleta
        df_tjsp_com = df_tjsp_com.drop(
            labels=["municipio_tjsp"],
            axis="columns",
            errors="ignore",
        )

        # Bata Bater
        df_tjsp_com = adjust_columns(
            df=df_tjsp_com,
            column_ajust="comarca_tjsp",
        )
