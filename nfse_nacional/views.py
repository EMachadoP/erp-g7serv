from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Empresa, NFSe
from .forms import EmpresaForm, NFSeForm

from django.db.models import Q
from django.http import HttpResponse

# Empresa Views
@login_required
def empresa_list(request):
    empresas = Empresa.objects.all()
    return render(request, 'nfse_nacional/empresa_list.html', {'empresas': empresas})

# ... (create/update views omitted for brevity if they are the same, but I'll keep them for safety) ...
@login_required
def empresa_create(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa cadastrada com sucesso.')
            return redirect('nfse_nacional:empresa_list')
    else:
        form = EmpresaForm()
    return render(request, 'nfse_nacional/empresa_form.html', {'form': form})

@login_required
def empresa_update(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa atualizada com sucesso.')
            return redirect('nfse_nacional:empresa_list')
    else:
        form = EmpresaForm(instance=empresa)
    return render(request, 'nfse_nacional/empresa_form.html', {'form': form})

# NFSe Views
@login_required
def nfse_list(request):
    query = request.GET.get('q', '')
    nfses = NFSe.objects.all().order_by('-data_emissao')
    
    if query:
        nfses = nfses.filter(
            Q(numero_dps__icontains=query) |
            Q(cliente__name__icontains=query) |
            Q(chave_acesso__icontains=query)
        )
        
    return render(request, 'nfse_nacional/nfse_list.html', {
        'nfses': nfses,
        'query': query
    })

@login_required
def nfse_create(request):
    if request.method == 'POST':
        form = NFSeForm(request.POST)
        if form.is_valid():
            nfse = form.save()
            messages.success(request, f'DPS {nfse.numero_dps} gerada com sucesso.')
            return redirect('nfse_nacional:nfse_list')
    else:
        form = NFSeForm()
    return render(request, 'nfse_nacional/nfse_form.html', {'form': form})

@login_required
def nfse_xml(request, pk):
    """Download do XML de retorno da NFSe."""
    nfse = get_object_or_404(NFSe, pk=pk)
    if not nfse.xml_retorno:
        messages.error(request, "XML não disponível para esta nota.")
        return redirect('nfse_nacional:nfse_list')
    
    response = HttpResponse(nfse.xml_retorno, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="NFSe_{nfse.numero_dps}.xml"'
    return response

@login_required
def nfse_view(request, pk):
    """Visualização da NFSe (DANFS)."""
    nfse = get_object_or_404(NFSe, pk=pk)
    # Reusa o template que criamos no faturamento se possível, ou usa um local
    # Para manter desacoplado, vamos usar o local if it exists, but the user liked the one I made.
    # Vou usar faturamento/nfse_view.html pois já está pronto e bonito.
    return render(request, 'faturamento/nfse_view.html', {
        'nfse': nfse,
        'invoice': nfse.invoices_linked.first() # Tenta pegar a fatura vinculada se houver
    })
