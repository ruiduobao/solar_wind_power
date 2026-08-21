# Global Green Energy Ecological Assessment (Solar & Wind Power)

Codebase for assessing the ecological impacts of global solar (photovoltaic) and wind power installations, covering land cover, power generation potential, carbon loss, and carbon payback time.

> This repository contains **code and documentation only**. Input data (rasters, vectors, CSV extracts) and intermediate products are not included. See [Data & Dependencies](#data--dependencies).

## Pipeline Overview

| Step | Folder | Description |
|------|--------|-------------|
| 1 | `step1.计算土地覆盖` | Land cover analysis of wind and solar installations (GEE + local processing, FROM_GLC / ESRI land cover sources) |
| 2 | `step2.计算发电潜力` | Power generation potential: solar PV (`step2.1计算光伏发电潜力`) and wind (`step3.2计算风电发电潜力`), plus a PV-vs-wind comparison |
| 3 | `step3.计算碳损失` | Carbon loss: soil carbon (`3.1土壤碳损失计算`), biomass carbon (`3.2计算生物碳损失`), manufacturing carbon (`3.3制造碳的计算`), total carbon loss & sensitivity experiment (`3.4计算总的碳损失(敏感性实验)`), and decomposition by land cover type (`3.5按土地覆盖类型分解`) |
| 4 | `step4.碳回本计算` | Carbon payback time: with grid emission factors (`4.1考虑电网排放因子`), without (`4.2不考虑电网排放因子`), and their comparison (`4.3对比考虑不考虑电网排放因子`) |
| 5 | `step5.制图` | Figure generation: land cover figures (`figure2.土地覆盖`), carbon loss figures (`figure3.碳损失`), carbon payback figures (`figure4.碳回本`), and grid/payback figure (`figure5.电网与碳回本`) |

## Workflow

1. **Step 1 – Land cover**: Use the GEE scripts (`step1.gee*.js`, `STEP1.gee下载代码.js`) to extract wind/solar installation footprints from Google Earth Engine, then run the local Python scripts to analyze the land cover composition of each installation (e.g., 耕地/cropland, 林地/forest, 草地/grassland, 灌木/shrubland, 湿地/wetland, 裸地/bareland).
2. **Step 2 – Generation potential**: Compute annual electricity generation potential for each solar/wind installation based on installation capacity and meteorological/irradiance data.
3. **Step 3 – Carbon loss**: Estimate the carbon cost of each installation in three parts:
   - **Soil carbon** (`3.1`): download soil organic carbon data (e.g., SoilGrids) and compute the soil carbon loss under the installation footprint.
   - **Biomass carbon** (`3.2`): convert biomass carbon netCDF data to GeoTIFF and compute the loss of above-ground/below-ground biomass.
   - **Manufacturing carbon** (`3.3`): estimate the carbon emissions embodied in manufacturing the panels/turbines (with density and installation-year adjustments).
   - The total carbon loss and a sensitivity experiment are computed in `3.4`; results decomposed by land cover type in `3.5`.
4. **Step 4 – Carbon payback**: Divide total carbon loss by the annual avoided emissions (using grid emission factors from `Grid_Emission_Factors_2021.csv` when applicable) to obtain the carbon payback time (years).
5. **Step 5 – Figures**: Generate all publication figures used in the paper.

## Documentation (English)

| File | Description |
|------|-------------|
| `公式计算.md` | Key formulas used in the assessment |
| `step1.计算土地覆盖\2光伏发电\光伏发电潜力计算规则.md` | Rules for computing solar PV potential |
| `step2.计算发电潜力\step2.1计算光伏发电潜力\光伏发电计算方法.md` | Method for computing PV electricity generation |
| `step2.计算发电潜力\step2.1计算光伏发电潜力\光伏发电潜力计算规则.md` | Rules for computing PV potential (step-2 copy) |
| `step2.计算发电潜力\step3.2计算风电发电潜力\风电发电能力计算方法.md` | Method for computing wind power generation |
| `step2.计算发电潜力\step3.2计算风电发电潜力\风电发电能力计算规则.md` | Rules for computing wind power generation |
| `step2.计算发电潜力\step3.2计算风电发电潜力\光伏和风能对比结果.md` | PV-vs-wind comparison results |
| `step1.计算土地覆盖\土地覆盖补充信息.md` | Supplementary notes on land cover classes |
| `step3.计算碳损失\3.1土壤碳损失计算\3.1.2计算光伏土壤碳\输出数据的格式和单位.md` | Output data format and units |

## Data & Dependencies

- **Grid emission factors**: `Grid_Emission_Factors_2021.csv` (in `step4.碳回本计算\4.1考虑电网排放因子\Grid_Emission_Factors_2021.csv`) is a small parameter table of regional grid emission factors used by the carbon-payback calculation. All other data (land cover rasters, soil carbon, biomass carbon, GEE assets, meteorological data) must be prepared/downloaded separately — see the individual scripts and GEE code for the exact data sources.
- **GEE**: Several Step-1 scripts run inside Google Earth Engine (`.js`); the Python scripts assume the corresponding GEE exports have already been downloaded.
- **Python environment**: scripts are written for Python 3.x and rely on common geospatial packages: `gdal`/`rasterio`, `geopandas`, `numpy`, `pandas`, `matplotlib` (plus `earthengine-api` where needed). Each script is self-contained; run them in the order indicated by their leading numbers within each folder.

## Notes

- Folder and file names keep their original Chinese names because they are referenced by the code; comments, docstrings, and this documentation are in English.
- Scripts are intended to be run from their own directory (paths are relative to each script's location).
- `check_classes.py`, `diagnose_match.py`, and `get_paper_stats.py` in the root are diagnostic/utility scripts used during development.
