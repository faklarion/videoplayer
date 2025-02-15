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

# Dictionary untuk menyimpan data rentang waktu
range_data = []

# Fungsi untuk memuat jadwal dari file JSON
def load_schedule():
    global schedule
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as file:
            schedule = json.load(file)
        update_schedule_table()

# Fungsi untuk menyimpan jadwal ke file JSON
def save_schedule():
    with open(SCHEDULE_FILE, "w") as file:
        json.dump(schedule, file, indent=4)

# Fungsi untuk memperbarui tabel jadwal
def update_schedule_table():
    tree_schedule.delete(*tree_schedule.get_children())  # Hapus semua data di tabel
    for day, schedules in schedule.items():
        for item in schedules:
            tree_schedule.insert("", "end", values=(day, item["video"], item["time"]))

# Fungsi untuk memperbarui tabel rentang waktu
def update_range_table():
    tree_range.delete(*tree_range.get_children())  # Hapus semua data di tabel
    for item in range_data:
        tree_range.insert("", "end", values=(item["video"], item["interval"]))

# Fungsi untuk memutar video di layar tertentu
def play_video(video_path, screen_offset_x=0):
    if not video_path:
        label_status.config(text="Tidak ada video yang dipilih.")
        return
    
    media = instance.media_new(video_path)
    player.set_media(media)
    player.set_fullscreen(True)  # Setel fullscreen
    
    # Atur posisi window ke layar kedua
    if screen_offset_x > 0:
        player.set_xwindow(screen_offset_x)  # Pindahkan ke layar kedua
    
    player.play()

    while True:
        state = player.get_state()
        if state in [vlc.State.Ended, vlc.State.Stopped, vlc.State.Error]:
            break
        time.sleep(1)

    player.stop()
    label_status.config(text="Video selesai diputar!")

# Fungsi untuk memutar video dalam rentang waktu tertentu dengan interval
def play_video_with_interval(video_path, interval_minutes, screen_offset_x=0):
    if not video_path:
        label_status.config(text="Tidak ada video yang dipilih.")
        return
    
    while True:  # Loop tanpa batas waktu (tanpa durasi)
        media = instance.media_new(video_path)
        player.set_media(media)
        player.set_fullscreen(True)  # Setel fullscreen
        
        # Atur posisi window ke layar kedua
        if screen_offset_x > 0:
            player.set_xwindow(screen_offset_x)  # Pindahkan ke layar kedua
        
        player.play()

        # Tunggu sampai video selesai diputar
        while player.get_state() not in [vlc.State.Ended, vlc.State.Stopped, vlc.State.Error]:
            time.sleep(1)
        
        player.stop()  # Hentikan pemutaran video

        # Tunggu interval sebelum memutar lagi
        time.sleep(interval_minutes * 60)

# Fungsi untuk memilih dan memutar video secara manual
def play_manual_video():
    video_path = entry_manual_video.get()
    if not video_path:
        messagebox.showerror("Error", "Harap pilih video terlebih dahulu!")
        return
    
    screen_choice = screen_var_manual.get()
    screen_offset_x = 1920 if screen_choice == "Screen 2" else 0  # Atur koordinat layar
    
    label_status.config(text=f"Memutar video: {video_path} di {screen_choice}")
    threading.Thread(target=play_video, args=(video_path, screen_offset_x), daemon=True).start()

# Fungsi untuk memilih video manual
def choose_manual_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
    if file_path:
        entry_manual_video.delete(0, tk.END)
        entry_manual_video.insert(0, file_path)

# Fungsi untuk memilih video rentang waktu
def choose_range_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
    if file_path:
        entry_range_video.delete(0, tk.END)
        entry_range_video.insert(0, file_path)

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
    update_schedule_table()
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
                screen_choice = screen_var_schedule.get()
                screen_offset_x = 1920 if screen_choice == "Screen 2" else 0  # Atur koordinat layar
                label_status.config(text=f"Memutar video untuk {today_id} pada {schedule_time}...")
                play_video(video_path, screen_offset_x)

        time.sleep(30)  # Cek setiap 30 detik

# Fungsi untuk memilih video terjadwal
def choose_scheduled_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
    if file_path:
        entry_scheduled_video.delete(0, tk.END)
        entry_scheduled_video.insert(0, file_path)

# Fungsi untuk menghapus jadwal yang dipilih
def delete_schedule():
    selected_item = tree_schedule.selection()
    if not selected_item:
        messagebox.showerror("Error", "Pilih jadwal yang ingin dihapus!")
        return

    for item in selected_item:
        values = tree_schedule.item(item, "values")
        day, video, time = values
        schedule[day] = [s for s in schedule[day] if not (s["video"] == video and s["time"] == time)]

    save_schedule()
    update_schedule_table()
    messagebox.showinfo("Sukses", "Jadwal berhasil dihapus!")

# Fungsi untuk memulai pemutaran video dalam rentang waktu dengan interval
def start_range_playback():
    video_path = entry_range_video.get()
    if not video_path:
        messagebox.showerror("Error", "Harap pilih video terlebih dahulu!")
        return
    
    try:
        interval_minutes = int(entry_range_interval.get())  # Ambil interval dari input
    except ValueError:
        messagebox.showerror("Error", "Interval harus berupa angka!")
        return
    
    screen_choice = screen_var_range.get()
    screen_offset_x = 1920 if screen_choice == "Screen 2" else 0  # Atur koordinat layar
    
    range_data.append({"video": video_path, "interval": interval_minutes})
    update_range_table()
    label_status.config(text=f"Memutar video setiap {interval_minutes} menit di {screen_choice}...")
    threading.Thread(target=play_video_with_interval, args=(video_path, interval_minutes, screen_offset_x), daemon=True).start()

# Fungsi untuk menghapus jadwal interval
def delete_interval():
    selected_item = tree_range.selection()
    if not selected_item:
        messagebox.showerror("Error", "Pilih jadwal interval yang ingin dihapus!")
        return

    for item in selected_item:
        values = tree_range.item(item, "values")
        video_path = values[0]  # Ambil path video dari nilai
        interval = int(values[1])  # Ambil interval dari nilai

        # Hapus entri dari range_data
        range_data[:] = [data for data in range_data if not (data["video"] == video_path and data["interval"] == interval)]

    update_range_table()  # Perbarui tabel
    messagebox.showinfo("Sukses", "Jadwal interval berhasil dihapus!")

# GUI Aplikasi
app = tk.Tk()
app.title("Penjadwal Multi-Video & Multi-Waktu")
app.geometry("700x650")

# Notebook (Tab)
notebook = ttk.Notebook(app)
notebook.pack(fill="both", expand=True)

# === Tab Rentang Waktu ===
tab_range = ttk.Frame(notebook)
notebook.add(tab_range, text="Rentang Waktu")

# Input video untuk rentang waktu
label_range_video = tk.Label(tab_range, text="Pilih Video:")
label_range_video.pack()
entry_range_video = tk.Entry(tab_range, width=50)
entry_range_video.pack()
button_choose_range = tk.Button(tab_range, text="Pilih Video", command=choose_range_video)
button_choose_range.pack()

# Input interval waktu
label_range_interval = tk.Label(tab_range, text="Interval (menit):")
label_range_interval.pack()
entry_range_interval = tk.Entry(tab_range, width=10)
entry_range_interval.pack()

# Pilihan layar untuk rentang waktu
label_range_screen = tk.Label(tab_range, text="Pilih Layar:")
label_range_screen.pack()
screen_var_range = tk.StringVar(value="Screen 1")
screen_menu_range = tk.OptionMenu(tab_range, screen_var_range, "Screen 1", "Screen 2")
screen_menu_range.pack()

# Tombol mulai rentang waktu
button_start_range = tk.Button(tab_range, text="Mulai Pemutaran", command=start_range_playback)
button_start_range.pack(pady=5)

# Tabel data rentang waktu
columns_range = ("Video", "Interval (menit)")
tree_range = ttk.Treeview(tab_range, columns=columns_range, show="headings")
for col in columns_range:
    tree_range.heading(col, text=col)
    tree_range.column(col, width=150)
tree_range.pack(pady=10)

# Tombol hapus jadwal interval
button_delete_interval = tk.Button(tab_range, text="Hapus Jadwal Interval", command=delete_interval)
button_delete_interval.pack(pady=5)

# === Tab Manual ===
tab_manual = ttk.Frame(notebook)
notebook.add(tab_manual, text="Manual")

# Input video manual
label_manual = tk.Label(tab_manual, text="Putar Video Manual", font=("Arial", 12, "bold"))
label_manual.pack(pady=5)

entry_manual_video = tk.Entry(tab_manual, width=50)
entry_manual_video.pack()
button_choose_manual = tk.Button(tab_manual, text="Pilih Video", command=choose_manual_video)
button_choose_manual.pack()

# Pilihan layar untuk pemutaran manual
label_manual_screen = tk.Label(tab_manual, text="Pilih Layar:")
label_manual_screen.pack()
screen_var_manual = tk.StringVar(value="Screen 1")
screen_menu_manual = tk.OptionMenu(tab_manual, screen_var_manual, "Screen 1", "Screen 2")
screen_menu_manual.pack()

button_play_manual = tk.Button(tab_manual, text="Putar Video Manual", command=play_manual_video)
button_play_manual.pack()

# === Tab Jadwal Perhari ===
tab_schedule = ttk.Frame(notebook)
notebook.add(tab_schedule, text="Jadwal Perhari")

# Form untuk penjadwalan video
label_schedule = tk.Label(tab_schedule, text="Tambah Jadwal Video", font=("Arial", 12, "bold"))
label_schedule.pack(pady=5)

# Pilihan hari
label_day = tk.Label(tab_schedule, text="Pilih Hari:")
label_day.pack()
day_var = tk.StringVar(value="Senin")
days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
day_menu = tk.OptionMenu(tab_schedule, day_var, *days)
day_menu.pack()

# Input video untuk jadwal
label_video = tk.Label(tab_schedule, text="Pilih Video (Jadwal):")
label_video.pack()
entry_scheduled_video = tk.Entry(tab_schedule, width=50)
entry_scheduled_video.pack()
button_choose_scheduled = tk.Button(tab_schedule, text="Pilih Video", command=choose_scheduled_video)
button_choose_scheduled.pack()

# Input waktu
label_time = tk.Label(tab_schedule, text="Atur Waktu (HH:MM):")
label_time.pack()
entry_time = tk.Entry(tab_schedule, width=10)
entry_time.pack()

# Pilihan layar untuk penjadwalan
label_schedule_screen = tk.Label(tab_schedule, text="Pilih Layar:")
label_schedule_screen.pack()
screen_var_schedule = tk.StringVar(value="Screen 1")
screen_menu_schedule = tk.OptionMenu(tab_schedule, screen_var_schedule, "Screen 1", "Screen 2")
screen_menu_schedule.pack()

# Tombol simpan jadwal
button_save = tk.Button(tab_schedule, text="Tambahkan Jadwal", command=set_schedule)
button_save.pack(pady=5)

# Tombol untuk memulai penjadwalan
button_start_schedule = tk.Button(tab_schedule, text="Mulai Penjadwalan", command=start_scheduler)
button_start_schedule.pack(pady=10)

# Tabel jadwal
columns_schedule = ("Hari", "Video", "Waktu")
tree_schedule = ttk.Treeview(tab_schedule, columns=columns_schedule, show="headings")
for col in columns_schedule:
    tree_schedule.heading(col, text=col)
    tree_schedule.column(col, width=150)
tree_schedule.pack(pady=10)

# Tombol hapus jadwal
button_delete = tk.Button(tab_schedule, text="Hapus Jadwal", command=delete_schedule)
button_delete.pack(pady=5)

# === Label status untuk menampilkan info ===
label_status = tk.Label(app, text="", fg="blue", font=("Arial", 10))
label_status.pack(pady=5)

# Load jadwal saat aplikasi dijalankan
load_schedule()

# Jalankan penjadwalan secara otomatis saat aplikasi dibuka
start_scheduler()

# Jalankan aplikasi
app.mainloop()