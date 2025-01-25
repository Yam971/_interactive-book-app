import os
import re
from PIL import Image

def generate_progressive_images(child_name, config):
    """
    Generates multiple images, each adding one letter up to the second-last letter of child_name.
    For example, 'Leah' => [L, LE, LEA].
    Returns a list of filenames that were generated, in order.
    """

    name_length = len(child_name)
    if name_length < 2:
        # If the name has 0 or 1 letter, we won't generate anything (since we skip full name).
        print("[Info] Name length is <2. No incremental images generated.")
        return []

    # Pull config settings for Renoir
    renoir_background_key = "renoir_background"
    renoir_letters_normal_key = "renoir_letters_normal"
    renoir_letters_small_key = "renoir_letters_small"
    renoir_output_key = "renoir_output"

    # The base logic for letter overlay remains the same, but we loop partial substrings.
    # We'll define a small helper function that, given some substring, does the overlay.
    def generate_partial_image(substr, step_index):
        """
        Creates an overlay image for 'substr' (e.g. 'LEA'), 
        saves it as Renoir_<child_name>_step{step_index}.png, 
        and returns the filename.
        """

        # Decide which folder + suffix to use based on length
        substring_len = len(substr)
        if 2 <= substring_len <= 7:
            letters_folder_key = renoir_letters_normal_key
            suffix_small = ""
        elif 8 <= substring_len <= 12:
            letters_folder_key = renoir_letters_small_key
            suffix_small = config.get("filename_suffix_small", "_small")
        else:
            letters_folder_key = renoir_letters_normal_key
            suffix_small = ""

        # Build paths from config
        background_path = os.path.join(
            os.path.dirname(__file__),
            config["paths"][renoir_background_key].replace("renoir_V0_1/", "")
        )

        letters_folder = os.path.join(
            os.path.dirname(__file__),
            config["paths"][letters_folder_key].replace("renoir_V0_1/", "")
        )

        output_folder = os.path.join(
            os.path.dirname(__file__),
            config["paths"][renoir_output_key].replace("renoir_V0_1/", "")
        )
        os.makedirs(output_folder, exist_ok=True)

        # Load background
        background = Image.open(background_path).convert("RGBA")
        bg_width, bg_height = background.size

        # Convert the partial substring into a list of characters
        letters_in_name = list(substr)
        if not letters_in_name:
            print("[Warning] Substring is empty, skipping.")
            return None

        # Determine letter spacing
        spacing_dict = config.get("letter_spacing_per_length", {})
        default_spacing = config.get("default_letter_spacing_px", 0)
        letter_spacing = spacing_dict.get(str(substring_len), default_spacing)

        # Variation logic
        variations_cache = {}

        def get_variations_for_char(char: str):
            """Return a list of valid image paths for the given character."""
            if char == '-':
                base_char = 'hyphen'
            else:
                base_char = char.upper()

            pattern_without_digits = rf"^{re.escape(base_char)}{suffix_small}\.png$"
            pattern_with_digits   = rf"^{re.escape(base_char)}(\d+){re.escape(suffix_small)}\.png$"

            valid_files = []
            for filename in os.listdir(letters_folder):
                if (re.match(pattern_without_digits, filename) or
                        re.match(pattern_with_digits, filename)):
                    valid_files.append(filename)

            valid_files.sort()
            return [os.path.join(letters_folder, f) for f in valid_files]

        def load_next_variation(char: str):
            if char not in variations_cache:
                variations_cache[char] = (get_variations_for_char(char), 0)

            files_list, index = variations_cache[char]
            if not files_list:
                return None

            chosen_file = files_list[index]
            new_index = (index + 1) % len(files_list)
            variations_cache[char] = (files_list, new_index)
            return Image.open(chosen_file).convert("RGBA")

        # Collect images for each character
        images_to_composite = []
        for ch in letters_in_name:
            img = load_next_variation(ch)
            if img:
                images_to_composite.append(img)
            else:
                print(f"[Warning] No images found for char '{ch}'. Skipping.")

        if not images_to_composite:
            print("[Warning] No valid images loaded for substring '{substr}', skipping generation.")
            return None

        # Calculate total width + spacing
        widths = [img.size[0] for img in images_to_composite]
        sum_widths = sum(widths)
        total_spacing = (len(images_to_composite) - 1) * letter_spacing
        total_width = sum_widths + total_spacing

        # Center horizontally, top aligned
        x_start = (bg_width - total_width) // 2
        top_y = 0

        current_x = x_start
        for img in images_to_composite:
            background.alpha_composite(img, dest=(current_x, top_y))
            current_x += img.size[0] + letter_spacing

        # Save the partial image
        output_filename = f"Renoir_{child_name}_step{step_index}.png"
        output_path = os.path.join(output_folder, output_filename)
        background.save(output_path)
        print(f"[Info] Generated partial image: {output_path}")
        return output_filename

    # Now produce images for each partial substring up to n-1
    partial_filenames = []
    for i in range(1, name_length):  # i = 1..(n-1)
        substr = child_name[:i]  # first i letters
        step_index = i  # or i could be something else
        filename = generate_partial_image(substr, step_index)
        if filename:
            partial_filenames.append(filename)

    return partial_filenames
