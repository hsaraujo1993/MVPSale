// Small helper to manage form submissions: sets loading state, handles field errors and shows toast
(function(){
  function setLoading(button, isLoading){
    if(!button) return;
    if(isLoading){
      button.setAttribute('disabled','disabled');
      button.dataset.origText = button.innerHTML;
      button.innerHTML = '<span class="opacity-80">Carregando...</span>';
    } else {
      button.removeAttribute('disabled');
      if(button.dataset.origText) button.innerHTML = button.dataset.origText;
    }
  }

  function clearFieldErrors(form){
    form.querySelectorAll('.field-error').forEach(el=> el.remove());
    form.querySelectorAll('[aria-invalid]').forEach(el=> el.removeAttribute('aria-invalid'));
  }

  function showFieldErrors(form, errors){
    if(!errors || typeof errors !== 'object') return;
    for(const key of Object.keys(errors)){
      const messages = errors[key];
      // try to find input/select/textarea with name=key or id variants (exact id, suffix with - or _, or contains)
      const selectors = [
        `[name="${key}"]`,
        `#${key}`,
        `[id$="-${key}"]`,
        `[id$="_${key}"]`,
        `[id*="-${key}"]`,
        `[id*="_${key}"]`,
      ];
      let field = null;
      for(const sel of selectors){ if(!field) field = form.querySelector(sel); }
      // fallback: try inputs with data-field attribute
      if(!field) field = form.querySelector(`[data-field="${key}"]`);
      if(field){
        field.setAttribute('aria-invalid','true');
        const wrap = document.createElement('div'); wrap.className='field-error text-rose-400 text-sm mt-1';
        wrap.textContent = (Array.isArray(messages)? messages.join('; '): String(messages));
        field.insertAdjacentElement('afterend', wrap);
      } else {
        // fallback to toast
        window.Http.toast(Array.isArray(errors[key])? errors[key].join('; '): String(errors[key]), 'error');
      }
    }
  }

  window.FormUtils = { setLoading, clearFieldErrors, showFieldErrors };
})();
