import sys
import os
import json
import zmq
import threading
import re
import time
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QScrollArea, QTextEdit,
    QFileDialog, QInputDialog, QGridLayout, QDialog, QMessageBox, QComboBox
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Signal, Slot, Qt
import pyqtgraph as pg

# Indirizzo IP della VM.
VM_IP = "192.168.56.102"

# Dizionario con tutti i valori di default
DEFAULT_VALUES = {
    # gNB Info
    "gnb_id": "0xe00",
    "gnb_name": "gNB-OAI",
    # Network
    "tac": "1",
    "mcc": "001",
    "mnc": "01",
    "mnc_length": "2",
    "amf_ip": "192.168.70.132",
    "gnb_ip": "192.168.70.129",
    "gnb_port_ngap": "38412", # Valore di default standard
    "gnb_port_s1u": "2152",
    # Hardware (per la modalità simulatore di default)
    "nb_tx": "1",
    "nb_rx": "1",
    "att_tx": "0",
    "att_rx": "0",
    "max_rxgain": "",
    "sdr_addrs": "",
    "clock_src": "internal",
    "time_src": "internal",
    # Radio
    "nr_band": "78",
    "scs": "1",
    "bw": "106",
    "dl_freq_pointA": "640008",
    "abs_freq_ssb": "641280",
    "initial_bwp_riv": "28875",
    "coreset_zero": "12",
    "prach_index": "98",
    # TDD
    "tdd_period": "6",
    "tdd_dl_slots": "7",
    "tdd_dl_sym": "6",
    "tdd_ul_slots": "2",
    "tdd_ul_sym": "4"
}

class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        self.toggle_button = QPushButton(f"► {title}")
        self.toggle_button.setObjectName("collapsible_header")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_area.setLayout(self.content_layout)
        self.content_area.hide()
        self.toggle_button.toggled.connect(self.toggle)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.toggle_button)
        main_layout.addWidget(self.content_area)

    def set_content_layout(self, layout):
        # Rimuove il layout di default e imposta quello fornito
        QWidget().setLayout(self.content_area.layout())
        self.content_area.setLayout(layout)

    def toggle(self, checked):
        if checked:
            self.toggle_button.setText(self.toggle_button.text().replace("►", "▼"))
            self.content_area.show()
        else:
            self.toggle_button.setText(self.toggle_button.text().replace("▼", "►"))
            self.content_area.hide()


class CreditsDialog(QDialog):
    """
    Finestra di dialogo personalizzata per mostrare i crediti.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crediti")
        self.setWindowIcon(QIcon(r"Images/logo-oai.png"))
        self.setMinimumWidth(400)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # --- Titolo e Nome ---
        title_label = QLabel("gNB Control Tool")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")

        creator_label = QLabel("Realizzato da: Matteo Di Maria \n\n Dottore in Ingegneria Informatica e dell\'Automazione")
        creator_label.setAlignment(Qt.AlignCenter)
        creator_label.setStyleSheet("font-size: 12pt; color: #ffffff;")

        main_layout.addWidget(title_label)
        main_layout.addWidget(creator_label)
        main_layout.addStretch()

        # --- Logo e Testo Politecnico ---
        poliba_logo_label = QLabel()
        poliba_pixmap = QPixmap("Images/logo_poliba.png")
        poliba_logo_label.setPixmap(poliba_pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        poliba_logo_label.setAlignment(Qt.AlignCenter)

        poliba_text_label = QLabel("Politecnico di Bari \n\n Il Politecnico di Bari è un\'università statale italiana fondata nel 1990, specializzata nelle discipline scientifiche e tecnologiche \n come l\'ingegneria, l\'architettura e il design. È l\'unico politecnico del Centro-Sud d\'Italia ed è un\'istituzione pubblica \n dedicata all\'istruzione superiore e alla ricerca scientifica e tecnologica,\n con l\'obiettivo di formare professionisti qualificati e promuovere il trasferimento di conoscenze verso le aziende.")
        poliba_text_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(poliba_logo_label)
        main_layout.addWidget(poliba_text_label)
        main_layout.addStretch()

        # --- Logo e Testo Laboratorio ---
        lab_logo_label = QLabel()
        lab_pixmap = QPixmap("Images/logo_lab-dei.png")
        lab_logo_label.setPixmap(lab_pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lab_logo_label.setAlignment(Qt.AlignCenter)

        lab_text_label = QLabel("Telematics Lab \n\n Il Telematics Lab del Politecnico di Bari è un laboratorio di ricerca del Dipartimento di Ingegneria Elettrica e dell\'Informazione (DEI) \n focalizzato sulle tecnologie delle reti di telecomunicazione. Si occupa di progettare, studiare e ottimizzare \n soluzioni ICT per applicazioni emergenti, concentrandosi su temi come i sistemi di comunicazione 5G, \n B5G e 6G, le architetture di comunicazione basate su tecnologia quantistica, l\'Internet of Things (IoT) sicuro e l\'Industria 4.0")
        lab_text_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(lab_logo_label)
        main_layout.addWidget(lab_text_label)
        main_layout.addStretch()

        # --- Pulsante Chiudi ---
        close_button = QPushButton("Chiudi")

        close_button.setObjectName("closeButton")

        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

class MainWindow(QWidget):
    new_log_message = Signal(str)
    new_metrics_data = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("gNB - OpenAirInterface")
        self.setWindowIcon(QIcon(r"Images/logo-oai.png"))
        self.setMinimumWidth(900)
        self.gnb_is_running = False

        self.metrics_history = []

        # Liste per memorizzare i dati dei grafici
        self.time_axis = []
        self.rsrp_data = []
        self.snr_data = []
        self.bler_dl_data = []
        self.bler_ul_data = []

        self.context = zmq.Context()
        self.req_socket = self.context.socket(zmq.REQ)
        self.req_socket.connect(f"tcp://{VM_IP}:5555")
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(f"tcp://{VM_IP}:5556")
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        self.config_file_content = None

        main_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.container_layout = QVBoxLayout(container)

        top_layout = QHBoxLayout()
        self.titolo = QLabel("Gestione gNB - OpenAirInterface")
        self.titolo.setObjectName("labelTitolo")
        top_layout.addWidget(self.titolo)
        top_layout.addStretch()

        self.btn_reset_all = QPushButton("Reset Generale")
        self.btn_reset_all.setObjectName("resetButton")
        self.btn_reset_all.clicked.connect(self.reset_all_fields)
        top_layout.addWidget(self.btn_reset_all)

        self.btn_credits = QPushButton("Crediti")
        self.btn_credits.setObjectName("creditsButton")
        self.btn_credits.clicked.connect(self.show_credits)
        top_layout.addWidget(self.btn_credits)

        self.btn_info = QPushButton("Info")
        self.btn_info.setObjectName("info")
        self.btn_info.clicked.connect(self.show_info)
        top_layout.addWidget(self.btn_info)
        self.container_layout.addLayout(top_layout)

        # Creazione delle sezioni
        self.create_gnb_info_section()
        self.create_network_section()
        self.create_hardware_section()
        self.create_radio_config_section()
        self.create_metrics_section()
        self.create_charts_section()

        self.container_layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_avvia = QPushButton("Avvia")
        self.btn_avvia.setObjectName("avvia")
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("stop")
        self.btn_config = QPushButton("Seleziona file base (Opzionale)");
        self.btn_config.setObjectName("config")
        btn_layout.addWidget(self.btn_avvia)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_config)
        self.container_layout.addLayout(btn_layout)

        self.log_area = QTextEdit()
        self.log_area.setObjectName("log_area")
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(250)
        self.container_layout.addWidget(self.log_area)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        self.btn_avvia.clicked.connect(self.handle_start)
        self.btn_config.clicked.connect(self.select_config_file)
        self.btn_stop.clicked.connect(self.handle_stop)
        self.new_log_message.connect(self.append_log)
        self.new_metrics_data.connect(self.update_metrics_display)
        threading.Thread(target=self.receive_logs, daemon=True).start()

        self.populate_default_values()

        self.show_startup_tutorial()

    def populate_default_values(self):
        """Imposta i valori di default per tutti i campi della GUI."""
        widgets_to_populate = self.findChildren(QLineEdit) + self.findChildren(QComboBox)

        for widget in widgets_to_populate:
            object_name = widget.objectName()
            if object_name in DEFAULT_VALUES:
                value = DEFAULT_VALUES[object_name]
                if isinstance(widget, QLineEdit):
                    widget.setText(value)
                elif isinstance(widget, QComboBox):
                    index = widget.findText(value)
                    if index != -1:
                        widget.setCurrentIndex(index)
        self.new_log_message.emit("[GUI] Campi popolati con i valori di default.")

    def reset_all_fields(self):
        """Svuota tutti i campi di input della GUI."""
        widgets_to_reset = self.findChildren(QLineEdit) + self.findChildren(QComboBox)

        for widget in widgets_to_reset:
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)  # Imposta l'opzione vuota
        self.new_log_message.emit("[GUI] Tutti i campi sono stati resettati.")

    def show_credits(self):
        """Crea e mostra la finestra di dialogo dei crediti."""
        dialog = CreditsDialog(self)
        dialog.exec()

    def reset_section_fields(self, layout):
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, QLineEdit):
                widget.clear()

    def create_gnb_info_section(self):
        gnb_box = CollapsibleBox("Informazioni gNB")
        gnb_layout = QGridLayout()

        self.gnb_id = QLineEdit()
        self.gnb_id.setObjectName("gnb_id")
        self.gnb_name = QLineEdit()
        self.gnb_name.setObjectName("gnb_name")
        gnb_layout.addWidget(QLabel("ID gNB:"), 0, 0)
        gnb_layout.addWidget(self.gnb_id, 0, 1)
        gnb_layout.addWidget(QLabel("Nome gNB:"), 0, 2)
        gnb_layout.addWidget(self.gnb_name, 0, 3)

        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("resetButton")
        reset_btn.clicked.connect(lambda: self.reset_section_fields(gnb_layout))
        gnb_layout.addWidget(reset_btn, 0, 4)

        gnb_box.set_content_layout(gnb_layout)
        self.container_layout.addWidget(gnb_box)

    def create_network_section(self):
        net_box = CollapsibleBox("Parametri di Rete e Connessione")
        net_layout = QGridLayout()

        self.tac = QLineEdit()
        self.tac.setObjectName("tac")
        self.mcc = QLineEdit()
        self.mcc.setObjectName("mcc")
        self.mnc = QLineEdit()
        self.mnc.setObjectName("mnc")
        self.mnc_length = QLineEdit()
        self.mnc_length.setObjectName("mnc_length")
        net_layout.addWidget(QLabel("TAC:"), 0, 0)
        net_layout.addWidget(self.tac, 0, 1)
        net_layout.addWidget(QLabel("MCC:"), 0, 2)
        net_layout.addWidget(self.mcc, 0, 3)
        net_layout.addWidget(QLabel("MNC:"), 0, 4)
        net_layout.addWidget(self.mnc, 0, 5)
        net_layout.addWidget(QLabel("MNC Length:"), 0, 6)
        net_layout.addWidget(self.mnc_length, 0, 7)
        self.amf_ip = QLineEdit()
        self.amf_ip.setObjectName("amf_ip")
        self.gnb_ip = QLineEdit()
        self.gnb_ip.setObjectName("gnb_ip")
        net_layout.addWidget(QLabel("IP AMF:"), 1, 0)
        net_layout.addWidget(self.amf_ip, 1, 1, 1, 3)
        net_layout.addWidget(QLabel("IP gNB:"), 1, 4, 1, 2)
        net_layout.addWidget(self.gnb_ip, 1, 6, 1, 2)

        self.gnb_port_ngap = QLineEdit()
        self.gnb_port_ngap.setObjectName("gnb_port_ngap")
        self.gnb_port_s1u = QLineEdit()
        self.gnb_port_s1u.setObjectName("gnb_port_s1u")

        net_layout.addWidget(QLabel("Porta gNB NGAP (N2):"), 2, 0)
        net_layout.addWidget(self.gnb_port_ngap, 2, 1, 1, 3)

        net_layout.addWidget(QLabel("Porta gNB S1U (N3):"), 2, 4, 1, 2)
        net_layout.addWidget(self.gnb_port_s1u, 2, 6, 1, 2)

        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("resetButton")
        reset_btn.clicked.connect(lambda: self.reset_section_fields(net_layout))
        net_layout.addWidget(reset_btn, 3, 0, 1, 8)

        net_box.set_content_layout(net_layout)
        self.container_layout.addWidget(net_box)

    def create_hardware_section(self):
        hw_box = CollapsibleBox("Modalità di Esecuzione e Hardware")
        hw_main_layout = QVBoxLayout()

        self.rb_ru = QRadioButton("Hardware Reale (USRP)")
        self.rb_rfsim = QRadioButton("Simulatore RF (rfsim)")
        self.rb_rfsim.setChecked(True)
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.rb_ru)
        radio_layout.addWidget(self.rb_rfsim)
        hw_main_layout.addLayout(radio_layout)

        self.hw_fields_container = QWidget()
        hw_layout = QGridLayout(self.hw_fields_container)

        # --- Riga 0: Antenne (distribuite su 8 colonne per equilibrio) ---
        self.nb_tx = QLineEdit()
        self.nb_tx.setObjectName("nb_tx")
        self.nb_rx = QLineEdit()
        self.nb_rx.setObjectName("nb_rx")
        hw_layout.addWidget(QLabel("Numero Antenne TX:"), 0, 0)
        hw_layout.addWidget(self.nb_tx, 0, 1, 1, 3)
        hw_layout.addWidget(QLabel("Numero Antenne RX:"), 0, 4)
        hw_layout.addWidget(self.nb_rx, 0, 5, 1, 3)

        # --- Riga 1: Attenuazione e Guadagno (distribuite su 8 colonne) ---
        self.att_tx = QLineEdit()
        self.att_tx.setObjectName("att_tx")
        self.att_rx = QLineEdit()
        self.att_rx.setObjectName("att_rx")
        self.max_rxgain = QLineEdit()
        self.max_rxgain.setObjectName("max_rxgain")
        hw_layout.addWidget(QLabel("Attenuazione TX (dB):"), 1, 0)
        hw_layout.addWidget(self.att_tx, 1, 1)
        hw_layout.addWidget(QLabel("Attenuazione RX (dB):"), 1, 2)
        hw_layout.addWidget(self.att_rx, 1, 3)
        hw_layout.addWidget(QLabel("Max RX Gain:"), 1, 4)
        hw_layout.addWidget(self.max_rxgain, 1, 5)

        # --- Riga 2: Indirizzo SDR (si estende su tutta la larghezza) ---
        self.sdr_addrs = QLineEdit()
        self.sdr_addrs.setObjectName("sdr_addrs")
        hw_layout.addWidget(QLabel("Indirizzo SDR (USRP):"), 2, 0)
        hw_layout.addWidget(self.sdr_addrs, 2, 1, 1, 7)  # Occupa le restanti 7 colonne

        # --- Riga 3: Sorgenti Clock e Tempo (distribuite su 8 colonne) ---
        self.clock_src = QComboBox()
        self.clock_src.setObjectName("clock_src")
        self.clock_src.addItems(["", "internal", "external", "gpsdo"])
        self.time_src = QComboBox()
        self.time_src.setObjectName("time_src")
        self.time_src.addItems(["", "internal", "external", "gpsdo"])
        hw_layout.addWidget(QLabel("Sorgente Clock:"), 3, 0)
        hw_layout.addWidget(self.clock_src, 3, 1, 1, 3)  # Occupa 3 colonne
        hw_layout.addWidget(QLabel("Sorgente Tempo:"), 3, 4)
        hw_layout.addWidget(self.time_src, 3, 5, 1, 3)  # Occupa 3 colonne

        # --- Riga 4: Reset ---
        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("resetButton")
        reset_btn.clicked.connect(lambda: self.reset_section_fields(hw_layout))
        hw_layout.addWidget(reset_btn, 4, 0, 1, 8)  # Occupa tutte le 8 colonne

        hw_main_layout.addWidget(self.hw_fields_container)
        hw_box.set_content_layout(hw_main_layout)
        self.container_layout.addWidget(hw_box)

        self.rb_ru.toggled.connect(self.toggle_ru_fields)
        self.toggle_ru_fields()

    def create_radio_config_section(self):
        radio_box = CollapsibleBox("Configurazione Radio (PHY/RF)")
        cell_layout = QGridLayout()

        # --- Riga 1: Banda e SCS ---
        self.nr_band = QLineEdit()
        self.nr_band.setObjectName("nr_band")
        self.scs = QLineEdit()
        self.scs.setObjectName("scs")
        cell_layout.addWidget(QLabel("Banda NR:"), 0, 0)
        cell_layout.addWidget(self.nr_band, 0, 1)
        cell_layout.addWidget(QLabel("SCS (DL/UL):"), 0, 2)
        cell_layout.addWidget(self.scs, 0, 3, 1, 3)

        # --- Riga 2: BW e Frequenze ---
        self.bw = QLineEdit()
        self.bw.setObjectName("bw")
        self.dl_freq_pointA = QLineEdit()
        self.dl_freq_pointA.setObjectName("dl_freq_pointA")
        self.abs_freq_ssb = QLineEdit()
        self.abs_freq_ssb.setObjectName("abs_freq_ssb")
        cell_layout.addWidget(QLabel("BW (DL/UL, in PRB):"), 1, 0)
        cell_layout.addWidget(self.bw, 1, 1)
        cell_layout.addWidget(QLabel("PointA ARFCN:"), 1, 2)
        cell_layout.addWidget(self.dl_freq_pointA, 1, 3)
        cell_layout.addWidget(QLabel("SSB ARFCN:"), 1, 4)
        cell_layout.addWidget(self.abs_freq_ssb, 1, 5)

        # --- Riga 3: BWP e CORESET ---
        self.initial_bwp_riv = QLineEdit()
        self.initial_bwp_riv.setObjectName("initial_bwp_riv")
        self.coreset_zero = QLineEdit()
        self.coreset_zero.setObjectName("coreset_zero")
        cell_layout.addWidget(QLabel("Initial BWP RIV:"), 2, 0)
        cell_layout.addWidget(self.initial_bwp_riv, 2, 1)
        cell_layout.addWidget(QLabel("CORESET#0 Index:"), 2, 2)
        cell_layout.addWidget(self.coreset_zero, 2, 3)

        # --- Riga 4: PRACH ---
        self.prach_index = QLineEdit()
        self.prach_index.setObjectName("prach_index")
        cell_layout.addWidget(QLabel("Indice PRACH:"), 3, 0)
        cell_layout.addWidget(self.prach_index, 3, 1)

        # --- Riga 5 e 6: TDD ---
        self.tdd_period = QLineEdit()
        self.tdd_period.setObjectName("tdd_period")
        self.tdd_dl_slots = QLineEdit()
        self.tdd_dl_slots.setObjectName("tdd_dl_slots")
        self.tdd_dl_sym = QLineEdit()
        self.tdd_dl_sym.setObjectName("tdd_dl_sym")
        self.tdd_ul_slots = QLineEdit()
        self.tdd_ul_slots.setObjectName("tdd_ul_slots")
        self.tdd_ul_sym = QLineEdit()
        self.tdd_ul_sym.setObjectName("tdd_ul_sym")
        cell_layout.addWidget(QLabel("Periodo TDD:"), 4, 0)
        cell_layout.addWidget(self.tdd_period, 4, 1)
        cell_layout.addWidget(QLabel("Slot DL:"), 4, 2)
        cell_layout.addWidget(self.tdd_dl_slots, 4, 3)
        cell_layout.addWidget(QLabel("Simboli DL:"), 4, 4)
        cell_layout.addWidget(self.tdd_dl_sym, 4, 5)
        cell_layout.addWidget(QLabel("Slot UL:"), 5, 0)
        cell_layout.addWidget(self.tdd_ul_slots, 5, 1)
        cell_layout.addWidget(QLabel("Simboli UL:"), 5, 2)
        cell_layout.addWidget(self.tdd_ul_sym, 5, 3)

        # --- Riga 7: Reset Button ---
        reset_btn = QPushButton("Reset")
        reset_btn.setObjectName("resetButton")
        reset_btn.clicked.connect(lambda: self.reset_section_fields(cell_layout))
        cell_layout.addWidget(reset_btn, 6, 0, 1, 6)

        radio_box.set_content_layout(cell_layout)
        self.container_layout.addWidget(radio_box)

    def create_metrics_section(self):
        metrics_box = CollapsibleBox("Metriche UE in Tempo Reale")
        metrics_layout = QGridLayout()

        # Creazione delle etichette per i valori
        self.lbl_rsrp = QLabel("N/A")
        self.lbl_snr = QLabel("N/A")
        self.lbl_bler_dl = QLabel("N/A")
        self.lbl_bler_ul = QLabel("N/A")
        self.lbl_throughput_dl = QLabel("N/A")
        self.lbl_throughput_ul = QLabel("N/A")
        self.lbl_mcs_dl = QLabel("N/A")
        self.lbl_mcs_ul = QLabel("N/A")

        # Applica lo stile per far risaltare i valori
        for label in [self.lbl_rsrp, self.lbl_snr, self.lbl_bler_dl, self.lbl_bler_ul,
                      self.lbl_throughput_dl, self.lbl_throughput_ul, self.lbl_mcs_dl, self.lbl_mcs_ul]:
            label.setObjectName("metricValue")

        # Layout a griglia per le metriche
        metrics_layout.addWidget(QLabel("RSRP:"), 0, 0)
        metrics_layout.addWidget(self.lbl_rsrp, 0, 1)
        metrics_layout.addWidget(QLabel("SNR (UL):"), 0, 2)
        metrics_layout.addWidget(self.lbl_snr, 0, 3)

        metrics_layout.addWidget(QLabel("BLER (DL %):"), 1, 0)
        metrics_layout.addWidget(self.lbl_bler_dl, 1, 1)
        metrics_layout.addWidget(QLabel("BLER (UL %):"), 1, 2)
        metrics_layout.addWidget(self.lbl_bler_ul, 1, 3)

        metrics_layout.addWidget(QLabel("Throughput DL:"), 2, 0)
        metrics_layout.addWidget(self.lbl_throughput_dl, 2, 1)
        metrics_layout.addWidget(QLabel("Throughput UL:"), 2, 2)
        metrics_layout.addWidget(self.lbl_throughput_ul, 2, 3)

        metrics_layout.addWidget(QLabel("MCS (DL):"), 3, 0)
        metrics_layout.addWidget(self.lbl_mcs_dl, 3, 1)
        metrics_layout.addWidget(QLabel("MCS (UL):"), 3, 2)
        metrics_layout.addWidget(self.lbl_mcs_ul, 3, 3)

        # Pulsante per salvare
        self.btn_save_metrics = QPushButton("Salva Metriche su File (.CSV)")
        self.btn_save_metrics.setObjectName("config")
        self.btn_save_metrics.clicked.connect(self.save_metrics_to_file)
        metrics_layout.addWidget(self.btn_save_metrics, 4, 0, 1, 4)

        metrics_box.set_content_layout(metrics_layout)
        self.container_layout.addWidget(metrics_box)

    def create_charts_section(self):
        charts_box = CollapsibleBox("Grafici in Tempo Reale")
        charts_layout = QVBoxLayout()

        x_axis_label = "Campioni Temporali"

        # Grafico 1: RSRP
        self.plot_rsrp = pg.PlotWidget()
        self.plot_rsrp.setMinimumHeight(200)
        self.plot_rsrp.addLegend()
        self.plot_rsrp.setLabel('left', 'RSRP (dBm)')
        self.plot_rsrp.setLabel('bottom', x_axis_label)
        self.plot_rsrp.showGrid(x=True, y=True)
        self.rsrp_line = self.plot_rsrp.plot(pen=pg.mkPen(color='#FFD700', width=2), name="RSRP")
        charts_layout.addWidget(self.plot_rsrp)

        # Grafico 2: SNR
        self.plot_snr = pg.PlotWidget()
        self.plot_snr.setMinimumHeight(200)
        self.plot_snr.addLegend()
        self.plot_snr.setLabel('left', 'SNR (dB)')
        self.plot_snr.setLabel('bottom', x_axis_label)
        self.plot_snr.showGrid(x=True, y=True)
        self.snr_line = self.plot_snr.plot(pen=pg.mkPen(color='#00FFFF', width=2), name="SNR")
        charts_layout.addWidget(self.plot_snr)

        # Grafico 3: BLER (DL vs UL)
        self.plot_bler = pg.PlotWidget()
        self.plot_bler.setMinimumHeight(200)
        self.plot_bler.addLegend()
        self.plot_bler.setLabel('left', 'BLER (%)')
        self.plot_bler.setLabel('bottom', x_axis_label)
        self.plot_bler.showGrid(x=True, y=True)
        self.bler_dl_line = self.plot_bler.plot(pen=pg.mkPen(color='#FF6347', width=2), name="BLER DL")
        self.bler_ul_line = self.plot_bler.plot(pen=pg.mkPen(color='#1E90FF', width=2), name="BLER UL")
        charts_layout.addWidget(self.plot_bler)

        charts_box.set_content_layout(charts_layout)
        self.container_layout.addWidget(charts_box)

    @Slot(dict)
    def update_metrics_display(self, metrics):

        # Aggiornamento Etichette
        self.lbl_rsrp.setText(metrics.get("rsrp", self.lbl_rsrp.text()))
        self.lbl_snr.setText(metrics.get("snr", self.lbl_snr.text()))
        self.lbl_bler_dl.setText(metrics.get("bler_dl", self.lbl_bler_dl.text()))
        self.lbl_bler_ul.setText(metrics.get("bler_ul", self.lbl_bler_ul.text()))
        self.lbl_throughput_dl.setText(metrics.get("throughput_dl", self.lbl_throughput_dl.text()))
        self.lbl_throughput_ul.setText(metrics.get("throughput_ul", self.lbl_throughput_ul.text()))
        self.lbl_mcs_dl.setText(metrics.get("mcs_dl", self.lbl_mcs_dl.text()))
        self.lbl_mcs_ul.setText(metrics.get("mcs_ul", self.lbl_mcs_ul.text()))

        # Aggiornamento Dati per i Grafici
        self.time_axis.append(len(self.time_axis) + 1)

        def extract_float(value_str):
            try:
                return float(re.search(r'(-?[\d\.]+)', value_str).group(1))
            except (AttributeError, ValueError):
                return None

        # Aggiunge i nuovi dati o ripete l'ultimo valore valido
        last_rsrp = self.rsrp_data[-1] if self.rsrp_data else None
        self.rsrp_data.append(extract_float(metrics.get("rsrp", "")) or last_rsrp)

        last_snr = self.snr_data[-1] if self.snr_data else None
        self.snr_data.append(extract_float(metrics.get("snr", "")) or last_snr)

        last_bler_dl = self.bler_dl_data[-1] if self.bler_dl_data else None
        self.bler_dl_data.append(extract_float(metrics.get("bler_dl", "")) or last_bler_dl)

        last_bler_ul = self.bler_ul_data[-1] if self.bler_ul_data else None
        self.bler_ul_data.append(extract_float(metrics.get("bler_ul", "")) or last_bler_ul)

        # Aggiorna le linee dei grafici
        self.rsrp_line.setData(self.time_axis, self.rsrp_data)
        self.snr_line.setData(self.time_axis, self.snr_data)
        self.bler_dl_line.setData(self.time_axis, self.bler_dl_data)
        self.bler_ul_line.setData(self.time_axis, self.bler_ul_data)

    def save_metrics_to_file(self):
        if not self.metrics_history:
            self.new_log_message.emit("[GUI] Nessuna metrica da salvare.")
            return

        default_filename = f"metriche_gnb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Salva Metriche", default_filename, "CSV Files (*.csv)")

        if file_path:
            try:
                # Raccoglie tutte le possibili intestazioni da tutta la cronologia
                all_keys = set()
                for entry in self.metrics_history:
                    all_keys.update(entry.keys())

                # Ordina le intestazioni (timestamp prima, le altre in ordine alfabetico)
                headers = sorted(list(all_keys))
                if 'timestamp' in headers:
                    headers.insert(0, headers.pop(headers.index('timestamp')))

                with open(file_path, 'w', newline='') as f:
                    # Usa il modulo csv per gestire correttamente i dati
                    import csv
                    writer = csv.writer(f)
                    writer.writerow(headers)  # Scrive l'intestazione

                    # Scrive ogni riga di dati
                    for entry in self.metrics_history:
                        row = [entry.get(h, '') for h in headers]
                        writer.writerow(row)

                self.new_log_message.emit(f"[GUI] Metriche salvate con successo in: {file_path}")
            except Exception as e:
                self.new_log_message.emit(f"[GUI] Errore nel salvataggio del file: {e}")

    def toggle_ru_fields(self):
        is_hw_mode = self.rb_ru.isChecked()
        self.hw_fields_container.setVisible(is_hw_mode)

    def select_config_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona file di configurazione", "",
                                                   "Config Files (*.conf)")
        if file_path:
            try:
                # Legge il contenuto del file e lo salva in una variabile.
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.config_file_content = f.read()
                file_name = os.path.basename(file_path)
                self.new_log_message.emit(f"[GUI] File base '{file_name}' caricato con successo.")
                self.new_log_message.emit(f"[GUI] Le impostazioni della GUI lo sovrascriveranno dove specificato.")
            except Exception as e:
                # In caso di errore, resetta e informa l'utente.
                self.config_file_content = None
                self.new_log_message.emit(f"[GUI] Errore nella lettura del file: {e}")

    def collect_params(self):
        params = {}
        widgets_to_collect = self.findChildren(QLineEdit) + self.findChildren(QComboBox)

        for widget in widgets_to_collect:
            if isinstance(widget, QLineEdit):
                if widget.text().strip():
                    params[widget.objectName()] = widget.text().strip()
            elif isinstance(widget, QComboBox):
                if widget.currentText():
                    params[widget.objectName()] = widget.currentText()

        if self.rb_rfsim.isChecked():
            params['use_rfsim'] = 'true'
        else:
            params['use_rfsim'] = 'false'
        return params

    def handle_start(self):
        if self.gnb_is_running:
            self.new_log_message.emit("[GUI] gNB è già in esecuzione. Premere Stop prima di riavviare.")
            return

        self.log_area.clear()
        self.metrics_history = []

        self.time_axis.clear()
        self.rsrp_data.clear()
        self.snr_data.clear()
        self.bler_dl_data.clear()
        self.bler_ul_data.clear()

        self.rsrp_line.setData([], [])
        self.snr_line.setData([], [])
        self.bler_dl_line.setData([], [])
        self.bler_ul_line.setData([], [])

        password, ok = QInputDialog.getText(self, "Password sudo", "Inserisci password sudo:", echo=QLineEdit.Password)
        if not ok or not password:
            self.new_log_message.emit("Avvio annullato: password non fornita.")
            return

        base_config_to_send = self.config_file_content if self.config_file_content else ""

        params_dict = self.collect_params()
        params_json = json.dumps(params_dict)

        command = f"START::{password}::{params_json}::{base_config_to_send}"

        self.gnb_is_running = True
        threading.Thread(target=self.send_command, args=(command,), daemon=True).start()

    def handle_stop(self):
        if not self.gnb_is_running:
            self.new_log_message.emit("[GUI] Nessuna gNB in esecuzione da arrestare.")
            return

        # Controlla se sono state raccolte delle metriche
        if self.metrics_history:
            # Crea il popup di domanda
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Salvare le Metriche?")
            dialog.setWindowIcon(self.windowIcon())
            dialog.setText("Sono state raccolte delle metriche durante l'esecuzione.")
            dialog.setInformativeText("Vuoi salvarle in un file CSV prima di arrestare la gNB?")
            dialog.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            dialog.setDefaultButton(QMessageBox.Save)

            # Mostra il popup e cattura la risposta
            risposta = dialog.exec()

            if risposta == QMessageBox.Save:
                # Se l'utente clicca 'Salva', chiama la funzione di salvataggio
                self.save_metrics_to_file()
            elif risposta == QMessageBox.Cancel:
                # Se l'utente clicca 'Annulla', non fare nulla e non fermare la gNB
                self.new_log_message.emit("[GUI] Arresto annullato dall'utente.")
                return
                # Se l'utente clicca 'Discard' (Ignora), il codice prosegue e ferma la gNB senza salvare

        # Resetta le etichette della GUI
        for label in [self.lbl_rsrp, self.lbl_snr, self.lbl_bler_dl, self.lbl_bler_ul,
                      self.lbl_throughput_dl, self.lbl_throughput_ul, self.lbl_mcs_dl, self.lbl_mcs_ul]:
            label.setText("N/A")

        # Avvia il comando di stop in un thread separato
        threading.Thread(target=self.send_command, args=("STOP",), daemon=True).start()

    def send_command(self, command):
        try:
            self.req_socket.send_string(command)
            response = self.req_socket.recv_string()
            self.new_log_message.emit(response)
            if "arrestato" in response or "Errore" in response:
                self.gnb_is_running = False
        except Exception as e:
            self.new_log_message.emit(f"Errore comunicazione server: {e}")
            self.gnb_is_running = False

    def receive_logs(self):
        current_metrics = {}

        # Variabili di stato per il calcolo del throughput
        last_mac_stats = {'time': 0, 'tx_bytes': 0, 'rx_bytes': 0}

        def format_throughput(bits_per_second):
            if bits_per_second < 1000:
                return f"{bits_per_second:.2f} bps"
            elif bits_per_second < 1000000:
                return f"{bits_per_second / 1000:.2f} kbps"
            else:
                return f"{bits_per_second / 1000000:.2f} Mbps"

        while True:
            try:
                msg = self.sub_socket.recv_string()
                self.new_log_message.emit(msg)

                if "Processo nr-softmodem terminato" in msg or "gNB arrestato" in msg:
                    self.gnb_is_running = False
                    last_mac_stats = {'time': 0, 'tx_bytes': 0, 'rx_bytes': 0}
                    current_metrics = {}
                    continue  # Salta il resto del ciclo

                if not self.gnb_is_running:
                    continue

                # Le metriche vengono accumulate nel dizionario 'current_metrics'

                if "average RSRP" in msg:
                    match = re.search(r'average RSRP (-?\d+)', msg)
                    if match:
                        current_metrics["rsrp"] = f"{match.group(1)} dBm"

                if "dlsch_rounds" in msg:
                    match = re.search(r'dlsch_rounds ([\d/]+).*BLER ([\d\.]+).*MCS \((\d+)\).*CCE fail (\d+)', msg)
                    if match:
                        current_metrics["harq_dl"] = match.group(1).replace('/', '-')
                        current_metrics["bler_dl"] = f"{float(match.group(2)) * 100:.2f}"
                        current_metrics["mcs_dl"] = match.group(3)
                        current_metrics["cce_fail_dl"] = match.group(4)

                if "ulsch_rounds" in msg:
                    match = re.search(
                        r'ulsch_rounds ([\d/]+).*BLER ([\d\.]+).*MCS \((\d+)\).*SNR ([\d\.]+) dB.*CCE fail (\d+)', msg)
                    if match:
                        current_metrics["harq_ul"] = match.group(1).replace('/', '-')
                        current_metrics["bler_ul"] = f"{float(match.group(2)) * 100:.2f}"
                        current_metrics["mcs_ul"] = match.group(3)
                        current_metrics["snr"] = f"{match.group(4)} dB"
                        current_metrics["cce_fail_ul"] = match.group(5)

                # La riga MAC è l'ultima del blocco, quindi la si usa per salvare i dati raccolti.
                if "MAC:    TX" in msg:
                    match = re.search(r'MAC:\s+TX\s+(\d+)\s+RX\s+(\d+)\s+bytes', msg)
                    if match:
                        current_time = time.time()
                        tx_bytes_total = int(match.group(1))
                        rx_bytes_total = int(match.group(2))

                        # Calcola il throughput
                        if last_mac_stats['time'] > 0:
                            delta_time = current_time - last_mac_stats['time']
                            if delta_time > 0:
                                delta_tx = tx_bytes_total - last_mac_stats['tx_bytes']
                                throughput_ul_bps = (delta_tx * 8) / delta_time
                                current_metrics["throughput_ul"] = format_throughput(throughput_ul_bps)

                                delta_rx = rx_bytes_total - last_mac_stats['rx_bytes']
                                throughput_dl_bps = (delta_rx * 8) / delta_time
                                current_metrics["throughput_dl"] = format_throughput(throughput_dl_bps)

                        last_mac_stats['time'] = current_time
                        last_mac_stats['tx_bytes'] = tx_bytes_total
                        last_mac_stats['rx_bytes'] = rx_bytes_total

                        # Ora che si hanno tutte le metriche, si crea e salva lo snapshot
                        if current_metrics:
                            snapshot = {"timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}
                            snapshot.update(current_metrics)

                            self.metrics_history.append(snapshot)
                            self.new_metrics_data.emit(current_metrics)

                            # Resetta per il prossimo ciclo di raccolta
                            current_metrics = {}

            except Exception:
                pass

    @Slot(str)
    def append_log(self, msg):
        self.log_area.append(msg)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())

    def show_info(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Info parametri gNB")
        dialog.setMinimumSize(700, 600)
        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(
            "\t\t\t*** INFORMAZIONI ***\n\n"
            "Questo tool permette di configurare e lanciare una gNB OpenAirInterface in due modalità:\n\n"
            "1.  **Da Zero (Default):** All'avvio i campi sono pre-compilati con valori di default.\n"
            "    Modifica i campi desiderati e clicca 'Avvia'.\n\n"
            "2.  **Da File Esistente:** Seleziona un file di configurazione (.conf) come base.\n"
            "    Puoi svuotare i campi pre-compilati con il pulsante 'Reset Generale'.\n"
            "    I campi che compilerai nella GUI sovrascriveranno i valori presenti nel file base.\n\n"
            "------------------------------------------------------------------------------\n"
            "=== Informazioni gNB ===\n\n"
            "ID gNB: gNB_ID\n"
            "  Identificativo univoco della gNB (esadecimale).\n\n"
            "Nome gNB: gNB_name, Active_gNBs\n"
            "  Nome descrittivo della gNB.\n\n"

            "=== Parametri di Rete e Connessione ===\n\n"
            "TAC (Tracking Area Code): tracking_area_code\n"
            "  Tracking Area Code (codice area di copertura della gNB).\n\n"
            "MCC: plmn_list.mcc\n"
            "  Mobile Country Code (codice paese).\n\n"
            "MNC: plmn_list.mnc\n"
            "  Mobile Network Code (codice rete).\n\n"
            "MNC Length: plmn_list.mnc_length\n"
            "  Lunghezza del MNC (2 o 3 cifre).\n\n"
            "IP AMF: amf_ip_address.ipv4\n"
            "  Indirizzo IPv4 dell’AMF a cui la gNB si connette.\n\n"
            "IP gNB: NETWORK_INTERFACES.GNB_IPV4_ADDRESS_FOR_NG_AMF / GNB_IPV4_ADDRESS_FOR_NGU\n"
            "  Indirizzo IP di origine della gNB usato per il piano di controllo e utente.\n\n"
            "Porta gNB NGAP (N2): NETWORK_INTERFACES.GNB_PORT_FOR_NG_AMF\n"
            "  Porta di origine della gNB per la comunicazione di controllo (N2) con l'AMF (default: 38412).\n\n"
            "Porta gNB S1U (N3): NETWORK_INTERFACES.GNB_PORT_FOR_S1U / GNB_PORT_FOR_NGU\n"
            "  Porta di origine della gNB per il traffico dati utente (N3) verso la UPF (default: 2152).\n\n"

            "=== Modalità di Esecuzione e Hardware ===\n\n"
            "Hardware Reale (USRP) / Simulatore RF (rfsim): RUs.local_rf / --rfsim\n"
            "  Se usare unità radio reale (SDR) o il simulatore software.\n\n"
            "Numero Antenne TX/RX: RUs.nb_tx / RUs.nb_rx\n"
            "  Numero di trasmettitori e ricevitori (per la modalità hardware).\n\n"
            "Attenuazione TX/RX (dB): RUs.att_tx / RUs.att_rx\n"
            "  Attenuazione in dB (per la modalità hardware).\n\n"
            "Max RX Gain: RUs.max_rxgain\n"
            "  Guadagno massimo del ricevitore in dB (specifico per l'hardware SDR).\n\n"
            "Indirizzo SDR (USRP): RUs.sdr_addrs\n"
            "  Argomenti per il driver UHD (es. 'addr=192.168.10.2').\n\n"
            "Sorgente Clock / Tempo: RUs.clock_src / RUs.time_src\n"
            "  Sorgente di sincronizzazione per il clock e il tempo dell'hardware SDR (internal, external, gpsdo).\n\n"

            "=== Configurazione Radio (PHY/RF) ===\n\n"
            "Banda NR: servingCellConfigCommon.dl_frequencyBand, ul_frequencyBand, RUs.bands\n"
            "  Banda NR della cella (es. 77, 78).\n\n"
            "SCS DL/UL: servingCellConfigCommon.dl_subcarrierSpacing / ul_subcarrierSpacing\n"
            "  Subcarrier spacing (0=15kHz, 1=30kHz, etc.).\n\n"
            "BW DL/UL (PRB): servingCellConfigCommon.dl_carrierBandwidth / ul_carrierBandwidth\n"
            "  Larghezza di banda in numero di Physical Resource Blocks.\n\n"
            "PointA ARFCN: servingCellConfigCommon.dl_absoluteFrequencyPointA\n"
            "  Frequenza assoluta del punto A della portante (riferimento).\n\n"
            "SSB ARFCN: servingCellConfigCommon.absoluteFrequencySSB\n"
            "  Frequenza assoluta del blocco di sincronizzazione.\n\n"
            "CORESET#0 Index: servingCellConfigCommon.initialDLBWPcontrolResourceSetZero\n"
            "  Indice della configurazione del primo set di risorse di controllo.\n\n"
            "Initial BWP RIV (DL/UL): initialDLBWPlocationAndBandwidth / initialULBWPlocationAndBandwidth\n"
            "  Resource Indication Value per la Bandwidth Part iniziale.\n\n"
            "Indice PRACH: prach_ConfigurationIndex\n"
            "  Indice della configurazione del canale di accesso (Random Access).\n\n"
            "Periodo TDD: dl_UL_TransmissionPeriodicity\n"
            "  Periodicità dello schema TDD (es. 6 = 5ms).\n\n"
            "Slot/Simboli DL/UL: nrofDownlinkSlots, nrofDownlinkSymbols, etc.\n"
            "  Parametri che definiscono la struttura dello slot TDD.\n\n"

            "------------------------------------------------------------------------------\n\n"
            "Per dettagli più approfonditi consultare la documentazione OAI:\n\n"
            "https://gitlab.eurecom.fr/oai/openairinterface5g/-/blob/develop/doc/gNB_frequency_setup.md\n\n"
            "https://gitlab.eurecom.fr/oai/openairinterface5g/-/tree/develop/radio/USRP\n"
        )
        layout.addWidget(text_edit)
        dialog.exec()

    def show_startup_tutorial(self):

        titolo = "Benvenuto nel Tool di Gestione gNB!"

        testo_informativo = """
        <h3>Come usare questo Tool:</h3>
        <p>Ci sono due modalità principali per configurare e avviare la gNB:</p>

        <p><b>1. Modalità con Valori di Default:</b></p>
        <ul>
            <li>All'avvio, i campi sono già compilati con valori standard.</li>
            <li>Modifica solo i campi che desideri personalizzare e premi <b>Avvia</b>.</li>
            <li>Il tool userà i valori che vedi nella GUI per generare la configurazione.</li>
        </ul>

        <p><b>2. Modalità da File Esistente:</b></p>
        <ul>
            <li>Usa il pulsante <b>"Seleziona file base"</b> per caricare un tuo file <code>.conf</code>.</li>
            <li><b>IMPORTANTE:</b> Dopo aver caricato il file, premi il pulsante <b>"Reset Generale"</b> in alto.</li>
            <li>Questo svuoterà tutti i campi, garantendo che vengano usati solo i valori del tuo file e che i default della GUI non li sovrascrivano accidentalmente.</li>
            <li>Se vuoi comunque sovrascrivere un parametro specifico del tuo file, puoi compilare il campo corrispondente <em>dopo</em> aver resettato.</li>
        </ul>

        <p>Una volta configurato, premi <b>Avvia</b> e inserisci la password <code>sudo</code> quando richiesta per lanciare la gNB.</p>
        """

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Guida Rapida")
        dialog.setWindowIcon(self.windowIcon())
        dialog.setText(titolo)
        dialog.setInformativeText(testo_informativo)
        dialog.setTextFormat(Qt.RichText)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.setDefaultButton(QMessageBox.Ok)

        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Attenzione: file style.qss non trovato. Lo stile non sarà applicato.")
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())