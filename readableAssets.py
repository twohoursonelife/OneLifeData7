import os
import uuid
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


repo = os.environ.get("REPO")
repo_path = Path( os.environ.get("REPO_PATH") )
pr_number = os.environ.get("PRNUM")

changes_all = os.environ.get("CHANGES_ALL").splitlines()

var1 = os.environ.get("VAR1")
var2 = os.environ.get("VAR2")

objects_path = repo_path / "objects"
transitions_path = repo_path / "transitions"


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
    return -9999

objects_dict = {}

def get_object_name_by_id(object_id):
    if object_id <= 0: return str(object_id)
    if object_id in objects_dict.keys(): return objects_dict[object_id]
    object_file_content = read_txt(objects_path / f"{object_id}.txt")
    object_name = object_file_content.splitlines()[1]
    objects_dict[object_id] = object_name
    return object_name

transitions_dict = {}



object_lines, transition_lines, other_lines = [], [], []

for changed_file in changes_all:
    if 'objects/' in changed_file:
        
        object_id = path_to_object_id(changed_file)
        if object_id != -9999:
            object_name = get_object_name_by_id(object_id)
            hash = sha256(changed_file.replace("\\","").encode('utf-8')).hexdigest()
            object_lines.append(f"[{object_id}](https://github.com/{repo}/pull/{pr_number}/files#diff-{hash}) {object_name}")
            
    elif 'transitions/' in changed_file:
        
        filename = changed_file.replace("transitions/","").replace(".txt","").replace("\\","")
        filename_parts = filename.split("_")
        transition_file_content = read_txt(transitions_path / changed_file)
        transition_file_content_parts = transition_file_content.split()
        
        a = int(filename_parts[0])
        b = int(filename_parts[1])
        c = int(transition_file_content_parts[2])
        d = int(transition_file_content_parts[3])
        
        a_name = get_object_name_by_id(a)
        b_name = get_object_name_by_id(b)
        c_name = get_object_name_by_id(c)
        d_name = get_object_name_by_id(d)
        
        transition_line = f"{a_name} + {b_name} = {c_name} + {d_name}"
        transition_lines.append(transition_line)
        
    else:
        other_lines.append(changed_file)
        




changed_everything = object_lines + transition_lines + other_lines


changed_files_message = "\r\n".join(changed_everything)
test_message = "\r\n".join(list_dir(repo_path, file=True, folder=True))

message = f"""

{changed_files_message}

"""





        
set_multiline_output("OUTPUT_CHANGES", message)