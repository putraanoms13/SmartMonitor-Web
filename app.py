from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import random
import os
from werkzeug.utils import secure_filename

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
# KONFIGURASI DATABASE
# ==========================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartmonitor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    foto_profil = db.Column(db.String(100), default='polines.png')

    def __init__(self, nama, email, password, foto_profil='polines.png'):
        self.nama = nama
        self.email = email
        self.password = password
        self.foto_profil = foto_profil

with app.app_context():
    db.create_all()

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
        user = User.query.filter_by(email=email_input).first()

        if user and check_password_hash(user.password, password_input):
            session['user_id'] = user.id
            session['nama'] = user.nama
            return redirect(url_for('dashboard'))
        else:
            flash('Email atau kata sandi salah! Silakan coba lagi.', 'error')
            # Jika error, kembalikan ke auth.html dan pastikan tab 'login' yang terbuka
            return render_template('auth.html', active_tab='login')
            
    return render_template('auth.html', active_tab='login')

@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
    if request.method == 'POST':
        nama = request.form.get('nama')
        email = request.form.get('email')
        password = request.form.get('password')

        user_exist = User.query.filter_by(email=email).first()
        if user_exist:
            flash('Email tersebut sudah terdaftar! Silakan langsung masuk.', 'error')
            # Jika error, kembalikan ke auth.html dan pastikan tab 'register' yang terbuka
            return render_template('auth.html', active_tab='register')

        hashed_password = generate_password_hash(password)
        new_user = User(nama=nama, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Pendaftaran berhasil! Silakan login.', 'success')
        return redirect(url_for('masuk'))
        
    return render_template('auth.html', active_tab='register')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    user_aktif = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user_aktif)

@app.route('/pengaturan', methods=['GET', 'POST'])
def pengaturan():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    
    user_aktif = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        nama_baru = request.form.get('nama')
        email_baru = request.form.get('email')
        password_baru = request.form.get('password')
        foto_baru = request.files.get('foto_profil')
        
        # PROSES UNGGAH FOTO
        if foto_baru and foto_baru.filename != '':
            if allowed_file(foto_baru.filename):
                filename = secure_filename(foto_baru.filename)
                nama_file_unik = f"user_{user_aktif.id}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], nama_file_unik)
                
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                    
                foto_baru.save(filepath)
                user_aktif.foto_profil = nama_file_unik
            else:
                flash('Format foto tidak didukung.', 'error')
                return redirect(url_for('pengaturan'))

        if nama_baru:
            user_aktif.nama = nama_baru
            session['nama'] = nama_baru
        if email_baru and email_baru != user_aktif.email:
            cek_email = User.query.filter_by(email=email_baru).first()
            if cek_email:
                flash('Email sudah terdaftar pada akun lain!', 'error')
                return redirect(url_for('pengaturan'))
            user_aktif.email = email_baru
        if password_baru:
            user_aktif.password = generate_password_hash(password_baru)
            
        db.session.commit()
        flash('Profil berhasil diperbarui!', 'success')
        return redirect(url_for('pengaturan'))
    
    return render_template('pengaturan.html', user=user_aktif)

@app.route('/smartcane')
def smartcane():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    user_aktif = User.query.get(session['user_id'])
    return render_template('smartcane.html', user=user_aktif)

@app.route('/smartglasses')
def smartglasses():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    user_aktif = User.query.get(session['user_id'])
    return render_template('smartglasses.html', user=user_aktif)

@app.route('/riwayat-sos')
def riwayat_sos():
    if 'user_id' not in session:
        return redirect(url_for('masuk'))
    return render_template('riwayat_sos.html')

# ==========================================
# API BARU: TRIGGER KIRIM EMAIL SOS KE SEMUA USER
# ==========================================
@app.route('/trigger-sos-email', methods=['POST'])
def trigger_sos_email():
    data = request.get_json()
    lat = data.get('lat')
    lng = data.get('lng')
    
    # 1. Ambil SEMUA data user dari database SQLite
    semua_user = User.query.all()
    
    # 2. Kumpulkan semua alamat emailnya ke dalam satu list
    daftar_email = [user.email for user in semua_user if user.email]
            
    if not daftar_email:
        print("⚠️ SOS Terdeteksi: Tapi tidak ada user terdaftar di database.")
        return jsonify({"status": "warning", "message": "Tidak ada user terdaftar"}), 200
        
    link_riwayat = url_for('riwayat_sos', _external=True)
    link_maps = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
    
    # 3. Tembakkan email ke semua alamat sekaligus
    try:
        msg = Message("[EMERGENCY] Panggilan SOS Tunanetra!", recipients=daftar_email)
        msg.body = f"Bahaya! Pengguna Smartcane baru saja menekan tombol darurat SOS.\n\nLokasi terakhir (Google Maps): {link_maps}\n\nLihat Log Riwayat Lengkap di Website:\n{link_riwayat}"
        mail.send(msg)
        print(f"✅ BERHASIL: Email SOS dikirim ke -> {daftar_email}")
        return jsonify({"status": "success", "message": f"Email SOS berhasil dikirim!"})
    except Exception as e:
        print(f"❌ GAGAL KIRIM EMAIL: {str(e)}") # Membantu melacak error di terminal
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
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(email, salt='email-reset-salt')
            link = url_for('reset_password', token=token, _external=True)
            try:
                msg = Message("Pemulihan Kata Sandi SmartMonitor", recipients=[email])
                msg.body = f"Klik tautan ini untuk reset: {link}"
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
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password_baru)
            db.session.commit()
            flash('Kata sandi berhasil diatur ulang!', 'success')
            return redirect(url_for('masuk'))
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)