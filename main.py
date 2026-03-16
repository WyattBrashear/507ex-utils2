import argparse
import os
import sys
import shutil
import hashlib
import subprocess
import zipfile
import requests
import uuid
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['build', 'upload', 'exec', 'unpack'], help='The operation to perform.')
parser.add_argument('path', help='The path to the Executable or folder')
args = parser.parse_args()

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
    current_path = os.getcwd()
    reading_depends = False
    has_depends = False
    dependency_platform = ''
    with open(path, 'rb') as f:
        if f.readline() != b'FZX2\n':
            raise ValueError('Invalid Executable!')
        for line in f:
            if line.startswith(b'!507EX-END-META'):
                break
            if line.startswith(b'507ex-hash'):
                exec_hash = line.split(b'|')[1].decode()
            if line.startswith(b'507ex-hashmode'):
                exec_hashmode = line.split(b'|')[1].decode()
            if line.startswith(b'507ex-id'):
                exec_id = line.split(b'|')[1].decode()
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
    os.makedirs(f'{current_path}/.fzx2-runtime/{exec_id}', exist_ok=True)

    with zipfile.ZipFile(f"{current_path}{path}", 'r') as zippy:
        zippy.extractall()
if args.mode == 'build':
    build(args.path)
if args.mode == 'exec':
    execute(args.path)