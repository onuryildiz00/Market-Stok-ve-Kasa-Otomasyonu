# 🏪 Market Stok Otomasyonu

Küçük ve orta ölçekli marketler için geliştirilmiş, **Python** tabanlı masaüstü stok ve kasa yönetim sistemi. Supabase bulut veritabanı ile gerçek zamanlı veri senkronizasyonu sağlar.

---

## 📸 Ekran Görüntüleri

### Giriş Ekranı
![Giriş Ekranı](screenshots/giris.png)

### Ana Ekran
![Ana Ekran](screenshots/ana_ekran.png)

### Kasa Ekranı
![Kasa Ekranı](screenshots/kasa.png)

### Satış Geçmişi
![Satış Geçmişi](screenshots/satis_gecmisi.png)

### En Çok Getiri
![En Çok Getiri](screenshots/en_cok_kar.png)

---

## ✨ Özellikler

### 🔐 Kimlik Doğrulama
- E-posta / şifre ile güvenli giriş
- Yeni market kaydı oluşturma
- Supabase Auth ile oturum yönetimi

### 📦 Stok Yönetimi
- Ürün ekleme, düzenleme ve silme
- Barkod numarası ile ürün tanımlama
- Barkod görseli otomatik üretimi ve dışa aktarma
- Ürün resmi URL'den otomatik yükleme
- Alış / satış fiyatı ve kâr oranı görüntüleme
- **Kritik stok uyarısı** — stok 5'in altına düşen ürünler kırmızıyla işaretlenir
- İsim veya barkod ile anlık ürün arama

### 🖥️ Kasa Ekranı
- Barkod okutarak sepete ürün ekleme
- **Dokunmatik ekran destekli numpad** — fare ile barkod girişi
- Nakit tutar girişi ve otomatik para üstü hesaplama
- Sepet yönetimi (adet artırma/azaltma, ürün silme)
- Satış tamamlandığında stok otomatik güncelleme

### 📋 Satış Geçmişi
- Tüm satışları listeleme ve detay görüntüleme
- **Tarih bazlı filtreleme:** Bugün / Bu Hafta / Bu Ay / Tümü
- Ürün adına göre metin arama
- Her satışta ürün detayı açılır panel (kalem kalem görüntüleme)
- Dönem toplam satış adedi ve ciro özeti

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Arayüz | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Veritabanı | [Supabase](https://supabase.com) (PostgreSQL) |
| Kimlik Doğrulama | Supabase Auth |
| Grafik | [Matplotlib](https://matplotlib.org) |
| Barkod | [python-barcode](https://github.com/WhyNotHugo/python-barcode) |
| Resim | [Pillow](https://python-pillow.org) |
| Dil | Python 3.11+ |

---

## 🚀 Kurulum

### 1. Depoyu klonlayın
```bash
git clone https://github.com/kullanici-adi/market-stok-otomasyonu.git
cd market-stok-otomasyonu
```

### 2. Sanal ortam oluşturun (önerilir)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Bağımlılıkları yükleyin
```bash
pip install -r requirements.txt
```

---

## ☁️ Supabase Kurulumu

### 1. Proje oluşturun
[supabase.com](https://supabase.com) adresinde ücretsiz hesap açın ve yeni bir proje oluşturun.

### 2. Tabloları oluşturun

Supabase Dashboard → **SQL Editor** bölümüne girip aşağıdaki sorguları çalıştırın:

```sql
-- Ürünler tablosu
CREATE TABLE urunler (
  id          BIGSERIAL PRIMARY KEY,
  market_id   UUID REFERENCES auth.users(id),
  barkod      TEXT,
  isim        TEXT NOT NULL,
  stok        INTEGER DEFAULT 0,
  fiyat       NUMERIC(10,2) DEFAULT 0,
  satis_fiyati NUMERIC(10,2) DEFAULT 0,
  resim_url   TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Satışlar tablosu
CREATE TABLE satislar (
  id          BIGSERIAL PRIMARY KEY,
  market_id   UUID REFERENCES auth.users(id),
  tarih       TIMESTAMPTZ DEFAULT NOW(),
  toplam      NUMERIC(10,2),
  nakit       NUMERIC(10,2),
  para_ustu   NUMERIC(10,2),
  urunler     TEXT
);
```

### 3. Row Level Security (RLS) ayarlayın

```sql
-- urunler tablosu için RLS
ALTER TABLE urunler ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Kullanici kendi urunlerini gorur"
  ON urunler FOR ALL
  USING (auth.uid() = market_id)
  WITH CHECK (auth.uid() = market_id);

-- satislar tablosu için RLS
ALTER TABLE satislar ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Kullanici kendi satislarini gorur"
  ON satislar FOR ALL
  USING (auth.uid() = market_id)
  WITH CHECK (auth.uid() = market_id);
```

### 4. API anahtarlarını alın

Supabase Dashboard → **Project Settings → API** bölümünden:
- `Project URL`
- `anon / public` key

### 5. Ortam değişkenlerini ayarlayın

Proje kök dizininde `.env` dosyası oluşturun:
```env
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI...
```

> ⚠️ `.env` dosyasını **asla** Git'e yüklemeyin. `.gitignore`'a eklendiğinden emin olun.

---

## ▶️ Çalıştırma

```bash
python main.py
```

---

## 📁 Proje Yapısı

```
market-stok-otomasyonu/
│
├── main.py              # Ana uygulama dosyası
├── requirements.txt     # Python bağımlılıkları
├── .env                 # API anahtarları (Git'e yüklenMEZ)
├── .env.example         # .env şablonu (bu dosya repoya girer)
├── .gitignore
├── README.md
│
├── barkodlar/           # Üretilen barkod görselleri (Git'e yüklenMEZ)
└── screenshots/         # Ekran görüntüleri (isteğe bağlı)
```

---

## 📋 Gereksinimler (requirements.txt)

```
supabase
customtkinter
pillow
requests
python-barcode[images]
matplotlib
python-dotenv
```

---

## 🔒 Güvenlik

- Supabase URL ve API anahtarı **`.env`** dosyasında tutulur, kod içinde yer almaz.
- `.env` dosyası `.gitignore` ile repoya dahil edilmez.
- Üretilen barkod görselleri (`barkodlar/` klasörü) de `.gitignore` ile hariç tutulur.
- `.env.example` dosyasını referans alarak kendi `.env`'inizi oluşturun.

---

## 🗺️ Eklenebilecek Özellikler

- [ ] Kâr/zarar grafikleri (günlük, haftalık, aylık)
- [ ] Fiş / makbuz yazdırma
- [ ] Excel ile toplu ürün aktarımı
- [ ] Çoklu kasiyer desteği
- [ ] Müşteri / sadakat sistemi
- [ ] Tedarikçi ve sipariş yönetimi
- [ ] PDF rapor çıktısı

---

## 🤝 Katkıda Bulunma

1. Bu depoyu fork'layın
2. Yeni bir dal oluşturun: `git checkout -b ozellik/yeni-ozellik`
3. Değişikliklerinizi kaydedin: `git commit -m 'Yeni özellik eklendi'`
4. Dalınızı gönderin: `git push origin ozellik/yeni-ozellik`
5. Pull Request açın

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

---

<div align="center">
  <b>⭐ Projeyi beğendiyseniz yıldız vermeyi unutmayın!</b>
</div>
