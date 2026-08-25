import re

with open('tests/test_i18n.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the test function
pattern = re.compile(
    r'(@pytest\.mark\.parametrize\("idioma", i18n\.IDIOMAS\)\s+def test_no_hay_entradas_huerfanas\(self, idioma\):.*?assert not huerfanas, \()',
    re.DOTALL
)

match = re.search(pattern, content, re.DOTALL)
if match:
    start, end = match.span()
    print(f"Found at position {start}-{end}")
    
    # Read the new implementation
    with open('new_test_impl.py', 'r', encoding='utf-8') as f:
        new_impl = f.read()
    
    new_content = content[:start] + new_impl + content[end:]
    
    with open('tests/test_i18n.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced successfully")
else:
    print("Pattern not found")