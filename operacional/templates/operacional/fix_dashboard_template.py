
import os

# Define path
file_path = r'g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\operacional\templates\operacional\operational_progress.html'

# Content with single-line tags
content = """{% extends 'base.html' %}

{% block title %}Andamento Operacional{% endblock %}

{% block content %}
<div class="container-fluid px-4 py-4">
    <!-- Header & Title -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="h4 text-gray-800">Andamento Operacional</h2>
        <a href="{% url 'operacional:service_order_list' %}" class="btn btn-outline-primary btn-sm">
            <i class="bi bi-list-ul me-2"></i>Ver Todas OS
        </a>
    </div>

    <!-- KPI Row -->
    <div class="row g-3 mb-4">
        <!-- KPI 1: Liberação -->
        <div class="col-6 col-md-3">
            <div class="card border-0 shadow-sm h-100 border-start border-4 border-primary">
                <div class="card-body py-3">
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <div class="text-uppercase text-xs fw-bold text-primary mb-1">Liberação</div>
                            <div class="h5 mb-0 fw-bold text-gray-800">{{ budgets_to_approve.count }}</div>
                        </div>
                        <div class="text-primary opacity-50"><i class="bi bi-file-earmark-check fs-2"></i></div>
                    </div>
                </div>
            </div>
        </div>
        <!-- KPI 2: Contratos -->
        <div class="col-6 col-md-3">
            <div class="card border-0 shadow-sm h-100 border-start border-4 border-warning">
                <div class="card-body py-3">
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <div class="text-uppercase text-xs fw-bold text-warning mb-1">Contratos</div>
                            <div class="h5 mb-0 fw-bold text-gray-800">{{ budgets_pending_contract.count }}</div>
                        </div>
                        <div class="text-warning opacity-50"><i class="bi bi-file-earmark-text fs-2"></i></div>
                    </div>
                </div>
            </div>
        </div>
        <!-- KPI 3: Pendentes OS -->
        <div class="col-6 col-md-3">
            <div class="card border-0 shadow-sm h-100 border-start border-4 border-info">
                <div class="card-body py-3">
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <div class="text-uppercase text-xs fw-bold text-info mb-1">Pendentes OS</div>
                            <div class="h5 mb-0 fw-bold text-gray-800">{{ budgets_pending_os.count }}</div>
                        </div>
                        <div class="text-info opacity-50"><i class="bi bi-tools fs-2"></i></div>
                    </div>
                </div>
            </div>
        </div>
        <!-- KPI 4: Em Execução -->
        <div class="col-6 col-md-3">
            <div class="card border-0 shadow-sm h-100 border-start border-4 border-success">
                <div class="card-body py-3">
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <div class="text-uppercase text-xs fw-bold text-success mb-1">Em Execução</div>
                            <div class="h5 mb-0 fw-bold text-gray-800">{{ os_in_progress.count }}</div>
                        </div>
                        <div class="text-success opacity-50"><i class="bi bi-gear-wide-connected fs-2"></i></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Kanban Grid -->
    <div class="row g-3">
        
        <!-- Column 1: Liberação -->
        <div class="col-lg-3 col-md-6">
            <div class="card h-100 bg-light border-0 shadow-sm">
                <div class="card-header bg-white border-bottom fw-bold py-3 text-primary d-flex justify-content-between align-items-center">
                    <span>Liberação</span>
                    <span class="badge bg-primary bg-opacity-10 text-primary rounded-pill">{{ budgets_to_approve.count }}</span>
                </div>
                <div class="card-body overflow-auto p-2" style="max-height: 70vh; min-height: 300px;">
                    {% for budget in budgets_to_approve %}
                    <div class="card mb-2 border-0 shadow-sm">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <span class="fw-bold fs-6">#{{ budget.id|stringformat:"06d" }}</span>
                                <small class="text-muted">{{ budget.date|date:"d/m" }}</small>
                            </div>
                            <div class="mb-2">
                                <div class="text-truncate fw-bold text-dark" title="{{ budget.client.name }}">{{ budget.client.name }}</div>
                                <div class="small text-muted">R$ {{ budget.total_value|floatformat:2 }}</div>
                            </div>
                            <div class="d-flex gap-2 mt-3">
                                <a href="{% url 'operacional:approve_budget' budget.pk %}" class="btn btn-sm btn-success flex-grow-1" title="Liberar">
                                    <i class="bi bi-check-lg"></i>
                                </a>
                                <a href="{% url 'operacional:refuse_budget' budget.pk %}" class="btn btn-sm btn-outline-danger flex-grow-1" title="Recusar">
                                    <i class="bi bi-x-lg"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                    {% empty %}
                    <div class="text-center py-5 text-muted opacity-50">
                        <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                        <small>Nada pendente</small>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Column 2: Contratos -->
        <div class="col-lg-3 col-md-6">
            <div class="card h-100 bg-light border-0 shadow-sm">
                <div class="card-header bg-white border-bottom fw-bold py-3 text-warning d-flex justify-content-between align-items-center">
                    <span>Contratos</span>
                    <span class="badge bg-warning bg-opacity-10 text-dark rounded-pill">{{ budgets_pending_contract.count }}</span>
                </div>
                <div class="card-body overflow-auto p-2" style="max-height: 70vh; min-height: 300px;">
                    {% for budget in budgets_pending_contract %}
                    <div class="card mb-2 border-0 shadow-sm">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <span class="fw-bold fs-6">#{{ budget.id|stringformat:"06d" }}</span>
                                <small class="text-muted">{{ budget.date|date:"d/m" }}</small>
                            </div>
                            <div class="mb-2">
                                <div class="text-truncate fw-bold text-dark" title="{{ budget.client.name }}">{{ budget.client.name }}</div>
                                <div class="small text-muted">R$ {{ budget.total_value|floatformat:2 }}</div>
                            </div>
                            <div class="d-grid mt-3">
                                <a href="{% url 'comercial:contract_create' %}?budget={{ budget.pk }}" class="btn btn-sm btn-warning text-dark">
                                    <i class="bi bi-file-earmark-plus me-1"></i>Contrato
                                </a>
                            </div>
                        </div>
                    </div>
                    {% empty %}
                    <div class="text-center py-5 text-muted opacity-50">
                        <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                        <small>Nada pendente</small>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Column 3: Gerar OS -->
        <div class="col-lg-3 col-md-6">
            <div class="card h-100 bg-light border-0 shadow-sm">
                <div class="card-header bg-white border-bottom fw-bold py-3 text-info d-flex justify-content-between align-items-center">
                    <span>Gerar OS</span>
                    <span class="badge bg-info bg-opacity-10 text-info rounded-pill">{{ budgets_pending_os.count }}</span>
                </div>
                <div class="card-body overflow-auto p-2" style="max-height: 70vh; min-height: 300px;">
                    {% for budget in budgets_pending_os %}
                    <div class="card mb-2 border-0 shadow-sm">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <span class="fw-bold fs-6">#{{ budget.id|stringformat:"06d" }}</span>
                                <small class="text-muted">{{ budget.date|date:"d/m" }}</small>
                            </div>
                            <div class="mb-2">
                                <div class="text-truncate fw-bold text-dark" title="{{ budget.client.name }}">{{ budget.client.name }}</div>
                                <div class="small text-muted">R$ {{ budget.total_value|floatformat:2 }}</div>
                            </div>
                            <div class="d-grid mt-3">
                                <a href="{% url 'operacional:create_os_from_budget' budget.pk %}" class="btn btn-sm btn-info text-white">
                                    <i class="bi bi-tools me-1"></i>Criar OS
                                </a>
                            </div>
                        </div>
                    </div>
                    {% empty %}
                    <div class="text-center py-5 text-muted opacity-50">
                        <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                        <small>Nada pendente</small>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Column 4: Em Execução -->
        <div class="col-lg-3 col-md-6">
            <div class="card h-100 bg-light border-0 shadow-sm">
                <div class="card-header bg-white border-bottom fw-bold py-3 text-success d-flex justify-content-between align-items-center">
                    <span>Em Execução</span>
                    <span class="badge bg-success bg-opacity-10 text-success rounded-pill">{{ os_in_progress.count }}</span>
                </div>
                <div class="card-body overflow-auto p-2" style="max-height: 70vh; min-height: 300px;">
                    {% for os in os_in_progress %}
                    {% with is_delayed=False %}
                        {% if os.scheduled_date and os.scheduled_date < now %}
                            <div class="card mb-2 border-0 shadow-sm border-start border-4 border-danger">
                                <div class="card-body p-3">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <span class="fw-bold fs-6">#{{ os.id|stringformat:"06d" }}</span>
                                        <span class="badge bg-danger">Atrasado</span>
                                    </div>
                                    <div class="mb-2">
                                        <div class="text-truncate fw-bold text-dark" title="{{ os.client.name }}">{{ os.client.name }}</div>
                                        <div class="small text-muted text-truncate">{{ os.product }}</div>
                                        {% if os.scheduled_date %}
                                        <div class="small text-danger mt-1">
                                            <i class="bi bi-clock me-1"></i>{{ os.scheduled_date|date:"d/m H:i" }}
                                        </div>
                                        {% endif %}
                                    </div>
                                    <div class="d-grid mt-3">
                                        <a href="{% url 'operacional:service_order_detail' os.pk %}" class="btn btn-sm btn-outline-success">
                                            Ver Detalhes
                                        </a>
                                    </div>
                                </div>
                            </div>
                        {% else %}
                            <div class="card mb-2 border-0 shadow-sm">
                                <div class="card-body p-3">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <span class="fw-bold fs-6">#{{ os.id|stringformat:"06d" }}</span>
                                        <small class="text-muted">{{ os.scheduled_date|date:"d/m H:i"|default:"-" }}</small>
                                    </div>
                                    <div class="mb-2">
                                        <div class="text-truncate fw-bold text-dark" title="{{ os.client.name }}">{{ os.client.name }}</div>
                                        <div class="small text-muted text-truncate">{{ os.product }}</div>
                                    </div>
                                    <div class="d-grid mt-3">
                                        <a href="{% url 'operacional:service_order_detail' os.pk %}" class="btn btn-sm btn-outline-success">
                                            Ver Detalhes
                                        </a>
                                    </div>
                                </div>
                            </div>
                        {% endif %}
                    {% endwith %}
                    {% empty %}
                    <div class="text-center py-5 text-muted opacity-50">
                        <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                        <small>Nada em execução</small>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    .card-body::-webkit-scrollbar { width: 4px; }
    .card-body::-webkit-scrollbar-track { background: #f1f1f1; }
    .card-body::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }
    .card-body::-webkit-scrollbar-thumb:hover { background: #aaa; }
</style>
{% endblock %}
"""

print(f"Writing clean content to {file_path}")
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done.")
