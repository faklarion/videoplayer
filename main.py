import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import vlc
from screeninfo import get_monitors
import pygetwindow as gw
import time
from datetime import datetime, timedelta
import json
import os

class VideoPlayerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Video Player")
        self.master.geometry("800x800")

        # Variabel untuk membedakan jenis pemutaran
        self.is_auto_play = False  # True jika sedang dalam mode Auto Play
        self.is_regular_play = False  # True jika sedang dalam mode Play Video

        # Tab Control
        self.tab_control = ttk.Notebook(master)

        # Tab 1 - Play Video
        self.tab_play = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_play, text="Play Video")

        # Tab 2 - Auto Play Video
        self.tab_auto_play = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_auto_play, text="Auto Play")

        # Tab 3 - Schedule Video
        self.tab_schedule = ttk.Frame(self.tab_control)
        self.tab_control.add(self.tab_schedule, text="Schedule Video")

        self.tab_control.pack(expand=1, fill="both")

        # Tab 1: Play Video
        self.setup_play_tab()

        # Tab 2: Auto Play Video
        self.setup_auto_play_tab()

        # Tab 3: Schedule Video
        self.setup_schedule_tab()

        # Initialize VLC player
        self.player = None
        self.video_path = ""
        self.auto_play_active = False
        self.auto_play_schedule_list = []  # Separate list for auto play
        self.schedule_list = []  # Separate list for scheduled play

        # Load existing schedules from JSON and reschedule them
        self.load_schedules()

        # Get monitor list
        self.monitors = get_monitors()
        self.populate_monitor_dropdown()

    def play_next_auto_play_video(self):
        """Play the next video in auto play mode"""
        if self.auto_play_active:
            # Play the video
            self.start_vlc_player(self.monitor_dropdown_auto.current(), self.volume_var_auto.get())

            # Start monitoring the video status
            self.master.after(1000, self.check_video_status)

    def setup_play_tab(self):
        """Setup UI for the play video tab"""
        # Tombol "Select Video" untuk tab Play Video
        tk.Button(self.tab_play, text="Select Video", command=lambda: self.select_video("play")).pack(pady=10)

        # Label to display the selected video path
        self.video_path_label_play = tk.Label(self.tab_play, text="No video selected", fg="blue")
        self.video_path_label_play.pack(pady=5)

        tk.Label(self.tab_play, text="Select Monitor:").pack(pady=5)
        self.monitor_var_play = tk.StringVar()
        self.monitor_dropdown_play = ttk.Combobox(self.tab_play, textvariable=self.monitor_var_play)
        self.monitor_dropdown_play.pack(pady=5)

        # Volume Slider
        tk.Label(self.tab_play, text="Volume:").pack(pady=5)
        self.volume_var_play = tk.IntVar(value=50)  # Default volume is 50%
        self.volume_slider_play = tk.Scale(self.tab_play, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume_var_play)
        self.volume_slider_play.pack(pady=5)
        self.volume_slider_play.bind("<ButtonRelease-1>", lambda event: self.set_volume(self.volume_var_play.get()))

        self.play_button = tk.Button(self.tab_play, text="Play Video", command=self.play_video, state=tk.DISABLED)
        self.play_button.pack(pady=10)

    def setup_auto_play_tab(self):
        """Setup UI for the auto play video tab"""
        # Tombol "Select Video" untuk tab Auto Play
        tk.Button(self.tab_auto_play, text="Select Video", command=lambda: self.select_video("auto_play")).pack(pady=10)

        # Label to display the selected video path
        self.video_path_label_auto = tk.Label(self.tab_auto_play, text="No video selected", fg="blue")
        self.video_path_label_auto.pack(pady=5)

        tk.Label(self.tab_auto_play, text="Select Monitor:").pack(pady=5)
        self.monitor_var_auto = tk.StringVar()
        self.monitor_dropdown_auto = ttk.Combobox(self.tab_auto_play, textvariable=self.monitor_var_auto)
        self.monitor_dropdown_auto.pack(pady=5)

        # Volume Slider
        tk.Label(self.tab_auto_play, text="Volume:").pack(pady=5)
        self.volume_var_auto = tk.IntVar(value=50)  # Default volume is 50%
        self.volume_slider_auto = tk.Scale(self.tab_auto_play, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume_var_auto)
        self.volume_slider_auto.pack(pady=5)
        self.volume_slider_auto.bind("<ButtonRelease-1>", lambda event: self.set_volume(self.volume_var_auto.get()))

        tk.Label(self.tab_auto_play, text="Interval (minutes):").pack(pady=5)
        self.interval_var = tk.IntVar(value=10)
        self.interval_entry = tk.Entry(self.tab_auto_play, textvariable=self.interval_var, width=5)
        self.interval_entry.pack(pady=5)

        self.start_timer_button = tk.Button(self.tab_auto_play, text="Start Timer", command=self.start_auto_play, state=tk.DISABLED)
        self.start_timer_button.pack(pady=5)

        self.stop_timer_button = tk.Button(self.tab_auto_play, text="Stop Timer", command=self.stop_auto_play, state=tk.DISABLED)
        self.stop_timer_button.pack(pady=5)

        # Table for auto play schedules
        self.auto_play_tree = ttk.Treeview(self.tab_auto_play, columns=("No", "Time"), show="headings")
        self.auto_play_tree.heading("No", text="No")
        self.auto_play_tree.heading("Time", text="Scheduled Time")
        self.auto_play_tree.column("No", width=50)
        self.auto_play_tree.column("Time", width=200)
        self.auto_play_tree.pack(pady=10)

        # Add buttons for CRUD operations in auto play
        self.auto_play_update_button = tk.Button(self.tab_auto_play, text="Update Schedule", command=self.update_auto_play_schedule, state=tk.DISABLED)
        self.auto_play_update_button.pack(pady=5)

        self.auto_play_delete_button = tk.Button(self.tab_auto_play, text="Delete Schedule", command=self.delete_auto_play_schedule, state=tk.DISABLED)
        self.auto_play_delete_button.pack(pady=5)

        self.auto_play_tree.bind("<<TreeviewSelect>>", self.on_auto_play_tree_select)

    def setup_schedule_tab(self):
        """Setup UI for the scheduled video tab"""
        # Tombol "Select Video" untuk tab Schedule Video
        tk.Button(self.tab_schedule, text="Select Video", command=lambda: self.select_video("schedule")).pack(pady=10)

        # Label to display the selected video path
        self.video_path_label_schedule = tk.Label(self.tab_schedule, text="No video selected", fg="blue")
        self.video_path_label_schedule.pack(pady=5)

        tk.Label(self.tab_schedule, text="Select Monitor:").pack(pady=5)
        self.monitor_var_schedule = tk.StringVar()
        self.monitor_dropdown_schedule = ttk.Combobox(self.tab_schedule, textvariable=self.monitor_var_schedule)
        self.monitor_dropdown_schedule.pack(pady=5)

        # Volume Slider
        tk.Label(self.tab_schedule, text="Volume:").pack(pady=5)
        self.volume_var_schedule = tk.IntVar(value=50)  # Default volume is 50%
        self.volume_slider_schedule = tk.Scale(self.tab_schedule, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume_var_schedule)
        self.volume_slider_schedule.pack(pady=5)
        self.volume_slider_schedule.bind("<ButtonRelease-1>", lambda event: self.set_volume(self.volume_var_schedule.get()))

        tk.Label(self.tab_schedule, text="Select Day:").pack(pady=5)
        self.day_var = tk.StringVar()
        self.day_dropdown = ttk.Combobox(self.tab_schedule, textvariable=self.day_var, 
                                          values=["Setiap Hari", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.day_dropdown.pack(pady=5)

        tk.Label(self.tab_schedule, text="Select Time (HH:MM):").pack(pady=5)
        self.time_var = tk.StringVar()
        self.time_entry = tk.Entry(self.tab_schedule, textvariable=self.time_var, width=10)
        self.time_entry.pack(pady=5)

        self.schedule_button = tk.Button(self.tab_schedule, text="Schedule Video", command=self.schedule_video, state=tk.DISABLED)
        self.schedule_button.pack(pady=10)

        # Table for scheduled video plays
        self.schedule_tree = ttk.Treeview(self.tab_schedule, columns=("No", "Time", "Video Path"), show="headings")
        self.schedule_tree.heading("No", text="No")
        self.schedule_tree.heading("Time", text="Scheduled Time")
        self.schedule_tree.heading("Video Path", text="Video Path")
        self.schedule_tree.column("No", width=50)
        self.schedule_tree.column("Time", width=200)
        self.schedule_tree.column("Video Path", width=300)
        self.schedule_tree.pack(pady=10)

        # Add buttons for CRUD operations in scheduled video
        self.schedule_update_button = tk.Button(self.tab_schedule, text="Update Schedule", command=self.update_schedule, state=tk.DISABLED)
        self.schedule_update_button.pack(pady=5)

        self.schedule_delete_button = tk.Button(self.tab_schedule, text="Delete Schedule", command=self.delete_schedule, state=tk.DISABLED)
        self.schedule_delete_button.pack(pady=5)

        # Tombol "Mulai Penjadwalan"
        self.start_scheduling_button = tk.Button(self.tab_schedule, text="Mulai Penjadwalan", command=self.start_scheduling)
        self.start_scheduling_button.pack(pady=10)

        self.schedule_tree.bind("<<TreeviewSelect>>", self.on_schedule_tree_select)

    def populate_monitor_dropdown(self):
        """Fill the monitor dropdown with available monitors"""
        monitor_names = [f"Monitor {i + 1} ({m.width}x{m.height})" for i, m in enumerate(self.monitors)]
        self.monitor_dropdown_play['values'] = monitor_names
        self.monitor_dropdown_auto['values'] = monitor_names
        self.monitor_dropdown_schedule['values'] = monitor_names
        if monitor_names:
            self.monitor_var_play.set(monitor_names[0])  # Set first monitor as default
            self.monitor_var_auto.set(monitor_names[0])  # Set first monitor as default
            self.monitor_var_schedule.set(monitor_names[0])  # Set first monitor as default

    def select_video(self, feature):
        # Hentikan pemutaran otomatis jika aktif
        if self.auto_play_active:
            self.stop_auto_play()

        video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi;*.mkv")])
        if video_path and os.path.isfile(video_path):  # Ensure the selected path is a valid file
            if feature == "play":
                self.video_path = video_path
                self.play_button.config(state=tk.NORMAL)
                self.video_path_label_play.config(text=self.video_path)
            elif feature == "auto_play":
                self.auto_play_video_path = video_path
                self.start_timer_button.config(state=tk.NORMAL)
                self.video_path_label_auto.config(text=self.auto_play_video_path)
            elif feature == "schedule":
                self.schedule_video_path = video_path
                self.schedule_button.config(state=tk.NORMAL)
                self.video_path_label_schedule.config(text=self.schedule_video_path)
        else:
            messagebox.showerror("Invalid Selection", "Please select a valid video file.")
    
    def play_video(self):
        if self.video_path and os.path.isfile(self.video_path):  # Check if the path is valid
            try:
                # Set status pemutaran
                self.is_regular_play = True
                self.is_auto_play = False

                # Play the video
                self.start_vlc_player(self.monitor_dropdown_play.current(), self.volume_var_play.get())
                self.player.set_fullscreen(True)

                # Start monitoring the video status
                self.master.after(1000, self.check_video_status)
            except Exception as e:
                messagebox.showerror("Playback Error", f"An error occurred while trying to play the video: {str(e)}")
        else:
            messagebox.showerror("Invalid Video", "Please select a valid video file.")

    def start_vlc_player(self, monitor_index, volume):
        if self.player is not None:
            self.player.stop()

        # Use the correct video path based on the feature
        video_path = self.video_path if hasattr(self, "video_path") else None
        if hasattr(self, "auto_play_video_path") and self.auto_play_active:
            video_path = self.auto_play_video_path
        elif hasattr(self, "schedule_video_path"):
            video_path = self.schedule_video_path

        if not video_path or not os.path.isfile(video_path):
            messagebox.showerror("Invalid Video", "No valid video file selected.")
            return

        # Initialize the VLC player
        self.player = vlc.MediaPlayer(video_path)
        self.player.play()

        # Wait for the VLC window to appear
        time.sleep(1)

        # Move to the selected monitor
        if monitor_index < len(self.monitors):
            monitor = self.monitors[monitor_index]

            # Wait for VLC to appear
            time.sleep(1)

            # Find the VLC window and move it to the selected monitor
            windows = gw.getWindowsWithTitle("VLC")
            if windows:
                window = windows[0]
                window.moveTo(monitor.x, monitor.y)
                window.maximize()

                # Set the VLC player to fullscreen
                self.player.set_fullscreen(True)

        # Set the volume
        self.player.audio_set_volume(volume)

        # Check the video status periodically
        self.check_video_status()

    def check_video_status(self):
        """Check if the video is still playing, if not, handle accordingly"""
        if self.player and not self.player.is_playing():
            # Video has finished, release the player
            self.player.stop()
            self.player.release()
            self.player = None
            print("Video finished, closing player.")

            # Jika dalam mode Auto Play, jadwalkan pemutaran berikutnya
            if self.is_auto_play:
                interval_millis = self.interval_var.get() * 60 * 1000  # Convert minutes to milliseconds
                next_play_time = datetime.now() + timedelta(milliseconds=interval_millis)
                self.auto_play_schedule_list.append(next_play_time.strftime("%H:%M:%S"))
                self.update_auto_play_schedule_table()

                print(f"Next video will play at {next_play_time.strftime('%H:%M:%S')}")
                self.auto_play_timer = self.master.after(interval_millis, self.play_next_auto_play_video)

            # Jika dalam mode Play Video, tidak perlu menjadwalkan apa pun
            elif self.is_regular_play:
                self.is_regular_play = False  # Reset status pemutaran biasa

        else:
            # Video is still playing, check again after 1 second
            self.master.after(1000, self.check_video_status)

    def set_volume(self, volume):
        """Set the volume of the VLC player"""
        if self.player:
            self.player.audio_set_volume(volume)

    def start_auto_play(self):
        """Start automatic video playback with a specific time interval"""
        # Hentikan timer sebelumnya jika ada
        if hasattr(self, "auto_play_timer"):
            self.master.after_cancel(self.auto_play_timer)

        # Set status pemutaran
        self.is_auto_play = True
        self.is_regular_play = False

        self.auto_play_active = True
        self.stop_timer_button.config(state=tk.NORMAL)
        self.start_timer_button.config(state=tk.DISABLED)

        # Clear the schedule list and table
        self.auto_play_schedule_list.clear()
        self.update_auto_play_schedule_table()

        # Start the first video immediately
        self.play_next_auto_play_video()

    def schedule_next_auto_play(self, interval):
        """Schedule the next video playback for auto play and update the table"""
        if self.auto_play_active:
            next_play_time = datetime.now() + timedelta(minutes=self.interval_var.get())
            self.auto_play_schedule_list.append(next_play_time.strftime("%H:%M:%S"))
            self.update_auto_play_schedule_table()

            print(f"Next video will play at {next_play_time.strftime('%H:%M:%S')}")
            self.start_vlc_player(self.monitor_dropdown_auto.current(), self.volume_var_auto.get())
            self.master.after(interval, lambda: self.schedule_next_auto_play(interval))

    def stop_auto_play(self):
        """Stop automatic video playback"""
        self.auto_play_active = False
        self.is_auto_play = False  # Reset status Auto Play
        self.stop_timer_button.config(state=tk.DISABLED)
        self.start_timer_button.config(state=tk.NORMAL)

        # Stop the player if it's running
        if self.player:
            self.player.stop()
            self.player.release()
            self.player = None

        # Batalkan timer jika ada
        if hasattr(self, "auto_play_timer"):
            self.master.after_cancel(self.auto_play_timer)
            del self.auto_play_timer

        print("Auto Play stopped.")

    def update_auto_play_schedule_table(self):
        """Update the auto play schedule table with the latest data"""
        for item in self.auto_play_tree.get_children():
            self.auto_play_tree.delete(item)

        for i, time_str in enumerate(self.auto_play_schedule_list, start=1):
            self.auto_play_tree.insert("", "end", values=(i, time_str))

    def schedule_video(self):
        """Schedule video playback based on the selected day and time"""
        selected_day = self.day_var.get()
        selected_time = self.time_var.get()

        if selected_day and selected_time and hasattr(self, "schedule_video_path"):
            try:
                # Convert the selected time to a datetime object
                schedule_time = datetime.strptime(selected_time, "%H:%M").time()
                now = datetime.now()

                if selected_day == "Setiap Hari":
                    # Jika "Setiap Hari" dipilih, jadwalkan untuk hari ini dan setiap hari berikutnya
                    scheduled_datetime = datetime.combine(now.date(), schedule_time)

                    # Jika waktu jadwal sudah lewat, jadwalkan untuk besok
                    if scheduled_datetime < now:
                        scheduled_datetime += timedelta(days=1)

                    # Simpan jadwal dengan format khusus untuk "Setiap Hari"
                    schedule_entry = {
                        "day_time": "Setiap Hari, " + scheduled_datetime.strftime("%H:%M"),
                        "video_path": self.schedule_video_path
                    }
                    self.schedule_list.append(schedule_entry)
                    self.update_schedule_table()

                    # Simpan jadwal ke file JSON
                    self.save_schedules()

                    # Jadwalkan pemutaran video
                    delay = (scheduled_datetime - now).total_seconds() * 1000
                    self.master.after(int(delay), lambda: self.play_scheduled_video(self.schedule_video_path))

                else:
                    # Jika hari tertentu dipilih, gunakan logika sebelumnya
                    day_offset = (["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(selected_day) - now.weekday()) % 7
                    scheduled_datetime = datetime.combine(now.date() + timedelta(days=day_offset), schedule_time)

                    if scheduled_datetime < now:
                        scheduled_datetime += timedelta(weeks=1)  # Jika waktu jadwal sudah lewat, jadwalkan untuk minggu depan

                    # Simpan jadwal dengan format hari dan waktu
                    schedule_entry = {
                        "day_time": scheduled_datetime.strftime("%A, %H:%M"),
                        "video_path": self.schedule_video_path
                    }
                    self.schedule_list.append(schedule_entry)
                    self.update_schedule_table()

                    # Simpan jadwal ke file JSON
                    self.save_schedules()

                    # Jadwalkan pemutaran video
                    delay = (scheduled_datetime - now).total_seconds() * 1000
                    self.master.after(int(delay), lambda: self.play_scheduled_video(self.schedule_video_path))

            except ValueError:
                print("Invalid time format. Use HH:MM.")
        else:
            messagebox.showerror("Error", "Please select a video and provide a valid day and time.")

    def save_schedules(self):
        """Save schedules to a JSON file"""
        with open("schedules.json", "w") as f:
            json.dump(self.schedule_list, f)

    def load_schedules(self):
        """Load schedules from a JSON file and reschedule them"""
        if os.path.exists("schedules.json"):
            with open("schedules.json", "r") as f:
                self.schedule_list = json.load(f)
                self.update_schedule_table()

                # Reschedule the videos
                now = datetime.now()
                for schedule_entry in self.schedule_list:
                    try:
                        day_time = schedule_entry["day_time"]
                        if day_time.startswith("Setiap Hari"):
                            # Handle "Setiap Hari" schedule
                            scheduled_time = datetime.strptime(day_time.split(", ")[1], "%H:%M").time()
                            scheduled_datetime = datetime.combine(now.date(), scheduled_time)

                            # Jika waktu jadwal sudah lewat, jadwalkan untuk besok
                            if scheduled_datetime < now:
                                scheduled_datetime += timedelta(days=1)

                            delay = (scheduled_datetime - now).total_seconds() * 1000
                            self.master.after(int(delay), lambda video_path=schedule_entry["video_path"]: self.play_scheduled_video(video_path))
                        else:
                            # Handle specific day schedule
                            scheduled_day, scheduled_time = day_time.split(", ")
                            scheduled_datetime = datetime.strptime(f"{scheduled_day} {scheduled_time}", "%A %H:%M")
                            scheduled_datetime = scheduled_datetime.replace(year=now.year, month=now.month, day=now.day)

                            # Jika waktu jadwal sudah lewat, jadwalkan untuk minggu depan
                            if scheduled_datetime < now:
                                scheduled_datetime += timedelta(weeks=1)

                            delay = (scheduled_datetime - now).total_seconds() * 1000
                            self.master.after(int(delay), lambda video_path=schedule_entry["video_path"]: self.play_scheduled_video(video_path))

                    except ValueError:
                        print(f"Invalid schedule format: {schedule_entry}")

    def play_scheduled_video(self, video_path):
        """Play a scheduled video"""
        if os.path.isfile(video_path):
            self.schedule_video_path = video_path  # Set the video path
            self.start_vlc_player(self.monitor_dropdown_schedule.current(), self.volume_var_schedule.get())
        else:
            messagebox.showerror("Error", f"Video file not found: {video_path}")

    def update_schedule_table(self):
        """Update the schedule table with the latest data"""
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)

        for i, schedule_entry in enumerate(self.schedule_list, start=1):
            self.schedule_tree.insert("", "end", values=(i, schedule_entry["day_time"], schedule_entry["video_path"]))

    def on_auto_play_tree_select(self, event):
        """Handle selection in the auto play schedule table"""
        selected_item = self.auto_play_tree.selection()
        if selected_item:
            self.auto_play_update_button.config(state=tk.NORMAL)
            self.auto_play_delete_button.config(state=tk.NORMAL)
        else:
            self.auto_play_update_button.config(state=tk.DISABLED)
            self.auto_play_delete_button.config(state=tk.DISABLED)

    def update_auto_play_schedule(self):
        """Update the selected auto play schedule"""
        selected_item = self.auto_play_tree.selection()
        if selected_item:
            index = self.auto_play_tree.index(selected_item[0])
            # Here you can implement the logic to update the selected schedule
            # For example, you can ask for new time input and update the list
            # This is a placeholder for the actual update logic
            new_time = self.interval_var.get()  # Example: just using the interval as new time
            self.auto_play_schedule_list[index] = new_time
            self.update_auto_play_schedule_table()

    def delete_auto_play_schedule(self):
        """Delete the selected auto play schedule"""
        selected_item = self.auto_play_tree.selection()
        if selected_item:
            index = self.auto_play_tree.index(selected_item[0])
            del self.auto_play_schedule_list[index]
            self.update_auto_play_schedule_table()

    def on_schedule_tree_select(self, event):
        """Handle selection in the schedule table"""
        selected_item = self.schedule_tree.selection()
        if selected_item:
            self.schedule_update_button.config(state=tk.NORMAL)
            self.schedule_delete_button.config(state=tk.NORMAL)
        else:
            self.schedule_update_button.config(state=tk.DISABLED)
            self.schedule_delete_button.config(state=tk.DISABLED)

    def update_schedule(self):
        """Update the selected schedule"""
        selected_item = self.schedule_tree.selection()
        if selected_item:
            index = self.schedule_tree.index(selected_item[0])
            selected_day = self.day_var.get()
            selected_time = self.time_var.get()

            if selected_day and selected_time and hasattr(self, "schedule_video_path"):
                try:
                    # Convert the selected time to a datetime object
                    schedule_time = datetime.strptime(selected_time, "%H:%M").time()
                    now = datetime.now()
                    day_offset = (["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(selected_day) - now.weekday()) % 7
                    scheduled_datetime = datetime.combine(now.date() + timedelta(days=day_offset), schedule_time)

                    if scheduled_datetime < now:
                        scheduled_datetime += timedelta(weeks=1)  # If the time has passed, schedule for next week

                    # Update the schedule entry
                    self.schedule_list[index] = {
                        "day_time": scheduled_datetime.strftime("%A, %H:%M"),
                        "video_path": self.schedule_video_path
                    }
                    self.update_schedule_table()

                    # Save schedules to JSON file
                    self.save_schedules()

                except ValueError:
                    print("Invalid time format. Use HH:MM.")
            else:
                messagebox.showerror("Error", "Please select a video and provide a valid day and time.")

    def delete_schedule(self):
        """Delete the selected schedule"""
        selected_item = self.schedule_tree.selection()
        if selected_item:
            index = self.schedule_tree.index(selected_item[0])
            del self.schedule_list[index]
            self.update_schedule_table()

            # Save schedules to JSON file
            self.save_schedules()

    def start_scheduling(self):
        """Start processing all scheduled videos"""
        if not self.schedule_list:
            messagebox.showinfo("Info", "Tidak ada jadwal yang tersedia.")
            return

        now = datetime.now()
        for schedule_entry in self.schedule_list:
            try:
                day_time = schedule_entry["day_time"]
                if day_time.startswith("Setiap Hari"):
                    # Handle "Setiap Hari" schedule
                    scheduled_time = datetime.strptime(day_time.split(", ")[1], "%H:%M").time()
                    scheduled_datetime = datetime.combine(now.date(), scheduled_time)

                    # Jika waktu jadwal sudah lewat, jadwalkan untuk besok
                    if scheduled_datetime < now:
                        scheduled_datetime += timedelta(days=1)

                    delay = (scheduled_datetime - now).total_seconds() * 1000
                    self.master.after(int(delay), lambda video_path=schedule_entry["video_path"]: self.play_scheduled_video(video_path))
                else:
                    # Handle specific day schedule
                    scheduled_day, scheduled_time = day_time.split(", ")
                    scheduled_datetime = datetime.strptime(f"{scheduled_day} {scheduled_time}", "%A %H:%M")
                    scheduled_datetime = scheduled_datetime.replace(year=now.year, month=now.month, day=now.day)

                    # Jika waktu jadwal sudah lewat, jadwalkan untuk minggu depan
                    if scheduled_datetime < now:
                        scheduled_datetime += timedelta(weeks=1)

                    delay = (scheduled_datetime - now).total_seconds() * 1000
                    self.master.after(int(delay), lambda video_path=schedule_entry["video_path"]: self.play_scheduled_video(video_path))

            except ValueError:
                print(f"Invalid schedule format: {schedule_entry}")

        messagebox.showinfo("Info", "Penjadwalan video telah dimulai.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoPlayerApp(root)
    root.mainloop()