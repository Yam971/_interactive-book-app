import os
import shutil
from PIL import Image

# Points to: monet/assets/girl_type_i/dynamic/transparent-letters/4-letters/
LETTER_IMAGES_FOLDER = os.path.join(
    os.path.dirname(__file__),
    'assets',
    'girl_type_i',
    'dynamic',
    'transparent-letters',
    '4-letters'
)

# Points to: monet/assets/girl_type_i/dynamic/final-background-spread/Background.png
BACKGROUND_FOLDER = os.path.join(
    os.path.dirname(__file__),
    'assets',
    'girl_type_i',
    'dynamic',
    'final-background-spread'
)

# Where the generated image (Background_<Name>.png) will go
OUTPUT_FOLDER = os.path.join(
    os.path.dirname(__file__),
    'generated-preview'
)


def generate_background_image(child_name):
    """
    Generates 'Background_<child_name>.png' by overlaying letter images
    onto the background. Letter images must follow the naming pattern:
        <position>_<uppercase_letter>.png
    The final image is placed into `monet/generated-preview/`.
    """
    # Load the background image
    background_path = os.path.join(BACKGROUND_FOLDER, 'Background.png')
    background = Image.open(background_path).convert("RGBA")

    # For each letter in the child's name, overlay the appropriate image
    for position, letter in enumerate(child_name, start=1):
        letter_filename = f"{position}_{letter.upper()}.png"
        letter_path = os.path.join(LETTER_IMAGES_FOLDER, letter_filename)
        
        if os.path.exists(letter_path):
            letter_image = Image.open(letter_path).convert("RGBA")
            mask = letter_image.split()[3]  # the alpha channel
            background.paste(letter_image, (0, 0), mask)
        else:
            print(f"[Warning] No image for letter '{letter}' at position {position}. Skipping.")

    # Construct the new filename, e.g. Background_Leah.png
    output_filename = f"Background_{child_name}.png"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    background.save(output_path)
    print(f"[Info] Generated image saved at: {output_path}")


if __name__ == "__main__":
    """
    Optional CLI usage:
        python Monet_V0_7.py Leah
    """
    import sys
    if len(sys.argv) > 1:
        name_arg = sys.argv[1]
        generate_background_image(name_arg)
    else:
        print("Usage: python Monet_V0_7.py <ChildName>")
