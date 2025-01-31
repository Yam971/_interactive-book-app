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

    # 1) Variation index map for round-robin letter usage
    variation_index_map = {}  # key=(filename), val=current index in that list
    # But we also need a quick way to find all images that match a certain char + small/normal suffix.

    # For backgrounds: we have keys like "Background_A.png", "Background_hyphen.png", etc.
    # For letters: we have filenames like "A.png", "A_small.png", "hyphen.png", "hyphen_small.png", etc.

    # Let's define a helper to retrieve the correct background from memory
    def get_background_for_step(next_char):
        """
        If next_char is '-', we might do "Background_hyphen.png".
        Else "Background_<Letter>.png".
        If not found, fallback to "Background.png".
        """
        if next_char == '-':
            fname = "Background_hyphen.png"
        else:
            fname = f"Background_{next_char}.png"

        if fname not in _renoir_backgrounds:
            # fallback
            fname = "Background.png"

        # Return a copy so we don't mutate the cached original
        return _renoir_backgrounds[fname].copy()

    # For letters, we store them in _renoir_letter_variations with keys like "A.png", "A1.png", "A_small.png", etc.
    # We'll do a function to retrieve the next variation for a given character, given small or not.
    def get_next_letter_image(char, use_small):
        # e.g. char='A', use_small=True => we look for filenames that start with "A" and end with "_small.png"
        # e.g. char='-', we look for "hyphen_small.png", "hyphen1_small.png", etc.
        base_char = '-' if char == '-' else char.upper()
        suffix_small = "_small" if use_small else ""
        # We'll gather all keys in _renoir_letter_variations that match the pattern
        matching_fnames = []
        for fname, pil_list in _renoir_letter_variations.items():
            # example fname="A.png" or "A1_small.png"
            # check if starts with base_char, ends with suffix_small+".png"
            if fname.startswith(base_char) and fname.endswith(suffix_small + ".png"):
                matching_fnames.append(fname)

        # We'll sort the matching filenames so that e.g. "A.png" < "A1.png" < "A2.png", etc.
        # Typically you do that by extracting digits.
        def extract_number(f):
            # remove suffix_small + .png, then see what's left after the base_char
            # e.g. "A1_small.png" -> remove "_small.png" => "A1"
            # remove "A" => "1"
            # If no digits, return 0
            stripped = f
            if suffix_small and stripped.endswith(suffix_small + ".png"):
                stripped = stripped[: -len(suffix_small + ".png")]
            else:
                stripped = stripped[:-4]  # remove ".png"
            # now stripped might be "A1" or "hyphen2" or "A"
            if stripped.startswith(base_char):
                stripped = stripped[len(base_char):]  # e.g. "1"
            return int(stripped) if stripped.isdigit() else 0

        matching_fnames.sort(key=extract_number)

        # Now we combine all images from those filenames in order
        # e.g. if "A.png" => _renoir_letter_variations["A.png"] might be multiple PIL images
        combined_images = []
        for fname in matching_fnames:
            combined_images.extend(_renoir_letter_variations[fname])

        if not combined_images:
            return None

        # Round-robin through combined_images
        key = (base_char, use_small)
        if key not in variation_index_map:
            variation_index_map[key] = 0

        idx = variation_index_map[key]
        chosen_img = combined_images[idx % len(combined_images)]
        variation_index_map[key] = idx + 1

        return chosen_img.copy()  # copy so we don't mutate the cached original

    # 2) For each step from 1..(name_length-1), build a partial substring image
    output_folder = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["renoir_output"]  # e.g. "renoir_V0_1/generated-preview"
    )
    os.makedirs(output_folder, exist_ok=True)

    for step_index in range(1, name_length):
        substr = child_name[:step_index]
        # Next char for background logic
        next_char = child_name[step_index] if step_index < len(child_name) else None

        # a) Get the background for this step
        bg = get_background_for_step(next_char)

        # b) Determine if we use "small" or "normal" for letters
        substr_len = len(substr)
        if 8 <= substr_len <= 12:
            use_small = True
        else:
            use_small = False

        # c) Determine spacing
        spacing = config["letter_spacing_per_length"].get(
            str(substr_len),
            config["default_letter_spacing_px"]
        )

        # d) Build letter images for the substring
        letter_images = []
        for ch in substr:
            letter_img = get_next_letter_image(ch, use_small)
            if letter_img is not None:
                letter_images.append(letter_img)

        if not letter_images:
            # If none found, skip this step
            continue

        # e) Composite them horizontally centered
        total_letter_width = sum(img.width for img in letter_images)
        total_spacing = spacing * (len(letter_images) - 1)
        total_width = total_letter_width + total_spacing
        x_start = (bg.width - total_width) // 2
        current_x = x_start
        top_y = 0

        for img in letter_images:
            bg.alpha_composite(img, (current_x, top_y))
            current_x += img.width + spacing

        # f) Save
        output_filename = f"Renoir_{child_name}_step{step_index}.png"
        out_path = os.path.join(output_folder, output_filename)
        bg.save(out_path)
        results.append(output_filename)

    return results
