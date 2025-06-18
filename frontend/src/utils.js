// frontend/src/utils.js
// This file contains utility functions, including chart rendering with Chart.js

// Chart.js is now loaded via a direct <script> tag in index.html,
// so dynamic loading here is commented out, but kept for reference if needed.
/*
if (typeof Chart === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = () => console.log('Chart.js loaded dynamically.');
    script.onerror = () => console.error('Failed to load Chart.js');
    document.head.appendChild(script);
}
*/

/**
 * Renders a new chart using Chart.js.
 * @param {HTMLCanvasElement} canvasElement The canvas DOM element to render the chart on.
 * @param {Object} data The data object for the chart (labels, datasets).
 * @param {string} type The type of chart (e.g., 'line', 'bar', 'pie').
 * @param {Object} options Optional configuration options for the chart.
 * @returns {Chart} The Chart.js instance.
 */
export function renderChart(canvasElement, data, type, options = {}) {
    if (typeof Chart === 'undefined') {
        console.error("Chart.js is not loaded. Cannot render chart.");
        return null;
    }
    // Destroy existing chart instance if it exists on the canvas
    if (canvasElement.chartInstance) {
        canvasElement.chartInstance.destroy();
    }

    const ctx = canvasElement.getContext('2d');
    const newChart = new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false, // Important for fitting into div containers
            plugins: {
                legend: {
                    labels: {
                        color: '#a0aec0' // Tailwind gray-400 for legend text
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: '#4a5568' // Tailwind gray-700 for grid lines
                    },
                    ticks: {
                        color: '#a0aec0' // Tailwind gray-400 for ticks
                    }
                },
                y: {
                    grid: {
                        color: '#4a5568'
                    },
                    ticks: {
                        color: '#a0aec0',
                        beginAtZero: true // Start y-axis from zero
                    }
                }
            },
            ...options // Merge custom options
        }
    });
    canvasElement.chartInstance = newChart; // Store chart instance on the canvas element
    return newChart;
}

/**
 * Updates an existing Chart.js chart with new data.
 * @param {Chart} chartInstance The existing Chart.js instance.
 * @param {Object} newData The new data object for the chart.
 */
export function updateChart(chartInstance, newData) {
    if (chartInstance) {
        chartInstance.data = newData;
        chartInstance.update();
    } else {
        console.warn("No chart instance found to update.");
    }
}
