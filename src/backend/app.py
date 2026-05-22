import json
import os
import time
import urllib.request

from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')

try:
    from .tiles import tiles_bp
    from .glyphs import glyphs_bp
    from .sprites import sprites_bp
except ImportError:
    from tiles import tiles_bp  # type: ignore[no-redef]  # direct invocation
    from glyphs import glyphs_bp  # type: ignore[no-redef]
    from sprites import sprites_bp  # type: ignore[no-redef]
app.register_blueprint(tiles_bp)
app.register_blueprint(glyphs_bp)
app.register_blueprint(sprites_bp)


@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


_report_rate: dict[str, float] = {}

@app.route('/api/report', methods=['POST'])
def report_issue():
    token = os.environ.get('GITHUB_TOKEN', '')
    if not token:
        return jsonify(error='Reporting is not configured on this server.'), 503

    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    now = time.time()
    if now - _report_rate.get(ip, 0) < 300:
        return jsonify(error='You already submitted a report recently. Try again in a few minutes.'), 429
    _report_rate[ip] = now

    data = request.get_json(silent=True) or {}
    description = (data.get('description') or '').strip()
    context = (data.get('context') or '').strip()[:1000]

    if not description:
        return jsonify(error='Description is required.'), 400
    if len(description) > 4000:
        return jsonify(error='Description is too long.'), 400

    first_line = description.split('\n', 1)[0].strip()
    title = (first_line[:77] + '…' if len(first_line) > 80 else first_line) or 'Site feedback'
    body = '\n'.join([
        description, '',
        '---',
        '<sub>',
        context,
        f'· user-agent: {request.headers.get("User-Agent", "unknown")}',
        '</sub>',
    ])

    payload = json.dumps({'title': title, 'body': body, 'labels': ['claude']}).encode()
    req = urllib.request.Request(
        'https://api.github.com/repos/eddielathamjones/map-tile-interceptor/issues',
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            issue = json.loads(resp.read())
        return jsonify(ok=True, issue_number=issue.get('number'))
    except Exception:
        return jsonify(error='Could not reach GitHub. Try again later.'), 502


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5003))
    app.run(debug=True, host='0.0.0.0', port=port)
