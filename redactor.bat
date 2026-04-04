@echo off
chcp 1251 >nul
setlocal enabledelayedexpansion

title FFmpeg Audio Editor

:: Инициализация переменных
set "filters="
set "active_filters_names="
set "current_file="

:SELECT_FILE
if not defined current_file goto INPUT_FILE
cls
echo.
echo Текущий файл: "!current_file!"
echo.
set /p "change_file=Хотите выбрать другой файл? (y/n): "
if /i "!change_file!"=="y" (
    set "current_file="
    set "filters="
    set "active_filters_names="
    goto INPUT_FILE
)
goto MENU

:INPUT_FILE
echo.
set /p "current_file=Введите путь к аудиофайлу: "
set "current_file=!current_file:"=!"
if not exist "!current_file!" (
    echo Файл не найден!
    timeout /t 2 >nul
    goto INPUT_FILE
)
goto MENU

:MENU
cls
echo.
echo Текущий файл: "!current_file!"
echo.
echo -----------------------------------------
echo ДОСТУПНЫЕ ЭФФЕКТЫ:
echo -----------------------------------------
echo 1. Speed Up        (Ускорение x1.5)
echo 2. Slowed          (Замедление x0.75)
echo 3. Reverb          (Реверберация/Эхо)
echo 4. Nightcore       (Ускорение + повышение тона)
echo 5. Bassboost       (Усиление басов)
echo 6. Pitch Up        (Повышение тона)
echo 7. Pitch Down      (Понижение тона)
echo -----------------------------------------
echo 8. ПРИМЕНИТЬ ЭФФЕКТЫ
echo 9. ОЧИСТИТЬ эффекты
echo 0. Выйти
echo -----------------------------------------
echo.

if defined active_filters_names (
    echo ВЫБРАННЫЕ ЭФФЕКТЫ: !active_filters_names!
    echo.
) else (
    echo Нет выбранных эффектов
    echo.
)

set /p "choice=Ваш выбор: "

if "!choice!"=="1" (
    set "filters=atempo=1.5"
    set "active_filters_names=Speed Up"
    echo Добавлен эффект: Speed Up
    timeout /t 1 >nul
    goto MENU
)

if "!choice!"=="2" (
    set "filters=atempo=0.75"
    set "active_filters_names=Slowed"
    echo Добавлен эффект: Slowed
    timeout /t 1 >nul
    goto MENU
)

if "!choice!"=="3" (
    set "filters=aecho=0.8:0.7:100:0.5"
    set "active_filters_names=Reverb"
    echo Добавлен эффект: Reverb
    timeout /t 1 >nul
    goto MENU
)

if "!choice!"=="4" (
    set "filters=atempo=1.25,asetrate=44100,aresample=44100"
    set "active_filters_names=Nightcore"
    echo Добавлен эффект: Nightcore
    timeout /t 1 >nul
    goto MENU
)

if "!choice!"=="5" (
    set "filters=bass=g=15:f=110:w=0.5"
    set "active_filters_names=Bassboost"
    echo Добавлен эффект: Bassboost
    timeout /t 1 >nul
    goto MENU
)

if "!choice!"=="6" (
    set "filters=atempo=1.1,asetrate=44100,aresample=44100"
    set "active_filters_names=Pitch Up"
    echo Добавлен эффект: Pitch Up
    timeout /t 1 >nul
    goto MENU
)

if "!choice!"=="7" (
    set "filters=atempo=0.9,asetrate=44100,aresample=44100"
    set "active_filters_names=Pitch Down"
    echo Добавлен эффект: Pitch Down
    timeout /t 1 >nul
    goto MENU
)

if "!choice!"=="8" goto PROCESS
if "!choice!"=="9" (
    set "filters="
    set "active_filters_names="
    echo Эффекты очищены!
    timeout /t 1 >nul
    goto MENU
)
if "!choice!"=="0" goto EXIT

echo Неверный выбор!
timeout /t 1 >nul
goto MENU

:PROCESS
if not defined filters (
    echo.
    echo ОШИБКА: Не выбрано ни одного эффекта!
    pause
    goto MENU
)

cls
echo.
echo Исходный файл: "!current_file!"
echo Применяемый эффект: !active_filters_names!
echo Фильтр: !filters!
echo.

for %%F in ("!current_file!") do (
    set "filename=%%~nF"
    set "fileext=%%~xF"
    set "filepath=%%~dpF"
)

set "timestamp=!date:~6,4!!date:~3,2!!date:~0,2!_!time:~0,2!!time:~3,2!!time:~6,2!"
set "timestamp=!timestamp: =0!"
set "timestamp=!timestamp::=!"
set "output_file=!filepath!edited_!filename!_!timestamp!!fileext!"

echo Обработка файла... Пожалуйста, подождите.
echo.

ffmpeg -y -hide_banner -loglevel error -i "!current_file!" -filter:a "!filters!" "!output_file!"

if !errorlevel! equ 0 (
    echo.
    echo [УСПЕШНО!] Файл сохранен:
    echo "!output_file!"
    echo.
    
    set /p "edit_new=Хотите редактировать полученный файл? (y/n): "
    if /i "!edit_new!"=="y" (
        set "current_file=!output_file!"
        set "filters="
        set "active_filters_names="
        echo.
        echo Теперь редактируем: "!current_file!"
        timeout /t 2 >nul
        goto MENU
    ) else (
        set "filters="
        set "active_filters_names="
        goto SELECT_FILE
    )
) else (
    echo.
    echo [ОШИБКА] Не удалось обработать файл!
    echo.
    pause
    goto MENU
)

:EXIT
echo.
echo Выход из программы...
timeout /t 2 >nul
exit /b