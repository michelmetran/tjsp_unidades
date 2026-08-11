"""
Módulo que obtem e trata a informação contida na página "Quem Somos" do TJSP.
"""

import re
import urllib.request

import pandas as pd
from lxml import html

from ..transform.small_functions import keep_numbers


class QuemSomos:
    """
    Classe que representa a página [Quem Somos](https://www.tjsp.jus.br/QuemSomos/QuemSomos/RegioesAdministrativasJudiciarias) do TJSP
    """

    def __init__(self) -> None:
        self.url = "https://www.tjsp.jus.br/QuemSomos/QuemSomos/RegioesAdministrativasJudiciarias"

        # Chama Função
        self._request()

    def _request(self):
        """
        Obtem os dados brutos do site
        """

        content = urllib.request.urlopen(url=self.url).read()
        tree = html.fromstring(content)

        list_divs = tree.xpath("//div[contains(@style, 'background')]")

        list_dfs_rajs = []
        list_dfs_cjs = []

        for div in list_divs:
            # A partir da div, pega os "p"
            list_p = div.xpath(".//p")

            # Obtem dados
            raj = list_p[0].text_content().strip()
            raj_list = re.split(pattern=r"[-–]", string=raj, maxsplit=0)
            raj_num = raj_list[0].strip()
            raj_regiao = raj_list[1].strip()
            juiz = list_p[1].text_content().strip().split(":")[1].strip()
            email = re.sub("[()]", "", list_p[2].text_content().strip())

            # Para cada div, pega o primeiro ul que encontramos
            list_ul = div.xpath("./..//ul")[0]
            list_ul = div.getnext()
            list_li = list_ul.xpath(".//li")

            # RAJs
            dict_raj = {
                "raj_nome": raj,
                "raj_sigla": raj_num,
                "raj_regiao": raj_regiao,
                "juiz_diretor_nome": juiz,
                "juiz_diretor_email": email,
            }
            list_dfs_rajs.append(dict_raj)

            # Lista de Circunscrições Judiciárias
            list_cjs = [x.text_content() for x in list_li]

            # Circunscrição Judiciária
            df = pd.DataFrame(data=list_cjs, columns=["comarca_cirscunscricao"])
            df["raj_sigla"] = raj_num

            # Lista de CJs
            list_dfs_cjs.append(df)

        self.list_dfs_cjs = list_dfs_cjs
        self.list_dfs_rajs = list_dfs_rajs

    @property
    def rajs(self) -> pd.DataFrame:
        """
        Tabela contendo informações das Regiões Administrativas Judiciárias (RAJs) do TJSP.

        :return: tabela contendo informações das RAJs
        """
        # Cria Tabela
        df_raj = pd.DataFrame(self.list_dfs_rajs)

        # Ajusta caracter separador
        df_raj["raj_nome"] = df_raj["raj_nome"].str.replace("–", "-")

        # Obtem ID da RAJ a partir do número da RAJ
        df_raj["id_raj"] = df_raj["raj_sigla"].apply(lambda x: keep_numbers(x))
        df_raj["id_raj"] = df_raj["id_raj"].astype(int)

        # Ordena RAJs
        df_raj = df_raj.sort_values(by="id_raj", ascending=True)
        df_raj = df_raj.reset_index(drop=True)

        # Reordena Colunas
        df_raj = df_raj[
            [
                # RAJ
                "id_raj",
                "raj_nome",
                "raj_sigla",
                "raj_regiao",
                "juiz_diretor_nome",
                "juiz_diretor_email",
            ]
        ]

        # Aplica Strip em tudo
        df_raj = df_raj.map(lambda x: x.strip() if isinstance(x, str) else x)

        return df_raj

    @property
    def cjs(self) -> pd.DataFrame:
        """
        Tabela contendo informações das Circuncrições Judiciárias (CJs) do TJSP.

        :return: tabela contendo informações das CJs
        """
        # Monta Tabela
        df_cj = pd.concat(
            objs=self.list_dfs_cjs,
            ignore_index=True,
        )

        # ddd
        df_cj[["comarca", "cj_sigla"]] = df_cj["comarca_cirscunscricao"].str.rsplit(
            "-",
            n=1,
            expand=True,
        )
        # Ajusta Texto
        df_cj["cj_sigla"] = df_cj["cj_sigla"].str.strip()

        # Id RAJ
        df_cj["id_raj"] = df_cj["raj_sigla"].apply(lambda x: keep_numbers(x))
        df_cj["id_raj"] = df_cj["id_raj"].astype(int)

        # Id CJ
        df_cj["id_cj"] = df_cj["cj_sigla"].apply(lambda x: keep_numbers(x))
        df_cj.loc[df_cj["id_cj"] == "", "id_cj"] = "0"
        df_cj["id_cj"] = df_cj["id_cj"].astype(int)

        # Renomeia Textos
        df_cj["cj_nome"] = df_cj["cj_sigla"].replace(
            "CJ",
            "Circunscrição Judiciária",
            regex=True,
        )

        # Ajusta Texto
        df_cj["cj_nome"] = df_cj["cj_nome"].str.strip()

        # Reordena Colunas
        df_cj = df_cj[
            [
                "id_cj",
                "cj_sigla",
                "cj_nome",
                "id_raj",
            ]
        ]

        df_cj = df_cj.drop_duplicates()
        df_cj = df_cj.sort_values(by="id_cj")
        df_cj = df_cj.reset_index(drop=True)
        df_cj = df_cj.drop_duplicates()

        # Aplica Strip em tudo
        df_cj = df_cj.map(lambda x: x.strip() if isinstance(x, str) else x)

        # Results
        return df_cj

    @property
    def comarcas(self) -> pd.DataFrame:
        """
        Tabela contendo informações das Comarcas e Vinculação com CJs do TJSP.

        :return: tabela contendo informações das Comarcas
        """
        # Monta Tabela
        df = pd.concat(
            objs=self.list_dfs_cjs,
            ignore_index=True,
        )

        df[["comarca", "cj_sigla"]] = df["comarca_cirscunscricao"].str.rsplit(
            "-", n=1, expand=True
        )

        # Arruma Texto
        df["cj_sigla"] = df["cj_sigla"].str.strip()

        # Id CJ
        df["id_cj"] = df["cj_sigla"].apply(lambda x: keep_numbers(x))
        df.loc[df["id_cj"] == "", "id_cj"] = "0"
        df["id_cj"] = df["id_cj"].astype(int)

        df["cj_nome"] = df["cj_sigla"].replace(
            "CJ", "Circunscrição Judiciária", regex=True
        )
        df["cj_nome"] = df["cj_nome"].str.strip()

        # Reordena Colunas
        df = df[["comarca", "id_cj"]]

        # Deleta Duplicatas
        df = df.drop_duplicates()

        # Renomear Colunas
        df = df.rename({"comarca": "comarca_tjsp"}, axis="columns")

        # Ordena
        df = df.iloc[df["comarca_tjsp"].str.normalize("NFKD").argsort()]
        df = df.reset_index(drop=True)

        # Aplica strip em tudo
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

        # Results
        comarcas = df["comarca_tjsp"]

        # Aplica Strip em tudo
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

        print(f"São {len(set(comarcas))} comarcas")
        return df
