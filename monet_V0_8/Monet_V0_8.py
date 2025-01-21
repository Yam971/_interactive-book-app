import os
from PIL import Image

def generate_background_image(child_name, config):
    """
    Generates 'Background_<child_name>.png' by overlaying letter images onto 
    the background. Unlike Monet_V0_7, we only have one letter image per letter 
    (e.g. 'A.png', 'B.png', etc.), so we must compute x-coordinates dynamically.
    """

    # Read relevant paths from the config
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

    # Create output folder if not exists
    os.makedirs(output_folder, exist_ok=True)

    # Load the background
    background = Image.open(background_path).convert("RGBA")
    bg_width, bg_height = background.size

    # Read letter spacing from config (fallback to 20 if not found)
    letter_spacing = config.get("letter_spacing_px", 20)
    top_y = config.get("top_alignment_y", 0)

    # The child's name might contain spaces or special chars. We'll loop letter by letter
    # Filter out spaces if you don’t want them rendered. Or handle hyphens, accented letters, etc.
    # For simplicity, assume each character has a corresponding image (like "É.png").
    # You might need a fallback if the file doesn't exist.

    letters = [char for char in child_name]  # or some custom logic

    # Load each letter image to measure total width
    loaded_letters = []
    total_width = 0
    for i, char in enumerate(letters):
        letter_filename = f"{char.upper()}.png"  # e.g. 'A.png', 'B.png'
        letter_path = os.path.join(letters_folder, letter_filename)
        if not os.path.exists(letter_path):
            print(f"[Warning] Missing letter image for '{char}'. Skipping.")
            continue
        letter_img = Image.open(letter_path).convert("RGBA")
        loaded_letters.append((char, letter_img))

    # Now that we have the valid letters, measure total needed width
    # total = sum of widths + spacing*(len-1)
    num_letters = len(loaded_letters)
    if num_letters == 0:
        print("[Warning] No letters to place.")
        return

    # Measure individual widths
    letter_widths = [img.size[0] for _, img in loaded_letters]
    # total width of letters
    sum_letter_widths = sum(letter_widths)
    # total spacing is spacing*(N-1)
    sum_spacing = letter_spacing * (num_letters - 1)

    total_width = sum_letter_widths + sum_spacing

    # The leftmost letter’s x-position so that the block is centered
    x_start = int((bg_width - total_width) / 2)

    # Composite each letter in place
    current_x = x_start
    for (char, letter_img), width in zip(loaded_letters, letter_widths):
        # Paste letter at (current_x, top_y)
        background.alpha_composite(letter_img, dest=(current_x, top_y))
        # Move x for next letter
        current_x += width + letter_spacing

    # Finally, save as "Background_<child_name>.png"
    output_filename = f"Background_{child_name}.png"
    output_path = os.path.join(output_folder, output_filename)
    background.save(output_path)
    print(f"[Info] Generated image saved at: {output_path}")
