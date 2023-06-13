from shiny import *
from shinywidgets import *
import shinycomponents.adminlte as sca
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from datetime import date, datetime, timedelta
from modules.input_multidate import *
from modules.calendar_plot import *

import constants as co
from .templates import build_sidebar


@module.ui
def calendar_ui():
    _sidebar = ui.TagList(
        ui.input_radio_buttons(
            "in_cal_metric",
            "Calendar Metric",
            choices=["Produced","Consumed", "Charged", "Discharged", "Imported","Exported"],
            selected="Produced",
            width="90%"
        ),
        ui.input_checkbox_group(
            "in_metric",
            "Display Metrics",
            choices=["Produced", "Consumed", "Charged", "Discharged", "Imported", "Exported"],
            selected=["Produced", "Consumed", "Charged", "Discharged", "Imported", "Exported"],
            width="90%"
        )
    )

    _content = ui.TagList(
        # output_widget("out_calendar"),
        calendar_plot_ui("out_calendar"),
        ui.row(
            ui.column(
                3,
                sca.output_value_box("out_eff_to_max", width=8),
                offset=2
            ),
            ui.column(
                3,
                sca.output_value_box("out_eff_to_month_max", width=8),
            ),
            ui.column(
                3,
                sca.output_value_box("out_eff_to_week_max", width=8)
            ),
            class_="mt-5"
        ),
        ui.row(
            ui.column(
                12,
                output_widget("out_metric"),
            )
        )
    )

    return build_sidebar(
        _sidebar,
        _content
    )

@module.server
def calendar_server(input, output, session, data):
    # clicked_day = reactive.Value()
    calendar_data = reactive.Value(pd.DataFrame())
    metric = reactive.Value(None)

    flt_selected_days = calendar_plot_server("out_calendar", calendar_data, metric, init_selection=date.today())

    @reactive.Effect
    def update_calendar_data():
        req(not data().empty, input.in_cal_metric())
        df = data()
        df = df.groupby(["Day", "Month", "Month Name", "Day of Week", "Day of Month"])[input.in_cal_metric()] \
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
    def update_metric():
        metric.set(input.in_cal_metric())


    @reactive.Calc
    def selected_summary_data():
        req(flt_selected_days(), not data().empty)

        df = data()
        print(flt_selected_days(), type(flt_selected_days()))
        df = df[["Time of Day",
                 "Max Produced (Global)",
                 "Max Produced (Month)",
                 "Max Produced (Week)",
                 input.in_cal_metric()]][df["Day"].isin(flt_selected_days())]

        return df



    @reactive.Calc
    def selected_data():
        req(flt_selected_days(), not data().empty)

        df = data()
        print(flt_selected_days(), type(flt_selected_days()))
        selected_metrics = input.in_metric()

        if type(selected_metrics) == str:
            selected_metrics = [selected_metrics]
        else:
            # convert tuple to list
            selected_metrics = list(selected_metrics)

        if "Produced" in input.in_metric():
            columns = [
                "Time of Day",
                "Max Produced (Global)",
                "Max Produced (Month)",
                "Max Produced (Week)"
            ] + selected_metrics
        else:
            columns = [
                "Time of Day"
            ] + selected_metrics

        df = df[columns][df["Day"].isin(flt_selected_days())]

        return df


    @output
    @render_widget
    def out_metric():
        req(not selected_data().empty)

        df = selected_data().copy()

        fig = px.bar(
            df,
            x="Time of Day",
            y=list(input.in_metric()),
            color_discrete_map=co.colors,
            height=400)

        if "Produced" in input.in_metric():

            fig.add_trace(
                go.Scatter(x=df["Time of Day"], y=df["Max Produced (Global)"], mode="lines",
                           line=dict(
                               color="green",
                               width=1
                           ))
            )

            fig.add_trace(
                go.Scatter(x=df["Time of Day"], y=df["Max Produced (Month)"], mode="lines",
                           line=dict(
                               color="orange",
                               width=1
                           ))
            )

            fig.add_trace(
                go.Scatter(x=df["Time of Day"], y=df["Max Produced (Week)"], mode="lines",
                           line=dict(
                               color="red",
                               width=1
                           ))
            )

        return go.FigureWidget(fig)

    @output
    @sca.render_value_box
    def out_eff_to_max():
        req(not selected_summary_data().empty)
        df = selected_summary_data()

        return create_value_box(df, "Produced", "Max Produced (Global)", "Efficiency to max", "bi-speedometer2")
        # total_selected_day = df["Produced"].sum()
        # max_selected_day = df["Max Produced (Global)"].sum()
        # eff = round(100 * total_selected_day / max_selected_day, 0)
        #
        # if eff >= 75:
        #     eff_color = "success"
        # elif eff >= 50:
        #     eff_color = "primary"
        # elif eff >= 25:
        #     eff_color = "warning"
        # else:
        #     eff_color = "danger"
        #
        # return sca.value_box(
        #     value = eff,
        #     unit="%",
        #     subtitle="Efficiency to max",
        #     icon="bi-speedometer2",
        #     color=eff_color
        # )

    @output
    @sca.render_value_box
    def out_eff_to_month_max():
        req(not selected_summary_data().empty)
        df = selected_summary_data()

        return create_value_box(df, "Produced", "Max Produced (Month)", "Efficiency to month max", "bi-speedometer2")
        # total_selected_day = df["Produced"].sum()
        # max_selected_day = df["Max Produced (Month)"].sum()
        # eff = round(100 * total_selected_day / max_selected_day, 0)
        #
        # if eff >= 75:
        #     eff_color = "success"
        # elif eff >= 50:
        #     eff_color = "primary"
        # elif eff >= 25:
        #     eff_color = "warning"
        # else:
        #     eff_color = "danger"
        #
        # return sca.value_box(
        #     value = eff,
        #     unit="%",
        #     subtitle="Efficiency to month max",
        #     icon="bi-speedometer2",
        #     color=eff_color
        # )

    @output
    @sca.render_value_box
    def out_eff_to_week_max():
        req(not selected_summary_data().empty)
        df = selected_summary_data()

        return create_value_box(df, "Produced", "Max Produced (Week)", "Efficiency to week max", "bi-speedometer2")
        # total_selected_day = df["Produced"].sum()
        # max_selected_day = df["Max Produced (Week)"].sum()
        # eff = round(100 * total_selected_day / max_selected_day, 0)
        #
        # if eff >= 75:
        #     eff_color = "success"
        # elif eff >= 50:
        #     eff_color = "primary"
        # elif eff >= 25:
        #     eff_color = "warning"
        # else:
        #     eff_color = "danger"
        #
        # return sca.value_box(
        #     value = eff,
        #     unit="%",
        #     subtitle="Efficiency to week max",
        #     icon="bi-speedometer2",
        #     color=eff_color
        # )

    def create_value_box(df, metric, compare_to_metric, title, icon):
        total_selected_day = df[metric].sum()
        max_selected_day = df[compare_to_metric].sum()
        eff = round(100 * total_selected_day / max_selected_day, 0)

        if eff >= 75:
            eff_color = "success"
        elif eff >= 50:
            eff_color = "primary"
        elif eff >= 25:
            eff_color = "warning"
        else:
            eff_color = "danger"

        return sca.value_box(
            value=eff,
            unit="%",
            subtitle=title,
            icon=icon,
            color=eff_color
        )