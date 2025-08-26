import { renderCourseCard } from './courseCard.js';

const container = document.getElementById('results-container');

function clearResults() {
    container.innerHTML = '';
}

// Unified function to render courses
export function displayCourses(courses = [], summaryMessage = '') {
    clearResults();

    if (!courses || !courses.length) {
        container.innerHTML = `
        <div class="col-span-3 text-center py-12">
            <i class="fas fa-search text-gray-400 text-5xl mb-4"></i>
            <p class="text-gray-600">No courses found. Try a different search query.</p>
        </div>`;
        return;
    }

    if (summaryMessage) {
        const summary = document.createElement('div');
        summary.className = 'col-span-3 mb-6';
        summary.innerHTML = `
            <div class="bg-purple-50 border border-purple-200 rounded-lg p-6 text-center">
                <h2 class="text-2xl font-bold text-purple-800 mb-2">Search Results</h2>
                <p class="text-purple-600">${summaryMessage}</p>
            </div>`;
        container.appendChild(summary);
    }

    courses.forEach(course => {
        const cardHtml = renderCourseCard(course);
        container.insertAdjacentHTML('beforeend', cardHtml);
    });
}

// Initialize server-injected courses (if any)
if (window.__LOCAL_COURSES__ && Array.isArray(window.__LOCAL_COURSES__)) {
    const msg = window.__LOCAL_TEST_MESSAGE__ || `Found ${window.__LOCAL_COURSES__.length} courses`;
    displayCourses(window.__LOCAL_COURSES__, msg);
}
