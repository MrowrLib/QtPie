from qtpy.QtGui import QAction
from qtpy.QtWidgets import QLabel

from qtpie import ColorScheme, Dialog, Menu, Separator, Var, dialog, menu, new, set_color_scheme, set_theme, set_zoom


@dialog
class FontAndTypographyDemoDialog(Dialog):
    ### Example Labels to demo Fonts ###
    lbl_font_avrile_sans: QLabel = new("Avrile Sans - The quick brown fox jumps over the lazy dog", stylesheet="font-family: 'Avrile Sans';")
    lbl_font_avrile_serif: QLabel = new("Avrile Serif - The quick brown fox jumps over the lazy dog", stylesheet="font-family: 'Avrile Serif';")
    lbl_font_droid_serif: QLabel = new("Droid Serif - The quick brown fox jumps over the lazy dog", stylesheet="font-family: 'Droid Serif';")
    lbl_font_high_sans: QLabel = new("High Sans Serif 7 - The quick brown fox jumps over the lazy dog", stylesheet="font-family: 'High Sans Serif 7';")
    lbl_font_open_sans: QLabel = new("Open Sans Condensed Light - The quick brown fox jumps over the lazy dog", stylesheet="font-family: 'Open Sans Condensed Light';")
    lbl_font_fira_code: QLabel = new("Fira Code iScript - The quick brown fox jumps over the lazy dog", stylesheet="font-family: 'Fira Code iScript';")
    lbl_font_yoster: QLabel = new("Yoster Island - The quick brown fox jumps over the lazy dog", stylesheet="font-family: 'Yoster Island';")
    lbl_font_typerighter: QLabel = new("RM Typerighter - The quick brown fox jumps over the lazy dog", stylesheet="font-family: 'RM Typerighter';")

    ### Example Labels to demo Typography Classes ###
    lbl_typo_h1: QLabel = new("Heading 1 - The quick brown fox", classes=["h1"])
    lbl_typo_h2: QLabel = new("Heading 2 - The quick brown fox", classes=["h2"])
    lbl_typo_h3: QLabel = new("Heading 3 - The quick brown fox", classes=["h3"])
    lbl_typo_h4: QLabel = new("Heading 4 - The quick brown fox", classes=["h4"])
    lbl_typo_h5: QLabel = new("Heading 5 - The quick brown fox", classes=["h5"])
    lbl_typo_h6: QLabel = new("Heading 6 - The quick brown fox", classes=["h6"])
    lbl_typo_display1: QLabel = new("Display 1 - Hero Text", classes=["display-1"])
    lbl_typo_display2: QLabel = new("Display 2 - Large Title", classes=["display-2"])
    lbl_typo_body: QLabel = new("Body text - Regular paragraph content for reading.", classes=["body"])
    lbl_typo_lead: QLabel = new("Lead text - Introductory paragraph with emphasis.", classes=["lead"])
    lbl_typo_small: QLabel = new("Small text - Fine print and secondary information.", classes=["small"])
    lbl_typo_tiny: QLabel = new("Tiny text - Very small annotations.", classes=["tiny"])
    lbl_typo_caption: QLabel = new("Caption - Image or figure description.", classes=["caption"])
    lbl_typo_footnote: QLabel = new("Footnote - Additional reference information.", classes=["footnote"])
    lbl_typo_code: QLabel = new("const x = 42;", classes=["code"])
    lbl_typo_code_block: QLabel = new("function hello() {\n  return 'world';\n}", classes=["code-block"])
    lbl_typo_terminal: QLabel = new("$ npm install && npm run build", classes=["terminal"])
    lbl_typo_quote: QLabel = new("To be or not to be, that is the question.", classes=["quote"])
    lbl_typo_label: QLabel = new("Form Label", classes=["label"])
    lbl_typo_meta: QLabel = new("Last updated: Jan 25, 2026", classes=["meta"])
    lbl_typo_bold: QLabel = new("Bold text example", classes=["font-bold"])
    lbl_typo_italic: QLabel = new("Italic text example", classes=["italic"])
    lbl_typo_uppercase: QLabel = new("Uppercase text", classes=["uppercase"])
    lbl_typo_mono: QLabel = new("Monospace font family", classes=["mono"])
    lbl_typo_serif: QLabel = new("Serif font family", classes=["serif"])


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
