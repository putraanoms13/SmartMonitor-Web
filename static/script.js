function navigate(url, element) {
    // 1. Tambahkan class CSS untuk mengecilkan tombol
    element.classList.add('btn-clicked');
    
    // 2. Tunggu 200 milidetik (0.2 detik) agar animasi terlihat
    setTimeout(() => {
        // Hilangkan class efek klik
        element.classList.remove('btn-clicked');
        
        // Pindah ke halaman tujuan
        window.location.href = url;
    }, 200); 
}

// Fungsi untuk memunculkan preview gambar
function previewImage(event) {
    const input = event.target;
    const preview = document.getElementById('logo-preview');
    const logoContainer = document.getElementById('logo-container');

    // Pastikan ada file yang dipilih
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            // Masukkan data gambar ke dalam tag <img>
            preview.src = e.target.result;
            preview.style.display = 'block'; // Tampilkan gambarnya
            logoContainer.style.backgroundColor = 'transparent'; // Opsional: hilangkan background putih
        }
        
        // Membaca file sebagai URL data
        reader.readAsDataURL(input.files[0]);
    }
}