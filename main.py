from supabase import create_client, Client
import json
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
import requests
import random
from io import BytesIO
from PIL import Image
import os
import barcode
from barcode.writer import ImageWriter
from dotenv import load_dotenv

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "SUPABASE_URL veya SUPABASE_KEY bulunamadı!\n"
        "Lütfen proje dizininde bir .env dosyası oluşturun.\n"
        "Örnek: .env.example dosyasını kopyalayıp doldurun."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


app = ctk.CTk()
app.title("Market Stok ve Kasa Otomasyonu")
app.geometry("400x450")
app.resizable(True, True)



def url_den_resim_getir(url):
    try:
        if not url or url.strip() == "":
            return None

        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        }

        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        resim_verisi = Image.open(BytesIO(response.content))
        return ctk.CTkImage(light_image=resim_verisi, dark_image=resim_verisi, size=(50, 50))

    except Exception as e:
        print(f"Resim yüklenemedi ({url}):", e)
        return None



def giris_yap():
    email = email_entry.get().strip()
    sifre = sifre_entry.get().strip()

    
    giris_btn.configure(state="disabled")

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": sifre
        })

        if response.user:
            messagebox.showinfo("Başarılı", "Giriş başarılı! Hoş geldiniz.")
            app.withdraw()
            ana_ekrani_ac(response.user)
        else:
            raise Exception("Kullanıcı verisi alınamadı.")

    except Exception as e:
        giris_btn.configure(state="normal")
        print("--- Hata Detayı ---")
        print(e)
        messagebox.showerror("Giriş Başarısız", f"Hata: {e}")


def kayit_ol():
    email = email_entry.get()
    sifre = sifre_entry.get()

    if not email or not sifre:
        messagebox.showwarning("Uyarı", "Lütfen e-posta ve şifre girin!")
        return

    try:
        supabase.auth.sign_up({
            "email": email,
            "password": sifre
        })
        messagebox.showinfo("Başarılı", "Kayıt başarılı! Şimdi aynı bilgilerle giriş yapabilirsiniz.")
    except Exception as e:
        messagebox.showerror("Hata", f"Kayıt işlemi başarısız oldu: {e}")



def ana_ekrani_ac(kullanici):
    dashboard = ctk.CTkToplevel()
    dashboard.title("Stok ve Kasa Yönetim Paneli")
    dashboard.geometry("950x650")
    dashboard.resizable(True, True)
    
    form_frame = ctk.CTkFrame(dashboard, width=300)
    form_frame.pack(side="left", fill="y", padx=10, pady=10)

    ctk.CTkLabel(form_frame, text="Yeni Ürün Ekle", font=("Roboto", 20, "bold")).pack(pady=20)

    barkod_entry = ctk.CTkEntry(form_frame, placeholder_text="Barkod Numarası", width=250)
    barkod_entry.pack(pady=10, padx=10)

    isim_entry = ctk.CTkEntry(form_frame, placeholder_text="Ürün İsmi", width=250)
    isim_entry.pack(pady=10, padx=10)

    resim_entry = ctk.CTkEntry(form_frame, placeholder_text="Resim URL", width=250)
    resim_entry.pack(pady=10, padx=10)

    stok_entry = ctk.CTkEntry(form_frame, placeholder_text="Stok Sayısı", width=250)
    stok_entry.pack(pady=10, padx=10)

    fiyat_entry = ctk.CTkEntry(form_frame, placeholder_text="Alış Fiyatı (₺)", width=250)
    fiyat_entry.pack(pady=10, padx=10)

    satis_entry = ctk.CTkEntry(form_frame, placeholder_text="Satış Fiyatı (₺)", width=250)
    satis_entry.pack(pady=10, padx=10)

    
    sag_frame = ctk.CTkFrame(dashboard, fg_color="transparent")
    sag_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    arama_frame = ctk.CTkFrame(sag_frame, fg_color="transparent")
    arama_frame.pack(fill="x", pady=(0, 10))

    ctk.CTkLabel(arama_frame, text="Ürün Ara:", font=("Roboto", 14, "bold")).pack(side="left", padx=(0, 10))
    arama_entry = ctk.CTkEntry(arama_frame, placeholder_text="İsim veya barkod yazın...", width=300)
    arama_entry.pack(side="left")

    liste_frame = ctk.CTkScrollableFrame(sag_frame)
    liste_frame.pack(fill="both", expand=True)

    
    def urunleri_listele(arama_metni=""):
        for widget in liste_frame.winfo_children():
            widget.destroy()

        try:
            sorgu = supabase.table("urunler").select("*")

            if arama_metni:
                arama_metni_alt = arama_metni.lower()
                response = sorgu.execute()
                urunler = [
                    u for u in response.data
                    if arama_metni_alt in u.get('isim', '').lower()
                    or arama_metni_alt in str(u.get('barkod', ''))
                ]
            else:
                response = sorgu.execute()
                urunler = response.data

            if not urunler:
                print("Veritabanı boş veya kriterlere uygun ürün yok.")
                return

            kritik_urunler = []

            for urun in urunler:
                stok_miktari = int(urun.get('stok', 0))

                
                kart_rengi = "#fee2e2" if stok_miktari <= 5 else "transparent"
                uyari_metni = " (KRİTİK STOK!)" if stok_miktari <= 5 else ""
                yazi_rengi = "#ef4444" if stok_miktari <= 5 else "black"

                if stok_miktari <= 5:
                    kritik_urunler.append(urun.get('isim', 'Tanımsız Ürün'))

                kart = ctk.CTkFrame(liste_frame, fg_color=kart_rengi, corner_radius=10)
                kart.pack(fill="x", pady=5, padx=5)

                
                sol = ctk.CTkFrame(kart, fg_color="transparent")
                sol.pack(side="left", fill="both", expand=True, padx=10, pady=8)

                resim_url = urun.get('resim_url')
                img = url_den_resim_getir(resim_url)
                if img:
                    ctk.CTkLabel(sol, image=img, text="").pack(side="left", padx=(0, 10))

                bilgi_frame = ctk.CTkFrame(sol, fg_color="transparent")
                bilgi_frame.pack(side="left")

                bilgi_metni = f"{urun.get('isim', 'İsimsiz')} {uyari_metni}"
                ctk.CTkLabel(bilgi_frame, text=bilgi_metni, font=("Roboto", 13, "bold"), text_color=yazi_rengi).pack(anchor="w")
                ctk.CTkLabel(bilgi_frame, text=f"Stok: {stok_miktari}", font=("Roboto", 11)).pack(anchor="w")

                
                alis = float(urun.get('fiyat', 0))
                satis = float(urun.get('satis_fiyati', 0))
                kar_tl = satis - alis
                if alis > 0:
                    kar_oran = (kar_tl / alis) * 100
                    kar_metni = f"Kâr: %{kar_oran:.1f} ({kar_tl:+.2f} ₺)"
                else:
                    kar_metni = f"Kâr: {kar_tl:+.2f} ₺"
                kar_rengi = "#16a34a" if kar_tl >= 0 else "#ef4444"

                ctk.CTkLabel(bilgi_frame, text=f"Alış: {alis:.2f} ₺  |  Satış: {satis:.2f} ₺", font=("Roboto", 11)).pack(anchor="w")
                ctk.CTkLabel(bilgi_frame, text=kar_metni, font=("Roboto", 11, "bold"), text_color=kar_rengi).pack(anchor="w")

                
                sag = ctk.CTkFrame(kart, fg_color="transparent")
                sag.pack(side="right", padx=10, pady=8)

                ctk.CTkButton(
                    sag, text="Güncelle", width=80,
                    command=lambda u=urun: urun_guncelle_penceresi(u)
                ).pack(pady=(0, 5))

                ctk.CTkButton(
                    sag, text="Sil", width=80, fg_color="#ef4444", hover_color="#b91c1c",
                    command=lambda u_id=urun['id']: urun_sil(u_id)
                ).pack()

            if kritik_urunler and not arama_metni:
                uyari_mesaji = "Şu ürünlerin stoğu bitmek üzere:\n\n" + "\n".join(kritik_urunler)
                messagebox.showwarning("Stok Uyarısı", uyari_mesaji)

        except Exception as e:
            print(f"Listeleme hatası: {e}")
            messagebox.showerror("Hata", f"Ürünler listelenirken bir sorun oluştu: {e}")

    
    arama_zamanlayici = None

    def gecikmeli_arama(event):
        nonlocal arama_zamanlayici

        if arama_zamanlayici is not None:
            dashboard.after_cancel(arama_zamanlayici)

        arama_zamanlayici = dashboard.after(500, lambda: urunleri_listele(arama_entry.get()))

    arama_entry.bind("<KeyRelease>", gecikmeli_arama)

    def urun_ekle_btn():
        try:
            girilen_barkod = barkod_entry.get().strip()
            urun_ismi = isim_entry.get()

            if not urun_ismi:
                messagebox.showwarning("Uyarı", "Lütfen ürün ismini girin!")
                return

            
            if not girilen_barkod:
                son_barkod = "20" + "".join([str(random.randint(0, 9)) for _ in range(11)])
            else:
                son_barkod = girilen_barkod

            
            try:
                if not os.path.exists("barkodlar"):
                    os.makedirs("barkodlar")

                barkod_turu = barcode.get_barcode_class('code128')
                kod_nesnesi = barkod_turu(son_barkod, writer=ImageWriter())

                temiz_isim = "".join(x for x in urun_ismi if x.isalnum() or x in "._- ")
                dosya_yolu = f"barkodlar/{temiz_isim}_{son_barkod}"
                kod_nesnesi.save(dosya_yolu)
            except Exception as e:
                print(f"Barkod resmi oluşturulamadı: {e}")

            
            data = {
                "market_id": kullanici.id,
                "barkod": son_barkod,
                "isim": urun_ismi,
                "resim_url": resim_entry.get(),
                "stok": int(stok_entry.get() or 0),
                "fiyat": float(fiyat_entry.get() or 0.0),
                "satis_fiyati": float(satis_entry.get() or 0.0)
            }
            supabase.table("urunler").insert(data).execute()

            
            barkod_entry.delete(0, 'end')
            isim_entry.delete(0, 'end')
            resim_entry.delete(0, 'end')
            stok_entry.delete(0, 'end')
            fiyat_entry.delete(0, 'end')
            satis_entry.delete(0, 'end')

            urunleri_listele(arama_entry.get())
            messagebox.showinfo("Başarılı", f"Ürün eklendi ve barkod resmi oluşturuldu!\nKod: {son_barkod}")

        except Exception as e:
            messagebox.showerror("Hata", f"İşlem sırasında bir hata oluştu.\nDetay: {e}")

    def urun_sil(urun_id):
        try:
            supabase.table("urunler").delete().eq("id", urun_id).execute()
            urunleri_listele(arama_entry.get())
        except Exception as e:
            messagebox.showerror("Hata", f"Silme işlemi başarısız: {e}")

    def urun_guncelle_penceresi(urun):
        guncelle_popup = ctk.CTkToplevel()
        guncelle_popup.title("Ürün Güncelle")
        guncelle_popup.geometry("350x350")
        guncelle_popup.attributes("-topmost", True)

        ctk.CTkLabel(guncelle_popup, text="Stok Sayısı:").pack(pady=(15, 5))
        yeni_stok_entry = ctk.CTkEntry(guncelle_popup)
        yeni_stok_entry.insert(0, str(urun.get('stok', 0)))
        yeni_stok_entry.pack(pady=5)

        ctk.CTkLabel(guncelle_popup, text="Alış Fiyatı (₺):").pack(pady=5)
        yeni_alis_entry = ctk.CTkEntry(guncelle_popup)
        yeni_alis_entry.insert(0, str(urun.get('fiyat', 0.0)))
        yeni_alis_entry.pack(pady=5)

        ctk.CTkLabel(guncelle_popup, text="Satış Fiyatı (₺):").pack(pady=5)
        yeni_satis_entry = ctk.CTkEntry(guncelle_popup)
        yeni_satis_entry.insert(0, str(urun.get('satis_fiyati', 0.0)))
        yeni_satis_entry.pack(pady=5)

        def degisiklikleri_kaydet():
            try:
                supabase.table("urunler").update({
                    "stok": int(yeni_stok_entry.get()),
                    "fiyat": float(yeni_alis_entry.get()),
                    "satis_fiyati": float(yeni_satis_entry.get())
                }).eq("id", urun['id']).execute()

                guncelle_popup.destroy()
                urunleri_listele(arama_entry.get())
            except Exception as e:
                messagebox.showerror("Hata", f"Lütfen sayısal değerler girin.\nDetay: {e}")

        ctk.CTkButton(guncelle_popup, text="Kaydet", command=degisiklikleri_kaydet).pack(pady=20)

    def istatistikleri_goster():
        try:
            response = supabase.table("urunler").select("*").execute()
            urunler = response.data

            if not urunler:
                messagebox.showinfo("Bilgi", "Grafik çizmek için henüz hiç ürününüz yok.")
                return

            
            urunler_sirali = sorted(
                urunler,
                key=lambda x: float(x.get('satis_fiyati', 0)) - float(x.get('fiyat', 0)),
                reverse=True
            )[:5]

            isimler = [u['isim'] for u in urunler_sirali]
            karlar = [float(u.get('satis_fiyati', 0)) - float(u.get('fiyat', 0)) for u in urunler_sirali]

            ist_popup = ctk.CTkToplevel()
            ist_popup.title("Analiz: En Kârlı 5 Ürün")
            ist_popup.geometry("600x450")
            ist_popup.attributes("-topmost", True)

            fig, ax = plt.subplots(figsize=(6, 4), dpi=100)

            renkler = ['#2ecc71', '#3498db', '#9b59b6', '#f1c40f', '#e74c3c']
            ax.bar(isimler, karlar, color=renkler[:len(isimler)])

            ax.set_title("Birim Başına En Yüksek Kâr Getiren Ürünler", fontsize=12, fontweight="bold")
            ax.set_ylabel("Kâr (₺)")
            ax.grid(axis='y', linestyle='--', alpha=0.7)

            plt.setp(ax.get_xticklabels(), rotation=15, ha="right")
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=ist_popup)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

        except Exception as e:
            messagebox.showerror("Hata", f"Grafik oluşturulurken bir hata meydana geldi.\nDetay: {e}")


    ctk.CTkButton(
        form_frame, text="Ürünü Sisteme Ekle",
        command=urun_ekle_btn, height=40,
        font=("Roboto", 14, "bold")
    ).pack(pady=20, padx=10, fill="x")

    ctk.CTkButton(
        form_frame, text="📊 İstatistikleri Gör",
        command=istatistikleri_goster,
        fg_color="#f39c12", hover_color="#d68910",
        text_color="black", height=40,
        font=("Roboto", 14, "bold")
    ).pack(pady=(0, 10), padx=10, fill="x")

    ctk.CTkButton(
        form_frame, text="🛒 Kasa Ekranı",
        command=lambda: kasa_ekrani_ac(kullanici),
        fg_color="#16a34a", hover_color="#166534",
        text_color="white", height=40,
        font=("Roboto", 14, "bold")
    ).pack(pady=(0, 10), padx=10, fill="x")

    def cikis_yap():
        if messagebox.askyesno("Çıkış Yap", "Oturumu kapatmak istediğinizden emin misiniz?"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            dashboard.destroy()
            email_entry.delete(0, "end")
            sifre_entry.delete(0, "end")
            giris_btn.configure(state="normal")
            app.deiconify()

    ctk.CTkButton(
        form_frame, text="🚪 Çıkış Yap",
        command=cikis_yap,
        fg_color="#ef4444", hover_color="#b91c1c",
        text_color="white", height=40,
        font=("Roboto", 14, "bold")
    ).pack(pady=(0, 20), padx=10, fill="x")

    dashboard.protocol("WM_DELETE_WINDOW", cikis_yap)

    urunleri_listele()


def kasa_ekrani_ac(kullanici):
    kasa = ctk.CTkToplevel()
    kasa.title("🛒 Kasa Ekranı")
    kasa.geometry("1200x780")
    kasa.resizable(True, True)
    kasa.attributes("-topmost", True)

    sepet = []  
    gecmis_yenile = []  


    ust_frame = ctk.CTkFrame(kasa, fg_color="#1e293b", corner_radius=0)
    ust_frame.pack(fill="x", padx=0, pady=0)

    ctk.CTkLabel(
        ust_frame, text="🛒  KASA", font=("Roboto", 22, "bold"),
        text_color="white"
    ).pack(side="left", padx=20, pady=12)

    barkod_kasa_entry = ctk.CTkEntry(
        ust_frame, placeholder_text="Barkod okutun veya yazın...",
        width=320, height=38, font=("Roboto", 14)
    )
    barkod_kasa_entry.pack(side="left", padx=10, pady=12)

    adet_var = ctk.StringVar(value="1")
    adet_spin = ctk.CTkEntry(
        ust_frame, textvariable=adet_var,
        width=60, height=38, font=("Roboto", 14)
    )
    adet_spin.pack(side="left", padx=(0, 10), pady=12)
    ctk.CTkLabel(ust_frame, text="adet", text_color="white", font=("Roboto", 12)).pack(side="left")

    ctk.CTkButton(
        ust_frame, text="← Geri",
        width=90, height=36,
        font=("Roboto", 12, "bold"),
        fg_color="#475569", hover_color="#334155",
        command=kasa.destroy
    ).pack(side="right", padx=15, pady=12)


    orta_frame = ctk.CTkFrame(kasa, fg_color="transparent")
    orta_frame.pack(fill="both", expand=True, padx=10, pady=10)


    stok_panel = ctk.CTkFrame(orta_frame, width=310)
    stok_panel.pack(side="left", fill="y", padx=(0, 6))
    stok_panel.pack_propagate(False)

    stok_baslik_frame = ctk.CTkFrame(stok_panel, fg_color="transparent")
    stok_baslik_frame.pack(fill="x", padx=8, pady=(10, 4))

    ctk.CTkLabel(
        stok_baslik_frame, text="Stok Listesi",
        font=("Roboto", 15, "bold")
    ).pack(side="left")

    stok_yenile_btn = ctk.CTkButton(
        stok_baslik_frame, text="↻", width=32, height=28,
        font=("Roboto", 14, "bold"), fg_color="#475569", hover_color="#334155",
        command=lambda: stok_listesini_yukle()
    )
    stok_yenile_btn.pack(side="right")

    stok_arama_entry = ctk.CTkEntry(
        stok_panel, placeholder_text="Ürün veya barkod ara...",
        height=32, font=("Roboto", 12)
    )
    stok_arama_entry.pack(fill="x", padx=8, pady=(0, 4))

    
    baslik_satir = ctk.CTkFrame(stok_panel, fg_color="#334155", corner_radius=6)
    baslik_satir.pack(fill="x", padx=8, pady=(0, 2))
    ctk.CTkLabel(baslik_satir, text="Ürün Adı", font=("Roboto", 10, "bold"),
                 text_color="white", anchor="w").pack(side="left", padx=6, pady=4, expand=True, fill="x")
    ctk.CTkLabel(baslik_satir, text="Barkod", font=("Roboto", 10, "bold"),
                 text_color="#94a3b8", anchor="w", width=90).pack(side="left", padx=4, pady=4)
    ctk.CTkLabel(baslik_satir, text="Stok", font=("Roboto", 10, "bold"),
                 text_color="#94a3b8", anchor="center", width=30).pack(side="left", padx=2, pady=4)
    ctk.CTkLabel(baslik_satir, text="₺", font=("Roboto", 10, "bold"),
                 text_color="#94a3b8", anchor="e", width=44).pack(side="right", padx=6, pady=4)

    stok_scroll = ctk.CTkScrollableFrame(stok_panel, fg_color="transparent")
    stok_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))


    sol_frame = ctk.CTkFrame(orta_frame)
    sol_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

    ctk.CTkLabel(
        sol_frame, text="Sepet", font=("Roboto", 16, "bold")
    ).pack(pady=(10, 5))

    sepet_liste_frame = ctk.CTkScrollableFrame(sol_frame)
    sepet_liste_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    sag_frame = ctk.CTkFrame(orta_frame, width=310)
    sag_frame.pack(side="right", fill="y", padx=(5, 0))
    sag_frame.pack_propagate(False)

    ctk.CTkLabel(sag_frame, text="Ödeme", font=("Roboto", 16, "bold")).pack(pady=(15, 10))

    toplam_label = ctk.CTkLabel(
        sag_frame, text="Toplam: 0,00 ₺",
        font=("Roboto", 22, "bold"), text_color="#16a34a"
    )
    toplam_label.pack(pady=5, padx=15)

    kdv_label = ctk.CTkLabel(
        sag_frame, text="KDV (%18): 0,00 ₺",
        font=("Roboto", 11), text_color="gray"
    )
    kdv_label.pack(pady=(0, 15), padx=15)

    ctk.CTkLabel(sag_frame, text="Alınan Nakit (₺):", font=("Roboto", 13)).pack(padx=15, anchor="w")
    nakit_entry = ctk.CTkEntry(sag_frame, placeholder_text="0.00", font=("Roboto", 14), height=38)
    nakit_entry.pack(pady=5, padx=15, fill="x")

    para_ustu_label = ctk.CTkLabel(
        sag_frame, text="Para Üstü: —",
        font=("Roboto", 18, "bold"), text_color="#2563eb"
    )
    para_ustu_label.pack(pady=10, padx=15)

    urun_sayisi_label = ctk.CTkLabel(
        sag_frame, text="Sepette 0 çeşit ürün",
        font=("Roboto", 11), text_color="gray"
    )
    urun_sayisi_label.pack(pady=(0, 5), padx=15)

    ayrac = ctk.CTkFrame(sag_frame, height=1, fg_color="#cbd5e1")
    ayrac.pack(fill="x", padx=15, pady=10)

    ctk.CTkLabel(
        sag_frame, text="⌨  Barkod Tuş Takımı",
        font=("Roboto", 11, "bold"), text_color="#64748b"
    ).pack(pady=(2, 4))

    numpad_frame = ctk.CTkFrame(sag_frame, fg_color="transparent")
    numpad_frame.pack(padx=8, pady=(0, 10))

    def numpad_tus(karakter):
        if karakter == "⌫":
            mevcut = barkod_kasa_entry.get()
            barkod_kasa_entry.delete(0, "end")
            barkod_kasa_entry.insert(0, mevcut[:-1])
        elif karakter == "✓":
            barkod_ile_urun_ekle()
        else:
            barkod_kasa_entry.insert("end", karakter)
        barkod_kasa_entry.focus()

    numpad_tuslar = [
        ["7", "8", "9"],
        ["4", "5", "6"],
        ["1", "2", "3"],
        ["⌫", "0", "✓"],
    ]

    for satir_tuslar in numpad_tuslar:
        satir_f = ctk.CTkFrame(numpad_frame, fg_color="transparent")
        satir_f.pack()
        for tus in satir_tuslar:
            if tus == "✓":
                fg, hover = "#16a34a", "#166534"
            elif tus == "⌫":
                fg, hover = "#ef4444", "#b91c1c"
            else:
                fg, hover = "#334155", "#1e293b"
            ctk.CTkButton(
                satir_f, text=tus,
                width=74, height=46,
                font=("Roboto", 17, "bold"),
                fg_color=fg, hover_color=hover,
                command=lambda k=tus: numpad_tus(k)
            ).pack(side="left", padx=2, pady=2)

    ayrac2 = ctk.CTkFrame(sag_frame, height=1, fg_color="#cbd5e1")
    ayrac2.pack(fill="x", padx=15, pady=(4, 8))



    def stok_listesini_yukle(filtre=""):
        for w in stok_scroll.winfo_children():
            w.destroy()
        try:
            resp = supabase.table("urunler").select("*").gt("stok", 0).execute()
            tum_urunler = resp.data or []
        except Exception as e:
            ctk.CTkLabel(stok_scroll, text=f"Yuklenemedi: {e}",
                         text_color="#ef4444", wraplength=260).pack()
            return

        if filtre:
            f = filtre.lower()
            tum_urunler = [
                u for u in tum_urunler
                if f in u.get("isim", "").lower() or f in str(u.get("barkod", ""))
            ]

        if not tum_urunler:
            ctk.CTkLabel(stok_scroll, text="Stokta urun yok.",
                         text_color="gray", font=("Roboto", 12)).pack(pady=20)
            return

        for urun in tum_urunler:
            stok_miktari = int(urun.get("stok", 0))
            satis_f = float(urun.get("satis_fiyati", 0))
            isim = urun.get("isim", "-")
            barkod_no = str(urun.get("barkod", ""))

            satir_rengi = "#fef2f2" if stok_miktari <= 5 else "#f8fafc"
            isim_rengi  = "#ef4444" if stok_miktari <= 5 else "black"

            satir = ctk.CTkFrame(stok_scroll, fg_color=satir_rengi,
                                 corner_radius=6, cursor="hand2")
            satir.pack(fill="x", pady=2)

            ctk.CTkLabel(
                satir, text=isim, font=("Roboto", 11, "bold"),
                text_color=isim_rengi, anchor="w", wraplength=90
            ).pack(side="left", padx=(6, 2), pady=5, fill="x", expand=True)

            ctk.CTkLabel(
                satir, text=barkod_no, font=("Roboto", 10),
                text_color="#475569", anchor="w", width=90
            ).pack(side="left", padx=2, pady=5)

            ctk.CTkLabel(
                satir, text=str(stok_miktari), font=("Roboto", 10, "bold"),
                text_color=isim_rengi, anchor="center", width=30
            ).pack(side="left", padx=2, pady=5)

            ctk.CTkLabel(
                satir, text=f"{satis_f:.2f}TL", font=("Roboto", 10),
                text_color="#16a34a", anchor="e", width=48
            ).pack(side="right", padx=6, pady=5)

            def satira_tikla(u=urun):
                try:
                    adet = int(adet_var.get() or 1)
                except ValueError:
                    adet = 1
                for s in sepet:
                    if s["urun"].get("barkod") == u.get("barkod"):
                        s["adet"] += adet
                        sepeti_yenile()
                        return
                sepet.append({"urun": u, "adet": adet})
                sepeti_yenile()

            satir.bind("<Button-1>", lambda e, u=urun: satira_tikla(u))
            for child in satir.winfo_children():
                child.bind("<Button-1>", lambda e, u=urun: satira_tikla(u))

    _stok_arama_timer = None

    def stok_arama_tetikle(event=None):
        nonlocal _stok_arama_timer
        if _stok_arama_timer:
            kasa.after_cancel(_stok_arama_timer)
        _stok_arama_timer = kasa.after(350, lambda: stok_listesini_yukle(stok_arama_entry.get()))

    stok_arama_entry.bind("<KeyRelease>", stok_arama_tetikle)

    def toplami_guncelle():
        toplam = sum(s["urun"].get("satis_fiyati", 0) * s["adet"] for s in sepet)
        kdv = toplam - toplam / 1.18
        toplam_label.configure(text=f"Toplam: {toplam:,.2f} ₺".replace(",", "."))
        kdv_label.configure(text=f"KDV (%18): {kdv:,.2f} ₺".replace(",", "."))
        urun_sayisi_label.configure(text=f"Sepette {len(sepet)} çeşit ürün")
        para_ustunu_hesapla()

    def para_ustunu_hesapla(*args):
        try:
            toplam = sum(s["urun"].get("satis_fiyati", 0) * s["adet"] for s in sepet)
            nakit = float(nakit_entry.get().replace(",", ".") or 0)
            if nakit >= toplam and toplam > 0:
                ustu = nakit - toplam
                para_ustu_label.configure(
                    text=f"Para Üstü: {ustu:,.2f} ₺".replace(",", "."),
                    text_color="#2563eb"
                )
            elif nakit < toplam and nakit > 0:
                eksik = toplam - nakit
                para_ustu_label.configure(
                    text=f"Eksik: {eksik:,.2f} ₺".replace(",", "."),
                    text_color="#ef4444"
                )
            else:
                para_ustu_label.configure(text="Para Üstü: —", text_color="#2563eb")
        except Exception:
            para_ustu_label.configure(text="Para Üstü: —", text_color="#2563eb")

    nakit_entry.bind("<KeyRelease>", para_ustunu_hesapla)

    def sepeti_yenile():
        for w in sepet_liste_frame.winfo_children():
            w.destroy()

        for idx, satir in enumerate(sepet):
            urun = satir["urun"]
            adet = satir["adet"]
            satis_f = float(urun.get("satis_fiyati", 0))
            ara_toplam = satis_f * adet
            stok_mevcut = int(urun.get("stok", 0)) if urun.get("stok") is not None else "?"

            kart = ctk.CTkFrame(sepet_liste_frame, fg_color="#f8fafc", corner_radius=8)
            kart.pack(fill="x", pady=3, padx=4)

            sol = ctk.CTkFrame(kart, fg_color="transparent")
            sol.pack(side="left", fill="both", expand=True, padx=10, pady=6)

            isim_metni = urun.get("isim", "—")
            barkod_metni = urun.get("barkod", "")
            ctk.CTkLabel(sol, text=isim_metni, font=("Roboto", 13, "bold")).pack(anchor="w")
            ctk.CTkLabel(
                sol,
                text=f"Barkod: {barkod_metni}  |  {satis_f:.2f} ₺ × {adet} = {ara_toplam:.2f} ₺",
                font=("Roboto", 11), text_color="gray"
            ).pack(anchor="w")

            if isinstance(stok_mevcut, int) and adet > stok_mevcut:
                ctk.CTkLabel(
                    sol, text=f"⚠️ Stok yetmez! (Stok: {stok_mevcut})",
                    font=("Roboto", 10), text_color="#ef4444"
                ).pack(anchor="w")

            sag = ctk.CTkFrame(kart, fg_color="transparent")
            sag.pack(side="right", padx=8, pady=6)

            def adet_artir(i=idx):
                sepet[i]["adet"] += 1
                sepeti_yenile()
                toplami_guncelle()

            def adet_azalt(i=idx):
                if sepet[i]["adet"] > 1:
                    sepet[i]["adet"] -= 1
                    sepeti_yenile()
                    toplami_guncelle()

            def satirdan_kaldir(i=idx):
                sepet.pop(i)
                sepeti_yenile()
                toplami_guncelle()

            ctk.CTkButton(sag, text="+", width=28, height=28, font=("Roboto", 14, "bold"),
                          command=adet_artir).pack(pady=(0, 2))
            ctk.CTkButton(sag, text="−", width=28, height=28, font=("Roboto", 14, "bold"),
                          fg_color="#64748b", hover_color="#475569",
                          command=adet_azalt).pack(pady=2)
            ctk.CTkButton(sag, text="✕", width=28, height=28, font=("Roboto", 12),
                          fg_color="#ef4444", hover_color="#b91c1c",
                          command=satirdan_kaldir).pack(pady=(2, 0))

        toplami_guncelle()

    def barkod_ile_urun_ekle(event=None):
        barkod_no = barkod_kasa_entry.get().strip()
        if not barkod_no:
            return

        try:
            adet = int(adet_var.get() or 1)
            if adet < 1:
                adet = 1
        except ValueError:
            adet = 1

        try:
            resp = supabase.table("urunler").select("*").eq("barkod", barkod_no).execute()
            sonuclar = resp.data
        except Exception as e:
            messagebox.showerror("Hata", f"Veritabanı hatası: {e}")
            return

        barkod_kasa_entry.delete(0, "end")
        adet_var.set("1")

        if not sonuclar:
            stoksuz_urun_ekle(barkod_no, adet)
            return

        urun = sonuclar[0]

        for satir in sepet:
            if satir["urun"].get("barkod") == urun.get("barkod"):
                satir["adet"] += adet
                sepeti_yenile()
                return

        sepet.append({"urun": urun, "adet": adet})
        sepeti_yenile()

    def stoksuz_urun_ekle(barkod_no, adet):
        """Veritabanında kaydı olmayan ürünü manuel bilgiyle kasadan geçir."""
        popup = ctk.CTkToplevel(kasa)
        popup.title("Kayıtsız Ürün — Manuel Giriş")
        popup.geometry("380x280")
        popup.attributes("-topmost", True)
        popup.grab_set()

        ctk.CTkLabel(
            popup,
            text=f"Barkod {barkod_no} sistemde bulunamadı.\nÜrünü manuel olarak ekleyebilirsiniz.",
            font=("Roboto", 12), wraplength=340
        ).pack(pady=(15, 10), padx=20)

        isim_p = ctk.CTkEntry(popup, placeholder_text="Ürün adı", width=320)
        isim_p.pack(pady=5, padx=20)

        fiyat_p = ctk.CTkEntry(popup, placeholder_text="Satış fiyatı (₺)", width=320)
        fiyat_p.pack(pady=5, padx=20)

        def manuel_ekle():
            isim = isim_p.get().strip() or f"Ürün ({barkod_no})"
            try:
                fiyat = float(fiyat_p.get().replace(",", ".") or 0)
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir fiyat girin.", parent=popup)
                return

            yapay_urun = {
                "barkod": barkod_no,
                "isim": isim,
                "satis_fiyati": fiyat,
                "stok": None,   
                "fiyat": 0.0
            }
            sepet.append({"urun": yapay_urun, "adet": adet})
            sepeti_yenile()
            popup.destroy()

        ctk.CTkButton(popup, text="Sepete Ekle", command=manuel_ekle,
                      fg_color="#16a34a", hover_color="#166534").pack(pady=15)

    def satis_tamamla():
        if not sepet:
            messagebox.showwarning("Uyarı", "Sepet boş!", parent=kasa)
            return

        toplam = sum(s["urun"].get("satis_fiyati", 0) * s["adet"] for s in sepet)

        try:
            nakit = float(nakit_entry.get().replace(",", ".") or 0)
        except ValueError:
            nakit = 0

        if nakit < toplam:
            onay = messagebox.askyesno(
                "Yetersiz Nakit",
                f"Alınan nakit ({nakit:.2f} ₺) toplamdan ({toplam:.2f} ₺) az.\n"
                "Yine de satışı tamamlamak istiyor musunuz?",
                parent=kasa
            )
            if not onay:
                return

        hatalar = []
        satis_kalemleri = []
        for satir in sepet:
            urun = satir["urun"]
            adet = satir["adet"]
            urun_id = urun.get("id")
            mevcut_stok = urun.get("stok")

            satis_kalemleri.append({
                "isim": urun.get("isim", "?"),
                "barkod": urun.get("barkod", ""),
                "adet": adet,
                "birim_fiyat": float(urun.get("satis_fiyati", 0)),
                "ara_toplam": float(urun.get("satis_fiyati", 0)) * adet
            })

            if urun_id is None or mevcut_stok is None:
                continue

            yeni_stok = max(0, int(mevcut_stok) - adet)
            try:
                supabase.table("urunler").update({"stok": yeni_stok}).eq("id", urun_id).execute()
            except Exception as e:
                hatalar.append(f"{urun.get('isim')}: {e}")

        ustu = max(0, nakit - toplam)
        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        satis_kaydedildi = False
        kayit_verisi = {
            "market_id": str(kullanici.id),
            "tarih": simdi,
            "toplam": round(toplam, 2),
            "nakit": round(nakit, 2),
            "para_ustu": round(ustu, 2),
            "urunler": json.dumps(satis_kalemleri, ensure_ascii=False)
        }
        print(f"[DEBUG] Satış kaydediliyor: market_id={kayit_verisi['market_id']!r}, toplam={kayit_verisi['toplam']}")
        try:
            insert_resp = supabase.table("satislar").insert(kayit_verisi).execute()
            print(f"[DEBUG] Insert sonucu: {insert_resp.data}")
            satis_kaydedildi = True
        except Exception as e:
            print(f"[DEBUG] Insert HATASI: {e}")
            messagebox.showerror(
                "Kayıt Hatası",
                f"Satış veritabanına kaydedilemedi!\n\nHata: {e}\n\n"
                "Sepet temizlenmedi, tekrar deneyin.",
                parent=kasa
            )
            return  

        ozet = (
            f"✅ Satış Tamamlandı\n\n"
            f"Tarih: {simdi}\n"
            f"Toplam: {toplam:.2f} ₺\n"
            f"Alınan Nakit: {nakit:.2f} ₺\n"
            f"Para Üstü: {ustu:.2f} ₺"
        )
        if hatalar:
            ozet += "\n\n⚠️ Uyarılar:\n" + "\n".join(hatalar)

        messagebox.showinfo("Satış Özeti", ozet, parent=kasa)

        sepet.clear()
        nakit_entry.delete(0, "end")
        sepeti_yenile()
        stok_listesini_yukle()

        if gecmis_yenile:
            try:
                gecmis_yenile[0]()
            except Exception:
                gecmis_yenile.clear()

    def sepeti_temizle():
        if sepet and messagebox.askyesno("Onayla", "Sepet temizlensin mi?", parent=kasa):
            sepet.clear()
            sepeti_yenile()

    ctk.CTkButton(
        ust_frame, text="Ekle →", width=80, height=38,
        font=("Roboto", 13, "bold"),
        command=barkod_ile_urun_ekle
    ).pack(side="left", padx=10, pady=12)

    barkod_kasa_entry.bind("<Return>", barkod_ile_urun_ekle)
    barkod_kasa_entry.focus()

    ctk.CTkButton(
        sag_frame, text="✅  Satışı Tamamla", height=48,
        font=("Roboto", 15, "bold"),
        fg_color="#16a34a", hover_color="#166534",
        command=satis_tamamla
    ).pack(fill="x", padx=15, pady=5)

    ctk.CTkButton(
        sag_frame, text="🗑  Sepeti Temizle", height=38,
        font=("Roboto", 13),
        fg_color="#ef4444", hover_color="#b91c1c",
        command=sepeti_temizle
    ).pack(fill="x", padx=15, pady=(0, 5))

    ctk.CTkButton(
        sag_frame, text="📋  Satış Geçmişi", height=38,
        font=("Roboto", 13),
        fg_color="#2563eb", hover_color="#1d4ed8",
        command=lambda: satis_gecmisi_ac(kullanici, kasa, gecmis_yenile)
    ).pack(fill="x", padx=15, pady=(0, 10))

    stok_listesini_yukle()
    sepeti_yenile()


def satis_gecmisi_ac(kullanici, parent=None, yenile_ref=None):
    from datetime import timedelta

    pencere = ctk.CTkToplevel(parent)
    pencere.title("📋 Satış Geçmişi")
    pencere.geometry("900x660")
    pencere.resizable(True, True)
    if parent:
        pencere.attributes("-topmost", True)

    ust = ctk.CTkFrame(pencere, fg_color="#1e293b", corner_radius=0)
    ust.pack(fill="x")

    ctk.CTkLabel(
        ust, text="📋  Satış Geçmişi",
        font=("Roboto", 20, "bold"), text_color="white"
    ).pack(side="left", padx=20, pady=12)

    filtre_entry = ctk.CTkEntry(
        ust, placeholder_text="Ürün ara...",
        width=200, height=34, font=("Roboto", 12)
    )
    filtre_entry.pack(side="left", padx=10, pady=12)

    ctk.CTkButton(
        ust, text="↻ Yenile", width=80, height=34,
        font=("Roboto", 12, "bold"),
        fg_color="#475569", hover_color="#334155",
        command=lambda: gecmisi_yukle()
    ).pack(side="right", padx=15, pady=12)

    filtre_bar = ctk.CTkFrame(pencere, fg_color="#f8fafc", corner_radius=0)
    filtre_bar.pack(fill="x")

    aktif_filtre = ["tumu"]  
    filtre_butonlari = {}

    def filtre_sec(kod):
        aktif_filtre[0] = kod
        for k, btn in filtre_butonlari.items():
            if k == kod:
                btn.configure(fg_color="#1e293b", text_color="white")
            else:
                btn.configure(fg_color="#e2e8f0", text_color="#334155")
        gecmisi_yukle()

    for kod, etiket in [("tumu", "📅 Tümü"), ("bugun", "Bugün"), ("hafta", "Bu Hafta"), ("ay", "Bu Ay")]:
        btn = ctk.CTkButton(
            filtre_bar, text=etiket,
            width=110, height=32,
            font=("Roboto", 12, "bold"),
            fg_color="#1e293b" if kod == "tumu" else "#e2e8f0",
            text_color="white" if kod == "tumu" else "#334155",
            hover_color="#334155",
            command=lambda k=kod: filtre_sec(k)
        )
        btn.pack(side="left", padx=(10 if kod == "tumu" else 4), pady=8)
        filtre_butonlari[kod] = btn

    ozet_frame = ctk.CTkFrame(pencere, fg_color="#f1f5f9", corner_radius=0)
    ozet_frame.pack(fill="x")

    toplam_satis_label = ctk.CTkLabel(
        ozet_frame, text="Toplam: 0 satış  |  0,00 ₺",
        font=("Roboto", 12, "bold"), text_color="#334155"
    )
    toplam_satis_label.pack(side="left", padx=20, pady=6)

    donem_label = ctk.CTkLabel(
        ozet_frame, text="",
        font=("Roboto", 11), text_color="#64748b"
    )
    donem_label.pack(side="left", padx=5, pady=6)

    tablo_baslik = ctk.CTkFrame(pencere, fg_color="#334155", corner_radius=0)
    tablo_baslik.pack(fill="x", padx=0)

    for metin, genislik, hiza in [
        ("Tarih & Saat", 160, "w"),
        ("Ürünler", 0, "w"),
        ("Toplam", 90, "e"),
        ("Nakit", 80, "e"),
        ("Para Üstü", 90, "e"),
    ]:
        pack_kw = {"expand": True, "fill": "x"} if genislik == 0 else {}
        label_kw = {} if genislik == 0 else {"width": genislik}
        ctk.CTkLabel(
            tablo_baslik, text=metin,
            font=("Roboto", 11, "bold"), text_color="white",
            anchor=hiza, **label_kw
        ).pack(side="left", padx=8, pady=6, **pack_kw)

    liste_scroll = ctk.CTkScrollableFrame(pencere, fg_color="transparent")
    liste_scroll.pack(fill="both", expand=True, padx=8, pady=8)

    tum_satislar = []

    def tarih_araligini_hesapla():
        """Aktif filtreye göre başlangıç tarihini döndür (None = tümü)."""
        bugun = datetime.now().date()
        if aktif_filtre[0] == "bugun":
            return bugun, bugun, "Bugün"
        elif aktif_filtre[0] == "hafta":
            baslangic = bugun - timedelta(days=bugun.weekday())
            return baslangic, bugun, f"Bu Hafta ({baslangic.strftime('%d.%m')} – {bugun.strftime('%d.%m.%Y')})"
        elif aktif_filtre[0] == "ay":
            baslangic = bugun.replace(day=1)
            return baslangic, bugun, f"Bu Ay ({bugun.strftime('%B %Y')})"
        return None, None, "Tüm Zamanlar"

    def tarih_parse(tarih_str):
        """Supabase tarih stringini date nesnesine çevir."""
        try:
            return datetime.fromisoformat(tarih_str.replace("Z", "+00:00")).date()
        except Exception:
            try:
                return datetime.strptime(tarih_str[:10], "%Y-%m-%d").date()
            except Exception:
                return None

    def tarih_goster(tarih_str):
        """Supabase tarihini okunabilir formata çevir."""
        try:
            dt = datetime.fromisoformat(tarih_str.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y  %H:%M")
        except Exception:
            return tarih_str

    def gecmisi_yukle(filtre=""):
        nonlocal tum_satislar
        for w in liste_scroll.winfo_children():
            w.destroy()

        kullanici_id_str = str(kullanici.id) if kullanici and kullanici.id else None

        try:
            resp = (
                supabase.table("satislar")
                .select("*")
                .eq("market_id", kullanici_id_str)
                .order("tarih", desc=True)
                .execute()
            )
            tum_satislar = resp.data or []
        except Exception as e:
            ctk.CTkLabel(liste_scroll, text=f"Yüklenemedi: {e}",
                         text_color="#ef4444").pack(pady=20)
            return

        baslangic, bitis, donem_metni = tarih_araligini_hesapla()
        donem_label.configure(text=f"— {donem_metni}")

        if baslangic is not None:
            filtrelenmis = []
            for s in tum_satislar:
                s_tarih = tarih_parse(s.get("tarih", ""))
                if s_tarih and baslangic <= s_tarih <= bitis:
                    filtrelenmis.append(s)
            tum_satislar = filtrelenmis

        metin = filtre_entry.get().strip().lower() if not filtre else filtre.lower()
        if metin:
            tum_satislar = [
                s for s in tum_satislar
                if metin in str(s.get("urunler", "")).lower()
                or metin in s.get("tarih", "").lower()
            ]

        if not tum_satislar:
            ctk.CTkLabel(
                liste_scroll,
                text="Bu dönemde satış kaydı bulunamadı." if baslangic else "Henüz satış kaydı yok.",
                text_color="gray", font=("Roboto", 13)
            ).pack(pady=30)
            toplam_satis_label.configure(text="Toplam: 0 satış  |  0,00 ₺")
            return

        genel_toplam = sum(float(s.get("toplam", 0)) for s in tum_satislar)
        toplam_satis_label.configure(
            text=f"Toplam: {len(tum_satislar)} satış  |  {genel_toplam:,.2f} ₺".replace(",", ".")
        )

        for idx, satis in enumerate(tum_satislar):
            satir_rengi = "#f8fafc" if idx % 2 == 0 else "#ffffff"
            kart = ctk.CTkFrame(liste_scroll, fg_color=satir_rengi, corner_radius=8)
            kart.pack(fill="x", pady=3)

            tarih_str = tarih_goster(satis.get("tarih", "—"))
            tarih_label = ctk.CTkLabel(
                kart, text=tarih_str,
                font=("Roboto", 11, "bold"), text_color="#1e293b",
                width=155, anchor="w"
            )
            tarih_label.pack(side="left", padx=(10, 4), pady=8)

            try:
                urunler_raw = satis.get("urunler", "[]")
                kalemler = urunler_raw if isinstance(urunler_raw, list) else json.loads(urunler_raw)
                urun_ozeti = ", ".join(f"{k['isim']} ×{k['adet']}" for k in kalemler)
                if len(urun_ozeti) > 55:
                    urun_ozeti = urun_ozeti[:52] + "..."
            except Exception:
                urun_ozeti = "—"

            ctk.CTkLabel(
                kart, text=urun_ozeti,
                font=("Roboto", 11), text_color="#475569", anchor="w"
            ).pack(side="left", padx=4, pady=8, fill="x", expand=True)

            ctk.CTkLabel(
                kart, text=f"{float(satis.get('toplam', 0)):.2f} ₺",
                font=("Roboto", 11, "bold"), text_color="#16a34a",
                width=85, anchor="e"
            ).pack(side="left", padx=4, pady=8)

            ctk.CTkLabel(
                kart, text=f"{float(satis.get('nakit', 0)):.2f} ₺",
                font=("Roboto", 11), text_color="#334155",
                width=75, anchor="e"
            ).pack(side="left", padx=4, pady=8)

            ustu_val = float(satis.get("para_ustu", 0))
            ctk.CTkLabel(
                kart, text=f"{ustu_val:.2f} ₺",
                font=("Roboto", 11, "bold"),
                text_color="#2563eb" if ustu_val > 0 else "gray",
                width=85, anchor="e"
            ).pack(side="left", padx=(4, 10), pady=8)

            detay_frame = ctk.CTkFrame(liste_scroll, fg_color="#eef2ff", corner_radius=6)
            detay_acik = [False]

            def detay_toggle(df=detay_frame, acik=detay_acik, s=satis):
                acik[0] = not acik[0]
                if acik[0]:
                    try:
                        urunler_raw = s.get("urunler", "[]")
                        kalemler = urunler_raw if isinstance(urunler_raw, list) else json.loads(urunler_raw)
                    except Exception:
                        kalemler = []
                    for w in df.winfo_children():
                        w.destroy()
                    for k in kalemler:
                        ctk.CTkLabel(
                            df,
                            text=f"  • {k['isim']}  —  Barkod: {k.get('barkod', '?')}  |  "
                                 f"{k['adet']} adet × {k['birim_fiyat']:.2f} ₺ = {k['ara_toplam']:.2f} ₺",
                            font=("Roboto", 11), text_color="#1e3a5f", anchor="w"
                        ).pack(anchor="w", padx=16, pady=2)
                    df.pack(fill="x", padx=12, pady=(0, 4))
                else:
                    df.pack_forget()

            kart.bind("<Button-1>", lambda e, t=detay_toggle: t())
            tarih_label.bind("<Button-1>", lambda e, t=detay_toggle: t())


    _timer = None
    def filtre_tetikle(event=None):
        nonlocal _timer
        if _timer:
            pencere.after_cancel(_timer)
        _timer = pencere.after(350, gecmisi_yukle)

    filtre_entry.bind("<KeyRelease>", filtre_tetikle)

    if yenile_ref is not None:
        yenile_ref.clear()
        yenile_ref.append(gecmisi_yukle)

    def pencere_kapat():
        if yenile_ref is not None:
            yenile_ref.clear()
        pencere.destroy()

    pencere.protocol("WM_DELETE_WINDOW", pencere_kapat)

    gecmisi_yukle()


baslik = ctk.CTkLabel(app, text="Stok Takip Otomasyonu", font=("Roboto", 24, "bold"))
baslik.pack(pady=(40, 20))

email_entry = ctk.CTkEntry(app, placeholder_text="E-posta Adresiniz", width=250)
email_entry.pack(pady=10)

sifre_entry = ctk.CTkEntry(app, placeholder_text="Şifreniz", show="*", width=250)
sifre_entry.pack(pady=10)

giris_btn = ctk.CTkButton(app, text="Giriş Yap", command=giris_yap, width=250)
giris_btn.pack(pady=(20, 10))

kayit_btn = ctk.CTkButton(
    app, text="Kayıt Ol", command=kayit_ol, width=250,
    fg_color="transparent", border_width=2,
    text_color=("gray10", "#DCE4EE")
)
kayit_btn.pack(pady=10)

app.mainloop()