# 🚒 PROEISBM Bot — Monitor de Vagas do Corpo de Bombeiros RJ

> Um robô que nunca dorme, vigiando o site do PROEISBM enquanto você vive sua vida — e avisa no Telegram no exato instante em que uma vaga nova aparece.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Selenium](https://img.shields.io/badge/Selenium-WebDriver-43B02A?logo=selenium)
![Status](https://img.shields.io/badge/status-em%20produção-brightgreen)
![License](https://img.shields.io/badge/license-privado-lightgrey)

---

## 🎯 O problema

Vagas para os cursos do PROEISBM (Corpo de Bombeiros Militar do Rio de Janeiro) abrem em janelas curtas e imprevisíveis. Quem depende de ficar atualizando a página manualmente, várias vezes ao dia, perde a vaga por minutos — ou nem fica sabendo que ela existiu.

## 💡 A solução

Um bot de automação que **acessa o site continuamente, resolve captchas automaticamente e dispara um alerta no Telegram em tempo real** assim que detecta uma vaga nova — sem intervenção humana, sem perder a janela de inscrição.

## ⚙️ Como funciona

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐     ┌──────────────┐
│  Scheduler   │ --> │  Selenium WebDriver │ --> │  Anti-Captcha  │ --> │  Parser HTML  │
│ (monitora em │     │  acessa o site      │     │  resolve o     │     │  extrai dados │
│  intervalos) │     │  do PROEISBM        │     │  captcha       │     │  das vagas    │
└─────────────┘     └──────────────────┘     └───────────────┘     └──────┬───────┘
                                                                            │
                                                                            v
                                                                  ┌───────────────────┐
                                                                  │  Detecção de       │
                                                                  │  mudança (nova vaga)│
                                                                  └────────┬───────────┘
                                                                           │
                                                                           v
                                                                  ┌───────────────────┐
                                                                  │  Notificação        │
                                                                  │  via Telegram Bot   │
                                                                  └───────────────────┘
```

## 🛠️ Stack técnica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11 |
| Automação de navegador | Selenium WebDriver + ChromeDriver |
| Resolução de captcha | Anti-Captcha API |
| Notificações | Telegram Bot API |
| Perfis de sessão | Chrome profiles isolados por região monitorada |
| Configuração | Variáveis de ambiente (`.env`) |

## ✨ Funcionalidades

- 🔄 Monitoramento contínuo e automatizado do portal do PROEISBM
- 🧩 Resolução automática de captchas via Anti-Captcha
- 📍 Suporte a múltiplos perfis/regiões monitoradas simultaneamente
- 📲 Notificação instantânea via Telegram assim que uma vaga é detectada
- 🗂️ Sistema de logs para auditoria de execuções
- 🔐 Nenhuma credencial exposta no código — tudo via variáveis de ambiente

## 🚀 Rodando localmente

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/proeisbm-bot.git
cd proeisbm-bot

# Instale as dependências
pip install -r requirements.txt

# Configure suas variáveis de ambiente
cp .env.example .env
# preencha o .env com sua chave da Anti-Captcha e token do Telegram

# Execute
python bot.py
```

## 🔐 Segurança

Este projeto **não contém nenhuma chave de API, token ou credencial** no código-fonte. Todas as configurações sensíveis são carregadas via variáveis de ambiente (`.env`, não versionado). Veja `.env.example` para a lista de variáveis necessárias.

## 📌 Contexto

Projeto desenvolvido sob demanda para um cliente real, como parte dos serviços de automação que ofereço como desenvolvedor freelancer — unindo web scraping, resolução de captcha e integrações de mensageria para resolver problemas concretos de negócio.

---

<p align="center">Feito com Python, Selenium e a persistência de um bombeiro esperando a vaga certa. 🔥</p>
