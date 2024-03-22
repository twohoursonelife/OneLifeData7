import os
import uuid
from pathlib import Path
from hashlib import sha256


### util

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

def set_multiline_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        delimiter = uuid.uuid1()
        print(f'{name}<<{delimiter}', file=fh)
        print(value, file=fh)
        print(delimiter, file=fh)

def set_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'{name}={value}', file=fh)


### processing the inputs

repo = os.environ.get("REPO")
repo_path = Path( os.environ.get("REPO_PATH") )
pr_number = os.environ.get("PRNUM")

changes_all = [e.replace("\\","") for e in os.environ.get("CHANGES_ALL").split("\n")]
changes_deleted = [e.replace("\\","") for e in os.environ.get("CHANGES_DELETED").split("\n")]
changes_added = [e.replace("\\","") for e in os.environ.get("CHANGES_ADDED").split("\n")]

renamed_pairs = os.environ.get("CHANGES_RENAME_PAIRS")

renamed_before, renamed_after = [], []
if ',' in renamed_pairs:
    renamed_pairs = [e.replace("\\","") for e in renamed_pairs.split("\n")]
    renamed_before = [e.split(',')[0] for e in renamed_pairs]
    renamed_after = [e.split(',')[1] for e in renamed_pairs]


### some functions

def path_to_object_id(p):
    s = p.replace("objects/","").replace("categories/","").replace(".txt","").strip()
    if s.isnumeric(): return int(s)
    return -9999

objects_dict = {} # so we read each object only once

def get_object_name_by_id(object_id):
    if object_id <= 0: return str(object_id)
    if object_id in objects_dict.keys(): return objects_dict[object_id]
    object_path = repo_path / "objects" / f"{object_id}.txt"
    # if not object_path.is_file():
    #     object_path = Path("deleted_files") / "objects" / f"{object_id}.txt"
    #     print( object_path )
    object_file_content = read_txt( object_path )
    object_name = object_file_content.splitlines()[1]
    objects_dict[object_id] = object_name
    return object_name


### go through the changed files, summarize each in a line

object_lines, transition_lines, category_lines, other_lines = [], [], [], []

for changed_file in changes_all:
    
    ### whether the change is an added file, or a deleted one, or a modified one
    ### note that renamed files are configured to show as deleted of old and added of new
    sign = "`.`"
    if changed_file in changes_added:
        sign = "`+`"
    elif changed_file in changes_deleted:
        sign = "`-`"
    
    ### the hash is used to link directly to the changed file on github site
    file_change_hash = 0
    if changed_file in renamed_before:
        index = renamed_before.index(changed_file)
        file_change_hash = sha256(renamed_after[index].encode('utf-8')).hexdigest()
    else:
        file_change_hash = sha256(changed_file.encode('utf-8')).hexdigest()
    
    change_processed = False
    
    if 'objects/' in changed_file or 'categories/' in changed_file:
        
        object_id = path_to_object_id(changed_file)
        if object_id != -9999:
            object_name = get_object_name_by_id(object_id)
            object_name = object_name.replace("#", "<span>#</span>")
            if 'objects/' in changed_file:
                object_lines.append(f"{sign} [{object_id}](https://github.com/{repo}/pull/{pr_number}/files#diff-{file_change_hash}) {object_name}")
            elif 'categories/' in changed_file:
                category_lines.append(f"{sign} [{object_id}](https://github.com/{repo}/pull/{pr_number}/files#diff-{file_change_hash}) {object_name}")

            change_processed = True
            
    elif 'transitions/' in changed_file:
        
        filename = changed_file.replace("transitions/","").replace(".txt","")
        filename_parts = filename.split("_")
        
        transition_path = repo_path / "transitions" / f"{filename}.txt"
        # if not transition_path.is_file():
        #     transition_path = Path("deleted_files") / "transitions" / f"{filename}.txt"
        #     print( transition_path )
        transition_file_content = read_txt( transition_path )
        transition_file_content_parts = transition_file_content.split()
        
        a = int(filename_parts[0])
        b = int(filename_parts[1])
        c = int(transition_file_content_parts[0])
        d = int(transition_file_content_parts[1])
        flag = ""
        if len(filename_parts) > 2: flag = "_".join(filename_parts[2:])
        
        a_name = get_object_name_by_id(a)
        b_name = get_object_name_by_id(b)
        c_name = get_object_name_by_id(c)
        d_name = get_object_name_by_id(d)
        
        fields = [
                "a", "b", "c", "d",
                "flag",
                "autoDecaySeconds",
                "actorMinUseFraction",
                "targetMinUseFraction",
                "reverseUseActorFlag",
                "reverseUseTargetFlag",
                "move",
                "desiredMoveDist",
                "noUseActorFlag",
                "noUseTargetFlag"
                ]
        trans_keyValuePairs = []
        
        trans_keyValuePairs.append( (fields[0], a) )
        trans_keyValuePairs.append( (fields[1], b) )
        trans_keyValuePairs.append( (fields[2], c) )
        trans_keyValuePairs.append( (fields[3], d) )
        trans_keyValuePairs.append( (fields[4], flag) )
            
        for i in range(2, len(transition_file_content_parts)):
            trans_keyValuePairs.append( (fields[i+3], transition_file_content_parts[i]) )
        
        if flag != "": flag = f"({flag})"
        
        transition_details = "\r\n".join( [ f"{e[0]}: {e[1]}" for e in trans_keyValuePairs] )
        
        transition_line = f"""
{sign} [{a} + {b} = {c} + {d} {flag}](https://github.com/{repo}/pull/{pr_number}/files#diff-{file_change_hash})
<details>
<summary><code class="notranslate">{a_name}</code> + <code class="notranslate">{b_name}</code> = <code class="notranslate">{c_name}</code> + <code class="notranslate">{d_name}</code></summary>

```yaml
{transition_details}
```

</details>
"""
        transition_lines.append(transition_line)
        change_processed = True
        
    if not change_processed:
        line = f"{sign} [link](https://github.com/{repo}/pull/{pr_number}/files#diff-{file_change_hash}) {changed_file}"
        other_lines.append(line)
        

### assemble the output message

message = ""

if len(object_lines) > 0:
    message += "## Objects:\r\n" + "\r\n".join(object_lines) + "\r\n"

if len(category_lines) > 0:
    message += "## Categories:\r\n" + "\r\n".join(category_lines) + "\r\n"

if len(transition_lines) > 0:
    message += "## Transitions:\r\n" + "".join(transition_lines) + "\r\n"

if len(other_lines) > 0:
    message += "## Others:\r\n" + "\r\n".join(other_lines)
        
set_multiline_output("OUTPUT_MESSAGE", message)