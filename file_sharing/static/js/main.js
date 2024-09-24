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
        if (loadingIndicator) {
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

    // Анимация заголовка
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
});