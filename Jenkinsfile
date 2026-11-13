pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        // Ваш путь к Python
        PYTHON = 'C:\\Python314\\python.exe'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                bat 'echo Branch: %BRANCH_NAME%'
            }
        }

        stage('Setup') {
            steps {
                // Установка зависимостей
                bat '"%PYTHON%" -m pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                // Запуск тестов с созданием отчета для Jenkins
                bat 'if not exist reports mkdir reports'
                bat '"%PYTHON%" -m pytest -v --junitxml=reports/results.xml'
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/results.xml'
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                // 1. Убиваем старые процессы Python
                bat 'taskkill /F /IM python.exe /T > nul 2>&1 || exit 0'

                // 2. Создаем временный bat-файл для запуска сервера
                // Это делается прямо в пайплайне, чтобы обойти проблемы с кавычками
                bat '''
                    echo @echo off > run_server.bat
                    echo cd /d %CD% >> run_server.bat
                    echo "%PYTHON%" -c "from app import app; app.run(host='127.0.0.1', port=80)" >> run_server.bat
                '''

                // 3. Запускаем этот bat-файл в фоне, отвязанно от Jenkins
                bat '''
                    powershell -Command "$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c run_server.bat' -WindowStyle Hidden -PassThru; Write-Host 'Запущен процесс с PID:' $p.Id"
                '''
                
                // 4. Ждем 5 секунд
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
        success {
            echo "Pipeline finished OK for branch ${env.BRANCH_NAME}"
        }
        failure {
            echo "Pipeline failed on branch ${env.BRANCH_NAME} - check test report"
        }
    }
}