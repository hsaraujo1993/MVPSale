// Normalize common mojibake on Sales page without relying on file encoding
(function(){
  try {
    function normalizeText(s){
      if (!s) return s;
      var t = String(s);
      // Preço
      t = t.replace(/PreÃ§o|Pre\?\?o|Pre\?o|Pre�o|PreÃo|Preco/g, 'Pre\u00E7o');
      // Unitário
      t = t.replace(/UnitÃ¡rio|Unit\?rio|Unit�rio|Unitario|Unitorio/g, 'Unit\u00E1rio');
      // Código
      t = t.replace(/cÃ³digo|c\?digo/g, 'c\u00F3digo');
      // Não
      t = t.replace(/nÃ£o|n\?o/g, 'n\u00E3o');
      // Descrição
      t = t.replace(/DescriÃ§Ã£o|Descri\?\?o/g, 'Descri\u00E7\u00E3o');
      // Ações
      t = t.replace(/AÃ§\u00F5es|A\?\?es|Acoes/g, 'A\u00E7\u00F5es');
      return t;
    }

    // fix placeholder (uses unicode escapes)
    var inp = document.querySelector('input[x-model="search"]');
    if (inp) inp.setAttribute('placeholder', 'Buscar produto (nome, c\u00F3digo, c\u00F3digo de barras)');

    // fix common text containers
    document.querySelectorAll('th, label, button, h1, h2, h3, span, option').forEach(function(el){
      var before = el.textContent || '';
      var after = normalizeText(before);
      if (after !== before) el.textContent = after;
    });

    // fix toasts
    if (window.Http && typeof window.Http.toast === 'function') {
      var _toast = window.Http.toast;
      window.Http.toast = function(message, type){
        try { message = normalizeText(String(message)); } catch(e) {}
        return _toast(message, type);
      }
    }
  } catch(e) {}
})();

