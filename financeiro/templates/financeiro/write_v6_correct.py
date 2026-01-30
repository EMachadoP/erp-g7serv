
import os

content = """{% extends 'base.html' %}
{% load static %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="bi bi-wallet2"></i> Contas a Pagar</h2>
        <a href="{% url 'financeiro:account_payable_create' %}" class="btn btn-primary">
            <i class="bi bi-plus-lg"></i> Nova Conta
        </a>
    </div>

    <!-- Filters -->
    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <form method="get" class="row g-3">
                <div class="col-md-3">
                    <label class="form-label">Fornecedor</label>
                    <select name="supplier" class="form-select select2">
                        <option value="">Todos</option>
                        {% for s in suppliers %}
                        {% with supplier_id_str=s.id|stringformat:"i" %}
                        <option value="{{ s.id }}" {% if request.GET.supplier == supplier_id_str %}selected{% endif %}>{{ s.name }}</option>
                        {% endwith %}
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">Status</label>
                    <select name="status" class="form-select">
                        <option value="">Todos</option>
                        <option value="PENDING" {% if status_filter == 'PENDING' %}selected{% endif %}>Pendentes</option>
                        <option value="PAID" {% if status_filter == 'PAID' %}selected{% endif %}>Pagas</option>
                        <option value="OVERDUE" {% if status_filter == 'OVERDUE' %}selected{% endif %}>Vencidas</option>
                        <option value="CANCELLED" {% if status_filter == 'CANCELLED' %}selected{% endif %}>Canceladas</option>
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label">De</label>
                    <input type="date" name="start_date" class="form-control" value="{{ start_date|default:'' }}">
                </div>
                <div class="col-md-2">
                    <label class="form-label">Até</label>
                    <input type="date" name="end_date" class="form-control" value="{{ end_date|default:'' }}">
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary w-100"><i class="bi bi-filter"></i> Filtrar</button>
                    <a href="{% url 'financeiro:account_payable_list' %}" class="btn btn-outline-secondary ms-2" title="Limpar"><i class="bi bi-x-lg"></i></a>
                </div>
            </form>
        </div>
    </div>

    <!-- Table -->
    <div class="card shadow-sm">
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="bg-light">
                    <tr>
                        <th>Vencimento</th>
                        <th>Descrição</th>
                        <th>Fornecedor</th>
                        <th>Valor</th>
                        <th>Status</th>
                        <th class="text-end">Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {% for p in payables %}
                    <tr class="{% if p.status == 'OVERDUE' %}table-danger{% endif %}">
                        <td>
                            <strong>{{ p.due_date|date:"d/m/Y" }}</strong>
                            {% if p.status == 'PENDING' and p.due_date < today %}
                            <span class="badge bg-danger rounded-pill ms-1">!</span>
                            {% endif %}
                        </td>
                        <td>
                            {{ p.description }}
                            {% if p.notes %}
                            <i class="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" title="{{ p.notes }}"></i>
                            {% endif %}
                        </td>
                        <td>{{ p.supplier.fantasy_name|default:p.supplier.name|default:"--" }}</td>
                        <td class="fw-bold">R$ {{ p.amount }}</td>
                        <td>
                            {% if p.status == 'PENDING' %}
                                <span class="badge bg-warning text-dark">Pendente</span>
                            {% elif p.status == 'PAID' %}
                                <span class="badge bg-success">Pago</span>
                            {% elif p.status == 'OVERDUE' %}
                                <span class="badge bg-danger">Vencido</span>
                            {% elif p.status == 'CANCELLED' %}
                                <span class="badge bg-secondary">Cancelado</span>
                            {% endif %}
                        </td>
                        <td class="text-end">
                            <div class="dropdown">
                                <button class="btn btn-sm btn-light border dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                    <i class="bi bi-gear"></i>
                                </button>
                                <ul class="dropdown-menu dropdown-menu-end">
                                    <li>
                                        <a class="dropdown-item" href="{% url 'financeiro:account_payable_detail' p.id %}">
                                            <i class="bi bi-eye me-2"></i> Detalhes
                                        </a>
                                    </li>
                                    {% if p.status == 'PENDING' or p.status == 'OVERDUE' %}
                                    <li>
                                        <button class="dropdown-item text-success btn-pay" 
                                                data-id="{{ p.id }}" 
                                                data-amount="{{ p.amount }}"
                                                data-desc="{{ p.description }}">
                                            <i class="bi bi-cash-stack me-2"></i> Baixar (Pagar)
                                        </button>
                                    </li>
                                    {% endif %}
                                    <li><hr class="dropdown-divider"></li>
                                    {% if p.status != 'CANCELLED' and p.status != 'PAID' %}
                                    <li>
                                        <form action="{% url 'financeiro:account_payable_cancel' p.id %}" method="post" onsubmit="return confirm('Cancelar esta conta?');" style="display:inline;">
                                            {% csrf_token %}
                                            <button type="submit" class="dropdown-item text-danger">
                                                <i class="bi bi-x-circle me-2"></i> Cancelar
                                            </button>
                                        </form>
                                    </li>
                                    {% endif %}
                                </ul>
                            </div>
                        </td>
                    </tr>
                    {% empty %}
                    <tr>
                        <td colspan="6" class="text-center py-4 text-muted">Nenhuma conta encontrada.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Modal Pagamento (Same as Detail) -->
<div class="modal fade" id="modalPagamento" tabindex="-1">
    <div class="modal-dialog">
        <form method="post" id="paymentForm" action="">
            {% csrf_token %}
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Registrar Pagamento</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="mb-3">Baixando conta: <strong id="modalDesc"></strong></p>
                    
                    <div class="mb-3">
                        <label class="form-label">Valor Original</label>
                        <div class="input-group">
                            <span class="input-group-text">R$</span>
                            <input type="text" id="modalOriginalAmount" class="form-control" readonly>
                        </div>
                    </div>

                    <div class="row g-2 mb-3">
                        <div class="col-4">
                            {{ payment_form.interest.label_tag }}
                            {{ payment_form.interest }}
                        </div>
                        <div class="col-4">
                            {{ payment_form.fine.label_tag }}
                            {{ payment_form.fine }}
                        </div>
                        <div class="col-4">
                            {{ payment_form.discount.label_tag }}
                            {{ payment_form.discount }}
                        </div>
                    </div>

                    <div class="mb-3 p-3 bg-light rounded border">
                        {{ payment_form.amount.label_tag }}
                        {{ payment_form.amount }}
                        <div class="form-text">Calculado automaticamente (Original + Juros + Multa - Desconto).</div>
                    </div>

                    <div class="row mb-3">
                        <div class="col-6">
                            {{ payment_form.payment_date.label_tag }}
                            {{ payment_form.payment_date }}
                        </div>
                        <div class="col-6">
                            {{ payment_form.account.label_tag }}
                            {{ payment_form.account }}
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        {{ payment_form.notes.label_tag }}
                        {{ payment_form.notes }}
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                    <button type="submit" class="btn btn-success">Confirmar Pagamento</button>
                </div>
            </div>
        </form>
    </div>
</div>

<script>
    document.addEventListener("DOMContentLoaded", function () {
        // Initialize Select2
        if (typeof $ !== 'undefined' && $.fn.select2) {
            $('.select2').select2({
                theme: 'bootstrap-5',
                width: '100%'
            });
        }

        // Modal Logic
        const paymentModal = document.getElementById('paymentModal');
        const modalDesc = document.getElementById('modalDesc');
        const paymentForm = document.getElementById('paymentForm');
        
        // Fields with safe fallbacks
        const inputAmount = document.getElementById('id_amount');
        const inputDate = document.getElementById('id_payment_date');
        const inputInterest = document.getElementById('id_interest');
        const inputFine = document.getElementById('id_fine');
        const inputDiscount = document.getElementById('id_discount');
        const displayOriginal = document.getElementById('modalOriginalAmount'); 

        // Set default date to today
        if(inputDate && !inputDate.value) {
            inputDate.valueAsDate = new Date();
        }

        let currentOriginalAmount = 0;

        function updateTotal() {
            if(!inputAmount) return;
            const interest = parseFloat(inputInterest ? inputInterest.value.replace(',', '.') : 0) || 0;
            const fine = parseFloat(inputFine ? inputFine.value.replace(',', '.') : 0) || 0;
            const discount = parseFloat(inputDiscount ? inputDiscount.value.replace(',', '.') : 0) || 0;
            
            const total = currentOriginalAmount + interest + fine - discount;
            
            inputAmount.value = total.toFixed(2).replace('.', ',');
        }

        document.querySelectorAll('.btn-pay').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.dataset.id;
                // Parse float from comma string (Django localization)
                let rawAmount = this.dataset.amount.replace(',', '.');
                currentOriginalAmount = parseFloat(rawAmount) || 0; 
                const desc = this.dataset.desc;

                // Update Modal Content
                if(modalDesc) modalDesc.textContent = desc;
                if(displayOriginal) {
                    displayOriginal.value = currentOriginalAmount.toFixed(2).replace('.', ',');
                }
                
                // Reset optional fields
                if(inputInterest) inputInterest.value = '0';
                if(inputFine) inputFine.value = '0';
                if(inputDiscount) inputDiscount.value = '0';
                
                updateTotal();
                
                // Update Action URL correctly using JS template literal
                paymentForm.action = `/financeiro/contas-a-pagar/${id}/pagar/`;
                
                // Show Modal
                if(typeof bootstrap !== 'undefined') {
                    const bsModal = new bootstrap.Modal(paymentModal);
                    bsModal.show();
                } else {
                    console.error('Bootstrap 5 not loaded');
                }
            });
        });
        
        // Listeners for calc
        if(inputInterest) inputInterest.addEventListener('input', updateTotal);
        if(inputFine) inputFine.addEventListener('input', updateTotal);
        if(inputDiscount) inputDiscount.addEventListener('input', updateTotal);
    });
</script>
{% endblock %}
"""

file_path = os.path.join(
    r"g:\Meu Drive\11 - Empresa - Descartex\Projetos IA\financeiro\templates\financeiro",
    "account_payable_list.html"
)

try:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully wrote utf-8 content to {file_path}")
except Exception as e:
    print(f"Error writing file: {e}")
