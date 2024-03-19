import os
import uuid
import json
from pathlib import Path
from hashlib import sha256


def list_dir(folderpath = ".", file = False, folder = False, silent = True):
    results = []
    for filename in os.listdir(folderpath):
        fullpath = os.path.join(folderpath, filename)
        if not file and os.path.isfile(fullpath): continue
        if not folder and os.path.isdir(fullpath): continue
        # ext = os.path.splitext(filename)[-1].lower()
        results.append(filename)
        if not silent: print(filename)
    return results

def read_txt(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        text = f.read()
    return text

input_changes = os.environ.get("CHANGES_ALL")
repo_path = Path( os.environ.get("REPO_PATH") )
repo = os.environ.get("REPO")
pr_number = os.environ.get("PRNUM")

var1 = os.environ.get("VAR1")
var2 = os.environ.get("VAR2")

objects_path = repo_path / "objects"


def set_multiline_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        delimiter = uuid.uuid1()
        print(f'{name}<<{delimiter}', file=fh)
        print(value, file=fh)
        print(delimiter, file=fh)


def set_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'{name}={value}', file=fh)
        

def path_to_object_id(p):
    s = p.replace("objects/","").replace(".txt","").replace("\\","").strip()
    if s.isnumeric(): return int(s)
    return -1

objects_dict = {}

def get_object_name_by_id(object_id):
    if object_id in objects_dict.keys(): return objects_dict[object_id]
    object_file_content = read_txt(objects_path / f"{object_id}.txt")
    object_name = object_file_content.splitlines()[1]
    return object_name





# changed_files = json.loads(input_changes)
changed_files = input_changes.splitlines()
changed_objects, changed_transitions, changed_others = [], [], []

for changed_file in changed_files:
    if 'objects/' in changed_file:
        # changed_objects.append(changed_file)
        object_id = path_to_object_id(changed_file)
        if object_id != -1:
            object_name = get_object_name_by_id(object_id)
            hash = sha256(changed_file.replace("\\","").encode('utf-8')).hexdigest()
            changed_objects.append(f"[{object_id}](https://github.com/{repo}/pull/{pr_number}/files#diff-{hash}) {object_name}")
    elif 'transitions/' in changed_file:
        changed_transitions.append(changed_file)
    else:
        changed_others.append(changed_file)
        




changed_everything = changed_objects + changed_transitions + changed_others


changed_files_message = "\r\n".join(changed_everything)
test_message = "\r\n".join(list_dir(repo_path, file=True, folder=True))

message = f"""

{changed_files_message}

"""





        
set_multiline_output("OUTPUT_CHANGES", message)