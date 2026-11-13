pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps { 
                checkout scm 
            }
        }

        stage('Run tests') {
            steps {
                bat "python -m pip install -r requirements.txt"
                bat "python -m pytest -v"
            }
        }

        stage('Deploy to main') {
            when {
                expression {
                    def b = env.GIT_BRANCH ?: env.BRANCH_NAME ?: ''
                    return b == 'main' || b == 'origin/main' || b == 'refs/heads/main'
                }
            }
            steps {
                // 1. Убиваем старые процессы Python, чтобы освободить порт 80
                bat 'taskkill /F /IM python.exe /T > nul 2>&1 || exit 0'

                // 2. Запускаем приложение через PowerShell в фоне
                // -PassThru возвращает объект процесса, -WindowStyle Hidden скрывает окно
                // -RedirectStandardOutput и -RedirectStandardError пишут логи в файлы
                bat '''
                    powershell -Command "$p = Start-Process python -ArgumentList '-c', 'from app import app; app.run(host=\\'127.0.0.1\\', port=80)' -RedirectStandardOutput 'app.log' -RedirectStandardError 'app.err.log' -WindowStyle Hidden -PassThru; Write-Host 'Запущен процесс с PID:' $p.Id"
                '''
                
                // 3. Ждем 5 секунд для инициализации сервера
                bat 'powershell -Command "Start-Sleep -Seconds 5"'

                // 4. Проверяем логи на критические ошибки
                bat '''
                    powershell -Command "if (Test-Path app.err.log) { $err = Get-Content app.err.log -Raw; if ($err -match 'Error|Traceback|SyntaxError|PermissionError') { Write-Host '=== ОШИБКА В ЛОГАХ ==='; Write-Host $err; exit 1 } }"
                '''

                // 5. Проверяем доступность сайта по адресу http://127.0.0.1/ (порт 80)
                bat '''
                    echo Проверка доступности сайта на http://127.0.0.1/...
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok = $false; for ($i = 0; $i -lt 5; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1/' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}; Start-Sleep -Seconds 1 }; if (-not $ok) { Write-Host '=== ОШИБКА: САЙТ НЕ ОТВЕЧАЕТ НА ПОРТУ 80 ==='; if (Test-Path app.err.log) { Get-Content app.err.log }; if (Test-Path app.log) { Get-Content app.log }; exit 1 }"
                    echo Сайт успешно запущен по адресу http://127.0.0.1/
                '''
            }
        }
    }

    post {
        success { echo 'Сборка, тесты и деплой завершены успешно.' }
        failure { echo 'Ошибка на одном из этапов.' }
        always  { echo 'Pipeline завершён.' }
    }
}