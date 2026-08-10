# Tribunal de Justiça de São Paulo (TJSP)

[![Repo](https://img.shields.io/badge/GitHub-repo-blue?logo=github&logoColor=f5f5f5)](https://github.com/michelmetran/tjsp_unidades)
[![PyPI - Version](https://img.shields.io/pypi/v/tjsp_unidades?logo=pypi&label=PyPI&color=blue)](https://pypi.org/project/tjsp_unidades)<br>
[![Publish Python to PyPI](https://github.com/michelmetran/tjsp_unidades/actions/workflows/publish-to-pypi-uv.yml/badge.svg)](https://github.com/michelmetran/tjsp_unidades/actions/workflows/publish-to-pypi-uv.yml)
[![Static Badge](https://img.shields.io/badge/MkDocs-Docs-Green)](https://tjsp-unidades.readthedocs.io/)

Na atuação do [Ministério Público do Estado de São Paulo (MPSP)](https://www.mpsp.mp.br/) faz-se obter informações atualizadas do [Tribunal de Justiça do Estado de São Paulo (TJSP)](https://portal.tjsp.jus.br/Home/) constantemente. Devido à inexistência de comunicação direta, via API ou _webservice_, entre as duas instituições do pode judiciário do Estado de São Paulo, foi necessário recorrer às técnicas de _webscrapping_ para raspar informações básicas do TJSP.

Dentre as informações básicas, está a divisão adminstrativa do definida pelo TJSP. Por meio do _site_ das [Regiões Administrativas Judiciárias](https://www.tjsp.jus.br/QuemSomos/QuemSomos/RegioesAdministrativasJudiciarias) faz-se possível obter dados de:

- Comarcas
- Circunscrições Judiciárias (CJs)
- Regiões Administrativas Judiciárias (RAJs)

<br>

O objetivo do presente repositório é manter **rotinas e códigos para obtenção de dados atualizados do [TJSP](https://portal.tjsp.jus.br).** Além disso, o pacote disponibiliza um conjunto de dados atualizados até determinada data.

> Dados Atualizados em 10.08.2026

<br>

---

## _TODO_

1. Obter Entrâncias das Comarcas?? Tabular leis... [Lei 1](https://www.al.sp.gov.br/norma/59545), [Lei 2](https://www.al.sp.gov.br/repositorio/legislacao/lei.complementar/2005/lei.complementar-980-21.12.2005.html) etc.
2. Usar pasta temporária
