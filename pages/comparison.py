from shiny import *
from shinywidgets import *
import shinycomponents.adminlte as sca
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from datetime import date, datetime, timedelta

from .templates import build_sidebar

@module.ui
def comp_ui():
    _sidebar = ui.TagList(
        ui.input_date(
            "in_date", "Date",
            min=date.today() - timedelta(days=90),
            max=date.today(),
            autoclose=False,
            width="90%"
        ),
        ui.input_select("in_granularity", "Granularity", choices=["15 min", "hour", "day", "month"], selected="day"),
    )

    _content = ui.TagList(
        output_widget("out_comparison"),
    )

    return build_sidebar(
        _sidebar,
        _content
    )


@module.server
def comp_server(input, output, session, data):
    selected_dates = reactive.Value([])

    @reactive.Effect
    def add_date():
        req(input.in_date())

        with reactive.isolate():
            current_dates = selected_dates()

        if not input.in_date() in current_dates:
            current_dates.append(input.in_date())
        else:
            current_dates.remove(input.in_date())

        current_dates.sort()

        selected_dates.set(current_dates.copy())

    @reactive.Calc
    def selected_data():
        df = data()

        df = df[df["Day"].isin(selected_dates())]

        return df

    @output
    @render_widget
    def out_comparison():
        req(not selected_data().empty)

        dfs = selected_data()
        dfs = dfs[["Day","Time of Day","Produced","Consumed","Imported","Exported"]]

        dfs = dfs.melt(id_vars=["Day","Time of Day"], value_vars=["Produced","Consumed","Imported","Exported"], var_name="Property", value_name="Wh")

        fig = px.line(dfs,
                      x="Time of Day",
                      y="Wh",
                      color="Day",
                      facet_row="Property",
                      height=1600)

        return go.FigureWidget(fig)
