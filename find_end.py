with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('HUERFANAS_PERMITIDAS = {')
if idx >= 0:
    print(f'Found at {idx}')
    # Find the matching closing brace
    brace_count = 0
    in_string = False
    escape = False
    for i in range(idx, len(content)):
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
                    print(f'Found closing brace at {i}')
                    print(repr(content[i-100:i+100]))
                    break
        if i > idx + 50000:
            print('Search limit reached')
            break
else:
    print('Not found')