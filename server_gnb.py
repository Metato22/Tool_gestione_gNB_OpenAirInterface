import zmq
import subprocess
import os
import signal
import threading
import json
import re
import atexit

# Configurazione Percorsi
OAI_DIR = os.path.expanduser("~/openairinterface5g")
OAI_BUILD_DIR = os.path.join(OAI_DIR, "cmake_targets", "ran_build", "build")
OAI_CONF_DIR = os.path.join(OAI_DIR, "targets", "PROJECTS", "GENERIC-NR-5GC", "CONF")
OAI_EXECUTABLE_NAME = "nr-softmodem"
TEMP_CONFIG_FILENAME = "temp_config.conf"
TEMP_CONFIG_FULL_PATH = os.path.join(OAI_CONF_DIR, TEMP_CONFIG_FILENAME)

# Template di Configurazione di Default
DEFAULT_CONFIG_TEMPLATE = """
// File di configurazione di base basato su file stabili e moderni di OAI.
Active_gNBs = ( "gNB-OAI");
# Asn1_verbosity, choice in: none, info, annoying
Asn1_verbosity = "none";

gNBs =
(
 {
    ////////// Identification parameters:
    gNB_ID    =  0xe00;
    gNB_name  =  "gNB-OAI";

    // Tracking area code, 0x0000 and 0xfffe are reserved values
    tracking_area_code  =  1;
    plmn_list = ({ mcc = 001; mnc = 01; mnc_length = 2; snssaiList = ({ sst = 1; }) });

    nr_cellid = 12345678L;

    ////////// Physical parameters:
	min_rxtxtime = 6;
    do_CSIRS                                                  = 1;
    do_SRS                                                    = 1;

    #uess_agg_levels = [0,1,2,2,1]
    servingCellConfigCommon = (
    {
 #spCellConfigCommon

      physCellId                                                    = 0;

#  downlinkConfigCommon
    #frequencyInfoDL
      # this is 3600 MHz + 43 PRBs@30kHz SCS (same as initial BWP)
      absoluteFrequencySSB                                             = 641280;
      dl_frequencyBand                                                 = 78;
      # this is 3600 MHz
      dl_absoluteFrequencyPointA                                       = 640008;
      #scs-SpecificCarrierList
        dl_offstToCarrier                                              = 0;
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120
        dl_subcarrierSpacing                                           = 1;
        dl_carrierBandwidth                                            = 106;
     #initialDownlinkBWP
      #genericParameters
        # this is RBstart=27,L=48 (275*(L-1))+RBstart
        initialDLBWPlocationAndBandwidth                               = 28875; # 6366 12925 12956 28875 12952
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120
        initialDLBWPsubcarrierSpacing                                   = 1;
      #pdcch-ConfigCommon
        initialDLBWPcontrolResourceSetZero                              = 12;
        initialDLBWPsearchSpaceZero                                     = 0;

  #uplinkConfigCommon
     #frequencyInfoUL
      ul_frequencyBand                                              = 78;
      #scs-SpecificCarrierList
      ul_offstToCarrier                                             = 0;
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120
      ul_subcarrierSpacing                                          = 1;
      ul_carrierBandwidth                                           = 106;
      pMax                                                          = 20;
     #initialUplinkBWP
      #genericParameters
        initialULBWPlocationAndBandwidth                            = 28875;
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120
        initialULBWPsubcarrierSpacing                               = 1;
      #rach-ConfigCommon
        #rach-ConfigGeneric
          prach_ConfigurationIndex                                  = 98;
#prach_msg1_FDM
#0 = one, 1=two, 2=four, 3=eight
          prach_msg1_FDM                                            = 0;
          prach_msg1_FrequencyStart                                 = 0;
          zeroCorrelationZoneConfig                                 = 13;
          preambleReceivedTargetPower                               = -96;
#preamblTransMax (0...10) = (3,4,5,6,7,8,10,20,50,100,200)
          preambleTransMax                                          = 6;
#powerRampingStep
# 0=dB0,1=dB2,2=dB4,3=dB6
        powerRampingStep                                            = 1;
#ssb_perRACH_OccasionAndCB_PreamblesPerSSB_PR
#1=oneeighth,2=onefourth,3=half,4=one,5=two,6=four,7=eight,8=sixteen
        ssb_perRACH_OccasionAndCB_PreamblesPerSSB_PR                = 4;
#one (0..15) 4,8,12,16,...60,64
        ssb_perRACH_OccasionAndCB_PreamblesPerSSB                   = 14;
#ra_ContentionResolutionTimer
#(0..7) 8,16,24,32,40,48,56,64
        ra_ContentionResolutionTimer                                = 7;
        rsrp_ThresholdSSB                                           = 19;
#prach-RootSequenceIndex_PR
#1 = 839, 2 = 139
        prach_RootSequenceIndex_PR                                  = 2;
        prach_RootSequenceIndex                                     = 1;
        # SCS for msg1, can only be 15 for 30 kHz < 6 GHz, takes precendence over the one derived from prach-ConfigIndex
        #
        msg1_SubcarrierSpacing                                      = 1,
# restrictedSetConfig
# 0=unrestricted, 1=restricted type A, 2=restricted type B
        restrictedSetConfig                                         = 0,

        msg3_DeltaPreamble                                          = 1;
        p0_NominalWithGrant                                         =-90;

# pucch-ConfigCommon setup :
# pucchGroupHopping
# 0 = neither, 1= group hopping, 2=sequence hopping
        pucchGroupHopping                                           = 0;
        hoppingId                                                   = 40;
        p0_nominal                                                  = -90;

      ssb_PositionsInBurst_Bitmap                                   = 1;

# ssb_periodicityServingCell
# 0 = ms5, 1=ms10, 2=ms20, 3=ms40, 4=ms80, 5=ms160, 6=spare2, 7=spare1
      ssb_periodicityServingCell                                    = 2;

# dmrs_TypeA_position
# 0 = pos2, 1 = pos3
      dmrs_TypeA_Position                                           = 0;

# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120
      subcarrierSpacing                                             = 1;


  #tdd-UL-DL-ConfigurationCommon
# subcarrierSpacing
# 0=kHz15, 1=kHz30, 2=kHz60, 3=kHz120
      referenceSubcarrierSpacing                                    = 1;
      # pattern1
      # dl_UL_TransmissionPeriodicity
      # 0=ms0p5, 1=ms0p625, 2=ms1, 3=ms1p25, 4=ms2, 5=ms2p5, 6=ms5, 7=ms10
      dl_UL_TransmissionPeriodicity                                 = 6;
      nrofDownlinkSlots                                             = 7;
      nrofDownlinkSymbols                                           = 6;
      nrofUplinkSlots                                               = 2;
      nrofUplinkSymbols                                             = 4;

      ssPBCH_BlockPower                                             = -25;
  }

  );


    # ------- SCTP definitions
    SCTP :
    {
        # Number of streams to use in input/output
        SCTP_INSTREAMS  = 2;
        SCTP_OUTSTREAMS = 2;
    };


    ////////// AMF parameters:
    amf_ip_address = ({ ipv4 = "192.168.70.132"; });


    NETWORK_INTERFACES :
    {
        GNB_IPV4_ADDRESS_FOR_NG_AMF              = "192.168.70.129/24";
        GNB_IPV4_ADDRESS_FOR_NGU                 = "192.168.70.129/24";
        GNB_PORT_FOR_NG_AMF                      = 38412;
        GNB_PORT_FOR_S1U                         = 2152; # Spec 2152
    };

  }
);

MACRLCs = (
{
  num_cc                      = 1;
  tr_s_preference             = "local_L1";
  tr_n_preference             = "local_RRC";
  pusch_TargetSNRx10          = 150;
  pucch_TargetSNRx10          = 200;
}
);

L1s = (
{
  num_cc = 1;
  tr_n_preference       = "local_mac";
  prach_dtx_threshold   = 120;
  pucch0_dtx_threshold  = 100;
  ofdm_offset_divisor   = 8; #set this to UINT_MAX for offset 0
}
);

RUs = (
{
  local_rf       = "yes";
  nb_tx          = 2;
  nb_rx          = 2;
  att_tx         = 0;
  att_rx         = 0;
  bands          = [78];
  max_pdschReferenceSignalPower = -27;
  max_rxgain                    = 75;
  eNB_instances  = [0];
  sdr_addrs = "addr=";
  clock_src = "external";
  time_src  = "external";
  tx_subdev ="A:0 B:0";
  rx_subdev ="A:1 B:1";
}
);



rfsimulator :
{
  serveraddr = "server";
  serverport = 4043;
  options = (); #("saviq"); or/and "chanmod"
  modelname = "AWGN";
  IQfile = "/tmp/rfsimulator.iqs";
};

security = {
  # preferred ciphering algorithms
  # the first one of the list that an UE supports in chosen
  # valid values: nea0, nea1, nea2, nea3
  ciphering_algorithms = ( "nea0" );

  # preferred integrity algorithms
  # the first one of the list that an UE supports in chosen
  # valid values: nia0, nia1, nia2, nia3
  integrity_algorithms = ( "nia2", "nia0" );

  # setting 'drb_ciphering' to "no" disables ciphering for DRBs, no matter
  # what 'ciphering_algorithms' configures; same thing for 'drb_integrity'
  drb_ciphering = "yes";
  drb_integrity = "no";
};

log_config :
{
  global_log_level                      ="info";
  hw_log_level                          ="info";
  phy_log_level                         ="info";
  mac_log_level                         ="info";
  rlc_log_level                         ="info";
  pdcp_log_level                        ="info";
  rrc_log_level                         ="info";
  ngap_log_level                        ="debug";
  f1ap_log_level                        ="debug";
};

e2_agent = {
  near_ric_ip_addr = "127.0.0.1";
  #sm_dir = "/path/where/the/SMs/are/located/"
  sm_dir = "/usr/local/lib/flexric/"
};
"""

# Configurazione ZeroMQ e Variabili Globali
context = zmq.Context()
rep_socket = context.socket(zmq.REP)
rep_socket.bind("tcp://*:5555")
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://*:5556")
gnb_process = None
print(f"[SERVER] Server gNB pronto su porta 5555. Directory di lavoro: {OAI_BUILD_DIR}")


# Funzioni Helper
def cleanup():
    if gnb_process and gnb_process.poll() is None:
        print("[SERVER] Eseguo pulizia: arresto processo gNB...")
        try:
            os.killpg(os.getpgid(gnb_process.pid), signal.SIGTERM)
            gnb_process.wait(timeout=2)
        except:
            os.killpg(os.getpgid(gnb_process.pid), signal.SIGKILL)
    if os.path.exists(TEMP_CONFIG_FULL_PATH):
        try:
            os.remove(TEMP_CONFIG_FULL_PATH)
            print(f"[SERVER] File temporaneo '{TEMP_CONFIG_FILENAME}' cancellato.")
        except OSError as e:
            print(f"[SERVER] Errore nella cancellazione del file temporaneo: {e}")


atexit.register(cleanup)


def publish_logs(process):
    for line in iter(process.stdout.readline, b''):
        if not line: break
        try:
            decoded_line = line.decode('utf-8', errors='ignore').rstrip()
            pub_socket.send_string(decoded_line)
        except Exception:
            pass
    process.stdout.close()
    ret = process.wait()
    final_msg = f"[SERVER] Processo nr-softmodem terminato con codice {ret}"
    print(final_msg)
    pub_socket.send_string(final_msg)

def create_modified_config(base_content, temp_path, params):
    content = base_content

    try:
        # --- SEZIONE 1: GESTIONE DEI PARAMETRI UNIFICATI ---

        if 'gnb_name' in params:
            val = params.pop('gnb_name')
            print(f"[SERVER] Modifico gnb_name (unificato) in: {val}")
            # Riga 1: Active_gNBs
            content = re.sub(r'(\s*Active_gNBs\s*=\s*\(\s*)".*?"(\s*\);)', r'\g<1>"{}"\g<2>'.format(val), content,
                             count=1)
            # Riga 2: gNB_name
            content = re.sub(r'(\s*gNB_name\s*=\s*)".*?"(\s*;)', r'\g<1>"{}"\g<2>'.format(val), content, count=1)

        if 'gnb_ip' in params:
            val = params.pop('gnb_ip')
            print(f"[SERVER] Modifico gnb_ip (unificato) in: {val}")
            ip_only = val.split('/')[0]
            # Si assicura di gestire anche i file che non hanno la subnet mask
            content = re.sub(r'(GNB_IPV4_ADDRESS_FOR_NG_AMF\s*=\s*)"[^"]+"', r'\g<1>"{}"'.format(ip_only), content)
            content = re.sub(r'(GNB_IPV4_ADDRESS_FOR_NGU\s*=\s*)"[^"]+"', r'\g<1>"{}"'.format(ip_only), content)

        if 'nr_band' in params:
            val = params.pop('nr_band')
            print(f"[SERVER] Modifico nr_band (unificato) in: {val}")
            content = re.sub(r'(\s*dl_frequencyBand\s*=\s*)\d+;?', r'\g<1>{};'.format(val), content)
            content = re.sub(r'(\s*ul_frequencyBand\s*=\s*)\d+;?', r'\g<1>{};'.format(val), content)
            content = re.sub(r'(\s*bands\s*=\s*\[\s*)\d+(\s*\];)', r'\g<1>{}\g<2>'.format(val), content)

        if 'scs' in params:
            val = params.pop('scs')
            print(f"[SERVER] Modifico scs (unificato) in: {val}")
            content = re.sub(r'(\s*dl_subcarrierSpacing\s*=\s*)\d+;?', r'\g<1>{};'.format(val), content)
            content = re.sub(r'(\s*ul_subcarrierSpacing\s*=\s*)\d+;?', r'\g<1>{};'.format(val), content)

        if 'bw' in params:
            val = params.pop('bw')
            print(f"[SERVER] Modifico bw (unificato) in: {val}")
            content = re.sub(r'(\s*dl_carrierBandwidth\s*=\s*)\d+;?', r'\g<1>{};'.format(val), content)
            content = re.sub(r'(\s*ul_carrierBandwidth\s*=\s*)\d+;?', r'\g<1>{};'.format(val), content)

        if 'initial_bwp_riv' in params:
            val = params.pop('initial_bwp_riv')
            print(f"[SERVER] Modifico initial_bwp_riv (unificato) in: {val}")
            content = re.sub(r'(\s*initialDLBWPlocationAndBandwidth\s*=\s*)\d+;?', r'\g<1>{};'.format(val), content)
            content = re.sub(r'(initialULBWPlocationAndBandwidth\s*=\s*)\d+;?', r'\g<1>{};'.format(val), content)

        # --- SEZIONE 2: MAPPA DI REGEX PER TUTTI GLI ALTRI PARAMETRI ---

        regex_map = {
            # Info gNB
            "gnb_id": (re.compile(r'(\s*gNB_ID\s*=\s*).*?;'), r'\g<1>{};'),
            # Rete
            "tac": (re.compile(r'(\s*tracking_area_code\s*=\s*).*?;'), r'\g<1>{};'),
            "mcc": (re.compile(r'(\s*mcc\s*=\s*).*?;'), r'\g<1>{};'),
            "mnc": (re.compile(r'(\s*mnc\s*=\s*).*?;'), r'\g<1>{};'),
            "mnc_length": (re.compile(r'(\s*mnc_length\s*=\s*).*?;'), r'\g<1>{};'),
            "amf_ip": (re.compile(r'(\s*amf_ip_address\s*=\s*\({[^{}]*?ipv4\s*=\s*)".*?"'), r'\g<1>"{}"'),
            # Porte
            "gnb_port_ngap": (re.compile(r'(\s*GNB_PORT_FOR_NG_AMF\s*=\s*).*?;'), r'\g<1>{};'),
            "gnb_port_s1u": (re.compile(r'(\s*GNB_PORT_FOR_(?:S1U|NGU)\s*=\s*).*?;'), r'\g<1>{};'),
            # Hardware
            "nb_tx": (re.compile(r'(\s*nb_tx\s*=\s*).*?;'), r'\g<1>{};'),
            "nb_rx": (re.compile(r'(\s*nb_rx\s*=\s*).*?;'), r'\g<1>{};'),
            "att_tx": (re.compile(r'(\s*att_tx\s*=\s*).*?;'), r'\g<1>{};'),
            "att_rx": (re.compile(r'(\s*att_rx\s*=\s*).*?;'), r'\g<1>{};'),
            "max_rxgain": (re.compile(r'(\s*max_rxgain\s*=\s*).*?;'), r'\g<1>{};'),
            "sdr_addrs": (re.compile(r'(\s*sdr_addrs\s*=\s*)".*?"'), r'\g<1>"{}"'),
            "clock_src": (re.compile(r'(\s*clock_src\s*=\s*)".*?"'), r'\g<1>"{}"'),
            "time_src": (re.compile(r'(\s*time_src\s*=\s*)".*?"'), r'\g<1>"{}"'),
            # Radio
            "dl_freq_pointA": (re.compile(r'(\s*dl_absoluteFrequencyPointA\s*=\s*).*?;'), r'\g<1>{};'),
            "abs_freq_ssb": (re.compile(r'(\s*absoluteFrequencySSB\s*=\s*).*?;'), r'\g<1>{};'),
            "coreset_zero": (re.compile(r'(\s*initialDLBWPcontrolResourceSetZero\s*=\s*).*?;'), r'\g<1>{};'),
            "prach_index": (re.compile(r'(\s*prach_ConfigurationIndex\s*=\s*).*?;'), r'\g<1>{};'),
            "tdd_period": (re.compile(r'(\s*dl_UL_TransmissionPeriodicity\s*=\s*).*?;'), r'\g<1>{};'),
            "tdd_dl_slots": (re.compile(r'(\s*nrofDownlinkSlots\s*=\s*).*?;'), r'\g<1>{};'),
            "tdd_dl_sym": (re.compile(r'(\s*nrofDownlinkSymbols\s*=\s*).*?;'), r'\g<1>{};'),
            "tdd_ul_slots": (re.compile(r'(\s*nrofUplinkSlots\s*=\s*).*?;'), r'\g<1>{};'),
            "tdd_ul_sym": (re.compile(r'(\s*nrofUplinkSymbols\s*=\s*).*?;'), r'\g<1>{};'),
        }

        # Ciclo "motore" che gestisce tutti i parametri nella mappa
        for key, (pattern, replacement_template) in regex_map.items():
            if key in params:
                value = params.pop(key)

                # Logica speciale per sdr_addrs
                if key == 'sdr_addrs' and '=' not in value and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', value):
                    value = f'addr={value}'

                content, count = pattern.subn(replacement_template.format(value), content, count=1)

                if count > 0:
                    print(f"[SERVER] Modificato '{key}' -> '{value}'")
                else:
                    # Logica di fallback per INSERIRE i parametri che potrebbero mancare
                    if key in ["gnb_port_ngap", "gnb_port_s1u", "max_rxgain", "clock_src", "time_src"]:
                        block_map = {
                            "gnb_port_ngap": "NETWORK_INTERFACES", "gnb_port_s1u": "NETWORK_INTERFACES",
                            "max_rxgain": "RUs", "clock_src": "RUs", "time_src": "RUs"
                        }
                        param_name_in_file_map = {
                            "gnb_port_ngap": "GNB_PORT_FOR_NG_AMF", "gnb_port_s1u": "GNB_PORT_FOR_S1U"
                        }
                        block_name = block_map.get(key)
                        param_name_in_file = param_name_in_file_map.get(key, key)
                        is_string = key in ["clock_src", "time_src"]

                        block_pattern = re.compile(r'(' + block_name + r'\s*=\s*\(\s*{\s*\n)')
                        if block_pattern.search(content):
                            formatted_value = f'"{value}"' if is_string else value
                            print(f"[SERVER] INSERITO '{param_name_in_file}' -> '{value}' nel blocco '{block_name}'")
                            content = block_pattern.sub(
                                r'\g<1>  ' + param_name_in_file + ' = ' + formatted_value + ';\n', content)

        if params:
            print(f"[SERVER] ATTENZIONE: Parametri non gestiti: {list(params.keys())}")

        with open(temp_path, 'w') as f:
            f.write(content)
        return True

    except Exception as e:
        print(f"[SERVER] Errore durante la modifica della configurazione: {e}")
        return False

# Ciclo principale del Server
while True:
    try:
        message = rep_socket.recv_string()
    except zmq.error.ZMQError as e:
        print(f"[SERVER] Errore ricezione ZMQ: {e}")
        break

    command_parts = message.split("::", 3)
    command = command_parts[0]

    if command == "START":
        if gnb_process and gnb_process.poll() is None:
            rep_socket.send_string("gNB già in esecuzione")
            continue

        if len(command_parts) != 4:
            rep_socket.send_string(f"Errore: Comando START malformato. Ricevute {len(command_parts)} parti.")
            continue

        _, password, params_json, base_config_from_gui = command_parts

        try:
            params = json.loads(params_json)
        except json.JSONDecodeError:
            rep_socket.send_string("Errore: JSON parametri non valido")
            continue

        base_content = ""
        if base_config_from_gui:
            print("[SERVER] Uso il file di configurazione fornito dalla GUI.")
            base_content = base_config_from_gui
        else:
            print("[SERVER] Nessun file base fornito, uso il template di default.")
            base_content = DEFAULT_CONFIG_TEMPLATE

        print("[SERVER] Creo file di configurazione temporaneo...")
        if not create_modified_config(base_content, TEMP_CONFIG_FULL_PATH, params):
            rep_socket.send_string("Errore nella creazione del file di configurazione temporaneo.")
            continue

        relative_temp_path = os.path.relpath(TEMP_CONFIG_FULL_PATH, OAI_BUILD_DIR)

        cmd_list = ['sudo', '-S', os.path.join(".", OAI_EXECUTABLE_NAME), '-O', relative_temp_path]

        if params.get('use_rfsim') == 'true':
            cmd_list.append("--rfsim")

        print(f"[SERVER] Comando costruito: {' '.join(cmd_list)}")

        try:
            gnb_process = subprocess.Popen(
                cmd_list,
                cwd=OAI_BUILD_DIR,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            gnb_process.stdin.write((password + '\n').encode())
            gnb_process.stdin.close()
            threading.Thread(target=publish_logs, args=(gnb_process,), daemon=True).start()
            rep_socket.send_string("gNB avviato con successo.")
        except Exception as e:
            rep_socket.send_string(f"Errore avvio nr-softmodem: {e}")

    elif command == "STOP":
        if gnb_process and gnb_process.poll() is None:
            print("[SERVER] Ricevuto comando STOP...")
            try:
                os.killpg(os.getpgid(gnb_process.pid), signal.SIGTERM)
                gnb_process.wait(timeout=5)
            except:
                os.killpg(os.getpgid(gnb_process.pid), signal.SIGKILL)
            finally:
                gnb_process = None
                rep_socket.send_string("gNB arrestato.")
        else:
            rep_socket.send_string("Nessun gNB in esecuzione.")
        cleanup()
    else:
        rep_socket.send_string(f"Comando sconosciuto.")