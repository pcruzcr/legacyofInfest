with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('HUERFANAS_PERMITIDAS = {')
if idx >= 0:
    print(f'Found at {idx}')
    brace_count = 0
    in_string = False
    escape = False
    start_idx = content.find('HUERFANAS_PERMITIDAS = {')
    brace_count = 0
    in_string = False
    escape = False
    for i in range(start_idx, len(content)):
        c = content[i]
        if not escape and c == '"' and not in_string:
            in_string = not in_string
        elif not escape and c == '\\':
            escape = True
        else:
            escape = False
        if not in_string:
            if c == '{':
                brace_count += 1
            elif c == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
    print(f'End pos: {end_pos}')
    print(repr(content[end_pos-50:end_pos+50]))
else:
    print('Not found')