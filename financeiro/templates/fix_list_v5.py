
import os

file_path = r'g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\financeiro\templates\financeiro\account_payable_list.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    fixed_count = 0
    
    while i < len(lines):
        line = lines[i]
        # Check for the specific split in the supplier loop
        if '{% endif' in line and not '%}' in line:
            if i + 1 < len(lines):
                next_line = lines[i+1]
                if '%}' in next_line:
                    # Consolidate
                    # Line 22: ... {% endif
                    # Line 23:    %}> ...
                    
                    # We want: ... {% endif %}> ...
                    
                    combined = line.rstrip() + ' %}' + next_line.lstrip().replace('%}', '', 1)
                    new_lines.append(combined)
                    i += 2
                    fixed_count += 1
                    continue
        
        new_lines.append(line)
        i += 1

    if fixed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"File updated successfully. Fixed {fixed_count} split tags.")
    else:
        print("No split tags found to fix.")

except Exception as e:
    print(f"Error: {e}")
