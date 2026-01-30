
import os

file_path = r"g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\comercial\templates\comercial\contract_template_form.html"

content = """{% extends 'base.html' %}

{% block title %}{% if template %}Editar Modelo{% else %}Novo Modelo{% endif %}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>{% if template %}Editar Modelo{% else %}Novo Modelo{% endif %}</h2>
    <a href="{% url 'comercial:contract_template_list' %}" class="btn btn-outline-secondary">
        <i class="bi bi-arrow-left"></i> Voltar
    </a>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card border-0 shadow-sm">
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}
                    {{ form.media }}
                    
                    <div class="mb-3">
                        <label for="name" class="form-label">Nome do Modelo *</label>
                        <input type="text" name="name" id="name" class="form-control" 
                               value="{{ template.name|default:'' }}" required>
                    </div>

                    <div class="mb-3">
                        <label for="template_type" class="form-label">Tipo de Modelo *</label>
                        <select name="template_type" id="template_type" class="form-select" required>
                            <option value="Novo Contrato" {% if template.template_type == 'Novo Contrato' %}selected{% endif %}>Novo Contrato</option>
                            <option value="Cancelamento" {% if template.template_type == 'Cancelamento' %}selected{% endif %}>Cancelamento</option>
                            <option value="Reajuste" {% if template.template_type == 'Reajuste' %}selected{% endif %}>Reajuste</option>
                            <option value="Aditivos" {% if template.template_type == 'Aditivos' %}selected{% endif %}>Aditivos</option>
                        </select>
                    </div>

                    <div class="mb-3">
                        <label for="content" class="form-label">Conteúdo *</label>
                        <textarea name="content" id="content" class="form-control" rows="20">{{ template.content|default:'' }}</textarea>
                    </div>

                    <div class="d-flex justify-content-end gap-2">
                        <a href="{% url 'comercial:contract_template_list' %}" class="btn btn-secondary">Cancelar</a>
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-check-lg"></i> Salvar Modelo
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card border-0 shadow-sm bg-light">
            <div class="card-body">
                <h5 class="card-title mb-3"><i class="bi bi-info-circle me-2"></i>Variáveis Disponíveis</h5>
                <p class="text-muted small">Use estas variáveis no conteúdo do contrato. Elas serão substituídas automaticamente pelos dados reais.</p>
                
                <ul class="list-group list-group-flush small bg-transparent">
                    <li class="list-group-item bg-transparent px-0">
                        <strong>{{NOME_CLIENTE}}</strong><br>
                        <span class="text-muted">Nome do cliente (Razão Social ou Nome Completo)</span>
                    </li>
                    <li class="list-group-item bg-transparent px-0">
                        <strong>{{CNPJ_CPF_CLIENTE}}</strong><br>
                        <span class="text-muted">CNPJ ou CPF do cliente</span>
                    </li>
                    <li class="list-group-item bg-transparent px-0">
                        <strong>{{ENDERECO_CLIENTE}}</strong><br>
                        <span class="text-muted">Endereço completo do cliente</span>
                    </li>
                    <li class="list-group-item bg-transparent px-0">
                        <strong>{{VALOR_MENSAL}}</strong><br>
                        <span class="text-muted">Valor mensal do contrato (R$)</span>
                    </li>
                    <li class="list-group-item bg-transparent px-0">
                        <strong>{{DIA_VENCIMENTO}}</strong><br>
                        <span class="text-muted">Dia de vencimento da fatura</span>
                    </li>
                    <li class="list-group-item bg-transparent px-0">
                        <strong>{{DATA_INICIO}}</strong><br>
                        <span class="text-muted">Data de início do contrato</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.ckeditor.com/4.22.1/standard/ckeditor.js"></script>
<script>
    CKEDITOR.config.versionCheck = false;
    CKEDITOR.replace('content', {
        height: 500,
        language: 'pt-br'
    });
</script>
{% endblock %}
"""

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("File written successfully.")
