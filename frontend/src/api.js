
const API_BASE_URL = "https://siem-tool.onrender.com"; // <-- *** ENSURE THIS IS MY ACTUAL BACKEND URL ***

// During local development, you would set this to:
// const API_BASE_URL = "http://127.0.0.1:5000"; 
//
// For a production deployment where the frontend and backend are separate services,
// you need the full, public URL of your backend.

export async function fetchApiData(endpoint, options = {}) {
    // Robustly construct the full URL, handling leading/trailing slashes.
    // Removes any trailing slash from API_BASE_URL.
    const baseUrlClean = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
    
    // Ensures endpoint has a leading slash and ADDS THE /api PREFIX
    const endpointClean = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${baseUrlClean}/api${endpointClean}`; // *** KEY CHANGE: Added /api prefix ***

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
