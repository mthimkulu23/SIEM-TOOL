// frontend/src/api.js
/**
 * api.js
 * Centralized module for making API calls to the SIEM backend.
 */

// Base URL for your backend API
// IMPORTANT: This has been updated for LOCAL DEVELOPMENT.
// When deploying your frontend to Render, you MUST change this back to your Render backend URL.
const API_BASE_URL = 'http://127.0.0.1:5000/api';


/**
 * Helper function for making API requests.
 * Exports this as the primary fetch utility.
 * @param {string} endpoint - The API endpoint relative to API_BASE_URL.
 * @param {Object} [options] - Fetch API options (method, headers, body).
 * @returns {Promise<Object>} A promise that resolves to the JSON response data.
 */
export async function fetchApiData(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Default headers, can be overridden by options.headers
    const defaultHeaders = {
        'Content-Type': 'application/json',
        // 'Authorization': `Bearer ${yourAuthToken}` // Add authentication token if applicable
    };

    const finalOptions = {
        method: options.method || 'GET',
        headers: { ...defaultHeaders, ...options.headers },
        body: options.body,
    };

    // Remove body for GET/HEAD requests
    if (finalOptions.method === 'GET' || finalOptions.method === 'HEAD') {
        delete finalOptions.body;
    }

    try {
        const response = await fetch(url, finalOptions);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: response.statusText }));
            // Log the full error response for debugging
            console.error(`API Error ${response.status} for ${url}:`, errorData);
            throw new Error(`API Error ${response.status}: ${errorData.message}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API request to ${url} failed:`, error);
        throw error; // Re-throw to be handled by the calling function
    }
}
