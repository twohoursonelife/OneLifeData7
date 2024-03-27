import os
import sys
import uuid
from pathlib import Path
from hashlib import sha256


### inputs

inAction = os.getenv("GITHUB_ACTIONS") is not None

if inAction:
    REPO = os.environ.get("REPO")
    PR_NUM = os.environ.get("PRNUM")
    COMMIT_A = os.environ.get("COMMIT_A")
    COMMIT_B = os.environ.get("COMMIT_B")
else:
    
    args = sys.argv
    
    helpMsg = f"""
Parse asset changes to be more readable.

Usage:
    python {args[0]} <commit_SHA_A> <commit_SHA_B>
    
If no commit_SHA is provided, the script defaults to HEAD~ and HEAD.
If one commit_SHA is provided, the script defaults to commit_SHA~ and commit_SHA.

"""
    
    if len(args) > 3:
        print(helpMsg)
        sys.exit()    

    elif len(args) == 3:
        COMMIT_A = args[1]
        COMMIT_B = args[2]
    elif len(args) == 2:
        COMMIT_B = args[1]
        COMMIT_A = COMMIT_B + "~"
    else:
        print(helpMsg)
        response = input("Input Y to go with the default, diff-ing HEAD~ and HEAD.")
        if response != "Y": sys.exit()
        COMMIT_A = "HEAD~"
        COMMIT_B = "HEAD"
    
    print("\n")


### util

def read_txt(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        text = f.read()
    return text

def read_file_even_deleted(path):
    if not Path(path).is_file():
        recovered_file_content = run_command(f"git show {COMMIT_A}:{path}")
        return recovered_file_content
    return read_txt(path)

def run_command(command):
    f = os.popen(command)
    output = f.read()
    status = f.close()
    if status:
        sys.exit(1)
    return output

def set_multiline_output(name, value):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        delimiter = uuid.uuid1()
        print(f'{name}<<{delimiter}', file=fh)
        print(value, file=fh)
        print(delimiter, file=fh)


### diff-ing the changes

changes_all, changes_deleted, changes_added, renamed_pairs = [], [], [], []

commands = [
    f"git diff --name-only --no-renames {COMMIT_A} {COMMIT_B}",
    f"git diff --diff-filter=D --name-only --no-renames {COMMIT_A} {COMMIT_B}",
    f"git diff --diff-filter=A --name-only --no-renames {COMMIT_A} {COMMIT_B}",
    f"git diff --name-status {COMMIT_A} {COMMIT_B}"
    ]

changes = []

for command in commands:
    output = run_command(command)
    output_list = []
    if output != "":
        output_list = output.strip().split("\n")
    changes.append(output_list)

changes_all, changes_deleted, changes_added, renamed_pairs = changes

if renamed_pairs:
    renamed_pairs = [e.split("\t") for e in renamed_pairs if e[0] == "R"]

renamed_before = [e[1] for e in renamed_pairs]
renamed_after = [e[2] for e in renamed_pairs]


### so we only read each object once

objects_dict = {} 

def get_object_name_by_id(object_id):
    if object_id <= 0: return str(object_id)
    if object_id in objects_dict.keys(): return objects_dict[object_id]
    object_path = f"objects/{object_id}.txt"
    object_file_content = read_file_even_deleted( object_path ).splitlines()
    if len(object_file_content) < 2:
        object_name = str(object_id)
    else:
        object_name = object_file_content[1]
    objects_dict[object_id] = object_name
    return object_name

def read_category_as_object_list(content):
    list_str = content[content.find("\n", content.find("numObjects="))+1:].splitlines()
    list_int = [int(e.split()[0]) for e in list_str]
    return list_int


### go through the changed files, parse object IDs into object names

object_lines, transition_lines, category_lines, other_lines = [], [], [], []

for changed_file in changes_all:
    
    # whether the change is an added file, or a deleted one, or a modified one
    # note that renamed files are configured to show as deleted of old and added of new
    sign = "."
    if changed_file in changes_added:
        sign = "+"
    elif changed_file in changes_deleted:
        sign = "-"
    if inAction:
        sign = f"`{sign}`"
    
    # the hash is used to link to the changed file on github site
    file_hash = 0
    if changed_file in renamed_before:
        index = renamed_before.index(changed_file)
        file_hash = sha256(renamed_after[index].encode('utf-8')).hexdigest()
    else:
        file_hash = sha256(changed_file.encode('utf-8')).hexdigest()
    
    change_processed = False
    
    if 'objects/' in changed_file or 'categories/' in changed_file:
        
        id_str = changed_file.replace("objects/","").replace("categories/","").replace(".txt","").strip()
        if id_str.isnumeric():
            
            object_id = int(id_str)
            object_name = get_object_name_by_id(object_id)
            object_name = object_name.replace("#", "<span>#</span>")
            

            
            if inAction:
                
                if 'categories/' in changed_file:
                    category_before_output = run_command(f"git show {COMMIT_A}:{changed_file}")
                    category_after_output = run_command(f"git show {COMMIT_B}:{changed_file}")
                    
                    if category_before_output != "" and category_after_output != "":
                        category_before = read_category_as_object_list(category_before_output)
                        category_after = read_category_as_object_list(category_after_output)
                        
                        added = list(set(category_after) - set(category_before))
                        removed = list(set(category_before) - set(category_after))
                        
                        category_details = ""
                        if len(added) > 0:
                            category_details += "\n".join( [ f"+ {e} {get_object_name_by_id(e)}" for e in added] )
                        if len(removed) > 0:
                            category_details += "\n".join( [ f"- {e} {get_object_name_by_id(e)}" for e in removed] )
                
                        line = f"""
{sign} [{object_id}](https://github.com/{REPO}/pull/{PR_NUM}/files#diff-{file_hash}) {object_name}
<details>
<summary>Details</summary>

```diff
{category_details}
```

</details>
"""
                else:
                    line = f"{sign} [{object_id}](https://github.com/{REPO}/pull/{PR_NUM}/files#diff-{file_hash}) {object_name}"
                
            else:
                line = f"{sign} {object_id} {object_name}"
                
            if 'objects/' in changed_file:
                object_lines.append(line)
            elif 'categories/' in changed_file:
                category_lines.append(line)

            change_processed = True
            
    elif 'transitions/' in changed_file:
        
        transition_file_content = read_file_even_deleted( changed_file )
        transition_file_content_parts = transition_file_content.split()

        filename_parts = changed_file.replace("transitions/","").replace(".txt","").split("_")
        
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
        
        if inAction:
        
            transition_details = "\n".join( [ f"{e[0]}: {e[1]}" for e in trans_keyValuePairs] )
        
            transition_line = f"""
{sign} [{a} + {b} = {c} + {d} {flag}](https://github.com/{REPO}/pull/{PR_NUM}/files#diff-{file_hash})
<details>
<summary><code class="notranslate">{a_name}</code> + <code class="notranslate">{b_name}</code> = <code class="notranslate">{c_name}</code> + <code class="notranslate">{d_name}</code></summary>

```yaml
{transition_details}
```

</details>
"""
        else:
            transition_line = f"{sign} {a} + {b} = {c} + {d} {flag}\n{a_name} + {b_name} = {c_name} + {d_name} {flag}\n\n"

        transition_lines.append(transition_line)
        change_processed = True
        
    if not change_processed:
        if inAction:
            line = f"{sign} [link](https://github.com/{REPO}/pull/{PR_NUM}/files#diff-{file_hash}) {changed_file}"
        else:
            line = f"{sign} {changed_file}"
        other_lines.append(line)


### assemble the output message

message = ""

if len(object_lines) > 0:
    message += "## Objects:\n\n" + "\n".join(object_lines) + "\n\n"

if len(category_lines) > 0:
    message += "## Categories:\n\n" + "\n".join(category_lines) + "\n\n"

if len(transition_lines) > 0:
    message += "## Transitions:\n\n" + "".join(transition_lines) + "\n\n"

if len(other_lines) > 0:
    message += "## Others:\n\n" + "\n".join(other_lines)
        

if inAction:
    set_multiline_output("OUTPUT_MESSAGE", message)
else:
    print(message)