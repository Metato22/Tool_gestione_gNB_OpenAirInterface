# Tool di Gestione per gNB OpenAirInterface

Questo progetto consiste in un'applicazione client-server per configurare, avviare, monitorare e arrestare una gNodeB (gNB) di OpenAirInterface (OAI) da un'interfaccia grafica (GUI).

## Panoramica del Progetto

L'architettura si basa su due componenti principali:

1.  **Server (`server_gnb.py`)**: Uno script Python da eseguire sulla macchina (es. una Virtual Machine) dove è installato e compilato OpenAirInterface. Questo server si mette in ascolto di comandi, gestisce il processo `nr-softmodem` (l'eseguibile della gNB), e trasmette i log e le metriche in tempo reale.
2.  **Client (`main.py`)**: Un'applicazione grafica (GUI) scritta in Python con PySide6, da eseguire su un PC locale (es. Windows, macOS, o un'altra macchina Linux). L'utente interagisce con la GUI per inviare comandi al server e visualizzare i dati ricevuti.

La comunicazione tra client e server avviene tramite la libreria ZeroMQ (ZMQ).

## Funzionalità Principali

*   **Configurazione Grafica**: Modifica dei principali parametri della gNB (rete, radio, hardware) tramite un'interfaccia intuitiva.
*   **Avvio Flessibile**: Possibilità di avviare la gNB partendo da un template di default o utilizzando un file di configurazione `.conf` esistente come base.
*   **Controllo Remoto**: Avvio e arresto della gNB sulla macchina remota.
*   **Monitoraggio in Tempo Reale**:
    *   Visualizzazione live dei log della gNB.
    *   Dashboard con le metriche principali dell'UE (RSRP, SNR, BLER, Throughput, etc.).
    *   Grafici in tempo reale per le metriche più importanti.
*   **Esportazione Dati**: Salvataggio della cronologia delle metriche raccolte in un file `.csv` per analisi offline.

---

## 📝 Guida alla Configurazione per un Nuovo Setup

Per utilizzare questo tool su un setup diverso, è necessario configurare alcuni parametri chiave in entrambi gli script.

### 1. Configurazione del Client (`main.py`)

L'unica modifica fondamentale richiesta in questo file è l'indirizzo IP del server.

*   **Indirizzo IP della VM/Server OAI**:
    *   Apri il file `main.py`.
    *   Trova la riga all'inizio del file:
      ```python
      # Indirizzo IP della VM.
      VM_IP = "192.168.56.102"
      ```
    *   **Sostituisci `"192.168.56.102"` con l'indirizzo IP della macchina su cui eseguirai `server_gnb.py`**. Assicurati che questo IP sia raggiungibile dalla macchina client.

### 2. Configurazione del Server (`server_gnb.py`)

Questo script contiene i percorsi specifici dell'installazione di OpenAirInterface. È fondamentale che questi percorsi corrispondano a quelli della macchina server.

*   **Directory Principale di OpenAirInterface**:
    *   Apri il file `server_gnb.py`.
    *   Trova la sezione `Configurazione Percorsi`:
      ```python
      # Configurazione Percorsi
      OAI_DIR = os.path.expanduser("~/openairinterface5g")
      ```
    *   **Modifica il percorso `"~/openairinterface5g"`** per farlo corrispondere alla directory dove hai clonato il repository di OAI sulla tua macchina server. `~` rappresenta la home directory dell'utente. Se OAI si trova in `/opt/oai`, per esempio, la riga diventerà `OAI_DIR = "/opt/oai"`.
    *   **Nota**: Lo script assume la struttura di directory standard di OAI. Le sottodirectory (`cmake_targets/ran_build/build`, etc.) vengono derivate automaticamente dal percorso `OAI_DIR`.
---

## ⚙️ Installazione e Utilizzo

### Prerequisiti

Assicurati che i seguenti requisiti siano soddisfatti.

**Sulla macchina Client (dove si esegue `main.py`):**

1.  **Python 3.x** installato.
2.  Le seguenti librerie Python, installabili via `pip`:
    ```bash
    pip install PySide6 pyqtgraph pyzmq
    ```

**Sulla macchina Server (la VM con OAI):**

1.  **Python 3.x** installato.
2.  **OpenAirInterface gNB** correttamente installato e compilato.
3.  La libreria Python `pyzmq`:
    ```bash
    pip install pyzmq
    ```

### Procedura di Esecuzione

1.  **Posiziona i File**:
    *   Copia `server_gnb.py` sulla macchina server OAI (es. nella sua home directory).
    *   Copia la cartella del progetto (`main.py`, `style.qss`, e la cartella `Images`) sulla tua macchina client locale.

2.  **Avvia il Server**:
    *   Connettiti alla macchina server OAI (es. tramite SSH).
    *   Esegui lo script del server.
      ```bash
      python3 server_gnb.py
      ```
    *   Dovresti vedere il messaggio: `[SERVER] Server gNB pronto su porta 5555. Directory di lavoro: ...`

3.  **Avvia il Client (GUI)**:
    *   Sulla tua macchina locale, vai nella cartella del progetto.
    *   Esegui lo script principale:
      ```bash
      python3 main.py
      ```
    *   L'interfaccia grafica si avvierà a schermo intero.

4.  **Utilizza l'Applicazione**:
    *   Apri le sezioni che ti interessano per configurare i parametri.
    *   (Opzionale) Clicca su "Seleziona file base" per caricare un file `.conf` pre-esistente dalla macchina server.
    *   Clicca su "Avvia".
    *   Inserisci la password `sudo` della macchina server quando richiesta.
    *   Monitora i log e le metriche che appariranno nella GUI.
    *   Per terminare, clicca su "Stop". Se sono state raccolte metriche, ti verrà chiesto se desideri salvarle prima di chiudere.