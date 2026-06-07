from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import random
import os
from werkzeug.utils import secure_filename

# IMPORT FIREBASE ADMIN SDK
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

app.secret_key = 'kunci_rahasia_smartmonitor_super_aman'
s = URLSafeTimedSerializer(app.secret_key)

# ==========================================
# KONFIGURASI UPLOAD FOTO
# ==========================================
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# KONFIGURASI FIREBASE CLOUD FIRESTORE
# ==========================================
# Membaca file kunci rahasia JSON dari Firebase Console yang kamu taruh di folder utama
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

# Inisialisasi Database Firestore
db = firestore.client()

# ==========================================
# KONFIGURASI FLASK-MAIL
# ==========================================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'smartmonitor335@gmail.com' 
app.config['MAIL_PASSWORD'] = 'rtjcfxidlpwriadv'    
app.config['MAIL_DEFAULT_SENDER'] = 'smartmonitor335@gmail.com'
mail = Mail(app)

# ==========================================
# ROUTING HALAMAN
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/masuk', methods=['GET', 'POST'])
def masuk():
    if request.method == 'POST':
        email_input = request.form.get('email')
        password_input = request.form.get('password')
        
        # Mengambil data dari dokumen dokumen 'email' di collection 'users'
        user_ref = db.collection('users').document(email_input)
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
            # Validasi hash password
            if check_password_hash(user_data['password'], password_input):
                session['user_id'] = email_input  # Gunakan email sebagai ID unik session
                session['nama'] = user_data['nama']
                return redirect(url_for('dashboard'))
        
        flash('Email atau kata sandi salah! Silakan coba lagi.', 'error')
        return render_template('auth.html', active_tab='login')
            
    return render_template('auth.html', active_tab='login')

@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
    if request.method == 'POST':
        nama = request.form.get('nama')
        email = request.form.get('email')
        password = request.form.get('password')

        # Cek apakah dokumen email sudah ada di Firebase
        user_ref = db.collection('users').document(email)
        if user_ref.get().exists:
            flash('Email tersebut sudah terdaftar! Silakan langsung masuk.', 'error')
            return render_template('auth.html', active_tab='register')

        # Eksekusi penyimpanan data baru ke Firebase Firestore
        hashed_password = generate_password_hash(password)
        user_ref.set({
            'nama': nama,
            'email': email,
            'password': hashed_password,
            'foto_profil': 'polines.png'
        })
        
        flash('Pendaftaran berhasil! Silakan login.', 'success')
        return redirect(url_for('masuk'))
        
    return render_template('auth.html', active_tab='register')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    
    user_ref = db.collection('users').document(session['user_id'])
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return redirect(url_for('keluar'))
        
    return render_template('dashboard.html', user=user_doc.to_dict())

@app.route('/pengaturan', methods=['GET', 'POST'])
def pengaturan():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    
    user_ref = db.collection('users').document(session['user_id'])
    user_data = user_ref.get().to_dict()
    
    if request.method == 'POST':
        nama_baru = request.form.get('nama')
        email_baru = request.form.get('email')
        password_baru = request.form.get('password')
        foto_baru = request.files.get('foto_profil')
        
        update_data = {}

        # PROSES UNGGAH FOTO
        if foto_baru and foto_baru.filename != '':
            if allowed_file(foto_baru.filename):
                filename = secure_filename(foto_baru.filename)
                # Membuat nama file unik berdasarkan session ID (email)
                nama_file_unik = f"user_{session['user_id'].replace('@', '_')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], nama_file_unik)
                
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                    
                foto_baru.save(filepath)
                update_data['foto_profil'] = nama_file_unik
            else:
                flash('Format foto tidak didukung.', 'error')
                return redirect(url_for('pengaturan'))

        if nama_baru:
            update_data['nama'] = nama_baru
            session['nama'] = nama_baru
            
        if password_baru:
            update_data['password'] = generate_password_hash(password_baru)
            
        # Jika ada data yang diubah, lakukan pembaruan dokumen di Firebase
        if update_data:
            user_ref.update(update_data)
            
        flash('Profil berhasil diperbarui!', 'success')
        return redirect(url_for('pengaturan'))
    
    return render_template('pengaturan.html', user=user_data)

@app.route('/smartcane')
def smartcane():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    user_ref = db.collection('users').document(session['user_id'])
    return render_template('smartcane.html', user=user_ref.get().to_dict())

@app.route('/smartglasses')
def smartglasses():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    user_ref = db.collection('users').document(session['user_id'])
    return render_template('smartglasses.html', user=user_ref.get().to_dict())

@app.route('/riwayat-sos')
def riwayat_sos():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    return render_template('riwayat_sos.html')

# ==========================================
# API TRIGGER EMERGENSI SOS (MEMBACA DATA FIREBASE GLOBLAL)
# ==========================================
@app.route('/trigger-sos-email', methods=['POST'])
def trigger_sos_email():
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    
    # 1. Ambil SEMUA dokumen dari collection 'users' di Firebase
    users_ref = db.collection('users')
    docs = users_ref.stream()
    
    # 2. Ambil list email dari seluruh dokumen
    daftar_email = [doc.to_dict().get('email') for doc in docs if doc.to_dict().get('email')]
            
    if not daftar_email:
        print("⚠️ SOS Terdeteksi: Tapi tidak ada user terdaftar di Firebase.")
        return jsonify({"status": "warning", "message": "Tidak ada user terdaftar"}), 200
        
    link_riwayat = url_for('riwayat_sos', _external=True)
    link_maps = f"https://maps.google.com/?q={lat},{lng}"
    
    # 3. Tembakkan email SOS massal
    try:
        msg = Message("[EMERGENCY] Panggilan SOS Tunanetra!", recipients=daftar_email)
        msg.body = f"Bahaya! Pengguna Smartcane baru saja menekan tombol darurat SOS.\n\nLokasi terakhir (Google Maps): {link_maps}\n\nLihat Log Riwayat Lengkap di Website:\n{link_riwayat}"
        mail.send(msg)
        print(f"✅ BERHASIL: Email SOS Firebase dikirim ke -> {daftar_email}")
        return jsonify({"status": "success", "message": f"Email SOS berhasil dikirim!"})
    except Exception as e:
        print(f"❌ GAGAL KIRIM EMAIL SOS: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/kirim-kode', methods=['POST'])
def kirim_kode():
    data = request.get_json()
    email_tujuan = data.get('email')
    if email_tujuan:
        kode_otp = str(random.randint(100000, 999999))
        try:
            msg = Message("Kode Verifikasi SmartMonitor", recipients=[email_tujuan])
            msg.body = f"Halo!\n\nKode verifikasi pendaftaran Anda adalah: {kode_otp}"
            mail.send(msg)
            return jsonify({"status": "sukses", "pesan": "Kode terkirim"})
        except Exception as e:
            return jsonify({"status": "gagal", "pesan": str(e)}), 500
    return jsonify({"status": "gagal", "pesan": "Email tidak valid"}), 400

@app.route('/keluar')
def keluar():
    session.clear()
    return redirect(url_for('index'))

@app.route('/lupa-kata-sandi', methods=['GET', 'POST'])
def lupa_kata_sandi():
    if request.method == 'POST':
        email = request.form.get('email')
        user_ref = db.collection('users').document(email)
        
        if user_ref.get().exists:
            token = s.dumps(email, salt='email-reset-salt')
            link = url_for('reset_password', token=token, _external=True)
            try:
                msg = Message("Pemulihan Kata Sandi SmartMonitor", recipients=[email])
                msg.body = f"Klik tautan ini untuk mereset kata sandi akun SmartMonitor Anda: {link}"
                mail.send(msg)
                flash('Tautan pemulihan telah berhasil dikirim!', 'success')
            except Exception:
                flash('Gagal mengirim email.', 'error')
        else:
            flash('Email tidak terdaftar.', 'error')
        return redirect(url_for('lupa_kata_sandi'))
    return render_template('lupa_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='email-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('Tautan kedaluwarsa.', 'error')
        return redirect(url_for('lupa_kata_sandi'))
    except Exception:
        flash('Tautan tidak valid.', 'error')
        return redirect(url_for('lupa_kata_sandi'))
        
    if request.method == 'POST':
        password_baru = request.form.get('password')
        user_ref = db.collection('users').document(email)
        
        if user_ref.get().exists:
            hashed_password = generate_password_hash(password_baru)
            user_ref.update({'password': hashed_password}) # Perbarui password di Firebase
            flash('Kata sandi berhasil diatur ulang!', 'success')
            return redirect(url_for('masuk'))
            
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)