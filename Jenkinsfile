pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        // ДОБАВЛЯЕМ ВАШ ПУТЬ К DOCKER
        PATH = "C:\\Users\\Дмитрий\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin;${env.PATH}"
        
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
                // Собираем образ с тегом текущей сборки и тегом latest
                bat "docker build -t ${env.IMAGE_NAME}:${env.IMAGE_TAG} -t ${env.IMAGE_NAME}:latest ."
            }
        }

        stage('Run tests') {
            steps {
                // Тесты запускаем внутри контейнера (окружение идентично продакшну)
                bat "docker run --rm ${env.IMAGE_NAME}:${env.IMAGE_TAG} python -m pytest -v --junitxml=reports/results.xml"
            }
            post {
                always {
                    // Публикуем отчет о тестах в Jenkins
                    junit allowEmptyResults: true, testResults: 'reports/results.xml'
                }
            }
        }

        stage('Push to Docker Hub') {
            when {
                branch 'main' // Загружаем на Docker Hub только из ветки main
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', env.DOCKER_CREDENTIALS_ID) {
                        // Пушим и версию сборки, и latest
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
                // Останавливаем старые контейнеры, чтобы не было конфликта портов
                bat 'docker compose down || exit 0'
                
                // Запускаем новые контейнеры в фоне (--build заставит собрать образ, если его нет)
                bat 'docker compose up -d --build'

                // Проверка доступности
                bat '''
                    echo Проверка доступности сайта через Nginx

                    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok = $false; for ($i = 0; $i -lt 15; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1/' -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}; Start-Sleep -Seconds 2 }; if (-not $ok) { exit 1 }"

                    if errorlevel 1 (
                        echo ОШИБКА: сайт не отвечает.
                        docker compose ps
                        docker compose logs --tail=100
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