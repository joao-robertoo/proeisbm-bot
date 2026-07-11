# 🤖 GUIA DO CLIENTE — BOT PROEISBM v5.1

---

## COMO TROCAR SEU LOGIN E SENHA

1. Abra a pasta do bot
2. Clique com o botão direito no arquivo **`.env`**
3. Escolha **"Abrir com"** → **Bloco de Notas**
4. Altere os campos desejados:

```
MARICA_LOGIN=SEU_RG_AQUI
MARICA_SENHA=SUA_SENHA_AQUI

NITEROI_LOGIN=SEU_RG_AQUI
NITEROI_SENHA=SUA_SENHA_AQUI
```

5. Salve o arquivo (**CTRL+S**)
6. Feche e reabra o bot — ele usará os novos dados automaticamente.

> ⚠️ Não altere nada além do que está entre o `=` e o final da linha.
> Não apague linhas que começam com `#` — são comentários.

---

## COMO INICIAR OS DOIS ROBÔS (Maricá + Niterói)

1. Abra a pasta do bot
2. Dê **clique duplo** no arquivo **`iniciar.bat`**
3. Duas janelas vão abrir automaticamente:
   - 🟢 Janela verde → **Bot Maricá**
   - 🔵 Janela azul → **Bot Niterói**
4. Pronto! Os dois robôs estão monitorando ao mesmo tempo.

---

## O QUE VOCÊ VAI RECEBER NO CELULAR

Quando o robô encontrar uma vaga compatível, você receberá **3 mensagens** no Telegram:

| # | Mensagem | Significado |
|---|----------|-------------|
| 1 | 🚨 **VAGA ENCONTRADA!** | Vaga apareceu no sistema |
| 2 | ⏳ **Se inscrevendo...** | Robô clicando em Solicitar Serviço |
| 3 | ✅ **INSCRIÇÃO CONFIRMADA!** | Inscrição realizada com sucesso |

> ℹ️ Se aparecer uma vaga de outra especialidade (ex: Guarda-Vidas), o robô tenta mas o sistema recusará automaticamente. Você receberá um aviso no Telegram e o robô **continua monitorando** sem precisar reiniciar.

---

## COMO ENCERRAR OS ROBÔS

Em cada janela aberta, pressione:
```
CTRL + C
```
Ou simplesmente **feche a janela**.

---

## PROBLEMAS COMUNS

**Janela fecha sozinha ao iniciar?**
→ Verifique se o arquivo `.env` está na mesma pasta que o `iniciar.bat`

**Robô não recebe mensagens no Telegram?**
→ Entre em contato com o desenvolvedor para configurar o Telegram

**Como saber se o robô ainda está funcionando?**
→ A janela mostra o painel atualizando a cada tentativa. Se parou, feche e abra o `iniciar.bat` novamente.

**O Chrome abre uma janela na tela?**
→ Normal para o Bot Maricá (monitoramento visual). O Bot Niterói roda em modo oculto.

---

*Dúvidas? Entre em contato com o desenvolvedor.*
