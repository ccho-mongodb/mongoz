import yaml
from re import match
from generate_certificate import create_self_signed_cert
from pathlib import Path
import os
import colorama
import subprocess

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
    colorama.init(autoreset=True)
    header_colors = colorama.Fore.GREEN
    setting_colors = colorama.Fore.YELLOW
    hint_colors = colorama.Fore.BLUE
    question_colors = colorama.Fore.WHITE + colorama.Style.BRIGHT
    default_colors = colorama.Fore.CYAN 
    responses = {}
    for q in questions:
        loopPrompt = True
        while loopPrompt:
            try:
                os.system('clear')

                def_val = get_nested_val(q['conf_path'], existing_config) if existing_config else q['default']
                print(header_colors + "mongOz: Configuration Wizard for MongoDB server\n\n")
                print(setting_colors + "Setting: {}\n\n".format(q['conf_path']))
                print(hint_colors + "{}\n\n".format(q['hint']))
                print(question_colors + "{} ".format(q['text']), end='')
                print(default_colors + "[{}]".format(def_val))
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

    if new_token in ["true", "t", "y", "yes"]:
        new_token = True
    elif new_token in ["false", "f", "n", "no"]:
        new_token = False 

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

    # create certificate file
    print ('Creating security certificates...', end='')
    create_self_signed_cert(Path("cert_dir/"))
    print('Created!')

    # start mongod with newly-created config file
    print ('Starting mongod...')
    subprocess.call(['mongod', '--config', 'mongod.conf'])
