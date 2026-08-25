import re

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the test function
pattern = re.compile(
    r'(@pytest\.mark\.parametrize\("idioma", i18n\.IDIOMAS\)\s+def test_no_hay_entradas_huerfanas\(self, idioma\):.*?assert not huerfanas, \()',
    re.DOTALL
)

match = re.search(r'(@pytest\.mark\.parametrize\("idioma", i18n\.IDIOMAS\)\s+def test_no_hay_entradas_huerfanas\(self, idioma\):.*?assert not huerfanas, \()', content, re.DOTALL)

if match:
    print(f"Found at position {match.start()}-{match.end()}")
    # We'll replace using a different approach
    print("Match found")
else:
    print("Pattern not found")
    # Find the function
    idx = content.find('def test_no_hay_entradas_huerfanas')
    if idx >= 0:
        print(f"Found function at {idx}")
        # Find the end of the function
        # Find the next 'def ' after this one
        next_def = content.find('def ', content.find('def test_no_hay_entradas_huerfanas') + 1)
        if next_def > 0:
            print(f"Next function at {next_def}")
        else:
            print("No next function found")

with open('tests/test_i18n.py', 'w', encoding='utf-8') as f:
    f.write(content)