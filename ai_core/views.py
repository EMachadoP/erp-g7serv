from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def processar_ia(request):
    """
    Endpoint de triagem de IA.
    Implementação básica para satisfazer o roteamento e testes.
    """
    if request.method == 'POST':
        return JsonResponse({
            'status': 'sucesso',
            'mensagem': 'Mensagem processada pela IA.',
            'triagem': 'manutencao'
        })
    return JsonResponse({'erro': 'Método não permitido'}, status=405)
