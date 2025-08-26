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

        // Create a grid container for the courses
        const coursesGrid = document.createElement('div');
        coursesGrid.className = 'results-grid';
        resultsContainer.appendChild(coursesGrid);

        // Create course cards for each result
        courses.forEach(course => {
            try {
                const courseCol = document.createElement('div');
                courseCol.className = 'course-col';

                // Handle inconsistent data types
                const instructors = Array.isArray(course.instructors)
                    ? course.instructors.join(', ')
                    : (course.instructors || 'Unknown');

                const skills = Array.isArray(course.skills) ? course.skills : [];
                const price = course.price || 'Free';
                const viewers = course.viewers || 0;
                const duration = course.duration || '';
                const level = course.level || '';
                const category = course.category || '';
                const language = course.language || '';
                const title = course.title || 'Untitled Course';
                const site = course.site || course.provider || 'Unknown';
                const description = course.description || 'No description available.';
                const url = course.url || '';

                // Generate skills HTML
                let skillsHTML = '';
                if (skills.length > 0) {
                    const skillsList = skills.slice(0, 4).map(skill =>
                        `<span class="bg-gray-100 text-gray-800 text-xs px-2.5 py-1 rounded-full">${skill}</span>`
                    ).join('');

                    skillsHTML = `
                <div class="mb-4">
                    <h4 class="text-sm font-semibold text-gray-700 mb-2">
                        <i class="fas fa-tools mr-1 text-blue-500"></i>
                        Key Skills
                    </h4>
                    <div class="flex flex-wrap gap-2">
                        ${skillsList}
                        ${skills.length > 4 ? `<span class="text-xs text-gray-500">+${skills.length - 4} more</span>` : ''}
                    </div>
                </div>`;
                }

                // Generate details HTML
                let detailsHTML = '';
                if (duration || level || category || language) {
                    detailsHTML = `
                <div class="grid grid-cols-2 gap-3 mb-4">
                    ${duration ? `
                        <div class="flex items-center text-sm text-gray-600">
                            <i class="far fa-clock mr-2 text-blue-500"></i>
                            <span class="truncate">${duration}</span>
                        </div>
                    ` : ''}
                    
                    ${level ? `
                        <div class="flex items-center text-sm text-gray-600">
                            <i class="fas fa-chart-line mr-2 text-green-500"></i>
                            <span>${level}</span>
                        </div>
                    ` : ''}
                    
                    ${category ? `
                        <div class="flex items-center text-sm text-gray-600">
                            <i class="fas fa-tag mr-2 text-purple-500"></i>
                            <span class="truncate">${category}</span>
                        </div>
                    ` : ''}
                    
                    ${language ? `
                        <div class="flex items-center text-sm text-gray-600">
                            <i class="fas fa-language mr-2 text-red-500"></i>
                            <span>${language}</span>
                        </div>
                    ` : ''}
                </div>`;
                }

                // Generate price HTML
                let priceHTML = '<span class="text-green-600 font-semibold"><i class="fas fa-tag mr-1"></i>Free</span>';
                if (price !== 'Free') {
                    const displayPrice = price.length > 30 ? price.substring(0, 30) + '...' : price;
                    priceHTML = `<span class="text-green-600 font-semibold"><i class="fas fa-tag mr-1"></i>${displayPrice}</span>`;
                }

                // Generate instructors HTML
                let instructorsHTML = '';
                if (instructors !== 'Unknown') {
                    instructorsHTML = `
                <div class="mb-4">
                    <h4 class="text-sm font-semibold text-gray-700 mb-1">
                        <i class="fas fa-chalkboard-teacher mr-1 text-purple-500"></i>
                        Instructors
                    </h4>
                    <p class="text-xs text-gray-600 line-clamp-2">
                        ${instructors}
                    </p>
                </div>`;
                }

                // Generate URL HTML
                let urlHTML = '';
                if (url) {
                    urlHTML = `
                <a href="${url}" target="_blank" 
                   class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center justify-center">
                    View Course 
                    <i class="fas fa-external-link-alt ml-2 text-xs"></i>
                </a>`;
                }

                // Build the complete course card HTML
                courseCol.innerHTML = `
            <div class="course-card bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 h-full flex flex-col">
                <div class="p-6 flex-grow">
                    <!-- Header with title and provider -->
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-xl font-bold text-gray-800 mb-2 line-clamp-2 hover:text-blue-600 transition-colors">
                            ${title}
                        </h3>
                        <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full whitespace-nowrap ml-2">
                            ${site}
                        </span>
                    </div>
                    
                    <!-- Description -->
                    <p class="text-gray-600 mb-4 line-clamp-3 text-sm">
                        ${description}
                    </p>
                    
                    <!-- Key Details Grid -->
                    ${detailsHTML}
                    
                    <!-- Price and Viewers -->
                    <div class="flex justify-between items-center mb-4 text-sm">
                        ${priceHTML}
                        
                        ${viewers > 0 ? `
                            <span class="text-gray-500">
                                <i class="fas fa-eye mr-1"></i>
                                ${viewers.toLocaleString()} viewers
                            </span>
                        ` : ''}
                    </div>
                    
                    <!-- Skills -->
                    ${skillsHTML}
                    
                    <!-- Instructors -->
                    ${instructorsHTML}
                </div>
                
                <!-- Footer with CTA -->
                <div class="bg-gray-50 px-6 py-4 border-t border-gray-100">
                    ${urlHTML}
                </div>
            </div>
            `;

                coursesGrid.appendChild(courseCol);
            } catch (error) {
                console.error('Error rendering course:', course, error);
                // Create a simple fallback card for debugging
                const errorCol = document.createElement('div');
                errorCol.className = 'course-col';
                errorCol.innerHTML = `
                <div class="course-card bg-red-50 border border-red-200 rounded-xl p-6">
                    <h3 class="text-xl font-bold text-red-800 mb-2">Error displaying course</h3>
                    <p class="text-red-600">Title: ${course.title || 'Unknown'}</p>
                    <p class="text-red-600 text-sm">${error.message}</p>
                </div>
            `;
                coursesGrid.appendChild(errorCol);
            }
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

    // Auto-render courses if injected by server (from /test-local)
    if (window.__LOCAL_COURSES__ && Array.isArray(window.__LOCAL_COURSES__) && window.__LOCAL_COURSES__.length) {
        // optional: show a bot message about loaded results
        if (window.__LOCAL_TEST_MESSAGE__) {
            addMessage(window.__LOCAL_TEST_MESSAGE__, 'bot');
        }
        updateCourseResults(window.__LOCAL_COURSES__);
    }

});