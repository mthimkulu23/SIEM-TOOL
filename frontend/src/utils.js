// frontend/src/utils.js

/**
 * utils.js
 * Contains reusable utility functions for the frontend.
 */

/**
 * Formats a Date object into a readable "YYYY-MM-DD HH:MM:SS" string.
 * @param {Date} date - The Date object to format.
 * @returns {string} The formatted date-time string.
 */
function formatDateTime(date) {
    const pad = (num) => num < 10 ? '0' + num : num;
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

/**
 * Maps log levels (INFO, WARN, ERROR, etc.) to Tailwind CSS text colors.
 * @param {string} level - The log level string.
 * @returns {string} The Tailwind CSS class for the given log level's color.
 */
function getLogLevelColor(level) {
    switch (level.toUpperCase()) {
        case 'INFO': return 'text-green-400';
        case 'WARN': return 'text-yellow-400';
        case 'ERROR': return 'text-orange-400';
        case 'ALERT': return 'text-red-400';
        case 'CRITICAL': return 'text-red-500';
        case 'AUTH': return 'text-purple-400'; // Specific color for authentication logs
        case 'DEBUG': return 'text-gray-400';
        case 'TRACE': return 'text-gray-500';
        default: return 'text-gray-300'; // Default color
    }
}

/**
 * Maps alert severity levels to Tailwind CSS background and text colors for badges.
 * @param {string} severity - The alert severity string (e.g., 'Critical', 'High', 'Medium', 'Low').
 * @returns {string} The Tailwind CSS classes for the severity badge.
 */
function getSeverityBadgeColor(severity) {
    switch (severity.toLowerCase()) {
        case 'critical': return 'bg-red-800 text-red-100';
        case 'high': return 'bg-orange-800 text-orange-100';
        case 'medium': return 'bg-yellow-800 text-yellow-100';
        case 'low': return 'bg-blue-800 text-blue-100';
        default: return 'bg-gray-700 text-gray-200'; // Default for unknown severity
    }
}

/**
 * Maps alert status values to Tailwind CSS background and text colors for badges.
 * @param {string} status - The alert status string (e.g., 'Open', 'Closed', 'In Progress').
 * @returns {string} The Tailwind CSS classes for the status badge.
 */
function getAlertStatusColor(status) {
    switch (status.toLowerCase()) {
        case 'open': return 'bg-yellow-800 text-yellow-100';
        case 'closed': return 'bg-green-800 text-green-100';
        case 'in progress': return 'bg-blue-800 text-blue-100';
        default: return 'bg-gray-700 text-gray-200'; // Default for unknown status
    }
}

/**
 * A simple implementation of Python's defaultdict for JavaScript.
 * Allows providing a default factory function for keys not yet present.
 */
class defaultdict extends Map {
    constructor(defaultFactory) {
        super();
        this.defaultFactory = defaultFactory;
    }

    get(key) {
        if (!this.has(key)) {
            this.set(key, this.defaultFactory());
        }
        return super.get(key);
    }
}

// Export the utility functions globally so they can be accessed by main.js
window.utils = {
    formatDateTime,
    getLogLevelColor,
    getSeverityBadgeColor,
    getAlertStatusColor,
    defaultdict
};
