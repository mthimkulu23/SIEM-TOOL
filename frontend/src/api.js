// frontend/src/api.js

// IMPORTANT: You MUST replace this placeholder with the actual PUBLIC URL of your deployed Render backend API.
// Examples:
// If your Render backend service is named 'siem-backend-api', its URL might be:
// "https://siem-backend-api.onrender.com"
//
// You can find this URL in your Render dashboard, under the settings for your backend web service.
// It will usually look something like 'https://your-service-name.onrender.com'.
const API_BASE_URL = "https://siem-tool.onrender.com/"; // <-- *** UPDATE THIS LINE ***

// During local development, you would set this to:
// const API_BASE_URL = "http://127.0.0.1:5000"; 
//
// For a production deployment where the frontend and backend are separate services,
// you need the full, public URL of your backend.

export async function fetchApiData(endpoint, options = {}) {
    // Construct the full URL for the API request
    const url = `${API_BASE_URL}${endpoint}`;

    try {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const fetchOptions = { ...defaultOptions, ...options };

        if (fetchOptions.body && typeof fetchOptions.body !== 'string') {
            fetchOptions.body = JSON.stringify(fetchOptions.body);
        }

        console.log(`api.js: Fetching data from: ${url} with options:`, fetchOptions); // Debug log

        const response = await fetch(url, fetchOptions);

        if (!response.ok) {
            // Attempt to read error text from response body if available
            const errorBody = await response.text();
            console.error(`api.js: API Error ${response.status} from ${url}:`, errorBody);
            throw new Error(`API Error ${response.status}: ${errorBody}`);
        }

        const data = await response.json();
        console.log(`api.js: Received data from ${url}:`, data); // Debug log
        return data;
    } catch (error) {
        console.error(`api.js: Network or parsing error for ${url}:`, error);
        // Re-throw the error so calling functions can handle it
        throw error;
    }
}
