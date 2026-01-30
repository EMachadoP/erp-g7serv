import re
import os

file_path = r'g:/Meu Drive/11 - Empresa - Descartex/Projetos IA/templates/base.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Regex to find multi-line {% if ... %} tags
# We look for {% if, followed by anything until %}, allowing for newlines
pattern = r'({%\s*if\s+.*?%})'

def replace_match(match):
    tag_content = match.group(1)
    # Replace newlines and multiple spaces with a single space
    new_tag = re.sub(r'\s+', ' ', tag_content)
    return new_tag

# Apply substitution with DOTALL flag to match across lines
new_content = re.sub(pattern, replace_match, content, flags=re.DOTALL)

# Also fix the redundant inner if block if it exists
# We'll just fix the multi-line tags first as that's the syntax error.
# The redundant logic is harmless but messy.

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Fixed base.html successfully.")
