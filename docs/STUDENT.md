# Profil siswa & feedback orang tua (wajib dibaca sebelum membuat materi atau soal)

File ini adalah **memori proyek**: semua feedback orang tua tentang cara membuat materi dan soal
dicatat di sini. Setiap agen yang mengerjakan issue **Materi** (#34–#38), **Konten** (#22–#26)
atau QA wajib mengikutinya. Feedback baru → tambahkan di bagian "Log feedback" (tanggal + isi),
lalu sesuaikan aturan di atasnya.

> Privasi: repo ini publik. Jangan menulis nama lengkap, sekolah, foto, atau data pribadi siswa
> di repo. Sapa siswa dengan **"kamu"**.

## Siapa siswanya
- Grade 9 (IB MYP 4), persiapan HUSO Round 1 (15 Nov 2026).
- **Visual learner**: paham lewat gambar, diagram, warna, dan cerita — bukan paragraf panjang.
- Minat besar: **🍳 memasak**, **🎮 Valorant** (game FPS taktis), **🏊 berenang**.

## Aturan membuat materi (mudah dipahami & menarik)
1. **Mulai dari dunia dia, baru konsep.** Setiap file materi dibuka dengan *hook* singkat (2–3
   kalimat) dari salah satu dari tiga minat: dapur, Valorant, atau kolam renang. Lalu jelaskan
   konsepnya, lalu kembali ke contoh itu.
2. **Gambar dulu, teks kemudian.** Setiap konsep yang bisa digambar → diagram SVG berwarna (kode
   warna mapel). Teks maks. 6 poin pendek per bagian; kata kunci tebal.
3. **Bahasa santai & sederhana**, seperti kakak kelas yang menjelaskan; kalimat pendek; sapa
   "kamu". Istilah Inggris dalam kurung karena ujiannya berbahasa Inggris.
4. **Analogi harus benar.** Analogi hanya pintu masuk: tulis juga **"Bedanya:"** satu kalimat
   bila analogi tidak 100 % tepat, supaya tidak menimbulkan miskonsepsi.
5. **Variasikan** ketiga tema di sepanjang mapel (jangan semuanya Valorant). Gunakan tema yang
   paling *alami* untuk konsep itu (lihat bank ide di bawah); jangan dipaksakan.
6. **Valorant**: fokus pada strategi, ekonomi (credits), peta, ronde, agent & ability, timing,
   suara langkah, peluang — bukan kekerasan. Nama agent/peta boleh disebut (fakta game), tanpa
   gambar/logo resmi (hak cipta) — gambar sendiri dalam SVG sederhana.
7. Akhiri setiap materi dengan **"Gambar dari ingatan"** dan **Cek Paham** (lihat issue Materi).

## Aturan membuat soal (Cek Paham, contoh soal, bank soal)
1. **Soal ujian tetap bergaya HUSO** (bahasa Inggris, A–E, satu jawaban benar) — siswa harus
   terbiasa dengan gaya ujian asli.
2. **Sekitar 40 % soal** diberi **konteks tema** (dapur/Valorant/renang) sebagai *word problem*;
   sisanya bergaya ujian murni. Konteks tidak boleh mengubah fisika/kimia/matematikanya.
3. **Contoh bergaya HUSO** di materi boleh lebih "bercerita" (mis. "Jett dashes…", "A swimmer
   pushes off the wall…", "A recipe needs…") dengan langkah penyelesaian bergambar.
4. Angka realistis (kecepatan perenang ±2 m/s, kolam 25/50 m, credits Valorant 0–9000, suhu
   minyak goreng ±180 °C, air mendidih 100 °C).
5. Semua soal orisinal dan **diselesaikan ulang secara independen** sebelum commit
   (`docs/CONTENT.md`).

## Bank ide tema per mapel (pakai yang cocok; boleh menambah)

| Mapel | 🍳 Dapur | 🎮 Valorant | 🏊 Renang |
|---|---|---|---|
| 🟦 Matematika | Resep diperbesar/diperkecil (perbandingan, polinom); kombinasi topping (kombinatorik); loyang bulat vs kotak (luas, volume) | Ekonomi credits antar ronde (barisan, pertidaksamaan: cukup untuk Vandal + armor?); kombinasi 5 agent dari pool (kombinasi); peluang headshot/menang ronde (peluang); sudut *peek* & garis pandang di peta (geometri, koordinat); pergantian sisi tiap 12 ronde (modulo) | Panjang total latihan 50 m × n lap (deret); sudut pantulan tembok saat *turn* (refleksi); urutan lintasan & start (permutasi) |
| 🟥 Fisika | Memanaskan air vs minyak (kalor jenis); air mendidih = perubahan fase; panci presto (gas ideal: P naik → titik didih naik); konduksi gagang panci | Dash Jett & kecepatan (kinematika); granat/satchel melambung (gerak parabola, energi); suara langkah kaki & jarak (bunyi, kenyaringan, frekuensi) | Menolak dinding kolam (hukum III Newton, impuls, momentum); hambatan air (gaya gesek); start lompat (kinematika); gerakan lengan berulang (gerak periodik/GHS) |
| 🟨 Kimia | Baking soda + cuka (asam-basa, gas CO₂); garam/gula larut (kelarutan, jenuh); resep = stoikiometri ("mol itu seperti lusin"); warna api kompor (uji nyala); karamelisasi (reaksi, entalpi) | "Recipe" ability (Viper: gas beracun → molekul & difusi) — gunakan hemat, hanya sebagai hook | Klorin & pH air kolam (asam-basa, buffer); kerak/kapur (kelarutan, Ksp) |
| 🟩 Biologi | Pencernaan makanan yang dimasak (sistem pencernaan, kelas zat makanan); ragi & roti (respirasi anaerob); daging = jaringan otot | Reaksi *flick* = gerak refleks & sistem saraf; tim 5 agent dengan peran = organel sel bekerja sama (nukleus = IGL/pemimpin, mitokondria = penyedia energi…); heal Sage ↔ sistem imun | Menahan napas & CO₂ (sistem pernapasan); jantung berdebar saat sprint (sistem peredaran darah); otot lurik vs jantung (jaringan); keringat di air? (ekskresi) |
| 🟫 Earth Science | Sup mendidih = konveksi (mantel bumi, sirkulasi atmosfer); lasagna berlapis = lapisan batuan (superposisi); garam di masakan ↔ salinitas laut | Peta: Icebox (gletser, es), Breeze (pantai tropis, arus), Lotus/Bind (gurun, angin); waktu ronde ↔ periode orbit | Ombak & pasang surut di pantai; arus laut; tekanan bertambah saat menyelam (atmosfer/hidrosfer); air kolam menguap (siklus air, kelembapan) |

## Log feedback orang tua
- **2026-10-11** — Siswa visual learner; materi harus mudah dipahami dan menarik.
- **2026-10-11** — Gunakan tiga minat siswa (memasak, Valorant, berenang) untuk membantu
  menjelaskan materi dan membuat contoh/soal.
- **2026-10-11** — Setiap pekerjaan dimulai dari GitHub issue; jangan langsung dikerjakan.
- **2026-10-11** — Target: seluruh materi tuntas paling lambat 7 Nov (seminggu sebelum HUSO);
  libur 12–18 Okt 4 jam/hari, lalu 30 menit hari sekolah + 2 jam akhir pekan (#33).
- **2026-10-11** — Perangkat belajar: laptop.
- **2026-10-11** — Konten: soal & flashcard orisinal buatan AI + link ke soal resmi (tidak disalin).
