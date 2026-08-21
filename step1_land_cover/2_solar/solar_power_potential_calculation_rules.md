# Solar Generation Potential: Calculation Rules and Figure Descriptions

This document details the figure-generation rules, calculation methods, and corresponding outputs for the solar generation potential analysis of the "Global Green Energy Ecological Assessment" project.

**Output directory**: `Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算`

---

## Global Grid Emission Factors Map

![Map_Global_Grid_EF](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Map_Global_Grid_EF.png)

### Method

*   **Indicator definition**: Average grid emission factor of each country. Unit: `tCO2/MWh`. Note: 1 MWh = 1000 kWh; an average household uses about 200 kWh per month.
*   **Data source**: `Harmonized_IFI_Default_Grid_Factors_2021_v3.2` dataset.
*   **Plotting logic**:
    *   Render using world map polygons.
    *   Map each country's average emission factor onto the map.
    *   Color mapping uses `RdYlGn_r` (red-yellow-green reversed):
        *   **Red**: high-carbon grids (e.g., countries dominated by coal power).
        *   **Green**: low-carbon grids (e.g., countries dominated by hydro or nuclear power).
    *   This figure directly shows the "cleanliness" distribution of the global power system, explaining why the same generation amount yields vastly different emission-reduction benefits across countries.



## Global PVOUT Raster Map

![Map_Raster_PVOUT](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Map_Raster_PVOUT.png)

### Method

*   **Data source**: original GeoTIFF raster file (`PVOUT.tif`).
*   **Plotting logic**:
    *   Render the raster directly to show the raw spatial distribution of global solar resource potential.
    *   Overlay world country boundaries for geographic orientation.
    *   This figure serves as the baseline background reference for the analysis.



## 1. Global Solar Power Potential Map

![Map_Global_PVOUT](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Map_Global_PVOUT.png)

### Method
*   **Data source**: `PVOUT` (Specific Photovoltaic Power Output) data from the World Bank Global Solar Atlas.
*   **Indicator definition**: `PVOUT` is the average daily electricity generated per kilowatt-peak of installed PV capacity (kWp). Unit: `kWh/kWp/day`.
*   **Plotting logic**:
    *   Extract the PVOUT raster value at the center point of each PV plant (Polygon).
    *   Plot all PV plants as scatter points on the map.
    *   Colormap `plasma`: brighter (yellow) colors indicate better solar resources, darker (purple) colors indicate poorer resources.

## 2. Global Annual Avoided CO2 Emissions Map

![Map_Global_Avoided_CO2](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Map_Global_Avoided_CO2.png)

### Method
*   **Indicator definition**: Annual CO2 emissions avoided by each PV plant. Unit: `ton CO2/year`.
*   **Formula**:
    $$ Avoided\ CO_2 = Annual\ Generation \times Grid\ Emission\ Factor $$
    *   `Annual Generation` (MWh/yr) = $Capacity (MW) \times PVOUT (kWh/kWp/day) \times 365$
    *   `Grid Emission Factor` (tCO2/MWh): the country's average grid emission factor, from the `Harmonized_IFI_Default_Grid_Factors_2021_v3.2` dataset.
*   **Plotting logic**:
    *   Because values span a huge range (from a few tons to hundreds of thousands of tons), a **log scale** is used for color mapping.
    *   Colormap `RdYlGn_r` (red-yellow-green reversed): **red** = very large avoided emissions (large contribution), **green** = smaller avoided emissions.

## 3. Top 15 Countries by Estimated Solar Capacity

![Bar_Top15_Capacity](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Bar_Top15_Capacity.png)

### Method
*   **Indicator definition**: Estimated total solar installed capacity per country. Unit: `MW`.
*   **Formula**:
    $$ Capacity (MW) = Area (km^2) \times Power\ Density $$
    *   `Area`: polygon area of PV panels identified by remote sensing.
    *   `Power Density`: assumed to be **45 MW/km²** (empirical value).
*   **Plotting logic**:
    *   Group and sum by country (`country` field).
    *   Show the top 15 countries by total capacity.

## 4. Solar Potential Distribution by Latitude

![Box_Latitude_PVOUT](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Box_Latitude_PVOUT.png)

### Method
*   **Objective**: Examine whether global PV siting follows the natural rule of "seeking the best irradiance".
*   **Data processing**:
    *   Bin latitudes from 60°S to 90°N at **10-degree** intervals (`lat_bin`).
*   **Plotting logic**:
    *   Draw box plots of `PVOUT` for all PV plants within each latitude band.
    *   The box shows the distribution range (median, quartiles) of solar resources within the band.

## 5. Resource Mismatch Analysis

![Resource_Mismatch_Analysis](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Resource_Mismatch_Analysis.png)

### Method
*   **Objective**: Assess whether PV is deployed where it "should be" (i.e., good irradiance and able to replace dirty grids).
*   **Four dimensions**:
    *   **X axis**: grid emission factor — how "dirty" the grid is (dirtier to the right).
    *   **Y axis**: solar resource potential (`PVOUT`) — how good the irradiance is (better upward).
    *   **Bubble size**: total PV installed capacity of the country.
    *   **Bubble color**: annual total avoided CO2 of the country; red = larger contribution.
*   **Key zones**:
    *   **High Impact Zone (top right)**: good irradiance + dirty grid = best environmental benefit zone (e.g., India).
    *   **Low Impact Zone (bottom left)**: poor irradiance + clean grid = diminishing environmental benefit zone (e.g., some European countries).

## 6. Annual Newly Installed Solar Capacity Trend

![Temporal_Annual_New_Capacity](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Temporal_Annual_New_Capacity.png)

### Method
*   **Data source**: `constructi` (construction year) field in the Shapefile.
*   **Processing rule**:
    *   **Stock**: plants built in 2017 or earlier are grouped as "Pre-2018 Stock", shown as a text annotation, not included in the bar chart.
    *   **New**: for 2018-2024, new capacity is aggregated per year.
*   **Plotting logic**: bar chart of 2018-2024 additions only, directly reflecting recent growth.

## 7. Quarterly Newly Installed Solar Capacity Trend

![Temporal_Quarterly_Trend](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Temporal_Quarterly_Trend.png)

### Method
*   **Data source**: `constructi` (year) and `construc_1` (quarter) fields.
*   **Processing rule**: aggregate data from 2018 Q1 to 2024 Q4 by quarter.
*   **Plotting logic**: line and area charts showing finer-grained seasonal construction fluctuations.

## 8. Spatiotemporal Evolution of Solar Construction Centroid

![Spatiotemporal_Heatmap](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Spatiotemporal_Heatmap.png)

### Method
*   **Objective**: Observe whether the centroid of solar construction has shifted in latitude over time (e.g., from high-latitude developed countries to low-latitude developing countries).
*   **Data processing**:
    *   **Rows**: latitude bands (5-degree intervals).
    *   **Columns**: years (2018-2024).
    *   **Values**: newly installed capacity in that year and latitude band.
    *   **Normalization**: normalize each year (column) to compute the share of each latitude band that year.
*   **Plotting logic**: heatmap. Darker colors indicate a higher share of construction in that latitude band that year.

## 9. Evolution of Solar Siting Efficiency

![Evolution_Efficiency](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Evolution_Efficiency.png)

### Method
*   **Indicator definition**:
    *   **Resource Quality (orange line)**: capacity-weighted mean PVOUT of newly added PV plants that year.
    *   **Grid Carbon Intensity (grey line)**: capacity-weighted mean grid emission factor of the countries hosting newly added PV plants that year.
*   **Interpretation**:
    *   If the orange line rises over time, we are increasingly building plants in well-irradiated places.
    *   If the grey line rises over time, we are increasingly building plants in coal-dominated grids (replacing dirty electricity).

## 10. Lorenz Curve of Solar Carbon Avoidance

![Lorenz_Curve_CO2](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Lorenz_Curve_CO2.png)

### Method
*   **Objective**: Assess the inequality of global solar emission-reduction contributions (whether a few mega plants contribute most of the reductions).
*   **X axis**: cumulative share of PV plants (Cumulative Share of Sites).
*   **Y axis**: cumulative share of avoided emissions (Cumulative Share of Avoided CO2).
*   **Gini coefficient**: area between the curve and the diagonal. A higher Gini means emission-reduction contributions are more concentrated (more unequal).
