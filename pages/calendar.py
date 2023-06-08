from shiny import *
from shinywidgets import *
import shinycomponents.adminlte as sca
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from datetime import date, datetime, timedelta
from modules.input_multidate import *

import constants as co
from .templates import build_sidebar


@module.ui
def calendar_ui():
    _sidebar = ui.TagList(
        ui.input_select(
            "in_metric",
            "Metric",
            choices=["Produced","Consumed", "Charged", "Discharged", "Imported","Exported"],
            selected="Produced",
            multiple=False,
            width="90%"
        ),
        input_multidate(
            "in_multidate",
            "Dates",
            format="yyyy-mm-dd",
            autoclose=False
        )
    )

    _content = ui.TagList(
        output_widget("out_calendar"),
        ui.row(
            ui.column(
                2,
                sca.output_value_box("out_eff_to_max"),
                sca.output_value_box("out_eff_to_month_max"),
                sca.output_value_box("out_eff_to_week_max")
            ),
            ui.column(
                10,
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
    clicked_day = reactive.Value()

    @reactive.Calc
    def calendar_data():
        req(not data().empty, input.in_metric())
        df = data()
        df = df.groupby(["Day", "Month", "Month Name", "Day of Week", "Day of Month"])[input.in_metric()] \
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

        return df


    @reactive.Calc
    def selected_data():
        req(clicked_day(), not data().empty)

        df = data()
        print(clicked_day(), type(clicked_day()))
        df = df[["Time of Day",
                 "Max Produced (Global)",
                 "Max Produced (Month)",
                 "Max Produced (Week)",
                 input.in_metric()]][df["Day"].isin(clicked_day())]

        return df


    @output
    @render_widget
    def out_calendar():
        req(not calendar_data().empty)

        df = calendar_data()

        month_names = df["Month Name"].drop_duplicates().tolist()

        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                x=df["x"],
                y=df["y"],
                z=df["Total"],
                customdata=pd.to_datetime(df["Day"]),
                xgap=3,
                ygap=3,
                text=df["Day of Month"],
                colorscale="YlGn",
                hovertemplate="Day: %{customdata|%Y-%B-%d}<br>" + input.in_metric() + ": %{z:.d}",
                hoverongaps=False,
                texttemplate="%{text}",
                reversescale=True
            )
        )

        fig.add_trace(
            go.Scatter(
                x=[i * 7 for i in range(len(month_names))],
                y=[-1 for i in range(len(month_names))],
                text=month_names,
                mode="text"
            )
        )

        # show month lines
        line_data_x = [[i * 7 - 0.5, i * 7 - 0.5, None] for i in range(len(month_names))]
        line_data_y = [[0, 7, None] for i in range(len(month_names))]
        line_data_x = [item for sublist in line_data_x for item in sublist]
        line_data_y = [item for sublist in line_data_y for item in sublist]

        fig.add_trace(
            go.Scatter(
                x=line_data_x,
                y=line_data_y,
                mode="lines",
                line=dict(
                    color="lightgrey",
                    width=2,
                ),
                hoverinfo='skip'
            )
        )

        fig = go.FigureWidget(fig)

        # Update cosmetics
        fig.update_yaxes(
            autorange="reversed",
            showticklabels=False,
            showgrid=False,
            showline=False,
            visible=False,
        )
        fig.update_xaxes(
            showticklabels=False,
            showgrid=False,
            showline=False,
            visible=False
        )
        fig.update_layout(
            showlegend=False,
            height=400
        )

        fig.data[0].on_click(click_day)

        return fig

    @output
    @render_widget
    def out_metric():
        req(not selected_data().empty)

        df = selected_data().copy()
        df["Metric"] = input.in_metric()

        fig = px.bar(
            df,
            x="Time of Day",
            y=input.in_metric(),
            color="Metric",
            color_discrete_map=co.colors,
            height=400)

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
        req(not selected_data().empty)
        df = selected_data()

        total_selected_day = df["Produced"].sum()
        max_selected_day = df["Max Produced (Global)"].sum()
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
            value = eff,
            unit="%",
            subtitle="Efficiency to max",
            icon="bi-speedometer2",
            color=eff_color
        )

    @output
    @sca.render_value_box
    def out_eff_to_month_max():
        req(not selected_data().empty)
        df = selected_data()

        total_selected_day = df["Produced"].sum()
        max_selected_day = df["Max Produced (Month)"].sum()
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
            value = eff,
            unit="%",
            subtitle="Efficiency to month max",
            icon="bi-speedometer2",
            color=eff_color
        )

    @output
    @sca.render_value_box
    def out_eff_to_week_max():
        req(not selected_data().empty)
        df = selected_data()

        total_selected_day = df["Produced"].sum()
        max_selected_day = df["Max Produced (Week)"].sum()
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
            value = eff,
            unit="%",
            subtitle="Efficiency to week max",
            icon="bi-speedometer2",
            color=eff_color
        )

    # @output
    # @render.text
    # def out_debug_click():
    #     return clicked_day()


    def click_day(trace, points, selector):
        clicked_day.set([t.date() for t in trace.customdata[points.point_inds]])
