from flask import Flask, render_template, request, send_from_directory
import os
import json

app = Flask(__name__)

# 1) Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# 2) Import Monet & Renoir modules
from monet_V0_8.Monet_V0_8 import generate_background_image as monet_generate
from renoir_V0_1.Renoir_V0_1 import generate_progressive_images as renoir_generate

@app.route('/')
def personalize():
    return render_template('personalize.html')

@app.route('/preview')
def preview():
    """
    Generates:
      - One Monet image: Background_<child_name>.png
      - Multiple Renoir images: Renoir_<child_name>_step1..stepX.png
    Displays all on the preview page.
    """
    child_name = request.args.get('child_name', '').strip()
    gender = request.args.get('gender', '')
    character = request.args.get('character', '')
    nb_letters = len(child_name)

    monet_filename = None
    renoir_image_list = []

    if child_name:
        # 1) Generate Monet’s single overlay
        monet_generate(child_name, config) 
        monet_filename = f"Background_{child_name}.png"

        # 2) Generate Renoir’s progressive images
        renoir_image_list = renoir_generate(child_name, config)

    return render_template(
        'preview.html',
        child_name=child_name,
        gender=gender,
        character=character,
        nb_letters=nb_letters,
        # Monet single image
        monet_filename=monet_filename,
        # Renoir multiple images
        renoir_image_list=renoir_image_list,
        # Additional info
        monet_version="Monet & Renoir Combined",
        branch_version=config.get("branch", "N/A")
    )

@app.route('/preview-image/<filename>')
def serve_preview_image(filename):
    """
    Serve both Monet and Renoir images from different folders using 
    the same route. We'll guess which folder by the filename.
    """
    if filename.startswith("Renoir_"):
        folder = config["paths"]["renoir_output"]  # e.g. "renoir_V0_1/generated-preview"
    else:
        # Assume it's Monet's (Background_<child_name>.png, etc.)
        folder = config["paths"]["new_output"]      # e.g. "monet_V0_8/generated-preview"

    full_folder_path = os.path.join(os.path.dirname(__file__), folder)
    return send_from_directory(full_folder_path, filename)

if __name__ == '__main__':
    app.run(debug=True)
