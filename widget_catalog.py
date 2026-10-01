"""Built-in Flet controls offered by the visual builder."""

import flet as ft


WIDGETS = {
    "Text": {"value": "Text", "size": 20},
    "Button": {"content": "Button"},
    "FilledButton": {"content": "Confirm"},
    "FilledTonalButton": {"content": "Continue"},
    "OutlinedButton": {"content": "Outlined"},
    "TextButton": {"content": "Text button"},
    "FloatingActionButton": {"content": "Add"},
    "IconButton": {"icon": "STAR"},
    "TextField": {"label": "Label", "hint_text": "", "password": False},
    "Checkbox": {"label": "Checkbox", "value": False},
    "Switch": {"label": "Switch", "value": False},
    "Radio": {"label": "Option", "value": "option1"},
    "Dropdown": {"label": "Choose one", "value": "One", "options": ["One", "Two", "Three"]},
    "Slider": {"value": 0.5, "min": 0, "max": 1},
    "RangeSlider": {"start_value": 0.25, "end_value": 0.75, "min": 0, "max": 1},
    "ProgressBar": {"value": 0.5},
    "ProgressRing": {"value": 0.65},
    "Icon": {"icon": "STAR", "size": 32},
    "Image": {"src": "https://picsum.photos/320/120"},
    "Container": {"content": "Container content", "items": []},
    "Row": {"items": ["First", "Second"]},
    "Column": {"items": ["First item", "Second item"]},
    "Stack": {"items": ["Back", "Front"]},
    "ListView": {"items": ["First item", "Second item", "Third item"]},
    "GridView": {"items": ["One", "Two", "Three", "Four"]},
    "ResponsiveRow": {"items": ["First", "Second"]},
    "SafeArea": {"content": "Safe area content"},
    "Card": {"content": "Card content"},
    "ListTile": {"title": "List item", "subtitle": "Description"},
    "ExpansionTile": {"title": "More details", "subtitle": "Tap to expand", "items": ["Expanded content"]},
    "Divider": {},
    "VerticalDivider": {},
    "Placeholder": {},
    "CircleAvatar": {"content": "F"},
    "Chip": {"label": "Tag"},
    "AppBar": {"title": "App title"},
    "SelectionArea": {"content": "Selectable text"},
    "AnimatedSwitcher": {"content": "Switchable content"},
    "InteractiveViewer": {"content": "Zoomable content"},
    "GestureDetector": {"content": "Gesture target"},
    "PageView": {"items": ["Page one", "Page two"]},
    "Markdown": {"value": "## Markdown\nFlet renders **Markdown** content."},
    "DataTable": {"columns": ["Name", "Status"], "rows": [["Welcome", "Ready"], ["Profile", "Draft"]]},
}


_TEXT_BUTTONS = {"Button", "FilledButton", "FilledTonalButton", "OutlinedButton", "TextButton"}
CLICK_WIDGETS = _TEXT_BUTTONS | {
    "FloatingActionButton", "IconButton", "TextField", "Container", "ListTile", "Chip",
}
_LAYOUTS = {"Row", "Column", "Stack", "ListView", "GridView", "ResponsiveRow"}
TEXT_PROPERTY = {
    "Text": "value", "Button": "content", "FilledButton": "content",
    "FilledTonalButton": "content", "OutlinedButton": "content", "TextButton": "content",
    "FloatingActionButton": "content", "TextField": "value", "Checkbox": "label",
    "Switch": "label", "Radio": "label", "Dropdown": "label", "Container": "content",
    "SafeArea": "content", "Card": "content", "ListTile": "title",
    "ExpansionTile": "title", "CircleAvatar": "content", "Chip": "label",
    "AppBar": "title", "SelectionArea": "content", "AnimatedSwitcher": "content",
    "InteractiveViewer": "content", "GestureDetector": "content", "Markdown": "value",
}
def normalize_props(kind, props):
    """Fill common and widget-specific properties with editable defaults."""
    defaults = WIDGETS[kind]
    result = {}
    text_key = TEXT_PROPERTY.get(kind)
    if text_key:
        result[text_key] = defaults.get(text_key, "")
    result["size"] = defaults.get("size", 16.0)
    result.update({
        "color": None, "bgcolor": None,
        "visible": True, "disabled": False, "opacity": 1.0,
        "tooltip": "", "width": None, "height": None, "expand": False,
        "autofocus": False, "can_request_focus": True,
        "horizontal_alignment": "Left", "vertical_alignment": "Top",
    })
    for key, value in defaults.items():
        if key not in result:
            result[key] = value
    result.update(props)
    result.pop("z_index", None)
    return result


def property_label(kind, key):
    if key == TEXT_PROPERTY.get(kind):
        return "Text"
    common = {
        "size": "Size", "color": "Color", "bgcolor": "Background color",
        "visible": "Visible", "disabled": "Disabled",
        "opacity": "Opacity", "tooltip": "Tooltip", "width": "Width",
        "height": "Height", "expand": "Expand",
        "autofocus": "Autofocus", "can_request_focus": "Can request focus",
        "horizontal_alignment": "Horizontal alignment",
        "vertical_alignment": "Vertical alignment",
    }
    return common.get(key, key.replace("_", " ").title())


def apply_widget_properties(control, kind, props):
    """Apply shared editable properties that Flet controls expose."""
    for name in (
        "visible", "disabled", "opacity", "tooltip",
        "autofocus", "can_request_focus",
    ):
        value = props.get(name)
        if value is not None and hasattr(control, name):
            setattr(control, name, value)

    size = props.get("size")
    color = _color(props.get("color"))
    bgcolor = _color(props.get("bgcolor"))
    if size is not None:
        if hasattr(control, "size"):
            control.size = size
        if hasattr(control, "text_size"):
            control.text_size = size
    if color:
        for name in ("color", "active_color", "icon_color"):
            if hasattr(control, name):
                setattr(control, name, color)
                break
    if bgcolor and hasattr(control, "bgcolor"):
        control.bgcolor = bgcolor

    style_values = {}
    if size is not None:
        style_values["size"] = size
    if color:
        style_values["color"] = color
    if style_values:
        style = ft.TextStyle(**style_values)
        for name in ("label_style", "label_text_style", "title_text_style", "subtitle_text_style", "data_text_style"):
            if hasattr(control, name):
                setattr(control, name, style)
        _style_text_descendants(control, size, color)

    if bgcolor and not hasattr(control, "bgcolor"):
        control = ft.Container(content=control, bgcolor=bgcolor)

    horizontal = {"Left": -1, "Center": 0, "Right": 1}.get(
        props.get("horizontal_alignment", "Left"), -1
    )
    vertical = {"Top": -1, "Center": 0, "Bottom": 1}.get(
        props.get("vertical_alignment", "Top"), -1
    )
    if (
        horizontal == -1
        and vertical == -1
        and props.get("width") is None
        and props.get("height") is None
        and not props.get("expand", False)
    ):
        return control
    return ft.Container(
        content=control,
        alignment=ft.Alignment(x=horizontal, y=vertical),
        width=props.get("width"),
        height=props.get("height"),
        expand=bool(props.get("expand", False)),
    )


def _style_text_descendants(control, size, color):
    if isinstance(control, ft.Text):
        if size is not None:
            control.size = size
        if color:
            control.color = color
    for name in ("content", "title", "subtitle", "controls", "cells"):
        child = getattr(control, name, None)
        children = child if isinstance(child, list) else [child]
        for item in children:
            if isinstance(item, ft.Control):
                _style_text_descendants(item, size, color)
            elif hasattr(item, "content") and isinstance(item.content, ft.Control):
                _style_text_descendants(item.content, size, color)


def _color(value):
    if value is None or value == "":
        return None
    if hasattr(ft.Colors, str(value).upper()):
        return getattr(ft.Colors, str(value).upper())
    return value


def _icon(name):
    return getattr(ft.Icons, str(name), ft.Icons.STAR)


def make_control(kind, props, children=None):
    """Create a preview control, optionally composed with builder child widgets."""
    p = props
    child_controls = children if children is not None else None
    if kind == "Text":
        return ft.Text(value=str(p.get("value", "Text")), size=float(p.get("size", 20)))
    if kind in _TEXT_BUTTONS:
        return getattr(ft, kind)(content=ft.Text(str(p.get("content", kind))))
    if kind == "FloatingActionButton":
        return ft.FloatingActionButton(content=ft.Text(str(p.get("content", "Add"))))
    if kind == "IconButton":
        return ft.IconButton(icon=_icon(p.get("icon", "STAR")))
    if kind == "TextField":
        return ft.TextField(value=str(p.get("value", "")), label=p.get("label", ""), hint_text=p.get("hint_text", ""), password=bool(p.get("password", False)))
    if kind == "Checkbox":
        return ft.Checkbox(label=p.get("label", "Checkbox"), value=bool(p.get("value", False)))
    if kind == "Switch":
        return ft.Switch(label=p.get("label", "Switch"), value=bool(p.get("value", False)))
    if kind == "Radio":
        return ft.Radio(label=p.get("label", "Option"), value=str(p.get("value", "option1")))
    if kind == "Dropdown":
        options = [ft.DropdownOption(text=str(option)) for option in p.get("options", ["One", "Two"])]
        value = p.get("value", options[0].text if options else None)
        return ft.Dropdown(label=p.get("label", "Choose one"), value=value, options=options)
    if kind == "Slider":
        low, high = float(p.get("min", 0)), float(p.get("max", 1))
        return ft.Slider(value=max(low, min(high, float(p.get("value", 0.5)))), min=low, max=high)
    if kind == "RangeSlider":
        low, high = float(p.get("min", 0)), float(p.get("max", 1))
        start = max(low, min(high, float(p.get("start_value", 0.25))))
        end = max(start, min(high, float(p.get("end_value", 0.75))))
        return ft.RangeSlider(start_value=start, end_value=end, min=low, max=high)
    if kind in {"ProgressBar", "ProgressRing"}:
        value = max(0.0, min(1.0, float(p.get("value", 0.5))))
        return getattr(ft, kind)(value=value)
    if kind == "Icon":
        return ft.Icon(icon=_icon(p.get("icon", "STAR")), size=float(p.get("size", 32)))
    if kind == "Image":
        return ft.Image(src=str(p.get("src", "")), width=240, height=100, fit=ft.BoxFit.CONTAIN, error_content=ft.Text("Image unavailable"))
    if kind == "Container":
        content = p.get("content", "Container content")
        static_children = _text_items(p.get("items", []))
        controls = [ft.Text(str(content)), *static_children, *(child_controls or [])]
        return ft.Container(content=ft.Column(controls=controls))
    if kind in _LAYOUTS:
        children = child_controls if child_controls is not None else _text_items(p.get("items", []))
        if not children:
            children = [ft.Text("Add items in the Items property")]
        if kind == "Row":
            return ft.Row(controls=children)
        if kind == "Column":
            return ft.Column(controls=children)
        if kind == "Stack":
            return ft.Stack(controls=[ft.Container(content=item) for item in children])
        if kind == "ListView":
            return ft.ListView(controls=children, height=150)
        if kind == "GridView":
            return ft.GridView(controls=[ft.Container(content=item) for item in children], max_extent=100, height=160)
        return ft.ResponsiveRow(controls=children)
    if kind == "SafeArea":
        return ft.SafeArea(content=ft.Text(str(p.get("content", "Safe area content"))))
    if kind == "Card":
        return ft.Card(content=ft.Container(content=ft.Text(str(p.get("content", "Card content"))), padding=12))
    if kind == "ListTile":
        return ft.ListTile(title=ft.Text(str(p.get("title", "List item"))), subtitle=ft.Text(str(p.get("subtitle", "Description"))))
    if kind == "ExpansionTile":
        children = _text_items(p.get("items", [])) or [ft.Text("Expanded content")]
        return ft.ExpansionTile(title=ft.Text(str(p.get("title", "More details"))), subtitle=ft.Text(str(p.get("subtitle", ""))), controls=children)
    if kind == "Divider":
        return ft.Divider()
    if kind == "VerticalDivider":
        return ft.VerticalDivider()
    if kind == "Placeholder":
        return ft.Placeholder(width=120, height=60)
    if kind == "CircleAvatar":
        return ft.CircleAvatar(content=ft.Text(str(p.get("content", "F"))))
    if kind == "Chip":
        return ft.Chip(label=str(p.get("label", "Tag")))
    if kind == "AppBar":
        return ft.AppBar(title=ft.Text(str(p.get("title", "App title"))))
    if kind == "SelectionArea":
        return ft.SelectionArea(content=ft.Text(str(p.get("content", "Selectable text"))))
    if kind == "AnimatedSwitcher":
        return ft.AnimatedSwitcher(content=ft.Text(str(p.get("content", "Switchable content"))))
    if kind == "InteractiveViewer":
        return ft.InteractiveViewer(content=ft.Text(str(p.get("content", "Zoomable content"))))
    if kind == "GestureDetector":
        return ft.GestureDetector(content=ft.Text(str(p.get("content", "Gesture target"))))
    if kind == "PageView":
        pages = _text_items(p.get("items", [])) or [ft.Text("Page one")]
        return ft.PageView(controls=pages, height=160)
    if kind == "Markdown":
        return ft.Markdown(value=str(p.get("value", "")))
    if kind == "DataTable":
        columns = [ft.DataColumn(label=ft.Text(str(name))) for name in p.get("columns", [])]
        rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(cell))) for cell in row]) for row in p.get("rows", [])]
        return ft.DataTable(columns=columns, rows=rows)
    return ft.Text(f"Unsupported widget: {kind}")


def _text_items(items):
    if not isinstance(items, list):
        return []
    return [ft.Text(str(item)) for item in items]


def _text_list_source(items):
    if not isinstance(items, list):
        items = []
    return "[" + ", ".join(f"ft.Text({str(item)!r})" for item in items) + "]"


def widget_expression(kind, props, child_expressions=None, on_click=False):
    """Return a Python expression constructing a catalog widget."""
    p = props
    click_arg = ", on_click=button_clicked" if on_click else ""
    if kind == "Text":
        return f"ft.Text(value={str(p.get('value', 'Text'))!r}, size={p.get('size', 20)!r})"
    if kind in _TEXT_BUTTONS:
        return f"ft.{kind}(content=ft.Text({str(p.get('content', kind))!r}){click_arg})"
    if kind == "FloatingActionButton":
        return f"ft.FloatingActionButton(content=ft.Text({str(p.get('content', 'Add'))!r}){click_arg})"
    if kind == "IconButton":
        icon_name = str(p.get("icon", "STAR"))
        if not hasattr(ft.Icons, icon_name):
            icon_name = "STAR"
        return f"ft.IconButton(icon=ft.Icons.{icon_name}{click_arg})"
    if kind == "TextField":
        return f"ft.TextField(value={str(p.get('value', ''))!r}, label={p.get('label', '')!r}, hint_text={p.get('hint_text', '')!r}, password={p.get('password', False)!r}{click_arg})"
    if kind in {"Checkbox", "Switch"}:
        return f"ft.{kind}(label={p.get('label', kind)!r}, value={p.get('value', False)!r})"
    if kind == "Radio":
        return f"ft.Radio(label={p.get('label', 'Option')!r}, value={str(p.get('value', 'option1'))!r})"
    if kind == "Dropdown":
        options = ", ".join(f"ft.DropdownOption(text={str(item)!r})" for item in p.get("options", []))
        return f"ft.Dropdown(label={p.get('label', 'Choose one')!r}, value={p.get('value', 'One')!r}, options=[{options}])"
    if kind in {"Slider", "RangeSlider"}:
        props_to_emit = [f"{key}={p.get(key)!r}" for key in (("value", "min", "max") if kind == "Slider" else ("start_value", "end_value", "min", "max"))]
        return f"ft.{kind}({', '.join(props_to_emit)})"
    if kind in {"ProgressBar", "ProgressRing"}:
        return f"ft.{kind}(value={p.get('value', 0.5)!r})"
    if kind == "Icon":
        icon_name = str(p.get("icon", "STAR"))
        if not hasattr(ft.Icons, icon_name):
            icon_name = "STAR"
        return f"ft.Icon(icon=ft.Icons.{icon_name}, size={p.get('size', 32)!r})"
    if kind == "Image":
        return f"ft.Image(src={str(p.get('src', ''))!r}, width=240, height=100, fit=ft.BoxFit.CONTAIN)"
    if kind == "Container":
        child = f"ft.Text({str(p.get('content', 'Container content'))!r})"
        items = p.get("items", [])
        extra = (
            "[" + ", ".join(child_expressions) + "]"
            if child_expressions is not None
            else _text_list_source(items)
        )
        return f"ft.Container(content=ft.Column(controls=[{child}, *{extra}]){click_arg})"
    if kind in _LAYOUTS:
        items = (
            "[" + ", ".join(child_expressions) + "]"
            if child_expressions is not None
            else _text_list_source(p.get("items", []))
        )
        if kind in {"Stack", "GridView"}:
            if child_expressions is not None:
                items = "[" + ", ".join(
                    f"ft.Container(content={control})" for control in child_expressions
                ) + "]"
            else:
                items = f"[ft.Container(content=control) for control in {items}]"
        if kind == "GridView":
            return f"ft.GridView(controls={items}, max_extent=100, height=160)"
        if kind == "ListView":
            return f"ft.ListView(controls={items}, height=150)"
        return f"ft.{kind}(controls={items})"
    if kind == "SafeArea":
        return f"ft.SafeArea(content=ft.Text({str(p.get('content', 'Safe area content'))!r}))"
    if kind == "Card":
        return f"ft.Card(content=ft.Container(content=ft.Text({str(p.get('content', 'Card content'))!r}), padding=12))"
    if kind == "ListTile":
        return f"ft.ListTile(title=ft.Text({str(p.get('title', 'List item'))!r}), subtitle=ft.Text({str(p.get('subtitle', 'Description'))!r}){click_arg})"
    if kind == "ExpansionTile":
        return f"ft.ExpansionTile(title=ft.Text({p.get('title', 'More details')!r}), subtitle=ft.Text({p.get('subtitle', '')!r}), controls={_text_list_source(p.get('items', []))})"
    if kind in {"Divider", "VerticalDivider"}:
        return f"ft.{kind}()"
    if kind == "Placeholder":
        return "ft.Placeholder(width=120, height=60)"
    if kind == "CircleAvatar":
        return f"ft.CircleAvatar(content=ft.Text({str(p.get('content', 'F'))!r}))"
    if kind == "Chip":
        return f"ft.Chip(label={str(p.get('label', 'Tag'))!r}{click_arg})"
    if kind == "AppBar":
        return f"ft.AppBar(title=ft.Text({str(p.get('title', 'App title'))!r}))"
    if kind == "SelectionArea":
        return f"ft.SelectionArea(content=ft.Text({str(p.get('content', 'Selectable text'))!r}))"
    if kind == "AnimatedSwitcher":
        return f"ft.AnimatedSwitcher(content=ft.Text({str(p.get('content', 'Switchable content'))!r}))"
    if kind == "InteractiveViewer":
        return f"ft.InteractiveViewer(content=ft.Text({str(p.get('content', 'Zoomable content'))!r}))"
    if kind == "GestureDetector":
        return f"ft.GestureDetector(content=ft.Text({str(p.get('content', 'Gesture target'))!r}))"
    if kind == "PageView":
        return f"ft.PageView(controls={_text_list_source(p.get('items', []))}, height=160)"
    if kind == "Markdown":
        return f"ft.Markdown(value={str(p.get('value', ''))!r})"
    if kind == "DataTable":
        columns = ", ".join(f"ft.DataColumn(label=ft.Text({str(col)!r}))" for col in p.get("columns", []))
        rows = []
        for row in p.get("rows", []):
            cells = ", ".join(f"ft.DataCell(ft.Text({str(cell)!r}))" for cell in row)
            rows.append(f"ft.DataRow(cells=[{cells}])")
        return f"ft.DataTable(columns=[{columns}], rows=[{', '.join(rows)}])"
    return f"ft.Text({f'Unsupported widget: {kind}'!r})"
