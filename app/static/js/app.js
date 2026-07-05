function formatRupiah(value) {
    if (!value || isNaN(value)) return 'Rp 0';
    return 'Rp ' + Math.round(value).toLocaleString('id-ID');
}

function formatNumber(value) {
    if (!value || isNaN(value)) return '0';
    return Number(value).toLocaleString('id-ID');
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    toast.className = `${colors[type] || colors.info} text-white px-4 py-3 rounded-lg shadow-lg mb-2 transition-all duration-300 transform translate-x-0`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Alpine.js + HTMX integration: re-init Alpine directives after HTMX swaps
document.addEventListener('htmx:afterSettle', function(evt) {
    if (evt.detail.target) {
        Alpine.initTree(evt.detail.target);
    }
});
