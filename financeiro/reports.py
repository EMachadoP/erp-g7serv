from django.db.models import Sum
from comercial.models import Budget

def gerar_relatorio_comissoes(data_inicio, data_fim):
    vendas = Budget.objects.filter(
        status='Ganho', 
        closing_date__range=[data_inicio, data_fim]
    )
    
    # Agrupamento para o resumo
    relatorio = {
        'direta': vendas.filter(origin='direta'),
        'preventiva': vendas.filter(origin='preventiva'),
        'total_vendas': vendas.aggregate(Sum('total_value'))['total_value__sum'] or 0,
        'total_comissoes': 0
    }
    
    # Cálculo total de comissões (vendedor + técnico)
    total_comissoes = 0
    for v in vendas:
        v_comm, t_comm = v.calculate_commission_values()
        total_comissoes += v_comm + t_comm
    
    relatorio['total_comissoes'] = total_comissoes
    
    return relatorio
