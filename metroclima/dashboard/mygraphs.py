from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, BoxAnnotation, WheelZoomTool
from bokeh.layouts import column, grid
import pandas as pd
from datetime import timedelta
import numpy as np


def find_date_gaps(df):
    campaigns = []
    start_dates = []
    end_dates = []
    stations = []

    for campaign, group in df.groupby('campaign'):
        group = group.sort_values('date')
        start_date = None
        end_date = None
        station = group['station'].iloc[0]

        for i, row in group.iterrows():
            if start_date is None:
                start_date = row['date']
                end_date = row['date']
            elif row['date'] == end_date + timedelta(hours=1):
                end_date = row['date']
            else:
                campaigns.append(campaign)
                start_dates.append(start_date)
                end_dates.append(end_date)
                start_date = row['date']
                end_date = row['date']
                stations.append(station)

        campaigns.append(campaign)
        start_dates.append(start_date)
        end_dates.append(end_date)
        stations.append(station)

    return pd.DataFrame({'station': stations, 'campaign': campaigns, 'start_date': start_dates, 'end_date': end_dates})


def data_overview_graph(df):
    gaps_df = find_date_gaps(df)
    gaps_df['end_date'] = pd.to_datetime(gaps_df['end_date']) + pd.to_timedelta(59, unit='m')
    gaps_df.sort_values('start_date', ascending=True, inplace=True)
    gaps_df.sort_values('station', ascending=False, inplace=True)
    print(gaps_df.head())
    source = ColumnDataSource(gaps_df)

    hover = HoverTool()
    hover.tooltips = [
        ("Start date", "@start_date{%m/%d/%Y %H:%M}"),
        ("End date", "@end_date{%m/%d/%Y %H:%M}"),
        ("Campaign", "@campaign"),
    ]
    hover.formatters = {
        '@start_date': 'datetime',
        '@end_date': 'datetime',
    }

    p = figure(y_range=gaps_df['campaign'].unique(), x_axis_type='datetime',
               width=1100, height=600, toolbar_location='right',
               tools="pan, box_zoom, reset")

    p.hbar(y="campaign", left='start_date', right='end_date', height=0.4, source=source)

    wheel_zoom_x = WheelZoomTool(dimensions='width')
    p.add_tools(wheel_zoom_x)
    p.add_tools(hover)
    p.ygrid.grid_line_color = None
    p.xaxis.axis_label = "Date"
    p.outline_line_color = None

    script, div = components(p)

    return script, div


def find_intervals(df, problem_var):
    intervals = []
    start = None
    for index, value in df[problem_var].items():
        if value == 1 and start is None:
            start = df.loc[index, 'time']
        elif value == 0 and start is not None:
            end = df.loc[index, 'time']
            intervals.append((start, end))
            start = None
    if start is not None:
        intervals.append((start, df.iloc[-1]['time']))
    return intervals


def bokeh_raw(df, start_dates, end_dates, color='#1f77b4'):
    # source
    source = ColumnDataSource(df)

    # variables
    my_vars = [x for x in df.columns[1:] if '_dry' not in x]
    my_vars_dry = [x for x in df.columns[1:] if '_dry' in x]

    # hover tool
    hover_tool_p = HoverTool(
        tooltips=[('date', '@DATE_TIME{%m/%d/%Y %H:%M:%S}'),
                  ('value', '$y')],
        formatters={'@DATE_TIME': 'datetime'})

    plots = []
    i = 0
    for my_var in my_vars:
        p = figure(plot_height=100,
                   plot_width=900,
                   toolbar_location='right',
                   tools="pan, box_zoom, reset",
                   x_axis_type="datetime",
                   x_axis_location="below")
        p.line(x='DATE_TIME', y=my_var,
               legend_label=my_var, source=source, line_color=color)
        if my_var + '_dry' in my_vars_dry:
            p.line(x='DATE_TIME', y=my_var + '_dry',
                   legend_label=my_var + '_dry', source=source,
                   line_color=color, alpha=0.5)

        # logbook events - shaded area
        for start_date, end_date in zip(start_dates, end_dates):
            box = BoxAnnotation(left=start_date.timestamp() * 1000,
                                right=end_date.timestamp() * 1000,
                                fill_alpha=0.4,
                                fill_color='gray')
            p.add_layout(box)

        p.add_tools(hover_tool_p)
        p.xaxis.visible = False
        p.legend.background_fill_alpha = 0.75
        p.legend.click_policy = "hide"
        p.legend.spacing = 0
        p.legend.padding = 2
        p.toolbar.logo = None
        plots.append(p)
        if i == 0:
            x_range = p.x_range
        else:
            p.x_range = x_range
        i += 1

    a = column(*plots)
    my_layout = grid([a], ncols=1)
    script, div = components(my_layout)

    return script, div


def bokeh_raw_mobile(df, start_dates, end_dates, color='#1f77b4'):
    # source
    source = ColumnDataSource(df)

    # variables
    my_vars = [x for x in df.columns[1:] if 'd_' not in x]
    my_vars_dry = [x for x in df.columns[1:] if 'd_' in x]

    # hover tool
    hover_tool_p = HoverTool(
        tooltips=[('date', '@Time{%m/%d/%Y %H:%M:%S}'),
                  ('value', '$y')],
        formatters={'@Time': 'datetime'})

    plots = []
    i = 0
    for my_var in my_vars:
        p = figure(plot_height=100,
                   plot_width=900,
                   toolbar_location='right',
                   tools="pan, box_zoom, reset",
                   x_axis_type="datetime",
                   x_axis_location="below")
        p.line(x='Time', y=my_var,
               legend_label=my_var, source=source, line_color=color)
        if my_var[:-4] + 'd_ppm' in my_vars_dry:
            p.line(x='Time', y=my_var[:-4] + 'd_ppm',
                   legend_label=my_var[:-4] + 'd_ppm', source=source,
                   line_color=color, alpha=0.5)

        # logbook events - shaded area
        for start_date, end_date in zip(start_dates, end_dates):
            box = BoxAnnotation(left=start_date.timestamp() * 1000,
                                right=end_date.timestamp() * 1000,
                                fill_alpha=0.4,
                                fill_color='gray')
            p.add_layout(box)

        p.add_tools(hover_tool_p)
        p.xaxis.visible = False
        p.legend.background_fill_alpha = 0.75
        p.legend.click_policy = "hide"
        p.legend.spacing = 0
        p.legend.padding = 2
        p.toolbar.logo = None
        plots.append(p)
        if i == 0:
            x_range = p.x_range
        else:
            p.x_range = x_range
        i += 1

    a = column(*plots)
    my_layout = grid([a], ncols=1)
    script, div = components(my_layout)

    return script, div


def bokeh_level_0(ds, variable_name, color='#1f77b4'):
    # source
    df = ds.to_dataframe().reset_index()
    source = ColumnDataSource(df)

    # variables
    my_var = variable_name

    # hover tool
    hover_tool_p = HoverTool(
        tooltips=[('date', '@time{%m/%d/%Y %H:%M:%S}'),
                  ('value', '$y')],
        formatters={'@time': 'datetime'})

    problem_colors = {
        'FA': '#DC35457F',
        'FM': '#007BFF7F',
        'CAL': '#28A7457F'
    }

    p = figure(plot_height=200,
               plot_width=900,
               toolbar_location='right',
               tools="pan, box_zoom, reset",
               x_axis_type="datetime",
               x_axis_location="below")
    p.line(x='time', y=my_var,
           legend_label=my_var, source=source, line_color=color)

    # Add shaded areas for problem indicators
    for problem_var, problem_color in problem_colors.items():
        intervals = find_intervals(df, problem_var)
        for start, end in intervals:
            box = BoxAnnotation(left=start, right=end,
                                fill_alpha=0.5, fill_color=problem_color)
            p.add_layout(box)

    p.add_tools(hover_tool_p)
    p.xaxis.visible = False
    p.legend.background_fill_alpha = 0.75
    p.legend.click_policy = "hide"
    p.legend.spacing = 0
    p.legend.padding = 2
    p.toolbar.logo = None

    script, div = components(p)

    return script, div
