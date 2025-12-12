from sqlmodel import SQLModel, create_engine, Session
import os

# URL dari Environment Variable atau default ke SQLite lokal
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local_travel.db")

# string koneksi Postgres dari Railway
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Engine database dengan konfigurasi yang tepat
if DATABASE_URL.startswith("sqlite"):
    # Untuk SQLite, gunakan sync driver dan check_same_thread=False
    engine = create_engine(
        DATABASE_URL, 
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    # Untuk PostgreSQL atau database lainnya
    engine = create_engine(DATABASE_URL, echo=False)

# membuat semua tabel yang didefinisikan di SQLModel metadata
def init_db():
    SQLModel.metadata.create_all(engine)

# Dependency injection untuk session database
def get_session():
    with Session(engine) as session:
        yield session

# Alias untuk konsistensi dengan router
get_db = get_session