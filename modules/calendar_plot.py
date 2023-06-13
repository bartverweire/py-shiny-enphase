from shiny import *
from shinywidgets import *

import datetime
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np

@module.ui
def calendar_plot_ui():
    return output_widget("out_calendar")

@module.server
def calendar_plot_server(input, output, session, data, metric, init_selection=None, multiple=False):
    clicked_day = reactive.Value([] if init_selection is None else [init_selection])

    # @reactive.Calc
    # def calendar_data():
    #     req(not data().empty, input.in_metric())
    #     df = data()
    #     df = df.groupby(["Day", "Month", "Month Name", "Day of Week", "Day of Month"])[input.in_metric()] \
    #         .sum() \
    #         .rename("Total") \
    #         .reset_index()
    #
    #     month = df["Month"].tolist()
    #     day_of_month = df["Day of Month"].tolist()
    #     day_of_week = df["Day of Week"].tolist()
    #     week_of_month = [int((day_of_month[i] - day_of_week[i] +(day_of_week[i]-day_of_month[i])%7)/7+1)for i in range(len(day_of_month))]
    #     min_month = min(month)
    #     x = [(month[i] - min_month) * 7 + day_of_week[i] for i in range(len(day_of_month))]
    #     y = week_of_month
    #
    #     df["x"] = x
    #     df["y"] = y
    #
    #     return df


    @output
    @render_widget
    def out_calendar():
        req(not data().empty)

        df = data()

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
                hovertemplate="Day: %{customdata|%Y-%B-%d}<br>" + metric() + ": %{z:.d}",
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

        if clicked_day():
            # show selected days
            df_sel = df[df["Day"].isin(clicked_day())]
            sel_x = []
            sel_y = []
            for i in df_sel.index:
                x = df_sel["x"].loc[i]
                y = df_sel["y"].loc[i]

                sel_x.extend([x-0.5, x-0.5, x+0.5, x+0.5, x-0.5, None])
                sel_y.extend([y-0.5, y+0.5, y+0.5, y-0.5, y-0.5, None])

            fig.add_trace(
                go.Scatter(
                    x=sel_x,
                    y=sel_y,
                    mode="lines",
                    line=dict(
                        color="green",
                        width=2
                    )
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
            height=200,
            margin=dict(t=10,b=0)
        )

        fig.data[0].on_click(click_day)

        return fig

    def click_day(trace, points, selector):
        with reactive.isolate():
            current_selection = clicked_day()

        if multiple:
            # remove already selected
            clicked_day.set([t.date() for t in trace.customdata[points.point_inds] if not t.date() in current_selection] +
                            [t for t in current_selection if t not in [t.date() for t in trace.customdata[points.point_inds]]])
        else:
            clicked_day.set([t.date() for t in trace.customdata[points.point_inds]])

    return clicked_day