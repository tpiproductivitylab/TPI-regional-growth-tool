import random
from matplotlib.colors import to_rgb, to_hex
import pandas as pd
import json
import colorsys

itlmap = pd.read_csv('itlmapping.csv')

itl1_to_itl2 = itlmap.groupby("itl1name")["itl2name"].apply(list).to_dict()

itl1_to_itl3 = itlmap.groupby("itl1name")["itl3name"].apply(list).to_dict()

itl1_to_mca = itlmap.groupby("itl1name")["mcaname"].apply(list).to_dict()

#add marker colors based on ITL1 names
itl1_colormap = {'Scotland':'rgb(57,151,223)',
        'North East': 'rgb(3,151,157)',
        'North West': 'rgb(111,194,89)',
        'Northern Ireland': 'rgb(186,224,42)',
        'Yorkshire and The Humber':'rgb(209,220,35)',
        'Wales': 'rgb(231,215,27)',
        'West Midlands': 'rgb(232,174,45)',
        'East Midlands': 'rgb(233,143,58)',
        'East': 'rgb(235,94,80)',
        'South West': 'rgb(174,66,103)',
        'South East': 'rgb(149,54,113)',
        'London': 'rgb(108,35,128)',
        }

random.seed(200)

def rgb_to_tuple(rgb_str):
    return tuple(map(int, rgb_str.strip('rgb()').split(',')))

def hsl_to_rgb(h, s, l):
    """Convert HSL to RGB (values in range 0–255)."""
    r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
    return int(r * 255), int(g * 255), int(b * 255)

def generate_randomized_colors(num_colors, base_hue=0, saturation=70, lightness=50, hue_variation=20, lightness_variation=10):
    """
    Generate colors with uniform spacing and random variations.
    
    Args:
    - num_colors: Number of colors to generate.
    - base_hue: Starting hue (0–360 degrees).
    - saturation: Fixed saturation value (0–100%).
    - lightness: Fixed lightness value (0–100%).
    - hue_variation: Max random change to hue.
    - lightness_variation: Max random change to lightness.

    Returns:
    - List of hex color strings.
    """
    hues = [(base_hue + i * (360 // num_colors)) % 360 for i in range(num_colors)]
    colors = []
    for h in hues:
        randomized_h = (h + random.randint(-hue_variation, hue_variation)) % 360
        randomized_l = max(0, min(100, lightness + random.randint(-lightness_variation, lightness_variation)))
        r, g, b = hsl_to_rgb(randomized_h, saturation, randomized_l)
        colors.append(f'#{r:02x}{g:02x}{b:02x}')
    return colors

# Generate ITL2 colormap with uniform colors
itl2_colormap = {}
for itl1, itl2_regions in itl1_to_itl2.items():
    num_regions = len(itl2_regions)
    base_color = rgb_to_tuple(itl1_colormap[itl1])
    base_hue = colorsys.rgb_to_hls(*[x / 255.0 for x in base_color])[0] * 360
    region_colors = generate_randomized_colors(num_regions, base_hue=base_hue)
    itl2_colormap.update(dict(zip(itl2_regions, region_colors)))

# Similar for ITL3 and MCA
itl3_colormap = {}
for itl1, itl3_regions in itl1_to_itl3.items():
    num_regions = len(itl3_regions)
    base_color = rgb_to_tuple(itl1_colormap[itl1])
    base_hue = colorsys.rgb_to_hls(*[x / 255.0 for x in base_color])[0] * 360
    region_colors = generate_randomized_colors(num_regions, base_hue=base_hue)
    itl3_colormap.update(dict(zip(itl3_regions, region_colors)))

mca_colormap = {}
for itl1, mca_regions in itl1_to_mca.items():
    num_regions = len(mca_regions)
    base_color = rgb_to_tuple(itl1_colormap[itl1])
    base_hue = colorsys.rgb_to_hls(*[x / 255.0 for x in base_color])[0] * 360
    region_colors = generate_randomized_colors(num_regions, base_hue=base_hue)
    mca_colormap.update(dict(zip(mca_regions, region_colors)))

data = [itl1_colormap, itl2_colormap, itl3_colormap, mca_colormap]

with open("colormaps.json", "w") as file:
    json.dump(data, file, indent=4)
