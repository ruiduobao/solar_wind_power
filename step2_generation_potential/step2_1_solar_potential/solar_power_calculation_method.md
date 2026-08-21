https://globalsolaratlas.info/download/world


You should download the **GeoTIFF** file under **`PVOUT`** (photovoltaic power potential). This is the direct source of `Specific Yield` in your calculation formula.

Please find and download this item on the page (I have bolded it for you):

---

PVOUT - Photovoltaic power potential

[kWh/kWp]

- PVOUT - LTAy\_AvgDailyTotals (AAIGrid)
- **PVOUT - LTAy_AvgDailyTotals (GeoTIFF)**  \<-- **click to download this (361.35 MB)**

  - *Data format: GEOTIFF*
  - *File size : 361.35 MB*

---

### Why this one?

1. **It IS the Specific Yield:**

   - **`PVOUT`** represents "photovoltaic power potential" in `kWh/kWp`. This is exactly the definition of `Specific_Yield` in your paper's CPT formula (i.e., how much electricity 1 kW of panels generates).
   - **`GHI`** (Global Horizontal Irradiation) is only "solar radiation" (irradiance). If you download it, you would have to assume the photovoltaic conversion efficiency (Performance Ratio) yourself, and reviewers can easily attack the parameter uncertainty. `PVOUT` already accounts for temperature effects and conversion efficiency, which is more scientific.
2. **LTAy vs LTAm:**

   - **`LTAy`** (Long Term Average **Yearly**): represents the annual mean level. Since your CPT computes "payback years", annual mean data is sufficient. The file is smaller (360MB) and faster to process.
   - `LTAm` (Monthly): monthly data, 4.5GB. Unless you study subtle seasonal issues such as "originally grassland, but in winter the panels are covered by snow and cannot generate", you do not need it.
3. **Key calculation tip (unit conversion):**

   - Note the filename says **`AvgDailyTotals`** (average daily totals).
   - The downloaded TIF pixel value is usually "how many kWh per day" (e.g., 3.5 kWh/kWp/day).
   - When computing Annual\_Gen:

     $$
     Annual\_Gen = Capacity\_MW \times (\text{Pixel\_Value} \times 365.25)
     $$

   * *(Note: if you do not multiply by 365, your payback time will come out as hundreds of years — remember to check the units.)*

**Summary:** download **`PVOUT - LTAy_AvgDailyTotals (GeoTIFF)`** and multiply by 365 in the calculation.



---

This is a very good question. The "suddenly" here — I guess you may have meant **"soil"** or how the two are linked.

In fact, **PVOUT (kWh/kWp) does not need to be directly converted to soil units (t/ha)**. They sit at opposite ends of a fraction in your paper's logic:

- **Numerator:** your previously computed **carbon debt (Total Debt)** — losses from soil and biomass (unit: $tCO_2$).
- **Denominator:** the carbon avoided annually by PV — which requires **PVOUT** to compute (unit: $tCO_2/year$).

Dividing the two cancels out $tCO_2$, leaving **years** — your **CPT**.

To help you avoid errors in code or Excel formulas, I have derived the simplest calculation chain:

### 1. Physical meaning of the PVOUT unit

The `PVOUT` data you download is in `kWh/kWp`, meaning:

> **"At this location, if you install 1 kW, how many kWh can it generate in a year (or a day)."**

But note! The downloaded filename contains **`AvgDailyTotals`**, meaning the pixel value is a **"daily mean"**.

- **Pixel Value** $\approx$ 3.0 ~ 5.0 kWh/kWp/**day**

---

### 2. Core formula derivation (The "Magic" Conversion)

Your PV capacity data (from GRW) is usually in MW (megawatts), while PVOUT is in kW (kilowatts).

There is a very convenient mathematical cancellation that lets you skip tedious $10^3$ conversions.

#### Step 1: Compute annual generation ($Gen_{annual}$)

$$
Gen_{annual} (MWh) = \text{Capacity (MW)} \times \text{Pixel\_Value} \times 365.25
$$

- **Why no unit conversion needed?**

  - Because: $1 \text{ MW} = 1000 \text{ kW}$
  - And: $1 \text{ MWh} = 1000 \text{ kWh}$
  - So: **"MW** **$\times$** **kWh/kW" directly yields MWh**. You do not need to multiply or divide by 1000 at all.
- **Note:** you MUST multiply by **365.25**! Because you downloaded daily-mean data.

#### Step 2: Compute annual avoided emissions ($Emission_{avoided}$)

$$
Emission_{avoided} (tCO_2/yr) = Gen_{annual} (MWh) \times \text{Grid\_Factor} (tCO_2/MWh)
$$

- `Grid_Factor` here is the local grid emission factor (e.g., how much carbon a coal plant emits per kWh).

---

### 3. The final CPT linking formula

Now link "soil/biomass" and "PVOUT" together:

$$
CPT (\text{Years}) = \frac{\text{Total Carbon Debt (soil + biomass + manufacturing)}}{\text{Capacity (MW)} \times \text{Pixel\_Value} \times 365.25 \times \text{Grid\_Factor}}
$$

### A practical example (to self-check)

Assume you have a PV plant in **Inner Mongolia**:

1. **Scale ($C$)** : **100 MW** (from GRW data).
2. **PVOUT ($P$)** : read from the map as **4.2** (unit kWh/kWp/day).
3. **Total carbon debt ($D$)** : from your earlier GIS soil+biomass+manufacturing computation, assume **200,000** **$tCO_2$**.
4. **Grid factor ($EF$)** : China's thermal power is about **0.8** **$tCO_2/MWh$**.

**Calculation:**

1. Annual generation:

   $$
   100 \text{ MW} \times 4.2 \times 365 = 153,300 \text{ MWh}
   $$

- Annual avoided emissions:

  $$
  153,300 \text{ MWh} \times 0.8 = 122,640 \text{ } tCO_2/\text{year}
  $$
- Payback time (CPT):

  $$
  200,000 \div 122,640 = \mathbf{1.63} \text{ years}
  $$

### Summary

You do not need to convert PVOUT to soil units.

- **Soil data** determines how much you owe (the total carbon debt).
- **PVOUT data** determines how fast you "print money" (annual repayment capacity).

Operational reminder:

When processing the PVOUT TIF in GIS or Python, the only processing needed is: read the pixel value $\to$ multiply by 365.25.
