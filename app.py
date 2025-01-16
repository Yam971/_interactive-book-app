from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def personalize():
    return render_template('personalize.html')

@app.route('/preview')
def preview():
    # Get query parameters
    child_name = request.args.get('child_name')
    gender = request.args.get('gender')
    character = request.args.get('character')

    # For testing, display the selected values
    return f"""
    <h1>Preview Page</h1>
    <p>Child's Name: {child_name}</p>
    <p>Gender: {gender}</p>
    <p>Character: {character}</p>
    """

if __name__ == '__main__':
    app.run(debug=True)
