import os
from PIL import Image
import chardet
import sys
import codecs

ptf = ""
while (ptf == ""):
    print("Path to png file: ")
    ptf = input()

tile_size = 8

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

if not (os.path.exists(ptf) and ptf.find(".png") != -1):
    sys.exit("File not found, exiting.")

this_path = ptf.split("/")
filename = this_path.pop(-1).replace(".png", "").replace("-","_")
this_path = '/'.join(this_path)
img = Image.open(ptf)
img_width, img_height = img.size

output_folder = this_path + "/"

os.makedirs(output_folder, exist_ok=True)

sprite_settings = ""
sprite_chars = ""

tile_index = 0
char_index = 0
tiles = []
character_ascii_data = []
invalid_utf8 = [127,129,141,143,144,157,160,173]

for i in range(32, 256):
    if i not in invalid_utf8:
        this_char = fix_and_convert_str_to_utf8(chr(i))
        character_ascii_data.append(str(i) + " " + this_char.replace("\\","backslash"))

for i in range(0, img_height, tile_size):
    for j in range(0, img_width, tile_size):
        left = j
        upper = i
        right = j + tile_size
        lower = i + tile_size
        
        if(tile_index + 32 < 256 ) and (tile_index + 32) not in invalid_utf8:
            tile = img.crop((left, upper, right, lower)).convert('P', palette=Image.Palette.ADAPTIVE, colors=8)
            tiles.append(tile)
            width, height = tile.size
            # Iterate through each row and then each pixel to find consecutive runs
            max_consecutive_length = 0
            current_consecutive_length = 0
            for x in range(width):
                pixel_color = tile.getpixel((x, 0))
                # Convert pixel_color to RGB if it's RGBA for comparison
                if isinstance(pixel_color, tuple) and len(pixel_color) == 4:
                    pixel_color = pixel_color[:3]
                if pixel_color == 0:#First color in the palette index is 0
                    current_consecutive_length += 1
                else:
                    max_consecutive_length = max(max_consecutive_length, current_consecutive_length)
                    current_consecutive_length = 0
            # After each row, update max_consecutive_length in case the longest run was at the end of the row
            max_consecutive_length = tile_size - max(max_consecutive_length, current_consecutive_length)
            rv = str(max_consecutive_length) + ",  //" + character_ascii_data[char_index] + "\n"
            char_index = char_index + 1
            print(rv)
            sprite_settings += rv
            if(tile_index + 32 >= 127):
                sprite_chars += fix_and_convert_str_to_utf8(chr(tile_index + 32)) + "\n"

        # # Save the tile into individual files
        # tile_filename = os.path.join(output_folder, f"tile_{tile_index:04d}.bmp")
        # tile.save(tile_filename , format="BMP")
        tile_index += 1
strip_width = tile_size
strip_height = (len(tiles) * tile_size) - tile_size # last one is for the space character, which is ignored in butano

vertical_strip_img = Image.new('P', (strip_width, strip_height))

# Paste each tile into the new image
current_height = 0
thispalette = tiles[0].getpalette()
tiles.pop(0)

for tile in tiles:        
    vertical_strip_img.paste(tile, (0, current_height))
    current_height += tile_size

vertical_strip_img.putpalette(thispalette)

vertical_strip_img.save(output_folder + filename + ".bmp", format="BMP")
sprite_settings += "\n\n" + sprite_chars
with open(output_folder + filename + ".txt", "w", encoding="utf-8") as f:
    f.write(sprite_settings)