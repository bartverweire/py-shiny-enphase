from shiny import *
from shinywidgets import *
import shinycomponents.adminlte as sca
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from datetime import date, datetime, timedelta

import constants as co
from .templates import build_sidebar

@module.ui
def today_ui():
    _sidebar = ui.TagList(

    )

    _content = ui.TagList(
        output_widget("out_today"),
    )

    return build_sidebar(
        _sidebar,
        _content
    )


@module.server
def today_server(input, output, session, data):
    selected_dates = reactive.Value([])

    @reactive.Calc
    def today_data():
        df = data()

        df = df[df["Day"] == date.today()]

        return df

    @output
    @render_widget
    def out_today():
        req(not today_data().empty)

        # dfs = today_data()
        # dfs = dfs[["Day","Time of Day","Produced","Consumed","Imported","Exported"]]
        #
        # dfs = dfs.melt(id_vars=["Day","Time of Day"], value_vars=["Produced","Consumed","Imported","Exported"], var_name="Property", value_name="Wh")
        #
        # fig = px.line(dfs,
        #               x="Time of Day",
        #               y="Wh",
        #               color="Day",
        #               facet_row="Property",
        #               height=1600)
        #
        # return go.FigureWidget(fig)
        df = today_data().copy()
        df["Category"] = "Produced"

        fig = px.bar(
            df,
            x="Time of Day",
            y="Produced",
            color="Category",
            color_discrete_map=co.colors,
            height=400)

        fig.add_trace(
            go.Scatter(x=df["Time of Day"], y=df["Max Produced (Global)"], mode="lines",
                       name="Max (Global)",
                       line=dict(
                           color="green",
                           width=1
                       ))
        )

        fig.add_trace(
            go.Scatter(x=df["Time of Day"], y=df["Max Produced (Month)"], mode="lines",
                       name="Max (Month)",
                       line=dict(
                           color="orange",
                           width=1
                       ))
        )

        fig.add_trace(
            go.Scatter(x=df["Time of Day"], y=df["Max Produced (Week)"], mode="lines",
                       name="Max (Week)",
                       line=dict(
                           color="red",
                           width=1
                       ))
        )

        return go.FigureWidget(fig)
