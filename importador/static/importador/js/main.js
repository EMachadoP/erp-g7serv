// Main JavaScript for Importador Inteligente

// Utility functions
const Utils = {
    // Format date to Brazilian format
    formatDate: (dateStr) => {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('pt-BR');
    },

    // Format datetime to Brazilian format
    formatDateTime: (dateStr) => {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleString('pt-BR');
    },

    // Format currency
    formatCurrency: (value) => {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },

    // Show loading spinner
    showLoading: (element, text = 'Carregando...') => {
        element.dataset.originalText = element.innerHTML;
        element.innerHTML = `<span class="spinner-border spinner-border-sm"></span> ${text}`;
        element.disabled = true;
    },

    // Hide loading spinner
    hideLoading: (element) => {
        element.innerHTML = element.dataset.originalText;
        element.disabled = false;
    }
};

// Auto-refresh for processing jobs
function initAutoRefresh() {
    const isProcessingPage = document.querySelector('.status-processing') || document.querySelector('.progress-bar-animated');
    if (isProcessingPage) {
        setTimeout(() => {
            window.location.reload();
        }, 5000);
    }
}

// Funções específicas para preview de clientes e contratos

function showClientesPreview(data) {
    const modalId = 'clientesPreviewModal';
    let modalElement = document.getElementById(modalId);
    if (modalElement) modalElement.remove();

    modalElement = document.createElement('div');
    modalElement.className = 'modal fade';
    modalElement.id = modalId;
    modalElement.innerHTML = `
        <div class="modal-dialog modal-xl">
            <div class="modal-content border-0 shadow">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title">
                        <i class="bi bi-people me-2"></i> Preview de Clientes Extraídos
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-4">
                    <div class="alert alert-info border-0 shadow-sm d-flex align-items-center">
                        <i class="bi bi-info-circle fs-4 me-3"></i>
                        <div>
                            Foram extraídos <strong>${data.total}</strong> clientes com inteligência artificial.
                        </div>
                    </div>
                    <div class="table-responsive" style="max-height: 500px;">
                        <table class="table table-sm table-hover align-middle">
                            <thead class="table-light sticky-top">
                                <tr>
                                    <th>Nome</th>
                                    <th>CPF/CNPJ</th>
                                    <th>Telefone</th>
                                    <th>Endereço</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.preview.map(c => `
                                    <tr>
                                        <td class="fw-bold">${c.nome || '-'}</td>
                                        <td><code>${c.cpf_cnpj || '-'}</code></td>
                                        <td>${c.telefone || '-'}</td>
                                        <td><small class="text-muted">${c.endereco ? (c.endereco.length > 50 ? c.endereco.substring(0, 50) + '...' : c.endereco) : '-'}</small></td>
                                        <td>
                                            ${c.status === 'ATIVO'
            ? '<span class="badge bg-success">ATIVO</span>'
            : '<span class="badge bg-secondary">' + (c.status || 'N/A') + '</span>'}
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer bg-light">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>
                    <button type="button" class="btn btn-primary px-4" onclick="confirmarImportacaoClientes('${data.file_path}')">
                        <i class="bi bi-check-circle me-2"></i> Confirmar Importação
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modalElement);
    const bsModal = new bootstrap.Modal(modalElement);
    bsModal.show();
}

function showContratosPreview(data) {
    const modalId = 'contratosPreviewModal';
    let modalElement = document.getElementById(modalId);
    if (modalElement) modalElement.remove();

    modalElement = document.createElement('div');
    modalElement.className = 'modal fade';
    modalElement.id = modalId;
    modalElement.innerHTML = `
        <div class="modal-dialog modal-xl">
            <div class="modal-content border-0 shadow">
                <div class="modal-header bg-dark text-white">
                    <h5 class="modal-title">
                        <i class="bi bi-file-contract me-2"></i> Preview de Contratos Detectados
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-4">
                    <div class="alert alert-info border-0 shadow-sm d-flex align-items-center">
                        <i class="bi bi-robot fs-4 me-3"></i>
                        <div>
                            Foram estruturados <strong>${data.total}</strong> contratos encontrados na planilha.
                        </div>
                    </div>
                    <div class="table-responsive" style="max-height: 500px;">
                        <table class="table table-sm table-hover align-middle">
                            <thead class="table-light sticky-top">
                                <tr>
                                    <th>Nº Contrato</th>
                                    <th>Tipo</th>
                                    <th>Cliente</th>
                                    <th>Vigência</th>
                                    <th>Valor</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.preview.map(c => `
                                    <tr>
                                        <td><code>${c.numero_contrato || '-'}</code></td>
                                        <td><small>${c.tipo_contrato || '-'}</small></td>
                                        <td class="fw-bold">${c.cliente || '-'}</td>
                                        <td>
                                            <small>
                                                ${c.data_inicio || '-'}
                                                ${c.data_fim ? '<br>até ' + c.data_fim : '<br>(Indeterminado)'}
                                            </small>
                                        </td>
                                        <td class="text-success fw-bold">
                                            ${c.valor_mensal
            ? 'R$ ' + c.valor_mensal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
            : '-'}
                                        </td>
                                        <td>
                                            ${c.status === 'Ativo'
            ? '<span class="badge bg-success">Ativo</span>'
            : c.status === 'Expirado'
                ? '<span class="badge bg-warning">Expirado</span>'
                : '<span class="badge bg-secondary">' + (c.status || 'N/A') + '</span>'}
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="modal-footer bg-light">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Fechar</button>
                    <button type="button" class="btn btn-dark px-4" onclick="confirmarImportacaoContratos('${data.file_path}')">
                        <i class="bi bi-check-circle me-2"></i> Confirmar Processamento
                    </button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modalElement);
    const bsModal = new bootstrap.Modal(modalElement);
    bsModal.show();
}

function confirmarImportacaoClientes(filePath) {
    if (confirm('Deseja realmente importar estes clientes para o sistema?')) {
        // Chamar API de execução de importação real
        executarImportacaoAPI('clientes', filePath);
    }
}

function confirmarImportacaoContratos(filePath) {
    if (confirm('Deseja realmente importar estes contratos para o sistema?')) {
        executarImportacaoAPI('contratos', filePath);
    }
}

async function executarImportacaoAPI(moduleType, filePath) {
    try {
        const response = await fetch('/importador/api/import/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                module_type: moduleType,
                file_path: filePath
            })
        });

        const data = await response.json();
        if (data.success) {
            alert('Importação iniciada com sucesso! Redirecionando para o histórico...');
            window.location.href = '/importador/importacoes/';
        } else {
            alert('Erro na importação: ' + data.detail);
        }
    } catch (error) {
        alert('Erro ao conectar com o servidor: ' + error.message);
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
