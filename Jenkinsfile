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
                bat 'powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"'

                bat 'powershell -Command "Start-Process python -ArgumentList \'app.py\' -RedirectStandardOutput \'app.log\' -RedirectStandardError \'app.err.log\' -WindowStyle Hidden"'
                
                bat 'powershell -Command "Start-Sleep -Seconds 5"'
          
                bat '''
                    echo Проверка доступности сайта...
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok = $false; $urls = @('http://127.0.0.1/', 'http://127.0.0.1:5000/'); foreach ($u in $urls) { for ($i = 0; $i -lt 10; $i++) { try { $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}; Start-Sleep -Seconds 1 }; if ($ok) { break } }; if (-not $ok) { exit 1 }"

                    if errorlevel 1 (
                        echo ОШИБКА: сайт не отвечает ни на порту 80, ни на порту 5000.
                        echo --- ЛОГИ ПРИЛОЖЕНИЯ (app.log) ---
                        type app.log
                        echo --- ОШИБКИ ПРИЛОЖЕНИЯ (app.err.log) ---
                        type app.err.log
                        exit /b 1
                    )

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