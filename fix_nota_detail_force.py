
import os

file_path = r'g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\faturamento\templates\faturamento\nota_entrada_detail.html'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define the incorrect pattern
    bad_pattern = """{% if item.produto.created_at|date:"Y-m-d H:i" == item.produto.updated_at|date:"Y-m-d H:i"
                            %}"""
    
    # Define the replacement
    good_pattern = """{% if item.produto.created_at|date:"Y-m-d H:i" == item.produto.updated_at|date:"Y-m-d H:i" %}"""

    if bad_pattern in content:
        new_content = content.replace(bad_pattern, good_pattern)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("File updated successfully.")
    else:
        print("Pattern not found. Trying simpler replace or file is already fixed.")
        # Fallback: try to find it with normalized whitespace issues if simple replace fails
        # Assuming the view_file output was exact, but let's be robust
        if "{% if item.produto.created_at|date:\"Y-m-d H:i\" == item.produto.updated_at|date:\"Y-m-d H:i\"" in content:
             print("Found part of the start.")
        
        # Alternative approach: overwrite the specific line range if we can locate it by context
        # But let's trust exact match first.
        
except Exception as e:
    print(f"Error: {e}")
