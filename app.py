from flask import Flask, render_template, request, send_from_directory
import os

app = Flask(__name__)

# 1) Import the new Monet function
#    Adjust the path as needed so Python can find Monet_V0.7 in /monet
#    If your project structure is such that "monet" is a package, do:
#    from monet.Monet_V0_7 import generate_background_image
#    or we might do a sys.path hack if needed. Example:
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'monet'))
from Monet_V0_7 import generate_background_image

# The folder where newly generated images are stored
GENERATED_PREVIEW_FOLDER = os.path.join(
    os.path.dirname(__file__), 
    'monet', 
    'generated-preview'
)

@app.route('/')
def personalize():
    return render_template('personalize.html')

@app.route('/preview')
def preview():
    # 2) Capture form fields
    child_name = request.args.get('child_name')
    gender = request.args.get('gender')
    character = request.args.get('character')
    
    # 3) Call Monet to generate the new image if child_name is provided
    if child_name:
        generate_background_image(child_name.strip())

    # 4) Pass everything into the preview template
    #    (If you want to display the new image, you could pass a filename)
    #    e.g. "Background_Rony.png"
    preview_filename = f"Background_{child_name}.png" if child_name else None

    return render_template(
        'preview.html',
        child_name=child_name,
        gender=gender,
        character=character,
        preview_filename=preview_filename
    )

# 5) OPTIONAL: Provide a route to serve the generated images
#    so you can do <img src="/preview-image/Background_Rony.png"> in preview.html
@app.route('/preview-image/<filename>')
def serve_preview_image(filename):
    return send_from_directory(GENERATED_PREVIEW_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
