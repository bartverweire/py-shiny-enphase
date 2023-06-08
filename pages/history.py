from shiny import *
from shinywidgets import *
import shinycomponents.adminlte as sca
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .templates import build_sidebar
from datetime import date, datetime, timedelta
import shinycomponents.modalfilter as scmf

import constants as co


@module.ui
def history_ui():
    _sidebar = ui.TagList(
        ui.input_select("in_granularity", "Granularity", choices=["15 min", "hour", "day", "month"], selected="day"),
    )

    _content = ui.TagList(
        ui.row(
            ui.column(
                1,
            ),
            ui.column(
                10,
                ui.input_slider("in_time_range", "Time Range",
                                min=datetime.now() - timedelta(days=90),
                                max=datetime.now(),
                                value=[datetime.now() - timedelta(days=7), datetime.now() - timedelta(days=1)],
                                step=3600,
                                time_format="%Y-%m-%d %H:%M",
                                width="100%")
            ),
            ui.column(
                1,
            )
        ),
        output_widget("out_history"),
    )

    return build_sidebar(
        _sidebar,
        _content
    )

@module.server
def history_server(input, output, session, data):

    @reactive.Effect
    def update_time_range():
        req(not data().empty)

        min_time = data()["Time"].min()
        max_time = data()["Time"].max()
        # min_time = datetime.now() - timedelta(days=10)
        # max_time = datetime.now()

        # ui.update_slider("in_time_range", min=datetime.now() - timedelta(days=30), max=datetime.now(),
        #                  value=[datetime.today(), datetime.now()], step=900)
        ui.update_slider("in_time_range",
                         min=min_time,
                         max=max_time,
                         time_format="%Y-%m-%d %H:%M:%S",
                         step=3600)

    @reactive.Calc
    def time_column():
        if input.in_granularity() == "hour":
            col="Hour"
        elif input.in_granularity() == "day":
            col="Day"
        elif input.in_granularity() == "month":
            col="Month"
        else:
            col="Time"

        return col



    @reactive.Calc
    def data_summary():
        req(input.in_time_range(), input.in_granularity(), not data().empty)

        df = data()
        df = df[(df["Time"] >= input.in_time_range()[0]) & (df["Time"] <= input.in_time_range()[1])]

        if input.in_granularity() in ["hour","day","month"]:
            df = df.groupby(time_column()).sum(numeric_only=True).reset_index()

        return df


    @output
    @render_widget
    def out_history():
        req(not data_summary().empty, time_column())

        df = data_summary()
        fig = px.bar(
            df,
            x=time_column(),
            y=["Produced","Consumed","Imported","Exported"],
            color_discrete_map=co.colors,
            height=800)

        return go.FigureWidget(fig)
