import os
import re
import sys
import builtins
import threading
import queue
import importlib
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import PatchApk as apk_mod # Your module

# Constants and Globals
APK_PATCH_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "Apk_Patch")
search_mode = False
file_types = ['.SMALI', '.XML']
file_type_vars = {}

# Helper Functions
def get_selected_file_types():
    return [ft.lower() for ft, var in file_type_vars.items() if var.get()]


# ---------- UI helpers ----------
class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, s):
        if not s:
            return
        if search_mode:
            # Remove 'Progress: xx%' patterns
            s = re.sub(r'\r?Progress: \d+%', '', s)
            s = re.sub(r'\r?\[[#\s]{0,50}\]\s+\d+%', '', s)

            # If the result is just whitespace after removal, skip logging entirely
            #if not s.strip():
            #    return
        def append():
            try:
                self.text_widget.insert(tk.END, s)
                self.text_widget.see(tk.END)
            except Exception:
                pass
        # Ensure GUI update runs in main thread
        self.text_widget.after(0, append)

    def flush(self):
        pass

class InputRequester:

    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        self.root.after(100, self._process)

    def request(self, prompt=""):
        event = threading.Event()
        container = {"response": None}
        self.q.put((prompt, event, container))
        event.wait()
        return container["response"] if container["response"] is not None else ""

    def _process(self):
        try:
            while not self.q.empty():
                prompt, event, container = self.q.get_nowait()
                # Heuristic for yes/no prompts
                lp = prompt.lower()
                if "(y/n" in lp or "y/n" in lp or "yes/no" in lp or lp.strip().endswith("(y/n)"):
                    ok = messagebox.askyesno("Question", prompt, parent=self.root)
                    container["response"] = "y" if ok else "n"
                else:
                    resp = simpledialog.askstring("Input required", prompt, parent=self.root)
                    container["response"] = resp if resp is not None else ""
                event.set()
        except Exception as e:
            print("[INPUT ERROR]", e)
        finally:
            self.root.after(100, self._process)

# ---------- Main GUI ----------
def create_gui():
    root = tk.Tk()
    root.title("APKPatch GUI")
    root.geometry("900x650")
    root.minsize(900, 600)

    # Set ttk style theme (use 'clam', 'alt', 'default', 'classic', etc.)
    style = ttk.Style(root)
    style.theme_use('clam')  # you can try 'default', 'alt', 'clam' etc.

    # Fonts
    title_font = ("Segoe UI", 16, "bold")
    label_font = ("Segoe UI", 10)
    button_font = ("Segoe UI", 10)

     # -------- Main container frame with horizontal layout --------
    main_frame = ttk.Frame(root, padding=(10, 0, 10, 0))
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Title label top center
    title_label = ttk.Label(main_frame, text="APK Patch Toolkit", font=title_font)
    title_label.pack(side=tk.TOP, pady=(0, 0))

    # Create horizontal paned window to split left and right
    paned = ttk.Panedwindow(main_frame, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True)

    # -------- Left frame: buttons + file type checkboxes --------
    left_frame = ttk.Frame(paned, width=300)
    paned.add(left_frame, weight=1)

    # -------- Right frame: log + progress bar --------
    right_frame = ttk.Frame(paned)
    paned.add(right_frame, weight=3)

     # File type selection label
    ttk.Label(left_frame, text="Select File Types For Search:", font=label_font ).pack(anchor='w', pady=(0, 2))


    # File type checkboxes container with padding
    file_types_container = ttk.Frame(left_frame)
    file_types_container.pack(fill=tk.BOTH, pady=(0, 0))

    # Create checkboxes dynamically
    for i, ft in enumerate(file_types):
        var = tk.BooleanVar()
        tk.Checkbutton(file_types_container, text=ft, variable=var).grid(row=0, column=i, padx=5, pady=2)
        file_type_vars[ft] = var
    
    # Buttons container with spacing and uniform button size
    buttons_container = ttk.Frame(left_frame)
    buttons_container.pack(fill=tk.BOTH, expand=True)

      # Example of button styling and uniform size:
    btn_style = ttk.Style()
    btn_style.configure('TButton', font=button_font, padding=6)

    def update_progress(p):
        progress_var.set(p)
        progress_label.config(text=f"{p}%")
        root.update_idletasks()

    # Log area with horizontal scrollbar and no wrapping
    log_frame = ttk.Frame(right_frame)
    log_frame.pack(fill=tk.BOTH, expand=True)

    # Text widget without wrap
    log_box = tk.Text(log_frame, wrap=tk.NONE, height=30)
    log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Vertical scrollbar (optional, if you want custom)
    v_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_box.yview)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    log_box.configure(yscrollcommand=v_scroll.set)
    
    # Horizontal scrollbar
    h_scroll = ttk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=log_box.xview)
    h_scroll.pack(fill=tk.X)
    log_box.configure(xscrollcommand=h_scroll.set)

    #progress bar with label
    progress_frame = ttk.Frame(right_frame)
    progress_frame.pack(fill=tk.X, pady=10)

    progress_label = ttk.Label(progress_frame, text="Progress:")
    progress_label.pack(side=tk.LEFT, padx=(0, 5))

    progress_var = tk.IntVar()
    progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=100, mode="determinate", variable=progress_var, maximum=100, style="green.Horizontal.TProgressbar")
    progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
    style.configure("green.Horizontal.TProgressbar", foreground='green', background='green')

    progress_label = ttk.Label(progress_bar, text="0%", font=("Arial", 7))
    progress_label.pack()

    # Utility buttons at bottom
    util_frame = ttk.Frame(root, padding=(0, 0, 0, 10))
    util_frame.pack(fill=tk.X)

    clear_log_btn = ttk.Button(util_frame, text="Clear Log", width=10, command=lambda: log_box.delete("1.0", tk.END))
    clear_log_btn.pack(side=tk.LEFT, padx=(10,0))

    def reload_backend():
        try:
            importlib.reload(apk_mod)
            messagebox.showinfo("Reloaded", "APKPATCH module reloaded.",  parent=root)
        except Exception as e:
            messagebox.showerror("Error", f"Reload failed: {e}")

    reload_btn = ttk.Button(util_frame, text="Reload Backend", width=15, command=reload_backend)
    reload_btn.pack(side=tk.LEFT, padx=(5,0))

    # instantiate helpers
    input_requester = InputRequester(root)

    def run_in_thread(func, *args, **kwargs):
        def target():
            import time
            done = threading.Event()

            def animate_progress():
                current = 0
                while current < 87 and not done.is_set():
                    if search_mode:  # Stop animation immediately if search_mode becomes True
                        break
                    current += 1
                    root.after(0, update_progress, current)
                    time.sleep(0.5)

            progress_thread = None
            if not search_mode:
                progress_thread = threading.Thread(target=animate_progress)
                progress_thread.start()

            old_stdout = sys.stdout
            old_stderr = sys.stderr
            old_input = builtins.input
            sys.stdout = TextRedirector(log_box)
            sys.stderr = TextRedirector(log_box)
            builtins.input = lambda prompt="": input_requester.request(prompt)

            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"[ERROR] {e}")
            finally:
                done.set()
                if progress_thread is not None:
                    progress_thread.join()
                root.after(0, update_progress, 100)
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                builtins.input = old_input
        t = threading.Thread(target=target, daemon=True)
        t.start()


    def set_search_mode(value: bool):
        global search_mode
        search_mode = value

    def search_with_flag():
        try:
            set_search_mode(True)
            apk_mod.search(
                get_selected_file_types(),
                progress_callback=lambda p: root.after(0, update_progress, p)
            )
        finally:
            set_search_mode(False)

    def download_with_flag():
        try:
            set_search_mode(True)
            apk_mod.check_dependency(
                progress_callback=lambda p: root.after(0, update_progress, p)
            )
        finally:
            set_search_mode(False)

    # Buttons mapped to your existing functions
    btn_cfg = [
        ("Check & Install Dependencies", download_with_flag),
        ("Select/Import APK to Patch", apk_mod.select_Apk),
        ("Unpack APK", apk_mod.unpack_Apk),
        ("Pack APK", apk_mod.pack_Apk),
        ("Sign APK", apk_mod.sign_Apk),
        ("Install Signed APK via ADB", apk_mod.install_Apk),
        ("Clear old APK files", apk_mod.clear_old_apk_files),
        ("Search in base folder", search_with_flag),
        ("Delete/Replace keywords", apk_mod.delete_or_replace_keywords),
        ("Revert modifications", apk_mod.revert_modifications),
    ]

    for i, (label, func) in enumerate(btn_cfg):
        b = ttk.Button(buttons_container, text=label, width=28, style='TButton', command=lambda f=func: run_in_thread(f))
        b.pack(fill=tk.X, pady=4)
    
    # initial message
    log_box.insert(tk.END, "APK Patch GUI started, press a button to run an action.\n")

    root.mainloop()

if __name__ == "__main__":
    create_gui()
