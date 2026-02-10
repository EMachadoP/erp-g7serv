import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from core.views import get_permissions_from_mapping

def verify():
    print("Verificando Mapeamento de Permissões...")
    mapping = get_permissions_from_mapping()
    
    # Apps a verificar
    expected_apps = [
        'Importador de Dados',
        'NFSe Nacional',
        'Integração Cora',
        'Inteligência Artificial (Studio AI)'
    ]
    
    # Modelos a verificar (nomes traduzidos esperados)
    expected_model_names = [
        'atendimento com IA',
        'empresa emissora (NFS-e)',
        'NFS-e Nacional',
        'configuração Cora',
        'boleto Cora',
        'template de importação',
        'trabalho de importação',
        'erro de importação',
        'campo de módulo'
    ]
    
    found_apps = mapping.keys()
    print(f"\nApps encontrados: {list(found_apps)}")
    
    for app in expected_apps:
        if app in found_apps:
            print(f"[OK] App '{app}' encontrado.")
        else:
            print(f"[ERRO] App '{app}' NÃO encontrado.")
            
    print("\nVerificando traduções de modelos...")
    all_perm_names = []
    for perms in mapping.values():
        for p in perms:
            all_perm_names.append(p.name)
            
    all_perms_str = " | ".join(all_perm_names)
    
    for model_name in expected_model_names:
        if model_name.lower() in all_perms_str.lower():
            print(f"[OK] Modelo '{model_name}' encontrado nas permissões.")
        else:
            print(f"[AVISO] Modelo '{model_name}' NÃO encontrado nas permissões (pode ser que não existam instâncias de Permission para este modelo no banco ainda).")

if __name__ == "__main__":
    verify()
