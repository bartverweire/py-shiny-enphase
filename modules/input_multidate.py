from typing import List, Optional, Union
from htmltools import HTML, HTMLDependency, Tag, TagAttrArg, TagChildArg, css, div, span, tags
from shiny import *
from shiny.module import resolve_id
from shiny.ui._utils import *
from datetime import date

import json

def input_multidate(
    id: str,
    label: TagChildArg,
    *,
    value: Optional[Union[date, str]] = None,
    min: Optional[Union[date, str]] = None,
    max: Optional[Union[date, str]] = None,
    format: str = "yyyy-mm-dd",
    startview: str = "month",
    weekstart: int = 0,
    language: str = "en",
    width: Optional[str] = None,
    autoclose: bool = True,
    datesdisabled: Optional[List[str]] = None,
    daysofweekdisabled: Optional[List[int]] = None,
) -> Tag:
    """
    Creates a text input which, when clicked on, brings up a calendar that the user can
    click on to select dates.

    Parameters
    ----------
    id
        An input id.
    label
        An input label.
    value
        The starting date. Either a :func:`~datetime.date` object, or a string in
        `yyyy-mm-dd` format. If None (the default), will use the current date in the
        client's time zone.
    min
        The minimum allowed date. Either a :func:`~datetime.date` object, or a string in
        yyyy-mm-dd format.
    max
        The maximum allowed date. Either a :func:`~datetime.date` object, or a string in
        yyyy-mm-dd format.
    format
        The format of the date to display in the browser. Defaults to `"yyyy-mm-dd"`.
    startview
        The date range shown when the input object is first clicked. Can be "month" (the
        default), "year", or "decade".
    weekstart
        Which day is the start of the week. Should be an integer from 0 (Sunday) to 6
        (Saturday).
    language
        The language used for month and day names. Default is "en". Other valid values
        include "ar", "az", "bg", "bs", "ca", "cs", "cy", "da", "de", "el", "en-AU",
        "en-GB", "eo", "es", "et", "eu", "fa", "fi", "fo", "fr-CH", "fr", "gl", "he",
        "hr", "hu", "hy", "id", "is", "it-CH", "it", "ja", "ka", "kh", "kk", "ko", "kr",
        "lt", "lv", "me", "mk", "mn", "ms", "nb", "nl-BE", "nl", "no", "pl", "pt-BR",
        "pt", "ro", "rs-latin", "rs", "ru", "sk", "sl", "sq", "sr-latin", "sr", "sv",
        "sw", "th", "tr", "uk", "vi", "zh-CN", and "zh-TW".
    width
        The CSS width, e.g. '400px', or '100%'
    autoclose
        Whether or not to close the datepicker immediately when a date is selected.
    datesdisabled
        Which dates should be disabled (in `yyyy-mm-dd` format).
    daysofweekdisabled
        Days of the week that should be disabled. Should be a integer vector with values
        from 0 (Sunday) to 6 (Saturday).

    Returns
    -------
    A UI element.

    Note
    ----
    The date ``format`` string specifies how the date will be displayed in the browser.
    It allows the following values:

    - ``yy``: Year without century (12)
    - ``yyyy``: Year with century (2012)
    - ``mm``: Month number, with leading zero (01-12)
    - ``m``: Month number, without leading zero (1-12)
    - ``M``: Abbreviated month name
    - ``MM``: Full month name
    - ``dd``: Day of month with leading zero
    - ``d``: Day of month without leading zero
    - ``D``: Abbreviated weekday name
    - ``DD``: Full weekday name

    Notes
    ------
    .. admonition:: Server value

        A :func:`~datetime.date` object.

    See Also
    -------
    ~shiny.ui.update_date
    ~shiny.ui.input_date_range
    """

    return div(
        shiny_input_label(id, label),
        _date_input_tag(
            id=resolve_id(id),
            value=value,
            min=min,
            max=max,
            format=format,
            startview=startview,
            weekstart=weekstart,
            language=language,
            autoclose=autoclose,
            data_date_dates_disabled=json.dumps(datesdisabled),
            data_date_days_of_week_disabled=json.dumps(daysofweekdisabled),
            data_date_multidate="true"
        ),
        id=resolve_id(id),
        class_="shiny-date-input form-group shiny-input-container",
        style=css(width=width),
    )

def _date_input_tag(
    id: str,
    value: Optional[Union[date, str]],
    min: Optional[Union[date, str]],
    max: Optional[Union[date, str]],
    format: str,
    startview: str,
    weekstart: int,
    language: str,
    autoclose: bool,
    **kwargs: TagAttrArg,
):
    return tags.input(
        datepicker_deps(),
        {"class": "form-control"},
        type="text",
        # `aria-labelledby` attribute is required for accessibility to avoid doubled labels (#2951).
        aria_labelledby=id + "-label",
        # title attribute is announced for screen readers for date format.
        title="Date format: " + format,
        data_date_language=language,
        data_date_week_start=weekstart,
        data_date_format=format,
        data_date_start_view=startview,
        data_min_date=_as_date_attr(min),
        data_max_date=_as_date_attr(max),
        data_initial_date=_as_date_attr(value),
        data_date_autoclose="true" if autoclose else "false",
        **kwargs,
    )

def datepicker_deps() -> HTMLDependency:
    return HTMLDependency(
        name="bootstrap-datepicker",
        version="1.9.0",
        source={"package": "shiny", "subdir": "www/shared/datepicker/"},
        stylesheet={"href": "css/bootstrap-datepicker3.min.css"},
        script={"src": "js/bootstrap-datepicker.js"},
        # Need to enable noConflict mode. See #1346.
        head=HTML(
            "<script>(function() { var datepicker = $.fn.datepicker.noConflict(); $.fn.bsDatepicker = datepicker; })();</script>"
        ),
    )

def _as_date_attr(x: Optional[Union[date, str]]) -> Optional[str]:
    if x is None:
        return None
    if isinstance(x, date):
        return str(x)
    return str(date.fromisoformat(x))
