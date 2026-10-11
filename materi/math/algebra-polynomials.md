# 🟦 Polinom  ·  `math.algebra.polynomials`
> 📅 Dipelajari: Sel 13 Okt · ⏱️ Baca ±12 menit · 📋 Silabus: Divisibility and factorization of polynomials, Vieta's formulas, Binomial theorem, Rational root theorem

## 🏊 Mulai dari kolam renang
Kolam latihan di sekolahmu berbentuk persegi panjang. Panjangnya **(x + 5)** meter dan lebarnya **(x + 2)** meter. Berapa luasnya?

Kalau kamu gambar petak-petaknya, luasnya muncul sendiri: **x² + 7x + 10**. Sekarang balik arahnya: kalau cuma diberi luas **x² + 7x + 10**, kamu bisa menebak sisi-sisi kolamnya. Itulah **memfaktorkan** (factoring). Polinom itu seperti kolam: ada luas total, dan ada sisi-sisi yang membentuknya.

## 🖼️ Gambaran besar
![Model luas kolam (x+5)(x+2) dibagi empat petak: x², 5x, 2x, dan 10](../../public/content/math/polynomials-area-model.svg)

Empat alat utama di subtopik ini: **Teorema Sisa/Faktor**, **Vieta**, **Teorema Akar Rasional**, dan **Teorema Binomial**.

## 💡 Konsep inti
1. **Teorema Sisa (Remainder Theorem):** kalau P(x) dibagi (x − a), **sisanya = P(a)**. Kalau P(a) = 0, maka **(x − a) adalah faktor** dari P(x) (Teorema Faktor).
2. **Pola faktorisasi yang wajib hafal:**
   - a² − b² = (a − b)(a + b)
   - a² ± 2ab + b² = (a ± b)²
   - a³ + b³ = (a + b)(a² − ab + b²) dan a³ − b³ = (a − b)(a² + ab + b²)
   - Kuadrat x² + bx + c: cari dua bilangan yang **dikali = c** dan **dijumlah = b** (model luas di atas).
3. **Rumus Vieta (Vieta's formulas):**
   - Untuk ax² + bx + c = 0 dengan akar p dan q: **p + q = −b/a** dan **p·q = c/a**.
   - Untuk ax³ + bx² + cx + d = 0 dengan akar p, q, r: **p + q + r = −b/a**, **pq + qr + rp = c/a**, **pqr = −d/a**.
   - Gunanya: menghitung ekspresi akar **tanpa mencari akarnya**. Contoh: p² + q² = (p + q)² − 2pq.
4. **Teorema Akar Rasional (Rational Root Theorem):** kalau koefisiennya bilangan bulat dan pecahan **m/n** (paling sederhana) adalah akar, maka **m membagi suku konstan** dan **n membagi koefisien utama**. Ini daftar *kandidat*, belum tentu semuanya akar.
5. **Teorema Binomial (Binomial theorem):** (a + b)ⁿ = Σ C(n, k) · aⁿ⁻ᵏ · bᵏ, untuk k = 0 sampai n. Koefisiennya ada di **Segitiga Pascal**.
6. **Dua trik cepat:** jumlah semua koefisien P(x) = **P(1)**, dan suku konstan = **P(0)**.

![Segitiga Pascal baris 0 sampai 6](../../public/content/math/pascal-triangle.svg)

> 🍕 **Analogi topping:** kamu punya 5 topping pizza. Memilih tepat k topping ada C(5, k) cara, dan angka-angka itu adalah baris n = 5 di Segitiga Pascal: 1, 5, 10, 10, 5, 1. **Bedanya:** di binomial, tiap suku juga membawa pangkat a dan b, bukan hanya jumlah cara memilih.

## 🧮 Contoh bergaya HUSO

**Contoh 1.** The roots of x³ − 7x² + 14x − 8 = 0 are r, s, and t. What is r² + s² + t²?

(A) 7  (B) 14  (C) 21  (D) 35  (E) 49

Langkah:
1. Dari Vieta: r + s + t = 7 dan rs + st + tr = 14.
2. Kuadratkan jumlahnya: (r + s + t)² = r² + s² + t² + 2(rs + st + tr).
3. Jadi r² + s² + t² = 7² − 2·14 = 49 − 28 = **21**. **Jawaban: (C).**
4. Pengecekan: akarnya 1, 2, 4 → 1 + 4 + 16 = 21 ✓.

**Contoh 2.** What is the coefficient of x⁴ in the expansion of (x + 2)⁶?

(A) 15  (B) 30  (C) 45  (D) 60  (E) 120

Langkah:
1. Suku x⁴ berarti dari 6 faktor, 4 kali mengambil x dan **2 kali mengambil 2**.
2. Banyak cara: C(6, 4) = 15 (baris n = 6 Pascal: 1, 6, **15**, 20, 15, 6, 1).
3. Nilai tiap cara: 2² = 4. Koefisien = 15 · 4 = **60**. **Jawaban: (D).**

## ⚠️ Jebakan umum
- **Tanda Vieta:** jumlah akar = **−b/a** (ada minus). Banyak yang lupa tanda minus, apalagi di rumus kubik untuk pqr = **−d/a**.
- **Lupa membagi dengan a** saat koefisien utama bukan 1: untuk 2x² − 10x + 12, p + q = 10/2 = 5, bukan 10.
- **Akar rasional:** daftar kandidat bukan jaminan. Kamu harus **mencoba** dulu (substitusi). Penyebut kandidat harus membagi koefisien utama (misalnya ⅔ tidak mungkin untuk 2x³ − …).
- **Binomial:** pangkat b ikut dihitung. Koefisien x² di (x + 3)⁵ adalah C(5, 2)·3³, bukan C(5, 2)·3².

## ✏️ Gambar dari ingatan
Tutup materi ini, ambil kertas, lalu gambar dalam 5 menit:
- [ ] Model luas kolam (x + 5)(x + 2) dengan 4 petak dan labelnya.
- [ ] Rumus Vieta untuk kuadrat **dan** kubik (tulis tandanya!).
- [ ] Segitiga Pascal sampai baris n = 5.
- [ ] Teorema Sisa dalam satu kalimat dengan contoh angka.
- [ ] Aturan kandidat akar rasional (m membagi apa, n membagi apa).

Bandingkan dengan materi, tandai yang terlewat dengan pulpen merah.

## 🎥 Tonton / coba
- [Polynomial remainder theorem](https://www.youtube.com/watch?v=MwG6QD352yc) — Khan Academy · 6:42 · perhatikan kenapa sisa dibagi (x − a) selalu P(a)
- [Art of Problem Solving: Vieta for Quadratics Part 1](https://www.youtube.com/watch?v=3sOSIFLHz-s) — Art of Problem Solving · 9:16 · perhatikan cara memakai jumlah dan hasil kali akar tanpa mencari akarnya
- [Pascal's triangle for binomial expansion](https://www.youtube.com/watch?v=v9Evg2tBdRk) — Khan Academy · 8:20 · perhatikan cara membaca koefisien dari satu baris segitiga

## ✅ Cek Paham (5 soal)
Kerjakan tanpa melihat materi. Kamu **SIAP** jika benar ≥ 4 dari 5.

**1.** What is the remainder when x³ − 3x² + 2x + 5 is divided by x − 3?

(A) 5  (B) 6  (C) 11  (D) 17  (E) 27

**2.** 🏊 A rectangular swimming pool has area x² − 7x + 10 square meters and length (x − 2) meters. If x = 9, what is the width of the pool, in meters?

(A) 2  (B) 4  (C) 7  (D) 10  (E) 28

**3.** Which of the following can **not** be a rational root of 2x³ − 3x² + 5x − 6 = 0?

(A) 3/2  (B) 1/2  (C) 6  (D) 2/3  (E) −3

**4.** What is the coefficient of x² in the expansion of (x + 3)⁵?

(A) 90  (B) 135  (C) 180  (D) 270  (E) 405

**5.** The roots of 2x² − 10x + 12 = 0 are p and q. What is 1/p + 1/q?

(A) 1/6  (B) 5/6  (C) 6/5  (D) 5  (E) 11/6

<details><summary>Kunci & pembahasan</summary>

1. **(C) 11.** Sisa = P(3) = 27 − 27 + 6 + 5 = 11. (B) 6 muncul kalau lupa suku konstan 5; (A) 5 adalah P(1), yaitu sisa untuk pembagi x − 1.
2. **(B) 4.** Untuk x = 9: luas = 81 − 63 + 10 = 28 dan panjang = 7, jadi lebar = 28 / 7 = 4. Cara faktor: x² − 7x + 10 = (x − 2)(x − 5), lebar = x − 5 = 4.
3. **(D) 2/3.** Kandidat m/n: m membagi 6 (±1, ±2, ±3, ±6), n membagi 2 (1 atau 2). Penyebut 3 tidak membagi 2, jadi 2/3 mustahil. Pilihan lain semuanya kandidat yang mungkin.
4. **(D) 270.** Suku x²: C(5, 2) · x² · 3³ = 10 · 27 = 270. (A) 90 muncul kalau memakai 3² salah.
5. **(B) 5/6.** 1/p + 1/q = (p + q)/(pq). Vieta: p + q = 10/2 = 5 dan pq = 12/2 = 6. Jadi 5/6. Pengecekan: akarnya 2 dan 3 → 1/2 + 1/3 = 5/6.
</details>
