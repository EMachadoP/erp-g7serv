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

document.addEventListener('DOMContentLoaded', function() {
    initAutoRefresh();
});
