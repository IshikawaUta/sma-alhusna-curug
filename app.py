from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from pymongo import MongoClient
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader
import os
from datetime import datetime
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from math import ceil # Import ceil untuk perhitungan pagination

# Memuat variabel lingkungan dari file .env
load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')

# --- Inisialisasi Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = "Harap login untuk mengakses halaman ini."
login_manager.login_message_category = "warning"

# --- Inisialisasi Flask-Mail ---
mail = Mail(app)

# --- Koneksi MongoDB ---
try:
    client = MongoClient(app.config['MONGO_URI'])
    db = client[app.config['MONGO_DB_NAME']]
    posts_collection = db.posts
    users_collection = db.users
    print("Koneksi MongoDB berhasil!")

    # --- Setup User Admin Awal (Hanya Jalankan Sekali Saat Pertama Kali Aplikasi) ---
    if users_collection.count_documents({"username": app.config['ADMIN_USERNAME']}) == 0:
        hashed_password = generate_password_hash(app.config['ADMIN_PASSWORD'], method='pbkdf2:sha256')
        users_collection.insert_one({
            "username": app.config['ADMIN_USERNAME'],
            "password_hash": hashed_password,
            "role": "admin"
        })
        print(f"User admin '{app.config['ADMIN_USERNAME']}' berhasil dibuat!")

except Exception as e:
    print(f"Error koneksi MongoDB atau setup user admin: {e}")


# --- Inisialisasi Cloudinary ---
try:
    cloudinary.config(
        cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=app.config['CLOUDINARY_API_KEY'],
        api_secret=app.config['CLOUDINARY_API_SECRET']
    )
    print("Konfigurasi Cloudinary berhasil!")
except Exception as e:
    print(f"Error konfigurasi Cloudinary: {e}")


# --- Kelas User untuk Flask-Login ---
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.password_hash = user_data['password_hash']
        self.role = user_data.get('role', 'user')

    @staticmethod
    def get(user_id):
        try:
            user_data = users_collection.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User(user_data)
            return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    @staticmethod
    def find_by_username(username):
        user_data = users_collection.find_one({"username": username})
        if user_data:
            return User(user_data)
        return None

# --- Flask-Login user_loader callback ---
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# --- Filter Jinja2 kustom untuk memformat tanggal ---
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d %B %Y'):
    if isinstance(value, datetime):
        return value.strftime(format)
    return value

# --- Rute Utama Aplikasi ---

@app.route('/')
def index():
    return render_template('index.html',
                           og_title="Beranda - Sekolah Harapan Bangsa",
                           og_description="Membangun generasi cerdas dan berkarakter melalui pendidikan inovatif.",
                           og_type="website",
                           twitter_title="Beranda - Sekolah Harapan Bangsa",
                           twitter_description="Membangun generasi cerdas dan berkarakter melalui pendidikan inovatif."
                           )

@app.route('/about')
def about():
    return render_template('about.html',
                           og_title="Tentang Kami - Sekolah Harapan Bangsa",
                           og_description="Pelajari lebih lanjut tentang visi, misi, dan komitmen Sekolah Harapan Bangsa.",
                           og_type="article",
                           twitter_title="Tentang Kami - Sekolah Harapan Bangsa",
                           twitter_description="Pelajari lebih lanjut tentang visi, misi, dan komitmen Sekolah Harapan Bangsa."
                           )

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email_sender = request.form['email']
        subject = request.form['subject']
        message_content = request.form['message']

        msg = Message(
            subject=f"Pesan dari Website Sekolah: {subject}",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[app.config['MAIL_USERNAME']],
            reply_to=email_sender
        )
        msg.body = f"""
        --- Pesan dari Formulir Kontak ---

        Nama Pengirim: {full_name}
        Email Pengirim: {email_sender}
        Subjek: {subject}

        Isi Pesan:
        {message_content}

        --- Akhir Pesan ---
        """

        try:
            mail.send(msg)
            flash("Pesan Anda telah berhasil dikirim! Kami akan segera menghubungi Anda.", "success")
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f"Maaf, terjadi kesalahan saat mengirim pesan Anda: {e}", "danger")
            print(f"Error mengirim email: {e}")

    return render_template('contact.html',
                           og_title="Kontak Kami - Sekolah Harapan Bangsa",
                           og_description="Hubungi Sekolah Harapan Bangsa untuk informasi lebih lanjut atau pertanyaan.",
                           og_type="website",
                           twitter_title="Kontak Kami - Sekolah Harapan Bangsa",
                           twitter_description="Hubungi Sekolah Harapan Bangsa untuk informasi lebih lanjut atau pertanyaan."
                           )

# --- Rute Pendaftaran SPMB ---
@app.route('/spmb_pendaftaran', methods=['GET', 'POST'])
def spmb_form():
    if request.method == 'POST':
        nama_lengkap = request.form['nama_lengkap']
        tempat_lahir = request.form['tempat_lahir']
        tanggal_lahir = request.form['tanggal_lahir']
        jenis_kelamin = request.form['jenis_kelamin']
        alamat = request.form['alamat']
        kota = request.form['kota']
        provinsi = request.form['provinsi']
        nomor_telepon = request.form['nomor_telepon']
        email_pendaftar = request.form['email_pendaftar']
        asal_sekolah = request.form['asal_sekolah']
        program_minat = request.form['program_minat']

        email_body = f"""
        --- Formulir Pendaftaran SPMB Baru ---

        Tanggal Pendaftaran: {datetime.now().strftime('%d %B %Y %H:%M:%S')}

        Detail Pendaftar:
        Nama Lengkap: {nama_lengkap}
        Tempat, Tanggal Lahir: {tempat_lahir}, {tanggal_lahir}
        Jenis Kelamin: {jenis_kelamin}
        Alamat: {alamat}, {kota}, {provinsi}
        Nomor Telepon: {nomor_telepon}
        Email Pendaftar: {email_pendaftar}
        Asal Sekolah: {asal_sekolah}
        Program Minat: {program_minat}

        --- Akhir Formulir ---
        """

        msg = Message(
            subject=f"Pendaftaran SPMB Baru: {nama_lengkap}",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[app.config['MAIL_USERNAME']],
            reply_to=email_pendaftar
        )
        msg.body = email_body

        try:
            mail.send(msg)
            flash("Pendaftaran SPMB Anda berhasil dikirim! Kami akan segera menghubungi Anda.", "success")
            return redirect(url_for('spmb_form'))
        except Exception as e:
            flash(f"Maaf, terjadi kesalahan saat mengirim pendaftaran Anda: {e}", "danger")
            print(f"Error mengirim email pendaftaran SPMB: {e}")

    return render_template('spmb_form.html',
                           og_title="Pendaftaran SPMB - Sekolah Harapan Bangsa",
                           og_description="Daftar Seleksi Penerimaan Mahasiswa Baru di Sekolah Harapan Bangsa.",
                           og_type="website",
                           twitter_title="Pendaftaran SPMB - Sekolah Harapan Bangsa",
                           twitter_description="Daftar Seleksi Penerimaan Mahasiswa Baru di Sekolah Harapan Bangsa."
                           )


@app.route('/blog')
def blog():
    page = request.args.get('page', 1, type=int)
    posts_per_page = app.config['POSTS_PER_PAGE']

    total_posts = posts_collection.count_documents({})
    total_pages = ceil(total_posts / posts_per_page)

    skip = (page - 1) * posts_per_page
    posts = list(posts_collection.find().sort("date", -1).skip(skip).limit(posts_per_page))

    return render_template('blog.html',
                           posts=posts,
                           page=page,
                           total_pages=total_pages,
                           og_title="Blog Sekolah - Berita dan Artikel Terbaru",
                           og_description="Ikuti berita terbaru, pengumuman, dan kisah inspiratif dari Sekolah Harapan Bangsa.",
                           og_type="blog",
                           twitter_title="Blog Sekolah - Berita dan Artikel Terbaru",
                           twitter_description="Ikuti berita terbaru, pengumuman, dan kisah inspiratif dari Sekolah Harapan Bangsa."
                           )

@app.route('/blog/<post_id>')
def blog_post(post_id):
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            flash("Postingan tidak ditemukan.", "danger")
            return redirect(url_for('blog'))

        # Set meta tags dari data postingan blog
        post_title = post.get('title', 'Postingan Blog')
        post_description = post.get('content', '')[:160] + '...' if len(post.get('content', '')) > 160 else post.get('content', '')
        post_image = post.get('image_url', url_for('static', filename='img/logo.png', _external=True))

        return render_template('blog_post.html',
                               post=post,
                               og_title=post_title,
                               og_description=post_description,
                               og_image=post_image,
                               og_type="article",
                               twitter_title=post_title,
                               twitter_description=post_description,
                               twitter_image=post_image
                               )
    except Exception as e:
        flash(f"Terjadi kesalahan saat mengambil postingan: {e}", "danger")
        return redirect(url_for('blog'))

# --- Rute Admin (dengan Flask-Login) ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.find_by_username(username)

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Login berhasil! Selamat datang, {user.username}.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Username atau password salah.", "danger")
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash("Anda telah logout.", "info")
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    posts = list(posts_collection.find().sort("date", -1))
    return render_template('admin/dashboard.html', posts=posts)

@app.route('/admin/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')

        image_url = None
        if image and image.filename != '':
            try:
                upload_result = cloudinary.uploader.upload(image)
                image_url = upload_result['secure_url']
                flash("Gambar berhasil diunggah.", "info")
            except Exception as e:
                flash(f"Gagal mengunggah gambar: {e}", "danger")
                image_url = None

        new_post = {
            "title": title,
            "content": content,
            "image_url": image_url,
            "date": datetime.now()
        }
        posts_collection.insert_one(new_post)
        flash("Postingan baru berhasil ditambahkan!", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_post.html')

@app.route('/admin/edit_post/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            flash("Postingan tidak ditemukan.", "danger")
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            image = request.files.get('image')

            image_url = post.get('image_url')
            if image and image.filename != '':
                try:
                    if image_url:
                        public_id = image_url.split('/')[-1].split('.')[0]
                        cloudinary.uploader.destroy(public_id)
                        flash(f"Gambar lama ({public_id}) dihapus.", "info")
                    upload_result = cloudinary.uploader.upload(image)
                    image_url = upload_result['secure_url']
                    flash("Gambar baru berhasil diunggah.", "info")
                except Exception as e:
                    flash(f"Gagal mengunggah gambar baru: {e}", "danger")
                    image_url = post.get('image_url')

            posts_collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$set": {"title": title, "content": content, "image_url": image_url, "date": datetime.now()}}
            )
            flash("Postingan berhasil diperbarui!", "success")
            return redirect(url_for('admin_dashboard'))
        return render_template('admin/edit_post.html', post=post)
    except Exception as e:
        flash(f"Terjadi kesalahan saat mengedit postingan: {e}", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_post/<post_id>')
@login_required
def delete_post(post_id):
    try:
        post = posts_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            flash("Postingan tidak ditemukan.", "danger")
            return redirect(url_for('admin_dashboard'))

        if post.get('image_url'):
            try:
                public_id = post['image_url'].split('/')[-1].split('.')[0]
                cloudinary.uploader.destroy(public_id)
                flash(f"Gambar ({public_id}) berhasil dihapus dari Cloudinary.", "info")
            except Exception as e:
                print(f"Error menghapus gambar dari Cloudinary: {e}")

        posts_collection.delete_one({"_id": ObjectId(post_id)})
        flash("Postingan berhasil dihapus!", "success")
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f"Terjadi kesalahan saat menghapus postingan: {e}", "danger")
        return redirect(url_for('admin_dashboard'))


# --- Penanganan Error Kustom ---
@app.errorhandler(404)
def page_not_found(e):
    """Handler untuk error 404 (Halaman Tidak Ditemukan)."""
    return render_template('404.html',
                           og_title="404 Halaman Tidak Ditemukan",
                           og_description="Maaf, halaman yang Anda cari tidak dapat ditemukan.",
                           og_type="website",
                           twitter_title="404 Halaman Tidak Ditemukan",
                           twitter_description="Maaf, halaman yang Anda cari tidak dapat ditemukan."
                           ), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handler untuk error 500 (Kesalahan Server Internal)."""
    return render_template('500.html',
                           og_title="500 Kesalahan Server Internal",
                           og_description="Maaf, terjadi kesalahan tak terduga pada server kami.",
                           og_type="website",
                           twitter_title="500 Kesalahan Server Internal",
                           twitter_description="Maaf, terjadi kesalahan tak terduga pada server kami."
                           ), 500

# --- Rute robots.txt ---
@app.route('/robots.txt')
def robots_txt():
    """Menyajikan file robots.txt untuk crawler mesin pencari."""
    # Anda bisa menyesuaikan aturan ini.
    # Disallow: /admin/ mencegah crawler mengakses halaman admin.
    return Response("User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: " + request.url_root + "sitemap.xml", mimetype="text/plain")

# --- Rute sitemap.xml ---
@app.route('/sitemap.xml')
def sitemap_xml():
    """Menyajikan file sitemap.xml dinamis."""
    # Daftar URL statis yang ingin Anda masukkan di sitemap
    static_urls = [
        url_for('index', _external=True),
        url_for('about', _external=True),
        url_for('contact', _external=True),
        url_for('blog', _external=True),
        url_for('spmb_form', _external=True),
    ]

    # Tambahkan URL postingan blog dari MongoDB
    blog_posts = posts_collection.find({}, {"_id": 1}).sort("date", -1) # Ambil hanya ID dan urutkan
    for post in blog_posts:
        static_urls.append(url_for('blog_post', post_id=str(post['_id']), _external=True))

    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for url in static_urls:
        sitemap_content += f'<url><loc>{url}</loc><lastmod>{datetime.now().isoformat()}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>\n'

    sitemap_content += '</urlset>'

    return Response(sitemap_content, mimetype="application/xml")


if __name__ == '__main__':
    app.run(debug=True)
