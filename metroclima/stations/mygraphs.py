from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.layouts import column, grid


def station_graphs(df):

    if df.empty:
        plots = []
        p = figure(plot_height=200,
                   plot_width=800,
                   toolbar_location='right',
                   tools="pan, ywheel_zoom, box_zoom, reset",
                   x_axis_type="datetime",
                   x_axis_location="below",
                   title="data will be available soon")
        p.toolbar.logo = None
        plots.append(p)

        a = column(*plots)
        my_layout = grid([a], ncols=1)
        script, div = components(my_layout)

        return script, div

    else:
        df = df.set_index('DATE_TIME')
        df_day = df.resample('D').mean()
        df = df.reset_index()
        df_day = df_day.reset_index()

        # source
        source = ColumnDataSource(df)
        source_day = ColumnDataSource(df_day)

        my_vars_dry = [x for x in df.columns[1:] if '_dry_m' in x]

        # hover tool
        hover_tool_p = HoverTool(
            tooltips=[('date', '@DATE_TIME{%m/%d/%Y %H:%M:%S}'),
                      ('value', '$y')],
            formatters={'@DATE_TIME': 'datetime'})

        plots = []
        i = 0
        for my_var in my_vars_dry:
            p = figure(plot_height=200,
                       plot_width=800,
                       toolbar_location='right',
                       tools="pan, ywheel_zoom, box_zoom, reset",
                       x_axis_type="datetime",
                       x_axis_location="below")
            p.line(x='DATE_TIME', y=my_var,
                   legend_label=my_var[:3] + ' (hourly average)', source=source, line_color='#1f77b4', alpha=0.3)
            p.line(x='DATE_TIME', y=my_var,
                   legend_label=my_var[:3] + ' (daily average)', source=source_day, line_color='#1f77b4')

            p.add_tools(hover_tool_p)
            p.legend.background_fill_alpha = 0.75
            p.legend.click_policy = "hide"
            p.legend.spacing = 0
            p.legend.padding = 2
            p.toolbar.logo = None
            plots.append(p)
            i += 1

        a = column(*plots)
        my_layout = grid([a], ncols=1)
        script, div = components(my_layout)

        return script, div
