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
                // 1. Безопасно завершаем старые процессы Python (не падает, если их нет)
                bat 'taskkill /F /IM python.exe /T > nul 2>&1 || exit 0'

                // 2. Запускаем приложение в фоне на порту 5000
                bat 'powershell -Command "Start-Process python -ArgumentList \'-c\', \'from app import app; app.run(port=5000)\' -RedirectStandardOutput \'app.log\' -RedirectStandardError \'app.err.log\' -WindowStyle Hidden"'
                
                // 3. Ждем 4 секунды для инициализации сервера
                bat 'powershell -Command "Start-Sleep -Seconds 4"'

                // 4. Проверяем логи на наличие критических ошибок ДО проверки сайта
                bat '''
                    powershell -Command "if (Test-Path app.err.log) { $err = Get-Content app.err.log -Raw; if ($err -match 'Error|Traceback|PermissionError') { Write-Host '=== ОШИБКА В ЛОГАХ ==='; Write-Host $err; exit 1 } }"
                '''

                // 5. Проверяем доступность сайта на порту 5000
                bat '''
                    echo Проверка доступности сайта на http://127.0.0.1:5000/...
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok = $false; for ($i = 0; $i -lt 5; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}; Start-Sleep -Seconds 1 }; if (-not $ok) { Write-Host '=== ОШИБКА: САЙТ НЕ ОТВЕЧАЕТ НА ПОРТУ 5000 ==='; if (Test-Path app.err.log) { Get-Content app.err.log }; exit 1 }"
                    echo Сайт успешно запущен!
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
