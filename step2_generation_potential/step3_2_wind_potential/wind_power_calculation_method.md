This is a very critical choice! To match the `Annual_Gen` calculation in your **carbon payback time (CPT) formula**, you need to select data that most directly represents "generation capability" rather than "wind resource".

### 1. Which layer should you choose? (Layer)

In the dropdown, select: **`CAPACITY-FACTOR_IEC2`**

- **What is it?**

  - **Capacity Factor** is the ratio of a turbine's actual electricity generation to its theoretical maximum generation (percentage, 0-1.0).
  - **IEC2** stands for **IEC Class II** turbines. This is the most mainstream turbine class for global onshore wind, suitable for medium wind-speed regions.
  - *Note: IEC1 is for extreme high-wind areas, IEC3 for low-wind areas. For a global-scale study, IEC2 is the safest "average assumption".*
- **Why not** **`POWER-DENSITY`**?
  - Although power density reflects "resource endowment", it is in **$W/m^2$** (physical energy). If you use it, you would have to assume blade diameter, conversion efficiency formulas yourself, making the calculation extremely complex.
  - **`CAPACITY-FACTOR`** is the "finished product" officially computed by applying a standard turbine curve; it directly corresponds to the **generation efficiency** you need. It is the wind equivalent of `PVOUT` in solar.

### 2. Which height? (Height)

Select: **`100`**

- **Reason:**

  - Your study period is **2017-2024**.
  - During this period, the hub height of mainstream global onshore turbines is usually between **80m and 120m**.
  - **100m** is the most commonly used representative height in recent academic global wind assessments. Choosing 10m or 50m would severely underestimate modern turbine output.

---

### 3. Formula correction after download (Important!)

The `PVOUT` unit for solar is `kWh/kWp`, while the wind `Capacity Factor` is a `percentage` (or a 0-1 decimal). **Your formula needs to be adapted:**

$$
Annual\_Gen (MWh) = Capacity (MW) \times \text{Pixel\_Value} \times 8760
$$

- **Capacity (MW):** your GRW wind farm installed capacity.
- **Pixel_Value:** the capacity factor (e.g., 0.35 or 35%). *Note: if the downloaded data is an integer 0-100, remember to divide by 100.*
- **8760:** hours in a year ($24 \times 365$).

**Summary of operations:**

1. Select **`CAPACITY-FACTOR_IEC2`** as the layer.
2. Select **`100`** as the height.
3. Remember to multiply by **8760** in your calculation.

---

This is a very sharp, fundamental question. Your intuition is completely correct — **region (wind resource) does affect turbine selection**.

However, when building a global-scale assessment model, the reason we *prefer "time"* as the primary variable for rated power, and treat "region" as a correction variable (mainly for rotor diameter), is that the underlying industrial logic of the wind industry has changed.

Simply put: **"Time" determines the upper limit of industrial capability (how large can be built), while "region" determines the lower limit of specific configuration (how large the blades should be).**

Below is a detailed logic breakdown and correction suggestions for your model:

### 1. Why is "time" the primary factor determining rated power?

Because turbines are not "tailor-made" like a tailor making clothes; they are produced on "platforms" like cars.

- **Inter-generational lock-in of industrial capability:**

  - **2017:** Whether in the North Sea with extremely strong winds or inland with weak winds, the most mature and cost-effective onshore turbine platform in the global supply chain was the **2.0MW - 2.5MW** class. Even if you wanted to install a 6MW turbine in a windy place, the technology was extremely expensive and immature (the supply chain could not deliver it).
  - **2024:** Advances in technology (materials, control algorithms, generator efficiency) made the **4.0MW - 6.0MW** platform the "standard product". By then, regardless of location, developers would prefer these large-power platforms to reduce the levelized cost of energy (LCOE).

**Conclusion:** In any given year, the **"mainstream rated power" is determined by the global supply chain level of that time, not by wind speed.** This is why the model must use a "time axis" to set the power baseline (Base Value).

### 2. Where does regional difference appear? — "Specific power" (swept area per kilowatt)

Since everyone uses a 4MW platform, how do high-wind and low-wind areas differ? The answer: **change the blades (change the rotor diameter)**.

This is a key concept in the wind industry: **same power, different rotors**.

- **High wind-speed regions (IEC Class I, e.g., coastal Scotland):**

  - **Strategy:** Wind is strong; you do not need very long blades to reach 4MW. Overly long blades may even be damaged by the wind.
  - **Configuration:** 4.0 MW nacelle + **130m** rotor diameter.
- **Low wind-speed regions (IEC Class III, e.g., inland central-eastern China):**

  - **Strategy:** Wind is weak; you need a huge "wind-catching net" to reach 4MW in gentle breezes.
  - **Configuration:** 4.0 MW nacelle + **165m** rotor diameter.

Case validation:

Take the Vestas EnVentus platform as an example:

- It has a **V150-6.0 MW** model (150m rotor), designed for medium-to-high wind speeds.
- It also has a **V162-6.2 MW** model (162m rotor), designed for medium-to-low wind speeds.
- **Notice: power is nearly the same (6.0 vs 6.2), but the rotors differ by 12 meters.**

### 3. What does this mean for your LCA model?

Your earlier question — "isn't power different in different places" — should be translated in model terms to: **"in different places, at the same power, the land footprint (disturbance radius) differs".**

If your model adjusts "power" by "region" alone, you may make a mistake:

- **Wrong logic:** "Here the wind is weak, so install a small turbine (e.g., 1MW)." → **Wrong.** Small turbines have lower generation efficiency in low winds and higher unit construction costs.
- **Correct logic:** "Here the wind is weak, so we should install an advanced unit with **large blades** (e.g., 4MW with a 170m rotor) to capture more wind energy."

### 4. Corrected model parameter strategy

To make your assessment both scientific and consistent with industrial facts, we recommend a two-layer logic: **"time sets power, region sets radius"**.

#### Layer 1: Time dominance (determines Generator Capacity)

Set the "mainstream platform power" for each year. This represents the technological ceiling of that year.

- 2017: 2.2 MW
- 2020: 3.2 MW
- 2024: 5.0 MW

#### Layer 2: Regional correction (determines Rotor Radius & Disturbance Area)

Based on the **wind class** in your GIS maps, correct the **disturbance radius** of each turbine.

| **Wind class** | **Typical regions**                     | **Model operation (Rotor Adjustment)**                     | **Impact on soil disturbance**                       |
| -- | ---------------------- | ---------------------- | ------------------------ |
| **High wind (Class I)** | Coastal, mountain passes, offshore     | Use **standard radius** (Standard Rotor) | Normal disturbance area (baseline)  |
| **Medium wind (Class II)** | Plains, conventional land       | Increase radius by **5% - 10%**             | Slightly increased disturbance area           |
| **Low wind (Class III)** | Inland low-wind areas, mountain basins | Increase radius by **15% - 20%**             | **Significantly increased disturbance area** (wider roads needed to transport large blades) |

### Summary

You do not need to change the "rated power" setting by region (that is determined by the era); what you need to change is **"land footprint per MW"**.

In low wind-speed regions, to reach the same 4MW, developers must install larger blades, which means **wider transport roads** and **larger swept areas (ecological impact zones)**. This is exactly the focus of your study: **promoting wind power in low wind-speed regions often carries a higher ecological cost per unit of energy (Ecological Cost per MWh).**

---

This is a solid and forward-looking research design. Combining "equipment manufacturing (static carbon debt)" with "land-use change (dynamic ecological debt)" precisely captures the pain point of the current life cycle assessment (LCA) field.

Regarding your question on **wind turbine rated power setting**, and the findings in your survey report on spatial disturbance and carbon-pool loss, here are parameterization suggestions based on the 2017-2024 technology iteration characteristics.

### Core suggestion: abandon a single mean; use "time-step dynamic parameters"

2017 to 2024 was a period of "giantization" in wind technology. If you use a single rated power for the whole period (e.g., a mean of 3 MW), early **carbon debt would be underestimated** (because more units were needed per MW at that time) and later **disturbance would be misjudged** (large turbines have larger per-unit disturbance but fewer total units).

We suggest setting up **three-stage gradient parameters** in the model:

#### 1. Dynamic setting of rated power and physical dimensions

You need to establish the correspondence between "rated power" and "rotor diameter" (the basis of the 80m disturbance radius).

| **Time window** | **Recommended rated power (Onshore)** | **Rotor diameter**                 | **Corresponding disturbance characteristics**                                                                                                                                |
| -- | -- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| **2017-2018** | **2.0 - 2.2 MW** | ~110 m       | Lower towers, shorter blades. **High density**: more turbines per square kilometer, dense road networks, greatest impact on land fragmentation.                                            |
| **2019-2021** | **2.8 - 3.2 MW** | ~127 m       | Transition-period mainstream class. Longer blades significantly increase transport-road turning radii; **extra earthwork from wider roads** becomes prominent.                                                |
| **2022-2024** | **3.8 - 4.5+ MW** | ~140m - 160m | Giantization era. Larger per-unit capacity, **fewer turbine positions**, but per-point hardstand area surges to nearly 1 acre (~0.4 ha), with very high foundation bearing requirements and severe deep-soil compaction. |

**Parameter setting strategy:**

- **Formula-based linkage:** In your GIS model, do not input power directly; input a **disturbance weight** derived from power.
- **Correction coefficient:** A 2024 4MW turbine, despite doubling per-unit power, does not double its physical footprint (concrete + hardstand + roads). Data show that direct land use per MW actually shows a **declining trend** (from ~1 ha/MW to ~0.75 ha/MW).

  - Therefore, we suggest keeping your **wind manufacturing carbon intensity (200-250 t/MW) relatively constant or slightly decreasing, but dynamically increasing the land disturbance radius by year** (from 50m → 80m).

---

### 2. Deep corrections to your survey report

Two points in your current survey conclusions are very important; I suggest refining them as follows to enhance model robustness:

#### A. The "50m vs 80m buffer" (spatial fingerprint validation)

Your "80m radius (~2 ha)" is a very accurate engineering estimate; it corrects the bias of considering only the tower base.

- **Logical support:** Modern turbine blades exceed 70m in length; the transport road swept path and straight-section width (increasing from 4.5m to over 6m) do expand the disturbance range.
- **Ecological fragmentation:** The 80m radius is not only physical coverage, but also the zone where **ecological edge effects** occur. In forest ecosystems, soil microclimate (humidity, temperature) within 50-100m on both sides of roads changes, accelerating soil respiration. You can confidently define this 80m as a "carbon-pool-function damaged zone" rather than a simple "occupied zone".

#### B. PV "site grading" and soil carbon loss (20%-50% range)

Your identification of "grading" as the culprit is very sharp. Shading alone has little impact on carbon pools, and can even have positive effects in arid regions (reducing evaporation).

- **Set categorical coefficients:** Rather than applying a uniform 20-50% loss rate to all PV projects, weight by **slope**:

  - **Plain/desert PV (slope < 2°):** Almost no earthwork. Set **$C_{loss} \approx 5-10\%$** (only topsoil compaction).
  - **Hilly/mountain PV (slope > 5°):** Must "cut peaks and fill valleys" to accommodate single-axis trackers. Set **$C_{loss} \approx 40-50\%$** (deep soil exposure, strong oxidation).
- **Reason:** During 2017-2024, high-quality flat land declined, and PV is increasingly built on sloped terrain, so the global average soil carbon loss coefficient in later years should show an **upward trend**.

---

### 3. Benchmarking manufacturing carbon debt vs. ecological carbon debt (your model loop)

Your manufacturing emission baselines (PV ~600t, Wind ~250t) are reasonable, but note the **system boundary**:

- **Wind (250 t/MW):** This value mainly covers tower (steel), blades (composites), and nacelle. **Note:** many LCA studies do not include **concrete foundation** emissions. For onshore wind, the large gravity foundation consumes substantial cement, potentially adding 10-20% embodied carbon. Please confirm whether the foundation is included in your calculation.
- **PV (600 t/MW):** This value may be slightly high in 2024 (as wafers get thinner and hydropower-based silicon increases), but it is accurate for 2017-2020. Since your study spans periods, using 600 as a weighted average is safe.

### Summary: your next steps

1. **Turbine power:** Use a piecewise function (2017: 2.2MW → 2024: 4.0MW) and compute the annual number of newly added turbines accordingly.
2. **Disturbance radius:** Link the wind disturbance radius to per-unit capacity (e.g., $R_{disturbance} = 20 \times \sqrt{P_{rated}}$, or simple piecewise settings of 50m/65m/80m).
3. **PV loss:** Introduce DEM (digital elevation model) data; if global DEM overlay is infeasible, give mountain projects higher soil-loss weights based on regional terrain characteristics.

Your research path is very clear: mapping "physical engineering parameters" to "ecological processes" is the key to fixing the overestimation problem in current carbon-neutrality assessments.

---

This is an excellent intuitive question! It touches the most core conceptual distinction in the energy field: **"Capacity" vs "Generation"**.

The confusion comes from understanding "rated power" as *"what it is always doing"*, when in fact "rated power" refers to *"the limit it can reach when pushing itself"*.

Let me use the most intuitive example to break this misconception:

### 1. Core misconception: it is not a "constant", it is a "ceiling"

- **Your understanding:** Rated power 3MW = this machine **steadily** generates 3MW every hour.
- **Reality:** Rated power 3MW = this machine **only when wind speed is perfect** (e.g., 12 m/s) can instantly generate 3MW.

If the wind is weaker (e.g., 6 m/s), it may generate only **0.5 MW**; if there is no wind, it generates **0 MW**.

### 2. Intuitive analogy: a Ferrari

Imagine you buy a Ferrari:

- **Rated power** = **top speed of 300 km/h** (the limit ability the manufacturer stamps on the nameplate).
- **Time** = you drive for **1 hour**.
- **Actual distance (Generation)** = ?

If you drive for 1 hour, must you cover 300 km?

Impossible. Because there is traffic, traffic lights, and speed limits. You may actually cover only 60 km.

Here:

- **300 km/h** is the **turbine's rated power** (theoretical limit).
- **60 km** is the **actual annual generation**.
- **0.2 (60/300)** is the **capacity factor (CF)**. Normally you can only achieve 20% of its performance.

### 3. Why multiply by the capacity factor (CF)?

Back to the formula:

$$
\text{Annual Generation} = \underbrace{\text{Turbine Rated Power} \times 8760}_{\text{theoretical maximum}} \times \text{Capacity Factor (CF)}
$$

- **The first part ($\text{Power} \times 8760$):** assumes the turbine runs at full load **365 days a year, every minute of every second**. This is physically impossible unless you mount it in a wind tunnel blowing forever.
- **Capacity factor (CF):** this is a **"discount coefficient"**. It represents the harshness of reality — sometimes there is no wind, sometimes wind is too weak, sometimes it is too strong and the turbine must shut down for protection, sometimes the machine needs maintenance.

### 4. Summary

- **Rated power (MW):** determines the **upper limit** of how much wind this machine can consume (determines cost and equipment size).
- **Capacity factor (CF):** determines how much of the time the local **wind resource** can feed it (determines payback speed).

Therefore, the capacity factor is **essential**. Without it, your calculated electricity assumes the turbine runs at full capacity like a "perpetual motion machine", overestimating by 2-4 times, which would make your carbon payback assessment completely wrong.

---

- **Rated power (MW):** determines the **upper limit** of how much wind this machine can consume (determines cost and equipment size).
- **Capacity factor (CF):** determines how much of the time the local **wind resource** can feed it (determines payback speed).
