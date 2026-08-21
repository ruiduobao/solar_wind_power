import matplotlib.pyplot as plt
import pandas as pd
import io

# Set global font and font size
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 15  # uniformly increase the font size (original default ~10 -> 15)

# Your data
csv_data = """country_final,Standard_Wind_CPTDays,Standard_Solar_CPTDays,Optimistic_Wind_CPTDays,Optimistic_Solar_CPTDays,Pessimistic_Wind_CPTDays,Pessimistic_Solar_CPTDays
Norway,2532.42,19094.77,1992.72,14879.63,3127.46,23970.22
Sweden,2305.73,11114.80,1808.84,8575.14,2862.21,14179.86
France,836.57,3346.93,661.68,2586.19,1024.09,4257.74
UK,185.98,1397.61,146.14,1080.79,230.22,1776.56
Brazil,306.06,1118.45,242.98,869.12,372.28,1409.80
Canada,234.83,1069.97,184.84,823.33,289.84,1370.38
Germany,179.56,869.49,141.77,677.60,220.47,1091.26
Spain,251.06,801.69,198.48,632.15,307.57,986.42
US,190.56,798.30,150.92,613.98,232.74,1023.61
Japan,141.22,613.22,110.67,463.73,175.60,806.01
Poland,103.00,457.15,81.70,361.13,125.44,560.82
China,119.42,455.66,94.89,353.60,145.03,572.65
Australia,110.36,390.11,87.25,304.72,135.21,487.69
India,106.83,288.20,84.94,226.77,129.59,355.75
South Africa,68.17,194.23,54.20,152.77,82.70,240.02"""

# Read data
df = pd.read_csv(io.StringIO(csv_data))

# Reverse the data order so Norway appears at the top of the Y axis
df = df.iloc[::-1].reset_index(drop=True)

# Create canvas with broken axis (two subplots, left wide right narrow)
fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, figsize=(10, 8), 
                               gridspec_kw={'width_ratios': [4, 1]})
plt.subplots_adjust(wspace=0.05)  # reduce the spacing between the two subplots

# Define colors
color_wind = '#2E8B57'   # SeaGreen (wind-green)
color_solar = '#C71585'  # MediumVioletRed (solar-magenta)

# Plotting loop
for i, row in df.iterrows():
    # Extract data
    country = row['country_final']
    
    # Wind data (S2, S3, S1)
    w_vals = [row['Optimistic_Wind_CPTDays'], row['Standard_Wind_CPTDays'], row['Pessimistic_Wind_CPTDays']]
    
    # Solar data (S2, S3, S1)
    s_vals = [row['Optimistic_Solar_CPTDays'], row['Standard_Solar_CPTDays'], row['Pessimistic_Solar_CPTDays']]
    
    # Y-axis position offset (to stagger them)
    y_wind = i + 0.15
    y_solar = i - 0.15
    
    # Draw on both subplots (display range controlled by xlim)
    for ax in [ax1, ax2]:
        # --- Draw wind (green) ---
        # Draw horizontal line (S3 to S1)
        ax.plot([w_vals[0], w_vals[2]], [y_wind, y_wind], color=color_wind, lw=2, alpha=0.7, zorder=1)
        # Draw endpoints (S3, S1 with vertical lines)
        ax.scatter([w_vals[0], w_vals[2]], [y_wind, y_wind], color=color_wind, marker='|', s=60, zorder=2)
        # Draw center point (S2 with a dot)
        ax.scatter(w_vals[1], y_wind, color=color_wind, marker='o', s=60, edgecolor='white', zorder=3)
        
        # --- Draw solar (magenta) ---
        ax.plot([s_vals[0], s_vals[2]], [y_solar, y_solar], color=color_solar, lw=2, alpha=0.7, zorder=1)
        ax.scatter([s_vals[0], s_vals[2]], [y_solar, y_solar], color=color_solar, marker='|', s=60, zorder=2)
        ax.scatter(s_vals[1], y_solar, color=color_solar, marker='o', s=60, edgecolor='white', zorder=3)

    # Value annotation (Wind) - above the point (drawn on only one axis)
    # Determine which axis range the value belongs to
    if w_vals[1] < 6000: # belongs to the left plot
        ax1.text(w_vals[1], y_wind + 0.25, f'{int(w_vals[1])}', ha='center', va='bottom', 
                fontsize=18, color=color_wind, clip_on=False, fontweight='bold', zorder=10)
    else: # belongs to the right plot
        ax2.text(w_vals[1], y_wind + 0.25, f'{int(w_vals[1])}', ha='center', va='bottom', 
                fontsize=18, color=color_wind, clip_on=False, fontweight='bold', zorder=10)

    # Value annotation (Solar) - below the point (drawn on only one axis)
    if s_vals[1] < 6000: # belongs to the left plot
        ax1.text(s_vals[1], y_solar - 0.25, f'{int(s_vals[1])}', ha='center', va='top', 
                fontsize=18, color=color_solar, clip_on=False, fontweight='bold', zorder=10)
    else: # belongs to the right plot
        ax2.text(s_vals[1], y_solar - 0.25, f'{int(s_vals[1])}', ha='center', va='top', 
                fontsize=18, color=color_solar, clip_on=False, fontweight='bold', zorder=10)

# --- Set broken-axis display ranges ---
# Left subplot: show 0 to 4800 days (covers most data)
ax1.set_xlim(-100, 4800)
# Right subplot: show 8000 to 26000 days (only Sweden and Norway solar)
ax2.set_xlim(8000, 26000)

# --- Hide the inner spines to create the broken effect ---
ax1.spines['right'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.tick_params(left=False, labelleft=False) # right plot does not show Y-axis ticks

# Draw diagonal lines at the break (Diagonal lines)
d = .015 
kwargs = dict(transform=ax1.transAxes, color='k', clip_on=False)
ax1.plot((1 - d, 1 + d), (-d, +d), **kwargs)        
ax1.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  

kwargs.update(transform=ax2.transAxes)  
ax2.plot((-d * 4, +d * 4), (1 - d, 1 + d), **kwargs)  
ax2.plot((-d * 4, +d * 4), (-d, +d), **kwargs)

# --- Set axis labels ---
# Y-axis labels (country names)
ax1.set_yticks(range(len(df)))
ax1.set_yticklabels(df['country_final'], fontsize=17) # font size increased 11->16
ax1.tick_params(axis='y', length=0) # hide tick lines

# X-axis grid
ax1.grid(axis='x', linestyle='--', alpha=0.3)
ax2.grid(axis='x', linestyle='--', alpha=0.3)

# Increase X-axis tick label size
ax1.tick_params(axis='x', labelsize=22) 
ax2.tick_params(axis='x', labelsize=22)

# Overall title and label
fig.text(0.5, 0.02, 'Carbon payback time[days]', ha='center', fontsize=24) # font size increased 12->18
# Remove title
# plt.suptitle('Country-level CPBT Ranking: Solar vs Wind (S1-S2-S3)', fontsize=14, y=0.95)

# --- Custom legend ---
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color=color_wind, lw=2, label='Wind Power'),
    Line2D([0], [0], color=color_solar, lw=2, label='Solar PV'),
    Line2D([0], [0], marker='o', color='gray', linestyle='None', markersize=8, label='S2 Baseline'),
    Line2D([0], [0], marker='|', color='gray', linestyle='None', markersize=10, label='S1-S3 Range')
]
# Legend at lower right, larger font
ax1.legend(handles=legend_elements, loc='lower right', frameon=True, fontsize=15)

plt.show()
