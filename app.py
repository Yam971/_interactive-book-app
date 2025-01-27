from flask import Flask, render_template, request, send_from_directory
import os
import json
import time
import psutil

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
    monet_execution_time = 0.0
    monet_cpu_usage = 0.0
    renoir_execution_time = 0.0
    renoir_cpu_usage = 0.0

    if child_name:
        # Generate Monet's image with metrics
        proc = psutil.Process()
        proc.cpu_percent(interval=None)  # Initialize CPU measurement
        start_monet = time.time()
        monet_generate(child_name, config)
        monet_execution_time = time.time() - start_monet
        monet_cpu_usage = proc.cpu_percent(interval=None)
        monet_filename = f"Background_{child_name}.png"

        # Generate Renoir's images with metrics
        proc.cpu_percent(interval=None)  # Reset for Renoir
        start_renoir = time.time()
        renoir_image_list = renoir_generate(child_name, config)
        renoir_execution_time = time.time() - start_renoir
        renoir_cpu_usage = proc.cpu_percent(interval=None)

    return render_template(
        'preview.html',
        child_name=child_name,
        gender=gender,
        character=character,
        nb_letters=nb_letters,
        monet_filename=monet_filename,
        renoir_image_list=renoir_image_list,
        monet_version="Monet & Renoir Combined",
        branch_version=config.get("branch", "N/A"),
        monet_execution_time=monet_execution_time,
        monet_cpu_usage=monet_cpu_usage,
        renoir_execution_time=renoir_execution_time,
        renoir_cpu_usage=renoir_cpu_usage
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