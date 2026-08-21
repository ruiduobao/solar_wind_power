### Stage 1: Excel Input Data Preparation (Input Data)

Before running the calculation, make sure each row (each PV/wind site) in your Excel file contains the following base columns:

**Basic Information:**
* **FID:** Unique ID
* **Capacity_MW:** Installed capacity
* **Region:** Region

**GIS Raw Zonal Statistics:**
* **SUM_Bio_GIS:** Total biomass carbon within the polygon (unit: tC) — from the Spawn dataset
* **SUM_Soil_GIS:** Total soil carbon within the polygon (unit: tC) — from the SoilGrids dataset

**Fine Land-Cover Pixel Counts (FROM-GLC10 Pixel Counts):**
* **N_10:** Cropland pixel count
* **N_20:** Forest pixel count
* **N_30:** Grassland pixel count
* **N_40:** Shrubland pixel count
* **N_50:** Wetland pixel count
* **N_60:** Bare land / impervious surface / water pixel count (key noise term)

**Slope Pixel Counts:**
* **N_Slope_L1:** Pixels with slope < 5°
* **N_Slope_L2:** Pixels with slope 5°–15°
* **N_Slope_L3:** Pixels with slope > 15°

---

### Stage 2: Spatial Denoising

**Purpose:** Remove interpolation noise ("ghost carbon") from SoilGrids/Spawn on bare land and impervious surfaces (e.g., parking lots, gobi deserts).
**Why:** Avoid computing carbon debt on non-ecological land.

**1. Compute the ecological efficiency ratio ($Ratio_{Eco}$)**

$$Ratio_{Eco} = \frac{N_{10} + N_{20} + N_{30} + N_{40} + N_{50}}{N_{10} + N_{20} + N_{30} + N_{40} + N_{50} + N_{60}}$$

> **Logic:** If a polygon is 90% concrete, then 90% of the GIS-derived total carbon is noise and must be discounted.

**2. Compute the corrected total carbon (Corrected Total)**

$$SUM_{Bio}^{Corrected} = SUM_{Bio}^{GIS} \times Ratio_{Eco}$$

$$SUM_{Soil}^{Corrected} = SUM_{Soil}^{GIS} \times Ratio_{Eco}$$

**Result:** The totals are now fully free of bare/hardened-area interference.

---

### Stage 3: Categorical Re-allocation

**Purpose:** Re-allocate the corrected total carbon back according to land-cover type differences.
**Why:** Avoid the "averaging error" of diluting high forest carbon into grassland.

**1. Introduce the IPCC reference weight table (Reference Table)**
*(Create this table in a separate Excel sheet, used for VLOOKUP or formula references)*

| Land cover | Code | Biomass weight (WBio) | Soil weight (WSoil) |
| :--- | :--- | :--- | :--- |
| **Cropland** | 10 | 5 | 50 |
| **Forest** | 20 | 100 | 90 |
| **Grassland** | 30 | 6 | 70 |
| **Shrubland** | 40 | 20 | 60 |
| **Wetland** | 50 | 15 | 120 |
| **Bare land** | 60 | 0 | 0 |

**2. Compute the theoretical score**

$$Score_{Bio} = (N_{10} \times 5) + (N_{20} \times 100) + (N_{30} \times 6) + ... + (N_{60} \times 0)$$

$$Score_{Soil} = (N_{10} \times 50) + (N_{20} \times 90) + (N_{30} \times 70) + ... + (N_{60} \times 0)$$

**3. Compute the allocation factor**

$$Factor_{Bio} = \frac{SUM_{Bio}^{Corrected}}{Score_{Bio}}$$

$$Factor_{Soil} = \frac{SUM_{Soil}^{Corrected}}{Score_{Soil}}$$

> **Note:** If $Score$ is 0, set the Factor to 0.

**4. Derive the real carbon stock (Real Stock Calculation)**
*These are hidden columns in Excel representing the true holdings of each land-cover class within each PV site.*

* **Forest stock:** $Stock_{Bio}^{Forest} = N_{20} \times 100 \times Factor_{Bio}$
* **Grassland stock:** $Stock_{Bio}^{Grass} = N_{30} \times 6 \times Factor_{Bio}$
* *(and so on for all 5 ecological land-cover classes, for both Bio and Soil stocks)*

---

### Stage 4: Loss Accounting

**Purpose:** Calculate how much carbon was actually lost based on engineering disturbance intensity.
**Setup:** Build a control panel at the top of the Excel sheet to switch Scenario A/B/C.

**1. Biomass carbon loss ($Loss_{Bio}$)**
Apply land-cover loss coefficients $L$ (e.g., forest Baseline=100%, grassland Baseline=100%).

$$Loss_{Bio} (tC) = \sum (Stock_{Bio}^{Class\_i} \times L_{Class\_i})$$

> Expanded: $= (Stock_{Forest} \times L_{Forest}) + (Stock_{Grass} \times L_{Grass}) + ...$

**2. Soil carbon loss ($Loss_{Soil}$)**
Since spatial overlay is not possible, we use the **"slope-weighted average coefficient method"**.

* **Step A: Compute total soil stock in ecological areas**
    $$Total\_Eco\_Soil = Stock_{Soil}^{Forest} + Stock_{Soil}^{Grass} + ... + Stock_{Soil}^{Wetland}$$
    *(Note: bare land is excluded, as its stock was forced to 0 during allocation)*

* Set the $K_{soil}$ coefficient:
    * PV: IF `avg_slope` < 5 THEN $K=0.2$ ELSE IF `avg_slope` < 25 THEN $K=0.5$ ELSE $K=1.0$.
    * Wind: $K=0.1$ (within an 80 m range, assuming 10% of the area is disturbed).

* **Step C: Compute the final soil loss**
    $$Loss_{Soil} (tC) = Total\_Eco\_Soil \times K_{Poly}$$

---

### Stage 5: Final Assessment

**Purpose:** Aggregate all data and draw conclusions.

**1. Total carbon debt ($Total\_Debt$)**
Note the unit conversion: C $\rightarrow$ CO2 (factor 3.67)

$$Total\_Debt (tCO_2e) = \left[ (Loss_{Bio} + Loss_{Soil}) \times 3.67 \right] + (Capacity \times I_{Mfg})$$

* $I_{Mfg}$: manufacturing carbon intensity (PV ~600, wind ~250)

**2. Carbon payback time ($CPT$)**

$$CPT (Years) = \frac{Total\_Debt}{Capacity \times Hours_{PVOUT} \times EF_{Grid}}$$
