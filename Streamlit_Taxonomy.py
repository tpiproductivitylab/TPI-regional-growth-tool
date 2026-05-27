import streamlit as st
# import streamlit_antd_components as sac
# #Check out additional options, also for data display: https://nicedouble-streamlitantdcomponentsdemo-app-middmy.streamlit.app/
import pandas as pd
import graphs
import numpy as np
import textwrap
# import plotly.io as pio
import io
import time
# Streamlit-app
import os
from groq import Groq

api_key = os.getenv("groq_key") or st.secrets["groq_key"]
client = Groq(api_key = api_key)
 
@st.cache_data
def load_data():
    t0 = time.time()
    data = pd.read_csv('src/regional_growth_tool_scatter.csv', index_col = [0,1,2,3])
    itlmapping = pd.read_csv('src/itlmapping.csv')

    print("Runtime loading data: " + str(int((time.time() - t0)*1000)) + " miliseconds")
    return data, itlmapping

@st.cache_data
def load_indicators():
    indicators = pd.read_csv('src/regional_growth_tool_indicators.csv', index_col=[3,1]).drop(columns={'level', 'name', 'GVA per hour worked'})
    return indicators

@st.cache_data
def process_data(data, itlmapping, start, year, levels, region, customregion, include_itl1):
    t0 = time.time()

    period =  list(range(start,year+1))
    volume = 'Change in GVA per hour' #Use data in constant prices
    nominal = 'GVA per Hour' #Nominal 2019 data used by Bart is smoothed GVA per hour worked



    # '''Do this more efficienty, essentially create a new dataframe with 3 columns:
    #     start year volume, end year volume and end year nominal,
    #     divide the end year volume by start year volume and subtract 1.
    #     This gives the data we need, no need for aggregation or natural logs,
    #     perhaps no need for numpy either.
    #     See if we can combine all data in 1 dataframe, including UK average
    #     '''

    #Select productivity data from the output frame
    dta = data.loc[(slice(None), slice(None), slice(None), period), [volume, 'Population']]



    #Create a new column with the log growth of the productivity level
    dta['Log percentage change'] = np.log(dta[volume]).groupby(['level', 'code', 'name']).diff()
    median_population = dta['Population'].median()
    dta['Population'] = dta['Population'].fillna(median_population)
     #finally calculate the growth average over the period
    #create new dataframe for the aggregates over the period
    dtaAgg = pd.DataFrame()
    dtaAgg['Population'] = dta['Population']
    dtaAgg['Average Annual log percentage change'] = dta['Log percentage change'].groupby(['level', 'code', 'name']).mean()
    #Calculate the total growth over the period and add in new column
    dtaAgg['Log percentage change'] = dta['Log percentage change'].groupby(['level', 'code', 'name']).sum()
    #Calculate regular percentage growth
    dtaAgg['Average Annual percentage change'] = (np.exp(dtaAgg['Average Annual log percentage change']) - 1)
    dtaAgg['Percentage change'] = (np.exp(dtaAgg['Log percentage change']) - 1)

    #Add the nominal data
    dtaAgg['GVA per hour'] = data.loc[(slice(None), slice(None), slice(None), year), nominal].droplevel('year', axis = 'index')

    #Select data to plot
    selected = itlmapping.loc[itlmapping['itl1name'].isin(region), :]
    all_selected_values = [item for level in levels for item in selected[level.lower() + 'name'].unique()]
    # Remove empty for ITL3s with no MCA parent
    all_selected_values = [x for x in all_selected_values if x == x and x is not None]
    dtaselected = pd.DataFrame()
    for level in levels:
        temp = dtaAgg.loc[(level, slice(None), all_selected_values, year),:]
        dtaselected = pd.concat([dtaselected, temp])

    #Add names names for aggregate regions and scorecard data:
    itl_dropset = {'mca': ['itl2', 'itl2name', 'itl3', 'itl3name'], 
                   'itl1': ['itl2', 'itl2name', 'itl3', 'itl3name'], 
                   'itl2': ['itl3', 'itl3name'], 
                   'itl3': []}

    levels = [level.lower() for level in levels]
    dtaselected = dtaselected.reset_index()
    concatenated_df = pd.DataFrame()
    for level in levels:
        temp = dtaselected.copy()
        itlmapping_itl = itlmapping.drop(itl_dropset[level], axis = 'columns').drop_duplicates()
        temp = temp.join(itlmapping_itl.set_index(level), on = 'code')

        concatenated_df = pd.concat([concatenated_df, temp], ignore_index=True)
        
    dtaselected = concatenated_df
    dtaselected = dtaselected.set_index(['level', 'code', 'name', 'year'])


    #Check custom selection of regions, and update selected data accordingly
    if customregion != None and len(customregion) > 1:
        #print(customregion)
        dtaselected = dtaselected.loc[(slice(None), slice(None), customregion, year), :]

    #Sort values according to ITL1 region
    sorter = ['Scotland', 'North East', 'North West', 'Northern Ireland', 'Yorkshire and The Humber', 'Wales', 'West Midlands', 'East Midlands', 'East', 'South West', 'South East', 'London']
    for i, v in enumerate(sorter):
        dtaselected.loc[dtaselected['itl1name'] == v, 'sorter'] = i
    del i, v, sorter

    #Sort data by the indicator for the bubble size (in this case population)
    # dtaselected = dtaselected.sort_values(by = 'pop', ascending = False)
    dtaselected = dtaselected.sort_values(by = 'sorter', ascending = True)

    #Break region names
    dtaselected = dtaselected.reset_index('name')
    dtaselected['name'] = ['<br>'.join(textwrap.wrap(x, width = 15)) for x in dtaselected['name']]
    dtaselected = dtaselected.set_index('name', append = True)

    dtaselected = dtaselected.drop_duplicates()

    dtaselected = dtaselected.droplevel('year')
    dtaAgg = dtaAgg.droplevel('year')
    
    dtaITL1 = None
    if include_itl1:
        selected_itl1_names = itlmapping.loc[itlmapping['itl1name'].isin(region), 'itl1name'].unique()
        itl1_temp = dtaAgg.loc[('ITL1', slice(None), list(selected_itl1_names)), :]
        itl1_temp = itl1_temp.reset_index()
        itlmapping_itl1 = itlmapping[['itl1', 'itl1name']].drop_duplicates()
        itl1_temp = itl1_temp.join(itlmapping_itl1.set_index('itl1'), on='code')
        itl1_temp = itl1_temp.drop(columns='Population').drop_duplicates()
        dtaITL1 = itl1_temp.set_index(['level', 'code', 'name']).drop_duplicates()

    print("Runtime data processing: " + str(int((time.time() - t0)*1000)) + " miliseconds")
    return dtaAgg, dtaselected, dtaITL1

def generate_insight():
    insight_text = """Data overview:
    London and the South East >"""
    return insight_text

def main():
    st.set_page_config(layout="wide", page_icon="favicon.ico", page_title="UK Regional Productivity Growth")
    data, itlmapping = load_data()

    t0 = time.time()

    #Define sidebar

    #Sidebar logo 
    #Embed the logo as HTML. This allows the logo to also be a link, and stops Streamlit showing the 'enlarge image' icon 
    st.sidebar.html("<a href='https://lab.productivity.ac.uk' alt='The Productivity Lab'></a>")

    #Back button
    #Embed the button as styled HTML. This stops the link opening in a new tab (like st.link_button enforces)
    # st.markdown("""
    #     <style>
    #         a.btn {
    #             color: rgb(49, 51, 63);
    #             border: 1px solid rgba(49, 51, 63, 0.2);
    #             background-color: rgb(249, 249, 251);
    #             border-radius: 6px;
    #             padding: 8px 12px;
    #             text-decoration: none;
    #         }
    #         a.btn:hover {
    #             color: rgb(255, 75, 75);
    #             border: 1px solid rgb(255, 75, 75);
    #         }
    #     </style>
    #     """, unsafe_allow_html=True)

    # st.sidebar.html("<a class='btn' href='https://lab.productivity.ac.uk/tools/uk-regional-productivity-growth/'>Back to the Productivity Lab</a>")

    #Alternative logo
    # Add an app logo. This is the new 'official' way to add logos. The logo still appears when the sidebar is collapsed (you can use 'icon_image' to specify a smaller version, if preferred). 
    # I created a rough example logo (static/logo.png) as an illustration
    # Must be 24px x 240px max and 10:1 aspect ratio
  
    st.logo("static/logo.png", link="https://lab.productivity.ac.uk/", icon_image=None)
    query_params = {k.lower(): v.lower() for k, v in st.query_params.items()}
    if 'level' in query_params.keys():
        levels_default = []
        levels = [l.strip().lower() for l in query_params['level'].split(",")]
        for level in ['ITL3', 'ITL2', 'ITL1', 'MCA']:
            if level.lower() in levels:
                levels_default.append(level)
        if not levels_default:
            levels_default = 'ITL3'
    else:
        levels_default = 'ITL3'
    if 'itl1' in query_params.keys():
        itl1_default = []
        itl1s = [l.strip().upper() for l in query_params['itl1'].split(",")]
        print(itl1s)
        print(data)
        for itl1 in list(data.reset_index().loc[data.reset_index()['level'] == 'ITL1', 'code'].unique()):
            if itl1.upper() in itl1s:
                itl1_default.append(itl1)
            if itl1.upper() == 'ALL':
                itl1_default.append('All')
        if not itl1_default:
            itl1_default = ['All']
    else:
        itl1_default = ['All']
    if 'size' in query_params.keys():
        try:
            size_default = float(max(min(2, float(query_params['size'])), 0.65))
        except:
            size_default = 0.75
    else:
        size_default = 0.75
    if 'label' in query_params.keys():
        if query_params['label'] == 'True' or query_params['label'] == '1':
            showlabel_default = True
        else:
            showlabel_default = False
    else:
        showlabel_default = False
    if 'population' in query_params.keys():
        if query_params['population'] == 'True' or query_params['population'] == '1':
            population_default = True
        else:
            population_default = False
    else:
        population_default = False
    #Data selection tools
    st.sidebar.divider()
    # Experimental
    threeD = st.sidebar.toggle(label='3D mode', value=False)
    #threeD = False
    if threeD:
        indicators = load_indicators()
        z = st.sidebar.selectbox('Select indicator for 3rd axis:', indicators.columns)
    st.sidebar.subheader('Select data to plot')
    # Set years to max period
    year = st.sidebar.slider('Time Period:', 2008, max_value=int(max(data.index.unique(level='year'))),
        value=[2008, int(max(data.index.unique(level='year')))])
    if year[0] == year[1]:
        year = [year[0], year[0] + 1] if year[0] < int(max(data.index.unique(level='year'))) else [year[0] - 1, year[0]]

    indicator_bounds = {'Export Intensity': [2016, 2023],
                        'New Businesses': [2017, 2023],
                        'Low Skilled': [2016, 2023],
                        'High Skilled': [2016, 2023],
                        'Active': [2016, 2023],
                        'Inactive due to Illness': [2016, 2023],
                        'Working Age': [2016, 2023],
                        '5G connectivity': [2023, 2023],
                        'Gigabit connectivity': [2021, 2023],
                        'GFCF per job': [2008, 2020],
                        'ICT per job': [2008, 2020],
                        'Intangibles per job': [2008, 2020]}
    
    if threeD and (year[1] < indicator_bounds[z][0] or year[1] > indicator_bounds[z][1]):
        year = (year[0], indicator_bounds[z][1])
        st.sidebar.error(f'Indicator data only available between {indicator_bounds[z][0]}-{indicator_bounds[z][1]}')
    
    color_mapping = {
        'ITL3': '#d63f3f',
        'ITL2': '#3F7CD6',
        'ITL1': '#713AB7',
        'MCA': '#3FB9B1'
    }

    # Inject custom CSS to style the selected tags
    st.markdown(f"""
        <style>
        /* Style tags for selected options */
        span[data-baseweb="tag"][aria-label*="ITL3"] {{
            background-color: {color_mapping['ITL3']} !important;
            color: white !important;
        }}
        span[data-baseweb="tag"][aria-label*="ITL2"] {{
            background-color: {color_mapping['ITL2']} !important;
            color: white !important;
        }}
        span[data-baseweb="tag"][aria-label*="ITL1"] {{
            background-color: {color_mapping['ITL1']} !important;
            color: white !important;
        }}
        span[data-baseweb="tag"][aria-label*="MCA"] {{
            background-color: {color_mapping['MCA']} !important;
            color: white !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    level_options_mapping = {
    'ITL3': ['ITL1', 'ITL2', 'ITL3', 'MCA'],
    'ITL2': ['ITL1', 'ITL2', 'MCA'],
    'ITL1': ['ITL1'],
    'MCA': ['ITL1', 'MCA']
}

    # Multiselect box
    levels = st.sidebar.multiselect(
        'Geographical Aggregation Level:',
        options=['ITL3', 'ITL2', 'ITL1', 'MCA'],
        default=levels_default
    )
    itl1_default = itlmapping.loc[itlmapping['itl1'].isin(itl1_default), 'itl1name'].unique()
    selected_regions = st.sidebar.multiselect('Select ITL1 region(s):', options = list(itlmapping['itl1name'].unique()) + ['All'], default = itl1_default)


    if 'All' in selected_regions or selected_regions == []:
        selected_regions = list(itlmapping['itl1name'].unique())

    if levels == []:
        levels = ['ITL3']
    
    # Get unique colour options from selected levels
    available_color_levels = set(level_options_mapping[levels[0]])
    for level in levels[1:]:
        available_color_levels &= set(level_options_mapping[level])

    color_level = st.sidebar.selectbox('Select colour level:', options=sorted(available_color_levels))
    
    regs = []
    for level in levels:
        regs.extend(itlmapping.loc[itlmapping['itl1name'].isin(selected_regions), level.lower() + 'name'].unique())
    # Remove empty for ITL3s with no MCA parent
    regs = [x for x in regs if x == x and x is not None]
    css = ""
    for level, name in data.reset_index()[['level', 'name']].drop_duplicates().values:
        if level not in levels:
            continue
        # Create a CSS selector for each combination of level and name
        css += f"""
        span[data-baseweb="tag"][aria-label="{name}, close by backspace"] {{
            background-color: {color_mapping[level]} !important;
            color: white !important;
        }}
        """

    # Inject the custom CSS into Streamlit
    st.markdown(f"""
        <style>
        /* Dynamic styling based on region levels and names */
        {css}
        </style>
    """, unsafe_allow_html=True)

    custom_regions = st.sidebar.multiselect('Customise selection of regions (optional):', options = regs, default = None)


    #Figure formatting tools
    st.sidebar.divider()
    st.sidebar.subheader('Configure layout')
    size = st.sidebar.slider('Figure size', min_value=0.65, max_value = 2.0, value = size_default, step=0.01)
    legend = st.sidebar.toggle(label='Show legend', value=True)
    if not threeD:
        showtrend = st.sidebar.toggle(label='Show trendline', value=False)
    else:
        showtrend = False
    showlabel = st.sidebar.toggle(label='Show labels', value=showlabel_default)
    population = st.sidebar.toggle(label='Toggle population bubbles', value=population_default)

    # download = st.sidebar.toggle(label="Enable PDF download *(slower app)*", value=False)


    # print(custom_regions)
    if custom_regions != []:
        highlight = st.sidebar.multiselect('Add label for selected regions:', options = custom_regions, default = None)
    else:
        highlight = st.sidebar.multiselect('Add label for selected regions:', options = regs, default = None)

    if not threeD:
        fixaxes = st.sidebar.toggle(label='Set axes manually', value=False)
    else:
        fixaxes = False
    
    if fixaxes:
        xrange = st.sidebar.slider('Set X-axis range for productivity per hour', min_value=0, max_value=100,
            value=[15, 75], format = "£%d") 
        yrange = st.sidebar.slider('Set Y-axis range for productivity change', -20, max_value=20,
            value=[-3, 3], format = "%f %%") 
    else:
        xrange = None
        yrange = None

    transition = st.sidebar.slider('Set duration of transitions', min_value=0, max_value=30,
            value=2, format = "%d seconds")
    delay = st.sidebar.slider('Set delay between transitions', min_value=0, max_value=30,
            value=1, format = "%d seconds")

    #Define main content --> change header to something smaller like st.header...
    st.header('TPI Visualisation tool for UK regional productivity growth')
    # for the [ONS dataset](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/labourproductivity/datasets/subregionalproductivitylabourproductivitygvaperhourworkedandgvaperfilledjobindicesbyuknuts2andnuts3subregions) on UK regional productivity growth'


    with st.expander(label="**About this tool**", expanded=False):

        st.markdown(
            """

            ###### Developed by the [TPI Productivity Lab](https://www.productivity.ac.uk/the-productivity-lab/), this tool facilitates dynamic visualizations of regional productivity in the United Kingdom, allowing for visual comparisons of productivity across different time periods and geographic areas. Data is sourced from the June 2024 release of the [ONS dataset on sub-regional productivity](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/labourproductivity/datasets/subregionalproductivitylabourproductivitygvaperhourworkedandgvaperfilledjobindicesbyuknuts2andnuts3subregions), which provides information on annual labour productivity. Labour productivity is measured as gross value added (GVA) per hour worked for regions in the UK, defined according to the [International Territorial Level (ITL)](https://www.ons.gov.uk/methodology/geography/ukgeographies/eurostat) definitions.

            #### Interpreting the Figure: Taxonomy and Convergence

            The figure generated using this tool serves as a visual representation of regional productivity, where each point on the scatterplot represents a specific region in relation to the UK national average. The X-axis reflects labour productivity in a chosen year, measured as Gross Value Added (GVA) per hour worked. The Y-axis represents the change in productivity, adjusted for changes in prices, from a selected start year to the chosen year on the X-axis.
            Using this framework, the figure provides insights into how different regions in the UK are performing relative to the national average in terms of their productivity level and growth. Taking the UK as a reference point, each region can be categorized according to the following productivity taxonomy, based on the work of Zymek and Jones (2020):
            - **Falling Behind:** Both the region's current year productivity and its productivity growth are below the UK average.
            - **Catching Up:** The region's current year productivity is below the UK average, but its productivity growth is above the UK average.
            - **Losing Ground:** The region's current year productivity is above the UK average, but its productivity growth is below the UK average.
            - **Steaming Ahead:** Both the region's current year productivity and its productivity growth are above the UK average.

            In addition, the optional trendline provides information on whether the selected regions are converging (negative slope), or diverging (positive slope) in terms of their productivity performance.

            #### Options for Data Selection

            The top section of the left-hand side panel of the tool offers several options to customize the data plotted in the visualization. These options provide users with flexibility in defining the scope of their analysis, enabling them to focus on specific time periods, geographical areas, and levels of detail according to their research or analytical needs. The following options for data selection are available:

            **3D mode:** Switch the plot to 3D mode where you can use your cursor to move the perspective of the plot to compare GVA per Hour and growth to a 3rd variable.

            **Select indicator for 3rd axis:** Available when 3D mode is on. Choose one of the productivity indicators from the [TPI ITL3 scorecard](https://doi.org/10.48420/23791680) series and look at the data in a different percpective. Time frame of available data varies for each indicator. 

            **Time Period:** Users can specify the start and end years for the data they want to analyze. This allows for the exploration of productivity trends for a specific timeframe.

            **Geographical Aggregation Level (ITL/MCA):** Users can choose the level of geographical aggregation for the data. There are three ITL levels available as well as the Mayoral Combined Authority level:
            - **ITL Level 1:** This is the highest level of aggregation, encompassing the 12 English Regions and Devolved Nations of the United Kingdom.
            - **ITL Level 2:** This level offers the intermediate level of geographic aggregation with 41 regions covering the UK.
            - **ITL Level 3:** This is the lowest level of aggregation, comprising 179 regions covering the UK in more detail.
            - **MCA Level:** This level of aggregation covers 12 English regions so far, and are made up of ITL3 regions.

            **Select ITL1 Region(s):** Users can narrow down their analysis by selecting specific ITL1 regions. Upon selecting an ITL1 region, all underlying regions associated with that ITL1 region will be automatically included in the analysis, according to the previously chosen geographical aggregation level.

            **Select colour level:** Users can decide at which aggregation level they want the data to be coloured at. Levels below the selected aggregation cannot be coloured as this would result in an overlap or misrepresentation of the data.

            **Customize selection of regions (optional) *requires a minimum of two regions*:** The dropdown box allows users to choose regions from a list. This list includes only those regions that can be derived from the previously chosen geographical aggregation level and the selected ITL1 regions. This ensures that users are presented with relevant options based on their previous selections.

            #### Configure Layout Options

            The bottom section of the left-hand side panel provides the following options to changes elements of the scatterplot’s layout:

            **Figure size:** Increase or decrease the size of the figure to fit your screen. This also affects the size of the PDF export.

            **Show legend:** Shows or hides the legend for the graph. The legend gives the colour coding of the aggregate ITL1 regions of which the selected regions are a part. The legend is shown by default.

            **Show trendline:** Shows or hides the OLS trendline. The trendline can be included to gauge convergence or divergence of regional productivity. The trendline is hidden by default.

            **Show labels:** Shows or hides the names for each of the selected regions. The names are hidden by default.

            **Toggle population bubbles:** This changes the size of the data points based on their population in that particular year relative to the other data points.

            **Add label for selected regions:** The names for selected regions can be added to the graph.

            **Set axes manually:** This option allows users to manually set the range for nominal productivity per hour worked on the x-axis, as well as the range for productivity growth on the y-axis. By default this option is disabled, and the axes automatically rescale dependent on the selection of the data. Manually setting the axes can be used to remove outliers from view or prevent the axes from automatically rescaling during animation.

            **Set duration of transitions:** This controls the time taken to transition in-between the years of data when animating. 

            **Set delay between transitions:** This controls the amount of time the animation pauses before the next transition.

            #### Additional Options

            The data tool shows four buttons to the right of the figure:
            - **Animate start year:** Creates a time-lapse of the figure, by incrementing the start year, leaving the end year unchanged.
            - **Animate end year:** Creates a time-lapse of the figure, by incrementing the end year, leaving the start year unchanged.
            - **Animate period:** Creates a time-lapse of the figure, by keeping the interval for productivity change constant, and incrementing both the start and end year.
            - **Exit animation:** Return from the animation mode to the default.

            It is also possible to interact directly with the figure. Hover over individual data points to show the information for that region or zoom in on a specific clusters of scatter points by drawing a rectangle with the mouse. In addition, when hovering over the figure a menu the top right will appear. From this menu it is possible to select additional options such as *panning, zooming,* or *enlarging* the figure to fill the screen. Lastly, from this menu it is possible to save the figure, including the manual changes, as a png image.

            On the top-right of the application window there is an additional menu to rerun the application, change the appearance of the application (dependent on your system settings), print the current view of the application, record a screencast, and get technical information on this application.


            """
            )
    print("Runtime constructing frame: " + str(int((time.time() - t0)*1000)) + " miliseconds")


    #Experiment with buttons side by side to improve layout when the download button is visible and when we add
    #more buttons (animate start year and animate end year)


    #test this: https://nicedouble-streamlitantdcomponentsdemo-app-middmy.streamlit.app/

    # test = sac.buttons([
    #
    #         sac.ButtonsItem(label='Download PDF', icon='download'),
    #
    #         sac.ButtonsItem(label='Annimate start year', icon='film'),
    #         sac.ButtonsItem(label='Annimate end year', icon='film'),
    #         sac.ButtonsItem(label='Annimate period', icon='film'),
    #
    #
    #     ], align='center', variant='filled')
    #
    #
    # print('test is ' + test)

    col1, col2 = st.columns([6,1])


    #Add play animation button
    # with col2:  st.divider()
    with col2:
        st.write("#")
        st.write("#")
        if not threeD:
            play_start = st.button(label = 'Animate start year', type="primary", use_container_width=True)
            play_end = st.button(label = 'Animate end year', type="primary", use_container_width=True)
            play_period = st.button(label = 'Animate period', type="primary", use_container_width=True)
            exit_animation = st.button(label = 'Exit animation', type="primary", use_container_width=True)
            if exit_animation:
                animate = False
        else:
            play_start = False
            play_end = False
            play_period = False

    # with col2: download_pdf = st.button(label="Export to PDF", type="primary", use_container_width=True)
    animate = False
    #Create placeholder for the figure, which can be overwritten, but we need to use the container for that
    with col1: 
        figure = st.empty()
    
    if play_start and year[1] - year[0] > 1:
        # Process and store data for each full year
        yearly_dataselected = []
        yearly_dtaAgg = []
        for i in range(year[0], year[1] + 1):
            if i == year[1]:
                break
            dtaAgg, dtaselected, dtaITL1 = process_data(
                data=data,
                itlmapping=itlmapping,
                start=i,
                year=year[1],
                levels=levels,
                region=selected_regions,
                customregion = custom_regions,
                include_itl1 = False
            )
            dtaselected['year'] = i
            dtaAgg['year'] = i
            yearly_dataselected.append(dtaselected)
            yearly_dtaAgg.append(dtaAgg)

        yearly_dataselected = pd.concat(yearly_dataselected)
        yearly_dtaAgg = pd.concat(yearly_dtaAgg)
        
        # Generate the figure with interpolated data
        fig = graphs.scatter(
            dtaAgg=yearly_dtaAgg,
            dtaselected=yearly_dataselected,
            size=size,
            start=year[0],
            year=year[1],
            levels=levels,
            highlight=highlight,
            legend=legend,
            showlabel=showlabel,
            showtrend=showtrend,
            color_level=color_level,
            population=population,
            xrange=xrange,
            yrange=yrange,
            animate=True,
            delay=delay,
            transition=transition
        )
     
        figure.plotly_chart(fig, use_container_width=True)
        animate = True

    elif play_end and int(max(data.index.unique(level='year')) - year[1]) > 0:
        yearly_dataselected = []
        yearly_dtaAgg = []
        for i in range(year[1], int(max(data.index.unique(level='year'))) + 1):
            dtaAgg, dtaselected, dtaITL1 = process_data(
                data=data,
                itlmapping=itlmapping,
                start=year[0],
                year=i,
                levels=levels,
                region=selected_regions,
                customregion = custom_regions,
                include_itl1 = False
            )
            dtaselected['year'] = i
            dtaAgg['year'] = i
            yearly_dataselected.append(dtaselected)
            yearly_dtaAgg.append(dtaAgg)

        yearly_dataselected = pd.concat(yearly_dataselected)
        yearly_dtaAgg = pd.concat(yearly_dtaAgg)
        # Generate the figure with interpolated data
        fig = graphs.scatter(
            dtaAgg=yearly_dtaAgg,
            dtaselected=yearly_dataselected,
            size=size,
            start=year[0],
            year=year[1],
            levels=levels,
            highlight=highlight,
            legend=legend,
            showlabel=showlabel,
            showtrend=showtrend,
            color_level=color_level,
            population=population,
            xrange=xrange,
            yrange=yrange,
            animate=True,
            delay=delay,
            transition=transition
        )

        # Display the interpolated frame in Streamlit
        figure.plotly_chart(fig, use_container_width=True)
        animate=True

    
    elif play_period and int(max(data.index.unique(level='year')) - year[1]) > 0:
        yearly_dataselected = []
        yearly_dtaAgg = []
        for i in range(year[1], int(max(data.index.unique(level='year'))) + 1):
            dtaAgg, dtaselected, dtaITL1 = process_data(
                data=data,
                itlmapping=itlmapping,
                start=year[0] - year[1] + i,
                year=i,
                levels=levels,
                region=selected_regions,
                customregion = custom_regions,
                include_itl1 = False
            )
            dtaselected['year'] = i
            dtaAgg['year'] = i
            yearly_dataselected.append(dtaselected)
            yearly_dtaAgg.append(dtaAgg)
        yearly_dataselected = pd.concat(yearly_dataselected)
        yearly_dtaAgg = pd.concat(yearly_dtaAgg)
        # Generate the figure with interpolated data
        fig = graphs.scatter(
            dtaAgg=yearly_dtaAgg,
            dtaselected=yearly_dataselected,
            size=size,
            start=year[0],
            year=year[1],
            levels=levels,
            highlight=highlight,
            legend=legend,
            showlabel=showlabel,
            showtrend=showtrend,
            color_level=color_level,
            population=population,
            xrange=xrange,
            yrange=yrange,
            animate=True,
            delay=delay,
            transition=transition
        )

        # Display the interpolated frame in Streamlit
        figure.plotly_chart(fig, use_container_width=True)
        animate=True
    elif ((play_end or play_period) and int(max(data.index.unique(level='year')) - year[1]) <= 0) or (play_start and (year[1] - year[0] <= 1)):
        with col2:
            st.error('Adjust the time period, no frames animated')
    if not animate:
        with figure.container():
            dtaAgg, dtaselected, dtaITL1 = process_data(
                    data = data,
                    itlmapping = itlmapping,
                    start = year[0],
                    year = year[1],
                    levels = levels,
                    region = selected_regions,
                    customregion = custom_regions,
                    include_itl1 = True
                    )
            # print(dtaAgg, dtaselected)  # Remove
            print(dtaITL1)
            dtaITL1.to_csv('ITL1.csv')
            dtaAgg.to_csv('full.csv')
            dtaselected.to_csv('testing.csv')

            t0 = time.time()
            if threeD:
                fig = graphs.scatter_3D(
                                dtaselected = dtaselected,
                                size = size,
                                start = year[0],
                                year = year[1],
                                levels = levels,
                                legend=legend,
                                showlabel=showlabel,
                                color_level = color_level,
                                population=population,
                                z=indicators[z]
                                )
            else:
                fig = graphs.scatter(
                            dtaAgg = dtaAgg,
                            dtaselected = dtaselected,
                            size = size,
                            start = year[0],
                            year = year[1],
                            levels = levels,
                            highlight = highlight,
                            legend = legend,
                            showlabel = showlabel,
                            showtrend = showtrend,
                            color_level = color_level,
                            population = population,
                            xrange = xrange,
                            yrange = yrange,
                            )

            
            figure.plotly_chart(fig, use_container_width=True,
                config = {
                    'toImageButtonOptions': {
                        'filename': f'TPI_scatter_plot',
                        'scale': 2
                    }
                }
            )
        print("Runtime constructing figure: " + str(int((time.time() - t0)*1000)) + " miliseconds")

    # if download_pdf:
    #     t0 = time.time()
    #     # Create an in-memory buffer
    #     buffer = io.BytesIO()
    
    #     try:
    #         print('Saving fig')
    #         # Save the figure as a PDF to the buffer
    #         fig.write_image(file=buffer, format="pdf")
    #         print('Saved')
    #         # Reset buffer position to the start
    #         buffer.seek(0)
    #         # Provide the PDF file for download
    #         st.download_button(
    #             label="Click here to download your plot as PDF",
    #             data=buffer,
    #             file_name="figure.pdf",
    #             mime="application/pdf",
    #             use_container_width=True,
    #         )
    #         print("PDF generated successfully!")
            
    #     except Exception as e:
    #         print(f"An error occurred: {e}")
        
    #     finally:
    #         buffer.close()  # Ensure the buffer is properly closed
    #     print("Runtime pdf buffering: " + str(int((time.time() - t0)*1000)) + " miliseconds")

    # AI overview box
    if st.button("Generate A.I. insights of selected data"):
        # insight_text = generate_insight()
        # st.write(insight_text)
        # Use functions to generate prompt, then call
        # print(year[0])
        # print(year[1])
        # print(levels)  # 
        # print(selected_regions)
        # print(color_level)
        # print(custom_regions)
        avgUK = dtaAgg.loc[(slice(None), 'UKX', slice(None)),['GVA per hour', 'Average Annual log percentage change', 'Population']].reset_index().drop(columns=['Population']).drop_duplicates()
        print("avgUK:", avgUK)
        dtaITL1 = dtaITL1.reset_index()

        growth_col = "Average Annual log percentage change"
        productivity_col = "GVA per hour"

        average_productivity = avgUK[productivity_col][0]
        average_growth = avgUK[growth_col][0]

        median_growth = dtaITL1[growth_col].median()
        median_productivity = dtaITL1[productivity_col].median()

        # print(f"Median growth:       {average_growth:.6f}")
        # print(f"Median productivity: {average_productivity:.2f}")

        # CU: high growth, low productivity (Catching Up)
        CU = dtaITL1[(dtaITL1[growth_col] > average_growth) & (dtaITL1[productivity_col] < average_productivity)]["name"].tolist()

        # FB: low growth, low productivity (Falling Behind)
        FB = dtaITL1[(dtaITL1[growth_col] < average_growth) & (dtaITL1[productivity_col] < average_productivity)]["name"].tolist()

        # SA: high growth, high productivity (Steaming Ahead)
        SA = dtaITL1[(dtaITL1[growth_col] > average_growth) & (dtaITL1[productivity_col] > average_productivity)]["name"].tolist()

        # LG: high productivity, low growth (Losing Ground)
        LG = dtaITL1[(dtaITL1[growth_col] < average_growth) & (dtaITL1[productivity_col] > average_productivity)]["name"].tolist()

        prompt = f"""Analyse this economic data using professional, analytical language. 
            You may ONLY use the numbers and entities provided below.
            You MUST reference the specific regions mentioned
            You MUST reference the years mentioned
            Only use British English

            ALLOWED to add: 
            - Economic terminology (outpaced, lagged, diverged, contracted, etc.)
            - Comparative language (significantly, slightly, nearly double)
            - Structural observations (gap between, performance spread)

            FORBIDDEN to add:
            - Any specific numbers not listed
            - Time periods (quarterly, annually, last year)
            - External causes (due to, because of, driven by)
            - Names of policies, events, or leaders
            """
        
        if levels[0] == 'ITL1' and len(levels) == 0:
            CU_values = dtaITL1[(dtaITL1[growth_col] > average_growth) & (dtaITL1[productivity_col] < average_productivity)][growth_col].multiply(100).tolist()
            FB_values = dtaITL1[(dtaITL1[growth_col] < average_growth) & (dtaITL1[productivity_col] < average_productivity)][growth_col].multiply(100).tolist()
            SA_values = dtaITL1[(dtaITL1[growth_col] > average_growth) & (dtaITL1[productivity_col] > average_productivity)][growth_col].multiply(100).tolist()
            LG_values = dtaITL1[(dtaITL1[growth_col] < average_growth) & (dtaITL1[productivity_col] > average_productivity)][growth_col].multiply(100).tolist()
            prompt = prompt + f"""Data:
                - Across time-period: {year[0]} - {year[1]}
                - Catching Up regions and growth rates (%) (high productivity growth, low productivity):  {CU, CU_values}
                - Falling Behind regions and growth rates (%) (low productivity growth, low productivity):  {FB, FB_values}
                - Steaming Ahead regions and growth rates (%) (high productivity growth, high productivity): {SA, SA_values}
                - Losing Ground regions and growth rates (%) (low productivity growth,  high productivity): {LG, LG_values}
                Write one analytical paragraph about the data
                """
        else:
            prompt = prompt + f"""Data:
                Data for ITL1 regions:
                - Across time-period: {year[0]} - {year[1]}
                - Catching Up regions (high productivity growth, low productivity):  {CU}
                - Falling Behind regions (low productivity growth, low productivity):  {FB}
                - Steaming Ahead regions (high productivity growth, high productivity): {SA}
                - Losing Ground regions (low productivity growth,  high productivity): {LG}
                """
            
            if 'MCA' in levels:
                dtaselected = dtaselected.reset_index()
                MCA_data = [dtaselected['level'] == 'MCA']
                MCA_data = (
                    dtaselected.set_index("name")["Average Annual log percentage change"]
                    .mul(100)
                    .round(2)
                    .to_dict()
                )

                prompt = prompt + f"""Data:
                Data for Mayoral Combined Authorities:
                - MCA Regions and their annual growth rates (%) {MCA_data}

                """
            
            if 'ITL2' in levels:
                dtaselected = dtaselected.reset_index()
                ITL2_data = dtaselected[dtaselected['level'] == 'ITL2']

                highest = ITL2_data.loc[ITL2_data[growth_col].idxmax()]
                lowest = ITL2_data.loc[ITL2_data[growth_col].idxmin()]

                prompt += f"""
                Data for ITL2 regions:
                Highest growth: {highest['name']} ({highest[growth_col] * 100:.2f}%)
                Lowest growth: {lowest['name']} ({lowest[growth_col] * 100:.2f}%)
                """
            
            if 'ITL3' in levels:
                dtaselected = dtaselected.reset_index()
                ITL3_data = dtaselected[dtaselected['level'] == 'ITL3']
                
                highest = ITL3_data.loc[ITL3_data[growth_col].idxmax()]
                lowest = ITL3_data.loc[ITL3_data[growth_col].idxmin()]

                prompt += f"""
                Data for ITL3 regions:
                Highest growth: {highest['name']} ({highest[growth_col] * 100:.2f}%)
                Lowest growth: {lowest['name']} ({lowest[growth_col] * 100:.2f}%)
                """

            prompt = prompt + f"""
            Write one brief paragraph about the ITL1 regions, and then additional paragraphs for extra regions if included"""

        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,  # Lower = more consistent outputs
        )
        result = completion.choices[0].message.content
        st.info(result)

if __name__ == '__main__':
    main()
