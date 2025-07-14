import streamlit as st
import urllib.parse
import time
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import re
import os
from PIL import Image

# === CONFIGURAÇÕES INICIAIS ===
CACHE_KEY_INTERVALO = "intervalo_envio"
CACHE_KEY_MENSAGEM = "mensagem_padrao"
DEFAULT_LINK = "https://docs.google.com/spreadsheets/d/1c9_rJNg7i3Y-6K_s-IVDps1V3cp64uBO5X3Swy8liAI/edit?usp=sharing"

# Inicializa variáveis no session_state, se ainda não existirem
if 'cancelar_envio' not in st.session_state:
    st.session_state.cancelar_envio = False
if 'ultimo_enviado' not in st.session_state:
    st.session_state.ultimo_enviado = None
if "LINK_PLANILHA" not in st.session_state:
    st.session_state["LINK_PLANILHA"] = DEFAULT_LINK
if "intervalo_envio" not in st.session_state:
    st.session_state["intervalo_envio"] = 40
if "mensagem_padrao" not in st.session_state:
    st.session_state["mensagem_padrao"] = "Olá *{nome}*,\\n\\n*Nova versão do E2 Administrativo 5.00.00/000 liberada!* \\n\\n Confira a lista de demandas:\\n\\n* 123456 - Ajuste para ...;\\n* 789102 - Melhoria ...;\\n\\nAtenciosamente,\\n\\nAtendimento E2 Administrativo\\n📞 Telefone: (48) 3411-0680"

# Inicializa o driver do Selenium uma vez
@st.cache_resource
def get_webdriver():
    options = webdriver.ChromeOptions()
    # Usar um caminho relativo ou configurável para o perfil do usuário
    # Para produção, considere usar um diretório temporário ou configurável via st.secrets
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument("--profile-directory=Default")
    # Adicionar argumentos para execução headless em ambientes de servidor
    # options.add_argument("--headless")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def formatar_para_whatsapp(texto):
    # Ordem CRÍTICA das substituições
    substituicoes = [
        (r'\\*\\*(.*?)\\*\\*', r'*\\1*'),  # Negrito primeiro
        (r'_(.*?)_', r'_\\1_'),        # Itálico depois
        (r'```(.*?)```', r'```\\1```'), # Código
        (r'^\\s*\\*\\s', '◦ ', re.MULTILINE),  # Listas
        ('•', '◦'),
        ('\\n', '\n'),
        ('<br>', '\n'),
        ('&nbsp;', ' ')
    ]
    
    for pattern, repl, *flags in substituicoes:
        flags = flags[0] if flags else 0
        texto = re.sub(pattern, repl, texto, flags=flags)
    
    return texto

st.set_page_config(page_title="WpAut", page_icon=":zap:", layout="wide")
st.markdown("""
    <style>
        /* Ajuste para a largura da sidebar, tornando-a mais flexível */
        section[data-testid="stSidebar"] {
            width: 350px !important; /* Largura padrão */
            max-width: 800px !important; /* Largura máxima */
            min-width: 800px !important; /* Largura mínima */
        }
        /* Ajuste para o conteúdo principal se mover corretamente */
        section.main > div {
            margin-left: 370px; /* Ajuste baseado na largura da sidebar */
        }
        .log-box {
            max-height: 300px;
            overflow-y: auto;
            font-family: monospace;
            white-space: pre-wrap;
            background-color: #1e1e1e;
            color: #f8f8f2;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #333;
        }
    </style>
""", unsafe_allow_html=True)



# === LOGO E TÍTULO ===
col1, col2 = st.columns([6, 1])
with col1:
    svg_path = "logo_wpaut3.svg"
    if os.path.exists(svg_path):
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_logo = f.read()
        # Limpa fundo branco do SVG
        svg_logo = svg_logo.replace('fill="white"', 'fill="currentColor"')
        svg_logo = svg_logo.replace('<svg ', '<svg width="250" height="250" ')
        st.markdown(f"""
        <div style='display: flex; color: inherit;'>
            {svg_logo}
        </div>
            <h4 style='color:gray; display: flex;'>Automatizador de mensagens via WhatsApp</h4>
        """, unsafe_allow_html=True)
    else:
        st.write("Logo não encontrada.")
with col2:
    st.markdown(" ", unsafe_allow_html=True)

st.markdown("---")

# === SIDEBAR ===
st.sidebar.header("Configurações")

link_planilha = st.sidebar.text_input(
    "Link da planilha do Google",
    value=st.session_state.get("LINK_PLANILHA", DEFAULT_LINK)
)

intervalo = st.sidebar.number_input(
    "Intervalo entre mensagens (segundos)", min_value=1, max_value=600,
    value=st.session_state.get(CACHE_KEY_INTERVALO, 40)
)

mensagem_base = st.sidebar.text_area(
    "Mensagem",
    value=st.session_state[CACHE_KEY_MENSAGEM],
    height=550,
    help="Esta mensagem será enviada aos contatos"    
)

# Pré-visualização da mensagem
st.sidebar.subheader("Pré-visualização da Mensagem")
nome_exemplo = "João" # Nome de exemplo para pré-visualização
mensagem_preview = mensagem_base.replace("{nome}", nome_exemplo)
st.sidebar.markdown(f"**Para {nome_exemplo}:**")
st.sidebar.markdown(mensagem_preview) # Removido formatar_para_whatsapp


with st.sidebar.expander("😀 Inserir Emojis"):
    emojis = ["😀", "🎉", "✅", "❌", "📞", "📢", "💡", "🔥", "🚀", "🙏", "👍","▪️","🚫","⛔","❗","📍"]
    cols = st.columns(6)
    for i, emoji in enumerate(emojis):
        if cols[i % 6].button(emoji, key=f"emoji_{i}"):
            # Usar JavaScript para inserir o emoji sem st.rerun()
            st.session_state[CACHE_KEY_MENSAGEM] += emoji
            # st.rerun() # Removido para evitar recarregamento total

# Expander corrigido para sidebar
expander = st.sidebar.expander("📝 Formatação da Mensagem")
with expander:
    st.markdown("""
    **Guia de Formatação:**  
    (Suporta Markdown básico e emojis)
    
    ```
    • {nome} = nome do contato
    • Quebras de linha: Enter 
    • Emojis: 😀 🎉 ✅ ❌ 📞 etc.
    • Negrito: *texto*
    • Itálico: _texto_
    • Código = ```texto``` 
    • Listas: * item ou - item
    • Links: [texto](url)
    ```
    """, unsafe_allow_html=True)

if st.sidebar.button("Salvar configurações"):
    st.session_state["LINK_PLANILHA"] = link_planilha
    st.session_state[CACHE_KEY_INTERVALO] = intervalo
    st.session_state[CACHE_KEY_MENSAGEM] = mensagem_base
    st.sidebar.success("Configurações salvas!")

# === AUTENTICAÇÃO COM GOOGLE SHEETS ===
# Usar st.secrets para credenciais
@st.cache_data
def carregar_contatos(link):
    try:
        # Carregar credenciais de st.secrets
        # Exemplo de como st.secrets deve ser configurado no .streamlit/secrets.toml:
        # [gcp_service_account]
        # type = "service_account"
        # project_id = "your-project-id"
        # private_key_id = "your-private-key-id"
        # private_key = "your-private-key"
        # client_email = "your-client-email"
        # client_id = "your-client-id"
        # auth_uri = "https://accounts.google.com/o/oauth2/auth"
        # token_uri = "https://oauth2.googleapis.com/token"
        # auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        # client_x509_cert_url = "your-client-x509-cert-url"

        # creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        # Para fins de demonstração, mantendo o arquivo, mas a recomendação é st.secrets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
        
        client = gspread.authorize(creds)
        planilha_id = link.split("/d/")[1].split("/")[0]
        planilha = client.open_by_key(planilha_id)
        abas = planilha.worksheets()
        return planilha, [a.title for a in abas]
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return None, []

planilha, abas = carregar_contatos(link_planilha)

# Definir aba padrão
if abas:
    if "lista_teste" in abas:
        default_index = abas.index("lista_teste")
    else:
        default_index = 0
    aba_escolhida = st.selectbox("Escolha a aba com os contatos:", abas, index=default_index)
else:
    aba_escolhida = None

@st.cache_data
def obter_contatos_cached(_planilha_obj, aba_nome):
    if _planilha_obj and aba_nome:
        aba = _planilha_obj.worksheet(aba_nome)
        dados = aba.get_all_records()
        return [(d['Numero'], d['Nome']) for d in dados if d.get('Numero')]
    return []

contatos = obter_contatos_cached(planilha, aba_escolhida)

# === INICIALIZAÇÃO DO LOG ===
if "log" not in st.session_state:
    st.session_state.log = []

if "resultado_envio" not in st.session_state:
    st.session_state.resultado_envio = None

# === ENVIO DE MENSAGENS ===
def iniciar_envio():
    st.session_state.log = []
    st.session_state.resultado_envio = None
    st.session_state.cancelar_envio = False
    st.session_state.ultimo_enviado = None

    if 'log_history' not in st.session_state:
        st.session_state.log_history = []

    total = len(contatos)

    # Botão de cancelar fora do loop
    cancel_button_placeholder = st.empty()
    if cancel_button_placeholder.button("❌ Cancelar Envio", key="cancelar_envio_btn_main"):
        st.session_state.cancelar_envio = True
        st.warning("Cancelamento solicitado...")

    # Containers para atualização em tempo real
    log_container = st.empty()
    barra_container = st.empty()
    porcentagem_container = st.empty()
    contador_container = st.empty()

    def atualizar_log():
        with log_container.container():
            with st.expander("📋 Log de envio", expanded=True):
                st.markdown("""
                    <div class="log-box">
                        {log}
                    </div>
                """.format(log="<br>".join(st.session_state.log[-40:])), unsafe_allow_html=True)


    st.session_state.log.append(f"📊 Total de contatos: {total}")
    tempo_total = total * intervalo
    duracao = str(datetime.timedelta(seconds=tempo_total))
    st.session_state.log.append(f"⏱️ Tempo estimado: {duracao}")
    st.session_state.log.append("=" * 50)
    atualizar_log()

    # Selenium
    driver = get_webdriver() # Reutiliza o driver
    driver.get("https://web.whatsapp.com")
    
    st.session_state.log.append("🔗 Conectando ao WhatsApp Web...")
    st.session_state.log.append("📱 Escaneie o QR Code no WhatsApp. Se já estiver conectado, apenas aguarde...")
    atualizar_log()
    
    # Esperar até que o WhatsApp Web esteja carregado (ex: elemento de pesquisa visível)
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')) # Exemplo de seletor para barra de pesquisa
        )
        st.session_state.log.append("✅ WhatsApp Web conectado!")
    except Exception as e:
        st.session_state.log.append(f"❌ Falha ao conectar ao WhatsApp Web: {e}. Tente novamente.")
        driver.quit()
        return

    st.session_state.log.append("🚀 Iniciando envio das mensagens...")
    st.session_state.log.append("=" * 50)
    atualizar_log()

    sucesso = 0
    falhas = []

    for i, (numero, nome) in enumerate(contatos):
        if st.session_state.cancelar_envio:
            st.session_state.log_history = st.session_state.log.copy()
            st.session_state.log.append(f"⛔ Envio cancelado pelo usuário")
            st.session_state.log.append(f"⏸️ Último envio completo: {nome} ({numero})")
            atualizar_log()

            # Salva o resultado como cancelado
            st.session_state.resultado_envio = {
                "sucesso": sucesso,
                "falhas": len(falhas),
                "lista_falhas": falhas,
                "cancelado": True,
                "ultimo_enviado": f"{nome} ({numero})"
            }
            # driver.quit() # Não fechar o driver aqui, pois ele é reutilizado
            atualizar_log()
            break 

        mensagem_personalizada = mensagem_base.replace("{nome}", nome)
        mensagem_formatada = formatar_para_whatsapp(mensagem_personalizada)

        # Codifica para URL (importante!)
        mensagem_codificada = urllib.parse.quote(mensagem_formatada)
        
        st.session_state.log.append(f"📤 Enviando para {nome} ({numero})...")
        atualizar_log()
        
        try:
            # Verificar se número tem formato correto
            numero_limpo = ''.join(filter(str.isdigit, str(numero)))
            if len(numero_limpo) < 10:
                raise Exception("Número inválido ou muito curto")
            
            driver.get(f"https://web.whatsapp.com/send?phone=55{numero_limpo}&text={mensagem_codificada}")
            
            # Esperar até que o campo de mensagem esteja visível e clicável
            campo = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Caixa de texto da mensagem"]'))
            )
            
            # Verificar se há mensagem de número inválido
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'não está no WhatsApp') or contains(text(), 'Phone number shared via url is invalid')]"))
                )
                raise Exception("Número não encontrado no WhatsApp")
            except:
                pass  # Não há erro, continuar
            
            campo.send_keys(Keys.ENTER)
            # Esperar um pouco para o envio ser processado
            time.sleep(3) 
            
            st.session_state.log.append(f"✔️ Enviado para {nome} ({numero})")
            sucesso += 1
            
        except Exception as e:
            msg = f"❌ Falha para {nome} ({numero}): {str(e).splitlines()[0]}"
            st.session_state.log.append(msg)
            falhas.append((nome, numero))
        
        # Atualizar barra de progresso com porcentagem
        progresso = (i + 1) / total
        with barra_container.container():
            st.progress(progresso)
        porcentagem_container.text(f"Progresso: {progresso:.1%} ({i+1}/{total})")
        atualizar_log()
        
        # Contador regressivo apenas se não for a última mensagem
        if i < total - 1:
            st.session_state.log.append(f"⏳ Aguardando {intervalo} segundos para próxima mensagem...")
            atualizar_log()
            
            for t in range(intervalo, 0, -1):
                contador_container.info(f"⏰ Próxima mensagem em: {t} segundos")
                time.sleep(1)
            
            contador_container.empty()

    # driver.quit() # Não fechar o driver aqui, pois ele é reutilizado
    cancel_button_placeholder.empty()
    
    # Mostra resultado final apenas se não foi cancelado
    if not st.session_state.cancelar_envio:
        st.session_state.resultado_envio = {
            "sucesso": sucesso,
            "falhas": len(falhas),
            "lista_falhas": falhas
        }
        st.session_state.log.append("🎉 Envio concluído!")
    else:
        st.session_state.resultado_envio = {
            "sucesso": sucesso,
            "falhas": len(falhas),
            "lista_falhas": falhas,
            "cancelado": True
        }
    atualizar_log()
    
    # Limpar contador
    contador_container.empty()

# === INTERFACE PRINCIPAL ===
# Botão de envio
if st.button("Iniciar envio"):
    if not link_planilha or not aba_escolhida:
        st.error("Informe o link da planilha e selecione uma aba")
    else:
        st.session_state["enviando"] = True
        iniciar_envio()
        st.session_state["enviando"] = False

# Exibir resultado do envio (fora do log)
if st.session_state.get('resultado_envio'):
    resultado = st.session_state.resultado_envio
    
    # Se foi cancelado
    if resultado.get('cancelado'):
        st.warning("Envio cancelado pelo usuário")
        if st.session_state.ultimo_enviado:
            st.info(f"⏸️ Último envio completo: {st.session_state.ultimo_enviado}")
        
        if st.button("🔄 Reiniciar Envio"):
            st.session_state.cancelar_envio = False
            st.session_state.ultimo_enviado = None
            st.rerun()
    
    # Se foi concluído (não cancelado)
    else:
        st.success(f"✅ Envio concluído. Sucesso: {resultado['sucesso']}, Falhas: {resultado['falhas']}")
        
        if resultado['lista_falhas']:
            with st.expander("📝 Ver falhas"):
                for nome, numero in resultado['lista_falhas']:
                    st.write(f"❌ {nome} ({numero})")

    # Botão para limpar log (aparece em ambos os casos)
    if st.button("🧹 Limpar log e resultados"):
        st.session_state.log = []
        st.session_state.resultado_envio = None
        st.session_state.cancelar_envio = False
        st.session_state.ultimo_enviado = None
        st.rerun()