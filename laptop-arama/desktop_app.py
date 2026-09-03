"""Selanik laptop aramasını Telegram olmadan, basit bir masaüstü pencereden
kullanmak için. Aynı arama kodunu (search_laptops_greece.py) kullanıyor,
sadece arayüz farklı. Python'la birlikte gelen tkinter'ı kullanıyor - ekstra
kütüphane kurmaya gerek yok.

Çalıştırmak için: python desktop_app.py
"""
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

from currency import eur_to_try_rate
from manis import rastgele_mani
from search_laptops_greece import search_by_cpu, search_by_gpu

MAX_RESULTS = 5


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Selanik Laptop Arama")
        self.geometry("700x600")

        top = tk.Frame(self)
        top.pack(pady=10)

        self.cpu_button = tk.Button(
            top, text="Ryzen AI 9 365+ ara", width=25, command=lambda: self.run_search("cpu")
        )
        self.cpu_button.grid(row=0, column=0, padx=5)

        self.gpu_button = tk.Button(
            top, text="RTX 5070 Ti/5080/5090 ara", width=25, command=lambda: self.run_search("gpu")
        )
        self.gpu_button.grid(row=0, column=1, padx=5)

        self.status_label = tk.Label(self, text="Hazır.")
        self.status_label.pack(pady=(0, 5))

        self.output = scrolledtext.ScrolledText(self, wrap=tk.WORD, font=("Segoe UI", 10))
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.output.config(state=tk.DISABLED)

    def set_status(self, text: str) -> None:
        self.status_label.config(text=text)

    def write_output(self, text: str) -> None:
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.config(state=tk.DISABLED)

    def run_search(self, kind: str) -> None:
        self.cpu_button.config(state=tk.DISABLED)
        self.gpu_button.config(state=tk.DISABLED)
        self.set_status("Aranıyor, birkaç dakika sürebilir...")
        self.write_output("")
        threading.Thread(target=self._search_worker, args=(kind,), daemon=True).start()

    def _search_worker(self, kind: str) -> None:
        try:
            if kind == "cpu":
                laptops = search_by_cpu()
                baslik = "Ryzen AI 9 365+ işlemcili laptoplar (Selanik)"
            else:
                laptops = search_by_gpu()
                baslik = "RTX 5070 Ti/5080/5090 laptoplar (Selanik)"

            rate = eur_to_try_rate()
            text = self._format_results(laptops, rate, baslik)
            self.after(0, lambda: self._on_done(text))
        except Exception as e:
            self.after(0, lambda: self._on_done(f"Bir hata oldu: {e}"))

    def _format_results(self, laptops: list[dict], rate: float, baslik: str) -> str:
        lines = [rastgele_mani(), "", baslik, ""]
        if not laptops:
            lines.append("Şu an bu kritere uyan bir laptop bulunamadı.")
            return "\n".join(lines)

        for laptop in laptops[:MAX_RESULTS]:
            try_equivalent = laptop["price_eur"] * rate
            lines.append(laptop["name"])
            lines.append(f"{laptop['price_eur']:,.2f} EUR  (~{try_equivalent:,.2f} TL, güncel kur: {rate:.2f})")
            lines.append(laptop["url"])
            lines.append("")

        if len(laptops) > MAX_RESULTS:
            lines.append(f"(Toplam {len(laptops)} sonuç bulundu, en ucuz {MAX_RESULTS} tanesi gösterildi.)")

        return "\n".join(lines)

    def _on_done(self, text: str) -> None:
        self.write_output(text)
        self.set_status("Hazır.")
        self.cpu_button.config(state=tk.NORMAL)
        self.gpu_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    App().mainloop()
