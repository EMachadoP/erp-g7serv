@echo off
set /p msg="Digite a mensagem do commit: "
if "%msg%"=="" set msg="Update sistema"

echo Adicionando alteracoes...
git add .

echo Fazendo commit...
git commit -m "%msg%"

echo Enviando para GitHub/Railway...
git push origin main

echo Done!
pause
