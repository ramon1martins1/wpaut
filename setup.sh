#!/bin/bash

# Encerra o script imediatamente se um comando falhar
set -e

echo "--- Iniciando a instalação do Google Chrome ---"
# Usa 'sudo -n' para rodar os comandos de forma não-interativa
sudo -n apt-get update -y
sudo -n apt-get install -y wget gnupg

echo "--- Baixando e adicionando a chave do Google ---"
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo -n apt-key add -

echo "--- Adicionando o repositório do Chrome ---"
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo -n tee /etc/apt/sources.list.d/google-chrome.list

echo "--- Instalando o Google Chrome ---"
sudo -n apt-get update -y
sudo -n apt-get install -y google-chrome-stable

echo "--- Instalação concluída com sucesso! ---"
