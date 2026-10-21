Alunos:

->Gabriel Ribeiro Canela de Souza

->Victor Luiz Angelo de Oliveira

🪴Este projeto consiste em um sistema de Jardim Inteligente IoT baseado em comunicação via protocolo MQTT com segurança TLS. Ele é composto por duas partes principais:

Hardware (ESP32): Desenvolvido em MicroPython, conecta-se à rede Wi-Fi e utiliza um sensor analógico para monitorar a umidade do solo em tempo real. Os dados são enviados periodicamente para um broker MQTT na nuvem (EMQX Cloud). O ESP32 também atua como assinante de comandos para acionar ou desligar uma bomba de irrigação conectada a um pino de saída digital, conforme a necessidade do solo ou comandos remotos.

Interface de Monitoramento (Streamlit): Uma aplicação web interativa em Python que exibe um dashboard em tempo real com o status e o nível percentual de umidade do solo coletado pelo sensor. A interface se conecta ao mesmo broker MQTT para receber os dados dos sensores e permite ao usuário enviar comandos manuais ("Ligar" ou "Desligar" a bomba de água) de forma remota e segura.
