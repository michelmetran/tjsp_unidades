"""
Módulo contendo pequenas Funções utilizadas no código.
"""

import re
import unicodedata

import pandas as pd


def keep_numbers(my_string):
    """
    Mantem apenas números
    '987978098098098'
    https://stackoverflow.com/questions/1249388/removing-all-non-numeric-characters-from-string-in-python

    :return: _description_
    :rtype: _type_
    """
    return re.sub("[^0-9]", "", my_string)


def find_text_between_parenthesis(my_string):
    """
    _summary_
    https://stackoverflow.com/questions/4894069/regular-expression-to-return-text-between-parenthesis

    """
    return my_string[my_string.find("(") + 1 : my_string.find(")")]


def remove_multiple_spaces(my_string: str) -> str:
    """
    _summary_
    https://stackoverflow.com/questions/1546226/is-there-a-simple-way-to-remove-multiple-spaces-in-a-string

    :param my_string: _description_
    :type my_string: _type_
    :return: _description_
    :rtype: _type_
    """
    return re.sub(r"\s\s+", " ", my_string)


def remove_accents(my_string: str) -> str:
    """
    _summary_

    :param input_str: _description_
    :type input_str: _type_
    :return: _description_
    :rtype: _type_
    """
    nfkd_form = unicodedata.normalize("NFKD", my_string)
    only_ascii = nfkd_form.encode("ASCII", "ignore")
    return only_ascii.decode()


def strip_accents(my_string: str) -> str:
    """
    Retira acentos das palavras
    https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string

    :param my_string: Texto com acento
    :type my_string: string
    :return: Texto sem acento
    :rtype: my_string
    """
    return "".join(
        c
        for c in unicodedata.normalize("NFD", str(my_string))
        if unicodedata.category(c) != "Mn"
    )


def adjust_columns(df: pd.DataFrame, column_ajust: str) -> pd.DataFrame:
    """
    Adiciona coluna à tabela, com sufixo _temp,
    com correções diversas para fins de "fazer bater"

    :param df: tabela bruta
    :return: tabela com coluna a mais
    """
    #
    dd_fix = {
        # Errado / Certo
        "rio grande de serra": "rio grande da serra",
        "santa rosa de viterbo": "santa rosa do viterbo",
        "santana do parnaiba": "santana de parnaiba",
        "sao luis do paraitinga": "sao luiz do paraitinga",
    }

    # Coluna para ajustar
    col_temp = f"{column_ajust}_temp"

    # Para Bater
    df[col_temp] = df[column_ajust]
    df[col_temp] = df[col_temp].str.strip()
    df[col_temp] = df[col_temp].str.lower()
    df[col_temp] = df.apply(lambda x: strip_accents(x[col_temp]), axis="columns")
    df[col_temp] = df[col_temp].str.replace("’", "")
    df[col_temp] = df[col_temp].str.replace("´", "")
    df[col_temp] = df[col_temp].str.replace("'", "")
    df[col_temp] = df[col_temp].rename(dd_fix, axis="rows")
    df = df.replace({col_temp: dd_fix})
    return df


if __name__ == "__main__":
    # a = keep_numbers("Michel   333  Metran")
    a = remove_accents("Antônio")
    print(a)
