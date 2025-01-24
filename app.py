from flask import Flask, render_template, request, send_from_directory
import os
import json
import importlib

app = Flask(__name__)

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Direct imports (you can also import dynamically if you want)
import renoir_V0_1.Renoir_V0_1 as renoir_module
import monet_V0_8.Monet_V0_8 as monet_module

@app.route('/')
def personalize():
    return render_template('personalize.html')

@app.route('/preview')
def preview():
    """
    This route generates TWO images:
      1) Renoir_<child_name>.png
      2) Background_<child_name>.png

    Then shows them both on the preview page.
    """
    child_name = request.args.get('child_name', '')
    gender = request.args.get('gender', '')
    character = request.args.get('character', '')
    nb_letters = 0

    # Generate both images if we have a child name
    renoir_filename = None
    monet_filename = None

    if child_name.strip():
        # 1) Call Renoir
        renoir_module.generate_background_image(child_name.strip(), config)
        renoir_filename = f"Renoir_{child_name}.png"

        # 2) Call Monet
        monet_module.generate_background_image(child_name.strip(), config)
        monet_filename = f"Background_{child_name}.png"

        nb_letters = len(child_name.strip())

    return render_template(
        'preview.html',
        child_name=child_name,
        gender=gender,
        character=character,
        nb_letters=nb_letters,
        renoir_filename=renoir_filename,  # pass to template
        monet_filename=monet_filename,    # pass to template
        # Could pass the version/branch if you want:
        monet_version="Dual (Renoir + Monet)",
        branch_version=config.get("branch", "N/A")
    )

@app.route('/preview-image/<filename>')
def serve_preview_image(filename):
    """
    Serves both Renoir and Monet images from different folders 
    using a single route. We'll decide the folder by inspecting `filename`.
    """
    # 1) If it's "Renoir_<child_name>.png", serve from Renoir folder
    if filename.startswith("Renoir_"):
        folder = config["paths"]["renoir_output"]  # e.g. "renoir_V0_1/generated-preview"
    else:
        # Otherwise, assume it's Monet's. (Could refine logic if needed.)
        folder = config["paths"]["new_output"]     # e.g. "monet_V0_8/generated-preview"

    # Make the path absolute
    full_folder_path = os.path.join(os.path.dirname(__file__), folder)

    return send_from_directory(full_folder_path, filename)

if __name__ == '__main__':
    app.run(debug=True)
