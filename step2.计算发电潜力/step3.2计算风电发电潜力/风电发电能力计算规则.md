# Wind Generation Capacity: Calculation Rules and Figure Descriptions

This document details the figure-generation rules, calculation methods, and corresponding outputs for the wind generation potential analysis of the "Global Green Energy Ecological Assessment" project.

**Output directory**: `Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算`

---

## 1. Global Wind Capacity Factor Map

![Map_Global_CF](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Map_Global_CF.png)

### Method
*   **Data source**: `Capacity Factor` (IEC Class II, 100m height) data from the Global Wind Atlas.
*   **Indicator definition**: `Capacity Factor` (CF) is the ratio of a turbine's actual generation to its theoretical maximum (0-1).
*   **Plotting logic**:
    *   Extract the CF raster value at each turbine (Point) location.
    *   Plot all turbine points on the map.
    *   Color mapping uses `viridis`; brighter (yellow) colors indicate better wind resources.

## 2. Global Annual Avoided CO2 Emissions Map

![Map_Global_Avoided_CO2](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Map_Global_Avoided_CO2.png)

### Method
*   **Indicator definition**: Annual CO2 emissions avoided by each wind farm. Unit: `ton CO2/year`.
*   **Formula**:
    $$ Avoided\ CO_2 = Annual\ Generation \times Grid\ Emission\ Factor $$
    *   `Annual Generation` (MWh/yr) = $Capacity (MW) \times CF \times 8760$
    *   `Grid Emission Factor` (tCO2/MWh): the average grid emission factor of the country.
*   **Plotting logic**:
    *   Uses a **log scale**.
    *   Colormap `RdYlGn_r` (red-yellow-green reversed); red indicates larger emission-reduction contributions.

## 3. Top 15 Countries by Estimated Wind Capacity

![Bar_Top15_Capacity](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Bar_Top15_Capacity.png)

### Method
*   **Indicator definition**: Estimated total wind installed capacity per country. Unit: `MW`.
*   **Formula**:
    $$ Capacity (MW) = \sum Rated\ Power $$
    *   `Rated Power`: dynamic estimate based on construction year (2017-2018: 2.2MW; 2019-2021: 3.0MW; >=2022: 4.2MW).
*   **Plotting logic**: Sum by country group and show the top 15.

## 4. Wind CF Distribution by Latitude

![Box_Latitude_CF](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Box_Latitude_CF.png)

### Method
*   **Objective**: Examine whether global wind farms are sited in the latitude bands with the best wind resources.
*   **Data processing**: Bin by 10-degree latitude intervals.
*   **Plotting logic**: Box plots showing the CF distribution of each latitude band.

## 5. Resource Mismatch Analysis

![Resource_Mismatch_Analysis](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Resource_Mismatch_Analysis.png)

### Method
*   **Objective**: Assess the resource-environment benefit matching of wind deployment.
*   **Four dimensions**:
    *   **X axis**: grid emission factor.
    *   **Y axis**: wind capacity factor.
    *   **Bubble size**: total wind installed capacity.
    *   **Bubble color**: annual total avoided emissions.
*   **Key zones**:
    *   **High Impact Zone (top right)**: good wind + dirty grid = best benefit.
    *   **Low Impact Zone (bottom left)**: poor wind + clean grid = lower benefit.

## 6. Annual Newly Installed Wind Capacity Trend

![Temporal_Annual_New_Capacity](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Temporal_Annual_New_Capacity.png)

### Method
*   **Data source**: `constructi` (year) field in the Shapefile.
*   **Processing rule**: 2017 and earlier are treated as existing stock; 2018-2024 are increments.
*   **Plotting logic**: Bar chart of annual additions.

## 7. Quarterly Newly Installed Wind Capacity Trend

![Temporal_Quarterly_Trend](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Temporal_Quarterly_Trend.png)

### Method
*   **Data source**: `constructi` (year) and `construc_1` (quarter).
*   **Plotting logic**: Line/area chart showing quarterly fluctuations.

## 8. Spatiotemporal Evolution of Wind Construction Centroid

![Spatiotemporal_Heatmap](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Spatiotemporal_Heatmap.png)

### Method
*   **Objective**: Observe the latitudinal migration of the wind construction centroid over time.
*   **Plotting logic**: Heatmap (year x latitude).

## 9. Evolution of Wind Siting Efficiency

![Evolution_Efficiency](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Evolution_Efficiency.png)

### Method
*   **Indicator definition**:
    *   **Resource Quality (blue line)**: capacity-weighted mean CF.
    *   **Grid Carbon Intensity (grey line)**: capacity-weighted mean grid emission factor.
*   **Interpretation**: The curve trend reflects changes in siting strategy (going to better-wind places or dirtier-grid places).

## 10. Lorenz Curve of Wind Carbon Avoidance

![Lorenz_Curve_CO2](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Lorenz_Curve_CO2.png)

### Method
*   **Objective**: Assess the inequality of emission-reduction contributions.
*   **Plotting logic**: cumulative share of sites vs. cumulative share of avoided emissions.

## 11. Global CF Raster Map

![Map_Raster_CF](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Map_Raster_CF.png)

### Method
*   **Data source**: `cf_iec2_cog_100m.tif`.
*   **Plotting logic**: Render the raster directly to show the global wind resource background.

## 12. Global Grid Emission Factors Map

![Map_Global_Grid_EF](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.2风力发电潜力计算\Map_Global_Grid_EF.png)

### Method
*   **Data source**: same as the PV part, `Harmonized_IFI_Default_Grid_Factors_2021_v3.2`.
*   **Plotting logic**:
    *   Polygon map showing grid cleanliness by country.
    *   **Red**: high-carbon grids.
    *   **Green**: low-carbon grids.

---

# Part II: Deep Comparative Analysis of Solar PV and Wind Power Potential (Comparative Analysis)

**Output directory**: `Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比`

The figures in this section are generated by `3.光伏和风能对比.py`, aiming to compare the resource characteristics and spatio-temporal distribution differences between solar PV and wind power.

## 13. [Resource Endowment] Global Capacity-Factor Distribution Comparison (Violin Plot)

![1_Resource_Quality_Violin](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比\1_Resource_Quality_Violin.png)

### Method
*   **Objective**: Compare the distribution of resource quality (CF) between wind and solar PV.
*   **Plotting logic**: Violin plot shows the density distribution; the red dot marks the mean. Wind CF is usually higher on average but more widely dispersed.

## 14. [Spatial Complementarity] Latitude-Resource-Capacity Composite Plot (Dual-Axis Latitude Profile)

![2_Latitude_Profile_DualAxis](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比\2_Latitude_Profile_DualAxis.png)

### Method
*   **Objective**: Reveal the spatial complementarity of the two resources across latitude.
*   **Top panel (Bar)**: Installed capacity (GW) by latitude band. PV is concentrated in low latitudes, wind in mid-to-high latitudes.
*   **Bottom panel (Line)**: Mean resource quality (CF) by latitude band.

## 15. [Country Dimension] Country Resource Competitiveness Matrix (Country Resource Matrix)

![3_Country_Resource_Matrix](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比\3_Country_Resource_Matrix.png)

### Method
*   **Objective**: Assess each country's resource advantage tendency.
*   **X axis**: mean solar PV CF.
*   **Y axis**: mean wind CF.
*   **Color**: grid emission factor (Grid EF).
*   **Interpretation**: countries above the diagonal are "wind-advantage", those below are "solar-advantage".

## 16. [Equity] Lorenz Curves of Emission-Reduction Contribution (Lorenz Curves)

![4_Lorenz_Curve_Comparison](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比\4_Lorenz_Curve_Comparison.png)

### Method
*   **Objective**: Compare the degree of inequality in resource distribution between the two types.
*   **Indicator**: Gini coefficient. A higher Gini means resources are more concentrated in a few sites. Typically Gini(wind) > Gini(solar PV).

## 17. [Emission-Reduction Strategy] Resource-Grid Joint Distribution (Joint Distribution)

![5_Joint_Distribution_Nexus](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比\5_Joint_Distribution_Nexus.png)

### Method
*   **Objective**: Examine whether sites are located in "benefit-maximizing" regions (i.e., dirty grids with good resources).
*   **Plotting logic**: Kernel density contour plot (KDE Contour).

## 18. [Temporal Evolution] Technology Improvement and Resource Selection Trends (Temporal Evolution)

![6_Temporal_Evolution](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比\6_Temporal_Evolution.png)

### Method
*   **Objective**: Whether, during 2010-2024, the resource quality (CF) of chosen sites improved as installed capacity grew.
*   **Dual axis**: Bars represent newly added capacity (GW); the line represents mean CF.

## 19. [Regional Pattern] Continental Wind/Solar Capacity Mix (Regional Energy Mix)

![7_Continent_Mix](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比\7_Continent_Mix.png)

### Method
*   **Objective**: Show continental preferences for wind vs. solar.
*   **Plotting logic**: Stacked bar chart.

## 20. [Resource Preference] Global Wind/Solar Resource Advantage Ratio Map (Resource Preference Map)

![8_Global_Resource_Ratio_Map](Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.3风力光伏发电潜力差异对比\8_Global_Resource_Ratio_Map.png)

### Method
*   **Objective**: Spatialize the resource endowment differences across countries.
*   **Indicator**: $Log_2(CF_{Solar} / CF_{Wind})$.
*   **Color**:
    *   **Red**: solar resources significantly outperform wind (e.g., Africa).
    *   **Blue**: wind resources significantly outperform solar (e.g., Northern Europe).
