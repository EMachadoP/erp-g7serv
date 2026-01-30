
import os

file_path = r'g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\faturamento\templates\faturamento\nota_entrada_detail.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The problematic pattern (exactly as seen in error log)
    bad_pattern_start = '{% if item.produto.created_at|date:"Y-m-d H:i" == item.produto.updated_at|date:"Y-m-d H:i"'
    
    lines = content.splitlines()
    new_lines = []
    i = 0
    fixed_count = 0
    
    while i < len(lines):
        line = lines[i]
        if bad_pattern_start in line and not '%}' in line:
            # Found the split start
            if i + 1 < len(lines) and '%}' in lines[i+1]:
                # Found the split end on next line
                combined = line.strip() + ' %}'
                new_lines.append(combined)
                i += 2 # Skip next line
                fixed_count += 1
                continue
        
        new_lines.append(line)
        i += 1

    if fixed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print(f"File updated successfully. Fixed {fixed_count} split tags.")
    else:
        print("No split tags found to fix.")

except Exception as e:
    print(f"Error: {e}")
