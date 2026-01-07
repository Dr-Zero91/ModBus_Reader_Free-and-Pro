import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import hmac
import hashlib
import sqlite3
import datetime
import requests
import json
import os

# SECRET SALT
SALT_PART_A = b"ModbusPro"
SALT_PART_B = b"_SuperSecret_2025"
SECRET_SALT = SALT_PART_A + SALT_PART_B

CONFIG_FILE = "config.json"
DB_FILE = "licenses.db"

class KeyGenManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Modbus Pro License Manager")
        self.geometry("900x700")
        
        self.license_server_url = "https://www.recodestudio.it/app/modbus-server/license_server.php"
        self.admin_secret = "YOUR_ADMIN_SECRET_123"
        
        self.load_config()
        self.setup_db()
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.setup_generator_tab()
        self.setup_database_tab()
        self.setup_settings_tab()
        
        # Auto-Sync on startup
        self.after(100, self.sync_from_server)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.license_server_url = data.get("server_url", self.license_server_url)
                    self.admin_secret = data.get("admin_secret", self.admin_secret)
            except: pass

    def save_config(self):
        data = {
            "server_url": self.entry_server_url.get(),
            "admin_secret": self.entry_admin_secret.get()
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f)
            self.license_server_url = data["server_url"]
            self.admin_secret = data["admin_secret"]
            messagebox.showinfo("Saved", "Configuration saved!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def setup_db(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY,
                owner TEXT,
                email TEXT,
                machine_id TEXT,
                license_key TEXT UNIQUE,
                status TEXT DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def setup_generator_tab(self):
        t = self.tabview.add("Generator")
        ctk.CTkLabel(t, text="Generate New License", font=("Arial", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(t, text="Customer Name:").pack(); self.entry_name = ctk.CTkEntry(t, width=300); self.entry_name.pack(pady=5)
        # ctk.CTkLabel(t, text="Customer Email:").pack(); self.entry_email = ctk.CTkEntry(t, width=300); self.entry_email.pack(pady=5)
        ctk.CTkLabel(t, text="Machine ID (8 chars):").pack(); self.entry_hwid = ctk.CTkEntry(t, width=300); self.entry_hwid.pack(pady=5)
        ctk.CTkButton(t, text="Generate & Sync", command=self.generate_and_save, fg_color="#2CC985").pack(pady=20)
        ctk.CTkLabel(t, text="Generated Key:").pack(); self.entry_key = ctk.CTkEntry(t, width=400); self.entry_key.pack(pady=5)

    def setup_database_tab(self):
        t = self.tabview.add("Database")
        
        # New: Use Treeview instead of Textbox for selection
        columns = ("ID", "Owner", "Key", "Status", "Machine")
        self.tree = ttk.Treeview(t, columns=columns, show="headings", height=15)
        
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=30)
        self.tree.heading("Owner", text="Owner")
        self.tree.column("Owner", width=120)
        self.tree.heading("Key", text="Key")
        self.tree.column("Key", width=250)
        self.tree.heading("Status", text="Status")
        self.tree.column("Status", width=80)
        self.tree.heading("Machine", text="Machine")
        self.tree.column("Machine", width=80)
        
        self.tree.pack(pady=10, fill="both", expand=True)
        
        btn_frame = ctk.CTkFrame(t)
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="Sync from Server", command=self.sync_from_server, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Revoke Selected", command=self.revoke_selected, fg_color="#D97706", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="DELETE Selected", command=self.delete_selected, fg_color="#C92C2C", width=120).pack(side="left", padx=5)
        
        self.refresh_db_view()

    def setup_settings_tab(self):
        t = self.tabview.add("Settings")
        t.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(t, text="Connection Options", font=("Arial", 16, "bold")).pack(pady=20)
        
        frm = ctk.CTkFrame(t)
        frm.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(frm, text="Server URL:").pack(anchor="w", padx=10)
        self.entry_server_url = ctk.CTkEntry(frm, width=400)
        self.entry_server_url.insert(0, self.license_server_url)
        self.entry_server_url.pack(padx=10, pady=(0,10), fill="x")
        
        ctk.CTkLabel(frm, text="Admin Secret:").pack(anchor="w", padx=10)
        self.entry_admin_secret = ctk.CTkEntry(frm, width=400)
        self.entry_admin_secret.insert(0, self.admin_secret)
        self.entry_admin_secret.pack(padx=10, pady=(0,10), fill="x")
        
        btn_frm = ctk.CTkFrame(t, fg_color="transparent")
        btn_frm.pack(pady=20)
        
        ctk.CTkButton(btn_frm, text="Test Connection", command=self.test_connection, fg_color="#3B8ED0").pack(side="left", padx=10)
        ctk.CTkButton(btn_frm, text="Save Settings", command=self.save_config, fg_color="#2CC985").pack(side="left", padx=10)

    def test_connection(self):
        url = self.entry_server_url.get()
        secret = self.entry_admin_secret.get()
        try:
            # We try to list_all just to check auth
            data = {"action": "list_all", "admin_secret": secret}
            r = requests.post(url, data=data, timeout=5)
            if r.status_code == 200:
                js = r.json()
                if js.get("status") == "SUCCESS":
                    messagebox.showinfo("Success", "Connection & Authentication Successful!")
                else:
                    messagebox.showerror("Failed", f"Server Info: {js.get('message')}")
            else:
                messagebox.showerror("Error", f"HTTP Error: {r.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection Failed: {e}")

    def sync_from_server(self):
        print("Syncing...")
        try:
            payload = {"action": "list_all", "admin_secret": self.admin_secret}
            r = requests.post(self.license_server_url, data=payload, timeout=5)
            if r.status_code == 200:
                js = r.json()
                if js.get("status") == "SUCCESS":
                    server_licenses = js.get("data", [])
                    
                    self.cursor.execute("DELETE FROM licenses")
                    
                    for l in server_licenses:
                        # id, license_key, machine_id, owner_name, status, created_at
                        self.cursor.execute(
                            "INSERT INTO licenses (owner, machine_id, license_key, status, created_at) VALUES (?, ?, ?, ?, ?)",
                            (l.get('owner_name'), l.get('machine_id'), l.get('license_key'), l.get('status'), l.get('created_at'))
                        )
                    self.conn.commit()
                    self.refresh_db_view()
                else:
                    print("Sync Error: " + js.get("message", ""))
        except Exception as e:
            print(f"Sync Failed: {e}")

    def generate_and_save(self):
        name = self.entry_name.get(); hwid = self.entry_hwid.get().strip().upper()
        if not hwid or len(hwid) < 8: messagebox.showwarning("Error", "Invalid Machine ID"); return
        
        # Local Gen
        sig = hmac.new(SECRET_SALT, hwid.encode(), hashlib.sha256).hexdigest()[:16].upper()
        key = f"MRPRO-{hwid}-{sig}"
        self.entry_key.delete(0, "end"); self.entry_key.insert(0, key)
        
        # Sync Server
        try:
            payload = {"action": "add", "key": key, "hwid": hwid, "owner": name, "admin_secret": self.admin_secret}
            r = requests.post(self.license_server_url, data=payload, timeout=5)
            if r.status_code == 200 and r.json().get("status") == "SUCCESS":
                messagebox.showinfo("Success", "License Generated & Synced!")
                self.sync_from_server() 
            else:
                messagebox.showwarning("Error", "Server add failed.")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")

    def refresh_db_view(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        self.cursor.execute("SELECT * FROM licenses ORDER BY id DESC")
        rows = self.cursor.fetchall()
        for r in rows:
            # db schema: id, owner, email, machine, key, status, created
            # tree cols: ID, Owner, Key, Status, Machine
            # Note: email column might be missing if we used old schema logic, simply skipped
            # My current create table has 7 columns.
            # r[0]=id, r[1]=owner, r[2]=email, r[3]=machine, r[4]=key, r[5]=status
            
            # Let's be safe slightly
            vals = (r[0], r[1], r[4], r[5], r[3])
            self.tree.insert("", "end", values=vals)

    def get_selected_key(self):
        sel = self.tree.selection()
        if not sel: return None
        item = self.tree.item(sel[0])
        return item['values'][2] # Key is col idx 2

    def revoke_selected(self):
        key = self.get_selected_key()
        if not key:
            messagebox.showwarning("Select", "Please select a license to revoke.")
            return
            
        if not messagebox.askyesno("Confirm", f"Revoke license?\n{key}"): return

        try:
            payload = {"action": "revoke", "key": key, "admin_secret": self.admin_secret}
            r = requests.post(self.license_server_url, data=payload, timeout=5)
            if r.status_code == 200 and r.json().get("status") == "SUCCESS": 
                messagebox.showinfo("Revoked", "Key Revoked on Server.")
                self.sync_from_server()
            else: messagebox.showwarning("Error", "Server Revocation Failed.")
        except Exception as e: messagebox.showwarning("Error", f"Conn failed: {e}")

    def delete_selected(self):
        key = self.get_selected_key()
        if not key:
            messagebox.showwarning("Select", "Please select a license to DELETE.")
            return

        if not messagebox.askyesno("Confirm", f"PERMANENTLY DELETE license?\n{key}\n\nThis cannot be undone."): return

        try:
            payload = {"action": "delete", "key": key, "admin_secret": self.admin_secret}
            r = requests.post(self.license_server_url, data=payload, timeout=5)
            if r.status_code == 200 and r.json().get("status") == "SUCCESS": 
                messagebox.showinfo("Deleted", "License Deleted from Server.")
                self.sync_from_server()
            else: messagebox.showwarning("Error", "Server Delete Failed.")
        except Exception as e: messagebox.showwarning("Error", f"Conn failed: {e}")

if __name__ == "__main__":
    app = KeyGenManager()
    app.mainloop()
