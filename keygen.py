import customtkinter as ctk
import hmac
import hashlib

# SECRET SALT - SPLIT FOR OBFUSCATION
SALT_PART_A = b"ModbusPro"
SALT_PART_B = b"_SuperSecret_2025"
SECRET_SALT = SALT_PART_A + SALT_PART_B

class KeyGen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Modbus Pro Activator v2")
        self.geometry("400x350")
        
        ctk.CTkLabel(self, text="Modbus Reader Pro KeyGen", font=("Arial", 20, "bold")).pack(pady=20)
        
        ctk.CTkLabel(self, text="Target Machine ID (Fingerprint):").pack(pady=5)
        self.entry_hwid = ctk.CTkEntry(self, width=300)
        self.entry_hwid.pack(pady=5)
        
        ctk.CTkButton(self, text="Generate Key", command=self.generate, fg_color="#2CC985", hover_color="#229A65").pack(pady=20)
        
        ctk.CTkLabel(self, text="License Key:").pack(pady=5)
        self.entry_key = ctk.CTkEntry(self, width=300)
        self.entry_key.pack(pady=5)
        
        self.lbl_status = ctk.CTkLabel(self, text="", text_color="green")
        self.lbl_status.pack(pady=10)
        
    def generate(self):
        fingerprint = self.entry_hwid.get().strip().upper()
        if not fingerprint:
            self.lbl_status.configure(text="Error: Enter Machine ID", text_color="red")
            return
            
        if len(fingerprint) != 8:
             self.lbl_status.configure(text="Warning: Machine ID usually 8 chars", text_color="orange")

        # Crypto Logic
        # 1. Sign the fingerprint
        signature = hmac.new(SECRET_SALT, fingerprint.encode(), hashlib.sha256).hexdigest()[:16].upper()
        
        # 2. Construct Key: MRPRO-{FINGERPRINT}-{SIGNATURE}
        # Format: MRPRO-XXXX-XXXX-XXXX-XXXX
        # Actually logic: MRPRO-{FP}-{SIG}
        # Example: MRPRO-CAFE-BABE-1234-5678 (Total 23 chars approx)
        # Let's clean up format to standard groups of 4 for readability?
        # Key: MRPRO-<FP>-<SIG>
        # SIG is 16 chars. FP is 8 chars.
        # Clean format: MRPRO-FP(8)-SIG(16) -> MRPRO-ABCD1234-1A2B3C4D5E6F7890
        
        key = f"MRPRO-{fingerprint}-{signature}"
        
        self.entry_key.delete(0, "end")
        self.entry_key.insert(0, key)
        self.lbl_status.configure(text="Key Generated!", text_color="green")

if __name__ == "__main__":
    app = KeyGen()
    app.mainloop()
