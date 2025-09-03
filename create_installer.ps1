# PowerShell скрипт для создания простого установщика SkimNote
# Этот скрипт создает самораспаковывающийся архив с установщиком

param(
    [string]$Version = "1.02",
    [string]$OutputName = "SkimNote_Setup"
)

Write-Host "=== Создание установщика SkimNote ===" -ForegroundColor Green

# Проверяем наличие исполняемого файла
if (-not (Test-Path "dist\SkimNote.exe")) {
    Write-Host "Ошибка: Файл dist\SkimNote.exe не найден!" -ForegroundColor Red
    Write-Host "Сначала запустите: python build_exe.py" -ForegroundColor Yellow
    exit 1
}

# Создаем папку для установщика
$installerDir = "installer"
if (-not (Test-Path $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir | Out-Null
}

# Создаем временную папку для файлов установки
$tempDir = "temp_installer"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Копируем файлы в временную папку
Write-Host "Копирование файлов..." -ForegroundColor Yellow
Copy-Item "dist\SkimNote.exe" -Destination "$tempDir\"
Copy-Item "icons" -Destination "$tempDir\" -Recurse
Copy-Item "LICENSE.txt" -Destination "$tempDir\"
if (Test-Path "README.md") {
    Copy-Item "README.md" -Destination "$tempDir\"
}

# Создаем bat-файл для установки
$installScript = @"
@echo off
chcp 65001 >nul
echo ========================================
echo    Установка SkimNote v$Version
echo ========================================
echo.

set /p "installDir=Введите путь для установки (по умолчанию: %ProgramFiles%\SkimNote): "
if "%installDir%"=="" set "installDir=%ProgramFiles%\SkimNote"

echo.
echo Установка в: %installDir%
echo.

if not exist "%installDir%" mkdir "%installDir%"

echo Копирование файлов...
copy "SkimNote.exe" "%installDir%\"
xcopy "icons" "%installDir%\icons\" /E /I /Y
copy "LICENSE.txt" "%installDir%\"
if exist "README.md" copy "README.md" "%installDir%\"

echo.
echo Создание ярлыков...

REM Создание ярлыка в меню Пуск
set "startMenu=%APPDATA%\Microsoft\Windows\Start Menu\Programs\SkimNote"
if not exist "%startMenu%" mkdir "%startMenu%"

echo @echo off > "%startMenu%\SkimNote.bat"
echo cd /d "%installDir%" >> "%startMenu%\SkimNote.bat"
echo start "" "SkimNote.exe" >> "%startMenu%\SkimNote.bat"

REM Создание ярлыка на рабочем столе
set "desktop=%USERPROFILE%\Desktop"
echo @echo off > "%desktop%\SkimNote.bat"
echo cd /d "%installDir%" >> "%desktop%\SkimNote.bat"
echo start "" "SkimNote.exe" >> "%desktop%\SkimNote.bat"

echo.
echo ========================================
echo    Установка завершена!
echo ========================================
echo.
echo Программа установлена в: %installDir%
echo Ярлыки созданы на рабочем столе и в меню Пуск
echo.
pause
"@

$installScript | Out-File -FilePath "$tempDir\install.bat" -Encoding UTF8

# Создаем bat-файл для удаления
$uninstallScript = @"
@echo off
chcp 65001 >nul
echo ========================================
echo    Удаление SkimNote
echo ========================================
echo.

set "installDir=%ProgramFiles%\SkimNote"

if not exist "%installDir%" (
    echo Программа не найдена в %installDir%
    echo Возможно, она была установлена в другую папку
    pause
    exit /b 1
)

echo Удаление файлов из: %installDir%
rmdir /s /q "%installDir%"

echo.
echo Удаление ярлыков...

REM Удаление ярлыка из меню Пуск
set "startMenu=%APPDATA%\Microsoft\Windows\Start Menu\Programs\SkimNote"
if exist "%startMenu%" rmdir /s /q "%startMenu%"

REM Удаление ярлыка с рабочего стола
set "desktop=%USERPROFILE%\Desktop"
if exist "%desktop%\SkimNote.bat" del "%desktop%\SkimNote.bat"

echo.
echo ========================================
echo    Удаление завершено!
echo ========================================
echo.
pause
"@

$uninstallScript | Out-File -FilePath "$tempDir\uninstall.bat" -Encoding UTF8

# Создаем основной bat-файл установщика
$mainInstaller = @"
@echo off
chcp 65001 >nul
title Установщик SkimNote v$Version

echo ========================================
echo    Установщик SkimNote v$Version
echo ========================================
echo.
echo Этот установщик распакует и установит
echo программу SkimNote на ваш компьютер.
echo.
echo Нажмите любую клавишу для начала установки...
pause >nul

REM Создаем временную папку
set "tempDir=%TEMP%\SkimNote_Install"
if exist "%tempDir%" rmdir /s /q "%tempDir%"
mkdir "%tempDir%"

REM Копируем файлы во временную папку
echo Распаковка файлов...
copy "SkimNote.exe" "%tempDir%\"
xcopy "icons" "%tempDir%\icons\" /E /I /Y
copy "LICENSE.txt" "%tempDir%\"
if exist "README.md" copy "README.md" "%tempDir%\"
copy "install.bat" "%tempDir%\"

REM Запускаем установку
cd /d "%tempDir%"
call install.bat

REM Очистка
cd /d "%~dp0"
rmdir /s /q "%tempDir%"

echo.
echo Установка завершена!
pause
"@

$mainInstaller | Out-File -FilePath "$tempDir\setup.bat" -Encoding UTF8

# Создаем архив
Write-Host "Создание архива..." -ForegroundColor Yellow
$archivePath = "$installerDir\$OutputName.zip"

# Используем PowerShell для создания архива
Compress-Archive -Path "$tempDir\*" -DestinationPath $archivePath -Force

# Создаем самораспаковывающийся bat-файл
$selfExtracting = @"
@echo off
chcp 65001 >nul
title Установщик SkimNote v$Version

echo ========================================
echo    Установщик SkimNote v$Version
echo ========================================
echo.
echo Распаковка файлов...

REM Создаем временную папку
set "tempDir=%TEMP%\SkimNote_Install_%RANDOM%"
if exist "%tempDir%" rmdir /s /q "%tempDir%"
mkdir "%tempDir%"

REM Распаковываем архив
powershell -command "Expand-Archive -Path '%~f0' -DestinationPath '%tempDir%' -Force"

REM Запускаем установку
cd /d "%tempDir%"
if exist "setup.bat" (
    call setup.bat
) else (
    echo Ошибка: Файл установки не найден
    pause
)

REM Очистка
cd /d "%~dp0"
rmdir /s /q "%tempDir%"

exit /b 0

"@

# Добавляем содержимое архива в конец bat-файла
$selfExtracting | Out-File -FilePath "$installerDir\$OutputName.bat" -Encoding UTF8

# Копируем архив в bat-файл
$archiveBytes = [System.IO.File]::ReadAllBytes($archivePath)

# Добавляем команду для извлечения архива
$extractCommand = @"

REM Извлекаем архив из bat-файла
powershell -command "Expand-Archive -Path '%tempDir%\archive.zip' -DestinationPath '%tempDir%' -Force"
del "%tempDir%\archive.b64"
del "%tempDir%\archive.zip"

"@

$extractCommand | Out-File -FilePath "$installerDir\$OutputName.bat" -Append -Encoding UTF8

# Очистка временных файлов
Remove-Item -Path $tempDir -Recurse -Force
Remove-Item -Path $archivePath -Force

Write-Host "Установщик создан успешно!" -ForegroundColor Green
Write-Host "Файл: $installerDir\$OutputName.bat" -ForegroundColor Cyan

# Показываем размер файла
$fileSize = (Get-Item "$installerDir\$OutputName.bat").Length / 1MB
Write-Host "Размер: $([math]::Round($fileSize, 1)) МБ" -ForegroundColor Cyan

Write-Host "`nТеперь вы можете распространять файл $OutputName.bat" -ForegroundColor Yellow 