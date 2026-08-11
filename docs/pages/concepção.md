# Concepção do Projeto

## _Script_ 1: Quem Somos

A ideia iniciar foi "raspar" as informações da lista de CJs, RAJs e Comarcas da sessão ["Quem Somos"](https://www.tjsp.jus.br/QuemSomos/QuemSomos/RegioesAdministrativasJudiciarias) do _site_ do TJSP. Ainda faltaria a informação de cada um dos 645 municípios do Estado e a vinculação com a Comarca, assunto resolvido com outro _script_.

Para raspar os dados foi usado o _Selenium_, no _script_ [10_get_data_quem_somos_rajs](./../scripts/10_get_data_quem_somos_rajs.ipynb). Como resultado foram obtidas as listas de:

- **Comarcas**: totalizando 321 Comarcas do Estado (_descobri que tratam-se, na realidade, de 320 Comarcas... segue a leitura..._)
- **Circunscrições Judiciárias**, totalizando 57 CJs no Estado (56 mais a Capital!)
- **Regiões Administrativas Judiciárias**, totalizando 5 RAJs no Estado

<br>

---

## _Script_ 2: Método `POST`

Faltava ainda descobrir qual a Comarca dos 645 municípios do Estado de São Paulo, para conseguir relacioná-los a lista das 321 Comarcas (até então). Descobri que por meio da [Lista Telefônica](https://www.tjsp.jus.br/ListaTelefonica) era possível pesquisar um determinado município e obter as unidades do Poder Judiciário que tem atribuição no município pesquisado! Pronto! Era necessário apenas consultar todos os municípios agora, o que foi feito com auxílio do _script_ [13_get_data_listar_municipios](./../scripts/13_get_data_listar_municipios.ipynb).

![](https://i.imgur.com/I2iKlnE.png)

<br>

Notei que ao escrever parte do nome do município, um método `POST` atuava, retornando a lista dos 10 municípios prováveis de serem solicitados pelo usuário. Fiz a requisição `POST` dezenas de vezes, obtendo o nome dos Município definidos pelo TJSP (que contendo erros!, por exemplo "Florínia" está errado. O Correto é"Florínea") e o Código do Município definido pelo TJSP.

Em um segundo método `POST` que encontrei no _site_, era possível obter a jurisdição a partir do nome do Código do Municício definido pelo TJSP. Consultei todos os 645 códigos, obtendo a lista das Comarcas.

**IMPORTANTE**: Descartei a lista das unidades do Poder Judiciário (nomes de Fórums e outros). Pode ser que essa informação seja útil em alguma ocasião. Como não era meu objetivo nesse projeto, descartei!

Após obter as informações, fiz um trabalho de ajuste dos dados para que os Municípios e Comarcas fossem vinculados aos Códigos do IBGE, corrigindo também no nome dos Municípios.

Após ajustar a tabela e como resultado, observei a existência de 320 Comarcas, contrariando a informação anteriormente obtida!

<br>

---

## _Script_ 3: Comarcas: o que está certo?

O _script_ [20_transform](./../scripts/20_transform.ipynb) leu as informações das Comarcas obtidas no _script_ 1 e 2, visando compara-las e encontrar onde estava a diferença:

- De acordo com o _script_ 1 existem 321 Comarcas
- De acordo com o _script_ 2 existem 320 Comarcas

<br>

Com auxílio do _script_ 03 encontrei o erro que consta no ["Quem Somos"](https://www.tjsp.jus.br/QuemSomos/QuemSomos/RegioesAdministrativasJudiciarias), obtido no _script_ 01: Está listada "Vila Mimosa" como Comarca. Na realidade, trata-se de um Forum Regional no município de Campinas, pertencente a Comarca de Campinas, conforme se observa, inclusive, na hierarquia da [Secretaria da Fazenda](http://www.fazenda.sp.gov.br/ua/hierarquia3.asp?ua1=0021071).

![](https://i.imgur.com/RVAA9Ly.png)

<br>

O _script_ atualiza informações, trazendo o número da CJ para a tabela de Comarcas e excluí a tabela de Comarcas errada!

<br>

---

## _Script_ 4: Compilação de Dados e Mapas

Um quarto _script_ [30_results_geodata](./../scripts/30_results_geodata.ipynb) compila essas informações em uma talela única, gerando um mapa contendo a delimitação dos 645 municíos com todas as informações associadas.

<br>

---

## _Script_ 5: _Webmap_

Para finalizar, o _script_ [31_results_create_map](./../scripts/31_results_create_map.ipynb) foi também gerado um _webmap_, para facilitar a visualização de dados.
