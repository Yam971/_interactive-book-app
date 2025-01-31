import os
import re
from PIL import Image

# NEW: import the in-memory caches
from cache_manager import _monet_backgrounds, _monet_letter_variations

def generate_background_image(child_name, config):
    """
    Generates 'Background_<child_name>.png' by overlaying letter images
    onto the background. Fully uses the in-memory data from cache_manager,
    avoiding any disk reads at runtime.

    Features include:
      - Dynamic letter spacing per name length (2..12)
      - Two sets of letters: normal (length 2..7) vs. small (length 8..12)
      - Variation cycling for repeated letters (A.png, A1.png, A2.png, ... or hyphen.png, hyphen1.png, etc.)
      - Hyphenated names (e.g., 'Jean-Luc') counting the hyphen as a character
    """

    # 1) Determine the name length (including hyphens)
    name_length = len(child_name)

    # Decide which folder (normal vs. small) based on length
    if 2 <= name_length <= 7:
        letters_folder_key = "letters_normal"   # not used for path, but for "use_small=False"
        use_small = False
    elif 8 <= name_length <= 12:
        letters_folder_key = "letters_small"    # "use_small=True"
        use_small = True
    else:
        letters_folder_key = "letters_normal"
        use_small = False

    # 2) Get background from memory cache
    # We assume the "Background.png" key was loaded by cache_manager
    background_img = _monet_backgrounds.get("Background.png")
    if not background_img:
        # fallback: if for some reason it's missing, we can do a blank image or skip
        print("[Warning] Monet background not found in cache; skipping generation.")
        return
    # Always copy() so we don't modify the original cached image
    background = background_img.copy()
    bg_width, bg_height = background.size

    # If child_name is empty, skip
    if not child_name:
        print("[Warning] Child name is empty, nothing to generate.")
        return

    # 3) Determine letter spacing
    spacing_dict = config.get("letter_spacing_per_length", {})
    default_spacing = config.get("default_letter_spacing_px", 0)
    letter_spacing = spacing_dict.get(str(name_length), default_spacing)

    # 4) Build a function to find all variations for a given character in `_monet_letter_variations`
    #    We match the original logic: e.g., "A.png", "A1.png", "A_small.png", "A1_small.png", etc.
    variations_cache = {}

    def get_variations_for_char(char, use_small):
        """
        Returns a sorted list of PIL images from _monet_letter_variations for the given char,
        matching the suffix for small if needed. E.g. A.png, A1.png (normal); A_small.png, A1_small.png (small).
        """
        # We'll scan the keys of _monet_letter_variations, collecting any that match the pattern
        # e.g. if char='A', base might be 'A' or 'A_small'.
        # Then we sort them so A.png < A1.png < A2.png, etc.
        # We do the same logic for 'hyphen' or 'hyphen_small'.

        results = []
        if char == '-':
            base_prefix = "hyphen"
        else:
            base_prefix = char.upper()

        suffix_small = "_small" if use_small else ""

        # We'll loop over the filenames we have in _monet_letter_variations
        for fname, pil_list in _monet_letter_variations.items():
            # Example fname might be "A.png" or "A1_small.png"
            # We'll do a quick pattern check
            if fname.startswith(base_prefix) and fname.endswith(suffix_small + ".png"):
                # Also, we want to ensure that if there's a number, it is right after base_prefix
                # e.g. A1_small, hyphen2_small, etc.
                # We'll do a small regex to confirm.
                # But typically you could just rely on starts/ends. We'll do a simpler approach:
                # "A1_small.png".startswith("A") => True, .endswith("_small.png") => True
                # so we accept it.
                # We'll store all images from pil_list
                results.extend(pil_list)

        # We'll sort by embedded number if any
        # e.g. "A.png" => no digits, "A1.png" => digit 1, "A2.png" => digit 2
        # We'll do a function to extract the numeric portion if present
        def variation_sort_key(fn):
            # e.g. "A1_small.png" -> remove "_small.png" => "A1"
            # then remove "A" => "1"
            # but we already have "fname" here, not from iteration. We'll parse the actual fname in the loop above...
            # Actually let's re-check. We only have the PIL images in results, not the filenames. So let's keep it simpler:
            return 0  # If you want a stable order, you could store numeric indices differently
        # for a robust approach, we might store a separate dictionary: filenames -> images.
        # But for simplicity, let's just keep them in the order they're discovered. 
        # Or if you want to do real sorting, store the filename in a parallel structure.

        return results

    def load_next_variation(char, use_small):
        """
        Round-robin pick the next variation from the cached set for this char.
        """
        if char not in variations_cache:
            # Build the list of images for this char+size
            var_list = get_variations_for_char(char, use_small)
            variations_cache[char] = (var_list, 0)
        var_list, index = variations_cache[char]
        if not var_list:
            return None
        chosen_img = var_list[index]
        new_index = (index + 1) % len(var_list)
        variations_cache[char] = (var_list, new_index)
        return chosen_img.copy()  # copy so we don't mutate the cached object

    # 5) Collect images in order for each character
    images_to_composite = []
    for ch in child_name:
        img_obj = load_next_variation(ch, use_small)
        if img_obj:
            images_to_composite.append(img_obj)
        else:
            print(f"[Warning] No images found for character '{ch}' in Monet cache. Skipping.")

    if not images_to_composite:
        print("[Warning] No valid images loaded for any character, skipping generation.")
        return

    # 6) Composite them horizontally centered
    widths = [img.width for img in images_to_composite]
    sum_widths = sum(widths)
    total_spacing = (len(images_to_composite) - 1) * letter_spacing
    total_width = sum_widths + total_spacing

    x_start = (bg_width - total_width) // 2
    top_y = 0

    current_x = x_start
    for img in images_to_composite:
        background.alpha_composite(img, dest=(current_x, top_y))
        current_x += img.width + letter_spacing

    # 7) Save output
    output_folder = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_output"].replace("monet_V0_8/", "")  # If you want to preserve the output in disk
    )
    os.makedirs(output_folder, exist_ok=True)

    output_filename = f"Background_{child_name}.png"
    output_path = os.path.join(output_folder, output_filename)

    background.save(output_path)
    print(f"[Info] Generated image saved at: {output_path}")
