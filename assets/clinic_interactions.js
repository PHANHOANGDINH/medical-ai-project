(function () {
    function logReady() {
        console.log("CardioCare AI interface loaded.");
    }

    function enhanceChatPopover() {
        const buttons = window.parent.document.querySelectorAll("button");

        buttons.forEach(function (button) {
            const text = button.innerText || "";

            if (text.trim() === "💬") {
                button.setAttribute("title", "Mở chatbot RAG tư vấn tim mạch");
                button.setAttribute("aria-label", "Mở chatbot RAG tư vấn tim mạch");
            }
        });
    }

    function focusSearchShortcut() {
        document.addEventListener("keydown", function (event) {
            const key = event.key.toLowerCase();

            if (event.altKey && key === "s") {
                const inputs = window.parent.document.querySelectorAll("input");
                if (inputs && inputs.length > 0) {
                    inputs[0].focus();
                    event.preventDefault();
                }
            }
        });
    }

    function scrollToTopAfterPrediction() {
        const buttons = window.parent.document.querySelectorAll("button");

        buttons.forEach(function (button) {
            const text = button.innerText || "";

            if (text.includes("Dự đoán ngay")) {
                button.addEventListener("click", function () {
                    setTimeout(function () {
                        window.parent.scrollTo({
                            top: 0,
                            behavior: "smooth"
                        });
                    }, 700);
                });
            }
        });
    }

    function init() {
        logReady();
        enhanceChatPopover();
        focusSearchShortcut();
        scrollToTopAfterPrediction();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    setInterval(function () {
        enhanceChatPopover();
    }, 1500);
})();