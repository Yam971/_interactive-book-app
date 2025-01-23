import os
import re
from PIL import Image

def generate_background_image(child_name, config):
    """
    Generates 'Background_<child_name>.png' by overlaying letter images
    onto the background. Features include:
      - Dynamic letter spacing per name length (2..12)
      - Two sets of letters: normal (length 2..7) vs. small (length 8..12)
      - Variation cycling for repeated letters (E.png, E1.png, E2.png, etc.)
      - Hyphenated names (e.g., 'Jean-Luc'), counting the hyphen as a character
        and using hyphen.png / hyphen_small.png as needed.
    """

    # 1) Determine the name length (including hyphens)
    name_length = len(child_name)

    # Decide which folder + suffix to use based on length
    # 2..7 => normal
    # 8..12 => small
    # outside that => default to normal
    if 2 <= name_length <= 7:
        letters_folder_key = "letters_normal"
        suffix_small = ""
    elif 8 <= name_length <= 12:
        letters_folder_key = "letters_small"
        suffix_small = config.get("filename_suffix_small", "_small")
    else:
        letters_folder_key = "letters_normal"
        suffix_small = ""

    # 2) Build paths from config
    background_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_background"].replace("monet_V0_8/", "")
    )

    letters_folder = os.path.join(
        os.path.dirname(__file__),
        config["paths"][letters_folder_key].replace("monet_V0_8/", "")
    )

    output_folder = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_output"].replace("monet_V0_8/", "")
    )

    # Make sure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # 3) Load background
    background = Image.open(background_path).convert("RGBA")
    bg_width, bg_height = background.size

    # Convert child's name into a list of characters
    letters_in_name = list(child_name)  # includes hyphens if present
    if not letters_in_name:
        print("[Warning] Child name is empty, nothing to generate.")
        return

    # 4) Determine letter spacing
    spacing_dict = config.get("letter_spacing_per_length", {})
    default_spacing = config.get("default_letter_spacing_px", 0)
    letter_spacing = spacing_dict.get(str(name_length), default_spacing)

    # 5) Variation logic
    # We'll collect images for each character in the name, possibly cycling variations.
    # Hyphen => "hyphen.png" or "hyphen_small.png"
    # Letters => e.g. E.png, E1.png, E_small.png, E1_small.png, etc.

    variations_cache = {}

    def get_variations_for_char(char: str):
        """
        Returns the list of valid image paths for the given character,
        applying the suffix for 'small' if needed.
        """
        # If it's a hyphen, treat it as 'hyphen' as the base name
        if char == '-':
            base_char = 'hyphen'
        else:
            # For letters, uppercase them (e.g., 'E')
            base_char = char.upper()

        # Example filenames: 
        #   E.png, E1.png (normal)
        #   E_small.png, E1_small.png (small)
        #   hyphen.png, hyphen_small.png
        # We'll handle them with a regex that checks for optional digits 
        # between the base_char and suffix_small, e.g. E1_small
        pattern_without_digits = rf"^{re.escape(base_char)}{suffix_small}\.png$"
        pattern_with_digits   = rf"^{re.escape(base_char)}(\d+){re.escape(suffix_small)}\.png$"

        valid_files = []
        for filename in os.listdir(letters_folder):
            if re.match(pattern_without_digits, filename) or re.match(pattern_with_digits, filename):
                valid_files.append(filename)

        valid_files.sort()  # E.png < E1.png < E2.png, or hyphen.png < hyphen1.png, etc.
        return [os.path.join(letters_folder, f) for f in valid_files]

    def load_next_variation(char: str):
        # If we haven't cached variations for this character, do it now
        if char not in variations_cache:
            variations_cache[char] = (get_variations_for_char(char), 0)

        files_list, index = variations_cache[char]
        if not files_list:
            # No files found for this char
            return None

        chosen_file = files_list[index]
        new_index = (index + 1) % len(files_list)  # round-robin
        variations_cache[char] = (files_list, new_index)

        return Image.open(chosen_file).convert("RGBA")

    # 6) Collect images in order
    images_to_composite = []
    for ch in letters_in_name:
        img = load_next_variation(ch)
        if img:
            images_to_composite.append(img)
        else:
            print(f"[Warning] No images found for character '{ch}'. Skipping.")

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
    top_y = 0  # Could read from config if desired

    current_x = x_start
    for img in images_to_composite:
        background.alpha_composite(img, dest=(current_x, top_y))
        current_x += img.size[0] + letter_spacing

    # 9) Save
    output_filename = f"Background_{child_name}.png"
    output_path = os.path.join(output_folder, output_filename)
    background.save(output_path)
    print(f"[Info] Generated image saved at: {output_path}")
