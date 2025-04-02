
import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="Simulador Martingale", layout="wide")
st.title("📊 Simulador de Martingale para Operações Binárias")

col1, col2, col3 = st.columns(3)

with col1:
    banca_inicial = st.number_input("Banca Inicial (R$)", min_value=100.0, value=500.0, step=50.0)
    entrada_inicial = st.number_input("Entrada Inicial (R$)", min_value=1.0, value=5.0, step=1.0)

with col2:
    payout = st.slider("Payout (%)", min_value=50, max_value=100, value=80) / 100
    taxa_acerto = st.slider("Taxa de Acerto do Bot (%)", min_value=10, max_value=100, value=55) / 100

with col3:
    max_martingale = st.number_input("Máximo de Martingales", min_value=1, max_value=10, value=6)
    simulacoes = st.number_input("Número de Operações", min_value=10, max_value=10000, value=1000)

stop_loss_percent = 50
stop_loss_valor = banca_inicial * (stop_loss_percent / 100)
stop_gain = st.number_input("Stop Gain (R$)", min_value=0.0, value=200.0, step=10.0)

st.markdown(f"💥 Stop Loss configurado automaticamente para 50% da banca: R${stop_loss_valor:.2f}")

def simular_com_detalhes(banca, entrada_base, payout, acerto_chance, max_mg):
    entrada = entrada_base
    operacao = {"Entradas": [], "Resultado": "", "Banca Antes": banca, "Banca Depois": 0}

    for tentativa in range(max_mg + 1):
        if entrada > banca:
            operacao["Resultado"] = "Quebrou"
            operacao["Entradas"].append(entrada)
            operacao["Banca Depois"] = banca
            return False, banca, operacao

        banca -= entrada
        operacao["Entradas"].append(entrada)

        if random.random() < acerto_chance:
            lucro = entrada * payout
            banca += entrada + lucro
            operacao["Resultado"] = "Vitória"
            operacao["Banca Depois"] = banca
            return True, banca, operacao

        entrada *= 2

    operacao["Resultado"] = "Perdeu Sequência"
    operacao["Banca Depois"] = banca
    return False, banca, operacao

if st.button("▶️ Simular"):
    banca = banca_inicial
    detalhes = []
    for i in range(int(simulacoes)):
        lucro_antes = banca - banca_inicial
        if lucro_antes >= stop_gain or lucro_antes <= -stop_loss_valor:
            break

        sucesso, banca, operacao = simular_com_detalhes(banca, entrada_inicial, payout, taxa_acerto, max_martingale)
        operacao["Operação"] = i + 1
        detalhes.append(operacao)

    df = pd.DataFrame(detalhes)
    df["Entradas"] = df["Entradas"].apply(lambda x: ", ".join(f"R${v}" for v in x))

    st.subheader("📋 Resultado das Operações")
    st.dataframe(df, use_container_width=True)

    st.markdown(f"**Banca Final:** R${banca:.2f}")
    st.markdown(f"**Lucro/Prejuízo:** R${banca - banca_inicial:.2f}")
    st.markdown(f"**Total de Operações:** {len(df)}")
    st.download_button("📥 Baixar Resultado em CSV", data=df.to_csv(index=False), file_name="resultado_martingale.csv", mime="text/csv")
