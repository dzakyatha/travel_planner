[![CI Pipeline](https://github.com/dzakyatha/travel_planner/actions/workflows/main.yml/badge.svg)](https://github.com/dzakyatha/travel_planner/actions/workflows/main.yml)

# Travel Planner API

Repo ini berisikan API untuk perencanaan perjalanan yang diimplementasikan menggunakan **Domain-Driven Design (DDD)**. Repo ini dibuat untuk memenuhi **Tugas Besar** mata kuliah **II3160 - Teknologi Sistem Terintegrasi**. Proyek ini menggunakan **FastAPI** sebagai framework web dan menerapkan prinsip-prinsip DDD dengan **Value Objects**, **Entities**, dan **Aggregate Root**.

## 📋 Fitur

- Membuat dan mengelola rencana perjalanan
- Menambahkan hari dan aktivitas dalam rencana perjalanan
- Mengelola anggaran dan pengeluaran rencana perjalanan
- Validasi bisnis/invariants untuk menjaga integritas data
- Autentikasi berbasis **JWT** dengan **OAuth2 Password Flow** (protected endpoints)
- Database persistence menggunakan **SQLModel** (SQLite/PostgreSQL)
- Continuous Integration dengan GitHub Actions

## 🏗️ Arsitektur

Proyek ini mengimplementasikan **Domain-Driven Design (DDD)** dengan struktur:

### Value Objects
- [`Uang`](models/value_objects.py) - Representasi nilai moneter dengan validasi
- [`Durasi`](models/value_objects.py) - Rentang waktu perjalanan
- [`Lokasi`](models/value_objects.py) - Informasi lokasi dengan koordinat

### Entities
- [`HariPerjalanan`](models/entity.py) - Satu hari dalam rencana perjalanan
- [`Aktivitas`](models/entity.py) - Kegiatan terjadwal dalam satu hari
- [`Pengeluaran`](models/entity.py) - Pengeluaran uang dalam perjalanan

### Aggregate Root
- [`RencanaPerjalanan`](models/aggregate_root.py) - Titik masuk utama untuk memodifikasi state, mengelola invariants bisnis

### Business Rules (Invariants)
1. Total pengeluaran tidak boleh melebihi anggaran
2. Hari perjalanan dan pengeluaran harus dalam rentang durasi rencana perjalanan
3. Aktivitas dalam satu hari rencana perjalanan tidak boleh tumpang tindih waktu
4. Update durasi rencana perjalanan harus mencakup semua hari dan pengeluaran yang sudah ada

## 🚀 Cara Menjalankan Program

### Prasyarat
- Python >= 3.13
- `uv` package manager

### Langkah Instalasi

1. **Clone repository**
   ```bash
   git clone <repository-url>
   cd travel_planner
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Install dev dependencies (untuk testing)**
   ```bash
   uv sync --extra dev
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Atau generate SECRET_KEY baru:
   ```bash
   uv run security/generate_key.py
   ```
   
   Lalu simpan output ke file `.env`:
   ```
   SECRET_KEY=hasil_generated_key
   DATABASE_URL=sqlite:///./local_travel.db
   ```

## 🔐 Konfigurasi Autentikasi & JWT

Autentikasi menggunakan **JWT** dengan **OAuth2PasswordBearer**.

- **SECRET_KEY**
  - Disimpan di environment variable `SECRET_KEY`.
  - Untuk generate key baru:
    ```bash
    uv run security/generate_key.py
    ```
  - Minimal 32 karakter untuk keamanan

- **Password Hashing**
  - Menggunakan `passlib` dengan algoritma `bcrypt`.
  - Versi `bcrypt` dipin di [pyproject.toml](pyproject.toml) agar kompatibel dengan `passlib`.
  - Helper untuk generate password hash: `uv run security/hash.py`

- **User Dummy (In-Memory)**
  - Didefinisikan di [`fake_users_db`](security/security.py) dalam [security/security.py](security/security.py).
  - User yang tersedia:
    - `username`: **johndoe**, `password`: **rahasia**
    - `username`: **alice**, `password`: **rahasia2**

Semua endpoint di bawah prefix `/api/perencanaan` membutuhkan **Bearer token** di header:

```http
Authorization: Bearer <access_token>
```

## 💾 Database

Proyek ini menggunakan **SQLModel** yang mendukung SQLite dan PostgreSQL:

- **Development**: SQLite (default)
  ```
  DATABASE_URL=sqlite:///./local_travel.db
  ```

- **Production**: PostgreSQL
  ```
  DATABASE_URL=postgresql://user:password@host:port/dbname
  ```

Database akan otomatis diinisialisasi saat aplikasi dijalankan (lihat [database.py](database.py)).

## 💻 Penggunaan

### Menjalankan Server

```bash
uv run main.py
```

atau

```bash
uv run uvicorn main:app --reload
```

Server akan berjalan di `http://127.0.0.1:8000`

### Dokumentasi API

Setelah server berjalan, akses dokumentasi interaktif:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Login & Mendapatkan Token di Swagger UI

1. Buka `http://127.0.0.1:8000/docs`.
2. Klik tombol **Authorize** (ikon gembok).
3. Isi:
   - **Username**: `johndoe`
   - **Password**: `rahasia`
4. Klik **Authorize** lalu **Close**.
5. Setelah itu, semua request ke endpoint `/api/perencanaan/...` dari Swagger akan otomatis menyertakan token.

Response:
```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

Gunakan nilai `access_token` di header `Authorization` untuk memanggil endpoint lain.

## 📡 API Endpoints

> **Catatan**: Semua endpoint di bawah `/api/perencanaan` memerlukan header `Authorization: Bearer <access_token>`.

### Autentikasi

| Method | Endpoint             | Deskripsi                       |
|--------|----------------------|---------------------------------|
| POST   | `/api/auth/token`   | Login dan mendapatkan JWT token |

### Rencana Perjalanan

| Method | Endpoint                                     | Deskripsi                       |
|--------|----------------------------------------------|---------------------------------|
| POST   | `/api/perencanaan/`                         | Membuat rencana perjalanan baru |
| GET    | `/api/perencanaan/{rencana_id}`             | Mendapatkan rencana perjalanan  |
| PUT    | `/api/perencanaan/{rencana_id}/anggaran`    | Update anggaran                 |
| PUT    | `/api/perencanaan/{rencana_id}/durasi`      | Update durasi                   |

### Hari Perjalanan

| Method | Endpoint                                        | Deskripsi                   |
|--------|-------------------------------------------------|-----------------------------|
| POST   | `/api/perencanaan/{rencana_id}/hari`           | Menambahkan hari perjalanan |
| DELETE | `/api/perencanaan/{rencana_id}/hari/{tanggal}` | Menghapus hari perjalanan   |

### Aktivitas

| Method | Endpoint                                                      | Deskripsi                     |
|--------|---------------------------------------------------------------|-------------------------------|
| POST   | `/api/perencanaan/{rencana_id}/hari/{tanggal}/aktivitas`    | Menambahkan aktivitas ke hari |

### Pengeluaran

| Method | Endpoint                                                       | Deskripsi             |
|--------|----------------------------------------------------------------|-----------------------|
| POST   | `/api/perencanaan/{rencana_id}/pengeluaran`                   | Menambahkan pengeluaran|
| DELETE | `/api/perencanaan/{rencana_id}/pengeluaran/{id_pengeluaran}` | Menghapus pengeluaran |

## 📝 Contoh Request

> Pastikan sudah memiliki `access_token` dari `/api/auth/token` dan sertakan header:
> `Authorization: Bearer <access_token>`

### Login

```http
POST /api/auth/token
Content-Type: application/x-www-form-urlencoded
```

```
username=johndoe&password=rahasia
```

### Membuat Rencana Perjalanan

```http
POST /api/perencanaan/
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "nama": "Liburan ke Bali",
  "durasi": {
    "tanggalMulai": "2024-12-01",
    "tanggalSelesai": "2024-12-07"
  },
  "anggaran": {
    "jumlah": 5000000,
    "mata_uang": "IDR"
  }
}
```

### Menambahkan Hari Perjalanan

```http
POST /api/perencanaan/{rencana_id}/hari
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "tanggal": "2024-12-03"
}
```

### Menambahkan Pengeluaran

```http
POST /api/perencanaan/{rencana_id}/pengeluaran
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "deskripsi": "Hotel",
  "biaya": {
    "jumlah": 1000000.0,
    "mata_uang": "IDR"
  },
  "tanggalPengeluaran": "2024-12-02"
}
```

### Menambahkan Aktivitas

```http
POST /api/perencanaan/{rencana_id}/hari/2024-12-01/aktivitas
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "waktuMulai": "09:00:00",
  "waktuSelesai": "12:00:00",
  "lokasi": {
    "namaLokasi": "Pantai Kuta",
    "alamat": "Kuta, Bali",
    "latitude": -8.7224,
    "longitude": 115.1707
  },
  "deskripsi": "Berjemur di pantai"
}
```

## 🧪 Testing

### Menjalankan Semua Tests

```bash
uv run pytest
```

### Menjalankan Test dengan Verbose

```bash
uv run pytest -v
```

### Menjalankan Test dengan Coverage

```bash
uv run pytest --cov=. --cov-report=html
```

Report akan tersimpan di folder `htmlcov/`.

### Menjalankan Test File Tertentu

```bash
uv run pytest tests/test_create.py
```

### Menjalankan Test Spesifik

```bash
uv run pytest tests/test_create.py::test_create_rencana_perjalanan_success
```

### Test Categories

- **Unit Tests**: Test domain logic ([tests/test_domain.py](tests/test_domain.py))
- **Integration Tests**: Test API endpoints
  - [tests/test_create.py](tests/test_create.py) - CREATE operations
  - [tests/test_get.py](tests/test_get.py) - READ operations
  - [tests/test_update.py](tests/test_update.py) - UPDATE operations
  - [tests/test_delete.py](tests/test_delete.py) - DELETE operations
- **Security Tests**: Test authentication ([tests/test_security.py](tests/test_security.py))
- **Database Tests**: Test database functions ([tests/test_init_db.py](tests/test_init_db.py))

## 📁 Struktur Proyek

```text
travel_planner/
├── .github/
│   └── workflows/          # CI/CD workflows
├── models/                 # Domain models (DDD)
│   ├── __init__.py
│   ├── aggregate_root.py   # Aggregate Root: RencanaPerjalanan
│   ├── entity.py           # Entities: HariPerjalanan, Aktivitas, Pengeluaran
│   ├── value_objects.py    # Value Objects: Uang, Durasi, Lokasi
│   └── exception.py        # Business exceptions
├── router/                 # API routing
│   ├── __init__.py
│   ├── router.py           # Main API endpoints
│   └── auth_router.py      # Authentication endpoints
├── security/               # Security & authentication
│   ├── __init__.py
│   ├── security.py         # JWT & password hashing
│   ├── generate_key.py     # Script untuk generate SECRET_KEY
│   └── hash.py             # Script helper untuk hash password
├── tests/                  # Test files
│   ├── conftest.py         # Pytest fixtures
│   ├── test_auth_router.py # Auth endpoint tests
│   ├── test_create.py      # CREATE endpoint tests
│   ├── test_delete.py      # DELETE endpoint tests
│   ├── test_domain.py      # Domain logic unit tests
│   ├── test_get.py         # GET endpoint tests
│   ├── test_update.py      # UPDATE endpoint tests
│   ├── test_security.py    # Security function tests
│   ├── test_init_db.py     # Database tests
│   └── utils.py            # Test utilities
├── database.py             # Database configuration & session
├── main.py                 # FastAPI application entry point
├── schema.py               # Pydantic schemas untuk request/response
├── pyproject.toml          # Project dependencies & config
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

## 🛠️ Tech Stack

- **uv** - Python package manager
- **FastAPI** - Web framework modern untuk Python
- **Uvicorn** - ASGI server
- **SQLModel** - SQL database ORM dengan Pydantic models
- **Pydantic** - Data validation menggunakan Python type annotations
- **pytest** - Python testing framework
- **pytest-cov** - Coverage plugin untuk pytest
- **passlib[bcrypt]** - Password hashing
- **python-jose[cryptography]** - JWT handling
- **python-dotenv** - Environment variable management
- **httpx** - HTTP client untuk testing

## 🔄 CI/CD

Proyek ini menggunakan GitHub Actions untuk:
- Menjalankan tests otomatis pada setiap push/PR
- Mengecek code coverage
- Validasi di multiple Python versions

Lihat konfigurasi di [.github/workflows/](.github/workflows/).

## 📝 Environment Variables

Buat file `.env` di root directory:

```env
SECRET_KEY=your-secret-key-at-least-32-characters-long
DATABASE_URL=sqlite:///./local_travel.db  # atau PostgreSQL URL
```

Contoh untuk PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/travel_planner
```

## 🚀 Deployment: Railway


### Deployment Steps

#### Via Railway Dashboard

1. Klik **New Project** di Railway dashboard
2. Pilih **Deploy from GitHub repo**
3. Pilih repository `travel_planner`
4. Railway akan otomatis detect Python project dan build

### Konfigurasi Environment Variables

Di Railway dashboard, ditambahkan environment variables berikut di **Variables** tab:

```env
SECRET_KEY=your-production-secret-key-min-32-chars
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Otomatis jika pakai Railway Postgres
```

### Setup Database PostgreSQL

1. Di Railway project, klik **New** → **Database** → **Add PostgreSQL**
2. Railway secara otomatis membuat database dan set `DATABASE_URL`
3. Variabel `${{Postgres.DATABASE_URL}}` akan otomatis ter-inject ke aplikasi


### Domain & Akses

- Railway akan generate public domain otomatis: `https://travel_planner.up.railway.app`
- Akses Swagger UI: `https://travel_planner.up.railway.app/docs`
- Akses ReDoc: `https://travel_planner.up.railway.app/redoc`


## 👥 Author

**dzakyatha** - [GitHub Profile](https://github.com/dzakyatha)
