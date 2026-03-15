import os
import sys
from flask import Flask, send_from_directory

base_dir = os.path.dirname(os.path.abspath(__file__))
html_dir = os.path.join(base_dir, 'html')

app = Flask(__name__)

def serve_html(filename):
    """Serve HTML file directly — bypasses Jinja2 to avoid template conflicts."""
    return send_from_directory(html_dir, filename, mimetype='text/html')

@app.route('/')
def index():
    return serve_html('index.html')

@app.route('/dashboard')
def dashboard():
    return serve_html('dashboard.html')

@app.route('/rooms')
def rooms():
    return serve_html('rooms.html')

@app.route('/chat')
def chat():
    return serve_html('chat.html')

@app.route('/bots')
def bots():
    return serve_html('bots.html')

@app.route('/_layout.js')
def layout_js():
    return send_from_directory(html_dir, '_layout.js',
                               mimetype='application/javascript')

if __name__ == '__main__':
    if not os.path.exists(html_dir):
        print(f"\033[31m[!] HTML directory not found: {html_dir}\033[0m")
        sys.exit(1)
    print("\033[1;32m[*] XtermChat Web Admin starting...\033[0m")
    print("[*] URL: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)