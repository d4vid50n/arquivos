import streamlit as st
import random
import time
from PIL import Image, ImageDraw
from datetime import datetime, timedelta

st.set_page_config(page_title="Roleta Automática com Apostas", layout="centered")
st.title("🎡 Roleta Automática - Aposte em Amarelo ou Vermelho")

# === Parâmetros ===
TAMANHO = 400
FATIAS = 24
DURACAO_GIRO = 5  # segundos da animação do giro
VALOR_MIN_APOSTA = 10

# Inicializa estados persistentes
if "saldo" not in st.session_state:
    st.session_state.saldo = 1000

if "girando" not in st.session_state:
    st.session_state.girando = False

if "resultado" not in st.session_state:
    st.session_state.resultado = None

if "historico" not in st.session_state:
    st.session_state.historico = []

if "apostas" not in st.session_state:
    st.session_state.apostas = []

# Funções para criar imagens

def criar_roleta_rotacionada(angulo, tamanho=TAMANHO):
    roleta_base = Image.new("RGBA", (tamanho, tamanho), (255, 255, 255, 0))
    draw = ImageDraw.Draw(roleta_base)
    centro = tamanho // 2
    raio = centro - 10
    cores = ["#FFD700", "#FF0000"]  # amarelo, vermelho
    angulo_fatia = 360 / FATIAS

    for i in range(FATIAS):
        cor = cores[i % 2]
        start_angle = i * angulo_fatia
        end_angle = start_angle + angulo_fatia
        draw.pieslice([centro - raio, centro - raio, centro + raio, centro + raio],
                      start=start_angle, end=end_angle, fill=cor, outline="black")

    draw.ellipse([centro - 40, centro - 40, centro + 40, centro + 40], fill="black")

    roleta_rotacionada = roleta_base.rotate(angulo, resample=Image.BICUBIC, center=(centro, centro))
    return roleta_rotacionada

def criar_seta(tamanho=TAMANHO):
    seta = Image.new("RGBA", (tamanho, tamanho), (255, 255, 255, 0))
    draw = ImageDraw.Draw(seta)
    centro = tamanho // 2
    pontos = [(centro - 20, 10), (centro + 20, 10), (centro, 50)]
    draw.polygon(pontos, fill="black")
    return seta

# Variáveis fixas para a roleta
angulo_fatia = 360 / FATIAS
seta_img = criar_seta()

col1, col2 = st.columns([1,2])

with col1:
    st.markdown(f"### Seu saldo: R$ {st.session_state.saldo:.2f}")

    if st.session_state.girando:
        st.info("🔄 Roleta girando, apostas fechadas!")
    else:
        st.info("Faça sua aposta e clique em 'Girar roleta'")

    # Apostas só se a roleta não estiver girando
    if not st.session_state.girando:
        aposta_cor = st.radio("Aposte na cor:", ("Amarelo", "Vermelho"))
        aposta_valor = st.number_input("Valor da aposta (mínimo 10):", min_value=VALOR_MIN_APOSTA,
                                      max_value=st.session_state.saldo, step=10, value=VALOR_MIN_APOSTA)

        if st.button("Fazer aposta"):
            if aposta_valor > st.session_state.saldo:
                st.error("Saldo insuficiente!")
            else:
                st.session_state.apostas.append({"cor": aposta_cor, "valor": aposta_valor})
                st.session_state.saldo -= aposta_valor
                st.success(f"Aposta de R$ {aposta_valor} em {aposta_cor} registrada!")

    # Botão para iniciar o giro da roleta
    if not st.session_state.girando:
        if st.button("Girar roleta"):
            if len(st.session_state.apostas) == 0:
                st.warning("Faça ao menos uma aposta antes de girar a roleta!")
            else:
                st.session_state.girando = True
                st.session_state.resultado = None

    # Mostrar apostas feitas nesta rodada
    st.markdown("### Apostas nesta rodada:")
    if st.session_state.apostas:
        for i, ap in enumerate(st.session_state.apostas):
            st.write(f"{i+1}. {ap['cor']} - R$ {ap['valor']:.2f}")
    else:
        st.write("Nenhuma aposta feita.")

    # Mostrar histórico simplificado
    st.markdown("---")
    st.markdown("### Histórico de rodadas")
    if st.session_state.historico:
        for h in reversed(st.session_state.historico[-5:]):
            st.write(f"Fat: {h['fat']} | Cor: {h['cor']} | Resultado: {'Ganhou' if h['ganhou'] else 'Perdeu'} | Saldo: R$ {h['saldo']:.2f}")
    else:
        st.write("Nenhuma rodada ainda.")

with col2:
    frame_placeholder = st.empty()

    if st.session_state.girando:
        passos = 30
        fatia_resultado = random.randint(0, FATIAS-1)
        angulo_final = 360 - (fatia_resultado * angulo_fatia + angulo_fatia / 2)

        for i in range(passos):
            angulo = (360 * 3 * (i / passos)) + (angulo_final * (i / passos))
            img = criar_roleta_rotacionada(angulo % 360, TAMANHO)
            img_com_seta = Image.alpha_composite(img.convert("RGBA"), seta_img)
            frame_placeholder.image(img_com_seta, width=400)
            time.sleep(DURACAO_GIRO / passos)

        # Mostrar parada final
        img_final = criar_roleta_rotacionada(angulo_final, TAMANHO)
        img_com_seta = Image.alpha_composite(img_final.convert("RGBA"), seta_img)
        frame_placeholder.image(img_com_seta, width=400)

        # Mostrar resultado
        cor_resultado = ["Amarelo", "Vermelho"][fatia_resultado % 2]
        st.write(f"Roleta parou na fatia {fatia_resultado + 1} ({cor_resultado})")

        # Processar apostas e atualizar saldo
        ganhou_total = 0
        for aposta in st.session_state.apostas:
            if aposta["cor"] == cor_resultado:
                ganho = aposta["valor"] * 2  # paga 2x
                st.session_state.saldo += ganho
                ganhou_total += ganho

        rodada = {
            "fat": fatia_resultado + 1,
            "cor": cor_resultado,
            "ganhou": ganhou_total > 0,
            "saldo": st.session_state.saldo
        }
        st.session_state.historico.append(rodada)

        # Limpar apostas depois da rodada
        st.session_state.apostas = []

        st.success(f"Você ganhou R$ {ganhou_total:.2f} nesta rodada!" if ganhou_total > 0 else "Você não ganhou nesta rodada.")

        # Resetar estado de giro
        st.session_state.girando = False
        st.session_state.resultado = rodada

    else:
        # Mostrar roleta parada (último resultado ou neutra)
        if st.session_state.resultado:
            fatia = st.session_state.resultado["fat"] - 1
            angulo_final = 360 - (fatia * angulo_fatia + angulo_fatia / 2)
        else:
            angulo_final = 0

        roleta_img = criar_roleta_rotacionada(angulo_final, TAMANHO)
        img_com_seta = Image.alpha_composite(roleta_img.convert("RGBA"), seta_img)
        frame_placeholder.image(img_com_seta, width=400)
