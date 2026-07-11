@echo off
title BOT PROEISBM — Iniciador

echo.
echo  ====================================================
echo   BOT PROEISBM v7.1 — Iniciando os dois robos...
echo  ====================================================
echo.

:: Verifica se os .exe existem
if not exist "BotMarica.exe" (
    echo  ERRO: BotMarica.exe nao encontrado!
    echo  Certifique-se que o arquivo esta na mesma pasta.
    pause
    exit /b 1
)

if not exist "BotNiteroi.exe" (
    echo  ERRO: BotNiteroi.exe nao encontrado!
    echo  Certifique-se que o arquivo esta na mesma pasta.
    pause
    exit /b 1
)

:: Apaga perfis Chrome antigos para garantir sessao limpa
echo  Limpando sessoes Chrome anteriores...
if exist "chrome-profile-marica"  rmdir /s /q "chrome-profile-marica"
if exist "chrome-profile-niteroi" rmdir /s /q "chrome-profile-niteroi"
if exist "chrome-profile"         rmdir /s /q "chrome-profile"

:: Encerra processos Chrome anteriores
taskkill /f /im chrome.exe >nul 2>&1
taskkill /f /im chromedriver.exe >nul 2>&1
timeout /t 2 >nul

echo  Iniciando Bot Marica...
start "BOT PROEISBM — Marica" cmd /k "color 0A && BotMarica.exe"

echo  Aguardando 15s para iniciar o segundo bot...
timeout /t 15 >nul

echo  Iniciando Bot Niteroi...
start "BOT PROEISBM — Niteroi" cmd /k "color 0B && BotNiteroi.exe"

echo.
echo  ====================================================
echo   Ambos os robos estao rodando!
echo   Para encerrar: feche as janelas ou pressione CTRL+C
echo  ====================================================
echo.
timeout /t 3 >nul
exit