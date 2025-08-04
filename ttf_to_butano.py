from PIL import Image, ImageDraw, ImageFont
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

text_color = (0,0,0)
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

image_width = font_size 
image_height = len(text_to_render) * font_size - font_size # for the blank ' ' character

image = Image.new("P", (image_width, image_height), "#7f007f")
image_palette = image.getpalette()
if(image_palette != None): #put second color into palette, white.
    image_palette.insert(3,255)
    image_palette.insert(3,255)
    image_palette.insert(3,255)
    image.putpalette(image_palette)

draw = ImageDraw.Draw(image)

if(antialiased == "Y"):
    antialiased = "L" #antialiased, while set to 1 for aliased
else:
    antialiased = "1"
draw.fontmode = antialiased

y_position = 0
for i in range(1,len(text_to_render)):
    y_position = (i - 1) * font_size # Move down by font_size for the next character
    draw.text((0, y_position), text_to_render[i], font=font, spacing=spacing, align="left", fill=text_color)

blank_tile = Image.new("P", (font_size, font_size), "#7f007f")
if(image_palette != None):
    blank_tile.putpalette(image_palette)

sprite_settings = ""
ascii_index = 1
for char_index in range(33, 256): #33 is because relevant ascii characters starts at 33, excluding blank space (32)
    if (char_index) in invalid_utf8:
        continue

    i = (ascii_index - 1) * font_size
    left = 0
    upper = i
    right = font_size
    lower = i + font_size
    
    tile = image.crop((left, upper, right, lower)).convert('P', palette=Image.Palette.ADAPTIVE, colors=3)
    width, height = tile.size
    # Iterate through each row and then each pixel to find consecutive runs
    valid_pixels = 0
    empty_pixels_on_left = font_size

    for y in range(height):
        current_consecutive_length = font_size
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

    for y in range(height):
        for x in range(width):
            if(x - spacing >= valid_pixels):
                break
            if tile.getpixel((x,y)) == 0:
                tile.putpixel((x,y), (255,255,255)) #put to second color in the palette, aka white
    
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