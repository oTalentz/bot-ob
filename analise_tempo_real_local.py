
import cv2
import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

# ========== CONFIGURAÇÕES ==========
TOTAL_CAPTURAS = 10      # Número de capturas
INTERVALO_SEGUNDOS = 30  # Intervalo entre capturas
URL_QUOTEX = "https://quotex.io/pt/demo-trade"
PASTA_SAIDA = "capturas"

# ========== SETUP DO CHROME ==========
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Criar pasta de saída
os.makedirs(PASTA_SAIDA, exist_ok=True)

# Iniciar driver
driver = webdriver.Chrome(options=chrome_options)
driver.get(URL_QUOTEX)
print("🔄 Aguardando carregamento do gráfico...")
time.sleep(10)

# ========== LOOP DE CAPTURA + ANÁLISE ==========
for i in range(TOTAL_CAPTURAS):
    nome_arquivo = os.path.join(PASTA_SAIDA, f"grafico_{i+1}.png")
    driver.save_screenshot(nome_arquivo)
    print(f"📸 Captura {i+1} salva: {nome_arquivo}")

    # Análise com OpenCV
    image = Image.open(nome_arquivo).convert("RGB")
    img_array = np.array(image)
    img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(img_gray, threshold1=50, threshold2=150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=80, maxLineGap=10)

    sups_resistencias = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 10:
                sups_resistencias.append(y1)

    if sups_resistencias:
        zonas = sorted(list(set([round(y, -1) for y in sups_resistencias])))
        print(f"🔍 Zonas detectadas (Y): {zonas}")
    else:
        print("⚠️ Nenhuma zona detectada.")

    if i < TOTAL_CAPTURAS - 1:
        time.sleep(INTERVALO_SEGUNDOS)

# Encerrar navegador
driver.quit()
print("✅ Análise finalizada. Todas capturas salvas em ./capturas")
