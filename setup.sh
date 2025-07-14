set -e # Encerra o script imediatamente se um comando falhar

echo "--- Iniciando a instalação do Google Chrome ---"
apt-get update -y
apt-get install -y wget gnupg

echo "--- Baixando e adicionando a chave do Google ---"
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -

echo "--- Adicionando o repositório do Chrome ---"
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

echo "--- Instalando o Google Chrome ---"
apt-get update -y
apt-get install -y google-chrome-stable

echo "--- Instalação concluída com sucesso! ---"