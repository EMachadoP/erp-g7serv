@echo off
title Sistema ERP - Descartex
color 0A
echo ==========================================
echo      INICIANDO O SISTEMA...
echo ==========================================
echo.

:: Garantir que estamos na pasta correta
cd /d "g:\Meu Drive\11 - Empresa - Descartex\Projetos IA"

echo 1. Verificando conflitos de porta...
:: Tenta parar o container Docker especifico se estiver rodando
docker stop projetosia-web-1 >nul 2>&1

:: Força o fechamento de qualquer processo ocupando a porta 8000
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo 2. Abrindo o navegador...
:: Abre o navegador padrao
timeout /t 3 >nul
start "" "http://127.0.0.1:8000/"

echo 3. Iniciando servidor...
echo.
echo IMPORTANTE: Nao feche esta janela enquanto estiver usando o sistema.
echo Para sair, feche esta janela ou pressione Ctrl+C.
echo.

:: Inicia o Django
python manage.py runserver 0.0.0.0:8000

pause
