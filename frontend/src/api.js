// frontend/src/api.js

/**
 * api.js
 * Centralized module for making API calls to the SIEM backend.
 */

// Base URL for your backend API
// IMPORTANT: Change this to your actual backend API URL when deploying!
const API_BASE_URL = 'http://127.0.0.1:5000/api'; // Assuming Flask/FastAPI runs on 5000


// Helper function for making authenticated API requests
async function makeApiRequest(endpoint, method = 'GET', data = null) {
    const url = `${API_BASE_URL}${endpoint}`;
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            // 'Authorization': `Bearer ${yourAuthToken}` // Add authentication token if applicable
        },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: response.statusText }));
            throw new Error(`API Error ${response.status}: ${errorData.message}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        // Rethrow or return a structured error for the caller to handle
        throw error;
    }
}

/**
 * Fetches recent log entries from the backend.
 * @returns {Promise<Array>} A promise that resolves to an array of log entries.
 */
async function getRecentLogs() {
    return makeApiRequest('/logs/recent');
}

/**
 * Fetches alerts that are currently open or in progress.
 * @returns {Promise<Array>} A promise that resolves to an array of alert objects.
 */
async function getOpenAlerts() {
    return makeApiRequest('/alerts/open');
}

/**
 * Fetches dashboard metrics (e.g., critical alerts count, EPS, top sources).
 * @returns {Promise<Object>} A promise that resolves to an object containing dashboard metrics.
 */
async function getDashboardMetrics() {
    return makeApiRequest('/dashboard/metrics');
}

/**
 * Filters log entries based on search criteria.
 * @param {Object} filters - An object containing filter_text, source, and level.
 * @returns {Promise<Array>} A promise that resolves to an array of filtered log entries.
 */
async function filterLogs(filters) {
    return makeApiRequest('/logs/filter', 'POST', filters);
}

/**
 * Updates the status of a specific alert.
 * @param {string} alertId - The ID of the alert to update.
 * @param {string} newStatus - The new status for the alert (e.g., 'Closed', 'In Progress').
 * @returns {Promise<Object>} A promise that resolves to a confirmation object.
 */
async function updateAlertStatus(alertId, newStatus) {
    return makeApiRequest(`/alerts/${alertId}/status`, 'PUT', { status: newStatus });
}

/**
 * Generates a daily security summary report.
 * @returns {Promise<Object>} A promise that resolves to the report data.
 */
async function generateDailySecuritySummary() {
    return makeApiRequest('/reports/daily_summary');
}

/**
 * Generates a compliance audit report for a given standard.
 * @param {string} standard - The compliance standard (e.g., 'ISO 27001', 'GDPR').
 * @returns {Promise<Object>} A promise that resolves to the report data.
 */
async function generateComplianceAuditReport(standard) {
    return makeApiRequest('/reports/compliance_audit', 'POST', { standard: standard });
}


// Export the API functions globally (or using modules if bundling)
// This makes them accessible from main.js as `api.getRecentLogs()`, etc.
window.api = {
    getRecentLogs,
    getOpenAlerts,
    getDashboardMetrics,
    filterLogs,
    updateAlertStatus,
    generateDailySecuritySummary,
    generateComplianceAuditReport
};
