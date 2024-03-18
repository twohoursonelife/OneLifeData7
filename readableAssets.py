import os
import uuid
import json

input_changes = os.environ.get("INPUT_CHANGES")


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

output = "\r\n".join(changed_everything)


        
set_multiline_output("OUTPUT_CHANGES", output)