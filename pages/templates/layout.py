from shiny import ui, module

def build_sidebar(sidebar_ui, content_ui):
    return ui.layout_sidebar(
        ui.sidebar(
            *sidebar_ui,
            width=2,
            class_="sidebar"
        ),
        ui.panel_main(
            *content_ui,
            width=10,
            class_="page_content my-3"
        ),
    )
