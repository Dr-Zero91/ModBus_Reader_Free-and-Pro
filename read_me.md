# Modbus Reader Pro

Un'applicazione desktop avanzata per la lettura e il monitoraggio di dispositivi Modbus (TCP e Seriale), dotata di grafici in tempo reale, registrazione dati e un sistema di licenza professionale.

## Funzionalità Principali

### Connettività
*   **Modbus TCP & Seriale**: Supporto per connessioni tramite IP/Porta o COM/Baudrate.
*   **Configurazione Flessibile**: Imposta ID Slave, Indirizzo di Partenza, Lunghezza e Frequenza di Scansione (ms).
*   **Codici Funzione Supportati**:
    *   01: Coil Status
    *   02: Input Status
    *   03: Holding Register
    *   04: Input Register

### Interfaccia Utente
*   **Multi-Sessione a Schede**: Gestisci più connessioni contemporaneamente in tab separati.
*   **Visualizzazione Tabellare**: Dati mostrati in griglia con Indirizzo, Valore e Descrizione.
*   **Descrizioni Modificabili**: Doppio clic sulla colonna descrizione per assegnare nomi ai registri (persistenti).
*   **Console Log Integrata**: Tutti i messaggi di sistema e di errore sono visibili nella scheda dedicata "Logs", mantenendo l'interfaccia pulita.

### Sistema di Allarme
*   **Rilevamento Automatico**: Monitora le transizioni da 0 a 1 (per bit/coils).
*   **Avviso Sonoro**: Emette un "Beep" quando scatta un allarme.
*   **Popup Visivo**: Mostra una finestra di allerta con l'indirizzo e la descrizione dell'allarme scattato.

### Funzioni Avanzate (File & Dati)
*   **Salva/Carica Configurazione**: Salva i parametri di connessione e le descrizioni in file JSON per richiamarli rapidamente.
*   **Import/Export Excel**:
    *   Esporta la tabella dati corrente in `.xlsx`.
    *   Importa le descrizioni dei registri da un file Excel esistente.

## Funzionalità PRO (Licenza Richiesta)

La versione "Free" è limitata ad una sola sessione e ha un periodo di prova di 72 ore. La versione "Pro" sblocca:

1.  **Sessioni Illimitate**: Apri quante schede di connessione vuoi contemporaneamente.
2.  **Grafico in Tempo Reale (Oscilloscopio)**:
    *   Visualizza l'andamento del primo registro in un grafico scorrevole.
    *   Accessibile dal menu *File -> Session Graph*.
3.  **Registrazione e Playback**:
    *   **Rec**: Registra tutto il traffico dati in un file di log.
    *   **Playback**: Rivedi una sessione registrata come se fosse in diretta.

## Sistema di Licenza e Sicurezza

Il software implementa un robusto sistema di protezione:

*   **Periodo di Prova**: 72 ore dalla prima installazione (controllo via Registro di Sistema).
*   **Machine Fingerprint**: L'attivazione è legata all'hardware del PC (MAC Address + Nome Macchina).
*   **Attivazione**:
    1.  Dall'applicazione, andare su *License -> Copy ID*.
    2.   Generare una chiave univoca basata sull'ID.
    3.   Invia  il tuo codice  a info@recodestudio.it ed attendi  la tua licenza.
    4.  Inserire la chiave nell'applicazione per sbloccare la versione PRO permanentemente.

## Installazione

1.  Installare le dipendenze:
    ```bash
    pip install -r requirements.txt
    ```
2.  Avviare l'applicazione:
    ```bash
    python modbus_reader.py
    ```
3.  Per generare chiavi di licenza:
    ```bash
    Invia  HW ID a  info@recoedstudio.it
    ```

## Requisiti
*   Python 3.x
*   Librerie: `customtkinter`, `pymodbus`, `pandas`, `openpyxl`, `matplotlib`, `requests` (vedi `requirements.txt`).
