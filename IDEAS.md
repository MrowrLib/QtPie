See how the QWidget which are added to a class are added to a built-in layout? By default.

We don't have support for 3 things that I wanna add:

1. Stretch
2. Spacer item, for more custom spacing
3. Nested layouts (and assigning widgets [or stretch/spacer] to those layouts)

Here is my goal syntax that I wanna support:

```py
@widget
class SomeWidget(Widget):
    regular_widget: QLabel = new("Added to the built-in layout")
    
    # Now let's add a stretch to that!
    stretch: Stretch = new() # I think this should do addStretch(1) right? if I want a stretcher that'll fill its space
    
    # if you want to customize the param to addStretch
    stretch2: Stretch = new(3)
    
    # How about more customization by using a QSpacerItem though?
    spacer: QSpacerItem = new(<width>, <height>, <hPolicy>, <vPolicy>) # if a QSpacerItem is added, use addSpacerItem to add it
    
    # what about nested layouts?
    nested_layout_one: QVBoxLayout = new()
    
    # but ^ that doesn't impact that fact that qwidget (or spaceritem/stretch) apply to the default layout
    another_regular_widget: QLabel = new("this is added to the built-in layout normally, unrelated to nested_layout_one")
    
    # Ok, so how do you USE a nested layout? the layout argument! let's look at it real quick...
    not_added_to_any_layout: QLabel = new("I'm orphaned and not added automatically to any layout", layout=False)
    
    # But let's add to the nested_layout_one!
    added_to_nested_layout: QLabel = new("Yay I'm in the nested layout", layout=nested_layout_one) # <--- can reference it directly (it's a NewField instance)
    
    # or use a string to reference an attribute of the class like this:
    added_to_nested_layout: QLabel = new("Yay I'm in the nested layout", layout="nested_layout_one")
    
    # Make sense?
    
    # You can imagine how a layout can obvs be added to a layout in this way. or QSpacerItem. Or Stretch. in addition to QWidget...
    
    nested_in_nested: QHBoxLayout = new(layout="nested_layout_one")
    stretch3: Stretch = new(layout=nested_layout_one)
    spacer2: QSpacerItem = new(..., layout=nested_layout_one)
```

Make sense?
