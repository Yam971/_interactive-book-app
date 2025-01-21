import os
from PIL import Image

def generate_background_image(child_name, config):
    """
    Generates 'Background_<child_name>.png' by overlaying smaller letter images
    onto the background. 
    Now, the letter spacing depends on the length of the child's name, as defined
    in config["letter_spacing_per_length"].
    """

    # Extract relevant config paths
    # Here we remove "monet_V0_8/" if it's included in the path stored in config,
    # because we assume the code inside 'monet_V0_8/' references local subfolders.
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

    # Load the child's name letters (e.g., handle spaces or special chars as needed)
    letters = [char for char in child_name]  # basic approach: one image per character
    if not letters:
        print("[Warning] Child name is empty, nothing to generate.")
        return

    # Attempt to load each letter image
    loaded_letters = []
    for char in letters:
        # Convert to uppercase for your naming convention, e.g. 'A.png'
        letter_filename = f"{char.upper()}.png"
        letter_path = os.path.join(letters_folder, letter_filename)
        if os.path.exists(letter_path):
            letter_img = Image.open(letter_path).convert("RGBA")
            loaded_letters.append((char, letter_img))
        else:
            print(f"[Warning] Missing letter image for '{char}'. Skipping.")

    if not loaded_letters:
        print("[Warning] No valid letters found, nothing to place.")
        return

    # Determine the name length (just for the letters we actually loaded)
    num_letters = len(loaded_letters)

    # Read the spacing dictionary from config
    spacing_dict = config.get("letter_spacing_per_length", {})
    default_spacing = config.get("default_letter_spacing_px", 0)
    # If the length is in the dict, use that spacing; otherwise use the default
    letter_spacing = spacing_dict.get(str(num_letters), default_spacing)

    # Gather widths of each letter image
    letter_widths = [img.size[0] for (_, img) in loaded_letters]
    sum_letter_widths = sum(letter_widths)
    # total spacing is (num_letters - 1) * letter_spacing
    total_spacing = (num_letters - 1) * letter_spacing
    total_width = sum_letter_widths + total_spacing

    # Compute the x_start so that the text is horizontally centered
    x_start = (bg_width - total_width) // 2

    # For top alignment, you could also define "top_alignment_y" in config if you want
    top_y = 0  # or config.get("top_alignment_y", 0)

    # Composite each letter onto the background at the correct X
    current_x = x_start
    for (_, letter_img), w in zip(loaded_letters, letter_widths):
        background.alpha_composite(letter_img, dest=(current_x, top_y))
        current_x += w + letter_spacing

    # Save the final image
    output_filename = f"Background_{child_name}.png"
    output_path = os.path.join(output_folder, output_filename)
    background.save(output_path)
    print(f"[Info] Generated image saved at: {output_path}")
