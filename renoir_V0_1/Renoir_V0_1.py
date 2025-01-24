import os
import re
from PIL import Image

def generate_background_image(child_name, config):
    """
    Generates 'Renoir_<child_name>.png' by overlaying letter images
    onto a background. It's a perfect copy of Monet's logic, with paths
    referencing renoir_V0_1 instead of monet_V0_8.
    """

    # 1) Determine the name length (including hyphens)
    name_length = len(child_name)

    # Decide which folder + suffix to use based on length
    # 2..7 => normal
    # 8..12 => small
    # outside that => default to normal
    if 2 <= name_length <= 7:
        letters_folder_key = "renoir_letters_normal"
        suffix_small = ""
    elif 8 <= name_length <= 12:
        letters_folder_key = "renoir_letters_small"
        suffix_small = config.get("filename_suffix_small", "_small")
    else:
        letters_folder_key = "renoir_letters_normal"
        suffix_small = ""

    # 2) Build paths from config
    #   Note: Because __file__ = <...>/renoir_V0_1/Renoir_V0_1.py
    #   we can simply join without .replace(), if we set the config path
    #   as "renoir_V0_1/assets/..." – that already starts from this script's folder.
    background_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_background"].replace("renoir_V0_1/", "")
    )

    letters_folder = os.path.join(
        os.path.dirname(__file__),
        config["paths"][letters_folder_key].replace("renoir_V0_1/", "")
    )

    output_folder = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_output"].replace("renoir_V0_1/", "")
    )

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # 3) Load background
    background = Image.open(background_path).convert("RGBA")
    bg_width, bg_height = background.size

    # Convert child's name into a list of characters (including hyphens)
    letters_in_name = list(child_name)
    if not letters_in_name:
        print("[Warning] Child name is empty, nothing to generate.")
        return

    # 4) Determine letter spacing
    spacing_dict = config.get("letter_spacing_per_length", {})
    default_spacing = config.get("default_letter_spacing_px", 0)
    letter_spacing = spacing_dict.get(str(name_length), default_spacing)

    # 5) Variation logic (same as Monet)
    variations_cache = {}

    def get_variations_for_char(char: str):
        """Returns a list of valid image paths for the given character."""
        # If it's a hyphen, treat it as 'hyphen'
        if char == '-':
            base_char = 'hyphen'
        else:
            base_char = char.upper()

        # Use regex to find possible variations:
        #   E.png, E1.png, E_small.png, E1_small.png, etc.
        pattern_without_digits = rf"^{re.escape(base_char)}{suffix_small}\.png$"
        pattern_with_digits   = rf"^{re.escape(base_char)}(\d+){re.escape(suffix_small)}\.png$"

        valid_files = []
        for filename in os.listdir(letters_folder):
            if re.match(pattern_without_digits, filename) or re.match(pattern_with_digits, filename):
                valid_files.append(filename)

        valid_files.sort()  # e.g. E.png < E1.png < E2.png
        return [os.path.join(letters_folder, f) for f in valid_files]

    def load_next_variation(char: str):
        """Round-robin through each variation of a character."""
        if char not in variations_cache:
            variations_cache[char] = (get_variations_for_char(char), 0)

        files_list, index = variations_cache[char]
        if not files_list:
            # No files found for this char
            return None

        chosen_file = files_list[index]
        new_index = (index + 1) % len(files_list)
        variations_cache[char] = (files_list, new_index)

        return Image.open(chosen_file).convert("RGBA")

    # 6) Collect images in order
    images_to_composite = []
    for ch in letters_in_name:
        img = load_next_variation(ch)
        if img:
            images_to_composite.append(img)
        else:
            print(f"[Warning] No images found for char '{ch}'. Skipping.")

    if not images_to_composite:
        print("[Warning] No valid images loaded, skipping generation.")
        return

    # 7) Calculate total width + spacing
    widths = [img.size[0] for img in images_to_composite]
    sum_widths = sum(widths)
    total_spacing = (len(images_to_composite) - 1) * letter_spacing
    total_width = sum_widths + total_spacing

    # 8) Center horizontally, top aligned
    x_start = (bg_width - total_width) // 2
    top_y = 0

    current_x = x_start
    for img in images_to_composite:
        background.alpha_composite(img, dest=(current_x, top_y))
        current_x += img.size[0] + letter_spacing

    # 9) Save as "Renoir_<child_name>.png"
    output_filename = f"Renoir_{child_name}.png"
    output_path = os.path.join(output_folder, output_filename)
    background.save(output_path)
    print(f"[Info] Renoir image saved at: {output_path}")
