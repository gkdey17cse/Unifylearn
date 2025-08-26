// public/js/courseCard.js
let __courseCard_uid = 0;

/* -------------------------
   Utility helpers
   ------------------------- */
function escapeHtml(str) {
  if (str === undefined || str === null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function firstNWords(text, n = 20) {
  if (!text) return { short: '', full: '', truncated: false };
  const words = String(text).trim().split(/\s+/);
  if (words.length <= n) return { short: text.trim(), full: text.trim(), truncated: false };
  return { short: words.slice(0, n).join(' '), full: text.trim(), truncated: true };
}

/* -------------------------
   Unified color theme - Light Purple/Violet
   ------------------------- */
const UNIFIED_THEME = {
  borderClass: "border-t-4 border-purple-400",
  badgeClass: "bg-purple-600 text-white",
  iconClass: "text-purple-600",
  btnClass: "bg-purple-600 hover:bg-purple-700",
  textClass: "text-purple-700"
};

/* Helper for arrays/strings */
function renderStringOrArray(value) {
  if (!value) return '';
  if (Array.isArray(value)) {
    if (value.length === 0) return '';
    return escapeHtml(value.join(', '));
  }
  return escapeHtml(String(value));
}

/* Register global toggle */
if (!window.__courseCardToggleRegistered) {
  window.__courseCardToggleRegistered = true;
  window.toggleCourseCardSection = function (uid, section) {
    const shortEl = document.getElementById(`${uid}-${section}-short`);
    const fullEl = document.getElementById(`${uid}-${section}-full`);
    if (shortEl) shortEl.classList.toggle('hidden');
    if (fullEl) fullEl.classList.toggle('hidden');
    if (fullEl && !fullEl.classList.contains('hidden')) {
      fullEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };
}

/* -------------------------
   Main renderer
   ------------------------- */
export function renderCourseCard(course = {}) {
  __courseCard_uid += 1;
  const uid = `course-${Date.now().toString(36)}-${__courseCard_uid}`;

  // Use unified theme for all courses
  const styles = UNIFIED_THEME;

  // Fields (safe)
  const title = course.title ? escapeHtml(course.title) : 'Untitled Course';
  const providerDisplay = escapeHtml(course.provider || course.site || 'Online Course');

  const url = course.url ? escapeHtml(course.url) : '';
  const viewers = Number(course.viewers) > 0 ? Number(course.viewers).toLocaleString() : null;
  const price = course.price ? escapeHtml(course.price) : 'Free';
  const duration = course.duration ? escapeHtml(course.duration) : '';
  const level = course.level ? escapeHtml(course.level) : '';
  const category = course.category ? escapeHtml(course.category) : '';
  const language = course.language ? escapeHtml(course.language) : '';

  const instructors = renderStringOrArray(course.instructors);
  const prerequisites = renderStringOrArray(course.prerequisites);

  // Skills up to 4
  const skillsArr = Array.isArray(course.skills) ? course.skills.filter(Boolean) : [];
  const skillsHtml = skillsArr.length
    ? skillsArr.slice(0, 4).map(s => `<span class="bg-gray-100 text-gray-800 text-xs px-2.5 py-1 rounded-full break-words">${escapeHtml(s)}</span>`).join(' ')
    + (skillsArr.length > 4 ? ` <span class="text-xs text-gray-500">+${skillsArr.length - 4} more</span>` : '')
    : '';

  // description & learning outcomes truncated to 20 words
  const descriptionRaw = (course.description || '').toString().trim();
  const learningRaw = (course.learning_outcomes || '').toString().trim();
  const desc = firstNWords(descriptionRaw, 20);
  const learn = firstNWords(learningRaw, 20);

  // Build HTML
  const html = `
  <div class="course-card bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 h-full w-full flex flex-col overflow-hidden ${styles.borderClass}">
    <div class="p-6 flex-grow flex flex-col min-h-0">
      <!-- header -->
      <div class="flex justify-between items-start mb-3 gap-3 min-w-0">
        <div class="min-w-0">
          <h3 class="text-lg md:text-xl font-semibold text-gray-800 mb-1 truncate">${title}</h3>
          ${category || level ? `<div class="text-xs text-gray-500 truncate">${category ? category : ''}${category && level ? ' · ' : ''}${level ? level : ''}</div>` : ''}
        </div>

        <div class="flex-shrink-0 text-right ml-3">
          <div class="${styles.badgeClass} inline-flex items-center text-xs font-semibold px-3 py-1 rounded-full whitespace-nowrap">
            ${providerDisplay}
          </div>
        </div>
      </div>

      <!-- description -->
      ${desc.truncated ? `
        <p id="${uid}-desc-short" class="text-gray-600 text-sm mb-2 break-words whitespace-normal">${escapeHtml(desc.short)}... <button onclick="toggleCourseCardSection('${uid}', 'desc')" class="text-xs font-medium ${styles.textClass} ml-1">See more</button></p>
        <p id="${uid}-desc-full" class="text-gray-600 text-sm mb-2 break-words whitespace-normal hidden">${escapeHtml(desc.full)} <button onclick="toggleCourseCardSection('${uid}', 'desc')" class="text-xs font-medium ${styles.textClass} ml-1">See less</button></p>
      ` : (descriptionRaw ? `<p class="text-gray-600 text-sm mb-2 break-words whitespace-normal">${escapeHtml(descriptionRaw)}</p>` : '')}

      <!-- learning outcomes -->
      ${learn.truncated ? `
        <p id="${uid}-learn-short" class="text-gray-700 text-sm mb-2 break-words whitespace-normal"><strong>Learning outcomes:</strong> ${escapeHtml(learn.short)}... <button onclick="toggleCourseCardSection('${uid}', 'learn')" class="text-xs font-medium ${styles.textClass} ml-1">See more</button></p>
        <p id="${uid}-learn-full" class="text-gray-700 text-sm mb-2 break-words whitespace-normal hidden"><strong>Learning outcomes:</strong> ${escapeHtml(learn.full)} <button onclick="toggleCourseCardSection('${uid}', 'learn')" class="text-xs font-medium ${styles.textClass} ml-1">See less</button></p>
      ` : (learningRaw ? `<p class="text-gray-700 text-sm mb-2 break-words whitespace-normal"><strong>Learning outcomes:</strong> ${escapeHtml(learningRaw)}</p>` : '')}

      <!-- details -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-600 mb-3 min-w-0">
        ${duration ? `<div class="flex items-center min-w-0"><i class="far fa-clock mr-2 ${styles.iconClass}"></i><span class="truncate">${duration}</span></div>` : ''}
        ${language ? `<div class="flex items-center min-w-0"><i class="fas fa-language mr-2 ${styles.iconClass}"></i><span class="truncate">${language}</span></div>` : ''}
        ${prerequisites ? `<div class="sm:col-span-2 text-gray-700 break-words whitespace-normal"><strong>Prerequisites:</strong> ${prerequisites}</div>` : ''}
        ${instructors ? `<div class="sm:col-span-2 text-gray-700 break-words whitespace-normal"><strong>Instructors:</strong> ${instructors}</div>` : ''}
      </div>

      <!-- skills -->
      ${skillsHtml ? `<div class="mb-3"><h4 class="text-sm font-semibold text-gray-700 mb-2">Skills</h4><div class="flex flex-wrap gap-2">${skillsHtml}</div></div>` : ''}

      <!-- viewers/price -->
      <div class="flex justify-between items-center mt-auto text-sm">
        <div class="text-green-600 font-semibold"><i class="fas fa-tag mr-1"></i>${price}</div>
        ${viewers ? `<div class="text-gray-500"><i class="fas fa-eye mr-1"></i>${viewers} viewers</div>` : ''}
      </div>
    </div>

    <!-- footer -->
    <div class="bg-gray-50 px-6 py-4 border-t border-gray-100 flex items-center justify-between gap-3">
      <div class="flex-1 min-w-0 text-xs text-gray-500 truncate">${escapeHtml(course.original_provider_id || '')}</div>
      <div class="flex-shrink-0">
        ${url ? `<a href="${url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center text-white px-4 py-2 rounded-lg text-sm font-semibold ${styles.btnClass} transition-colors">View Course <i class="fas fa-external-link-alt ml-2 text-xs"></i></a>` : `<button disabled class="inline-flex items-center text-white px-4 py-2 rounded-lg text-sm font-semibold ${styles.btnClass} opacity-70 cursor-not-allowed">No link</button>`}
      </div>
    </div>
  </div>
  `;

  return html;
}