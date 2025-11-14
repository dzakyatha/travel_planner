# skrip berisikan exception untuk Invariants/Logika bisnis

# saat total pengeluaran melebihi anggaran
class AnggaranTerlampauiException(Exception):
    pass

# saat tanggal HariPerjalanan berada di luar Durasi RencanaPerjalanan
class TanggalDiLuarDurasiException(Exception):
    pass

# saat ada Aktivitas yang waktunya tumpang tindih dalam satu Hari
class AktivitasKonflikException(Exception):
    pass