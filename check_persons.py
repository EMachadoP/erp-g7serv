import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()

from core.models import Person

def check_persons():
    print(f"Total de pessoas no sistema: {Person.objects.count()}")
    print(f"Fornecedores: {Person.objects.filter(is_supplier=True).count()}")
    print(f"Colaboradores: {Person.objects.filter(is_collaborator=True).count()}")
    print(f"Clientes: {Person.objects.filter(is_client=True).count()}")
    
    if Person.objects.count() > 0:
        print("\nExemplos de pessoas (Nome - Flags):")
        for p in Person.objects.all()[:10]:
            flags = []
            if p.is_supplier: flags.append("Fornecedor")
            if p.is_collaborator: flags.append("Colaborador")
            if p.is_client: flags.append("Cliente")
            print(f"- {p.name}: {', '.join(flags) if flags else 'Sem flags'}")

if __name__ == "__main__":
    check_persons()
