document.addEventListener("DOMContentLoaded", function () {
    const selectLifetime = document.getElementById("file_lifetime");
    const oneTimeNotice = document.getElementById("oneTimeNotice");
    const submitButton = document.querySelector('#uploadForm button[type="submit"]');
    const fileInput = document.querySelector('#uploadForm input[type="file"]');
    const loadingIndicator = document.getElementById('loadingIndicator');

    // Функция для отображения уведомления при выборе одноразовой ссылки
    function toggleOneTimeNotice() {
        if (selectLifetime.value === "one_time") {
            oneTimeNotice.style.display = "block";
        } else {
            oneTimeNotice.style.display = "none";
        }
    }

    // Функция для активации/деактивации кнопки отправки
    function toggleSubmitButtonState() {
        if (fileInput.files.length > 0 && selectLifetime.value !== "") {
            submitButton.disabled = false;
        } else {
            submitButton.disabled = true;
        }
    }

    // Скрытие индикатора загрузки после полной загрузки страницы
    window.onload = function () {
        if (loadingIndicator && loadingIndicator.style) {
            loadingIndicator.style.display = 'none'; // Скрываем индикатор
        }
    };

    // Инициализация событий при загрузке
    selectLifetime.addEventListener("change", function () {
        toggleOneTimeNotice();
        toggleSubmitButtonState();
    });

    fileInput.addEventListener("change", toggleSubmitButtonState);

    // Проверка и инициализация видимости уведомления и состояния кнопки
    toggleOneTimeNotice();
    toggleSubmitButtonState();

    // Проверка, является ли клиент ботом
    function isBot() {
        const userAgent = navigator.userAgent.toLowerCase();
        const bots = [
            'googlebot',           // Google
            'bingbot',             // Bing
            'slurp',               // Yahoo
            'duckduckbot',         // DuckDuckGo
            'baiduspider',         // Baidu
            'yandexbot',           // Yandex
            'sogou',               // Sogou
            'exabot',              // Exalead
            'facebot',             // Facebook
            'ia_archiver',         // Alexa
            'applebot',            // Apple
            'twitterbot',          // Twitter
            'rogerbot',            // Moz
            'ahrefsbot',           // Ahrefs
            'semrushbot',          // SEMrush
            'mj12bot',             // Majestic-12
            'dotbot',              // Open Site Explorer (Moz)
            'gigabot',             // Gigabot
            'archive.org_bot',     // Internet Archive
            'surveybot',           // Facebook SurveyBot
            'linkdexbot',          // Linkdex
            'seznambot',           // Seznam
            'pinterestbot',        // Pinterest
            'redditbot',           // Reddit
            'whatsapp',            // WhatsApp
            'telegrambot',         // Telegram
            'discordbot',          // Discord
            'w3c_validator',       // W3C Validator
            'coccocbot-web',       // Cốc Cốc (Vietnamese search engine)
            'ia_archiver-web.archive.org', // Wayback Machine
            'screamingfrog',       // Screaming Frog SEO Spider
            'google-structured-data-testing-tool', // Google Structured Data Testing Tool
            'datadome',            // DataDome bot detection
            'linkfluence',         // Linkfluence
            'python-requests',     // Python requests library (used in scraping)
            'curl',                // Curl command-line tool (used in scraping)
            'wget',                // Wget command-line tool (used in scraping)
            'python',              // Generic Python user-agent (used in scraping)
            'phantomjs',           // Headless browser
            'headlesschrome',      // Headless Chrome
            'chrome-lighthouse',   // Google Lighthouse
            'uptimerobot',         // Uptime Robot
            'check_http',          // Nagios check HTTP
            'node-fetch',          // Node.js fetch
            'github-camo',         // GitHub image proxy
            'discordbot',          // Discord Bot
            'okhttp',              // OkHttp library (used in scraping)
            'java',                // Generic Java user-agent (used in scraping)
            'bot',                 // Generic 'bot' keyword for unidentified bots
            'crawler',             // Generic 'crawler' keyword
            'spider',              // Generic 'spider' keyword
            'fetch',               // Generic 'fetch' keyword
            'scrapy',              // Scrapy (Python web scraping framework)
        ];

        return bots.some(bot => userAgent.includes(bot));
    }

    if (!isBot()) {
        // Анимация заголовка только для пользователей
        const originalTitle = document.title = "AnonLoader";
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        const changeInterval = 100;
        const transitionDuration = 2000;
        const endDelay = 2000;

        function generateRandomCharacter() {
            return characters.charAt(Math.floor(Math.random() * characters.length));
        }

        function animateTitleToRandom(index = 0) {
            if (index < originalTitle.length) {
                document.title = document.title.substring(0, index) + generateRandomCharacter() + originalTitle.substring(index + 1);
                setTimeout(() => animateTitleToRandom(index + 1), changeInterval);
            } else {
                animateTitleToOriginal(originalTitle.length - 1);
            }
        }

        function animateTitleToOriginal(index) {
            if (index >= 0) {
                document.title = document.title.substring(0, index) + originalTitle.charAt(index) + document.title.substring(index + 1);
                setTimeout(() => animateTitleToOriginal(index - 1), changeInterval);
            } else {
                setTimeout(startCycle, transitionDuration + endDelay);
            }
        }

        function startCycle() {
            setTimeout(() => {
                animateTitleToRandom();
            }, transitionDuration);
        }

        startCycle();
    } else {
        // Устанавливаем фиксированный заголовок для ботов
        document.title = "AnonLoader - Бесплатный и анонимный файлообменник";
    }
});
