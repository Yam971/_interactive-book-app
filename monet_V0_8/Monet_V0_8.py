import os
import re
from PIL import Image

def generate_background_image(child_name, config):
    """
    Generates 'Background_<child_name>.png' by overlaying smaller letter images
    onto the background. Now supports:
      - Dynamic letter spacing based on name length
      - Multiple variations per letter (e.g., E.png, E1.png, E2.png) for
        repeated occurrences of the same letter.
    """

    # Extract relevant config paths
    background_path = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_background"].replace("monet_V0_8/", "")
    )
    letters_folder = os.path.join(
        os.path.dirname(__file__),
        config["paths"]["new_letters"].replace("monet_V0_8/", "")
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

    # Turn child's name into a list of characters
    # (In production, consider filtering out spaces/punctuation if desired)
    letters_in_name = [char for char in child_name]
    if not letters_in_name:
        print("[Warning] Child name is empty, nothing to generate.")
        return

    # 1) PREPARE LETTER VARIATIONS
    # We'll build a dictionary that maps the UPPERCASE letter (e.g. 'E') => list of variation files
    # Then, for each occurrence of that letter, we cycle through the list.

    # This function scans the folder for all files that match e.g. E.png, E1.png, E2.png, ...
    # and returns them sorted in ascending order (so E.png, E1.png, E2.png, ...)
    def get_variations_for_letter(letter_char: str):
        # letter_char is uppercase, e.g. 'E'
        variation_files = []
        for filename in os.listdir(letters_folder):
            # We'll do a simple pattern: it starts with the letter (like 'E') 
            # and ends with .png, possibly with a digit or digits in between.
            # Examples that match: E.png, E1.png, E2.png
            # Examples that do NOT match: E-something.png, or e1.png
            pattern = f"^{letter_char}(\\d*)\\.png$"
            if re.match(pattern, filename):
                variation_files.append(filename)
        
        # If we have no matches (e.g. letter_char + any digits), 
        # maybe there's a base file "E.png"? Let's check that too
        # But the above pattern already includes E.png, because the group (\d*) can be empty
        # So if none found, we could also check if 'E.png' is there. 
        # But the code above does that, so we might be good.

        # Sort them so that "E.png" < "E1.png" < "E2.png" etc.
        variation_files.sort()

        # If we found none, we might check for exactly letter_char + ".png" 
        # (But the pattern above already includes that if it exists.)
        # Return the full paths
        full_paths = [
            os.path.join(letters_folder, vf)
            for vf in variation_files
        ]
        return full_paths

    # We'll cache these variations to avoid scanning repeatedly
    variations_cache = {}

    def get_letter_variations(letter_char):
        """
        Return the list of variation image paths for the given uppercase letter_char.
        If none exist, returns an empty list.
        """
        if letter_char not in variations_cache:
            variations_cache[letter_char] = get_variations_for_letter(letter_char)
        return variations_cache[letter_char]

    # 2) DETERMINE LETTER SPACING (already present logic from config)
    spacing_dict = config.get("letter_spacing_per_length", {})
    default_spacing = config.get("default_letter_spacing_px", 0)
    num_letters_in_name = len(letters_in_name)
    letter_spacing = spacing_dict.get(str(num_letters_in_name), default_spacing)

    # We'll load each letter's image(s), keep track of the images we actually will composite.
    # For repeated letters, we cycle their variation index.

    # We'll store a list of (image, width) for each occurrence of each letter
    # in the order we plan to paste them.
    images_to_composite = []

    # We'll track how many times we've seen each uppercase letter so far
    # so we know which variation index to use next.
    occurrence_counter = {}

    for char in letters_in_name:
        uppercase_char = char.upper()

        # Get all variation paths for this letter (could be 1 or many)
        variation_paths = get_letter_variations(uppercase_char)
        if not variation_paths:
            # If no match found, we skip or look for a fallback like 'A.png' 
            # But to keep it simple: skip with a warning
            print(f"[Warning] No variations found for letter '{char}'. Skipping.")
            continue
        
        # We track how many times we've encountered this letter
        occurrence_counter[uppercase_char] = occurrence_counter.get(uppercase_char, 0) + 1
        occurrence_index = occurrence_counter[uppercase_char] - 1  # zero-based index

        # The variation list might be shorter than the number of occurrences, so we cycle
        chosen_variation = variation_paths[occurrence_index % len(variation_paths)]

        # Open that variation
        letter_img = Image.open(chosen_variation).convert("RGBA")
        images_to_composite.append(letter_img)

    # If no images end up in images_to_composite, there's nothing to do
    if not images_to_composite:
        print("[Warning] No valid letters loaded, skipping generation.")
        return

    # Calculate the total width of all chosen images + spacing
    letter_widths = [img.size[0] for img in images_to_composite]
    sum_letter_widths = sum(letter_widths)
    total_spacing = (len(images_to_composite) - 1) * letter_spacing
    total_width = sum_letter_widths + total_spacing

    # Centering horizontally
    x_start = (bg_width - total_width) // 2
    top_y = 0  # if you want an option for top alignment from config, do: config.get("top_alignment_y", 0)

    # Composite each image at the correct X
    current_x = x_start
    for img in images_to_composite:
        background.alpha_composite(img, dest=(current_x, top_y))
        current_x += img.size[0] + letter_spacing

    # Finally, save as "Background_<child_name>.png"
    output_filename = f"Background_{child_name}.png"
    output_path = os.path.join(output_folder, output_filename)
    background.save(output_path)
    print(f"[Info] Generated image saved at: {output_path}")
