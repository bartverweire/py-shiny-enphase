from shiny import *
from shinywidgets import *
import shinycomponents.adminlte as sca
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from datetime import date, datetime, timedelta

from modules.calendar_plot import *
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
        calendar_plot_ui("out_calendar"),
        output_widget("out_comparison"),
    )

    return build_sidebar(
        _sidebar,
        _content
    )


@module.server
def comp_server(input, output, session, data):
    selected_dates = reactive.Value([])
    calendar_data = reactive.Value(pd.DataFrame())
    metric = reactive.Value("Produced")

    flt_selected_days = calendar_plot_server("out_calendar", calendar_data, metric, init_selection=date.today(), multiple=True)

    @reactive.Effect
    def update_calendar_data():
        req(not data().empty)
        df = data()
        df = df.groupby(["Day", "Month", "Month Name", "Day of Week", "Day of Month"])[metric()] \
            .sum() \
            .rename("Total") \
            .reset_index()

        month = df["Month"].tolist()
        day_of_month = df["Day of Month"].tolist()
        day_of_week = df["Day of Week"].tolist()
        week_of_month = [int((day_of_month[i] - day_of_week[i] +(day_of_week[i]-day_of_month[i])%7)/7+1)for i in range(len(day_of_month))]
        min_month = min(month)
        x = [(month[i] - min_month) * 7 + day_of_week[i] for i in range(len(day_of_month))]
        y = week_of_month

        df["x"] = x
        df["y"] = y

        calendar_data.set(df)


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

        df = df[df["Day"].isin(flt_selected_days())]

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
