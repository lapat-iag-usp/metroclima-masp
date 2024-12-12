from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.layouts import column, grid


def station_graphs(df):
    # source
    source = ColumnDataSource(df)

    # variables
    my_vars = [x for x in df.columns[1:]]

    # hover tool
    hover_tool_p = HoverTool(
        tooltips=[('date', '@time{%m/%d/%Y %H:%M:%S}'),
                  ('value', '$y')],
        formatters={'@time': 'datetime'})

    plots = []
    i = 0
    for my_var in my_vars:
        p = figure(plot_height=175,
                   plot_width=800,
                   toolbar_location='right',
                   tools="pan, box_zoom, reset",
                   x_axis_type="datetime",
                   x_axis_location="below")
        p.scatter(x='time', y=my_var,
                  legend_label=my_var, source=source,
                  line_color='#1f77b4', fill_color='#1f77b4',
                  size=0.5, alpha=0.3)

        p.add_tools(hover_tool_p)
        p.legend.background_fill_alpha = 0.75
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
