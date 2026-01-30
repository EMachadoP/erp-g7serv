
import os

file_path = r"g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\comercial\templates\comercial\contract_form.html"

content = """{% extends 'base.html' %}

{% block title %}{% if contract %}Editar Contrato{% else %}Novo Contrato{% endif %}{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>{% if contract %}Editar Contrato #{{ contract.id }}{% else %}Novo Contrato{% endif %}</h2>
    <a href="{% url 'comercial:contract_list' %}" class="btn btn-outline-secondary">
        <i class="bi bi-arrow-left"></i> Voltar
    </a>
</div>

<div class="card border-0 shadow-sm">
    <div class="card-body">
        <form method="post">
            {% csrf_token %}
            
            <h5 class="mb-3 text-secondary">Informações Principais</h5>
            <div class="row g-3 mb-4">
                <div class="col-md-6">
                    <label for="client" class="form-label">Cliente *</label>
                    <select name="client" id="client" class="form-select" required>
                        <option value="">Selecione um cliente...</option>
                        {% for client in clients %}
                        <option value="{{ client.id }}" {% if contract and contract.client.id == client.id %}selected{% endif %}>
                            {{ client.name }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="col-md-6">
                    <label for="template" class="form-label">Modelo de Contrato *</label>
                    <select name="template" id="template" class="form-select" required>
                        <option value="">Selecione um modelo...</option>
                        {% for template in templates %}
                        <option value="{{ template.id }}" {% if contract and contract.template.id == template.id %}selected{% endif %}>
                            {{ template.name }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="col-md-4">
                    <label for="billing_group" class="form-label">Grupo de Faturamento</label>
                    <select name="billing_group" id="billing_group" class="form-select">
                        <option value="">Nenhum</option>
                        {% for group in billing_groups %}
                        <option value="{{ group.id }}" {% if contract and contract.billing_group.id == group.id %}selected{% endif %}>
                            {{ group.name }}
                        </option>
                        {% endfor %}
                    </select>
                </div>

                <div class="col-md-4">
                    <label for="status" class="form-label">Status *</label>
                    <select name="status" id="status" class="form-select" required>
                        <option value="Ativo" {% if contract and contract.status == 'Ativo' %}selected{% endif %}>Ativo</option>
                        <option value="Inativo" {% if contract and contract.status == 'Inativo' %}selected{% endif %}>Inativo</option>
                        <option value="Cancelado" {% if contract and contract.status == 'Cancelado' %}selected{% endif %}>Cancelado</option>
                        <option value="Expirado" {% if contract and contract.status == 'Expirado' %}selected{% endif %}>Expirado</option>
                    </select>
                </div>
            </div>

            <h5 class="mb-3 text-secondary">Detalhes Financeiros e Prazos</h5>
            <div class="row g-3 mb-4">
                <div class="col-md-3">
                    <label for="modality" class="form-label">Modalidade *</label>
                    <select name="modality" id="modality" class="form-select" required>
                        <option value="Mensal" {% if contract and contract.modality == 'Mensal' %}selected{% endif %}>Mensal</option>
                        <option value="Anual" {% if contract and contract.modality == 'Anual' %}selected{% endif %}>Anual</option>
                    </select>
                </div>

                <div class="col-md-3">
                    <label for="value" class="form-label">Valor (R$) *</label>
                    <input type="text" name="value" id="value" class="form-control" 
                           value="{{ contract.value|stringformat:'.2f'|default:'' }}" required>
                </div>

                <div class="col-md-3">
                    <label for="due_day" class="form-label">Dia de Vencimento *</label>
                    <input type="number" name="due_day" id="due_day" class="form-control" min="1" max="31"
                           value="{{ contract.due_day|default:'' }}" required>
                </div>
                
                <div class="col-md-3">
                    <!-- Spacer -->
                </div>

                <div class="col-md-3">
                    <label for="start_date" class="form-label">Data de Início *</label>
                    <input type="date" name="start_date" id="start_date" class="form-control" 
                           value="{{ contract.start_date|date:'Y-m-d' }}" required>
                </div>

                <div class="col-md-3">
                    <label for="end_date" class="form-label">Data de Término</label>
                    <input type="date" name="end_date" id="end_date" class="form-control" 
                           value="{{ contract.end_date|date:'Y-m-d'|default:'' }}">
                </div>
            </div>

            <div class="d-flex justify-content-end gap-2">
                <a href="{% url 'comercial:contract_list' %}" class="btn btn-secondary">Cancelar</a>
                <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check-lg"></i> Salvar Contrato
                </button>
            </div>
        </form>
    </div>
</div>

<script src="https://cdn.ckeditor.com/4.22.1/standard/ckeditor.js"></script>
<script>
    // Simple mask for currency
    const valueInput = document.getElementById('value');
    valueInput.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        value = (value / 100).toFixed(2) + '';
        value = value.replace(".", ",");
        value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1.");
        e.target.value = value;
    });
    
    // On submit, clean the value to be a float compatible string (dot decimal)
    document.querySelector('form').addEventListener('submit', function(e) {
        let value = valueInput.value.replace(/\./g, '').replace(',', '.');
        valueInput.value = value;
    });

    // Dynamic Contract Generation
    const clientSelect = document.getElementById('client');
    const templateSelect = document.getElementById('template');
    const valueField = document.getElementById('value');
    const dueDayField = document.getElementById('due_day');
    const startDateField = document.getElementById('start_date');

    let clientData = null;
    let templateContent = null;

    function updateContractContent() {
        if (!clientData || !templateContent) return;

        let content = templateContent;

        // Replace variables
        content = content.replace(/{{NOME_CLIENTE}}/g, clientData.name || '');
        content = content.replace(/{{CNPJ_CPF_CLIENTE}}/g, clientData.document || '');
        content = content.replace(/{{ENDERECO_CLIENTE}}/g, clientData.address || '');
        content = content.replace(/{{NOME_RESPONSAVEL}}/g, clientData.responsible_name || '');
        content = content.replace(/{{CPF_RESPONSAVEL}}/g, clientData.responsible_cpf || '');
        content = content.replace(/{{EMAIL_CLIENTE}}/g, clientData.email || '');
        content = content.replace(/{{TELEFONE_CLIENTE}}/g, clientData.phone || '');
        
        content = content.replace(/{{VALOR_MENSAL}}/g, valueField.value || '');
        content = content.replace(/{{DIA_VENCIMENTO}}/g, dueDayField.value || '');
        
        // Format date
        let startDate = startDateField.value;
        if (startDate) {
            let parts = startDate.split('-');
            startDate = `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        content = content.replace(/{{DATA_INICIO}}/g, startDate || '');

        // Update CKEditor
        if (CKEDITOR.instances.id_description) {
            CKEDITOR.instances.id_description.setData(content);
        } else if (CKEDITOR.instances.description) { // Fallback name
             CKEDITOR.instances.description.setData(content);
        }
    }

    clientSelect.addEventListener('change', function() {
        const clientId = this.value;
        if (clientId) {
            fetch(`/comercial/api/cliente/${clientId}/`)
                .then(response => response.json())
                .then(data => {
                    clientData = data;
                    updateContractContent();
                })
                .catch(error => console.error('Error fetching client details:', error));
        } else {
            clientData = null;
        }
    });

    templateSelect.addEventListener('change', function() {
        const templateId = this.value;
        if (templateId) {
            fetch(`/comercial/api/modelo-contrato/${templateId}/`)
                .then(response => response.json())
                .then(data => {
                    templateContent = data.content;
                    updateContractContent();
                })
                .catch(error => console.error('Error fetching template details:', error));
        } else {
            templateContent = null;
        }
    });

    // Update on field changes
    valueField.addEventListener('blur', updateContractContent);
    dueDayField.addEventListener('change', updateContractContent);
    startDateField.addEventListener('change', updateContractContent);
</script>
{% endblock %}
"""

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("File written successfully.")
