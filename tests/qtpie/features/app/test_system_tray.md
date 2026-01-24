# System Tray Feature Documentation

System tray allows apps to show an icon in the system notification area with an optional context menu.

## Enabling System Tray

Use `system_tray=True` in the `@app` decorator to enable the system tray.

```python
@app(system_tray=True)
class MyApp(AppBase):
    show: QAction = new("Show Window")
```

## System Tray with Explicit Menu

Define a `TrayMenu` class using `@menu` decorator and assign it to a `system_tray` field.

```python
@menu(text="Tray")
class TrayMenu(Menu):
    show: QAction = new("Show")
    quit: QAction = new("Quit")

@app(system_tray=True)
class MyApp(AppBase):
    system_tray: TrayMenu = new()
```

The field can also use underscore prefix (`_system_tray`).

## Auto-Created Tray Menu from QAction Fields

When QAction fields are defined directly on the app (without a separate Menu class), they are automatically added to an auto-created tray context menu.

```python
@app(system_tray=True)
class MyApp(AppBase):
    show: QAction = new("Show Window")
    quit: QAction = new("Quit")
```

## Separators in Tray Menu

Use `Separator` type annotation to add visual separators between menu items.

```python
@app(system_tray=True)
class MyApp(AppBase):
    show: QAction = new("Show")
    ____: Separator  # Creates a separator line
    quit: QAction = new("Quit")
```

## System Tray vs Menu Bar

System tray menus are NOT added to the window menu bar. They remain separate.

```python
@app(system_tray=True)
class MyApp(AppBase):
    file_menu: FileMenu = new()    # Goes to menu bar
    system_tray: TrayMenu = new()  # Tray only, not in menu bar
    label: QLabel = new("Content")
```

## System Tray Icons

### Tray-Specific Icon

```python
@app(system_tray=True, tray_icon=QIcon())
class MyApp(AppBase):
    show: QAction = new("Show")
```

### Fallback to Window Icon

If `tray_icon` is not specified, the `icon` parameter is used as fallback.

```python
@app(system_tray=True, icon=QIcon())
class MyApp(AppBase):
    show: QAction = new("Show")
```

## System Tray with Window Content

An app can have both window content (widgets) and a system tray simultaneously.

```python
@app(title="My App", system_tray=True)
class MyApp(AppBase):
    label: QLabel = new("Window Content")
    system_tray: TrayMenu = new()
```

## Signal Connections

### Direct Action Signals

Connect tray action signals to methods using `triggered=`.

```python
@app(system_tray=True)
class MyApp(AppBase):
    show: QAction = new("Show", triggered="on_show")

    def on_show(self) -> None:
        print("Show triggered!")
```

### Menu Action Signals

Signal connections also work inside tray Menu classes.

```python
@menu(text="Tray")
class TrayMenu(Menu):
    show: QAction = new("Show", triggered="on_show")

    def on_show(self) -> None:
        print("Show triggered!")
```

## Reactive Bindings

Tray actions support reactive property bindings like `enabled=`.

```python
@app(system_tray=True)
class MyApp(AppBase):
    _can_quit: Variable[bool] = new(False)
    quit: QAction = new("Quit", enabled="_can_quit")
```

When `_can_quit.value` changes, the action's enabled state updates automatically.

## No Auto-Window Behavior

Apps with only QAction fields (no QWidgets) do not create an auto-window. The system tray operates independently.
