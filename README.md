# butano-font-converters
Converts OTF/TTF fonts and gbstudio-ready font PNGs to a butano friendly format

## How to use
Make sure chardet and pillow are installed via ```pip install chardet``` and ```pip install pillow```
Run the script using python and follow the instructions in the CLI.

Use the data in FONT_NAME.txt to easily create font header files for butano!

### The output files can be found in:
- otf/ttf: Same folder as script file
- gbstudio: Same folder as png input

## Tips
You can recolor your fonts with ```text_generator.set_palette_item(bn::sprite_items::palette_sprite_name_here.palette_item());```!
