import uuid
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import AtendimentoAI

@csrf_exempt
@require_POST
def processar_ia(request):
    # Valida Content-Type
    if 'application/json' not in request.headers.get('Content-Type', ''):
        return JsonResponse({'error': 'JSON required'}, status=415)
    
    # Parse com tratamento de erro
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    # Valida campos
    if not data.get('mensagem') or not data.get('nome'):
        return JsonResponse({'error': 'mensagem and nome required'}, status=400)

    msg = data.get("mensagem", "").lower()
    nome = data.get("nome")
    # Lógica de Triagem
    categoria = 'outro'
    if any(word in msg for word in ['preço', 'valor', 'comprar', 'orçamento', 'precos', 'valores']):
        categoria = 'orcamento'
    elif any(word in msg for word in ['quebrou', 'conserto', 'visita', 'os', 'manutenção', 'manutencao', 'funcional', 'sistema']):
        categoria = 'suporte'
    elif any(word in msg for word in ['boleto', 'pagar', 'vencimento', 'nota', 'fatura']):
        categoria = 'financeiro'

    protocolo_num = str(uuid.uuid4().hex[:8]).upper()
    
    # Salva no Banco de Dados (Postgres no Railway)
    AtendimentoAI.objects.create(
        cliente_nome=nome,
        mensagem_usuario=msg,
        categoria_detectada=categoria,
        protocolo=protocolo_num
    )

    return JsonResponse({
        "success": True,
        "protocolo": protocolo_num,
        "categoria": categoria,
        "resposta": f"Olá {nome}, seu atendimento foi triado para o setor {categoria.upper()}. Protocolo: {protocolo_num}"
    })
