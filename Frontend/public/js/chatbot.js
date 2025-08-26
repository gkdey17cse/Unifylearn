// Frontend/public/js/chatbot.js

export function initChatbot() {
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotBody = document.getElementById('chatbotBody');
    const toggleIcon = document.getElementById('toggleIcon');
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');

    chatbotToggle.addEventListener('click', () => {
        chatbotBody.classList.toggle('hidden');
        toggleIcon.classList.toggle('rotate-180');
    });

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function addMessage(text, sender = 'user') {
        const msgDiv = document.createElement('div');
        msgDiv.className = sender === 'user' ? 'text-right mb-2' : 'text-left mb-2';
        msgDiv.innerHTML = `<span class="inline-block px-4 py-2 rounded-lg ${sender === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'}">${text}</span>`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function sendMessage() {
        const msg = userInput.value.trim();
        if (!msg) return;
        addMessage(msg, 'user');
        userInput.value = '';

        // Example bot response
        setTimeout(() => addMessage("This is a bot response.", 'bot'), 500);
    }

    return { addMessage, sendMessage };
}
