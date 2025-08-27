// public/js/courseCard.js - Course card rendering
export function renderCourseCard(course) {
  // Handle inconsistent data types safely
  const instructors = Array.isArray(course.instructors) && course.instructors.length > 0
    ? course.instructors.join(', ')
    : null;

  const skills = Array.isArray(course.skills) ? course.skills : [];
  const learningOutcomes = Array.isArray(course.learning_outcomes) ? course.learning_outcomes : [];
  const price = course.price || 'Free';
  const viewers = course.viewers || 0;
  const duration = course.duration || null;
  const level = course.level || null;
  const category = course.category || null;
  const language = course.language || null;
  const title = course.title || 'Untitled Course';
  const site = course.site || course.provider || 'Unknown';
  const description = course.description || 'No description available.';
  const url = course.url || null;

  // Truncate description to 25 words max
  const wordCount = 25;
  const words = description.split(/\s+/);
  const truncatedDescription = words.length > wordCount
    ? words.slice(0, wordCount).join(' ') + '...'
    : description;

  // Generate skills (max 3 visible initially)
  let skillsHTML = '';
  if (skills.length > 0) {
    const skillsList = skills.slice(0, 3).map(skill =>
      `<span class="bg-gray-100 text-gray-800 text-xs px-2.5 py-1 rounded-full">${skill}</span>`
    ).join('');

    skillsHTML = `
      <div class="mb-3">
        <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center justify-between">
          <span>
            <i class="fas fa-tools mr-1 text-blue-500"></i>
            Key Skills
          </span>
          ${skills.length > 3 ? `
          <button class="text-primary-600 hover:text-primary-800 text-xs font-medium toggle-skills">
            Show all
          </button>` : ''}
        </h4>
        <div class="flex flex-wrap gap-2">
          ${skillsList}
        </div>
        ${skills.length > 3 ? `
        <div class="all-skills hidden mt-2">
          <div class="flex flex-wrap gap-2">
            ${skills.slice(3).map(skill =>
      `<span class="bg-gray-100 text-gray-800 text-xs px-2.5 py-1 rounded-full">${skill}</span>`
    ).join('')}
          </div>
        </div>` : ''}
      </div>`;
  }

  // Generate learning outcomes (max 2 items initially)
  let learningOutcomesHTML = '';
  if (learningOutcomes.length > 0) {
    const outcomesList = learningOutcomes.slice(0, 2).map(outcome => `
      <li class="truncate">${outcome}</li>
    `).join('');

    learningOutcomesHTML = `
      <div class="mb-3">
        <h4 class="text-sm font-semibold text-gray-700 mb-2 flex items-center justify-between">
          <span>
            <i class="fas fa-graduation-cap mr-1 text-green-500"></i>
            Learning Outcomes
          </span>
          ${learningOutcomes.length > 2 ? `
          <button class="text-primary-600 hover:text-primary-800 text-xs font-medium toggle-outcomes">
            Show all
          </button>` : ''}
        </h4>
        <ul class="text-xs text-gray-600 list-disc list-inside space-y-1">
          ${outcomesList}
        </ul>
        ${learningOutcomes.length > 2 ? `
        <div class="all-outcomes hidden mt-2">
          <ul class="text-xs text-gray-600 list-disc list-inside space-y-1">
            ${learningOutcomes.slice(2).map(outcome => `
              <li class="truncate">${outcome}</li>
            `).join('')}
          </ul>
        </div>` : ''}
      </div>`;
  }

  // Generate details grid (only show available fields)
  let detailsHTML = '';
  const details = [];

  if (duration) details.push(`
    <div class="flex items-center text-sm text-gray-600">
      <i class="far fa-clock mr-2 text-blue-500"></i>
      <span class="truncate">${duration}</span>
    </div>
  `);

  if (level) details.push(`
    <div class="flex items-center text-sm text-gray-600">
      <i class="fas fa-chart-line mr-2 text-green-500"></i>
      <span>${level}</span>
    </div>
  `);

  if (category) details.push(`
    <div class="flex items-center text-sm text-gray-600">
      <i class="fas fa-tag mr-2 text-purple-500"></i>
      <span class="truncate">${category}</span>
    </div>
  `);

  if (language) details.push(`
    <div class="flex items-center text-sm text-gray-600">
      <i class="fas fa-language mr-2 text-red-500"></i>
      <span>${language}</span>
    </div>
  `);

  if (details.length > 0) {
    detailsHTML = `
      <div class="grid grid-cols-2 gap-3 mb-4">
        ${details.join('')}
      </div>`;
  }

  // Price
  let priceHTML = `<span class="text-green-600 font-semibold"><i class="fas fa-tag mr-1"></i>${price}</span>`;

  // Instructors (optional)
  let instructorsHTML = '';
  if (instructors) {
    instructorsHTML = `
      <div class="mb-3">
        <h4 class="text-sm font-semibold text-gray-700 mb-1">
          <i class="fas fa-chalkboard-teacher mr-1 text-purple-500"></i>
          Instructors
        </h4>
        <p class="text-xs text-gray-600 line-clamp-2">${instructors}</p>
      </div>`;
  }

  // CTA link
  let urlHTML = '';
  if (url) {
    urlHTML = `
      <a href="${url}" target="_blank" 
         class="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center justify-center">
        View Course 
        <i class="fas fa-external-link-alt ml-2 text-xs"></i>
      </a>`;
  }

  // Final card build
  return `
    <div class="course-card bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300 h-full flex flex-col">
      <div class="p-6 flex-grow">
        <!-- Title + provider -->
        <div class="flex justify-between items-start mb-4">
          <h3 class="text-lg font-bold text-gray-800 mb-2 line-clamp-2">
            ${title}
          </h3>
          <span class="bg-primary-100 text-primary-800 text-xs font-semibold px-3 py-1 rounded-full whitespace-nowrap ml-2 flex-shrink-0">
            ${site}
          </span>
        </div>

        <!-- Description -->
        <p class="text-gray-600 mb-4 text-sm">
          ${truncatedDescription}
        </p>
        ${words.length > wordCount ? `
        <button class="text-primary-600 hover:text-primary-800 text-xs font-medium mb-4 text-left toggle-description">
          Read more
        </button>
        <div class="full-description hidden text-sm text-gray-600 mb-4">${description}</div>
        ` : ''}

        <!-- Key Details -->
        ${detailsHTML}

        <!-- Price + Viewers -->
        <div class="flex justify-between items-center mb-4 text-sm">
          ${priceHTML}
          ${viewers > 0 ? `
            <span class="text-gray-500">
              <i class="fas fa-eye mr-1"></i>${viewers.toLocaleString()} viewers
            </span>` : ''}
        </div>

        <!-- Skills -->
        ${skillsHTML}

        <!-- Learning Outcomes -->
        ${learningOutcomesHTML}

        <!-- Instructors -->
        ${instructorsHTML}
      </div>

      <!-- Footer -->
      <div class="bg-gray-50 px-6 py-4 border-t border-gray-100">
        ${urlHTML}
      </div>
    </div>
  `;
}