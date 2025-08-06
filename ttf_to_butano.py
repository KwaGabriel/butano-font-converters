from PIL import Image, ImageDraw, ImageFont, ImageOps
import chardet
import codecs
import os
import sys

def fix_and_convert_str_to_utf8(input_str = ""):
    try:
        intermediate_bytes = input_str.encode('latin-1', errors='strict')
    except UnicodeEncodeError as e:
        print(f"Error re-byte-ifying string: {e}")
        print("This might happen if the input_str contains Unicode characters > U+00FF that cannot be encoded by latin-1.")
        return "Error: Could not process input string."
    
    try:
        decoded_text = intermediate_bytes.decode('windows-1252', errors='replace')
        return decoded_text # This is the final Unicode string
    except UnicodeDecodeError:
        encoding_info = chardet.detect(intermediate_bytes)
        encoding = encoding_info['encoding']

        if encoding is None:
            print(f"Warning: chardet failed to detect encoding. Trying 'latin-1' as a last resort. Confidence: {encoding_info['confidence']}")
            final_decoded_str = intermediate_bytes.decode('latin-1', errors='replace')
        else:
            print(f"Detected encoding by chardet: {encoding} with confidence {encoding_info['confidence']}")
            final_decoded_str = intermediate_bytes.decode(encoding, errors='replace')
        return final_decoded_str
    
ptf = ""
while (ptf == ""):
    print("Path to font file:")
    ptf = input()

tile_size = 0
while (tile_size <= 0):
    print("Tile size:")
    tile_size = int(input())

font_size = 0
while (font_size <= 0):
    print("Font size:")
    font_size = int(input())

antialiased = ""
while ((antialiased != "Y".casefold()) and (antialiased != "N".casefold())):
    print("Use antialiasing (Y/N):")
    antialiased = input().casefold()

spacing = -1
while (spacing < 0):
    print("Character spacing:")
    spacing = int(input())

font_yoffset = -1
while (font_yoffset < 0):
    print("Y-offset (for weird fonts):")
    font_yoffset = int(input())

bg_fill = ""
while ((bg_fill != "Y".casefold()) and (bg_fill != "N".casefold())):
    print("Fill BG (Y/N):")
    bg_fill = input().casefold()

bg_fill = bg_fill.casefold() == "Y".casefold()

drop_shadow = -1
while (drop_shadow < 0):
    print("Drop Shadow Offset:")
    drop_shadow = int(input())

this_path = ptf.split("/")
filename = this_path.pop(-1).replace(".ttf", "").replace(" ","_").replace("-","_")

output_folder = os.path.abspath(__file__).split("\\")
output_folder.pop(-1)
output_folder = '/'.join(output_folder) + "/"

os.makedirs(output_folder, exist_ok=True)
font_path = ptf
font = ImageFont.truetype(font_path, font_size)
if(font == None):
    sys.exit("Font not found, exiting. Path specified: " + font_path)

text_to_render = []

invalid_utf8 = [127,129,141,143,144,157,160,173]
character_ascii_data = []

for i in range(32, 256):
    if i not in invalid_utf8:
        this_char = fix_and_convert_str_to_utf8(chr(i))
        text_to_render.append(this_char)
        character_ascii_data.append(str(i) + " " + this_char.replace("\\","backslash"))
sprite_chars = ""
for i in range(127,256):
    if(i not in invalid_utf8):
        sprite_chars += fix_and_convert_str_to_utf8(chr(i)) + "\n"

image_width = tile_size 
image_height = len(text_to_render) * tile_size - tile_size # for the blank ' ' character

image = Image.new("P", (image_width, image_height), "#7f007f")
image_palette = image.getpalette()
if(image_palette != None): #put second color into palette, white.
    image_palette.insert(3,0)
    image_palette.insert(3,0)
    image_palette.insert(3,0)
    image_palette.insert(3,255)
    image_palette.insert(3,255)
    image_palette.insert(3,255)

    if bg_fill:
        image_palette.insert(3,127)
        image_palette.insert(3,127)
        image_palette.insert(3,0)

    image.putpalette(image_palette)

blank_tile = Image.new("P", (tile_size, tile_size), "#7f007f")
if(image_palette != None):
    blank_tile.putpalette(image_palette)
draw = ImageDraw.Draw(Image.new("P",(0,0)))

if(antialiased == "Y"):
    antialiased = "L" #antialiased, while set to 1 for aliased
else:
    antialiased = "1"

y_position = 0
text_color_white = (255,255,255)
text_color_black = (0,0,0)
for i in range(1,len(text_to_render)):    
    y_position = (i-1) * tile_size
    this_tile = blank_tile.copy()
    draw = ImageDraw.Draw(this_tile)
    draw.fontmode = antialiased
    if drop_shadow != 0:
        for x in range(drop_shadow - 1, 0, -1):
            draw.text((x, font_yoffset + x), text_to_render[i], font=font, spacing=spacing, align="left", fill=text_color_black)
        draw.text((0, font_yoffset), text_to_render[i], font=font, spacing=spacing, align="left", fill=text_color_white)
    else:
        draw.text((0, font_yoffset), text_to_render[i], font=font, spacing=spacing, align="left", fill=text_color_black)

    image.paste(this_tile, (0, y_position))

if(image_palette != None):
    blank_tile.putpalette(image_palette)

sprite_settings = ""
ascii_index = 1
for char_index in range(33, 256): #33 is because relevant ascii characters starts at 33, excluding blank space (32)
    if (char_index) in invalid_utf8:
        continue

    i = (ascii_index - 1) * tile_size
    left = 0
    upper = i
    right = tile_size
    lower = i + tile_size
    
    tile = image.crop((left, upper, right, lower)).convert('P', palette=Image.Palette.ADAPTIVE, colors=4)
    width, height = tile.size
    # Iterate through each row and then each pixel to find consecutive runs
    valid_pixels = 0
    empty_pixels_on_left = tile_size

    for y in range(height):
        current_consecutive_length = tile_size
        for right_x in range(width,0,-1):
            pixel_color = tile.getpixel((right_x - 1, y))

            if pixel_color == 0:
                current_consecutive_length -= 1
            else:
                valid_pixels = max(valid_pixels, current_consecutive_length)
                break
        valid_pixels = max(valid_pixels, current_consecutive_length)

        current_consecutive_length = 0
        for left_x in range(width):
            pixel_color = tile.getpixel((left_x, y))
            if pixel_color == 0:
                current_consecutive_length += 1
            else:
                empty_pixels_on_left = min(empty_pixels_on_left, current_consecutive_length)
                break
        empty_pixels_on_left = min(empty_pixels_on_left, current_consecutive_length)

    if bg_fill:
        valid_pixels -= 1 #to get calculations on base zero
        tile = ImageOps.expand(tile, border=(0,0,spacing,0), fill="#7f007f")
        for y in range(height):
            for x in range(width + spacing):
                if(x > valid_pixels + spacing):
                    break
                if tile.getpixel((x,y)) == 0:
                    tile.putpixel((x,y), (0,127,127))
        valid_pixels += 1

    image.paste(blank_tile,(0, i))
    image.paste(tile, (-empty_pixels_on_left, i))
    character_size = valid_pixels - empty_pixels_on_left + spacing
    if(character_size < 0):
        character_size = 0
    rv = str(character_size) + ",  //" + character_ascii_data[ascii_index] + "\n"
    ascii_index += 1
    sprite_settings += rv

sprite_settings = str(spacing) + ",  //" + character_ascii_data[0] + "\n" + sprite_settings
image.save(output_folder + filename + ".bmp", format="BMP")
sprite_settings += "\n\n" + sprite_chars
with open(output_folder + filename + ".txt", "w", encoding="utf-8") as f:
    f.write(sprite_settings)