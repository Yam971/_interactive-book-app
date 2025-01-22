from flask import Flask, render_template, request, send_from_directory
import os
import json
import importlib

app = Flask(__name__)

# 1) Load the config file at startup
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

use_new_monet = config["use_new_monet"]
branch_version = config.get("branch", "N/A")

# Dynamically import the chosen Monet module
if use_new_monet:
    monet_module_path = config["monet_v0_8_module"]
    monet_version_string = "Monet_V0_8"
else:
    monet_module_path = config["monet_v0_7_module"]
    monet_version_string = "Monet_V0_7"

monet_module = importlib.import_module(monet_module_path)
generate_background_image = monet_module.generate_background_image

# Output folder depends on whether we're using old or new
if use_new_monet:
    GENERATED_PREVIEW_FOLDER = config["paths"]["new_output"]
else:
    GENERATED_PREVIEW_FOLDER = config["paths"]["old_output"]

GENERATED_PREVIEW_FOLDER = os.path.join(os.path.dirname(__file__), GENERATED_PREVIEW_FOLDER)

@app.route('/')
def personalize():
    return render_template('personalize.html')

@app.route('/preview')
def preview():
    # Grab query parameters
    child_name = request.args.get('child_name')
    gender = request.args.get('gender')
    character = request.args.get('character')

    if child_name:
        # Generate the new image
        generate_background_image(child_name.strip(), config)
        nb_letters = len(child_name.strip())
    else:
        nb_letters = 0

    preview_filename = f"Background_{child_name}.png" if child_name else None

    return render_template(
        'preview.html',
        child_name=child_name,
        gender=gender,
        character=character,
        preview_filename=preview_filename,
        nb_letters=nb_letters,
        monet_version=monet_version_string,
        branch_version=branch_version
    )

@app.route('/preview-image/<filename>')
def serve_preview_image(filename):
    return send_from_directory(GENERATED_PREVIEW_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
