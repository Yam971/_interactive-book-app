import os
import re
from PIL import Image

def generate_background_image(child_name, config):
    """
    Generates 'Background_<child_name>.png' by overlaying smaller letter images
    (or smaller "small" images) onto the background.
    
    Key features:
      - Dynamic letter spacing per name length (2..12)
      - Two sets of letter images:
          * normal (2..7 letters)
          * small  (8..12 letters)
      - Variation cycling for repeated letters (E.png, E1.png, E2.png, etc.)
    """

    # 1) Decide which folder to use based on length
    #    2..7 => normal
    #    8..12 => small
    #    outside that range => let's default to normal 
    name_length = len(child_name)
    if 2 <= name_length <= 7:
        letters_folder_config_key = "letters_normal"
        suffix_small = ""  # no suffix
    elif 8 <= name_length <= 12:
        letters_folder_config_key = "letters_small"
        suffix_small = config.get("filename_suffix_small", "_small")
    else:
        # fallback if name length is 1 or >12
        letters_folder_config_key = "letters_normal"
        suffix_small = ""

    # 2) Extract relevant config paths
    background_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_background"].replace("monet_V0_8/", "")
    )

    letters_folder = os.path.join(
        os.path.dirname(__file__),
        config["paths"][letters_folder_config_key].replace("monet_V0_8/", "")
    )

    output_folder = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_output"].replace("monet_V0_8/", "")
    )

    # Make sure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Load the background image
    background = Image.open(background_path).convert("RGBA")
    bg_width, bg_height = background.size

    # Convert child's name into a list of characters
    letters_in_name = [char for char in child_name]
    if not letters_in_name:
        print("[Warning] Child name is empty, nothing to generate.")
        return

    # 3) Determine letter spacing
    spacing_dict = config.get("letter_spacing_per_length", {})
    default_spacing = config.get("default_letter_spacing_px", 0)
    letter_spacing = spacing_dict.get(str(name_length), default_spacing)

    # 4) Variation logic
    # We'll scan the letters folder for valid files for each letter and store them in a cache.
    # Filenames might be E.png, E1.png, E2.png, or if suffix_small is not empty: E_small.png, E1_small.png, etc.
    # We'll then pick the nth variation for the nth occurrence of that letter.

    variations_cache = {}

    def get_variations_for_letter(uppercase_char):
        """
        Return a list of paths to variation images for the given uppercase_char,
        optionally appending the _small suffix if needed.
        Example: For 'E' + suffix='_small', we look for E_small.png, E1_small.png, E2_small.png, etc.
        """
        pattern_without_digits = rf"^{uppercase_char}{suffix_small}\.png$"
        pattern_with_digits =   rf"^{uppercase_char}(\d+){suffix_small}\.png$"

        valid_files = []
        for filename in os.listdir(letters_folder):
            # Does the file match either E_small.png or E1_small.png or E2_small.png etc.?
            if re.match(pattern_without_digits, filename) or re.match(pattern_with_digits, filename):
                valid_files.append(filename)

        # Sort them so e.g. E_small.png < E1_small.png < E2_small.png
        valid_files.sort()

        # Convert to full paths
        full_paths = [os.path.join(letters_folder, f) for f in valid_files]
        return full_paths

    def load_next_variation(uppercase_char):
        """
        Each time we call this for a given uppercase_char, we get the next variation
        in a round-robin fashion.
        """
        # If not in cache, load once
        if uppercase_char not in variations_cache:
            variations_cache[uppercase_char] = get_variations_for_letter(uppercase_char), 0

        files_list, index = variations_cache[uppercase_char]

        if not files_list:
            # No images found, return None
            return None

        # Pick the current file
        chosen_file = files_list[index]
        # Move the index forward (wrap around if needed)
        new_index = (index + 1) % len(files_list)
        variations_cache[uppercase_char] = (files_list, new_index)

        # Return the image
        return Image.open(chosen_file).convert("RGBA")

    images_to_composite = []
    for char in letters_in_name:
        uppercase_char = char.upper()
        letter_img = load_next_variation(uppercase_char)
        if letter_img:
            images_to_composite.append(letter_img)
        else:
            print(f"[Warning] No images found for letter '{char}' with suffix '{suffix_small}'. Skipping.")

    # If no images loaded, do nothing
    if not images_to_composite:
        print("[Warning] No valid letters loaded, skipping generation.")
        return

    # 5) Calculate total width of images + spacing
    letter_widths = [img.size[0] for img in images_to_composite]
    sum_letter_widths = sum(letter_widths)
    total_spacing = (len(images_to_composite) - 1) * letter_spacing
    total_width = sum_letter_widths + total_spacing

    # 6) Compute x_start to center horizontally, and a top_y for top alignment
    x_start = (bg_width - total_width) // 2
    top_y = 0  # or config.get("top_alignment_y", 0) if you prefer a top offset

    # 7) Composite
    current_x = x_start
    for img in images_to_composite:
        background.alpha_composite(img, dest=(current_x, top_y))
        current_x += img.size[0] + letter_spacing

    # 8) Save
    output_filename = f"Background_{child_name}.png"
    output_path = os.path.join(output_folder, output_filename)
    background.save(output_path)
    print(f"[Info] Generated image saved at: {output_path}")
