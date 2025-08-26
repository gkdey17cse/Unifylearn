// public/js/results.js
import { renderCourseCard } from './courseCard.js';

export function updateCourseResults(courses = []) {
  const resultsContainer = document.getElementById('results-container');
  if (!resultsContainer) return;
  // ensure grid items stretch vertically
  resultsContainer.classList.add('items-stretch', 'w-full');

  resultsContainer.innerHTML = '';

  // responsive summary that spans grid columns
  const summary = document.createElement('div');
  // make it responsive: 1 col on mobile, 2 on sm, 3 on lg
  summary.className = 'col-span-1 sm:col-span-2 lg:col-span-3 text-center mb-8';
  summary.innerHTML = `
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
      <h2 class="text-2xl font-bold text-blue-800 mb-2">Search Results</h2>
      <p class="text-blue-600">Found ${courses.length} courses</p>
    </div>`;
  resultsContainer.appendChild(summary);

  // append each course directly as a grid item wrapper
  courses.forEach(course => {
    const wrap = document.createElement('div');

    // IMPORTANT: min-h-0 and min-w-0 allow flex children to shrink inside grid cells.
    // items-stretch makes the wrapper take full height of grid row so card equals height.
    wrap.className = 'flex items-stretch min-h-0 min-w-0';

    // insert card html (renderCourseCard returns HTML string)
    wrap.innerHTML = renderCourseCard(course);

    // append to grid (resultsContainer is the grid)
    resultsContainer.appendChild(wrap);
  });

  // optional: smooth scroll to results
  resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
