# 🟦 Lembar Ringkas Matematika HUSO 9–10

> 🖨️ Cetak 2 halaman (Ctrl+P). Ujian HUSO **tidak** memberi rumus, jadi semua ini harus hafal. Kalkulator hanya boleh di Round 1 (scientific, bukan graphing).

---
## 📄 Halaman 1: Aljabar & Teori Bilangan

### 🏊 Polinom
| Topik | Rumus |
|---|---|
| **Sisa & faktor** | P(x) dibagi (x − a) → sisa **P(a)**. P(a) = 0 ⇔ (x − a) faktor |
| **Pola faktor** | a² − b² = (a − b)(a + b) · (a ± b)² = a² ± 2ab + b² · a³ ± b³ = (a ± b)(a² ∓ ab + b²) |
| **Vieta kuadrat** ax² + bx + c | p + q = **−b/a** · pq = **c/a** · p² + q² = (p + q)² − 2pq |
| **Vieta kubik** ax³ + bx² + cx + d | p + q + r = **−b/a** · pq + qr + rp = **c/a** · pqr = **−d/a** |
| **Akar rasional** | akar m/n (sederhana): **m \| suku konstan**, **n \| koefisien utama** |
| **Binomial** | (a + b)ⁿ = Σ C(n, k) aⁿ⁻ᵏ bᵏ · jumlah koefisien = **P(1)** · suku konstan = **P(0)** |

### 🎮 Barisan & deret
| Jenis | Suku ke-n | Jumlah n suku |
|---|---|---|
| **Aritmetika** (beda d) | aₙ = a₁ + (n − 1)d | Sₙ = n(a₁ + aₙ)/2 |
| **Geometri** (rasio r) | aₙ = a₁ rⁿ⁻¹ | Sₙ = a₁(1 − rⁿ)/(1 − r), r ≠ 1 · tak hingga (\|r\| < 1): a₁/(1 − r) |
| **Teleskopik** | tulis suku sebagai selisih | 1/(k(k + 1)) = 1/k − 1/(k + 1) → jumlah n suku = **n/(n + 1)** |

### 🍳 Pertidaksamaan
- **Trivial:** x² ≥ 0 untuk semua bilangan real (sama dengan 0 hanya jika x = 0).
- **AM-GM** (a, b ≥ 0): (a + b)/2 ≥ √(ab), sama jika **a = b**. Untuk n bilangan: rata-rata ≥ akar pangkat n dari hasil kali.
- **Urutan:** HM ≤ GM ≤ AM, yaitu 2ab/(a + b) ≤ √(ab) ≤ (a + b)/2.
- **Segitiga:** |a − b| < c < a + b.

### 🍳 Fungsi
- **Injektif** = tiap output dari paling banyak 1 input · **Surjektif** = semua anggota kodomain terpakai · **Bijektif** = keduanya (punya invers).
- **Genap:** f(−x) = f(x) (simetris terhadap sumbu y) · **Ganjil:** f(−x) = −f(x) (simetris terhadap titik asal).
- **Floor ⌊x⌋** = bilangan bulat terbesar ≤ x · **Ceiling ⌈x⌉** = bilangan bulat terkecil ≥ x · x − 1 < ⌊x⌋ ≤ x.
- **Log:** log(ab) = log a + log b · log(a/b) = log a − log b · log aᵏ = k log a · log_b b = 1 · log 1 = 0.
- **Trigonometri:** sin²θ + cos²θ = 1 · sin(90° − θ) = cos θ

| θ | 30° | 45° | 60° |
|---|---|---|---|
| sin | ½ | √2/2 | √3/2 |
| cos | √3/2 | √2/2 | ½ |
| tan | 1/√3 | 1 | √3 |

### 🎮 Aritmetika modular & 🍳 teori bilangan
- a ≡ b (mod m) ⇔ **m membagi (a − b)**. Boleh dijumlah, dikurang, dikali, dipangkatkan.
- Pangkat besar: cari **pola berulang** (siklus) sisa.
- **Faktorisasi prima** itu unik. Jika n = pᵃ qᵇ, banyak faktor = **(a + 1)(b + 1)**.
- **Tripel Pythagoras:** 3-4-5 · 5-12-13 · 8-15-17 · 7-24-25 · 20-21-29 · 9-40-41 (dan kelipatannya).
- **Diophantine** ax + by = c punya solusi bulat ⇔ **FPB(a, b) membagi c**.
- **Basis:** 1011₂ = 8 + 2 + 1 = 11. Ke basis b: bagi berulang, baca sisa dari bawah.

---
## 📄 Halaman 2: Geometri, Kombinatorik & Peluang

### 🏊 Segitiga
| Titik | Dibentuk oleh | Sifat |
|---|---|---|
| **Centroid** | garis berat (median) | membagi median **2 : 1** |
| **Circumcenter** | sumbu sisi | sama jauh ke 3 titik sudut (jari-jari **R**) |
| **Orthocenter** | garis tinggi | — |
| **Incenter** | garis bagi sudut | sama jauh ke 3 sisi (jari-jari **r**) |

- **Luas:** ½ · alas · tinggi · ½ab sin C · **Heron:** s = (a + b + c)/2 → √(s(s − a)(s − b)(s − c)) · **L = r·s** · **R = abc / (4L)**
- **Garis bagi:** BD / DC = AB / AC.
- **30-60-90:** sisi 1 : √3 : 2 · **45-45-90:** sisi 1 : 1 : √2 · **Sebangun** (rasio k): panjang × k, luas × k².

### 🎮 Lingkaran
- **Sudut keliling = ½ sudut pusat** · sudut di setengah lingkaran = 90°.
- **Segiempat tali busur:** sudut berhadapan jumlahnya **180°**.
- **Power of a point:** dua tali busur PA·PB = PC·PD · garis singgung PT² = PA·PB.
- **Singgung ⟂ jari-jari.** Dua lingkaran bersinggungan luar: jarak pusat = r₁ + r₂ · dalam: \|r₁ − r₂\|.

### 🏊 Transformasi (terhadap titik asal)
| | Aturan |
|---|---|
| Cermin sumbu x / sumbu y / garis y = x | (x, −y) / (−x, y) / (y, x) |
| Rotasi 90° berlawanan jarum jam / 180° / 270° | (−y, x) / (−x, −y) / (y, −x) |
| Translasi (a, b) | (x + a, y + b) |
| Dilatasi faktor k | (kx, ky) · panjang × k · luas × k² |

### 🎮 Geometri koordinat
- **Jarak** √((x₂ − x₁)² + (y₂ − y₁)²) · **titik tengah** ((x₁ + x₂)/2, (y₁ + y₂)/2) · **gradien** m = (y₂ − y₁)/(x₂ − x₁).
- **Garis:** y = mx + c · sejajar: m sama · tegak lurus: **m₁ m₂ = −1**.
- **Lingkaran:** (x − h)² + (y − k)² = r².
- **Shoelace:** L = ½ \|Σ (xᵢ yᵢ₊₁ − xᵢ₊₁ yᵢ)\|, titik diurutkan searah/berlawanan jarum jam.

### 🍳 Bangun ruang
| Bangun | Volume | Luas permukaan |
|---|---|---|
| Prisma | alas × tinggi | 2 · alas + keliling alas × tinggi |
| Tabung | πr²h | 2πr² + 2πrh |
| Limas | ⅓ · alas · tinggi | alas + sisi-sisi tegak |
| Kerucut | ⅓πr²h | πr² + πrℓ, ℓ = √(r² + h²) |
| Bola | 4/3 πr³ | 4πr² |

### 🍳 Pencacahan & kombinatorik
- **Aturan kali** (tahap berurutan) · **aturan tambah** (pilihan saling lepas).
- **Inklusi-eksklusi:** \|A ∪ B\| = \|A\| + \|B\| − \|A ∩ B\| · tiga himpunan: jumlah satuan − jumlah irisan dua + irisan tiga.
- **Pigeonhole:** n + 1 benda ke n kotak → ada kotak berisi ≥ 2 · umum: ada kotak berisi ≥ ⌈N/k⌉.
- **Permutasi** P(n, k) = n!/(n − k)! · **Kombinasi** C(n, k) = n!/(k!(n − k)!) · C(n, k) = C(n, n − k) · C(n, k) = C(n − 1, k − 1) + C(n − 1, k) · ΣC(n, k) = 2ⁿ.
- **Stars and bars:** x₁ + … + xₖ = n → bilangan bulat ≥ 0: **C(n + k − 1, k − 1)** · bilangan bulat ≥ 1: **C(n − 1, k − 1)**.

### 🎮 Peluang & 🏊 strategi
- P(A) = kejadian yang diinginkan / semua kemungkinan (sama mungkin) · **P(tidak A) = 1 − P(A)**.
- P(A ∪ B) = P(A) + P(B) − P(A ∩ B) · saling bebas: **P(A ∩ B) = P(A)·P(B)** · bersyarat: **P(A \| B) = P(A ∩ B) / P(B)**.
- **Strategi:** bagi kasus (*casework*) · "paling sedikit satu" → **hitung kebalikannya** (*complementary*) · cari pasangan satu-satu (*bijection*) · manfaatkan simetri.
