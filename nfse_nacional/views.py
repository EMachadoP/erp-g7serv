from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Empresa, NFSe
from .forms import EmpresaForm, NFSeForm

# Empresa Views
@login_required
def empresa_list(request):
    empresas = Empresa.objects.all()
    return render(request, 'nfse_nacional/empresa_list.html', {'empresas': empresas})

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
    nfses = NFSe.objects.all().order_by('-data_emissao')
    return render(request, 'nfse_nacional/nfse_list.html', {'nfses': nfses})

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
