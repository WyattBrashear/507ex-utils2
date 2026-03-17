import os

from flask import Flask, request, send_from_directory
from werkzeug.utils import secure_filename
import json
import random
import hashlib
import os

app = Flask(__name__)

@app.route('/push', methods=['POST'])
def push():
    print(os.getcwd())
    filename = secure_filename(request.form.get('file_id'))
    with open(f"storage/{filename}.507ex", 'wb') as f:
        f.write(request.files['file'].read())
    with open(f"storage/{filename}.json", 'w') as f:
        secret_code = random.randint(100000, 999999)
        data = {
            'secret_code': hashlib.sha256(str(secret_code).encode()).hexdigest(),
        }
        json.dump(data, f)
    return {
        'status': 'success',
        'secret_code': str(secret_code),
        'url': f'{request.url_root}pull/{filename}'
    }

@app.route('/pull/<file_id>', methods=['POST'])
def pull(file_id):
    try:
        with open(f"storage/{file_id}.json", 'r') as json_file:
            codefile = json.load(json_file)
            secret_code = codefile['secret_code']
    except FileNotFoundError:
        return 'File not found', 404
    if request.form.get('secret_code') == secret_code:
        return send_from_directory('storage', f"{file_id}.507ex", as_attachment=True)
    else:
        return 'Invalid secret code', 401
if __name__ == '__main__':
    app.run()