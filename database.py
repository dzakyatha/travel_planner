from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import inspect
from sqlalchemy.sql import sqltypes
import os
from dotenv import load_dotenv

# Pastikan semua model terdaftar ke SQLModel.metadata sebelum init_db dipanggil.
from models import aggregate_root as _aggregate_root_models  # noqa: F401
from models import entity as _entity_models  # noqa: F401

# Load environment variables from .env file
load_dotenv()

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

def _column_type_family(column_type: object) -> str:
    """Normalisasi tipe kolom SQLAlchemy ke keluarga tipe yang stabil lintas dialect."""
    type_name = str(column_type).lower()
    if "varchar" in type_name or "character varying" in type_name or "text" in type_name:
        return "string"
    if "double precision" in type_name or "float" in type_name or "real" in type_name:
        return "float"
    if "timestamp" in type_name:
        return "timestamp"

    if isinstance(column_type, sqltypes.Uuid):
        return "uuid"
    if isinstance(column_type, sqltypes.Integer):
        return "integer"
    if isinstance(column_type, sqltypes.Float):
        return "float"
    if isinstance(column_type, sqltypes.Boolean):
        return "boolean"
    if isinstance(column_type, sqltypes.Date):
        return "date"
    if isinstance(column_type, sqltypes.Time):
        return "time"
    if isinstance(column_type, sqltypes.String):
        return "string"
    if isinstance(column_type, sqltypes.JSON):
        return "json"
    return str(column_type)


def validate_existing_schema_compatibility() -> list[str]:
    """Bandingkan schema DB saat ini vs schema model untuk mencegah konflik startup."""
    if DATABASE_URL.startswith("sqlite"):
        return []

    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())
    mismatches: list[str] = []

    for table_name, model_table in SQLModel.metadata.tables.items():
        if table_name not in db_tables:
            # Tabel baru akan dibuat oleh create_all, tidak dianggap konflik.
            continue

        db_columns_raw = inspector.get_columns(table_name)
        db_columns = {col["name"]: col for col in db_columns_raw}
        model_columns = {col.name: col for col in model_table.columns}

        for model_col_name, model_col in model_columns.items():
            if model_col_name not in db_columns:
                mismatches.append(
                    f"{table_name}.{model_col_name}: kolom tidak ada di DB"
                )
                continue

            db_col = db_columns[model_col_name]
            model_type = _column_type_family(model_col.type)
            db_type = _column_type_family(db_col["type"])
            if model_type != db_type:
                mismatches.append(
                    f"{table_name}.{model_col_name}: tipe model={model_type}, db={db_type}"
                )

            db_nullable = bool(db_col.get("nullable", True))
            model_nullable = bool(model_col.nullable)
            if db_nullable != model_nullable:
                mismatches.append(
                    f"{table_name}.{model_col_name}: nullable model={model_nullable}, db={db_nullable}"
                )

        db_fk_set = set()
        for fk in inspector.get_foreign_keys(table_name):
            constrained_cols = tuple(fk.get("constrained_columns") or [])
            referred_table = fk.get("referred_table")
            referred_cols = tuple(fk.get("referred_columns") or [])
            db_fk_set.add((constrained_cols, referred_table, referred_cols))

        model_fk_set = set()
        for model_col in model_table.columns:
            for fk in model_col.foreign_keys:
                model_fk_set.add(
                    ((model_col.name,), fk.column.table.name, (fk.column.name,))
                )

        missing_fks = model_fk_set - db_fk_set
        for constrained_cols, referred_table, referred_cols in sorted(missing_fks):
            mismatches.append(
                f"{table_name}.{constrained_cols} -> {referred_table}.{referred_cols}: foreign key tidak ada di DB"
            )

    return mismatches


# membuat semua tabel yang didefinisikan di SQLModel metadata
def init_db():
    mismatches = validate_existing_schema_compatibility()
    if mismatches:
        mismatch_text = "\n- " + "\n- ".join(mismatches)
        raise RuntimeError(
            "Schema database tidak kompatibel dengan model backend. "
            "Sinkronkan perubahan manual (psql) ke model/migrasi terlebih dahulu."
            f"{mismatch_text}"
        )

    SQLModel.metadata.create_all(engine)

# Dependency injection untuk session database
def get_session():
    with Session(engine) as session:
        yield session

# Alias untuk konsistensi dengan router
get_db = get_session