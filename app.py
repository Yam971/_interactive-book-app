import os
import json
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

# 1) Load the config file once at startup
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

use_new_monet = config["use_new_monet"]

# 2) Depending on config, dynamically import the chosen Monet module
import importlib

if use_new_monet:
    monet_module_path = config["monet_v0_8_module"]  # e.g. "monet_V0_8.Monet_V0_8"
else:
    monet_module_path = config["monet_v0_7_module"]  # e.g. "monet.Monet_V0_7"

monet_module = importlib.import_module(monet_module_path)

# We assume the chosen module has a function called generate_background_image
generate_background_image = monet_module.generate_background_image


# The folder where newly generated images are stored (point to old or new output)
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
    child_name = request.args.get('child_name')
    gender = request.args.get('gender')
    character = request.args.get('character')

    if child_name:
        # Call the correct Monet function
        generate_background_image(child_name.strip(), config)

    preview_filename = f"Background_{child_name}.png" if child_name else None

    return render_template(
        'preview.html',
        child_name=child_name,
        gender=gender,
        character=character,
        preview_filename=preview_filename
    )


@app.route('/preview-image/<filename>')
def serve_preview_image(filename):
    return send_from_directory(GENERATED_PREVIEW_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True)
