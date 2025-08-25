document.addEventListener('DOMContentLoaded', function () {
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotBody = document.getElementById('chatbotBody');
    const toggleIcon = document.getElementById('toggleIcon');
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');

    let isChatbotOpen = true;

    // Toggle chatbot
    chatbotToggle.addEventListener('click', function () {
        isChatbotOpen = !isChatbotOpen;
        chatbotBody.classList.toggle('hidden');
        toggleIcon.classList.toggle('fa-chevron-up');
        toggleIcon.classList.toggle('fa-chevron-down');
        toggleIcon.classList.toggle('rotate-180');
    });

    // Send message function
    function sendMessage() {
        const query = userInput.value.trim();
        if (!query) return;

        // Add user message to chat
        addMessage(query, 'user');
        userInput.value = '';

        // Show bot is typing
        const typingIndicator = addMessage('Searching for courses<span class="loading-dots"></span>', 'bot');

        // Send query to backend
        fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                chatMessages.removeChild(typingIndicator);

                if (data.success) {
                    // Show success message
                    addMessage(`Found ${data.total_results} courses! Displaying them now.`, 'bot');

                    // Update the course results on the page
                    updateCourseResults(data.results);
                } else {
                    addMessage(`Sorry, I couldn't process your request: ${data.error}`, 'bot');
                }
            })
            .catch(error => {
                chatMessages.removeChild(typingIndicator);
                addMessage('Sorry, there was an error processing your request. Please try again.', 'bot');
                console.error('Error:', error);
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

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageDiv;
    }

    // Update course results on page
    function updateCourseResults(courses) {
        // Clear any existing results
        const resultsContainer = document.getElementById('results-container');
        resultsContainer.innerHTML = '';

        if (!courses || courses.length === 0) {
            resultsContainer.innerHTML = `
            <div class="text-center py-12 col-span-3">
                <i class="fas fa-search text-gray-400 text-5xl mb-4"></i>
                <p class="text-gray-600">No courses found. Try a different search query.</p>
            </div>
        `;
            return;
        }

        // Add a summary of the search
        const summary = document.createElement('div');
        summary.className = 'col-span-3 text-center mb-8';
        summary.innerHTML = `
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h2 class="text-2xl font-bold text-blue-800 mb-2">Search Results</h2>
            <p class="text-blue-600">Found ${courses.length} courses matching your query</p>
        </div>
    `;
        resultsContainer.appendChild(summary);

        // Create course cards for each result
        courses.forEach(course => {
            const courseCol = document.createElement('div');
            courseCol.className = 'course-col';

            // You can use fetch to get the course card HTML from a partial
            // For now, we'll create it directly in JS
            courseCol.innerHTML = `
            <div class="course-card bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 h-full flex flex-col">
                <div class="p-6 flex-grow">
                    <!-- Header with title and provider -->
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-xl font-bold text-gray-800 mb-2 line-clamp-2 hover:text-blue-600 transition-colors">
                            ${course.title || 'Untitled Course'}
                        </h3>
                        <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full whitespace-nowrap ml-2">
                            ${course.site || course.provider || 'Unknown'}
                        </span>
                    </div>
                    
                    <!-- Description -->
                    <p class="text-gray-600 mb-4 line-clamp-3 text-sm">
                        ${course.description || 'No description available.'}
                    </p>
                    
                    <!-- Key Details Grid -->
                    <div class="grid grid-cols-2 gap-3 mb-4">
                        ${course.duration ? `
                            <div class="flex items-center text-sm text-gray-600">
                                <i class="far fa-clock mr-2 text-blue-500"></i>
                                <span class="truncate">${course.duration}</span>
                            </div>
                        ` : ''}
                        
                        ${course.level ? `
                            <div class="flex items-center text-sm text-gray-600">
                                <i class="fas fa-chart-line mr-2 text-green-500"></i>
                                <span>${course.level}</span>
                            </div>
                        ` : ''}
                        
                        ${course.category ? `
                            <div class="flex items-center text-sm text-gray-600">
                                <i class="fas fa-tag mr-2 text-purple-500"></i>
                                <span class="truncate">${course.category}</span>
                            </div>
                        ` : ''}
                        
                        ${course.language ? `
                            <div class="flex items-center text-sm text-gray-600">
                                <i class="fas fa-language mr-2 text-red-500"></i>
                                <span>${course.language}</span>
                            </div>
                        ` : ''}
                    </div>
                    
                    <!-- Price and Viewers -->
                    <div class="flex justify-between items-center mb-4 text-sm">
                        ${course.price ? `
                            <span class="text-green-600 font-semibold">
                                <i class="fas fa-tag mr-1"></i>
                                ${course.price.length > 30 ? course.price.substring(0, 30) + '...' : course.price}
                            </span>
                        ` : ''}
                        
                        ${course.viewers ? `
                            <span class="text-gray-500">
                                <i class="fas fa-eye mr-1"></i>
                                ${course.viewers.toLocaleString()} viewers
                            </span>
                        ` : ''}
                    </div>
                    
                    <!-- Skills -->
                    ${course.skills && course.skills.length > 0 ? `
                        <div class="mb-4">
                            <h4 class="text-sm font-semibold text-gray-700 mb-2">
                                <i class="fas fa-tools mr-1 text-blue-500"></i>
                                Key Skills
                            </h4>
                            <div class="flex flex-wrap gap-2">
                                ${course.skills.slice(0, 4).map(skill => `
                                    <span class="bg-gray-100 text-gray-800 text-xs px-2.5 py-1 rounded-full">
                                        ${skill}
                                    </span>
                                `).join('')}
                                ${course.skills.length > 4 ? `
                                    <span class="text-xs text-gray-500">+${course.skills.length - 4} more</span>
                                ` : ''}
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Instructors -->
                    ${course.instructors && course.instructors.length > 0 ? `
                        <div class="mb-4">
                            <h4 class="text-sm font-semibold text-gray-700 mb-1">
                                <i class="fas fa-chalkboard-teacher mr-1 text-purple-500"></i>
                                Instructors
                            </h4>
                            <p class="text-xs text-gray-600 line-clamp-2">
                                ${course.instructors.join(', ')}
                            </p>
                        </div>
                    ` : ''}
                </div>
                
                <!-- Footer with CTA -->
                <div class="bg-gray-50 px-6 py-4 border-t border-gray-100">
                    ${course.url ? `
                        <a href="${course.url}" target="_blank" 
                           class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center justify-center">
                            View Course 
                            <i class="fas fa-external-link-alt ml-2 text-xs"></i>
                        </a>
                    ` : ''}
                </div>
            </div>
        `;

            resultsContainer.appendChild(courseCol);
        });

        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Focus input when chatbot is opened
    chatbotToggle.addEventListener('click', function () {
        if (isChatbotOpen) {
            setTimeout(() => userInput.focus(), 100);
        }
    });
});