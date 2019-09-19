import yaml
from re import match
from generate_certificate import create_self_signed_cert
from pathlib import Path
import os

def load_yaml(fn):
    with open(fn) as f:
        return yaml.safe_load(f)

def get_nested_val(path, config):
    parts = path.split('.')

    curr_key = config[parts[0]]
    parts = parts[1:]
    while len(parts) > 0:
        curr_key = curr_key[parts[0]]
        parts = parts[1:]

    return curr_key

def add_nested_val(path, val, dictionary):
    parts = path.split('.', 1)
    if len(parts) > 1:
        branch = dictionary.setdefault(parts[0], {})
        add_nested_val(parts[1], val, branch)
    else:
        dictionary[parts[0]] = val

def show_prompt(questions, existing_config):
    responses = {}
    for q in questions:
        loopPrompt = True
        while loopPrompt:
            try:
                os.system('clear')
                def_val = get_nested_val(q['conf_path'], existing_config) if existing_config else q['default']
                print("mongOz\n\n")
                print("Setting: {}\n\n{}\n\n".format(q['conf_path'], q['hint']))

                print("{} [{}]".format(q['text'], def_val))
                answer = input() or def_val
                
                if 'validate' in q:
                    if q['validate'] == 'boolean':
                        answer = validate_and_format_boolean(answer)
                    elif q['validate'] == 'port_number':
                        answer = validate_and_format_port_number(answer)

                result = answer
                loopPrompt = False
            except Exception as e:
                print("{}\n".format(e))
                pass

        add_nested_val(q['conf_path'], result, responses)
       
        if 'auto_set' in q:
            for setting in q['auto_set']:
                add_nested_val(setting['conf_path'], setting['value'], responses)

    return responses

def validate_and_format_boolean(token):
    new_token = str(token).lower().replace(" ", "")
    matches = match(r"^(true|false|t|f|y|n|yes|no)$", new_token)
    if not matches:
        raise Exception("Invalid input: {}".format(token))

    if new_token in ["t", "y", "yes"]:
        new_token = "true"
    elif new_token in ["f", "n", "no"]:
        new_token = "false" 

    return new_token

def validate_and_format_port_number(token):
    try:
        new_token = int(token)
    except ValueError:
        raise Exception("Invalid input: {}".format(token))

    if not (1024 < new_token < 49151):
        raise Exception("Please use a registered port between 1024 and 49151")

    return new_token

if __name__ == "__main__":
    # create certificate file
    create_self_signed_cert(Path("cert_dir/"))

    existing_config = None
    # init
    if Path('mongod.conf').exists():
        print('Updating your existing mongo.conf file.')
        existing_config = load_yaml('mongod.conf')

    question_data = load_yaml('questions.yaml')

    # run wizard
    responses = show_prompt(question_data['questions'], existing_config)

    # write and exit
    with open('mongod.conf', 'w') as outfile:
        yaml.dump(responses, outfile)

    print('Configuration file written to mongod.conf')
