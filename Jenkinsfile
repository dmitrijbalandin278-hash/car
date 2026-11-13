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

                // 2. Запускаем приложение строго на 80-м порту
                bat 'start /B python -c "from app import app; app.run(host=\'127.0.0.1\', port=80)" > app.log 2>&1'
                
                // 3. Ждем 4 секунды для инициализации
                bat 'powershell -Command "Start-Sleep -Seconds 4"'

                // 4. Проверяем логи на ошибки
                bat '''
                    powershell -Command "if (Test-Path app.log) { $err = Get-Content app.log -Raw; if ($err -match 'Error|Traceback|SyntaxError|PermissionError') { Write-Host '=== ОШИБКА В ЛОГАХ ==='; Write-Host $err; exit 1 } }"
                '''

                // 5. Проверяем доступность сайта СТРОГО по адресу http://127.0.0.1/ (порт 80)
                bat '''
                    echo Проверка доступности сайта на http://127.0.0.1/...
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok = $false; for ($i = 0; $i -lt 5; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1/' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}; Start-Sleep -Seconds 1 }; if (-not $ok) { Write-Host '=== ОШИБКА: САЙТ НЕ ОТВЕЧАЕТ НА ПОРТУ 80 ==='; if (Test-Path app.log) { Get-Content app.log }; exit 1 }"
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