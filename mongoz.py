import yaml

def load_questions(fn):
    with open(fn) as f:
        # use safe_load instead loabd
        return yaml.safe_load(f)

def add_nested(string, val, dictionary):
    print(string)
    parts = string.split('.', 1)
    if len(parts) > 1:
        branch = dictionary.setdefault(parts[0], {})
        add_nested(parts[1], val, branch)
    else:
        dictionary[parts[0]] = val

def show_prompt(questions):
    responses = {}
    for q in questions:
        print("{} [{}]".format(q['text'], q['default']))
        answer = input() or q['default']

        add_nested(q['conf_path'], answer, responses)
       
        if 'auto_set' in q:
            for setting in q['auto_set']:
                add_nested(setting['conf_path'], setting['value'], responses)

    return responses

if __name__ == "__main__":
    # init
    data = load_questions('questions.yaml')

    # run
    responses = show_prompt(data['questions'])

    # write and exit
    with open('mongod.conf', 'w') as outfile:
        yaml.dump(responses, outfile)
