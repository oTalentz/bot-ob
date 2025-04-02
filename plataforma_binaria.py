
import streamlit as st
import random
import pandas as pd
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="Simulador + Análise de Imagem", layout="wide")
st.title("🧠 Plataforma Binária - Versão para Nuvem")

aba = st.sidebar.radio("Escolha o módulo", ["Simulador Martingale", "Análise de Imagem"])

if aba == "Simulador Martingale":
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

elif aba == "Análise de Imagem":
    st.markdown("Envie uma imagem de gráfico e o sistema detectará zonas de suporte/resistência.")
    uploaded_file = st.file_uploader("📤 Envie a imagem", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        img_array = np.array(image)
        img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        st.image(image, caption="Imagem Original", use_column_width=True)
        edges = cv2.Canny(img_gray, threshold1=50, threshold2=150)
        st.image(edges, caption="Detecção de Bordas (Canny)", use_column_width=True)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=80, maxLineGap=10)
        linhas_detectadas = img_array.copy()
        sups_resistencias = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(linhas_detectadas, (x1, y1), (x2, y2), (0, 255, 0), 2)
                if abs(y1 - y2) < 10:
                    sups_resistencias.append(y1)
        st.image(linhas_detectadas, caption="Linhas Detectadas (Verde)", use_column_width=True)
        if sups_resistencias:
            zonas = sorted(list(set([round(y, -1) for y in sups_resistencias])))
            st.subheader("🔍 Zonas de Suporte/Resistência:")
            for z in zonas:
                st.markdown(f"- Linha em Y = {z}px")
            st.markdown("**🔮 Entrada sugerida:** aguarde confirmação de pullback ou rompimento próximo a essas zonas.")
        else:
            st.warning("Nenhuma zona foi detectada com confiança.")
