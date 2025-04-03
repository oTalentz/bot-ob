# Interface com Streamlit + Log Visual Aprimorado + Melhorias - Deriv Rise/Fall
import streamlit as st
import websocket
import json
import threading
import time
import os
from playsound import playsound

st.set_page_config(page_title="Deriv Bot - Rise/Fall", layout="wide")
st.markdown("<style>div.block-container{padding-top:2rem;}</style>", unsafe_allow_html=True)

# === Sidebar ===
st.sidebar.title("🎛 Configurações do Bot")
TOKEN = st.sidebar.text_input("🔑 Token da Deriv", type="password")
USE_REAL_ACCOUNT = st.sidebar.checkbox("Usar Conta Real", value=False)
ativos_disponiveis = ["R_10", "R_25", "R_50", "R_75", "R_100"]
ativos_selecionados = st.sidebar.multiselect("📈 Ativos para operar", ativos_disponiveis, default=["R_50"])
CONTRATO_TIPO = st.sidebar.selectbox("Tipo de Contrato", ["CALL", "PUT"])
AMOUNT = st.sidebar.number_input("💵 Valor inicial ($)", value=1.00, min_value=0.35, step=0.01)
MAX_MARTINGALE = st.sidebar.number_input("🔁 Níveis de Martingale", value=5, min_value=0, max_value=10)
STOP_WIN = st.sidebar.number_input("🎯 Stop Win ($)", value=20.0, step=1.0)
STOP_LOSS = st.sidebar.number_input("🛑 Stop Loss ($)", value=-20.0, step=1.0)

# Estado do bot
st.title("🤖 Deriv Bot: Rise/Fall + Martingale + Interface Interativa")
status_placeholder = st.empty()
col_log1, col_log2 = st.columns(2)
log_tick = col_log1.empty()
log_eventos = col_log2.empty()

running_flags = {symbol: False for symbol in ativos_selecionados}
current_levels = {symbol: 0 for symbol in ativos_selecionados}
lucros = {symbol: 0.0 for symbol in ativos_selecionados}
operando = {symbol: False for symbol in ativos_selecionados}
ws_connections = {}

# ===================== FUNÇÕES =====================
def enviar_ordem(ws, valor, contract_type, symbol):
    operando[symbol] = True
    payload = {
        "buy": 1,
        "price": valor,
        "parameters": {
            "amount": valor,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": 1,
            "duration_unit": "t",
            "symbol": symbol
        },
        "passthrough": {"info": f"{symbol}"},
        "req_id": 2
    }
    ws.send(json.dumps(payload))

def autenticar(ws):
    ws.send(json.dumps({"authorize": TOKEN}))

def solicitar_ticks(ws, symbol):
    ws.send(json.dumps({"ticks_subscribe": symbol}))

def tocar_som(tipo):
    try:
        if tipo == "win":
            playsound("https://www.myinstants.com/media/sounds/smw_coin.wav")
        elif tipo == "loss":
            playsound("https://www.myinstants.com/media/sounds/mario-bros-death.mp3")
    except:
        pass

def registrar_log(simbolo, mensagem, tipo="info"):
    timestamp = time.strftime("%H:%M:%S")
    if tipo == "success":
        log_eventos.success(f"[{timestamp}] [{simbolo}] ✅ {mensagem}")
    elif tipo == "error":
        log_eventos.error(f"[{timestamp}] [{simbolo}] ❌ {mensagem}")
    elif tipo == "warning":
        log_eventos.warning(f"[{timestamp}] [{simbolo}] ⚠️ {mensagem}")
    else:
        log_eventos.info(f"[{timestamp}] [{simbolo}] {mensagem}")

def on_message_factory(symbol):
    def on_message(wsapp, message):
        data = json.loads(message)
        if "tick" in data:
            preco = float(data["tick"]["quote"])
            log_tick.info(f"💹 {symbol} | Preço atual: {preco}")
            if running_flags[symbol] and not operando[symbol]:
                valor = round(AMOUNT * (2 ** current_levels[symbol]), 2)
                registrar_log(symbol, f"Enviando ordem ${valor} ({CONTRATO_TIPO})")
                enviar_ordem(wsapp, valor, CONTRATO_TIPO, symbol)

        elif "buy" in data:
            registrar_log(symbol, f"Ordem enviada: {data['buy']['contract_id']}", tipo="success")

        elif "proposal_open_contract" in data:
            if data["proposal_open_contract"]["is_sold"]:
                lucro = float(data["proposal_open_contract"]["profit"])
                lucros[symbol] += lucro
                operando[symbol] = False
                if lucro >= 0:
                    current_levels[symbol] = 0
                    tocar_som("win")
                    registrar_log(symbol, f"Lucro de ${lucro:.2f} | Total: ${lucros[symbol]:.2f}", tipo="success")
                else:
                    current_levels[symbol] += 1
                    tocar_som("loss")
                    registrar_log(symbol, f"Prejuízo de ${lucro:.2f} | Total: ${lucros[symbol]:.2f}", tipo="error")

                if current_levels[symbol] > MAX_MARTINGALE:
                    running_flags[symbol] = False
                    registrar_log(symbol, "Stop Martingale atingido.", tipo="warning")

                if lucros[symbol] >= STOP_WIN:
                    running_flags[symbol] = False
                    registrar_log(symbol, "🎯 Stop Win atingido.", tipo="success")

                if lucros[symbol] <= STOP_LOSS:
                    running_flags[symbol] = False
                    registrar_log(symbol, "🛑 Stop Loss atingido.", tipo="error")

        elif "authorization" in data:
            solicitar_ticks(wsapp, symbol)
            wsapp.send(json.dumps({"subscribe": 1, "proposal_open_contract": 1}))
            registrar_log(symbol, "Autenticado com sucesso")

        elif "error" in data:
            registrar_log(symbol, data['error']['message'], tipo="error")

    return on_message

def iniciar_conexao(symbol):
    ws = websocket.WebSocketApp(
        "wss://ws.derivws.com/websockets/v3?app_id=1089",
        on_open=lambda ws: autenticar(ws),
        on_message=on_message_factory(symbol)
    )
    ws_connections[symbol] = ws
    threading.Thread(target=ws.run_forever, daemon=True).start()

# ===================== CONTROLES =====================
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Iniciar Bot"):
        for symbol in ativos_selecionados:
            iniciar_conexao(symbol)
            running_flags[symbol] = True
        status_placeholder.success("Bot em execução.")

with col2:
    if st.button("⏹ Parar Bot"):
        for symbol in ativos_selecionados:
            running_flags[symbol] = False
        status_placeholder.warning("Bot pausado.")

st.markdown("---")
st.subheader("📊 Logs de Atividades e Ticks")
