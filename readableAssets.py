import os
import uuid
import json
from pathlib import Path


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

input_changes = os.environ.get("INPUT_CHANGES")
repo_path = os.environ.get("REPO_PATH")



def set_multiline_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        delimiter = uuid.uuid1()
        print(f'{name}<<{delimiter}', file=fh)
        print(value, file=fh)
        print(delimiter, file=fh)


def set_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'{name}={value}', file=fh)
        




changed_files = json.loads(input_changes)
changed_objects, changed_transitions, changed_others = [], [], []

for changed_file in changed_files:
    if 'objects/' in changed_file:
        changed_objects.append(changed_file)
    elif 'transitions/' in changed_file:
        changed_transitions.append(changed_file)
    else:
        changed_others.append(changed_file)
        




changed_everything = changed_objects + changed_transitions + changed_others


changed_files_message = "\r\n".join(changed_everything)
test_message = "\r\n".join(list_dir(repo_path))

message = f"""

##Test output:
{repo_path}

##Test output:
{test_message}

##Changed files:
{changed_files_message}
"""





        
set_multiline_output("OUTPUT_CHANGES", message)