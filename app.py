
import json
import ssl
import queue
import uuid
import paho.mqtt.client as mqtt
import streamlit as st


# CONFIGURAÇÕES DO STREAMLIT


st.set_page_config(
    page_title="Jardim Inteligente IoT",
    page_icon="🌱",
)


# CONFIGURAÇÕES DO EMQX CLOUD


MQTT_BROKER = "i66f1101.ala.us-east-1.emqxsl.com"
MQTT_PORT = 8883

MQTT_USER = "teste"
MQTT_PASS = "teste"

MQTT_TOPIC_PUB = "jardim/solo/status"
MQTT_TOPIC_SUB = "jardim/irrigacao/comando"


# ESTADO DA SESSÃO


if "mqtt_client_id" not in st.session_state:
    st.session_state.mqtt_client_id = (
        f"streamlit_jardim_{uuid.uuid4().hex[:12]}"
    )

MQTT_CLIENT_ID = st.session_state.mqtt_client_id

if "umidade_solo" not in st.session_state:
    st.session_state.umidade_solo = 0.0

if "status_solo" not in st.session_state:
    st.session_state.status_solo = "DESCONHECIDO"

if "mqtt_messages" not in st.session_state:
    st.session_state.mqtt_messages = queue.Queue()

if "mqtt_status" not in st.session_state:
    st.session_state.mqtt_status = "Desconectado"

if "mqtt_client" not in st.session_state:
    st.session_state.mqtt_client = None

if "mqtt_data" not in st.session_state:
    st.session_state.mqtt_data = {
        "messages": st.session_state.mqtt_messages,
        "status": "Desconectado",
    }


# CALLBACKS MQTT

def on_connect(client, userdata, connect_flags, reason_code, properties):
    print(f"[MQTT] Resultado da conexão: {reason_code}")

    if reason_code == 0:
        print(f"[MQTT] Conectado ao broker: {MQTT_BROKER}")
        userdata["status"] = "Conectado"

        result, mid = client.subscribe(MQTT_TOPIC_PUB, qos=0)

        if result == mqtt.MQTT_ERR_SUCCESS:
            print(
                f"[MQTT] Assinatura solicitada: {MQTT_TOPIC_PUB}"
            )
        else:
            print(
                f"[MQTT] Falha ao solicitar assinatura: {result}"
            )

    else:
        userdata["status"] = f"Falha na conexão: {reason_code}"
        print(f"[MQTT] Conexão recusada: {reason_code}")


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    print(f"[MQTT] Resposta da assinatura: {reason_code_list}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        print(f"[MQTT] Mensagem recebida: {msg.topic} -> {payload}")

        # A thread MQTT envia os dados para uma fila.
        # O Streamlit processa a fila no contexto da interface.
        userdata["messages"].put(payload)

    except (ValueError, UnicodeError) as e:
        print(f"[MQTT] Erro ao interpretar mensagem: {e}")


def on_disconnect(
    client,
    userdata,
    disconnect_flags,
    reason_code,
    properties,
):
    print("[MQTT] Conexão encerrada.")
    print(f"[MQTT] Motivo: {reason_code}")
    print(
        f"[MQTT] Código numérico: "
        f"{getattr(reason_code, 'value', 'indisponível')}"
    )
    print(f"[MQTT] Flags de desconexão: {disconnect_flags}")

    userdata["status"] = "Desconectado"


# INICIALIZAÇÃO DO CLIENTE MQTT

def iniciar_mqtt():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=MQTT_CLIENT_ID,
        userdata=st.session_state.mqtt_data,
        protocol=mqtt.MQTTv311,
    )

    client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS_CLIENT,
    )

    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print(
        f"[MQTT] Conectando a {MQTT_BROKER}:{MQTT_PORT}"
    )
    print(f"[MQTT] Client ID: {MQTT_CLIENT_ID}")

    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        keepalive=60,
    )

    client.loop_start()

    return client


if st.session_state.mqtt_client is None:
    try:
        st.session_state.mqtt_client = iniciar_mqtt()

    except Exception as e:
        st.session_state.mqtt_status = f"Erro: {e}"
        print(f"[MQTT] Erro ao iniciar cliente: {e}")

# CABEÇALHO DO DASHBOARD

st.title("🌱 Dashboard - Jardim Inteligente")

st.markdown(
    "Monitoramento de umidade do solo e acionamento remoto "
    "da irrigação."
)

st.caption(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
st.caption(f"Client ID: {MQTT_CLIENT_ID}")

mqtt_data = st.session_state.mqtt_data
client = st.session_state.mqtt_client

if client is not None and client.is_connected():
    mqtt_status = "Conectado"
else:
    mqtt_status = mqtt_data["status"]

st.session_state.mqtt_status = mqtt_status

if mqtt_status == "Conectado":
    st.success("Conectado ao broker MQTT")
elif mqtt_status.startswith("Falha"):
    st.error(mqtt_status)
else:
    st.warning(f"Estado da conexão MQTT: {mqtt_status}")

# DADOS DO SENSOR

@st.fragment(run_every=2)
def atualizar_dados():

    mensagens = st.session_state.mqtt_messages

    while True:
        try:
            payload = mensagens.get_nowait()
        except queue.Empty:
            break

        try:
            if "umidade_solo" in payload:
                st.session_state.umidade_solo = float(
                    payload["umidade_solo"]
                )

            if "status" in payload:
                st.session_state.status_solo = payload["status"]

        except (ValueError, TypeError) as e:
            print(f"[Dashboard] Dados inválidos: {e}")

    col1, col2 = st.columns(2)

    with col1:
        umidade = st.session_state.umidade_solo

        st.metric(
            label="Umidade do Solo",
            value=f"{umidade:.1f} %",
        )

        st.progress(
            int(min(max(umidade, 0), 100))
        )

    with col2:
        status = st.session_state.status_solo

        if status == "SECO":
            st.error("⚠️ Solo seco! Necessita irrigação.")

        elif status == "UMIDO":
            st.success("✅ Solo com nível adequado de umidade.")

        else:
            st.info("Aguardando dados do sensor.")

atualizar_dados()

# CONTROLE DA IRRIGAÇÃO

st.divider()
st.subheader("🚰 Controle de Irrigação")

col_btn1, col_btn2 = st.columns(2)


def enviar_comando(comando):
    client = st.session_state.mqtt_client

    if client is None or not client.is_connected():
        st.error("Cliente MQTT desconectado.")
        return

    try:
        info = client.publish(
            MQTT_TOPIC_SUB,
            comando,
            qos=0,
        )

        if info.rc == mqtt.MQTT_ERR_SUCCESS:
            st.toast(f"Comando enviado: {comando}")
            print(f"[MQTT] Publicação solicitada: {comando}")
        else:
            st.error(
                f"Erro ao publicar comando. Código: {info.rc}"
            )

    except Exception as e:
        st.error(f"Erro ao enviar comando: {e}")
        print(f"[MQTT] Erro de publicação: {e}")


with col_btn1:
    if st.button("💧 Ligar bomba de água", type="primary"):
        enviar_comando("LIGAR")

with col_btn2:
    if st.button("🛑 Desligar bomba de água"):
        enviar_comando("DESLIGAR")
