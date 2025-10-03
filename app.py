# app.py
# Simple Notes server + UI (Flask)
# Run:
#   python3 -m venv .venv && . .venv/bin/activate
#   pip install flask
#   python3 app.py
# Open http://127.0.0.1:5173

import os, pathlib
from flask import Flask, request, jsonify, render_template

APP_DIR = pathlib.Path(__file__).parent.resolve()
ROOT = (APP_DIR / 'data' / 'BravoServer' / 'Notes').resolve()

# Use your chosen password here (env wins if set)
PASSWORD = os.environ.get('NOTES_PASS', 'Lammyoryammy3#')

NOTES_ROOT_STR = 'BravoServer/Notes'

def strip_notes_root(p: str) -> str:
    """Normalize incoming paths like:
       'BravoServer/Notes' or 'BravoServer/Notes/' or 'BravoServer/Notes/foo/bar'
       -> returns '' or 'foo/bar'
    """
    if not p:
        return ''
    if p.startswith(NOTES_ROOT_STR):
        p = p[len(NOTES_ROOT_STR):]
    return p.lstrip('/').strip()

app = Flask(__name__)

def safe_join(base: pathlib.Path, rel: str) -> pathlib.Path:
    """Prevent path traversal outside ROOT."""
    p = (base / rel).resolve()
    if not str(p).startswith(str(base)):
      raise ValueError('Path escape detected')
    return p

@app.route('/')
def index():
    return render_template('index.html')

@app.post('/api/fileStructure')
def file_structure():
    body = request.get_json(force=True) or {}
    path = body.get('path', NOTES_ROOT_STR)
    rel = strip_notes_root(path)
    base = safe_join(ROOT, rel)
    base.mkdir(parents=True, exist_ok=True)

    directories, files = [], []
    for entry in base.iterdir():
        if entry.is_dir():
            directories.append({'name': entry.name})
        elif entry.is_file() and entry.name.endswith('.md'):
            files.append({'name': entry.name})
    return jsonify({'directories': directories, 'files': files})

@app.post('/api/receiveFile')
def receive_file():
    body = request.get_json(force=True) or {}
    rel = strip_notes_root(body.get('path') or '')
    fp = safe_join(ROOT, rel)
    if not fp.exists() or not fp.is_file():
        return jsonify({'content': ''})
    return jsonify({'content': fp.read_text(encoding='utf-8')})

def require_password():
    body = request.get_json(silent=True) or {}
    if body.get('password') != PASSWORD:
        return jsonify({'error': 'Forbidden'}), 403

@app.post('/api/sendFile')
def send_file():
    rp = require_password()
    if rp: return rp
    body = request.get_json(force=True) or {}
    rel = strip_notes_root(body.get('path') or '')
    content = body.get('content', '')
    fp = safe_join(ROOT, rel)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding='utf-8')
    return jsonify({'ok': True})

@app.post('/api/deleteFile')
def delete_file():
    rp = require_password()
    if rp: return rp
    body = request.get_json(force=True) or {}
    rel = strip_notes_root(body.get('path') or '')
    fp = safe_join(ROOT, rel)
    try:
        if fp.exists():
            fp.unlink()
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'ok': True})

@app.post('/api/createFolder')
def create_folder():
    rp = require_password()
    if rp: return rp
    body = request.get_json(force=True) or {}
    rel = strip_notes_root(body.get('path') or '')
    fp = safe_join(ROOT, rel)
    fp.mkdir(parents=True, exist_ok=True)
    return jsonify({'ok': True})

if __name__ == '__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    app.run(host='127.0.0.1', port=5173, debug=True)

