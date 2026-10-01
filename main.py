import ast
import copy
import json
import uuid

import flet as ft

from widget_catalog import (
    CLICK_WIDGETS,
    WIDGETS,
    apply_widget_properties,
    make_control,
    normalize_props,
    property_label,
    widget_expression,
)


WIDGET_ICONS = {
    "Text": "TEXT_FIELDS",
    "Button": "TOUCH_APP",
    "FilledButton": "CHECK_BOX",
    "FilledTonalButton": "SMART_BUTTON",
    "OutlinedButton": "SMART_BUTTON",
    "TextButton": "TEXT_FIELDS",
    "FloatingActionButton": "ADD_CIRCLE_OUTLINE",
    "IconButton": "STAR",
    "TextField": "TEXT_FIELDS",
    "Checkbox": "CHECK_BOX",
    "Switch": "TOGGLE_ON",
    "Radio": "RADIO_BUTTON_UNCHECKED",
    "Dropdown": "ARROW_DROP_DOWN",
    "Slider": "TUNE",
    "RangeSlider": "TUNE",
    "ProgressBar": "INCOMPLETE_CIRCLE",
    "ProgressRing": "DONUT_LARGE",
    "Icon": "STAR",
    "Image": "IMAGE",
    "Container": "INVENTORY_2",
    "Row": "VIEW_COLUMN",
    "Column": "VIEW_AGENDA",
    "Stack": "LAYERS",
    "ListView": "LIST",
    "GridView": "GRID_VIEW",
    "ResponsiveRow": "VIEW_COMFY",
    "SafeArea": "SHIELD",
    "Card": "CREDIT_CARD",
    "ListTile": "LIST_ALT",
    "ExpansionTile": "EXPAND_MORE",
    "Divider": "HORIZONTAL_RULE",
    "VerticalDivider": "BORDER_VERTICAL",
    "Placeholder": "SQUARE",
    "CircleAvatar": "ACCOUNT_CIRCLE",
    "Chip": "LABEL",
    "AppBar": "MENU",
    "SelectionArea": "HIGHLIGHT_ALT",
    "AnimatedSwitcher": "ANIMATION",
    "InteractiveViewer": "ZOOM_IN",
    "GestureDetector": "GESTURE",
    "PageView": "PAGES",
    "Markdown": "FORMAT_LIST_BULLETED",
    "DataTable": "TABLE_VIEW",
}


def main(page: ft.Page):
    page.title = "Flet Visual Builder"
    page.padding = 12

    nodes = [
        {"id": uuid.uuid4().hex, "type": "Text", "props": {"value": "Welcome", "size": 28}, "children": []},
        {"id": uuid.uuid4().hex, "type": "TextField", "props": {"label": "Username", "hint_text": "Enter your username"}, "children": []},
        {"id": uuid.uuid4().hex, "type": "TextField", "props": {"label": "Password", "hint_text": "", "password": True}, "children": []},
        {"id": uuid.uuid4().hex, "type": "Button", "props": {"content": "Login"}, "children": []},
    ]
    nodes = [
        {"id": node["id"], "type": node["type"], "props": normalize_props(node["type"], node["props"]), "children": []}
        for node in nodes
    ]
    selected = [nodes[0]["id"]]
    dragging = [None]
    active_tab = ["Design"]
    safe_area_enabled = [False]
    executed_preview = [None]
    theme_seed = [None]
    dark_theme_seed = [None]
    undo_stack = []
    redo_stack = []
    canvas = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=8)
    palette = ft.Column(spacing=4)
    properties = ft.Column(spacing=8)
    toolbar = ft.Row(spacing=8)
    body = ft.Row(expand=True, spacing=12)
    clipboard = ft.Clipboard()
    picker = ft.FilePicker()

    def snapshot():
        executed_preview[0] = None
        undo_stack.append(copy.deepcopy(nodes))
        if len(undo_stack) > 30:
            undo_stack.pop(0)
        redo_stack.clear()

    def notify(message):
        page.show_dialog(ft.SnackBar(content=ft.Text(message)))

    def toggle_safe_area(event):
        safe_area_enabled[0] = bool(event.control.value)
        executed_preview[0] = None
        rebuild()

    def select_theme(is_dark, event):
        selected_seed = event.control.value
        value = None if not selected_seed or selected_seed.lower() == "none" else selected_seed
        state = dark_theme_seed if is_dark else theme_seed
        state[0] = value
        theme = ft.Theme(
            color_scheme_seed=getattr(ft.Colors, value) if value else None
        ) if value else None
        if is_dark:
            page.dark_theme = theme
        else:
            page.theme = theme
        rebuild()

    container_types = {"Container", "Row", "Column", "Stack", "ListView", "GridView", "ResponsiveRow"}

    def all_nodes(items=None):
        for node in nodes if items is None else items:
            yield node
            yield from all_nodes(node.get("children", []))

    def find_node(node_id):
        return next((node for node in all_nodes() if node["id"] == node_id), None)

    def find_parent_list(node_id, items=None):
        current = nodes if items is None else items
        for node in current:
            if node["id"] == node_id:
                return current
            found = find_parent_list(node_id, node.get("children", []))
            if found is not None:
                return found
        return None

    def new_node(kind):
        return {"id": uuid.uuid4().hex, "type": kind, "props": normalize_props(kind, copy.deepcopy(WIDGETS[kind])), "children": []}

    def add_widget(kind):
        snapshot()
        node = new_node(kind)
        nodes.append(node)
        selected[0] = node["id"]
        rebuild()

    def delete_selected(_=None):
        parent = find_parent_list(selected[0])
        if parent is None:
            return
        snapshot()
        index = next(i for i, node in enumerate(parent) if node["id"] == selected[0])
        parent.pop(index)
        selected[0] = parent[min(index, len(parent) - 1)]["id"] if parent else (nodes[0]["id"] if nodes else None)
        rebuild()

    def move_selected(delta):
        parent = find_parent_list(selected[0])
        if parent is None:
            return
        i = next(i for i, node in enumerate(parent) if node["id"] == selected[0])
        j = i + delta
        if 0 <= j < len(parent):
            snapshot()
            parent[i], parent[j] = parent[j], parent[i]
            rebuild()

    def undo(_=None):
        if undo_stack:
            redo_stack.append(copy.deepcopy(nodes))
            nodes[:] = undo_stack.pop()
            if find_node(selected[0]) is None:
                selected[0] = nodes[0]["id"] if nodes else None
            rebuild()

    def redo(_=None):
        if redo_stack:
            undo_stack.append(copy.deepcopy(nodes))
            nodes[:] = redo_stack.pop()
            if find_node(selected[0]) is None:
                selected[0] = nodes[0]["id"] if nodes else None
            rebuild()

    def ordered_nodes(items):
        return list(enumerate(items))

    def render_node(node):
        children = [render_node(child) for _, child in ordered_nodes(node.get("children", []))]
        control = make_control(node["type"], node["props"], children if node["type"] in container_types else None)
        return apply_widget_properties(control, node["type"], node["props"])

    def accept_drop(target_id, event):
        payload = event.src.data if event.src is not None else None
        if not isinstance(payload, str):
            return
        if payload.startswith("kind:"):
            kind = payload[5:]
            if kind not in WIDGETS:
                return
            target = find_node(target_id) if target_id else None
            if target_id and (target is None or target["type"] not in container_types):
                return
            snapshot()
            node = new_node(kind)
            if target is not None:
                target["children"].append(node)
            else:
                nodes.append(node)
            selected[0] = node["id"]
            rebuild()
            return
        if not payload.startswith("node:"):
            return
        source_id = payload[5:]
        source = find_node(source_id)
        target = find_node(target_id) if target_id else None
        if source is None or source is target:
            return
        if target and any(item["id"] == source_id for item in _descendants(target)):
            return
        source_list = find_parent_list(source_id)
        snapshot()
        source_list.remove(source)
        if target is None:
            nodes.append(source)
        elif target["type"] in container_types:
            target["children"].append(source)
        else:
            destination = find_parent_list(target_id)
            destination.insert(next(i for i, item in enumerate(destination) if item["id"] == target_id), source)
        selected[0] = source_id
        rebuild()

    def _descendants(node):
        for child in node.get("children", []):
            yield child
            yield from _descendants(child)

    def build_properties():
        properties.controls.clear()
        node = find_node(selected[0])
        if node is None:
            properties.controls.append(ft.Text("Select a widget to edit its properties."))
            return
        properties.controls.append(ft.Text(f"Properties · {node['type']}"))

        def set_prop(key, value):
            current = node["props"].get(key)
            if current == value:
                return
            snapshot()
            node["props"][key] = value
            rebuild()

        alignment_options = {
            "horizontal_alignment": ["Left", "Center", "Right"],
            "vertical_alignment": ["Top", "Center", "Bottom"],
        }
        for key, value in node["props"].items():
            label = property_label(node["type"], key)
            if key in alignment_options:
                dropdown = ft.Dropdown(
                    label=label,
                    value=value,
                    options=[ft.DropdownOption(text=option) for option in alignment_options[key]],
                    on_select=lambda e, k=key: set_prop(k, e.control.value),
                )
                properties.controls.append(dropdown)
            elif isinstance(value, bool):
                toggle = ft.Switch(label=label, value=value)
                toggle.on_change = lambda e, k=key: set_prop(k, e.control.value)
                properties.controls.append(toggle)
            else:
                if isinstance(value, (list, dict)):
                    field_value = json.dumps(value)
                elif value is None:
                    field_value = ""
                else:
                    field_value = str(value)
                field = ft.TextField(label=label, value=field_value)
                if key in {"color", "bgcolor"}:
                    field.hint_text = "#RRGGBB or a Flet Colors name"
                elif key in {"width", "height"}:
                    field.hint_text = "Automatic" if value is None else ""
                def commit(e, k=key, old=value):
                    raw_value = e.control.value
                    stripped_value = raw_value.strip()
                    new_value = raw_value
                    if k in {"color", "bgcolor"}:
                        new_value = stripped_value or None
                        if new_value:
                            is_hex = new_value.startswith("#") and len(new_value) in {4, 5, 7, 9} and all(ch in "0123456789abcdefABCDEF" for ch in new_value[1:])
                            color_name = new_value.upper()
                            if not is_hex and not hasattr(ft.Colors, color_name):
                                e.control.value = "" if old is None else str(old)
                                e.control.update()
                                notify("Use a hex color (for example #336699) or a Flet Colors name.")
                                return
                            if not is_hex:
                                new_value = color_name
                    elif k in {"width", "height"}:
                        try:
                            new_value = float(stripped_value) if stripped_value else None
                        except ValueError:
                            e.control.value = "" if old is None else str(old)
                            e.control.update()
                            return
                    elif isinstance(old, (list, dict)):
                        try:
                            new_value = json.loads(stripped_value)
                            if not isinstance(new_value, type(old)):
                                raise ValueError("Use the same JSON data type")
                        except (ValueError, json.JSONDecodeError):
                            e.control.value = json.dumps(old)
                            e.control.update()
                            return
                    elif isinstance(old, (int, float)) and not isinstance(old, bool):
                        try:
                            new_value = float(stripped_value) if isinstance(old, float) else int(stripped_value)
                        except ValueError:
                            e.control.value = str(old)
                            e.control.update()
                            return
                    if k == "size" and new_value <= 0:
                        e.control.value = str(old)
                        e.control.update()
                        return
                    if k in {"width", "height"} and new_value is not None and new_value < 0:
                        e.control.value = "" if old is None else str(old)
                        e.control.update()
                        return
                    if k == "opacity" and not 0 <= new_value <= 1:
                        e.control.value = str(old)
                        e.control.update()
                        return
                    set_prop(k, new_value)
                field.on_submit = commit
                properties.controls.append(field)
        properties.controls.append(ft.Text("Enter applies a value. Blank colors inherit the theme; blank width/height use defaults."))

    def canvas_node(node):
        child_controls = [canvas_node(child) for _, child in ordered_nodes(node.get("children", []))]
        inner = make_control(node["type"], node["props"], child_controls if node["type"] in container_types else None)
        inner = apply_widget_properties(inner, node["type"], node["props"])
        card = ft.Container(
            content=inner,
            padding=8,
            border=ft.Border.all(1, ft.Colors.BLUE if node["id"] == selected[0] else ft.Colors.OUTLINE),
            on_click=lambda e, node_id=node["id"]: select_node(node_id),
        )
        draggable = ft.Draggable(group="builder-widgets", data=f"node:{node['id']}", content=card)
        return ft.DragTarget(
            group="builder-widgets",
            content=draggable,
            on_accept=lambda e, target_id=node["id"]: accept_drop(target_id, e),
        )

    def refresh_canvas():
        canvas.controls.clear()
        canvas_content = ft.Container(
            content=ft.Column(
                controls=[canvas_node(node) for _, node in ordered_nodes(nodes)]
            )
        )
        if safe_area_enabled[0]:
            canvas_content = ft.SafeArea(content=canvas_content)
        canvas.controls.append(ft.DragTarget(
            group="builder-widgets",
            content=canvas_content,
            on_accept=lambda e: accept_drop(None, e),
        ))

    def select_node(node_id):
        selected[0] = node_id
        rebuild()

    def source_code():
        theme_setup_lines = []
        if theme_seed[0]:
            theme_setup_lines.append(
                f"    page.theme = ft.Theme(color_scheme_seed=ft.Colors.{theme_seed[0]})"
            )
        if dark_theme_seed[0]:
            theme_setup_lines.append(
                f"    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.{dark_theme_seed[0]})"
            )
        lines = [
            "import flet as ft",
            "",
            "def _apply_widget_properties(control, props):",
            "    for name in ('visible', 'disabled', 'opacity', 'tooltip', 'autofocus', 'can_request_focus'):",
            "        value = props.get(name)",
            "        if value is not None and hasattr(control, name):",
            "            setattr(control, name, value)",
            "    color = props.get('color')",
            "    bgcolor = props.get('bgcolor')",
            "    if isinstance(color, str): color = getattr(ft.Colors, color.upper(), color)",
            "    if isinstance(bgcolor, str): bgcolor = getattr(ft.Colors, bgcolor.upper(), bgcolor)",
            "    size = props.get('size')",
            "    if color:",
            "        for name in ('color', 'active_color', 'icon_color'):",
            "            if hasattr(control, name):",
            "                setattr(control, name, color)",
            "                break",
            "    if size is not None:",
            "        if hasattr(control, 'size'):",
            "            control.size = size",
            "        if hasattr(control, 'text_size'):",
            "            control.text_size = size",
            "    styles = {}",
            "    if size is not None: styles['size'] = size",
            "    if color: styles['color'] = color",
            "    if styles:",
            "        style = ft.TextStyle(**styles)",
            "        for name in ('label_style', 'label_text_style', 'title_text_style', 'subtitle_text_style', 'data_text_style'):",
            "            if hasattr(control, name): setattr(control, name, style)",
            "        _style_text(control, size, color)",
            "    if bgcolor:",
            "        if hasattr(control, 'bgcolor'): control.bgcolor = bgcolor",
            "        else: control = ft.Container(content=control, bgcolor=bgcolor)",
            "    horizontal = {'Left': -1, 'Center': 0, 'Right': 1}.get(props.get('horizontal_alignment', 'Left'), -1)",
            "    vertical = {'Top': -1, 'Center': 0, 'Bottom': 1}.get(props.get('vertical_alignment', 'Top'), -1)",
            "    if horizontal == -1 and vertical == -1 and props.get('width') is None and props.get('height') is None and not props.get('expand', False):",
            "        return control",
            "    return ft.Container(content=control, alignment=ft.Alignment(x=horizontal, y=vertical), width=props.get('width'), height=props.get('height'), expand=bool(props.get('expand', False)))",
            "",
            "def _style_text(control, size, color):",
            "    if isinstance(control, ft.Text):",
            "        if size is not None: control.size = size",
            "        if color: control.color = color",
            "    for name in ('content', 'title', 'subtitle', 'controls', 'cells'):",
            "        child = getattr(control, name, None)",
            "        items = child if isinstance(child, list) else [child]",
            "        for item in items:",
            "            if isinstance(item, ft.Control): _style_text(item, size, color)",
            "            elif hasattr(item, 'content') and isinstance(item.content, ft.Control): _style_text(item.content, size, color)",
            "",
            "def main(page: ft.Page):",
            "    page.title = 'My Flet App'",
            *theme_setup_lines,
            "    page.add(",
        ]
        def code_for_node(node):
            child_codes = [code_for_node(child) for _, child in ordered_nodes(node.get("children", []))]
            props = node["props"]
            common = {key: props.get(key) for key in (
                "size", "color", "bgcolor", "visible", "disabled", "opacity",
                "tooltip", "width", "height", "expand", "autofocus", "can_request_focus",
                "horizontal_alignment", "vertical_alignment",
            )}
            widget = widget_expression(
                node["type"], props,
                child_codes if node["type"] in container_types else None,
            )
            return f"_apply_widget_properties({widget}, {common!r})"

        root_expressions = [
            code_for_node(node) for _, node in ordered_nodes(nodes)
        ]
        if safe_area_enabled[0]:
            lines.extend([
                "        ft.SafeArea(",
                "            content=ft.Column(",
                "                controls=[",
            ])
            lines.extend(f"                    {expression}," for expression in root_expressions)
            lines.extend(["                ],", "            ),", "        ),"])
        else:
            lines.extend(f"        {expression}," for expression in root_expressions)
        lines.extend(["    )", "", "ft.run(main)"])
        return "\n".join(lines)

    def beautify_expression(expression, indent=4):
        expression_node = ast.parse(expression, mode="eval").body

        def format_node(node, level):
            pad = " " * level
            if isinstance(node, ast.Call) and (node.args or node.keywords):
                entries = [format_node(argument, level + 4) for argument in node.args]
                entries.extend(
                    f"{keyword.arg}={format_node(keyword.value, level + 4)}"
                    for keyword in node.keywords
                )
                body = ",\n".join(" " * (level + 4) + entry for entry in entries)
                return f"{ast.unparse(node.func)}(\n{body},\n{pad})"
            if isinstance(node, (ast.List, ast.Tuple)) and node.elts:
                entries = [format_node(item, level + 4) for item in node.elts]
                opening, closing = ("[", "]") if isinstance(node, ast.List) else ("(", ")")
                body = ",\n".join(" " * (level + 4) + entry for entry in entries)
                return f"{opening}\n{body},\n{pad}{closing}"
            return ast.unparse(node)

        return format_node(expression_node, indent)

    def object_code():
        declarations = []
        roots = []
        sequence = [0]

        def declare_node(node):
            child_names = [
                declare_node(child)
                for _, child in ordered_nodes(node.get("children", []))
            ]
            sequence[0] += 1
            variable = f"{node['type'].lower()}_{sequence[0]}"
            expression = widget_expression(
                node["type"],
                node["props"],
                child_names if node["type"] in container_types else None,
                on_click=node["type"] in CLICK_WIDGETS,
            )
            declarations.append((variable, node, expression))
            return variable

        for _, root in ordered_nodes(nodes):
            roots.append(declare_node(root))

        lines = [
            "import flet as ft",
            "",
            "",
            "def button_clicked(e):",
            "    pass",
            "",
            "",
            "def main(page: ft.Page):",
            "    page.title = 'My Flet App'",
        ]
        if theme_seed[0]:
            lines.append(
                f"    page.theme = ft.Theme(color_scheme_seed=ft.Colors.{theme_seed[0]})"
            )
        if dark_theme_seed[0]:
            lines.append(
                f"    page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.{dark_theme_seed[0]})"
            )

        for variable, node, expression in declarations:
            lines.append("")
            lines.append(f"    {variable} = {beautify_expression(expression)}")
            props = node["props"]
            probe = make_control(node["type"], props, [])
            for key in (
                "visible", "disabled", "opacity", "tooltip",
                "autofocus", "can_request_focus",
            ):
                value = props.get(key)
                if value is not None and hasattr(probe, key):
                    lines.append(f"    {variable}.{key} = {value!r}")

            size = props.get("size")
            if size is not None:
                size_target = "size" if hasattr(probe, "size") else "text_size"
                if hasattr(probe, size_target):
                    lines.append(f"    {variable}.{size_target} = {size!r}")

            color = props.get("color")
            if color:
                color_target = next(
                    (name for name in ("color", "active_color", "icon_color") if hasattr(probe, name)),
                    None,
                )
                if color_target:
                    color_value = (
                        f"ft.Colors.{color.upper()}"
                        if isinstance(color, str) and hasattr(ft.Colors, color.upper())
                        else repr(color)
                    )
                    lines.append(f"    {variable}.{color_target} = {color_value}")

            bgcolor = props.get("bgcolor")
            if bgcolor:
                bgcolor_value = (
                    f"ft.Colors.{bgcolor.upper()}"
                    if isinstance(bgcolor, str) and hasattr(ft.Colors, bgcolor.upper())
                    else repr(bgcolor)
                )
                if hasattr(probe, "bgcolor"):
                    lines.append(f"    {variable}.bgcolor = {bgcolor_value}")
                else:
                    lines.append(
                        f"    {variable} = ft.Container(content={variable}, bgcolor={bgcolor_value})"
                    )

            horizontal = {"Left": -1, "Center": 0, "Right": 1}.get(
                props.get("horizontal_alignment", "Left"), -1
            )
            vertical = {"Top": -1, "Center": 0, "Bottom": 1}.get(
                props.get("vertical_alignment", "Top"), -1
            )
            if (
                horizontal != -1
                or vertical != -1
                or props.get("width") is not None
                or props.get("height") is not None
                or props.get("expand", False)
            ):
                aligned_expression = (
                    f"ft.Container(content={variable}, "
                    f"alignment=ft.Alignment(x={horizontal}, y={vertical}), "
                    f"width={props.get('width')!r}, height={props.get('height')!r}, "
                    f"expand={bool(props.get('expand', False))!r})"
                )
                lines.append(
                    f"    {variable} = {beautify_expression(aligned_expression)}"
                )

        if safe_area_enabled[0] and roots:
            sequence[0] += 1
            safe_area_variable = f"safe_area_{sequence[0]}"
            safe_expression = (
                "ft.SafeArea(content=ft.Column(controls=["
                + ", ".join(roots)
                + "]))"
            )
            lines.append("")
            lines.append(
                f"    {safe_area_variable} = {beautify_expression(safe_expression)}"
            )
            roots = [safe_area_variable]

        if roots:
            lines.extend(["", "    page.add("])
            lines.extend(f"        {variable}," for variable in roots)
            lines.append("    )")
        else:
            lines.append("    pass")
        lines.extend(["", "", "ft.run(main)"])
        return "\n".join(lines)

    def show_tab(tab):
        active_tab[0] = tab
        rebuild()

    async def save_project(_=None):
        data = json.dumps(
            {
                "format": 1,
                "widgets": nodes,
                "safe_area": safe_area_enabled[0],
                "theme_seed": theme_seed[0],
                "dark_theme_seed": dark_theme_seed[0],
            },
            indent=2,
        ).encode("utf-8")
        path = await picker.save_file(dialog_title="Save Visual Flet Builder project", file_name="project.fvb.json", src_bytes=data, allowed_extensions=["json"])
        if path:
            notify("Project saved")

    async def export_python(_=None):
        code = source_code().encode("utf-8")
        path = await picker.save_file(
            dialog_title="Export Flet Python app from Code",
            file_name="app.py",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["py"],
            src_bytes=code,
        )
        if path:
            notify("Flet Python file exported")
    async def export_python2(_=None):
        code = source_code().encode("utf-8")
        path = await picker.save_file(
            dialog_title="Export Flet Python app from CodeE",
            file_name="app.py",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["py"],
            src_bytes=code,
        )
        if path:
            notify("Flet Python file exported")
    async def export_object_code(_=None):
        code = object_code().encode("utf-8")
        path = await picker.save_file(
            dialog_title="Export object-based Flet Python app",
            file_name="app_objects.py",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["py"],
            src_bytes=code,
        )
        if path:
            notify("Object-based Flet Python file exported")

    async def copy_object_code(_=None):
        await clipboard.set(object_code())
        notify("Object-based Flet code copied")

    def run_object_code():
        class PreviewPage:
            def __init__(self):
                self.controls = []
                self.title = ""
                self.theme = None
                self.dark_theme = None

            def add(self, *controls):
                self.controls.extend(controls)

        source = object_code()
        run_line = "\nft.run(main)"
        if not source.endswith(run_line):
            notify("Could not run CodeE: generated entry point was not found.")
            return
        try:
            namespace = {"ft": ft}
            exec(compile(source[:-len(run_line)], "<CodeE>", "exec"), namespace)
            preview_page = PreviewPage()
            namespace["main"](preview_page)
            executed_preview[0] = preview_page.controls
            active_tab[0] = "Preview"
            rebuild()
        except Exception as ex:
            notify(f"Could not run CodeE: {ex}")

    async def load_project(_=None):
        files = await picker.pick_files(dialog_title="Open project", allowed_extensions=["json"], with_data=True)
        if not files:
            return
        try:
            payload = json.loads(files[0].bytes.decode("utf-8"))
            loaded = payload.get("widgets", [])
            if not isinstance(loaded, list):
                raise ValueError("Unsupported project contents")

            def migrate_node(item):
                kind = item.get("type")
                if kind not in WIDGETS:
                    raise ValueError("Unsupported project contents")
                return {
                    "id": item.get("id") or uuid.uuid4().hex,
                    "type": kind,
                    "props": normalize_props(kind, item.get("props", {})),
                    "children": [migrate_node(child) for child in item.get("children", [])],
                }

            migrated = [migrate_node(item) for item in loaded]
            snapshot()
            nodes[:] = migrated
            safe_area_enabled[0] = bool(payload.get("safe_area", False))
            theme_seed[0] = payload.get("theme_seed")
            dark_theme_seed[0] = payload.get("dark_theme_seed")
            page.theme = (
                ft.Theme(color_scheme_seed=getattr(ft.Colors, theme_seed[0]))
                if theme_seed[0]
                else None
            )
            page.dark_theme = (
                ft.Theme(color_scheme_seed=getattr(ft.Colors, dark_theme_seed[0]))
                if dark_theme_seed[0]
                else None
            )
            selected[0] = nodes[0]["id"] if nodes else None
            rebuild()
            notify("Project loaded")
        except (ValueError, TypeError, KeyError, AttributeError) as ex:
            notify(f"Could not load project: {ex}")

    async def copy_code(_=None):
        await clipboard.set(source_code())
        notify("Generated code copied")

    def rebuild():
        toolbar.controls = [
            ft.Text("Visual Flet Builder"),
            ft.Button(content=ft.Text("Undo"), on_click=undo, disabled=not undo_stack),
            ft.Button(content=ft.Text("Redo"), on_click=redo, disabled=not redo_stack),
            ft.Button(content=ft.Text("Save project"), on_click=save_project),
            ft.Button(content=ft.Text("Exp Code"), on_click=export_python),
            ft.Button(content=ft.Text("Exp Python"), on_click=export_object_code),            
            ft.Button(content=ft.Text("Open"), on_click=load_project),
            ft.Container(expand=True),
            *[ft.TextButton(content=ft.Text(tab), on_click=lambda e, t=tab: show_tab(t)) for tab in ("Design", "Preview", "CodeE", "Code")],
        ]
        if active_tab[0] == "Design":
            palette.controls = [
                ft.Text("Widgets"),
                ft.Text(
                    "Drag widgets onto the canvas or into a container. "
                    "Drag canvas widgets to rearrange or nest."
                ),
            ]
            widget_tiles = []
            for kind in WIDGETS:
                icon_name = WIDGET_ICONS.get(kind, "WIDGETS")
                tile = ft.Draggable(
                    group="builder-widgets",
                    data=f"kind:{kind}",
                    content=ft.Container(
                        width=82,
                        content=ft.Column(
                            tight=True,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.IconButton(
                                    icon=getattr(ft.Icons, icon_name),
                                    icon_size=18,
                                    tooltip=kind,
                                    on_click=lambda e, k=kind: add_widget(k),
                                ),
                                ft.Text(kind, size=8, text_align=ft.TextAlign.CENTER),
                            ],
                        ),
                    ),
                )
                widget_tiles.append(tile)
            for index in range(0, len(widget_tiles), 2):
                palette.controls.append(
                    ft.Row(
                        spacing=0,
                        controls=widget_tiles[index:index + 2],
                    )
                )
            refresh_canvas()
            build_properties()
            color_names = sorted(ft.Colors.__members__)

            def make_theme_options():
                return [
                    ft.DropdownOption(text="none"),
                    *[ft.DropdownOption(text=name) for name in color_names],
                ]

            middle = ft.Column(expand=True, controls=[
                ft.Row(controls=[
                    ft.Text("Canvas"),
                    ft.Button(content=ft.Text("Move up"), on_click=lambda e: move_selected(-1)),
                    ft.Button(content=ft.Text("Move down"), on_click=lambda e: move_selected(1)),
                    ft.Button(content=ft.Text("Delete"), on_click=delete_selected),
                    ft.Checkbox(
                        label="Wrap in SafeArea",
                        value=safe_area_enabled[0],
                        on_change=toggle_safe_area,
                    ),
                ]),
                ft.Row(
                    controls=[
                        ft.Dropdown(
                            label="Theme",
                            value=theme_seed[0] or "none",
                            options=make_theme_options(),
                            enable_search=True,
                            menu_height=360,
                            expand=True,
                            on_select=lambda e: select_theme(False, e),
                        ),
                        ft.Dropdown(
                            label="Dark theme",
                            value=dark_theme_seed[0] or "none",
                            options=make_theme_options(),
                            enable_search=True,
                            menu_height=360,
                            expand=True,
                            on_select=lambda e: select_theme(True, e),
                        ),
                    ],
                ),
                canvas,
            ])
            body.controls = [
                ft.Column(width=190, scroll=ft.ScrollMode.AUTO, controls=[palette]),
                middle,
                ft.Column(width=240, scroll=ft.ScrollMode.AUTO, controls=[properties]),
            ]
            body.controls[1].expand = True
        elif active_tab[0] == "Preview":
            preview_controls = (
                executed_preview[0]
                if executed_preview[0] is not None
                else [render_node(node) for _, node in ordered_nodes(nodes)]
            )
            preview_content = ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=preview_controls,
            )
            if safe_area_enabled[0] and executed_preview[0] is None:
                preview_content = ft.SafeArea(content=preview_content)
            body.controls = [preview_content]
        elif active_tab[0] == "CodeE":
            body.controls = [
                ft.Column(expand=True, controls=[
                    ft.Row(controls=[
                        ft.Text("Object-based Flet code"),
                        ft.Button(content=ft.Text("Run in Studio"), on_click=run_object_code),
                        ft.Button(content=ft.Text("Copy code"), on_click=copy_object_code),
                        ft.Button(content=ft.Text("Export Python"), on_click=export_object_code),
                    ]),
                    ft.Text(object_code(), selectable=True),
                ], scroll=ft.ScrollMode.AUTO)
            ]
        else:
            body.controls = [
                ft.Column(expand=True, controls=[
                    ft.Row(controls=[ft.Text("Generated Flet code"), ft.Button(content=ft.Text("Copy code"), on_click=copy_code)]),
                    ft.Text(source_code(), selectable=True),
                ], scroll=ft.ScrollMode.AUTO)
            ]
        page.controls.clear()
        page.add(ft.Column(expand=True, controls=[toolbar, body]))
        page.update()

    rebuild()


if __name__ == "__main__":
    ft.run(main)
