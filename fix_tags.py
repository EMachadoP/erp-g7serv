import os
import re

def fix_template(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Merge tags split across lines
    # This regex looks for {% ... %} and {{ ... }} and merges them
    content = re.sub(r'\{%([^%}]*)\r?\n\s*([^%}]*)%\}', r'{%\1 \2%}', content)
    content = re.sub(r'\{\{([^}]*)\r?\n\s*([^}]*)\}\}', r'{{\1 \2}}', content)
    
    # 2. Add spaces around operators in tags
    # Focus on ==, !=, >=, <=, etc. inside {% if ... %}
    def add_spaces(match):
        tag_content = match.group(1)
        # Add spaces around == if missing
        tag_content = re.sub(r'([^ ])==', r'\1 ==', tag_content)
        tag_content = re.sub(r'==([^ ])', r'== \1', tag_content)
        return f'{{% if {tag_content} %}}'

    content = re.sub(r'\{% if ([^%}]*) %\}', add_spaces, content)
    
    # Clean up double spaces
    content = re.sub(r' +', ' ', content)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_template(r"c:\Projetos\erp-g7serv\financeiro\templates\financeiro\financial_statement.html")
