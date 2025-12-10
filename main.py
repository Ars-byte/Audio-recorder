import tkinter as tk
from tkinter import messagebox
import pyaudio
import wave
import threading
import time
import os

COLORS = {
    "BASE": "#1e1e2e",
    "CRUST": "#11111b",
    "TEXT": "#cdd6f4",
    "GREEN": "#a6e3a1",
    "YELLOW": "#f9e2af",
    "LAVENDER": "#b1b7fa",
    "RED": "#f38ba8"
}

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
OUTPUT_DIR = "grabaciones"

class AudioRecorderApp:
    def __init__(self, master):
        self.master = master
        master.title("Audio recorder - by arsbyte")
        master.config(bg=COLORS["BASE"])
        master.resizable(False, False)

        self.is_recording = False
        self.is_paused = False
        self.p = pyaudio.PyAudio()
        self.frames = []
        self.stream = None
        self.recording_thread = None
        self.timer_thread = None
        self.seconds = 0
        
        self.check_output_directory()
        
        main_frame = tk.Frame(master, padx=20, pady=20, bg=COLORS["CRUST"])
        main_frame.pack(padx=10, pady=10)

        self.timer_label = tk.Label(
            main_frame,
            text="00:00:00",
            font=("Hack", 32, "bold"),
            fg=COLORS["TEXT"],
            bg=COLORS["CRUST"]
        )
        self.timer_label.pack(pady=15)

        button_frame = tk.Frame(main_frame, bg=COLORS["CRUST"])
        button_frame.pack(pady=10)

        self.record_button = tk.Button(
            button_frame, 
            text="Grabar", 
            command=self.toggle_record,
            bg=COLORS["GREEN"], 
            fg=COLORS["CRUST"],
            activebackground=COLORS["GREEN"],
            activeforeground=COLORS["CRUST"],
            font=("Hack", 12, "bold"),
            relief=tk.FLAT,
            width=10
        )
        self.record_button.pack(side=tk.LEFT, padx=5)

        self.pause_button = tk.Button(
            button_frame, 
            text="Pausar", 
            command=self.pause_recording,
            bg=COLORS["YELLOW"], 
            fg=COLORS["CRUST"],
            activebackground=COLORS["YELLOW"],
            activeforeground=COLORS["CRUST"],
            font=("Hack", 12, "bold"),
            relief=tk.FLAT,
            state=tk.DISABLED,
            width=10
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(
            button_frame, 
            text="Guardar", 
            command=self.stop_and_save,
            bg=COLORS["LAVENDER"], 
            fg=COLORS["CRUST"],
            activebackground=COLORS["LAVENDER"],
            activeforeground=COLORS["CRUST"],
            font=("Hack", 12, "bold"),
            relief=tk.FLAT,
            state=tk.DISABLED,
            width=10
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
    def check_output_directory(self):
        if not os.path.exists(OUTPUT_DIR):
            try:
                os.makedirs(OUTPUT_DIR)
            except OSError as e:
                messagebox.showerror("Error de Carpeta", f"No se pudo crear la carpeta '{OUTPUT_DIR}': {e}")
                self.master.destroy()

    def update_timer(self):
        if self.is_recording and not self.is_paused:
            self.seconds += 1
            hours = self.seconds // 3600
            minutes = (self.seconds % 3600) // 60
            seconds = self.seconds % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.config(text=time_str, fg=COLORS["RED"])
            
        self.timer_thread = self.master.after(1000, self.update_timer)

    def record_audio(self):
        self.stream = self.p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)
        
        while self.is_recording:
            if not self.is_paused:
                try:
                    data = self.stream.read(CHUNK, exception_on_overflow=False)
                    self.frames.append(data)
                except IOError as e:
                    print(f"Advertencia: Desbordamiento de buffer: {e}")
                    pass
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def toggle_record(self):
        if not self.is_recording:
            self.is_recording = True
            self.is_paused = False
            self.frames = []
            self.seconds = 0
            
            self.recording_thread = threading.Thread(target=self.record_audio)
            self.recording_thread.start()
            self.update_timer()
            
            self.record_button.config(text="Detener", bg=COLORS["RED"], activebackground=COLORS["RED"])
            self.pause_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.DISABLED)
            
        else:
            self.is_recording = False
            self.is_paused = False
            
            if self.recording_thread and self.recording_thread.is_alive():
                 self.recording_thread.join() 

            if self.timer_thread:
                self.master.after_cancel(self.timer_thread)
            
            self.record_button.config(text="Grabar", bg=COLORS["GREEN"], activebackground=COLORS["GREEN"])
            self.pause_button.config(text="Pausar", state=tk.DISABLED)
            self.timer_label.config(fg=COLORS["TEXT"])
            
            if self.frames:
                self.save_button.config(state=tk.NORMAL)

    def pause_recording(self):
        if self.is_recording:
            if not self.is_paused:
                self.is_paused = True
                self.pause_button.config(text="Reanudar", bg=COLORS["YELLOW"])
                self.timer_label.config(fg=COLORS["YELLOW"])
            else:
                self.is_paused = False
                self.pause_button.config(text="Pausar", bg=COLORS["YELLOW"])
                self.timer_label.config(fg=COLORS["RED"])
                
    def stop_and_save(self):
        if self.is_recording:
            self.toggle_record()

        if self.frames:
            filename = os.path.join(OUTPUT_DIR, f"grabacion_{time.strftime('%Y%m%d_%H%M%S')}.wav")
            
            try:
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(self.p.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(self.frames))
                
                messagebox.showinfo("Guardado Exitoso", f"La grabación se ha guardado en:\n{filename}")
                
                self.frames = []
                self.seconds = 0
                self.timer_label.config(text="00:00:00", fg=COLORS["TEXT"])
                self.save_button.config(state=tk.DISABLED)
                
            except Exception as e:
                messagebox.showerror("Error al Guardar", f"Ocurrió un error al guardar el archivo: {e}")
        else:
            messagebox.showwarning("Advertencia", "No hay audio grabado para guardar.")

    def on_closing(self):
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
             self.recording_thread.join(timeout=1)
        self.p.terminate()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorderApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
