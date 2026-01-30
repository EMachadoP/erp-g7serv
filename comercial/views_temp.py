
from django.http import JsonResponse

@login_required
def get_client_details(request, pk):
    client = get_object_or_404(Person, pk=pk)
    data = {
        'name': client.name,
        'document': client.document,
        'address': f"{client.address}, {client.number} - {client.neighborhood}, {client.city} - {client.state}",
        'responsible_name': client.responsible_name,
        'responsible_cpf': client.responsible_cpf,
        'email': client.email,
        'phone': client.phone,
    }
    return JsonResponse(data)
