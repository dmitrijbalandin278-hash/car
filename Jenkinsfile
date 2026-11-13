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

                // 2. Удаляем старую задачу в планировщике (если есть)
                bat 'schtasks /Delete /TN "CarRentalApp" /F > nul 2>&1 || exit 0'

                // 3. Создаем и запускаем задачу в планировщике
                // Это полностью отвязывает процесс от Jenkins, и он не будет убит
                bat '''
                    schtasks /Create /TN "CarRentalApp" /TR "python -c \\"from app import app; app.run(host='127.0.0.1', port=80)\\"" /SC ONCE /ST 00:00 /F
                    schtasks /Run /TN "CarRentalApp"
                '''
                
                // 4. Ждем 5 секунд для инициализации
                bat 'powershell -Command "Start-Sleep -Seconds 5"'

                // 5. Проверяем доступность сайта
                bat '''
                    echo Проверка доступности сайта на http://127.0.0.1/...
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok = $false; for ($i = 0; $i -lt 5; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1/' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}; Start-Sleep -Seconds 1 }; if (-not $ok) { Write-Host '=== ОШИБКА: САЙТ НЕ ОТВЕЧАЕТ НА ПОРТУ 80 ==='; exit 1 }"
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