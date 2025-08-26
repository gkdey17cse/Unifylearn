document.addEventListener('DOMContentLoaded', function () {
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotBody = document.getElementById('chatbotBody');
    const toggleIcon = document.getElementById('toggleIcon');
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const pageLoader = document.getElementById('page-loader');

    let isChatbotOpen = true;

    // Toggle chatbot
    chatbotToggle.addEventListener('click', function () {
        isChatbotOpen = !isChatbotOpen;
        chatbotBody.classList.toggle('hidden');
        toggleIcon.classList.toggle('fa-chevron-up');
        toggleIcon.classList.toggle('fa-chevron-down');
        toggleIcon.classList.toggle('rotate-180');
        if (isChatbotOpen) setTimeout(() => userInput.focus(), 100);
    });

    // Send message
    function sendMessage() {
        const query = userInput.value.trim();
        if (!query) return;

        addMessage(query, 'user');
        userInput.value = '';

        // Show global page loader
        if (pageLoader) pageLoader.classList.remove('hidden');

        fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        })
            .then(res => res.json())
            .then(data => {
                if (pageLoader) pageLoader.classList.add('hidden');
                if (data.success) {
                    addMessage(`Found ${data.total_results} courses! Redirecting...`, 'bot');
                    window.location.href = `/${data.timestamp}`;
                } else {
                    addMessage(`Error: ${data.error}`, 'bot');
                }
            })
            .catch(err => {
                if (pageLoader) pageLoader.classList.add('hidden');
                addMessage('Error processing your request.', 'bot');
                console.error(err);
            });
    }

    // Add message to chat
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex mb-4 ${sender === 'user' ? 'justify-end' : ''}`;

        if (sender === 'bot') {
            const botIcon = document.createElement('div');
            botIcon.className = 'w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3 flex-shrink-0';
            botIcon.innerHTML = '<i class="fas fa-robot text-blue-600"></i>';
            messageDiv.appendChild(botIcon);
        }

        const contentDiv = document.createElement('div');
        contentDiv.className = sender === 'user'
            ? 'bg-blue-600 text-white rounded-lg rounded-tr-none px-4 py-2 max-w-[80%]'
            : 'bg-gray-100 rounded-lg rounded-tl-none px-4 py-2 max-w-[80%]';
        contentDiv.innerHTML = text;

        messageDiv.appendChild(contentDiv);

        if (sender === 'user') {
            const userIcon = document.createElement('div');
            userIcon.className = 'w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center ml-3 flex-shrink-0';
            userIcon.innerHTML = '<i class="fas fa-user text-white"></i>';
            messageDiv.appendChild(userIcon);
        }

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageDiv;
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    // Preloaded courses layout
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
        resultsContainer.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-12';
    }

});
