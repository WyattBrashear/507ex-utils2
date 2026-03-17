import argparse
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime

import requests
from flask import Flask, request, send_from_directory
from werkzeug.utils import secure_filename

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['build', 'upload', 'exec', 'unpack', 'start_server'], help='The operation to perform.')
parser.add_argument('path', help='The path to the Executable or folder')
args = parser.parse_args(sys.argv[1:])
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
#Alright. Lets rewrite this format!
def build(directory: str):
    #Check for a runfile in the directory
    if not os.path.exists(os.path.join(directory, 'runfile')):
        raise FileNotFoundError('No Runfile Detected!')
    depend_file = False
    if os.path.exists(os.path.join(directory, 'dependfile')):
        depend_file = True
        with open(os.path.join(directory, 'dependfile'), 'r') as f:
            dependencies = f.read()
    shutil.make_archive(directory, 'zip', directory)
    os.rename(f"{directory}.zip", f"{directory}.507ex")
    with open (f"{directory}.507ex", 'rb') as f:
        exec_contents = f.read()
    #Calculate hash
    hashfunc = hashlib.new('blake2s')
    with open(f"{directory}.507ex", 'rb') as f:
        while chunk := f.read(8192):
            hashfunc.update(chunk)
        exec_hash = hashfunc.hexdigest()

    with open(f"{directory}.507ex", 'wb') as f:
        f.write("FZX2".encode())
        f.write("\n!507EX-METADATA".encode())
        f.write(f"\n507ex-hash|{exec_hash}".encode())
        f.write(f"\n507ex-hashmode|blake2s".encode())
        f.write(f"\n507ex-id|{uuid.uuid4()}".encode())
        #DTOC - Date/Time of Creation
        f.write(f"\n507ex-dtoc|{datetime.now().now()}".encode())
        f.write(f"\n507ex-depends|{depend_file}".encode())
        f.write(f"\n!507EX-DEPENDENCIES\n{dependencies}".encode())
        f.write("\n!507EX-END-META\n".encode())
        f.write(exec_contents)
    print(f"Successfully built {directory}.507ex")

def execute(path: str):
    print(path)
    current_path = os.getcwd()
    reading_depends = False
    has_depends = False
    dependency_platform = ''
    fromcar = False
    #CAR Server logic
    if path.startswith("http://") or path.startswith("https://"):
        r = requests.post(path, data={'secret_code': hashlib.sha256(str(input("Please enter the secret code: \n")).encode()).hexdigest()})
        if r.status_code == 401:
            print("Your Secret Code is invalid!")
        with open("tmp.507ex", 'wb') as f:
            f.write(r.content)
        fromcar = True
        path = "tmp.507ex"
    with open(path, 'rb') as f:
        if f.readline() != b'FZX2\n':
            raise ValueError('Invalid Executable!')
        line_counter = 0
        for line in f:
            if line.startswith(b'!507EX-END-META'):
                break
            if line.startswith(b'507ex-hash|'):
                exec_hash = line.split(b'|')[1].decode().replace('\n', '')
            if line.startswith(b'507ex-hashmode'):
                exec_hashmode = line.split(b'|')[1].decode().replace('\n', '')
            if line.startswith(b'507ex-id'):
                exec_id = line.split(b'|')[1].decode().replace('\n', '')
            if line.startswith(b'507ex-depends'):
                if line.split(b'|')[1].decode() == 'True\n':
                    if input("Executable has dependencies that it wants to install. Continue? (y/n)\n").lower() == 'y':
                        has_depends = True
                    else:
                        raise ValueError('Aborted!')
                else:
                    has_depends = False
            if reading_depends:
                if line.startswith(b'!') and not line.startswith(b'!PLATFORM'):
                    command = line.split(b'|')[1].decode().replace('\n', '')
                if dependency_platform == sys.platform or dependency_platform == '*':
                    arg = line.decode().replace('\n', '')
                    subprocess.run(f"{command} {arg}", shell=True, check=False)
                if line.startswith(b'!PLATFORM'):
                    dependency_platform = line.decode().replace('\n', '').replace('!PLATFORM ', '')
            if line.startswith(b'!507EX-DEPENDENCIES'):
                if has_depends:
                    reading_depends = True
            line_counter += 1
    os.makedirs(f'{current_path}/.fzx2-runtime/{exec_id}', exist_ok=True)
    #Hash the executable
    line_counter +=2
    with open(path, 'rb') as f:
        lines = b''.join(f.readlines()[line_counter:])
        file_hash = hashlib.new(exec_hashmode, lines).hexdigest()
    pass_hashcheck = False
    if file_hash == exec_hash:
        pass_hashcheck = True
    else:
        raise ValueError('Hash Verification Failed. Executable may have been damaged.')
    os.chdir(f'{current_path}/.fzx2-runtime/{exec_id}')
    with zipfile.ZipFile(f"{current_path}/{path}", 'r') as zippy:
        zippy.extractall()
    with open("runfile", 'r') as runfile:
        runfile_contents = runfile.read()
    subprocess.run(runfile_contents, shell=True, check=False)
    #cleanup
    os.chdir('..')
    shutil.rmtree(f'{current_path}/.fzx2-runtime/{exec_id}')
    if fromcar:
        os.remove(f"{current_path}/tmp.507ex")

def upload(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError('File not found!')
    url = input("Please enter the server address: \n")
    with open(path, 'rb') as f:
        for line in f:
            if line.startswith(b'507ex-id|'):
                exec_id = line.split(b'|')[1].decode()
                break
    with open(path, 'rb') as f:
        r = requests.post(f"{url}/push", files={'file': f}, data={'file_id': exec_id})
    json_data = r.json()
    print('Upload Complete!')
    print(f"Upload URL: {json_data['url']}")
    print(f"Your Secret Code Is: {json_data['secret_code']}")
def unpack(path: str):
    os.mkdir(path)
    os.chdir(path)
    with zipfile.ZipFile(path, 'r') as zippy:
        zippy.extractall()
if args.mode == 'build':
    build(args.path)
if args.mode == 'exec':
    execute(args.path)
if args.mode == 'upload':
    upload(args.path)
if args.mode == 'unpack':
    unpack(args.path)
if args.mode == 'start_server':
    app.run()