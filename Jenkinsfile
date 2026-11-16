pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        DOCKER_CREDENTIALS_ID = 'docker-hub-credentials' 
        IMAGE_NAME            = 'dmitrybalandin278/car-rental-app' 
        IMAGE_TAG             = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                bat 'echo Branch: %BRANCH_NAME%'
            }
        }

        stage('Build Docker image') {
            steps {
                // Прямой вызов docker из папки C:\DockerBin
                bat 'C:\\DockerBin\\docker.exe build -t %IMAGE_NAME%:%IMAGE_TAG% -t %IMAGE_NAME%:latest .'
            }
        }

        stage('Run tests') {
            steps {
                bat 'C:\\DockerBin\\docker.exe run --rm %IMAGE_NAME%:%IMAGE_TAG% python -m pytest -v --junitxml=reports/results.xml'
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/results.xml'
                }
            }
        }

        stage('Push to Docker Hub') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Плагин Jenkins использует свой способ вызова Docker.
                    // Убедитесь, что путь C:\DockerBin\docker.exe прописан в настройках плагина (Manage Jenkins -> System -> Docker).
                    docker.withRegistry('https://registry.hub.docker.com', env.DOCKER_CREDENTIALS_ID) {
                        docker.image("${env.IMAGE_NAME}:${env.IMAGE_TAG}").push()
                        docker.image("${env.IMAGE_NAME}:latest").push()
                    }
                }
            }
        }

        stage('Deploy to main') {
            when {
                branch 'main'
            }
            steps {
                bat 'C:\\DockerBin\\docker.exe compose down || exit 0'
                bat 'C:\\DockerBin\\docker.exe compose up -d --build'

                bat '''
                    echo Проверка доступности сайта через Nginx
                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok = $false; for ($i = 0; $i -lt 15; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1/' -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}; Start-Sleep -Seconds 2 }; if (-not $ok) { exit 1 }"

                    if errorlevel 1 (
                        echo ОШИБКА: сайт не отвечает.
                        C:\\DockerBin\\docker.exe compose ps
                        C:\\DockerBin\\docker.exe compose logs --tail=100
                        exit /b 1
                    )

                    echo Сайт успешно запущен: http://localhost
                '''
            }
        }
    }

    post {
        success { echo 'Сборка, тесты, push и деплой завершены успешно.' }
        failure { echo 'Ошибка на одном из этапов.' }
        always  { echo 'Pipeline завершён.' }
    }
}