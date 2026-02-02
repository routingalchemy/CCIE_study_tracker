// Study Tracker JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Update current date and time
    updateDateTime();
    setInterval(updateDateTime, 1000);

    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            toggleTheme();
        });
    }

    // Set initial theme: prefer server-rendered value, fallback to localStorage
    const serverTheme = document.documentElement.getAttribute('data-theme');
    const savedTheme = serverTheme || localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    // Ensure localStorage matches the active theme
    try { localStorage.setItem('theme', savedTheme); } catch (e) {}

    // Sorting functionality
    const sortableHeaders = document.querySelectorAll('th.sortable');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const sortBy = this.dataset.sort;
            const currentOrder = this.classList.contains('sorted-asc') ? 'asc' : 'desc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';

            // Update URL with sort parameters
            const url = new URL(window.location);
            url.searchParams.set('sort', sortBy);
            url.searchParams.set('order', newOrder);
            window.location.href = url.toString();
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    setTheme(newTheme);

    // Save to localStorage
    localStorage.setItem('theme', newTheme);

    // Update server-side session (optional)
    fetch('/toggle_theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    }).catch(error => console.log('Theme update failed:', error));
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.textContent = theme === 'light' ? '🌙' : '☀️';
    }
}

function updateDateTime() {
    const now = new Date();
    
    // Format: YYYY.MM.DD
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const dateStr = `${year}.${month}.${day}`;
    
    // Format: HH:mm:ss (24-hour format)
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timeStr = `${hours}:${minutes}:${seconds}`;
    
    const dateElement = document.getElementById('current-date');
    const timeElement = document.getElementById('current-time');
    
    if (dateElement) dateElement.textContent = dateStr;
    if (timeElement) timeElement.textContent = timeStr;
}

// Progress bar animation
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-fill');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
}

// Run progress bar animation on page load
animateProgressBars();

// Bulk delete functionality for delete page
document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    const deleteSelectedBtn = document.getElementById('delete-selected');

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateDeleteButton();
        });
    }

    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateDeleteButton);
    });

    function updateDeleteButton() {
        const checkedBoxes = document.querySelectorAll('.item-checkbox:checked');
        if (deleteSelectedBtn) {
            deleteSelectedBtn.disabled = checkedBoxes.length === 0;
        }
    }

    function confirmDeleteAll() {
        const searchQuery = new URLSearchParams(window.location.search).get('search');
        const message = searchQuery
            ? `Are you sure you want to delete ALL FILTERED items? This action cannot be undone.`
            : `Are you sure you want to delete ALL items? This action cannot be undone.`;
        return confirm(message);
    }

    // Make confirmDeleteAll available globally
    window.confirmDeleteAll = confirmDeleteAll;

    // Initialize button state
    updateDeleteButton();
});