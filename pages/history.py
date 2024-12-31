from shiny import *
from shinywidgets import *
# import shinycomponents.adminlte as sca
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .templates import build_sidebar
from datetime import date, datetime, timedelta
import shinycomponents.modalfilter as scmf

import constants as co


@module.ui
def history_sidebar_ui():
    return ui.TagList(
        ui.input_radio_buttons(
            "in_granularity", "Granularity",
            choices={
                "Time": "15 min",
                "Hour": "Hour",
                "Day": "Day",
                "Month": "Month"
            },
            selected="Day"
        ),
        ui.input_checkbox_group(
            "in_metrics",
            "Display Metrics",
            choices=["Produced", "Consumed", "Charged", "Discharged", "Imported", "Exported"],
            selected=["Produced", "Consumed", "Charged", "Discharged", "Imported", "Exported"],
            width="90%"
        ),
    )


@module.ui
def history_ui():
    return ui.TagList(
        ui.h3("Time range selection"),
        ui.p("Select a time range for the history to be displayed"),
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
        ui.h3("Time of day selection"),
        ui.p("Click on a bar to filter the history for this hour. Click again to unselect"),
        output_widget("out_summary"),
        ui.h3("History"),
        output_widget("out_history"),
        ui.h3("History Detail"),
        output_widget("out_history_detail")
    )


@module.server
def history_server(input, output, session, data):
    clicked_timeofday = reactive.Value([])

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
        req(input.in_time_range())

        df = data()
        df = df.groupby("Time of Day")[["Produced","Consumed","Imported","Exported","Charged","Discharged"]] \
            .sum(numeric_only=True) \
            .reset_index()

        return df

    @reactive.Calc
    def data_history():
        req(input.in_time_range(), input.in_granularity(), not data().empty)

        df = data()
        df = df[(df["Time"] >= input.in_time_range()[0]) & (df["Time"] <= input.in_time_range()[1])]
        if clicked_timeofday():
            df = df[df["Time of Day"].isin(clicked_timeofday())]

        if input.in_granularity() in ["Hour", "Day", "Month"]:
            df = df.groupby(input.in_granularity()).sum(numeric_only=True).reset_index()

        return df


    @output
    @render_widget
    def out_history():
        req(not data_history().empty, input.in_granularity())

        df = data_history().copy()
        if input.in_granularity() == "Day":
            df["Day"] = pd.to_datetime(df["Day"])

        print(df.head())
        fig = px.bar(
            df,
            x=input.in_granularity(),
            y=["Produced","Consumed","Imported","Exported","Charged","Discharged"],
            color_discrete_map=co.colors,
            height=400)

        return go.FigureWidget(fig)


    @output
    @render_widget
    def out_history_detail():
        req(not data_history().empty, clicked_timeofday())

        df = data_history().copy()
        df["Day"] = pd.to_datetime(df["Day"])
        metrics = input.in_metrics()

        rows = (len(metrics) - 1) // 2 + 1
        cols = max(1, (len(metrics) + 1) % 2 + 1)

        fig = make_subplots(rows, cols,
                            subplot_titles=metrics)

        for idx, metric in enumerate(metrics):
            fig.add_trace(
                px.line(
                    df,
                    x="Day",
                    y=metric,
                    color="Time of Day"
                )["data"],
                row=idx // 2 + 1,
                col=idx % 2 + 1
            )

        fig.update_layout(
            height=800
        )

        return go.FigureWidget(fig)


    @output
    @render_widget
    def out_summary():
        req(not data_summary().empty)

        df = data_summary()
        print(df.head())
        fig = px.bar(
            df,
            x="Time of Day",
            y=["Produced","Consumed","Imported","Exported","Charged","Discharged"],
            color_discrete_map=co.colors,
            height=300)

        fig = go.FigureWidget(fig)
        for d in fig.data:
            d.on_click(click_handler)

        return fig


    def click_handler(trace, points, selector):
        with reactive.isolate():
            current_selection = clicked_timeofday()

        # remove already selected
        clicked_timeofday.set(
            [t for t in trace.x[points.point_inds] if not t in current_selection] +
            [t for t in current_selection if t not in [t for t in trace.x[points.point_inds]]]
        )

    @output
    @render.text
    def out_debug():
        return clicked_timeofday()