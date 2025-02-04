import os
import re
from PIL import Image

# NEW: import the in-memory caches
from cache_manager import _renoir_backgrounds, _renoir_letter_variations

def generate_progressive_images(child_name, config):
    """
    Generates progressive images from step 1..(len(child_name)-1),
    each partial substring adding one more letter.
    Fully uses the in-memory data from cache_manager,
    avoiding disk reads for backgrounds/letters.
    """

    name_length = len(child_name)
    if name_length < 2:
        return []

    # We'll store the final output filenames in a list
    results = []

    # 1) Variation index map for round-robin letter usage.
    # The key is a tuple (base_char, use_small) and the value is the current index.
    variation_index_map = {}

    # Helper function: Retrieve the appropriate background for the given step.
    def get_background_for_step(next_char):
        """
        If next_char is '-', return the image for "Background_hyphen.png".
        Otherwise, try "Background_<Letter>.png". If not found, fallback to "Background.png".
        """
        if next_char == '-':
            fname = "Background_hyphen.png"
        else:
            fname = f"Background_{next_char}.png"

        if fname not in _renoir_backgrounds:
            fname = "Background.png"
        return _renoir_backgrounds[fname].copy()

    # Helper function: Retrieve the next letter image for the given character.
    def get_next_letter_image(char, use_small):
        base_char = '-' if char == '-' else char.upper()
        suffix_small = "_small" if use_small else ""
        matching_fnames = []
        for fname, pil_list in _renoir_letter_variations.items():
            # Check if the filename starts with the base_char and ends with the correct suffix.
            if fname.startswith(base_char) and fname.endswith(suffix_small + ".png"):
                matching_fnames.append(fname)

        # Sort the matching filenames based on any trailing number.
        def extract_number(f):
            stripped = f
            if suffix_small and stripped.endswith(suffix_small + ".png"):
                stripped = stripped[:-len(suffix_small + ".png")]
            else:
                stripped = stripped[:-4]  # remove ".png"
            if stripped.startswith(base_char):
                stripped = stripped[len(base_char):]
            return int(stripped) if stripped.isdigit() else 0

        matching_fnames.sort(key=extract_number)

        # Combine all images from these filenames.
        combined_images = []
        for fname in matching_fnames:
            combined_images.extend(_renoir_letter_variations[fname])

        if not combined_images:
            return None

        # Use round-robin selection for repeated letters.
        key = (base_char, use_small)
        if key not in variation_index_map:
            variation_index_map[key] = 0
        idx = variation_index_map[key]
        chosen_img = combined_images[idx % len(combined_images)]
        variation_index_map[key] = idx + 1

        return chosen_img.copy()

    # 2) Compute the output folder relative to the project root.
    # Instead of using os.path.dirname(__file__), go two levels up.
    project_root = os.path.dirname(os.path.dirname(__file__))
    # config["paths"]["renoir_output"] should be set to "renoir_V0_1/generated-preview"
    output_folder = os.path.join(project_root, config["paths"]["renoir_output"])
    os.makedirs(output_folder, exist_ok=True)

    # 3) For each step (from 1 to name_length - 1), generate a progressive image.
    for step_index in range(1, name_length):
        substr = child_name[:step_index]
        # Determine the next character (used to pick the background).
        next_char = child_name[step_index] if step_index < len(child_name) else None

        # a) Get the background image for this step.
        bg = get_background_for_step(next_char)

        # b) Decide whether to use small letter images based on the length of the substring.
        use_small = True if 8 <= len(substr) <= 12 else False

        # c) Determine the spacing between letters.
        spacing = config["letter_spacing_per_length"].get(str(len(substr)), config["default_letter_spacing_px"])

        # d) Build a list of letter images for the substring.
        letter_images = []
        for ch in substr:
            letter_img = get_next_letter_image(ch, use_small)
            if letter_img is not None:
                letter_images.append(letter_img)
        if not letter_images:
            continue  # Skip this step if no letter images were found.

        # e) Composite the letter images horizontally centered on the background.
        total_letter_width = sum(img.width for img in letter_images)
        total_spacing = spacing * (len(letter_images) - 1)
        total_width = total_letter_width + total_spacing
        x_start = (bg.width - total_width) // 2
        current_x = x_start
        top_y = 0

        for img in letter_images:
            bg.alpha_composite(img, (current_x, top_y))
            current_x += img.width + spacing

        # f) Save the composite image.
        output_filename = f"Renoir_{child_name}_step{step_index}.png"
        out_path = os.path.join(output_folder, output_filename)
        bg.save(out_path)
        results.append(output_filename)

    return results
