import os
import sys
from flask import Flask, render_template

# Setup paths
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'html')

# Initialize Flask with custom template folder
app = Flask(__name__, template_folder=template_dir)

@app.route('/')
def index():
    """Halaman login/join session."""
    return render_template('index.html')

@app.route('/chat')
def chat():
    """Halaman interface chat interaktif."""
    return render_template('chat.html')

if __name__ == '__main__':
    # Validasi keberadaan folder template sebelum running
    if not os.path.exists(template_dir):
        print(f"\033[31m[!] CRITICAL ERROR: Template directory not found at {template_dir}\033[0m")
        sys.exit(1)

    print("\033[1;32m[*] XtermChat Web Server is starting...\033[0m")
    print(f"[*] Template Path : {template_dir}")
    print("[*] Local Access  : http://localhost:5000")
    
    # Run the web server
    app.run(host='0.0.0.0', port=5000, debug=False)