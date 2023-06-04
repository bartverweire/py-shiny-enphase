from shiny import *
from shinywidgets import *
import shinycomponents.adminlte as sca
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from datetime import date, datetime, timedelta

import constants as co


@module.ui
def stats_ui():
    return ui.TagList(
        sca.dashboardSidebar(
            content=ui.tags.nav(
                ui.tags.ul(
                    ui.tags.li(
                        ui.input_select("in_granularity", "Granularity", choices=["Month", "Year"], selected="Month", width="90%"),
                    ),
                    data_lte_toggle="treeview",
                    data_accordion="false",
                    role="menu",
                    class_="nav nav-pills nav-sidebar flex-column"
                ),
                class_="mt-2"
            )
        ),
        output_widget("out_stats"),
    )

@module.server
def stats_server(input, output, session, data):

    @reactive.Calc
    def data_stats():
        req(input.in_granularity(), not data().empty)

        df = data()
        df = df.groupby([input.in_granularity(), "Time of Day"])["Produced"] \
            .quantile([0.1, 0.25, 0.5, 0.75, 0.9]) \
            .rename("Value") \
            .rename_axis(index=[input.in_granularity(), "Time of Day", "Level"]) \
            .unstack()

        df.columns = ["10%", "25%", "50%", "75%", "90%"]
        df = df.reset_index()

        print(df.info())

        return df


    @output
    @render_widget
    def out_stats():
        req(not data_stats().empty)

        df = data_stats()
        monhts = df["Month"].drop_duplicates().sort_values().tolist()

        rows = len(monhts) // 2 + 1
        cols = max(1, len(monhts) % 2 + 1)

        fig = make_subplots(rows, cols,
                            subplot_titles=monhts)

        for idx, month in enumerate(monhts):
            df_m = df[df["Month"] == month]

            traces = {
                "10%": {"legendgroup": "10%-90%", "line": dict(width=0), "fill": None, "fillcolor": None, "showlegend": False },
                "90%": {"legendgroup": "10%-90%", "line": dict(width=0), "fill": "tonexty", "fillcolor": "rgba(0, 0, 255, 0.1)", "showlegend": idx==0},
                "25%": {"legendgroup": "25%-75%", "line": dict(width=0), "fill": None, "fillcolor": None, "showlegend": False },
                "75%": {"legendgroup": "25%-75%", "line": dict(width=0), "fill": "tonexty", "fillcolor": "rgba(0, 0, 255, 0.2)", "showlegend": idx==0},
                "50%": {"legendgroup": "50%", "line": dict(width=1, color="blue"), "fill": None, "fillcolor": None, "showlegend": idx==0},
            }

            for key, value in traces.items():
                fig.add_trace(
                    go.Scatter(
                        x=df_m["Time of Day"],
                        y=df_m[key],
                        fill=value["fill"],
                        line=value["line"],
                        showlegend=value["showlegend"],
                        name=value["legendgroup"],
                        legendgroup=value["legendgroup"],
                        fillcolor=value["fillcolor"]
                    ),
                    row=idx // 2 + 1,
                    col=idx % 2 + 1
                )
            # fig.add_trace(
            #     go.Scatter(
            #         x=df_m["Time of Day"],
            #         y=df_m["10%"],
            #         line=dict(width=0),
            #         showlegend=False,
            #         legendgroup="10%-90%"
            #     ),
            #     row=idx // 2 + 1,
            #     col=idx % 2 + 1
            # )
            #
            # fig.add_trace(
            #     go.Scatter(
            #         x=df_m["Time of Day"],
            #         y=df_m["90%"],
            #         fill="tonexty",
            #         line=dict(width=0),
            #         showlegend=idx==0,
            #         legendgroup="10%-90%",
            #         fillcolor="rgba(0, 0, 255, 0.1)"
            #     ),
            #     row=idx // 2 + 1,
            #     col=idx % 2 + 1
            # )

        fig.update_layout(
            height=800
        )

        return go.FigureWidget(fig)
