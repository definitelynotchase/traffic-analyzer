import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.ticker as ticker
import scipy.stats as stats
import warnings
import os
import sys
import subprocess  # Niezbędne dla macOS

# Konfiguracja wyglądu
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
warnings.filterwarnings('ignore')


def resource_path(relative_path):
    """ Pobiera absolutną ścieżkę do zasobu wewnątrz paczki .app """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# =============================================================================
# LOGIKA BIZNESOWA
# =============================================================================
class TrafficEngine:
    def __init__(self):
        self.wyczysc_dane()

    def wyczysc_dane(self):
        self.wszystkie_df = []
        self.tcbh_start_index = 0

    def wczytaj_baze_i_symuluj(self, sciezka_czas, sciezka_int, ile_dni=31):
        try:
            self.wyczysc_dane()
            if not os.path.isabs(sciezka_czas): sciezka_czas = resource_path(sciezka_czas)
            if not os.path.isabs(sciezka_int): sciezka_int = resource_path(sciezka_int)

            if not os.path.exists(sciezka_czas): return False, f"Brak pliku: {sciezka_czas}"
            if not os.path.exists(sciezka_int): return False, f"Brak pliku: {sciezka_int}"

            df_czas = pd.read_csv(sciezka_czas, header=None, names=['czas_trwania'], on_bad_lines='skip')
            df_czas['czas_trwania'] = pd.to_numeric(df_czas['czas_trwania'], errors='coerce')
            df_czas = df_czas.dropna()
            czasy = df_czas['czas_trwania'].values

            h_min = czasy.mean() / 60.0
            c_total = len(czasy)

            df_int = pd.read_csv(sciezka_int, sep='\s+', header=None, names=['minuta', 'intensywnosc_norm_str'])
            df_int['intensywnosc_norm'] = df_int['intensywnosc_norm_str'].str.replace(',', '.').astype(float)
            df_int = df_int[['minuta', 'intensywnosc_norm']].dropna()
            df_int['minuta'] = df_int['minuta'].astype(int)

            df_pelny = pd.DataFrame({'minuta': range(1, 1441)})
            df_pelny = pd.merge(df_pelny, df_int, on='minuta', how='left')
            df_pelny['intensywnosc_norm'] = df_pelny['intensywnosc_norm'].fillna(0)

            prob_sum = df_pelny['intensywnosc_norm'].sum()
            if not np.isclose(prob_sum, 1.0) and prob_sum > 0:
                df_pelny['intensywnosc_norm'] = df_pelny['intensywnosc_norm'] / prob_sum

            profil = df_pelny['intensywnosc_norm'].values
            df_pelny['ruch_erl'] = profil * c_total * h_min
            self.wszystkie_df = [df_pelny]

            for _ in range(ile_dni):
                self.wszystkie_df.append(self._symuluj_dzien(czasy, profil, c_total))

            return True, "Symulacja OK."
        except Exception as e:
            return False, f"Błąd symulacji: {str(e)}"

    def _symuluj_dzien(self, pula_czasow, profil_prawd, c_total_base):
        c_new = int(np.random.normal(loc=c_total_base, scale=c_total_base * 0.05))
        if c_new < 1: c_new = 1
        nowe_czasy = np.random.choice(pula_czasow, size=c_new, replace=True)
        h_new_min = nowe_czasy.mean() / 60.0
        shift = np.random.randint(-120, 121)
        profil_shifted = np.roll(profil_prawd, shift)
        wywolania = np.random.multinomial(c_new, profil_shifted)
        df = pd.DataFrame({'minuta': range(1, 1441)})
        df['ruch_erl'] = wywolania * h_new_min
        return df

    def wczytaj_folder_csv(self, sciezka_folderu):
        self.wyczysc_dane()
        try:
            pliki = [f for f in os.listdir(sciezka_folderu) if f.endswith('.csv')]
            if not pliki: return False, "Brak plików CSV w tym folderze."
            licznik = 0
            for plik in pliki:
                try:
                    full_path = os.path.join(sciezka_folderu, plik)
                    df = pd.read_csv(full_path, sep=';')
                    if 'ruch_erl' not in df.columns: df = pd.read_csv(full_path, sep=',')
                    if 'ruch_erl' in df.columns:
                        df['ruch_erl'] = pd.to_numeric(df['ruch_erl'].astype(str).str.replace(',', '.'),
                                                       errors='coerce').fillna(0)
                        if 'minuta' not in df.columns: df['minuta'] = range(1, len(df) + 1)
                        if len(df) > 1440: df = df.iloc[:1440]
                        if len(df) < 1440:
                            df = pd.concat([df, pd.DataFrame({'minuta': range(len(df) + 1, 1441), 'ruch_erl': 0})])
                        self.wszystkie_df.append(df)
                        licznik += 1
                except:
                    continue

            if licznik < 1: return False, "Brak poprawnych plików CSV."
            return True, f"Wczytano {licznik} plików."
        except Exception as e:
            return False, f"Błąd odczytu: {str(e)}"

    def oblicz_gnr(self, start_h=0, end_h=24):
        if not self.wszystkie_df: return None

        liczba_dni = len(self.wszystkie_df)
        macierz = np.zeros((1440, liczba_dni))
        for i, df in enumerate(self.wszystkie_df):
            macierz[:, i] = df['ruch_erl'].values

        sredni_profil = macierz.mean(axis=1)

        idx_start = max(0, int(start_h * 60))
        idx_end = min(1440, int(end_h * 60))
        if idx_start >= idx_end: idx_start, idx_end = 0, 1440

        profil_analizowany = sredni_profil[idx_start:idx_end]
        if len(profil_analizowany) < 60: return None

        okno = 60
        srednia_ruchoma = np.convolve(profil_analizowany, np.ones(okno) / okno, mode='valid')
        local_max_idx = np.argmax(srednia_ruchoma)
        self.tcbh_start_index = idx_start + local_max_idx
        val_tcbh = srednia_ruchoma[local_max_idx]

        h_s = self.tcbh_start_index // 60
        m_s = self.tcbh_start_index % 60
        h_e = (self.tcbh_start_index + 60) // 60
        m_e = (self.tcbh_start_index + 60) % 60
        str_tcbh = f"{h_s:02d}:{m_s:02d} - {h_e:02d}:{m_e:02d}"

        maxy_sliding = []
        macierz_okno = macierz[idx_start:idx_end, :]
        for i in range(liczba_dni):
            ruchoma_dnia = np.convolve(macierz_okno[:, i], np.ones(okno) / okno, mode='valid')
            if len(ruchoma_dnia) > 0:
                maxy_sliding.append(np.max(ruchoma_dnia))
            else:
                maxy_sliding.append(0)
        val_adph = np.mean(maxy_sliding)

        profil_godzinowy = sredni_profil.reshape(-1, 60).mean(axis=1)
        godziny_zakres = range(int(start_h), int(end_h))
        if len(godziny_zakres) > 0:
            godziny_zakres = [g for g in godziny_zakres if g < 24]
            val_fdmh = np.max(profil_godzinowy[godziny_zakres])
        else:
            val_fdmh = 0.0

        okno_tcbh_data = macierz[self.tcbh_start_index: self.tcbh_start_index + 60, :]
        srednie_dnia_w_tcbh = okno_tcbh_data.mean(axis=0)
        std_dev = np.std(srednie_dnia_w_tcbh, ddof=1)
        sem = std_dev / np.sqrt(liczba_dni)

        margines_bledu = 0.0
        if liczba_dni > 1:
            conf_interval = stats.t.interval(0.95, df=liczba_dni - 1, scale=sem)[1]
            margines_bledu = conf_interval * 1.0

        return {
            "dni": liczba_dni,
            "tcbh_val": val_tcbh,
            "tcbh_time": str_tcbh,
            "adph_val": val_adph,
            "fdmh_val": val_fdmh,
            "error_margin": margines_bledu
        }


# =============================================================================
# GUI
# =============================================================================
class TrafficApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("TrafficAnalyzer")
        self.geometry("1400x950")
        self.minsize(1024, 800)

        # Na macOS ikona jest ustawiana przez pakiet .app (Info.plist),
        # a nie przez kod. Usunąłem wywołanie iconbitmap, bo na Macu często
        # powoduje błędy z plikami .ico. PyInstaller zajmie się ikoną.

        self.engine = TrafficEngine()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # === LEWE MENU ===
        self.left_frame = ctk.CTkFrame(self, width=350, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nswe")

        self.btn_help = ctk.CTkButton(self.left_frame, text="POMOC / INSTRUKCJA", command=self.otworz_pomoc,
                                      fg_color="#3a7ebf", hover_color="#2a5e8f")
        self.btn_help.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="ew")

        self.btn_doc = ctk.CTkButton(self.left_frame, text="📄 PEŁNA DOKUMENTACJA (PDF)",
                                     command=self.otworz_pdf,
                                     fg_color="#8e44ad", hover_color="#9b59b6")
        self.btn_doc.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(self.left_frame, text="TRAFFIC ANALYZER", font=ctk.CTkFont(size=24, weight="bold")).grid(row=2,
                                                                                                              column=0,
                                                                                                              padx=20,
                                                                                                              pady=(10,
                                                                                                                    20))

        # --- IMPORT ---
        ctk.CTkLabel(self.left_frame, text="1. IMPORT DANYCH", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#aaaaaa").grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")

        self.btn_folder = ctk.CTkButton(self.left_frame, text="Wgraj Folder z Pomiarami (.csv)",
                                        command=self.akcja_tryb_folder, fg_color="#2fa34e", hover_color="#25803d",
                                        height=45)
        self.btn_folder.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.btn_auto = ctk.CTkButton(self.left_frame, text="Symulacja (Auto)", command=self.akcja_tryb_auto,
                                      fg_color="#3a7ebf", hover_color="#2a5e8f")
        self.btn_auto.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        # --- PARAMETRY ---
        ctk.CTkLabel(self.left_frame, text="2. PARAMETRY ANALIZY", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#aaaaaa").grid(row=6, column=0, padx=20, pady=(20, 5), sticky="w")

        self.frame_params = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.frame_params.grid(row=7, column=0, padx=20, pady=5, sticky="ew")

        godziny = [str(i) for i in range(25)]

        ctk.CTkLabel(self.frame_params, text="OD:").pack(side="left", padx=5)
        self.combo_start = ctk.CTkOptionMenu(self.frame_params, values=godziny, width=60)
        self.combo_start.set("0")
        self.combo_start.pack(side="left", padx=5)

        ctk.CTkLabel(self.frame_params, text="DO:").pack(side="left", padx=5)
        self.combo_end = ctk.CTkOptionMenu(self.frame_params, values=godziny, width=60)
        self.combo_end.set("24")
        self.combo_end.pack(side="left", padx=5)

        self.btn_recalc = ctk.CTkButton(self.frame_params, text="⟳ Przelicz", width=80,
                                        command=self.aktualizuj_wyniki, fg_color="#555555", hover_color="#333333")
        self.btn_recalc.pack(side="right", padx=10)

        # --- DASHBOARD ---
        ctk.CTkLabel(self.left_frame, text="3. WYNIKI (DASHBOARD)", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#aaaaaa").grid(row=8, column=0, padx=20, pady=(30, 5), sticky="w")

        self.results_container = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.results_container.grid(row=9, column=0, padx=10, pady=5, sticky="ew")

        self.card_tcbh = ctk.CTkFrame(self.results_container, fg_color="#2b2b2b", corner_radius=10, border_width=1,
                                      border_color="#ff0055")
        self.card_tcbh.pack(fill="x", pady=5)
        ctk.CTkLabel(self.card_tcbh, text="TCBH (Pływająca)", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(
            anchor="w", padx=10, pady=(5, 0))
        self.val_tcbh = ctk.CTkLabel(self.card_tcbh, text="--.-- Erl", font=("Arial", 28, "bold"), text_color="#ffffff")
        self.val_tcbh.pack(anchor="w", padx=10, pady=(0, 0))
        self.time_tcbh = ctk.CTkLabel(self.card_tcbh, text="Czas: --:-- - --:--", font=("Arial", 12),
                                      text_color="#ff0055")
        self.time_tcbh.pack(anchor="w", padx=10, pady=(0, 5))

        self.card_conf = ctk.CTkFrame(self.results_container, fg_color="#2b2b2b", corner_radius=10, border_width=1,
                                      border_color="#f1c40f")
        self.card_conf.pack(fill="x", pady=5)
        ctk.CTkLabel(self.card_conf, text="Przedział Ufności (95%)", font=("Arial", 12, "bold"),
                     text_color="#aaaaaa").pack(anchor="w", padx=10, pady=(5, 0))
        self.val_conf = ctk.CTkLabel(self.card_conf, text="+/- --.-- Erl", font=("Arial", 18, "bold"),
                                     text_color="#f1c40f")
        self.val_conf.pack(anchor="w", padx=10, pady=(0, 10))

        self.card_adph = ctk.CTkFrame(self.results_container, fg_color="#2b2b2b", corner_radius=10, border_width=1,
                                      border_color="#555555")
        self.card_adph.pack(fill="x", pady=5)
        ctk.CTkLabel(self.card_adph, text="ADPH (Śr. Max)", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(
            anchor="w", padx=10, pady=(5, 0))
        self.val_adph = ctk.CTkLabel(self.card_adph, text="--.-- Erl", font=("Arial", 20, "bold"), text_color="#dddddd")
        self.val_adph.pack(anchor="w", padx=10, pady=(0, 5))

        self.card_fdmh = ctk.CTkFrame(self.results_container, fg_color="#2b2b2b", corner_radius=10, border_width=1,
                                      border_color="#555555")
        self.card_fdmh.pack(fill="x", pady=5)
        ctk.CTkLabel(self.card_fdmh, text="FDMH (Zegarowa)", font=("Arial", 12, "bold"), text_color="#aaaaaa").pack(
            anchor="w", padx=10, pady=(5, 0))
        self.val_fdmh = ctk.CTkLabel(self.card_fdmh, text="--.-- Erl", font=("Arial", 20, "bold"), text_color="#dddddd")
        self.val_fdmh.pack(anchor="w", padx=10, pady=(0, 5))

        self.lbl_info = ctk.CTkLabel(self.left_frame, text="Brak danych.", font=("Arial", 11), text_color="gray")
        self.lbl_info.grid(row=10, column=0, pady=5)

        self.btn_clean = ctk.CTkButton(self.left_frame, text="WYCZYŚĆ DANE", command=self.akcja_clean,
                                       fg_color="#c0392b", hover_color="#a93226")
        self.btn_clean.grid(row=11, column=0, padx=20, pady=(10, 30), sticky="ew")

        self.right_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#2b2b2b")
        self.right_frame.grid(row=0, column=1, sticky="nswe")

        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI', 'DejaVu Sans']

        self.fig = plt.Figure(figsize=(8, 8), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#212121')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#555555')
        self.ax.spines['left'].set_color('#555555')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True, padx=20, pady=20)

        toolbar = NavigationToolbar2Tk(self.canvas, self.right_frame)
        toolbar.config(background='#2b2b2b')
        toolbar._message_label.config(background='#2b2b2b', foreground='white')
        for button in toolbar.winfo_children():
            button.config(background='#2b2b2b')
        toolbar.update()

        self.reset_wykresu()

    def otworz_pdf(self):
        plik = resource_path("dokumentacja.pdf")
        if not os.path.exists(plik):
            messagebox.showerror("Błąd", f"Nie znaleziono pliku dokumentacji!\nSzukano: {plik}")
            return
        try:
            # macOS Support
            if sys.platform == 'win32':
                os.startfile(plik)
            elif sys.platform == 'darwin':
                subprocess.call(('open', plik))
            else:
                subprocess.call(('xdg-open', plik))
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się otworzyć pliku: {e}")

    def otworz_pomoc(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Instrukcja Obsługi")
        help_window.geometry("600x600")
        help_window.attributes("-topmost", True)
        ctk.CTkLabel(help_window, text="Instrukcja Obsługi", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        txt = ctk.CTkTextbox(help_window, width=550, height=500, font=ctk.CTkFont(size=14))
        txt.pack(padx=20, pady=10)
        content = """1. Wybierz folder z plikami CSV.
2. Program automatycznie wykryje format i separator.
3. Wykres po prawej pokaże profil ruchu.
4. Karty po lewej pokażą obliczone TCBH, ADPH i FDMH.
5. Możesz zawęzić analizę do konkretnych godzin (OD-DO)."""
        txt.insert("0.0", content)
        txt.configure(state="disabled")

    def reset_wykresu(self):
        self.ax.clear()
        self.ax.text(0.5, 0.5, "Gotowy do pracy.\nWgraj dane.",
                     ha='center', va='center', color='#666666', fontsize=18, fontweight='bold')
        self.ax.set_axis_off()
        self.canvas.draw()
        self.val_tcbh.configure(text="--.-- Erl")
        self.time_tcbh.configure(text="Czas: --:-- - --:--")
        self.val_conf.configure(text="+/- --.-- Erl")
        self.val_adph.configure(text="--.-- Erl")
        self.val_fdmh.configure(text="--.-- Erl")
        self.lbl_info.configure(text="Brak danych.")

    def rysuj_wykres_glowny(self, start_h, end_h):
        self.ax.clear()
        self.ax.set_axis_on()
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#555555')
        self.ax.spines['left'].set_color('#555555')
        self.ax.tick_params(axis='both', colors='#cccccc', labelsize=10)

        for df in self.engine.wszystkie_df:
            self.ax.plot(df['minuta'], df['ruch_erl'], color='#aaaaaa', alpha=0.15, linewidth=0.8)

        if self.engine.wszystkie_df:
            macierz = np.array([df['ruch_erl'].values for df in self.engine.wszystkie_df])
            srednia = macierz.mean(axis=0)
            self.ax.plot(range(1, 1441), srednia, color='#00e5ff', linewidth=2.5, label='Średni Profil')

            start = self.engine.tcbh_start_index
            self.ax.axvspan(start, start + 60, color='#ff0055', alpha=0.2, label='TCBH (1h)')

            if start_h > 0 or end_h < 24:
                idx_start, idx_end = int(start_h * 60), int(end_h * 60)
                self.ax.axvline(idx_start, color='yellow', linestyle='--', alpha=0.5)
                self.ax.axvline(idx_end, color='yellow', linestyle='--', alpha=0.5)

        self.ax.set_title("Profil Ruchu (Aggregate Traffic Profile)", color="white", fontsize=14, pad=20,
                          fontweight='bold')
        self.ax.set_xlabel("Godzina doby", color="#aaaaaa", fontsize=11)
        self.ax.set_ylabel("Natężenie [Erl]", color="#aaaaaa", fontsize=11)

        self.ax.xaxis.set_major_locator(ticker.MultipleLocator(120))
        self.ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{int(x / 60):02d}:00'))
        self.ax.grid(True, linestyle=':', alpha=0.4, color='#666666', zorder=0)
        self.ax.legend(fontsize=10, facecolor='#212121', edgecolor='#212121', labelcolor='white', frameon=False)
        self.canvas.draw()

    def aktualizuj_wyniki(self):
        try:
            s = float(self.combo_start.get())
            e = float(self.combo_end.get())
        except ValueError:
            s, e = 0, 24
        dane = self.engine.oblicz_gnr(start_h=s, end_h=e)
        if dane:
            self.val_tcbh.configure(text=f"{dane['tcbh_val']:.2f} Erl")
            self.time_tcbh.configure(text=f"Czas: {dane['tcbh_time']}")
            err = dane['error_margin']
            err_percent = (err / dane['tcbh_val']) * 100 if dane['tcbh_val'] > 0 else 0
            col = "#2fa34e" if err_percent < 5 else "#f1c40f" if err_percent < 15 else "#c0392b"
            self.val_conf.configure(text=f"+/- {err:.2f} Erl ({err_percent:.1f}%)", text_color=col)
            self.card_conf.configure(border_color=col)
            self.val_adph.configure(text=f"{dane['adph_val']:.2f} Erl")
            self.val_fdmh.configure(text=f"{dane['fdmh_val']:.2f} Erl")
            self.lbl_info.configure(text=f"Przeanalizowano {dane['dni']} dni. Zakres: {int(s)}:00 - {int(e)}:00")
            self.rysuj_wykres_glowny(s, e)

    def akcja_tryb_auto(self):
        path_czas = resource_path("czas_obslugi.txt")
        path_int = resource_path("intensywnosc_wywolan.txt")
        if not os.path.exists(path_czas):
            return messagebox.showerror("Błąd", f"Nie znaleziono pliku: {path_czas}")
        ok, msg = self.engine.wczytaj_baze_i_symuluj(path_czas, path_int)
        if ok: self.aktualizuj_wyniki()

    def akcja_tryb_folder(self):
        folder = filedialog.askdirectory(title="Wybierz folder z danymi")
        if not folder: return
        ok, msg = self.engine.wczytaj_folder_csv(folder)
        if ok:
            self.aktualizuj_wyniki()
        else:
            messagebox.showerror("Błąd", msg)

    def akcja_clean(self):
        self.engine.wyczysc_dane()
        self.reset_wykresu()


if __name__ == "__main__":
    app = TrafficApp()
    app.mainloop()