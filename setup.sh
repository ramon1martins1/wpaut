# Encerra o script imediatamente se um comando falhar
set -e

echo "--- Iniciando a instalação do Google Chrome ---"
# Usa 'sudo' para rodar os comandos como administrador
sudo apt-get update -y
sudo apt-get install -y wget gnupg

echo "--- Baixando e adicionando a chave do Google ---"
# O pipe (|) passa a saída do wget para o apt-key, que também precisa de sudo
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

echo "--- Adicionando o repositório do Chrome ---"
# Escrever em /etc/apt/sources.list.d/ também requer sudo
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

echo "--- Instalando o Google Chrome ---"
sudo apt-get update -y
sudo apt-get install -y google-chrome-stable

echo "--- Instalação concluída com sucesso! ---"
