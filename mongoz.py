import yaml
import re

def load_questions(fn):
    with open(fn) as f:
        # use safe_load instead loabd
        return yaml.safe_load(f)

def add_nested(string, val, dictionary):
    parts = string.split('.', 1)
    if len(parts) > 1:
        branch = dictionary.setdefault(parts[0], {})
        add_nested(parts[1], val, branch)
    else:
        dictionary[parts[0]] = val

def show_prompt(questions):
    responses = {}
    for q in questions:
        result = None
        while result is None:
            try:
                print("{} [{}]".format(q['text'], q['default']))
                answer = input() or q['default']
                
                if 'validate' in q:
                    print("validate value: {}".format(q['validate']))
                    if q['validate'] == 'boolean':
                        answer = validate_and_format_boolean(answer)
                    elif q['validate'] == 'port_number':
                        answer = validate_and_format_port_number(answer)

                result = answer
            except Exception as e:
                print("{}\n".format(e))
                pass

        add_nested(q['conf_path'], result, responses)
       
        if 'auto_set' in q:
            for setting in q['auto_set']:
                add_nested(setting['conf_path'], setting['value'], responses)

    return responses

def validate_and_format_boolean(token):
    new_token = str(token).lower().replace(" ", "")
    matches = re.match(r"^(true|false|t|f|y|n|yes|no)$", new_token)
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
    # init
    data = load_questions('questions.yaml')

    # run
    responses = show_prompt(data['questions'])

    # write and exit
    with open('mongod.conf', 'w') as outfile:
        yaml.dump(responses, outfile)
