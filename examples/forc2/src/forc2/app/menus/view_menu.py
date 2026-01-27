from qtpy.QtCore import Qt
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QLabel, QSplitter

from qtpie import ColorScheme, Dialog, Menu, Separator, Stretch, Var, Widget, dialog, menu, new, set_color_scheme, set_theme, set_zoom, widget


@widget
class FontAndTypographyDemoPartOne(Widget):
    ### Example Labels to demo Fonts ###
    _lbl_fonts_header: QLabel = new("FONTS", classes=["h2", "bold"])
    lbl_font_avrile_sans: QLabel = new("Avrile Sans - The quick brown fox", stylesheet="font-family: 'Avrile Sans';")
    lbl_font_avrile_serif: QLabel = new("Avrile Serif - The quick brown fox", stylesheet="font-family: 'Avrile Serif';")
    lbl_font_droid_serif: QLabel = new("Droid Serif - The quick brown fox", stylesheet="font-family: 'Droid Serif';")
    lbl_font_high_sans: QLabel = new("High Sans Serif 7 - The quick brown fox", stylesheet="font-family: 'High Sans Serif 7';")
    lbl_font_open_sans: QLabel = new("Open Sans Condensed Light - The quick brown fox", stylesheet="font-family: 'Open Sans Condensed Light';")
    lbl_font_fira_code: QLabel = new("Fira Code iScript - The quick brown fox", stylesheet="font-family: 'Fira Code iScript';")
    lbl_font_yoster: QLabel = new("Yoster Island - The quick brown fox", stylesheet="font-family: 'Yoster Island';")
    lbl_font_typerighter: QLabel = new("RM Typerighter - The quick brown fox", stylesheet="font-family: 'RM Typerighter';")

    ### Headings ###
    _lbl_headings_header: QLabel = new("HEADINGS", classes=["h2", "bold", "mt-4"])
    lbl_h1: QLabel = new("h1 - The quick brown fox", classes=["h1"])
    lbl_h2: QLabel = new("h2 - The quick brown fox", classes=["h2"])
    lbl_h3: QLabel = new("h3 - The quick brown fox", classes=["h3"])
    lbl_h4: QLabel = new("h4 - The quick brown fox", classes=["h4"])
    lbl_h5: QLabel = new("h5 - The quick brown fox", classes=["h5"])
    lbl_h6: QLabel = new("h6 - The quick brown fox", classes=["h6"])

    ### Display / Hero ###
    _lbl_display_header: QLabel = new("DISPLAY / HERO", classes=["h2", "bold", "mt-4"])
    lbl_display1: QLabel = new("display-1 - Hero Text", classes=["display-1"])
    lbl_display2: QLabel = new("display-2 - Large Title", classes=["display-2"])
    lbl_display3: QLabel = new("display-3 - Subtitle", classes=["display-3"])
    lbl_display4: QLabel = new("display-4 - Small Subtitle", classes=["display-4"])
    lbl_display5: QLabel = new("display-5 - Tiny Subtitle", classes=["display-5"])

    ### Body Text ###
    _lbl_body_header: QLabel = new("BODY TEXT", classes=["h2", "bold", "mt-4"])
    lbl_p: QLabel = new("p - Regular paragraph content.", classes=["p"])
    lbl_lead: QLabel = new("lead - Introductory paragraph.", classes=["lead"])

    ### Small Text ###
    _lbl_small_header: QLabel = new("SMALL TEXT", classes=["h2", "bold", "mt-4"])
    lbl_text_small: QLabel = new("text-small - Fine print.", classes=["text-small"])
    lbl_text_tiny: QLabel = new("text-tiny - Very small.", classes=["text-tiny"])
    lbl_caption: QLabel = new("caption - Image description.", classes=["caption"])
    lbl_footnote: QLabel = new("footnote - Reference info.", classes=["footnote"])
    lbl_metadata: QLabel = new("metadata - Meta info.", classes=["metadata"])
    lbl_timestamp: QLabel = new("timestamp - Time displays.", classes=["timestamp"])

    _stretch: Stretch


@widget
class FontAndTypographyDemoPartTwo(Widget):
    ### Code ###
    _lbl_code_header: QLabel = new("CODE", classes=["h2", "bold"])
    lbl_code_inline: QLabel = new("code-inline - const x = 42;", classes=["code-inline"])
    lbl_pre: QLabel = new("pre - function hello() { return 'world'; }", classes=["pre"])
    lbl_console: QLabel = new("console - $ npm run build", classes=["console"])

    ### Special ###
    _lbl_special_header: QLabel = new("SPECIAL", classes=["h2", "bold", "mt-4"])
    lbl_blockquote: QLabel = new("blockquote - To be or not to be.", classes=["blockquote"])
    lbl_form_label: QLabel = new("form-label - Form Label", classes=["form-label"])
    lbl_brand: QLabel = new("brand - Brand text", classes=["brand"])
    lbl_accent: QLabel = new("accent - Accent colored text", classes=["accent"])

    ### Font Weight ###
    _lbl_weight_header: QLabel = new("FONT WEIGHT", classes=["h2", "bold", "mt-4"])
    lbl_font_thin: QLabel = new("font-thin (100)", classes=["font-thin"])
    lbl_font_extralight: QLabel = new("font-extralight (200)", classes=["font-extralight"])
    lbl_font_light: QLabel = new("font-light (300)", classes=["font-light"])
    lbl_font_normal: QLabel = new("font-normal (400)", classes=["font-normal"])
    lbl_font_medium: QLabel = new("font-medium (500)", classes=["font-medium"])
    lbl_font_semibold: QLabel = new("font-semibold (600)", classes=["font-semibold"])
    lbl_bold: QLabel = new("bold (700)", classes=["bold"])
    lbl_font_extrabold: QLabel = new("font-extrabold (800)", classes=["font-extrabold"])
    lbl_font_black: QLabel = new("font-black (900)", classes=["font-black"])

    ### Style ###
    _lbl_style_header: QLabel = new("STYLE", classes=["h2", "bold", "mt-4"])
    lbl_italic: QLabel = new("italic - Italic text example", classes=["italic"])
    lbl_uppercase: QLabel = new("uppercase - uppercase text", classes=["uppercase"])
    lbl_lowercase: QLabel = new("lowercase - LOWERCASE TEXT", classes=["lowercase"])
    lbl_capitalize: QLabel = new("capitalize - capitalize text", classes=["capitalize"])

    ### Font Family ###
    _lbl_family_header: QLabel = new("FONT FAMILY", classes=["h2", "bold", "mt-4"])
    lbl_monospace: QLabel = new("monospace - Monospace font", classes=["monospace"])
    lbl_serif: QLabel = new("serif - Serif font", classes=["serif"])
    lbl_sans: QLabel = new("sans - Sans-serif font", classes=["sans"])

    _stretch: Stretch


@dialog(title="Font and Typography Demo", size=(1200, 700))
class FontAndTypographyDemoDialog(Dialog):
    _splitter: QSplitter = new(orientation=Qt.Orientation.Horizontal)
    _part_one: FontAndTypographyDemoPartOne = new(splitter="_splitter")
    _part_two: FontAndTypographyDemoPartTwo = new(splitter="_splitter")


@menu(title="View")
class ViewMenu(Menu):
    ### Variables ###
    scale_factor: Var[float] = new(1.0, onChange="_on_scale_factor_changed")

    ### Actions ###
    _light_mode: QAction = new("Switch to Light Mode", triggered="_on_light_mode")
    _dark_mode: QAction = new("Switch to Dark Mode", triggered="_on_dark_mode")
    _________: Separator
    _zoom_in: QAction = new("Zoom In", shortcut="Ctrl+Shift+=", triggered="_on_zoom_in")
    _zoom_out: QAction = new("Zoom Out", shortcut="Ctrl+Shift+-", triggered="_on_zoom_out")
    __________: Separator
    _font_and_typography_demo: QAction = new("Font and Typography Demo", shortcut="Ctrl+Shift+D", triggered="{FontAndTypographyDemoDialog.show_dialog()}")

    def _on_light_mode(self):
        set_color_scheme(ColorScheme.Light)
        set_theme("light")
        self.emit_event("on_reload_window")

    def _on_dark_mode(self):
        set_color_scheme(ColorScheme.Dark)
        set_theme("dark")
        self.emit_event("on_reload_window")

    ### Methods ###
    def _on_zoom_in(self) -> None:
        self.scale_factor *= 1.1
        print(self.scale_factor)

    def _on_zoom_out(self) -> None:
        self.scale_factor /= 1.1
        print(self.scale_factor)

    def _on_scale_factor_changed(self, new_value: float) -> None:
        set_zoom(new_value)
