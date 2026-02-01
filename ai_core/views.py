import uuid
from .models import AtendimentoAI
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def processar_ia(request):
    if request.method == "POST":
        if request.headers.get('Content-Type') != 'application/json':
            return JsonResponse({"status": "erro", "mensagem": "Content-Type deve ser application/json"}, status=415)
            
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": "erro", "mensagem": "JSON inválido"}, status=400)
            
        msg = data.get("mensagem", "").lower()
        nome = data.get("nome", "Cliente")
        
        # Lógica de Triagem
        categoria = 'outro'
        if any(word in msg for word in ['preço', 'valor', 'comprar', 'orçamento', 'precos', 'valores']):
            categoria = 'orcamento'
        elif any(word in msg for word in ['quebrou', 'conserto', 'visita', 'os', 'manutenção', 'manutencao']):
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
            "status": "sucesso",
            "protocolo": protocolo_num,
            "categoria": categoria,
            "resposta": f"Olá {nome}, seu atendimento foi triado para o setor {categoria.upper()}. Protocolo: {protocolo_num}"
        })
    return JsonResponse({"status": "erro", "mensagem": "Método não permitido"}, status=405)
