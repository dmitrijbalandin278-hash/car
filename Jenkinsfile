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
               
                bat '''
                    echo Проверка доступности сайта через Nginx
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok = $false; for ($i = 0; $i -lt 15; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1/' -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}; Start-Sleep -Seconds 2 }; if (-not $ok) { exit 1 }"

                    if errorlevel 1 (
                        echo ОШИБКА: сайт не отвечает.
                        exit /b 1
                    )

                    echo Сайт успешно запущен: http://localhost
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