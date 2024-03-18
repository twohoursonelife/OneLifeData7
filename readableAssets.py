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


output = "\r\n".join(changed_files)


        
set_multiline_output("OUTPUT_CHANGES", "### TESTING " + output)