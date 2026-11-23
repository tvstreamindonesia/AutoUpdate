# Sistem Playlist M3U8 Sepak Bola Otomatis (Xoilac / Vebo) — 100% Gratis

Sistem otomatisasi pembuatan dan pembaruan playlist IPTV (`xoilac.m3u`) untuk pertandingan sepak bola siaran langsung (*Live*) dan jadwal mendatang (*Upcoming*), lengkap dengan metadata logo tim, logo kompetisi, waktu kick-off (WIB), filter whitelist kompetisi bergengsi, dan resolusi stream HLS (`.m3u8`).

---

## 1. Jawaban Utama: Sistem Ini "Harus Menggunakan Apa"?

Untuk membuat dan menjalankan sistem ini secara **100% GRATIS (Rp 0)** tanpa biaya langganan server atau API berbayar, Anda menggunakan kombinasi teknologi berikut:

| Komponen | Pilihan Teknologi Gratis | Alasan & Keunggulan |
| :--- | :--- | :--- |
| **Bahasa Pemrograman** | **Python 3** (3.9 - 3.14+) | Gratis, open-source, ringan, cepat, dan memiliki library scraping HTTP yang sangat matang (`requests`, `beautifulsoup4`). |
| **Otomatisasi Cloud 24/7 (Rekomendasi)** | **GitHub Actions** (Free Tier) | Berjalan otomatis setiap 15 menit di cloud GitHub. **Komputer/laptop Anda tidak perlu menyala**, tidak butuh sewa VPS, dan langsung menghasilkan tautan link m3u permanen di internet. |
| **Otomatisasi Lokal (Alternatif PC)** | **Windows Task Scheduler** / `run_service.bat` | Menjalankan script secara berkala di background komputer Anda tanpa mengganggu aktivitas lain. |
| **Distribusi Link ke Smart TV** | **Built-in HTTP Server** atau **GitHub Raw Link** | Smart TV atau aplikasi IPTV dapat langsung membaca playlist via URL lokal (e.g., `http://192.168.1.x:8080/xoilac.m3u`) atau cloud (`https://raw.githubusercontent.com/.../xoilac.m3u`). |
| **Aplikasi Pemutar (IPTV Player)** | **TiviMate, IPTV Smarters, Televizo, VLC, OTT Navigator** | Aplikasi gratis yang mendukung format M3U standar dengan logo, EPG, dan multi-server. |

---

## 2. Fitur & Kemampuan Sistem

1. **Pengambilan Data Otomatis**: Menarik jadwal pertandingan dari endpoint jaringan siaran sepak bola (Vebo / Xoilac network) secara real-time.
2. **Whitelist Kompetisi Ketat**: Hanya pertandingan dari kompetisi resmi yang diizinkan masuk ke playlist. Pertandingan di luar whitelist secara otomatis ditolak.
3. **Resolusi Stream HLS M3U8**: Mengurai player embed, mengekstrak URL manifest `.m3u8`, dan memverifikasi konektivitas siaran live.
4. **Pemisahan LIVE & UPCOMING**:
   - Pertandingan Live: `group-title="LIVE | [KOMPETISI]"` dengan indikator skor live.
   - Pertandingan Mendatang: `group-title="UPCOMING | [KOMPETISI]"` dengan tag jam kick-off WIB.
5. **Metadata Lengkap**: Memuat atribut `tvg-id`, `tvg-name`, `tvg-logo` (logo klub/tim), logo liga, `tvg-country="ID"`, dan `tvg-language="Indonesian"`.
6. **Multi-Server**: Menampilkan Server 1, Server 2, dst. jika pertandingan menyediakan lebih dari satu jalur siaran.

---

## 3. Daftar Whitelist Kompetisi

Sistem telah dikonfigurasi dengan aturan regex dan filter pengecualian khusus untuk kategori berikut:

1. **Top European Leagues**:
   - Premier League (Liga Inggris)
   - La Liga (Liga Spanyol)
   - Serie A Italia
   - Bundesliga (Liga Jerman)
   - Ligue 1 (Liga Prancis)
   - Eredivisie (Liga Belanda)
   - Primeira Liga Portugal
2. **Kompetisi Eropa**:
   - UEFA Champions League (UCL / Cúp C1)
   - UEFA Europa League (UEL / Cúp C2)
   - UEFA Conference League (UECL / Cúp C3)
   - UEFA Super Cup
3. **Liga Indonesia**:
   - BRI Liga 1 / Super League Indonesia
   - Pegadaian Liga 2 Indonesia
   - Piala Presiden
   - Piala Indonesia
4. **MLS**:
   - Major League Soccer (MLS)
   - MLS Cup Playoffs & MLS Cup
   - Leagues Cup
5. **Kompetisi Asia**:
   - AFC Champions League Elite
   - AFC Champions League Two
   - AFC Challenge League
   - AFC Asian Cup & Kualifikasi Piala Asia
   - AFC U23 Asian Cup & turnamen resmi AFC lainnya
6. **Timnas Indonesia (Prioritas Khusus)**:
   - Terdeteksi otomatis setiap kali tim "Indonesia" bertanding (Senior, U-23, U-20, U-17, Timnas Putri).
   - Mencakup Piala Asia, Kualifikasi Piala Dunia, AFF / ASEAN Cup, SEA Games, dan agenda FIFA Matchday.
7. **Turnamen Bergengsi**:
   - FIFA World Cup & Kualifikasi Piala Dunia
   - FIFA U-17 World Cup (Piala Dunia U-17) & Kualifikasi Piala Dunia U-17
   - FIFA U-20 World Cup (Piala Dunia U-20)
   - UEFA EURO
   - Copa América
   - Africa Cup of Nations (AFCON / CAN)
   - CONCACAF Gold Cup
   - FIFA Club World Cup & FIFA Intercontinental Cup
   - Olimpiade Sepak Bola

---

## 4. Struktur File Project

```text
Playlist Otomatis Xoilac/
│
├── config.py              # Konfigurasi sumber data, whitelist, dan opsi output
├── scraper.py             # Parser jadwal, metadata logo, dan resolver stream .m3u8
├── generator.py           # Pembuat file playlist format M3U standar
├── server.py              # Web server lokal ringan dengan CORS & status dashboard
├── main.py                # Program utama CLI (mode single, --watch, --serve)
│
├── xoilac.m3u             # File playlist yang dihasilkan (siap pakai)
├── requirements.txt       # Daftar dependensi Python
│
├── run_playlist.bat       # Klik 2x untuk update manual sekali
├── run_service.bat        # Klik 2x untuk auto-update berkala + server lokal
├── setup_scheduler.bat    # Mendaftarkan auto-update ke Windows Task Scheduler
│
└── .github/
    └── workflows/
        └── update_playlist.yml # Workflow otomatisasi 24/7 gratis di GitHub Actions
```

---

## 5. Cara Penggunaan (Pilihan Metode)

### Metode A: Menjalankan di Komputer Lokal (Windows)

#### 1. Instalasi Dependensi
Buka terminal / PowerShell di folder ini lalu jalankan:
```bash
pip install -r requirements.txt
```

#### 2. Menjalankan Update Playlist
- **Cara Mudah**: Cukup klik dua kali file **`run_playlist.bat`**.
- **Lewat Terminal**:
  ```bash
  python main.py
  ```
  File `xoilac.m3u` akan langsung diperbarui di folder yang sama.

#### 3. Menjalankan Sebagai Background Service + Server Streaming Smart TV
Jika Anda ingin playlist otomatis diperbarui setiap 5 menit dan langsung bisa diakses oleh Smart TV di jaringan Wi-Fi rumah:
- Klik dua kali **`run_service.bat`**, atau:
  ```bash
  python main.py --watch --serve --interval 300 --port 8080
  ```
- Terminal akan menampilkan URL lokal Anda, contoh:
  ```text
  http://192.168.1.15:8080/xoilac.m3u
  ```
- Salin URL tersebut ke aplikasi IPTV di Smart TV / HP Anda.

---

### Metode B: Otomatisasi Cloud 24/7 Tanpa Komputer Nyala (GitHub Actions - 100% Gratis)

Ini adalah cara paling praktis dan direkomendasikan karena **Anda tidak perlu membiarkan PC/laptop menyala 24 jam**.

1. Buat repositori baru di akun [GitHub](https://github.com) Anda (bisa public atau private).
2. Upload semua file dalam folder ini ke repositori tersebut:
   ```bash
   git init
   git add .
   git commit -m "Initial commit Xoilac M3U Generator"
   git remote add origin https://github.com/USERNAME/REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```
3. Buka menu **Settings** > **Actions** > **General** di repositori GitHub Anda.
   Pada bagian **Workflow permissions**, pilih **Read and write permissions**, lalu klik **Save**.
4. GitHub Actions akan otomatis berjalan setiap 15 menit (sesuai `.github/workflows/update_playlist.yml`) untuk memperbarui file `xoilac.m3u`.
5. Tautan Raw URL playlist Anda di GitHub dapat langsung digunakan di Smart TV:
   ```text
   https://raw.githubusercontent.com/USERNAME/REPO_NAME/main/xoilac.m3u
   ```

---

## 6. Cara Memasang Playlist di Aplikasi IPTV

### 1. Smart TV (Android TV / Google TV)
- Buka aplikasi **TiviMate** atau **Televizo** atau **OTT Navigator**.
- Pilih **Add Playlist** > **M3U Playlist**.
- Masukkan URL (bisa URL lokal `http://192.168.x.x:8080/xoilac.m3u` atau URL GitHub Raw).
- Atur refresh interval playlist ke **Every 2 hours** atau **On app start**.

### 2. HP Android / iPhone (iOS)
- Gunakan aplikasi **IPTV Smarters Pro** atau **VLC Media Player**.
- Di VLC: Menu **Media** > **Open Network Stream** > Tempelkan URL playlist atau buka file `xoilac.m3u` secara langsung.

### 3. PC / Laptop (Windows / Mac)
- Buka **VLC Media Player** > Tekan `Ctrl + O` > Pilih file `xoilac.m3u`.
- Buka playlist (`Ctrl + L`) untuk melihat daftar channel yang rapi dikelompokkan berdasarkan kompetisi.
