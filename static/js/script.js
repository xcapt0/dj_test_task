const form = document.querySelector('form');

form.addEventListener('submit', function(e) {
    e.preventDefault();
    const input = document.querySelector('.searchTerm');
    window.location.href = '/search?url=' + input.value;
})