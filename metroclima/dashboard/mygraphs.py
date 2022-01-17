from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, BoxAnnotation
from bokeh.layouts import column, grid


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
