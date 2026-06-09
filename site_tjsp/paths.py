"""
Pastas do Projeto
mar.23
"""

from pathlib import Path

project_path = Path(__file__).parents[0]
#module_path = Path(__file__).parents[0]

# Data
data_path = project_path / "data"
data_path.mkdir(exist_ok=True)

# input_path = data_path / 'input'
# input_path.mkdir(exist_ok=True)

output_path = data_path / "output"
output_path.mkdir(exist_ok=True)

output_path_gpkg = output_path / "gpkg"
output_path_gpkg.mkdir(exist_ok=True)

output_path_tab = output_path / "tab"
output_path_tab.mkdir(exist_ok=True)

output_path_geo = output_path / "geo"
output_path_geo.mkdir(exist_ok=True)

output_path_map = output_path / "map"
output_path_map.mkdir(exist_ok=True)

# # Scrapy
# scrapy_path = project_path / "scrapy"
# scrapy_path.mkdir(exist_ok=True)

# driver_path = scrapy_path / "driver"
# driver_path.mkdir(exist_ok=True)

# logs_path = scrapy_path / "logs"
# logs_path.mkdir(exist_ok=True)

# adds_path = scrapy_path / "adds"
# adds_path.mkdir(exist_ok=True)


if __name__ == "__main__":
    print(project_path)
