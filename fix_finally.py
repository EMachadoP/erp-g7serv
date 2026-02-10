path = r'nfse_nacional/services/api_client.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# find line 310 (which is index 309)
# we need to add the finally block before return False if it matches our pattern

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'return False' in line and i == 309: # index of line 310
         # Insert finally block
         pass

# Actually it is easier to just append the missing finally at the end
# if line 310 is the last return False of the method

# Let's just rewrite from line 302
final_block = '''            print(f"DEBUG NFSe: Falha ao obter PDF (Status {response.status_code})")
            
            # Tenta construir link para consulta pública se ainda não tiver e se falhou o PDF
            if not nfse_obj.link_danfse:
                link = f"https://www.nfse.gov.br/ConsultaPublica/?chave={nfse_obj.chave_acesso}"
                nfse_obj.link_danfse = link
                nfse_obj.save(update_fields=['link_danfse'])
            
            return False
            
        finally:
            for f in temp_files:
                if os.path.exists(f):
                    os.unlink(f)
'''

# Find the start of the block we want to replace
start_idx = -1
for i, line in enumerate(lines):
    if 'print(f"DEBUG NFSe: Falha ao obter PDF' in line:
        start_idx = i
        break

if start_idx != -1:
    fixed_lines = lines[:start_idx] + [final_block]
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    print("Fixed finally block.")
else:
    print("Could not find start index.")
