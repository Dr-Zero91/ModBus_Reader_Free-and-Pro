# Modbus Manager - Manuale Utente

Benvenuto in **Modbus Manager**. Questa guida ti aiuterà a configurare e utilizzare il software per testare e monitorare le tue reti Modbus TCP e RTU.

---

## 1. Avvio e Attivazione

### Avvio
Dopo l'installazione tramite il setup, avvia l'applicazione dall'icona sul desktop `Modbus Manager`.

### Attivazione (Versione Pro)
Al primo avvio, se hai acquistato la versione Pro:
1.  Ti verrà mostrato il tuo **Machine ID**.
2.  Inserisci la tua **Email** e il **Product Key** ricevuto.
3.  Clicca su **Activate**. Il software verificherà la licenza online.
    *   *Nota: È necessaria una connessione internet per la prima attivazione e per i controlli periodici.*

---

## 2. Modalità Client (Master)

Utilizza questa modalità per connetterti a dispositivi Modbus (PLC, sensori, ecc.) e leggere/scrivere dati.

### Configurazione Connessione
Nel pannello di sinistra "Connection settings":
1.  **Protocollo**: Scegli tra `Modbus TCP` (Ethernet/WiFi) o `Modbus Serial` (RS485/RS232).
2.  **TCP**: Inserisci l'indirizzo **IP** del dispositivo e la **Porta** (default 502).
3.  **Serial**: Seleziona la **Porta COM**, **Baud Rate**, **Parità**, **Stop Bits** e **Bytesize**.
4.  Clicca su **Connect**.

### Lettura Registri (Polling)
Una volta connesso:
1.  Nel pannello "Read settings" (o nella tabella principale):
    *   **Slave ID**: ID del dispositivo (default 1).
    *   **Function Code**: Scegli il tipo di dato:
        *   `01 Read Coils` (Output digitali)
        *   `02 Read Discrete Inputs` (Input digitali)
        *   `03 Read Holding Registers` (Registri 16-bit R/W)
        *   `04 Read Input Registers` (Registri 16-bit Read-only)
    *   **Address**: Indirizzo di partenza (es. 0 o 40001).
    *   **Quantity**: Numero di registri da leggere.
2.  Clicca **Read** per una lettura singola o **Start/Stop** per il monitoraggio continuo.

### Scrittura Dati
Per modificare un valore:
1.  Fai doppio clic sulla cella **Value** nella tabella.
2.  Inserisci il nuovo valore e premi Invio.
3.  Il software invierà automaticamente il comando di scrittura (`Write Single`) al dispositivo.

### Gestione Descrizioni
*   Puoi assegnare nomi ai registri (es. "Temperatura Forno") modificando la colonna **Description**.
*   Queste descrizioni vengono salvate automaticamente.

---

## 3. Modalità Server (Slave) - [Solo Pro]

Trasforma il tuo PC in un dispositivo Modbus virtuale per testare altri Client (HMI, SCADA).

1.  Vai alla scheda/modalità **Server**.
2.  **Configurazione**:
    *   Scegli se simulare un server **TCP** (tutte le interfacce o IP specifico) o **Serial** (scegliendo la COM).
3.  Clicca **Start Server**.
4.  **Monitoraggio**:
    *   Il pannello "Operation Log" mostrerà in tempo reale le richieste ricevute dai client (IP, tipo di richiesta, registri letti/scritti).
5.  **Simulazione Dati**:
    *   Puoi modificare i valori nella tabella del Server; i client connessi leggeranno questi nuovi valori aggiornati.

---

## 4. Funzionalità Avanzate

### Esportazione Excel
*   Clicca sull'icona **Export** (o seleziona dal menu File) per salvare la configurazione corrente (indirizzi, valori e descrizioni) in un file `.xlsx`.
*   Utile per creare report o mappare le variabili.

### Registrazione (Recording) - [Solo Pro]
1.  Clicca il pulsante **REC** in alto.
2.  Il software inizierà a salvare tutte le variazioni dei valori su un file di log.
3.  Clicca **STOP** per terminare. I dati possono essere riprodotti o analizzati successivamente.

### Multi-Sessione - [Solo Pro]
*   Puoi aprire più tab di connessione ("Session 1", "Session 2"...) per connetterti a dispositivi diversi contemporaneamente.

---

## 5. Risoluzione Problemi

*   **Connessione Fallita**:
    *   Verifica che l'IP sia raggiungibile (fai un ping).
    *   Controlla che la Porta 502 non sia bloccata dal Firewall.
    *   Per la seriale: verifica che nessun altro software stia usando la porta COM.
*   **Errori "Time-out"**:
    *   Il dispositivo non risponde. Controlla il cablaggio o aumenta il timeout nelle impostazioni.
*   **Licenza non valida**:
    *   Assicurati che l'orologio di sistema sia corretto (controllo NTP attivo).
    *   Verifica la connessione internet.

Per supporto tecnico, contattare: `info@recodestudio.it`
