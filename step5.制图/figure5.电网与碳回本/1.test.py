import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from scipy.optimize import curve_fit

# ---------------- 1. Simulated data preparation (replace with your real data) ----------------
# Simulate 460k facility records
np.random.seed(42)
grid_ef = np.random.uniform(0.05, 1.2, 5000) # grid emission factor
cpbt = 150 / grid_ef + np.random.normal(0, 50, 5000) # simulated hyperbolic relationship + noise
cpbt = np.clip(cpbt, 10, 5000)
df_facilities = pd.DataFrame({'Grid_EF': grid_ef, 'CPBT': cpbt})

# Simulate country deviation data (CPBT_Local - CPBT_Global)
global_mean_cpbt = 752 # baseline scenario solar average
countries = ['Norway', 'Sweden', 'France', 'Brazil', 'Global Mean', 'USA', 'Germany', 'China', 'India', 'South Africa']
deviations = [2000, 1500, 800, 500, 0, -100, -200, -400, -500, -600]
df_bar = pd.DataFrame({'Country': countries, 'Deviation': deviations})
df_bar = df_bar.sort_values('Deviation', ascending=True)

# ---------------- 2. Global plotting settings ----------------
plt.rcParams['font.family'] = 'Arial'
fig = plt.figure(figsize=(18, 5))
gs = fig.add_gridspec(1, 3, width_ratios=[1, 1.2, 1])

# ------------- (a) Hyperbolic relationship plot (Scatter Density + Curve) -------------
ax1 = fig.add_subplot(gs[0])
# Use hexbin for high-density visualization of many points
hb = ax1.hexbin(df_facilities['Grid_EF'], df_facilities['CPBT'], gridsize=40, cmap='Blues', mincnt=1)

# Fit the hyperbolic function y = a/x + b
def hyperbolic(x, a, b):
    return a / x + b
popt, _ = curve_fit(hyperbolic, df_facilities['Grid_EF'], df_facilities['CPBT'])
x_fit = np.linspace(0.05, 1.2, 100)
y_fit = hyperbolic(x_fit, *popt)

ax1.plot(x_fit, y_fit, color='red', linewidth=2.5, label='Fitted Hyperbola ($CPBT \propto 1/EF_{grid}$)')
ax1.set_xlabel('Grid Emission Factor ($tCO_2e/MWh$)', fontsize=12)
ax1.set_ylabel('Carbon Payback Time (Days)', fontsize=12)
ax1.set_title('(a) The Grid Decarbonization Penalty', fontsize=14, fontweight='bold')
ax1.set_ylim(0, 4000)
ax1.legend(loc='upper right')
ax1.grid(True, linestyle='--', alpha=0.5)

# ------------- (b) CPBT deviation map -------------
ax2 = fig.add_subplot(gs[1])
# Load the built-in world map basemap
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world = world[(world.pop_est > 0) & (world.name != "Antarctica")]

# Simulate merging deviation data into the map (random deviations generated here for demo)
world['Deviation'] = np.random.uniform(-800, 1000, len(world)) 

# Plot a Choropleth map with diverging colormap RdBu_r, center at 0 (vmin=-1000, vmax=1000)
world.plot(column='Deviation', ax=ax2, cmap='RdBu_r', 
           vmin=-1000, vmax=1000,
           legend=True, legend_kwds={'label': "CPBT Deviation (Days)", 'orientation': "horizontal", 'shrink': 0.6})
ax2.set_title('(b) Global CPBT Deviation Map', fontsize=14, fontweight='bold')
ax2.axis('off')

# ------------- (c) CPBT deviation ranking for typical countries -------------
ax3 = fig.add_subplot(gs[2])
# Assign colors by sign: negative in blue tones, positive in red tones
colors = ['#2b83ba' if x > 0 else '#d7191c' for x in df_bar['Deviation']] # Norway (positive deviation) lengthens CPBT, China (negative deviation) shortens CPBT

sns.barplot(x='Deviation', y='Country', data=df_bar, palette=colors, ax=ax3)
ax3.axvline(0, color='black', linewidth=1)
ax3.set_xlabel('CPBT Deviation ($CPBT_{Local} - CPBT_{Global}$)', fontsize=12)
ax3.set_ylabel('')
ax3.set_title('(c) CPBT Deviation by Country', fontsize=14, fontweight='bold')

# Highlight key countries (optional: bold the Y-axis labels of specific countries)
for tick_label in ax3.get_yticklabels():
    if tick_label.get_text() in ['Norway', 'Brazil', 'China', 'India']:
        tick_label.set_fontweight('bold')

plt.tight_layout()
plt.show()
