/*
 * TailorDev Biblio
 */
(function() {
  function submitFiltersFormOnChange() {
    const form = document.forms['publication-list-filters'];
    form.addEventListener('change', function() {
      form.submit();
    });
  };

  function ready(fn) {
    if (document.readyState != 'loading'){
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  ready(submitFiltersFormOnChange);
})();
