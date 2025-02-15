import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import datetime
import time
import threading
import vlc
import json
import os

# File untuk menyimpan jadwal
SCHEDULE_FILE = "schedule.json"

# Instance VLC
instance = vlc.Instance()
player = instance.media_player_new()

# Dictionary untuk menyimpan jadwal video per hari
schedule = {day: [] for day in ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]}

# Fungsi untuk memuat jadwal dari file JSON
def load_schedule():
    global schedule
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as file:
            schedule = json.load(file)
        update_table()

# Fungsi untuk menyimpan jadwal ke file JSON
def save_schedule():
    with open(SCHEDULE_FILE, "w") as file:
        json.dump(schedule, file, indent=4)

# Fungsi untuk memperbarui tabel dengan data jadwal terbaru
def update_table():
    tree.delete(*tree.get_children())  # Hapus semua data di tabel
    for day, schedules in schedule.items():
        for item in schedules:
            tree.insert("", "end", values=(day, item["video"], item["time"]))

# Fungsi untuk memutar video
def play_video(video_path):
    if not video_path:
        label_status.config(text="Tidak ada video yang dipilih.")
        return
    
    media = instance.media_new(video_path)
    player.set_media(media)
    
    # Set fullscreen sebelum mulai memutar video
    player.set_fullscreen(True)
    
    player.play()

    while True:
        state = player.get_state()
        if state in [vlc.State.Ended, vlc.State.Stopped, vlc.State.Error]:
            break
        time.sleep(1)

    player.stop()
    label_status.config(text="Video selesai diputar!")

# Fungsi untuk memilih dan memutar video secara manual
def play_manual_video():
    video_path = entry_manual_video.get()
    if not video_path:
        messagebox.showerror("Error", "Harap pilih video terlebih dahulu!")
        return
    
    label_status.config(text=f"Memutar video: {video_path}")
    threading.Thread(target=play_video, args=(video_path,), daemon=True).start()

# Fungsi untuk memilih video manual
def choose_manual_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
    if file_path:
        entry_manual_video.delete(0, tk.END)
        entry_manual_video.insert(0, file_path)

# Fungsi untuk menyimpan jadwal video
def set_schedule():
    day = day_var.get()
    video_path = entry_scheduled_video.get()
    schedule_time = entry_time.get()

    if not video_path or not schedule_time:
        messagebox.showerror("Error", "Harap pilih video dan atur waktu!")
        return

    try:
        datetime.datetime.strptime(schedule_time, "%H:%M")
    except ValueError:
        messagebox.showerror("Error", "Format waktu tidak valid! Gunakan format HH:MM.")
        return

    schedule[day].append({"video": video_path, "time": schedule_time})
    save_schedule()
    update_table()
    label_status.config(text=f"Jadwal {day} pada {schedule_time} disimpan!")
    messagebox.showinfo("Sukses", f"Jadwal baru untuk {day} telah disimpan!")

# Fungsi untuk menjalankan penjadwalan
def start_scheduler():
    threading.Thread(target=run_scheduler, daemon=True).start()
    messagebox.showinfo("Penjadwalan", "Penjadwalan telah dimulai!")

# Fungsi untuk mengecek jadwal setiap menit
def run_scheduler():
    while True:
        now = datetime.datetime.now()
        today = now.strftime("%A")  
        hari_id = {
            "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
            "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
        }
        today_id = hari_id[today]  

        for item in schedule[today_id]:
            video_path = item["video"]
            schedule_time = item["time"]
            schedule_hour, schedule_minute = map(int, schedule_time.split(":"))

            if now.hour == schedule_hour and now.minute == schedule_minute:
                label_status.config(text=f"Memutar video untuk {today_id} pada {schedule_time}...")
                play_video(video_path)

        time.sleep(30)  # Cek setiap 30 detik

# Fungsi untuk memilih video terjadwal
def choose_scheduled_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
    if file_path:
        entry_scheduled_video.delete(0, tk.END)
        entry_scheduled_video.insert(0, file_path)

# Fungsi untuk menghapus jadwal yang dipilih
def delete_schedule():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Pilih jadwal yang ingin dihapus!")
        return

    for item in selected_item:
        values = tree.item(item, "values")
        day, video, time = values
        schedule[day] = [s for s in schedule[day] if not (s["video"] == video and s["time"] == time)]

    save_schedule()
    update_table()
    messagebox.showinfo("Sukses", "Jadwal berhasil dihapus!")

# GUI Aplikasi
app = tk.Tk()
app.title("Penjadwal Multi-Video & Multi-Waktu")
app.geometry("600x600")

# === Form untuk penjadwalan video ===
label_schedule = tk.Label(app, text="Tambah Jadwal Video", font=("Arial", 12, "bold"))
label_schedule.pack(pady=5)

# Pilihan hari
label_day = tk.Label(app, text="Pilih Hari:")
label_day.pack()
day_var = tk.StringVar(value="Senin")
days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
day_menu = tk.OptionMenu(app, day_var, *days)
day_menu.pack()

# Input video untuk jadwal
label_video = tk.Label(app, text="Pilih Video (Jadwal):")
label_video.pack()
entry_scheduled_video = tk.Entry(app, width=50)
entry_scheduled_video.pack()
button_choose_scheduled = tk.Button(app, text="Pilih Video", command=choose_scheduled_video)
button_choose_scheduled.pack()

# Input waktu
label_time = tk.Label(app, text="Atur Waktu (HH:MM):")
label_time.pack()
entry_time = tk.Entry(app, width=10)
entry_time.pack()

# Tombol simpan jadwal
button_save = tk.Button(app, text="Tambahkan Jadwal", command=set_schedule)
button_save.pack(pady=5)

# Tombol untuk memulai penjadwalan
button_start_schedule = tk.Button(app, text="Mulai Penjadwalan", command=start_scheduler)
button_start_schedule.pack(pady=10)

# === Tabel jadwal ===
columns = ("Hari", "Video", "Waktu")
tree = ttk.Treeview(app, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=150)
tree.pack()

# Tombol hapus jadwal
button_delete = tk.Button(app, text="Hapus Jadwal", command=delete_schedule)
button_delete.pack(pady=5)

# === Form untuk memutar video manual ===
label_manual = tk.Label(app, text="Putar Video Manual", font=("Arial", 12, "bold"))
label_manual.pack(pady=5)

entry_manual_video = tk.Entry(app, width=50)
entry_manual_video.pack()
button_choose_manual = tk.Button(app, text="Pilih Video", command=choose_manual_video)
button_choose_manual.pack()

button_play_manual = tk.Button(app, text="Putar Video Manual", command=play_manual_video)
button_play_manual.pack()

# === Label status untuk menampilkan info ===
label_status = tk.Label(app, text="", fg="blue", font=("Arial", 10))
label_status.pack(pady=5)

# Load jadwal saat aplikasi dijalankan
load_schedule()

# Jalankan aplikasi
app.mainloop()
