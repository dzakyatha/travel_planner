# Travel Planner API

Repo ini berisikan API untuk perencanaan perjalanan yang diimplementasikan menggunakan **Domain-Driven Design (DDD)**. Repo ini dibuat untuk memenuhi **Tugas Besar** mata kuliah **II3160 - Teknologi Sistem Terintegrasi**. Proyek ini menggunakan **FastAPI** sebagai framework web dan menerapkan prinsip-prinsip DDD dengan **Value Objects**, **Entities**, dan **Aggregate Root**.

## 📋 Fitur

- Membuat dan mengelola rencana perjalanan
- Menambahkan hari dan aktivitas dalam rencana perjalanan
- Mengelola anggaran dan pengeluaran rencana perjalanan
- Validasi bisnis/invariants untuk menjaga integritas data

## 🏗️ Arsitektur

Proyek ini mengimplementasikan **Domain-Driven Design (DDD)** dengan struktur:

### Value Objects
- `Uang` - Representasi nilai moneter dengan validasi
- `Durasi` - Rentang waktu perjalanan
- `Lokasi` - Informasi lokasi dengan koordinat

### Entities
- `HariPerjalanan` - Satu hari dalam rencana perjalanan
- `Aktivitas` - Kegiatan terjadwal dalam satu hari
- `Pengeluaran` - Pengeluaran uang dalam perjalanan

### Aggregate Root
- `RencanaPerjalanan` - Titik masuk utama untuk memodifikasi state, mengelola invariants bisnis

### Business Rules (Invariants)
1. Total pengeluaran tidak boleh melebihi anggaran
2. Hari perjalanan dan pengeluaran harus dalam rentang durasi rencana perjalanan
3. Aktivitas dalam satu hari rencana perjalanan tidak boleh tumpang tindih waktu
4. Update durasi rencana perjalanan harus mencakup semua hari dan pengeluaran yang sudah ada

## 🚀 Instalasi

### Prasyarat
- Python >= 3.13
- [uv](https://github.com/astral-sh/uv) package manager

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
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📡 API Endpoints

### Rencana Perjalanan

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/perencanaan/` | Membuat rencana perjalanan baru |
| GET | `/api/perencanaan/{rencana_id}` | Mendapatkan rencana perjalanan |
| PUT | `/api/perencanaan/{rencana_id}/anggaran` | Update anggaran |
| PUT | `/api/perencanaan/{rencana_id}/durasi` | Update durasi |

### Hari Perjalanan

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/perencanaan/{rencana_id}/hari` | Menambahkan hari perjalanan |
| DELETE | `/api/perencanaan/{rencana_id}/hari/{tanggal}` | Menghapus hari perjalanan |

### Aktivitas

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/perencanaan/{rencana_id}/hari/{tanggal}/aktivitas` | Menambahkan aktivitas ke hari |

### Pengeluaran

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/perencanaan/{rencana_id}/pengeluaran` | Menambahkan pengeluaran |
| DELETE | `/api/perencanaan/{rencana_id}/pengeluaran/{id_pengeluaran}` | Menghapus pengeluaran |

## 📝 Contoh Request

### Membuat Rencana Perjalanan

```json
POST /api/perencanaan/
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

### Menambahkan Aktivitas

```json
POST /api/perencanaan/{rencana_id}/hari/2024-12-01/aktivitas
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

### Menjalankan Test File Tertentu

```bash
uv run pytest tests/create_tests.py
```

### Menjalankan Test Spesifik

```bash
uv run pytest tests/create_tests.py::test_create_rencana_perjalanan_success
```

## 📁 Struktur Proyek

```
travel_planner/
├── models/                 # Domain models (DDD)
│   ├── aggregate_root.py   # Aggregate Root: RencanaPerjalanan
│   ├── entity.py           # Entities: HariPerjalanan, Aktivitas, Pengeluaran
│   ├── value_objects.py    # Value Objects: Uang, Durasi, Lokasi
│   └── exception.py        # Business exceptions
├── tests/                  # Test files
│   ├── create_tests.py     # Test untuk CREATE endpoints
│   ├── get_tests.py        # Test untuk GET endpoints
│   ├── update_tests.py     # Test untuk UPDATE endpoints
│   ├── delete_tests.py     # Test untuk DELETE endpoints
│   └── utils.py            # Test fixtures dan utilities
├── main.py                 # FastAPI application entry point
├── router.py               # API routes dan endpoints
├── schema.py               # Pydantic schemas untuk request/response
├── pyproject.toml          # Project dependencies
└── README.md               # Dokumentasi proyek
```

## 🛠️ Tech Stack

- **uv** - Python package manager
- **FastAPI** - Web framework modern untuk Python
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation menggunakan Python type annotations
- **pytest** - Python testing framework