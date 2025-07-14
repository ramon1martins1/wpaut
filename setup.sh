#!/bin/bash

# Instala dependências necessárias
apt-get update && apt-get install -y wget gnupg

# Baixa e instala a chave de assinatura do Google
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -

# Adiciona o repositório do Google Chrome
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list

# Atualiza a lista de pacotes e instala o Google Chrome
apt-get update && apt-get install -y google-chrome-stable
