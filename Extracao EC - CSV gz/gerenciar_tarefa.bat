@echo off
chcp 65001 >nul
title Gerenciar Tarefa - ExtracaoEC
:MENU
cls
echo ============================================
echo    GERENCIAR TAREFA - ExtracaoEC
echo ============================================
echo.
echo  [1] Criar tarefa
echo  [2] Alterar dia e horario
echo  [3] Deletar tarefa
echo  [0] Sair
echo.
echo ============================================
set /p opcao="Selecione uma opcao: "

if "%opcao%"=="1" goto CRIAR
if "%opcao%"=="2" goto DIAHORA
if "%opcao%"=="3" goto DELETAR
if "%opcao%"=="0" goto FIM
echo Opcao invalida!
pause
goto MENU

:CRIAR
cls
echo ============================================
echo    CRIAR TAREFA
echo ============================================
echo.
echo  Dias:
echo  [1] Domingo     [4] Quarta-feira  [7] Sabado
echo  [2] Segunda     [5] Quinta-feira
echo  [3] Terca       [6] Sexta-feira
echo.
set /p dia="Selecione o dia: "

if "%dia%"=="1" set "DIAESCOLHIDO=Sunday"
if "%dia%"=="2" set "DIAESCOLHIDO=Monday"
if "%dia%"=="3" set "DIAESCOLHIDO=Tuesday"
if "%dia%"=="4" set "DIAESCOLHIDO=Wednesday"
if "%dia%"=="5" set "DIAESCOLHIDO=Thursday"
if "%dia%"=="6" set "DIAESCOLHIDO=Friday"
if "%dia%"=="7" set "DIAESCOLHIDO=Saturday"

if not defined DIAESCOLHIDO (
    echo Opcao invalida!
    pause
    goto MENU
)

echo.
echo  Formato: HH:MM (ex: 14:30)
set /p horario="Horario: "

powershell -Command "$action = New-ScheduledTaskAction -Execute 'C:\Alexandre\Repositorios\DaVita\Extracao EC - CSV gz\venv\Scripts\python.exe' -Argument '\"C:\Alexandre\Repositorios\DaVita\Extracao EC - CSV gz\extracao.py\"' -WorkingDirectory 'C:\Alexandre\Repositorios\DaVita\Extracao EC - CSV gz'; $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek %DIAESCOLHIDO% -At '%horario%'; Register-ScheduledTask -TaskName 'ExtracaoEC' -Action $action -Trigger $trigger -Description 'Extracao EC (CSV.gz)'"
echo.
echo Tarefa criada para %DIAESCOLHIDO% as %horario%
pause
goto MENU

:DIAHORA
cls
echo ============================================
echo    ALTERAR DIA E HORARIO
echo ============================================
echo.
echo  Dias:
echo  [1] Domingo     [4] Quarta-feira  [7] Sabado
echo  [2] Segunda     [5] Quinta-feira
echo  [3] Terca       [6] Sexta-feira
echo.
set /p dia="Selecione o dia: "

if "%dia%"=="1" set "DIAESCOLHIDO=Sunday"
if "%dia%"=="2" set "DIAESCOLHIDO=Monday"
if "%dia%"=="3" set "DIAESCOLHIDO=Tuesday"
if "%dia%"=="4" set "DIAESCOLHIDO=Wednesday"
if "%dia%"=="5" set "DIAESCOLHIDO=Thursday"
if "%dia%"=="6" set "DIAESCOLHIDO=Friday"
if "%dia%"=="7" set "DIAESCOLHIDO=Saturday"

if not defined DIAESCOLHIDO (
    echo Opcao invalida!
    pause
    goto MENU
)

echo.
echo  Formato: HH:MM (ex: 14:30)
set /p novahora="Novo horario: "

powershell -Command "$t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek %DIAESCOLHIDO% -At '%novahora%'; Set-ScheduledTask -TaskName 'ExtracaoEC' -Trigger $t"
echo.
echo Alterado para %DIAESCOLHIDO% as %novahora%
pause
goto MENU

:DELETAR
cls
echo ============================================
echo    DELETAR TAREFA
echo ============================================
echo.
set /p confirma="Tem certeza que deseja deletar a tarefa? (S/N): "
if /i "%confirma%"=="S" (
    powershell -Command "Unregister-ScheduledTask -TaskName 'ExtracaoEC' -Confirm:$false"
    echo Tarefa deletada com sucesso!
) else (
    echo Operacao cancelada.
)
pause
goto MENU

:FIM
exit
