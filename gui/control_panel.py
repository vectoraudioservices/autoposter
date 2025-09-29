import os, subprocess, threading, time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYEXE = os.path.join(ROOT, "venv", "Scripts", "python.exe")

def run_cmd(cmd, cwd=ROOT):
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=True)
        return out.stdout.strip() + ("\n" + out.stderr.strip() if out.stderr else "")
    except Exception as e:
        return f"ERROR: {e}"

def start_all():
    bat = os.path.join(ROOT, "start_all.bat")
    if not os.path.exists(bat):
        messagebox.showerror("Missing", "start_all.bat not found")
        return
    subprocess.Popen(f'"{bat}"', cwd=ROOT, shell=True)

def stop_all():
    bat = os.path.join(ROOT, "stop_all.bat")
    if not os.path.exists(bat):
        messagebox.showerror("Missing", "stop_all.bat not found")
        return
    subprocess.Popen(f'"{bat}"', cwd=ROOT, shell=True)

def refresh_status(text_widget):
    out = run_cmd(f'"{PYEXE}" "{os.path.join(ROOT,"scripts","status.py")}"')
    text_widget.configure(state="normal")
    text_widget.delete("1.0", tk.END)
    text_widget.insert(tk.END, out if out else "(no output)")
    text_widget.configure(state="disabled")

def add_client():
    def go():
        name = ent_name.get().strip()
        hours = ent_hours.get().strip()
        quota = ent_quota.get().strip()
        if not name:
            messagebox.showwarning("Required", "Client name is required")
            return
        hours_parts = hours.split() if hours else []
        cmd = f'"{PYEXE}" "{os.path.join(ROOT,"scripts","add_client.py")}" "{name}"'
        if quota:
            cmd += f" --quota {quota}"
        if hours_parts:
            cmd += " --hours " + " ".join(hours_parts)
        out = run_cmd(cmd)
        messagebox.showinfo("Add Client", out)
        dlg.destroy()

    dlg = tk.Toplevel()
    dlg.title("Add Client")
    ttk.Label(dlg, text="Client name:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
    ent_name = ttk.Entry(dlg, width=30); ent_name.grid(row=0, column=1, padx=6, pady=6)
    ttk.Label(dlg, text="Hours (24h, space-separated):").grid(row=1, column=0, sticky="e", padx=6, pady=6)
    ent_hours = ttk.Entry(dlg, width=30); ent_hours.grid(row=1, column=1, padx=6, pady=6)
    ttk.Label(dlg, text="Daily quota:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
    ent_quota = ttk.Entry(dlg, width=10); ent_quota.insert(0,"1"); ent_quota.grid(row=2, column=1, sticky="w", padx=6, pady=6)
    btn = ttk.Button(dlg, text="Create", command=go); btn.grid(row=3, column=0, columnspan=2, pady=10)
    dlg.transient(); dlg.grab_set()

def post_now():
    # pick client by reading config/clients folder
    clients_dir = os.path.join(ROOT,"config","clients")
    clients = sorted([d for d in os.listdir(clients_dir) if os.path.isdir(os.path.join(clients_dir,d))]) if os.path.exists(clients_dir) else []
    if not clients:
        messagebox.showwarning("No Clients", "No clients found in config/clients")
        return
    def choose_file():
        path = filedialog.askopenfilename(title="Choose image/video to enqueue", initialdir=os.path.join(ROOT,"content"))
        if path:
            var_path.set(path)
    def go():
        client = cmb_client.get().strip()
        path = var_path.get().strip()
        if not client or not os.path.exists(path):
            messagebox.showwarning("Required", "Choose a client and a file")
            return
        # copy file into content/<client> so watcher enqueues it
        import shutil
        dest_dir = os.path.join(ROOT,"content",client)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, os.path.basename(path))
        try:
            shutil.copy2(path, dest)
            messagebox.showinfo("Post Now", f"Copied to {dest}\nWatcher will enqueue automatically.")
            dlg.destroy()
        except Exception as e:
            messagebox.showerror("Copy failed", str(e))

    dlg = tk.Toplevel()
    dlg.title("Post Now")
    ttk.Label(dlg, text="Client:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
    cmb_client = ttk.Combobox(dlg, values=clients, state="readonly", width=30)
    cmb_client.grid(row=0, column=1, padx=6, pady=6)
    var_path = tk.StringVar()
    ttk.Label(dlg, text="File:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
    ent_path = ttk.Entry(dlg, textvariable=var_path, width=40); ent_path.grid(row=1, column=1, padx=6, pady=6)
    ttk.Button(dlg, text="Browse...", command=choose_file).grid(row=1, column=2, padx=6, pady=6)
    ttk.Button(dlg, text="Enqueue", command=go).grid(row=2, column=0, columnspan=3, pady=10)
    dlg.transient(); dlg.grab_set()

def fast_forward():
    out = run_cmd(f'"{PYEXE}" "{os.path.join(ROOT,"scripts","queue_fast_forward.py")}" --seconds 5')
    messagebox.showinfo("Fast Forward", out or "(done)")

def auto_refresh(text_widget):
    while True:
        try:
            refresh_status(text_widget)
        except:
            pass
        time.sleep(5)

def main():
    root = tk.Tk()
    root.title("Autoposter Control Panel")
    root.geometry("780x540")

    frm = ttk.Frame(root, padding=10); frm.pack(fill="both", expand=True)

    row1 = ttk.Frame(frm); row1.pack(fill="x", pady=6)
    ttk.Button(row1, text="Start All", command=start_all).pack(side="left", padx=6)
    ttk.Button(row1, text="Stop All", command=stop_all).pack(side="left", padx=6)
    ttk.Button(row1, text="Add Client", command=add_client).pack(side="left", padx=6)
    ttk.Button(row1, text="Post Now", command=post_now).pack(side="left", padx=6)
    ttk.Button(row1, text="Fast Forward", command=fast_forward).pack(side="left", padx=6)

    ttk.Separator(frm).pack(fill="x", pady=6)

    ttk.Label(frm, text="Status:").pack(anchor="w")
    txt = tk.Text(frm, height=22, wrap="word")
    txt.configure(font=("Consolas", 10))
    txt.pack(fill="both", expand=True)
    txt.configure(state="disabled")

    threading.Thread(target=auto_refresh, args=(txt,), daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
