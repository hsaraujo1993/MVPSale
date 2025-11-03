// Extrai csrftoken e expõe utilitário
(function(){
  function getCookie(name){
    const cookies = document.cookie ? document.cookie.split('; ') : [];
    for (const c of cookies){ const [k,v] = c.split('='); if(k===name) return decodeURIComponent(v); }
    return null;
  }
  window.getCsrfToken = () => getCookie('csrftoken');
})();

