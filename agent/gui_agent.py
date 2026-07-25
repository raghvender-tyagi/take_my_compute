import os
import time
import json
import platform
import logging
import threading
import requests
import psutil
import customtkinter as ctk

# Configure logging
logger = logging.getLogger("gui_agent")
logger.setLevel(logging.INFO)

class TextHandler(logging.Handler):
    """Custom logging handler to redirect logs to CustomTkinter TextBox."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", msg + "\n")
            self.text_widget.configure(state="disabled")
            self.text_widget.yview("end")
        # Ensure thread safety by using Tkinter's after method
        self.text_widget.after(0, append)

class ProviderAgentApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Settings
        self.title("TakeMyCompute - Provider Control Panel")
        self.geometry("850x550")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # State Variables
        self.is_sharing = False
        self.agent_thread = None

        # Load environment defaults
        self.default_url = os.getenv("BACKEND_URL", "http://localhost:8000/api/providers/heartbeat/")
        self.default_id = os.getenv("PROVIDER_ID", f"provider-{platform.node().lower()[:8]}")
        self.default_token = os.getenv("PROVIDER_TOKEN", "")

        self.setup_ui()
        self.setup_logging()

    def setup_ui(self):
        # Configure Grid Layout (1 row, 2 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=2)  # Left panel
        self.grid_columnconfigure(1, weight=3)  # Right panel

        # ================= LEFT PANEL (Controls & Settings) =================
        self.left_frame = ctk.CTkFrame(self, corner_radius=12)
        self.left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)

        # Title Label
        self.title_lbl = ctk.CTkLabel(
            self.left_frame, text="TakeMyCompute", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_lbl.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        # Subtitle
        self.subtitle_lbl = ctk.CTkLabel(
            self.left_frame, text="Rent out your CPU/RAM securely", 
            font=ctk.CTkFont(size=13, slant="italic"), text_color="gray"
        )
        self.subtitle_lbl.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Input: Backend URL
        self.url_lbl = ctk.CTkLabel(self.left_frame, text="Backend Server URL", font=ctk.CTkFont(size=12))
        self.url_lbl.grid(row=2, column=0, padx=20, pady=(10, 2), sticky="w")
        self.url_entry = ctk.CTkEntry(self.left_frame, placeholder_text="http://localhost:8000/api/providers/heartbeat/")
        self.url_entry.insert(0, self.default_url)
        self.url_entry.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Input: Provider ID
        self.id_lbl = ctk.CTkLabel(self.left_frame, text="Unique Provider ID", font=ctk.CTkFont(size=12))
        self.id_lbl.grid(row=4, column=0, padx=20, pady=(10, 2), sticky="w")
        self.id_entry = ctk.CTkEntry(self.left_frame, placeholder_text="e.g. my-desktop-machine")
        self.id_entry.insert(0, self.default_id)
        self.id_entry.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Input: Provider JWT Token
        self.token_lbl = ctk.CTkLabel(self.left_frame, text="Authentication Token (JWT)", font=ctk.CTkFont(size=12))
        self.token_lbl.grid(row=6, column=0, padx=20, pady=(10, 2), sticky="w")
        self.token_entry = ctk.CTkEntry(self.left_frame, placeholder_text="Paste token from dashboard...", show="*")
        self.token_entry.insert(0, self.default_token)
        self.token_entry.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Toggle Button
        self.action_btn = ctk.CTkButton(
            self.left_frame, text="Start Sharing", 
            fg_color="#1f85de", hover_color="#1867ab",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.toggle_sharing
        )
        self.action_btn.grid(row=8, column=0, padx=20, pady=10, sticky="ew")

        # Status Indicator
        self.status_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.status_frame.grid(row=9, column=0, padx=20, pady=10, sticky="ew")
        
        self.status_lbl = ctk.CTkLabel(self.status_frame, text="Status: ", font=ctk.CTkFont(size=13))
        self.status_lbl.pack(side="left")
        self.status_val = ctk.CTkLabel(
            self.status_frame, text="INACTIVE", 
            text_color="#e63946", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.status_val.pack(side="left")

        # ================= RIGHT PANEL (Monitoring & Logs) =================
        self.right_frame = ctk.CTkFrame(self, corner_radius=12)
        self.right_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(2, weight=1)  # Allow log box to expand

        # CPU Usage Monitor
        self.cpu_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.cpu_frame.grid(row=0, column=0, padx=20, pady=15, sticky="ew")
        self.cpu_lbl = ctk.CTkLabel(self.cpu_frame, text="CPU Usage: 0%", font=ctk.CTkFont(size=13, weight="bold"))
        self.cpu_lbl.pack(anchor="w")
        self.cpu_progress = ctk.CTkProgressBar(self.cpu_frame)
        self.cpu_progress.set(0)
        self.cpu_progress.pack(fill="x", pady=5)

        # RAM Usage Monitor
        self.ram_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.ram_frame.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.ram_lbl = ctk.CTkLabel(self.ram_frame, text="RAM Usage: 0% (0.0GB / 0.0GB)", font=ctk.CTkFont(size=13, weight="bold"))
        self.ram_lbl.pack(anchor="w")
        self.ram_progress = ctk.CTkProgressBar(self.ram_frame)
        self.ram_progress.set(0)
        self.ram_progress.pack(fill="x", pady=5)

        # Scrollable Logs Console
        self.log_lbl = ctk.CTkLabel(self.right_frame, text="Agent logs:", font=ctk.CTkFont(size=12))
        self.log_lbl.grid(row=2, column=0, padx=20, pady=(5, 0), sticky="w")
        
        self.log_box = ctk.CTkTextbox(self.right_frame, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_box.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.log_box.configure(state="disabled")

    def setup_logging(self):
        # Configure logging format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        
        # Link our custom handler to the textbox
        text_handler = TextHandler(self.log_box)
        text_handler.setFormatter(formatter)
        
        # Also print to python standard output
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(text_handler)
        logger.addHandler(console_handler)
        logger.info("Control Panel initialized. Ready to share.")

    def toggle_sharing(self):
        if not self.is_sharing:
            # Start Sharing Action
            self.is_sharing = True
            self.action_btn.configure(text="Stop Sharing", fg_color="#e63946", hover_color="#c92a3a")
            self.status_val.configure(text="SHARING ACTIVE", text_color="#2b9348")
            
            # Disable configuration fields during execution
            self.url_entry.configure(state="disabled")
            self.id_entry.configure(state="disabled")
            self.token_entry.configure(state="disabled")

            # Start background thread for agent statistics gathering
            self.agent_thread = threading.Thread(target=self.run_agent_loop, daemon=True)
            self.agent_thread.start()
            logger.info("Sharing started. System metrics reporting active.")
        else:
            # Stop Sharing Action
            self.is_sharing = False
            self.action_btn.configure(text="Start Sharing", fg_color="#1f85de", hover_color="#1867ab")
            self.status_val.configure(text="INACTIVE", text_color="#e63946")
            
            # Re-enable inputs
            self.url_entry.configure(state="normal")
            self.id_entry.configure(state="normal")
            self.token_entry.configure(state="normal")
            logger.info("Sharing stopped. Agent set to standby mode.")

    def get_system_stats(self):
        """Gathers system resources stats."""
        try:
            stats = {
                "provider_id": self.id_entry.get().strip(),
                "timestamp": time.time(),
                "cpu_usage_percent": psutil.cpu_percent(interval=None), # non-blocking
                "memory_total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                "memory_used_gb": round(psutil.virtual_memory().used / (1024 ** 3), 2),
                "memory_usage_percent": psutil.virtual_memory().percent,
                "disk_total_gb": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
                "disk_used_gb": round(psutil.disk_usage('/').used / (1024 ** 3), 2),
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "os_name": platform.system(),
                "os_version": platform.release(),
            }
            return stats
        except Exception as e:
            logger.error(f"Error gathering system stats: {e}")
            return None

    def run_agent_loop(self):
        backend_url = self.url_entry.get().strip()
        token = self.token_entry.get().strip()

        # Update stats loop
        while self.is_sharing:
            stats = self.get_system_stats()
            if stats:
                # Update UI Progress Bars & Labels in thread-safe manner
                cpu_percent = stats['cpu_usage_percent']
                ram_percent = stats['memory_usage_percent']
                ram_used = stats['memory_used_gb']
                ram_total = stats['memory_total_gb']
                
                self.cpu_lbl.configure(text=f"CPU Usage: {cpu_percent}%")
                self.cpu_progress.set(cpu_percent / 100.0)
                
                self.ram_lbl.configure(text=f"RAM Usage: {ram_percent}% ({ram_used}GB / {ram_total}GB)")
                self.ram_progress.set(ram_percent / 100.0)

                # Send data to Backend API
                try:
                    headers = {'Content-Type': 'application/json'}
                    if token:
                        headers['Authorization'] = f'Bearer {token}'
                        
                    response = requests.post(backend_url, data=json.dumps(stats), headers=headers, timeout=4)
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Heartbeat OK -> CPU: {cpu_percent}%, RAM: {ram_percent}%")
                    else:
                        logger.warning(f"Heartbeat failed. HTTP Status: {response.status_code}")
                except Exception as e:
                    logger.error(f"Failed to connect to backend: {e}")

            # Sleep for 10 seconds, but check periodically if sharing was stopped
            for _ in range(20):
                if not self.is_sharing:
                    break
                time.sleep(0.5)

if __name__ == "__main__":
    app = ProviderAgentApp()
    app.mainloop()
