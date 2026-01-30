
import os

file_path = os.path.join(os.path.dirname(__file__), 'service_order_form.html')

content = """{% extends 'base.html' %}

{% block content %}
<div class="row mt-4 justify-content-center">
    <div class="col-md-12">
        <div class="card border-0 shadow-sm">
            <div class="card-header bg-white border-bottom-0">
                <h3 class="mt-2">{% if order %}Editar{% else %}Nova{% endif %} Ordem de Serviço</h3>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}

                    <div class="row">
                        <!-- Left Column: Dados Básicos -->
                        <div class="col-md-6 border-end">
                            <h5 class="text-muted mb-3">Dados Básicos</h5>

                            <div class="mb-3">
                                <label for="client" class="form-label">Cliente *</label>
                                <select name="client" id="client" class="form-select" required>
                                    <option value="">Selecione..</option>
                                    {% for client in clients %}
                                    <option value="{{ client.id }}" {% if order.client.id == client.id %}selected{% endif %}>
                                        {{ client.name }}
                                    </option>
                                    {% endfor %}
                                </select>
                            </div>

                            <div class="row mb-3">
                                <div class="col-md-12">
                                    <div class="card bg-light border-0">
                                        <div class="card-body p-3">
                                            <div class="d-flex justify-content-between align-items-center mb-2">
                                                <small class="text-muted"><i
                                                        class="bi bi-geo-alt me-1"></i>Endereço</small>
                                                <button type="button"
                                                    class="btn btn-link btn-sm p-0 text-decoration-none">Alterar</button>
                                            </div>
                                            <textarea name="address" class="form-control bg-white border-0" rows="2"
                                                placeholder="Nenhum endereço selecionado.">{{ order.address|default:'' }}</textarea>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="row mb-3">
                                <div class="col-md-12">
                                    <div class="card bg-light border-0">
                                        <div class="card-body p-3">
                                            <div class="d-flex justify-content-between align-items-center mb-2">
                                                <small class="text-muted"><i
                                                        class="bi bi-telephone me-1"></i>Contato</small>
                                                <button type="button"
                                                    class="btn btn-link btn-sm p-0 text-decoration-none">Alterar</button>
                                            </div>
                                            <input type="text" name="contact" class="form-control bg-white border-0"
                                                placeholder="Nenhum contato selecionado."
                                                value="{{ order.contact|default:'' }}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Right Column: Dados da OS -->
                        <div class="col-md-6 ps-md-4">
                            <h5 class="text-muted mb-3">Dados da Ordem de Serviço</h5>

                            <div class="mb-3">
                                <label for="technical_team" class="form-label">Equipe Técnica</label>
                                <select name="technical_team" id="technical_team" class="form-select">
                                    <option value="">Selecione..</option>
                                    {% for collaborator in collaborators %}
                                    <option value="{{ collaborator.id }}" {% if order.technical_team.id == collaborator.id %}selected{% endif %}>
                                        {{ collaborator.name }}
                                    </option>
                                    {% endfor %}
                                </select>
                            </div>

                            <div class="mb-3">
                                <label for="seller" class="form-label">Vendedores</label>
                                <select name="seller" id="seller" class="form-select">
                                    <option value="">Selecione..</option>
                                    {% for seller in sellers %}
                                    <option value="{{ seller.id }}" {% if order.seller.id == seller.id %}selected{% endif %}>
                                        {{ seller.username }}
                                    </option>
                                    {% endfor %}
                                </select>
                            </div>

                            <div class="mb-3">
                                <label for="order_type" class="form-label">Tipo *</label>
                                <select name="order_type" id="order_type" class="form-select" required>
                                    {% for value, label in type_choices %}
                                    <option value="{{ value }}" {% if order.order_type == value %}selected{% endif %}>
                                        {{ label }}
                                    </option>
                                    {% endfor %}
                                </select>
                            </div>

                            <div class="mb-3">
                                <label for="reason" class="form-label">Motivo da OS *</label>
                                <select name="reason" id="reason" class="form-select" required>
                                    <option value="">Selecione..</option>
                                    {% for value, label in reason_choices %}
                                    <option value="{{ value }}" {% if order.reason == value %}selected{% endif %}>
                                        {{ label }}
                                    </option>
                                    {% endfor %}
                                </select>
                            </div>

                            <h6 class="text-muted mt-4 mb-3">Previsão de Atendimento</h6>

                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="scheduled" disabled checked>
                                    <label class="form-check-label text-muted" for="scheduled">
                                        Atendimento agendado com cliente
                                    </label>
                                </div>
                            </div>

                            <div class="row g-2">
                                <div class="col-md-8">
                                    <input type="datetime-local" name="scheduled_date" class="form-control"
                                        value="{{ order.scheduled_date|date:'Y-m-d\TH:i' }}">
                                </div>
                                <div class="col-md-4">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="bi bi-clock"></i></span>
                                        <input type="text" name="duration" class="form-control" placeholder="Duração"
                                            value="{{ order.duration|default:'' }}">
                                    </div>
                                    <div class="form-text small">Sem duração</div>
                                </div>
                            </div>

                        </div>
                    </div>

                    <hr class="my-4">

                    <hr class="my-4">

                    <!-- Itens da OS -->
                    <div class="row">
                        <div class="col-12">
                            <h5 class="text-muted mb-3">Itens / Produtos</h5>
                            {{ formset.management_form }}
                            <div class="table-responsive">
                                <table class="table table-bordered">
                                    <thead>
                                        <tr>
                                            <th>Produto</th>
                                            <th style="width: 150px;">Quantidade</th>
                                            <th style="width: 150px;">Preço Unit.</th>
                                            <th style="width: 50px;">Remover</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for form in formset %}
                                        <tr>
                                            <td>
                                                {{ form.id }}
                                                {{ form.product }}
                                                {% if form.product.errors %}
                                                <div class="text-danger small">{{ form.product.errors }}</div>
                                                {% endif %}
                                            </td>
                                            <td>
                                                {{ form.quantity }}
                                                {% if form.quantity.errors %}
                                                <div class="text-danger small">{{ form.quantity.errors }}</div>
                                                {% endif %}
                                            </td>
                                            <td>
                                                {{ form.unit_price }}
                                                {% if form.unit_price.errors %}
                                                <div class="text-danger small">{{ form.unit_price.errors }}</div>
                                                {% endif %}
                                            </td>
                                            <td class="text-center align-middle">
                                                {% if form.instance.pk %}
                                                {{ form.DELETE }}
                                                {% endif %}
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <hr class="my-4">

                    <!-- Ficha Técnica -->
                    <div class="row">
                        <div class="col-12">
                            <h5 class="text-muted mb-3">Ficha Técnica</h5>
                            <div class="mb-3">
                                <label for="description" class="form-label">Descreva o que deve ser feito</label>
                                <textarea name="description" id="description" class="form-control" rows="5"
                                    placeholder="Descreva o que a equipe técnica deve fazer">{{ order.description }}</textarea>
                            </div>

                            <!-- Hidden fields for compatibility with existing logic if needed -->
                            <input type="hidden" name="product" value="{{ order.product|default:'Serviço Geral' }}">
                            <input type="hidden" name="status" value="{{ order.status|default:'PENDING' }}">
                        </div>
                    </div>

                    <div class="d-flex gap-2 mt-4">
                        <button type="submit" class="btn btn-warning text-white fw-bold px-4">
                            {% if order %}Salvar Alterações{% else %}Abrir Ordem de Serviço{% endif %}
                        </button>
                        <a href="{% url 'operacional:service_order_list' %}"
                            class="btn btn-outline-secondary px-4">Cancelar</a>
                    </div>

                </form>
            </div>
        </div>
    </div>
</div>

<script>
    // Simple script to populate address/contact when client changes (if we had an API)
    // For now, it just clears them if client changes to prompt manual entry or could be enhanced later
    document.getElementById('client').addEventListener('change', function () {
        // Future: Fetch client details via AJAX
    });
</script>
{% endblock %}
"""

print(f"Writing to {file_path}")
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done.")
