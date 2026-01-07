import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import time
import logging
import winsound
import json
import csv
import sys
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
import subprocess
import hashlib
import hmac
import winreg
import os
import uuid
import platform
import ntplib
from urllib.request import urlretrieve

# Set default theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- APP CONSTANTS ---
APP_VERSION = "1.5.0"
LICENSE_SERVER_URL = "https://www.recodestudio.it/app/modbus-server/license_server.php" 
VERSION_CHECK_URL = "https://www.recodestudio.it/app/modbus-server/version.json"

# --- LICENSING CONSTANTS ---
SALT_PART_A = b"ModbusPro"
SALT_PART_B = b"_SuperSecret_2025"
SECRET_SALT = SALT_PART_A + SALT_PART_B

REG_PATH = r"Software\ModbusReaderPro"
TRIAL_LIMIT_HOURS = 72
GRACE_PERIOD_HOURS = 72

IS_PRO = False
MACHINE_ID = "UNKNOWN"

def get_machine_fingerprint():
    try:
        mac = uuid.getnode()
        node = platform.node()
        raw_data = f"{mac}-{node}"
        digest = hashlib.sha256(raw_data.encode()).hexdigest()
        return digest[:8].upper()
    except: return "ERROR_ID"

def verify_license_format(key):
    try:
        key = key.strip().upper()
        parts = key.split('-')
        if len(parts) != 3 or not key.startswith("MRPRO-"): return False
        fp_in_key = parts[1]; sig_in_key = parts[2]
        current_machine = get_machine_fingerprint()
        if fp_in_key != current_machine: return False
        expected_sig = hmac.new(SECRET_SALT, fp_in_key.encode(), hashlib.sha256).hexdigest()[:16].upper()
        return sig_in_key == expected_sig
    except: return False

def check_ntp_time():
    """Returns True if system time is roughly correct."""
    try:
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org', version=3)
        diff = abs(response.tx_time - time.time())
        if diff > 3600: return False # > 1 hour diff
        return True
    except:
        return True # Fail open if no net, handled by grace logic

def check_updates():
    try:
        r = requests.get(VERSION_CHECK_URL, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("version", "0.0.0") > APP_VERSION:
                if messagebox.askyesno("Update", "New version available! Download?"):
                    p = os.path.join(os.environ.get("TEMP"), "ModbusSetup.exe")
                    urlretrieve(data["url"], p)
                    subprocess.Popen([p, "/SILENT"]); sys.exit()
    except: pass

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"): self.widget = widget; self.tag = tag
    def write(self, str):
        try:
            self.widget.configure(state="normal"); self.widget.insert("end", str, (self.tag,)); self.widget.see("end"); self.widget.configure(state="disabled")
        except: pass
    def flush(self): pass

class GraphWindow(ctk.CTkToplevel):
    def __init__(self, parent, title="Oscilloscope"):
        super().__init__(parent); self.title(title); self.geometry("600x400")
        self.data_history = []; self.timestamps = []; self.max_points = 50
        self.fig, self.ax = plt.subplots(facecolor='#2b2b2b'); self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(axis='x', colors='white'); self.ax.tick_params(axis='y', colors='white')
        self.line, = self.ax.plot([], [], color='#2CC985', linewidth=2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self); self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.protocol("WM_DELETE_WINDOW", self.on_close); self.is_open = True
    def update_graph(self, value):
        if not self.is_open: return
        try:
            self.data_history.append(value)
            if len(self.data_history) > self.max_points: self.data_history = self.data_history[-self.max_points:]
            self.line.set_data(range(len(self.data_history)), self.data_history)
            self.ax.set_xlim(0, max(self.max_points, len(self.data_history)))
            self.ax.set_ylim(min(self.data_history) - 5 if self.data_history else 0, max(self.data_history) + 5 if self.data_history else 10)
            self.canvas.draw()
        except: pass
    def on_close(self): self.is_open = False; self.destroy()

class ModbusSessionFrame(ctk.CTkFrame):
    def __init__(self, parent, close_callback=None, tab_name=None):
        super().__init__(parent); self.close_callback = close_callback; self.tab_name = tab_name
        self.client = None; self.polling = False; self.poll_thread = None
        self.descriptions = {}; self.prev_data = {} 
        self.recording = False; self.recorded_data = []; self.playback_mode = False
        self.graph_win = None; self.graph_addr_idx = 0 
        self.poll_count = 0; self.valid_response_count = 0; self.error_count = 0
        self.setup_ui()
    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1) 
        self.control_frame = ctk.CTkFrame(self, corner_radius=10); self.control_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        self.conn_type_var = ctk.StringVar(value="TCP")
        ctk.CTkComboBox(self.control_frame, variable=self.conn_type_var, values=["TCP", "Serial"], command=self.update_conn_fields, width=80).grid(row=0, column=0, padx=5)
        self.conn_fields_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent"); self.conn_fields_frame.grid(row=0, column=1, sticky="w")
        self.ip_entry = ctk.CTkEntry(self.conn_fields_frame, width=120); self.ip_entry.insert(0, "127.0.0.1")
        self.port_entry = ctk.CTkEntry(self.conn_fields_frame, width=60); self.port_entry.insert(0, "502")
        self.com_entry = ctk.CTkEntry(self.conn_fields_frame, width=80); self.com_entry.insert(0, "COM1")
        self.baud_entry = ctk.CTkEntry(self.conn_fields_frame, width=80); self.baud_entry.insert(0, "9600")
        self.update_conn_fields("TCP")
        self.btn_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent"); self.btn_frame.grid(row=0, column=2, sticky="e")
        self.btn_connect = ctk.CTkButton(self.btn_frame, text="CONNECT", command=self.connect, fg_color="#2CC985", width=90); self.btn_connect.pack(side="left", padx=2)
        self.btn_disconnect = ctk.CTkButton(self.btn_frame, text="STOP", state="disabled", command=self.disconnect, fg_color="#C92C2C", width=90); self.btn_disconnect.pack(side="left", padx=2)
        self.btn_rec_status = ctk.CTkButton(self.btn_frame, text="⚫ REC", state="disabled", width=60, fg_color="gray"); self.btn_rec_status.pack(side="left", padx=2)
        ctk.CTkButton(self.btn_frame, text="X", command=self.close_session, width=30, fg_color="#555").pack(side="left", padx=5)
        self.slave_id_entry = ctk.CTkEntry(self.control_frame, width=40); self.slave_id_entry.insert(0, "1"); self.slave_id_entry.grid(row=1, column=0, padx=5)
        self.func_code_var = ctk.StringVar(value="03: HOLDING REGISTER")
        ctk.CTkComboBox(self.control_frame, variable=self.func_code_var, values=["01: COIL", "02: INPUT", "03: HOLDING", "04: INPUT REG"], width=160).grid(row=1, column=1, sticky="w")
        self.addr_entry = ctk.CTkEntry(self.control_frame, width=60); self.addr_entry.insert(0, "1"); self.addr_entry.grid(row=1, column=2, sticky="w")
        self.len_entry = ctk.CTkEntry(self.control_frame, width=50); self.len_entry.insert(0, "10"); self.len_entry.grid(row=1, column=2, padx=70, sticky="w")
        self.scan_rate_entry = ctk.CTkEntry(self.control_frame, width=60); self.scan_rate_entry.insert(0, "1000"); self.scan_rate_entry.grid(row=1, column=2, padx=130, sticky="w")
        self.tree_frame = ctk.CTkFrame(self); self.tree_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=15, pady=5)
        self.tree_frame.grid_columnconfigure(0, weight=1); self.tree_frame.grid_rowconfigure(0, weight=1) 
        columns = ("Address", "Value", "Description"); self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")
        self.tree.heading("Address", text="Address"); self.tree.heading("Value", text="Value"); self.tree.heading("Description", text="Description")
        self.tree.column("Address", width=100); self.tree.column("Value", width=150); self.tree.column("Description", width=300)
        self.tree.grid(row=0, column=0, sticky="nsew"); self.tree.bind("<Double-1>", self.on_double_click)
        sb = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview); sb.grid(row=0, column=1, sticky="ns"); self.tree.configure(yscroll=sb.set)
        self.status_bar = ctk.CTkFrame(self, height=30); self.status_bar.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.lbl_status = ctk.CTkLabel(self.status_bar, text="Ready"); self.lbl_status.pack(side="left", padx=10)
        self.lbl_valid = ctk.CTkLabel(self.status_bar, text="Valid: 0", text_color="green"); self.lbl_valid.pack(side="right", padx=10)
        self.lbl_polls = ctk.CTkLabel(self.status_bar, text="Polls: 0"); self.lbl_polls.pack(side="right", padx=10)
    def open_graph(self):
        if not IS_PRO: messagebox.showwarning("Pro", "Pro Feature Required."); return
        if self.graph_win is None or not self.graph_win.is_open: self.graph_win = GraphWindow(self, title=f"Graph - {self.tab_name}")
        else: self.graph_win.focus()
    def toggle_recording(self):
        if not IS_PRO: messagebox.showwarning("Pro", "Pro Feature Required."); return
        self.recording = not self.recording
        if self.recording: self.recorded_data = []; self.btn_rec_status.configure(fg_color="red", text="🔴 REC")
        else: self.btn_rec_status.configure(fg_color="gray", text="⚫ REC")
    def load_session(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if f:
            try:
                with open(f, 'r') as fi: data = json.load(fi)
                if "type" in data: self.conn_type_var.set(data["type"]); self.update_conn_fields(data["type"])
                if "ip" in data: self.ip_entry.delete(0,"end"); self.ip_entry.insert(0,data["ip"])
                if "port" in data: self.port_entry.delete(0,"end"); self.port_entry.insert(0,data["port"])
                if "slave" in data: self.slave_id_entry.delete(0,"end"); self.slave_id_entry.insert(0,data["slave"])
                if "func" in data: self.func_code_var.set(data["func"])
                if "addr" in data: self.addr_entry.delete(0,"end"); self.addr_entry.insert(0,data["addr"])
                if "len" in data: self.len_entry.delete(0,"end"); self.len_entry.insert(0,data["len"])
                if "descriptions" in data: self.descriptions = data["descriptions"]
            except Exception as e: messagebox.showerror("Error", str(e))
    def save_session(self):
        data = { "type": self.conn_type_var.get(), "ip": self.ip_entry.get(), "port": self.port_entry.get(), "slave": self.slave_id_entry.get(), "func": self.func_code_var.get(), "addr": self.addr_entry.get(), "len": self.len_entry.get(), "descriptions": self.descriptions }
        f = filedialog.asksaveasfilename(defaultextension=".json")
        if f: 
            with open(f,'w') as fo: json.dump(data, fo)
    def export_excel(self):
        data = [{"Address": self.tree.item(i)['values'][0], "Value": self.tree.item(i)['values'][1], "Description": self.tree.item(i)['values'][2]} for i in self.tree.get_children()]
        f = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if f: pd.DataFrame(data).to_excel(f, index=False)
    def import_excel(self):
        f = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if f:
            try:
                df = pd.read_excel(f)
                for _, r in df.iterrows(): self.descriptions[str(r['Address'])] = str(r['Description'])
            except: pass
    def load_playback(self):
        if not IS_PRO: messagebox.showwarning("Pro", "Pro Feature Required."); return
        f = filedialog.askopenfilename()
        if f: 
            with open(f) as fi: self.recorded_data = json.load(fi)
            self.playback_mode = True; threading.Thread(target=self.playback_loop, daemon=True).start()
    def playback_loop(self):
        for item in self.recorded_data:
            if not self.playback_mode: break
            self.after(0, self.update_display, item[1], item[2], item[3]); time.sleep(1.0)
        self.playback_mode = False
    def update_conn_fields(self, choice):
        for w in self.conn_fields_frame.winfo_children(): w.pack_forget()
        if choice=="TCP": self.ip_entry.pack(side="left"); self.port_entry.pack(side="left")
        else: self.com_entry.pack(side="left"); self.baud_entry.pack(side="left")
    def connect(self):
        try:
            if self.conn_type_var.get()=="TCP": self.client=ModbusTcpClient(self.ip_entry.get(), port=int(self.port_entry.get()))
            else: self.client=ModbusSerialClient(port=self.com_entry.get(), baudrate=int(self.baud_entry.get())); self.client.connect()
            self.btn_connect.configure(state="disabled"); self.btn_disconnect.configure(state="normal")
            self.polling=True; self.poll_count=0; self.valid_response_count=0; 
            self.poll_thread=threading.Thread(target=self.poll_loop, daemon=True); self.poll_thread.start()
            self.lbl_status.configure(text="Connected", text_color="green")
        except Exception as e: messagebox.showerror("Err", str(e))
    def disconnect(self):
        self.polling=False; 
        if self.client: self.client.close()
        self.btn_connect.configure(state="normal"); self.btn_disconnect.configure(state="disabled")
        self.lbl_status.configure(text="Disconnected", text_color="white")
        if self.recording: self.toggle_recording()
    def close_session(self): self.disconnect(); (self.close_callback(self.tab_name) if self.close_callback else None)
    def on_double_click(self, event):
        iid = self.tree.identify_row(event.y); col = self.tree.identify_column(event.x)
        if iid and col == '#3':
            d = ctk.CTkInputDialog(title="Edit", text="Description:").get_input()
            if d: self.descriptions[iid]=d; self.tree.set(iid, "Description", d)
    def poll_loop(self):
        while self.polling:
            self.poll_count+=1
            try:
                s=int(self.slave_id_entry.get()); a=int(self.addr_entry.get()); l=int(self.len_entry.get()); rate=int(self.scan_rate_entry.get())/1000.0
                f=self.func_code_var.get(); rr=None; p=""
                if "01" in f: rr=self.client.read_coils(a-1,l,slave=s); p="0"
                elif "02" in f: rr=self.client.read_discrete_inputs(a-1,l,slave=s); p="1"
                elif "03" in f: rr=self.client.read_holding_registers(a-1,l,slave=s); p="4"
                elif "04" in f: rr=self.client.read_input_registers(a-1,l,slave=s); p="3"
                if rr and not rr.isError():
                    self.valid_response_count+=1; d = rr.registers if hasattr(rr,'registers') else rr.bits[:l]
                    self.after(0, self.update_display, a, d, p); self.after(0, lambda: self.lbl_status.configure(text="Polling...", text_color="green"))
                    if self.recording: self.recorded_data.append([time.time(), a, d, p])
                else: self.error_count+=1; self.after(0, lambda: self.lbl_status.configure(text="Modbus Error", text_color="red"))
            except Exception as e: print(e); self.error_count+=1
            self.after(0, self.update_counters); time.sleep(rate if 'rate' in locals() else 1)
    def update_counters(self): self.lbl_polls.configure(text=f"Polls: {self.poll_count}"); self.lbl_valid.configure(text=f"Valid: {self.valid_response_count}")
    def update_display(self, start, data, prefix):
        iids = []
        for i, val in enumerate(data):
            addr = start+i; num = 1 if val is True else (0 if val is False else val)
            fid = f"{prefix}{addr:04d}"; iids.append(fid); desc = self.descriptions.get(fid, "")
            if self.prev_data.get(fid) == 0 and num == 1: threading.Thread(target=lambda: winsound.Beep(1000, 500), daemon=True).start()
            self.prev_data[fid] = num
            if self.graph_win and self.graph_win.is_open and i == self.graph_addr_idx: self.graph_win.update_graph(num)
            v = (fid, num, desc)
            if self.tree.exists(fid): self.tree.item(fid, values=v)
            else: self.tree.insert("", "end", iid=fid, values=v)
        for c in self.tree.get_children():
            if c not in iids: self.tree.delete(c)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Security: Time Check
        if not check_ntp_time():
            messagebox.showerror("Security", "System Time Tampered.\nCheck internet or fix clock."); sys.exit()

        # Security: Update Check
        threading.Thread(target=check_updates, daemon=True).start()

        self.check_trial_and_license()

        self.title(f"Modbus Reader {'PRO' if IS_PRO else 'FREE (Trial)'}")
        self.geometry("1100x800")
        
        self.top = ctk.CTkFrame(self, height=50); self.top.pack(fill="x")
        ctk.CTkLabel(self.top, text="Modbus Reader " + ("PRO" if IS_PRO else "FREE"), font=("Arial", 20, "bold")).pack(side="left", padx=20)
        
        for name, cmd in [("File", self.show_file), ("Recording", self.show_rec), ("License", self.show_lic)]:
            b=ctk.CTkButton(self.top, text=name+" ▼", width=60, fg_color="transparent", command=cmd); b.pack(side="left", padx=2)
            setattr(self, f"btn_{name.lower()}", b)

        ctk.CTkButton(self.top, text="+ Session", command=self.add_session).pack(side="right", padx=10)

        self.tabview = ctk.CTkTabview(self); self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self.session_count = 0; self.add_session()
        
        self.tabview.add("Logs")
        self.log_txt = ctk.CTkTextbox(self.tabview.tab("Logs")); self.log_txt.pack(fill="both", expand=True)
        sys.stdout = TextRedirector(self.log_txt); sys.stderr = TextRedirector(self.log_txt)
        print(f"App Started. Machine ID: {MACHINE_ID}")
        
        if not IS_PRO:
            print("Free Edition Active.")
            messagebox.showinfo("Free Edition", "You are using the Free Edition.\nTo unlock Pro features (Multiple Sessions, Graphing, Recording),\nplease donate/request a license at:\n\ninfo@recodestudio.it")
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def check_trial_and_license(self):
        global IS_PRO, MACHINE_ID
        MACHINE_ID = get_machine_fingerprint()

        # 1. Reg Key Check
        lic_key = None
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
            lic_key, _ = winreg.QueryValueEx(key, "LicenseKey")
            winreg.CloseKey(key)
        except: pass

        if lic_key and verify_license_format(lic_key):
            try:
                # 2. Online Check
                print("Syncing with License Server...")
                r = requests.get(f"{LICENSE_SERVER_URL}?action=check&key={lic_key}&hwid={MACHINE_ID}", timeout=5)
                
                if r.status_code == 200:
                    status = r.json().get("status", "INVALID")
                    
                    if status == "VALID":
                        print("License Verified: PRO Active")
                        IS_PRO = True
                        try:
                            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
                            winreg.SetValueEx(k, "LastVerified", 0, winreg.REG_SZ, str(time.time()))
                            winreg.CloseKey(k)
                        except: pass
                        return
                        
                    elif status == "REVOKED":
                         print("License REVOKED by Server.")
                         # Delete Key
                         try:
                            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
                            winreg.DeleteValue(k, "LicenseKey")
                            winreg.CloseKey(k)
                         except: pass
                         messagebox.showwarning("License", "License Revoked. Reverting to Free Mode.")
                         
                    else:
                        # INVALID or Key Not Found (e.g. deleted on server)
                        print(f"License Invalid: {status}")
                        try:
                            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
                            winreg.DeleteValue(k, "LicenseKey")
                            winreg.CloseKey(k)
                        except: pass
                        # Silent revert to free, but print logs
                        
            except Exception as e:
                print(f"Sync Failed ({e}). Trying Offline Grace.")
                # 3. Grace Period
                try:
                     key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
                     lv, _ = winreg.QueryValueEx(key, "LastVerified")
                     winreg.CloseKey(key)
                     elapsed = (time.time() - float(lv))/3600
                     if elapsed < GRACE_PERIOD_HOURS:
                         print(f"Offline Mode (Grace: {elapsed:.1f}h)"); IS_PRO = True; return
                     else:
                         print("Grace Period Expired")
                except: pass

        # 4. Trial Check (If we reach here, IS_PRO is False)
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
            try:
                install_date, _ = winreg.QueryValueEx(key, "InstallDate")
                ts = float(install_date)
            except:
                ts = time.time(); winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, str(ts))
            winreg.CloseKey(key)
            elapsed = (time.time() - ts) / 3600
            
            if elapsed > TRIAL_LIMIT_HOURS and not IS_PRO:
                 messagebox.showerror("Expired", f"Trial Ended.\nTo continue, please donate/request license at:\ninfo@recodestudio.it\n\nID: {MACHINE_ID}"); self.destroy(); sys.exit()
        except Exception as e: print(e)

    def show_file(self):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="New Session", command=self.add_session)
        m.add_command(label="Load Config", command=self.do('load_session'))
        m.add_command(label="Save Config", command=self.do('save_session'))
        m.add_separator()
        m.add_command(label="Export Excel", command=self.do('export_excel'))
        m.add_command(label="Import Excel", command=self.do('import_excel'))
        m.add_separator()
        m.add_command(label="Graph", command=self.do('open_graph'))
        m.add_command(label="Exit", command=self.on_close)
        m.post(self.btn_file.winfo_rootx(), self.btn_file.winfo_rooty() + 30)

    def show_rec(self):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="Toggle Rec", command=self.do('toggle_recording'))
        m.add_command(label="Playback", command=self.do('load_playback'))
        m.post(self.btn_recording.winfo_rootx(), self.btn_recording.winfo_rooty() + 30)

    def show_lic(self):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="Activate", command=self.activate)
        m.add_command(label=f"Copy ID: {MACHINE_ID}", command=lambda: self.clipboard_clear() or self.clipboard_append(MACHINE_ID))
        m.post(self.btn_license.winfo_rootx(), self.btn_license.winfo_rooty() + 30)

    def do(self, func): return lambda: self.call_active(func)
    def call_active(self, func):
        try:
            t = self.tabview.get()
            if t != "Logs": 
                for c in self.tabview.tab(t).winfo_children():
                    if isinstance(c, ModbusSessionFrame): getattr(c, func)()
        except: pass

    def on_close(self):
        try:
            for tab_name in self.tabview._tab_dict:
                if tab_name == "Logs": continue
                for child in self.tabview.tab(tab_name).winfo_children():
                    if isinstance(child, ModbusSessionFrame):
                        child.polling = False
                        if child.client: child.client.close()
        except: pass
        self.destroy(); sys.exit()

    def add_session(self):
        if not IS_PRO and self.session_count >= 1: messagebox.showwarning("Pro", "Free version limited to 1 session."); return
        self.session_count += 1; name = f"Session {self.session_count}"
        self.tabview.insert(self.session_count-1, name)
        f = self.tabview.tab(name); f.grid_columnconfigure(0, weight=1); f.grid_rowconfigure(0, weight=1)
        ModbusSessionFrame(f, close_callback=lambda n: self.tabview.delete(n), tab_name=name).grid(sticky="nsew")
        self.tabview.set(name)

    def activate(self):
        msg = (f"To request an activation key, email:\ninfo@recodestudio.it\n\n"
               f"Provide this Machine ID: {MACHINE_ID}\n\n"
               f"Enter License Key below:")
        c = simpledialog.askstring("Activate Pro", msg)
        if c and verify_license_format(c):
            try:
                # Save key locally first
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
                winreg.SetValueEx(key, "LicenseKey", 0, winreg.REG_SZ, c)
                winreg.CloseKey(key)
                messagebox.showinfo("Success", "License Activated! Please restart the app to verify online.")
                self.destroy(); sys.exit()
            except Exception as e: messagebox.showerror("Err", str(e))
        elif c: messagebox.showerror("Err", "Invalid Key or Machine ID mismatch")

if __name__ == "__main__":
    app = App()
    app.mainloop()
