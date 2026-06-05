const togglePassword = document.querySelector('#togglePassword');
const password = document.querySelector('#password');

togglePassword.addEventListener('click', function (e) {
    // Mengecek apakah tipenya password atau teks biasa
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);
    
    // Mengubah ikon mata tercoret menjadi mata terbuka
    this.classList.toggle('fa-eye');
    this.classList.toggle('fa-eye-slash');
});