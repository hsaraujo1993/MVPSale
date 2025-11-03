// UI helpers (toasts and modals integration placeholder)
window.UI = {
  confirm(message, onConfirm, title, type) {
    try {
      window.dispatchEvent(new CustomEvent('show-confirm', { detail: { title: title || 'Confirmar', message, onConfirm, type } }));
    } catch(e) {
      if (confirm(message)) onConfirm && onConfirm();
    }
  }
};
