#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 13:20:48 2024

@author: reitze
"""

"""
dependencies: Kaleido: sudo conda install -c conda-forge python-kaleido
or conda install -c conda-forge python-kaleido=0.1.0
Also statsmodels
"""
import pandas as pd
import textwrap
import plotly.express as px
import plotly.io as pio
from PIL import Image
import json
import plotly.graph_objects as go
from copy import deepcopy

UPCOMING_MSA_GROUP = 'Upcoming Mayoral Strategic Authorities'
ESTABLISHED_MSA_GROUP = 'Established Mayoral Strategic Authorities'
UPCOMING_MSA_NAMES = {
    'Cumbria',
    'Cheshire and Warrington',
    'Greater Essex',
    'Sussex and Brighton',
    'Hampshire and the Solent',
    'Wessex',
    'Norfolk and Suffolk',
    'Thames Valley',
    'Leicester, Leicestershire and Rutland'
}
ESTABLISHED_MSA_NAMES = {
    'Cambridgeshire and Peterborough',
    'East Midlands',
    'Greater Lincolnshire',
    'Greater London',
    'Tees Valley',
    'North East',
    'Greater Manchester',
    'Liverpool City Region',
    'West of England',
    'West Midlands',
    'Hull and East Yorkshire',
    'York and North Yorkshire',
    'South Yorkshire',
    'West Yorkshire',
    'Devon and Torbay',
    'Lancashire'
}


def _get_color_column(dtaselected, color_level):
    color_column = color_level.lower() + 'name'
    if color_level == 'MCA':
        dtaselected['mca_color_group'] = dtaselected[color_column].replace({
            **{name: UPCOMING_MSA_GROUP for name in UPCOMING_MSA_NAMES},
            **{name: ESTABLISHED_MSA_GROUP for name in ESTABLISHED_MSA_NAMES},
        })
        return 'mca_color_group'
    return color_column


# Makes scatter displayed in streamlit
def scatter(dtaAgg, dtaselected, size, start, year, levels, highlight, legend, showlabel, showtrend, color_level, population, xrange = None, yrange=None, animate=False, delay=3, transition=2):
    pio.renderers.default='browser'

    metric = 'Average Annual percentage change' #options are: 'Percentage change', 'Log percentage change', 'Average Annual Percentage change', 'Average Annual log percentage change'
    title_levels = [
        'Mayoral Strategic Authorities' if level == 'MCA' else level
        for level in levels
    ]
    itl_string = ','.join(title_levels)
    figure_title = 'UK ' + itl_string + ' regions<br>' +\
                    '<sup>' + str(year) + ' Nominal smoothed GVA per hour, vs. ' + str(start) + '-' + \
                    str(year) + ' productivity change</sup>'

                    # '<sup><b>By ' + level.upper() + ' region</b></sup>'

         
    yaxistitle = str(start) + '-' + str(year) + ' ' + metric + ' in productivity'
    xaxistitle = str(year) + ' output per hour worked (£)'

    # averages = ['UKX','MCA']
    # avgcolors = ['purple', 'blue']
    averages = ['UKX']
    avgcolors = ['grey']
    with open("src/colormaps.json", "r") as file:
        colour_maps = json.load(file)

    # Access the individual dictionaries
    if color_level == 'MCA':
        colormap = colour_maps[3]
    else:
        colormap = colour_maps[int(color_level[3]) - 1]
    color_column = _get_color_column(dtaselected, color_level)
    legend_title = (
        'Mayoral Strategic Authorities'
        if color_level == 'MCA'
        else color_level + ' Region'
    )

    if showlabel:
        labels = 'name'
    else: labels = None

    if showtrend and not animate:
        trend = 'ols'
    else: trend = None

    if dtaselected['Population'].max() - dtaselected['Population'].min() == 0:
        dtaselected['Scaled Population'] = 1
    else:
        dtaselected['Scaled Population'] = (10 + ((dtaselected['Population'] - dtaselected['Population'].min()) * (40 - 10)) / (dtaselected['Population'].max() - dtaselected['Population'].min())) * size
    if not animate:
        #Style plot
        if population:#marker = dict(size =dtaselected['Scaled Population']*size)
            custom_data=['name', 'code', 'GVA per hour', metric, 'Population', 'level']
            fig = px.scatter(dtaselected.reset_index(), x = 'GVA per hour', y=metric,
                        text=labels,
                        color = color_column,
                        color_discrete_map = colormap,
                        custom_data=['name', 'code', 'GVA per hour', metric, 'Population', 'level'],
                        trendline = trend,
                        trendline_scope="overall",
                        trendline_color_override="red",
                        size='Scaled Population',
                        width=1000*size,
                        height=700*size,
                        )
            fig.update_traces(textposition='top center', textfont_size = 10*size)
        else:
            custom_data=['name', 'code', 'GVA per hour', metric, 'level']
            fig = px.scatter(dtaselected.reset_index(), x = 'GVA per hour', y=metric,
                        text=labels,
                        color = color_column,
                        color_discrete_map = colormap,
                        custom_data=['name', 'code', 'GVA per hour', metric, 'level'],
                        trendline = trend,
                        trendline_scope="overall",
                        trendline_color_override="red",
                        width=1000*size,
                        height=700*size,
                        )
            fig.update_traces(marker = dict(size =10*size), textposition='top center', textfont_size = 10*size)
    else:
        #Style plot
        if population:#marker = dict(size =dtaselected['Scaled Population']*size)
            custom_data=['name', 'code', 'GVA per hour', metric, 'Population', 'level']
            fig = px.scatter(dtaselected.reset_index(), x = 'GVA per hour', y=metric,
                        text=labels,
                        color = color_column,
                        color_discrete_map = colormap,
                        custom_data=custom_data,
                        trendline = trend,
                        trendline_scope="overall",
                        trendline_color_override="red",
                        size='Scaled Population',
                        width=1000*size,
                        height=700*size,
                        animation_frame='year',
                        animation_group='name',
                        )
            fig.update_traces(textposition='top center', textfont_size = 10*size)
        else:
            custom_data=['name', 'code', 'GVA per hour', metric, 'level']
            fig = px.scatter(dtaselected.reset_index(), x = 'GVA per hour', y=metric,
                        text=labels,
                        color = color_column,
                        color_discrete_map = colormap,
                        custom_data=custom_data,
                        trendline = trend,
                        trendline_scope="overall",
                        trendline_color_override="red",
                        width=1000*size,
                        height=700*size,
                        animation_frame='year',
                        animation_group='name',
                        )
            fig.update_traces(marker = dict(size =10*size), textposition='top center', textfont_size = 10*size)
        x_min = dtaselected['GVA per hour'].min()
        x_max = dtaselected['GVA per hour'].max()
        y_min = dtaselected[metric].min()
        y_max = dtaselected[metric].max()

    # if showlabel:
    #     # Update label positions
    #     for i, row in dtaselected.reset_index().iterrows():
    #         fig.add_annotation(
    #             x=row['GVA per hour'] + row['x_offset'],
    #             y=row[metric] + row['y_offset'],
    #             text=row['name'],
    #             showarrow=False,
    #             font=dict(size=9)
    #         )
    #add the scatter point for the reference average, 1 for UK as whole one for UK excluding London:
    for i, v in enumerate(averages):
        if v == 'UKX':
            dtaAgg['flag'] = 'UK'
        else:
            subset = dtaAgg.loc[(v, slice(None), slice(None)), ['GVA per hour', metric, 'Population']]
            
            dtaAgg.loc[('Average', v, f'{v} average'), ['GVA per hour', metric, 'Population']] = subset.mean().to_numpy()
            dtaAgg.to_csv('test.csv')
            dtaAgg['flag'] = '▲'
            
        if not animate:
            avgUK = dtaAgg.loc[(slice(None), v, slice(None)),['GVA per hour', metric, 'Population', 'flag']].reset_index()
            if population:
                ukavg = px.scatter(avgUK.reset_index(), x = 'GVA per hour', y=metric,
                                # hover_name = 'name',
                                text='flag',
                                # labels = {'nominal': 'GVA per hour', 'tot perc growth': 'Percentage change'},
                                custom_data=custom_data,
                                )
            else:
                ukavg = px.scatter(avgUK.reset_index(), x = 'GVA per hour', y=metric,
                                # hover_name = 'name',
                                text='flag',
                                # labels = {'nominal': 'GVA per hour', 'tot perc growth': 'Percentage change'},
                                custom_data=custom_data,
                                )
        else:
            avgUK = dtaAgg.loc[(slice(None), v, slice(None)),['GVA per hour', metric, 'Population', 'year', 'flag']].reset_index()
            if population:
                ukavg = px.scatter(avgUK.reset_index(), x = 'GVA per hour', y=metric,
                                # hover_name = 'name',
                                text='flag',
                                # labels = {'nominal': 'GVA per hour', 'tot perc growth': 'Percentage change'},
                                custom_data=custom_data,
                                animation_frame='year',
                                animation_group='name',
                                )
            else:
                ukavg = px.scatter(avgUK.reset_index(), x = 'GVA per hour', y=metric,
                                # hover_name = 'name',
                                text='flag',
                                # labels = {'nominal': 'GVA per hour', 'tot perc growth': 'Percentage change'},
                                custom_data=custom_data,
                                animation_frame='year',
                                animation_group='name',
                                )
            hlines = []
            vlines = []

            for _, row in avgUK.iterrows():
                year = row['year']
                x_avg = row['GVA per hour']
                y_avg = row[metric]

                # Horizontal line (constant y)
                hlines.append({
                    'x': 0, 'y': y_avg, 'year': year, 'group': f'{year}_h'
                })
                hlines.append({
                    'x': 1000, 'y': y_avg, 'year': year, 'group': f'{year}_h'
                })

                # Vertical line (constant x)
                vlines.append({
                    'x': x_avg, 'y': -0.3, 'year': year, 'group': f'{year}_v'
                })
                vlines.append({
                    'x': x_avg, 'y': 0.3, 'year': year, 'group': f'{year}_v'
                })

            hlines_df = pd.DataFrame(hlines)
            vlines_df = pd.DataFrame(vlines)

            hlines_trace = px.line(
                hlines_df,
                x="x",
                y="y",
                animation_frame="year",
                line_group="group",  # important for animating multiple lines per frame
                color_discrete_sequence=[avgcolors[i]],
                hover_name=None,
            )

            vlines_trace = px.line(
                vlines_df,
                x="x",
                y="y",
                animation_frame="year",
                line_group="group",  # important for animating multiple lines per frame
                color_discrete_sequence=[avgcolors[i]],
                hover_name=None,
            )

            for htrace, vtrace in zip(hlines_trace.data, vlines_trace.data):
                htrace.update(line=dict(dash='dash'))
                vtrace.update(line=dict(dash='dash'))

        #styling for the UK average 'trace' or layer.
        ukavg.update_traces(marker=dict(
                                        size=2,
                                        # size=15,
                                        color=avgcolors[i],
                                        # line=dict(width=2, color = 'black')
                                        ),
                            textfont_size = 17,
                            # fillcolor = 'white',
                            # textfont_color = 'white',
                            textposition='middle center')
        # Add UK average trace to initial frame
        fig.add_trace(ukavg.data[0])
        if animate:
            fig.add_trace(hlines_trace.data[0])
            fig.add_trace(vlines_trace.data[0])
        else:
            fig.add_hline(y=avgUK.loc[0, metric], line_width=1, line_dash="dash", line_color=avgcolors[i])
            fig.add_vline(x=avgUK.loc[0, 'GVA per hour'], line_width=1, line_dash="dash", line_color=avgcolors[i])
            print()

        if population:
            hovertemp="<br>".join([
                    "<b> %{customdata[0]}</b>",
                    "%{customdata[5]} code: %{customdata[1]}",
                    str(year) + " Productivity" + ": £%{customdata[2]:.4} per hour",
                    "Productivity growth: %{customdata[3]:.2%}",
                    "Population: %{customdata[4]}"
                    ])
        else:
            hovertemp="<br>".join([
                "<b> %{customdata[0]}</b>",
                "%{customdata[4]} code: %{customdata[1]}",
                str(year) + " Productivity" + ": £%{customdata[2]:.4} per hour",
                "Productivity growth: %{customdata[3]:.2%}",
                ])

        if animate:
            # Ensure fig.frames exists
            if fig.frames is None:
                fig.frames = []

            for j, (uk_frame, h_frame, v_frame) in enumerate(zip(ukavg.frames, hlines_trace.frames, vlines_trace.frames)):
                year = int(uk_frame.name)
                for htrace, vtrace in zip(h_frame.data, v_frame.data):
                    htrace.update(line=dict(dash='dash'))
                    vtrace.update(line=dict(dash='dash'))

                # Safely merge with existing frame
                if j < len(fig.frames):
                    frame = fig.frames[j]
                    # Apply to initial traces
                    for trace in frame.data:
                        trace.customdata = trace.customdata
                        trace.hovertemplate = hovertemp
                    for trace in uk_frame.data:
                        trace.customdata = trace.customdata
                        trace.hovertemplate = hovertemp
                    frame.data += uk_frame.data
                    frame.data += h_frame.data
                    frame.data += v_frame.data
                else:
                    fig.frames.append(go.Frame(
                        data=uk_frame.data+h_frame.data+v_frame.data,
                        name=str(year)
                    ))

            fig.update_layout(
                xaxis=dict(range=[x_min, x_max]),
                yaxis=dict(range=[y_min, y_max]),
                updatemenus=[{
                    "type": "buttons",
                    "showactive": True,
                    "buttons": [
                        {
                            "label": "Play",
                            "method": "animate",
                            "args": [
                                None,
                                {
                                    "frame": {"duration": (transition+delay)*1000, "redraw": True},      # Time each year is shown
                                    "transition": {"duration": transition*1000},                 # Delay before next year starts (with animation)
                                    "fromcurrent": True
                                }
                            ]
                        },
                        {
                            "label": "Pause",
                            "method": "animate",
                            "args": [[None], {"frame": {"duration": 0}, "mode": "immediate"}]
                        }
                    ]
                }]
            )

    '''Add scatter labels for selected regions'''
    if highlight != None and not animate:
        highlight = ['<br>'.join(textwrap.wrap(x, width = 15)) for x in highlight]
        dtaHighlight = pd.DataFrame()
        temp = dtaselected.loc[(dtaselected.index.get_level_values('level').isin(levels), slice(None), highlight),:].reset_index()
        dtaHighlight = pd.concat([dtaHighlight, temp], ignore_index=True)
        #Add names with arrow
        for i, v in dtaHighlight.iterrows():
            text = textwrap.wrap(v['name'], width = 20)
            text = '<br>'.join(text)
            fig.add_annotation({
                            'text': '<b>' + v['name'] + '</b>',
                            # 'text': text,
                            'x': v['GVA per hour'],
                            'y': v[metric],
                            'font': {'size': 10*size, 'color': 'black'},
                            'showarrow': True,
                            'arrowwidth': 1,
                            'arrowhead': 0,
                            'ay': -50, #This creates a different y-position of the text, so that when the graph is reduced in width the text won't overlap
                            # 'ax': prm['highlight'][v['code']][1],

                            # textangle=0,
                            # xanchor='right',
                            # align:'left',
                            'bgcolor': 'rgba(237, 237, 237,0.0)',
                            'opacity': 1,
                            'xref': "x",
                            'yref': "y"
                        }
                        )


    #Plot formatting
    fig.update_layout(font = {'size': 18*size},
                      showlegend=legend,
                      legend_title = legend_title,
                      legend_title_font_size = 12*size,
                      legend_font_size = 12*size,
                      plot_bgcolor = 'rgba(237, 237, 237,0.5)',
                      paper_bgcolor = 'white',
                      title = {
                                'text': figure_title, #set main title
                                'x': 0.04,
                                'font_size': 15*size, #Title text size
                                },


                      margin = {
                          'l': 100*size,
                          'r': 100*size,
                          't': 100*size,
                          'b': 100*size,
                          },
                      )

    fig.layout.yaxis.tickformat =  '.1%'
    fig.update_xaxes(tickprefix='£')
    fig.update_yaxes(title = yaxistitle, tickfont=dict(size=12*size), title_font=dict(size=12*size))
    fig.update_xaxes(title = xaxistitle, tickfont=dict(size=12*size), title_font=dict(size=12*size))

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(199, 197, 197, 0.2)', zerolinewidth=1, zerolinecolor='rgba(199, 197, 197, 0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(199, 197, 197, 0.2)', zerolinewidth=1, zerolinecolor='rgba(199, 197, 197, 0.2)')

    if xrange != None: fig.update_xaxes(range=xrange)
    if yrange != None:
        yrange = [i/100 for i in yrange]

        fig.update_yaxes(range=yrange)

    #Update the traces to inlcude the tootlip information
    fig.update_traces(hovertemplate=hovertemp)


    #Add annotations
    tsize = 12*size

    #Add annotation boxes to the plot
    fig.add_annotation(dict(font=dict(size=tsize),
                                            x=0.99,
                                            y=0.03,
                                            showarrow=False,
                                            text="Losing ground",
                                            textangle=0,
                                            xanchor='right',
                                            align='left',
                                            #bgcolor = 'white',
                                            opacity = 0.8,
                                            xref="paper",
                                            yref="paper"
                                            ))

    fig.add_annotation(dict(font=dict(size=tsize),
                                            x=0.99,
                                            y=0.97,
                                            showarrow=False,
                                            text="Steaming ahead",
                                            textangle=0,
                                            xanchor='right',
                                            align='left',
                                            #bgcolor = 'white',
                                            opacity = 0.8,
                                            xref="paper",
                                            yref="paper"
                                            ))

    fig.add_annotation(dict(font=dict(size=tsize),
                                            x=0.01,
                                            y=0.97,
                                            showarrow=False,
                                            text="Catching up",
                                            textangle=0,
                                            xanchor='left',
                                            align='left',
                                            #bgcolor = 'white',
                                            opacity = 0.8,
                                            xref="paper",
                                            yref="paper"
                                            ))

    fig.add_annotation(dict(font=dict(size=tsize),
                                            x=0.01,
                                            y=0.03,
                                            showarrow=False,
                                            text="Falling behind",
                                            textangle=0,
                                            xanchor='left',
                                            align='left',
                                            #bgcolor = 'white',
                                            opacity = 0.8,
                                            xref="paper",
                                            yref="paper"
                                            ))
    return fig

def scatter_3D(dtaselected, size, start, year, levels, legend, showlabel, color_level, population, z):
    metric = 'Average Annual log percentage change' #options are: 'Percentage change', 'Log percentage change', 'Average Annual Percentage change', 'Average Annual log percentage change'
    title_levels = [
        'Mayoral Strategic Authorities' if level == 'MCA' else level
        for level in levels
    ]
    itl_string = ','.join(title_levels)
    figure_title = 'UK ' + itl_string + ' regions<br>' +\
                    '<sup>' + str(year) + ' Nominal smoothed GVA per hour, vs. ' + str(start) + '-' + \
                    str(year) + ' productivity change</sup>'
  
    yaxistitle = str(start) + '-' + str(year) + ' ' + metric + ' in productivity'
    xaxistitle = str(year) + ' output per hour worked (£)'
    with open("src/colormaps.json", "r") as file:
        colour_maps = json.load(file)

    if showlabel:
        labels = 'name'
    else: labels = None

    # Access the individual dictionaries
    if color_level == 'MCA':
        colormap = colour_maps[3]
    else:
        colormap = colour_maps[int(color_level[3]) - 1]
    color_column = _get_color_column(dtaselected, color_level)
    legend_title = (
        'Mayoral Strategic Authorities'
        if color_level == 'MCA'
        else color_level + ' Region'
    )
    
    if population:
        if dtaselected['Population'].max() - dtaselected['Population'].min() == 0:
            dtaselected['Scaled Population'] = 1
        else:
            dtaselected['Scaled Population'] = (10 + ((dtaselected['Population'] - dtaselected['Population'].min()) * (40 - 10)) / (dtaselected['Population'].max() - dtaselected['Population'].min())) * size
    else:
        dtaselected['Scaled Population'] = 1
    
    indicator = z.to_frame().columns[0]
    z = z.reset_index()
    z = z.loc[z['year'] == year].drop(columns='year')
    dtaselected = dtaselected.reset_index(['level', 'name']).join(z.set_index('code'))
    fig = px.scatter_3d(
        dtaselected.reset_index(),
        text=labels,
        x='GVA per hour', 
        y=metric, 
        z=indicator,  # Choose an appropriate third dimension
        color=color_column,
        color_discrete_map=colormap,
        custom_data=['name', 'code', 'GVA per hour', metric, 'Population', 'level', indicator],
        size='Scaled Population',
        width=1200 * size,
        height=900 * size,
    )
    if population:
        hovertemp="<br>".join([
                    "<b> %{customdata[0]}</b>",
                    "%{customdata[5]} code: %{customdata[1]}",
                    str(year) + " Productivity" + ": £%{customdata[2]:.4} per hour",
                    "Productivity growth: %{customdata[3]:.2%}",
                    "Population: %{customdata[4]}",
                    indicator + ": %{customdata[6]}"
                    ])
    else:
        hovertemp="<br>".join([
                    "<b> %{customdata[0]}</b>",
                    "%{customdata[5]} code: %{customdata[1]}",
                    str(year) + " Productivity" + ": £%{customdata[2]:.4} per hour",
                    "Productivity growth: %{customdata[3]:.2%}",
                    indicator + ": %{customdata[6]:.2%}"
                    ])

    fig.update_traces(textposition='top center', textfont_size = 10*size, hovertemplate=hovertemp)

    fig.update_layout(font = {'size': 12},
                      showlegend=legend,
                      legend_title = legend_title,
                      legend_title_font_size = 12*size,
                      legend_font_size = 12*size,
                      plot_bgcolor = 'rgba(237, 237, 237,0.5)',
                      paper_bgcolor = 'white',
                      title = {
                                'text': figure_title, #set main title
                                'x': 0.04,
                                'font_size': 15*size, #Title text size
                                },


                      margin = {
                          'l': 100*size,
                          'r': 100*size,
                          't': 100*size,
                          'b': 100*size,
                          },
                      )
    fig.layout.yaxis.tickformat =  '.1%'
    fig.update_xaxes(tickprefix='£')

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(199, 197, 197, 0.2)', zerolinewidth=1, zerolinecolor='rgba(199, 197, 197, 0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(199, 197, 197, 0.2)', zerolinewidth=1, zerolinecolor='rgba(199, 197, 197, 0.2)')
    return fig