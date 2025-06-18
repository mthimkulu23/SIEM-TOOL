// frontend/src/main.js

// Import any necessary functions from utils.js or api.js if you have them.
// For example, if fetchAndDisplayLogs is in api.js or main.js, you might need to export/import it.
// Assuming fetchAndDisplayLogs() is accessible globally or defined in this file.

document.addEventListener('DOMContentLoaded', () => {
    // --- Existing UI Navigation Logic (from your project) ---
    const navLinks = document.querySelectorAll('nav a');
    const sections = document.querySelectorAll('main section');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetSectionId = link.dataset.section + '-section';

            navLinks.forEach(nav => nav.classList.remove('active-link'));
            link.classList.add('active-link');

            sections.forEach(section => {
                if (section.id === targetSectionId) {
                    section.classList.remove('hidden');
                    section.classList.add('active-section');
                } else {
                    section.classList.add('hidden');
                    section.classList.remove('active-section');
                }
            });

            // If navigating to logs, also attempt to load them
            if (targetSectionId === 'logs-section') {
                // You might already have a function for this
                // For example, calling fetchAndDisplayFilteredLogs() from api.js
                // or wherever your log fetching logic resides.
                // If not, you'll need to ensure the logs are fetched when the section is shown.
                // Assuming `fetchAndDisplayFilteredLogs` is available from `api.js` or `utils.js`
                if (typeof fetchAndDisplayFilteredLogs === 'function') {
                    fetchAndDisplayFilteredLogs();
                }
            } else if (targetSectionId === 'dashboard-section') {
                 // Assuming `fetchDashboardMetrics` is available
                if (typeof fetchDashboardMetrics === 'function') {
                    fetchDashboardMetrics();
                }
            } else if (targetSectionId === 'alerts-section') {
                // Assuming `fetchAndDisplayAlerts` is available
                if (typeof fetchAndDisplayAlerts === 'function') {
                    fetchAndDisplayAlerts();
                }
            }
        });
    });

    // Set initial active link and section based on default
    const initialActiveLink = document.querySelector('nav a[data-section="dashboard"]');
    if (initialActiveLink) {
        initialActiveLink.click();
    }


    // --- Log Upload Functionality (NEW) ---
    const logInput = document.getElementById('logInput');
    const sendLogButton = document.getElementById('sendLogButton');
    const uploadStatus = document.getElementById('uploadStatus');

    if (sendLogButton) { // Ensure the button exists before adding listener
        sendLogButton.addEventListener('click', async () => {
            const rawLog = logInput.value.trim();
            if (!rawLog) {
                uploadStatus.textContent = "Please enter a log to upload.";
                uploadStatus.style.color = 'red';
                return;
            }

            try {
                uploadStatus.textContent = "Sending log...";
                uploadStatus.style.color = 'orange';

                const response = await fetch('/api/logs/ingest', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ raw_log: rawLog }),
                });

                const result = await response.json();

                if (response.ok) {
                    uploadStatus.textContent = `Log uploaded successfully! Log ID: ${result.log_id}`;
                    uploadStatus.style.color = 'green';
                    logInput.value = ''; // Clear textarea

                    // Crucial: Refresh your logs explorer display and recent events
                    // Assuming you have functions like these in api.js or main.js
                    if (typeof fetchAndDisplayFilteredLogs === 'function') {
                        fetchAndDisplayFilteredLogs(); // Refresh the main Log Explorer
                    }
                    if (typeof fetchRecentEvents === 'function') {
                        fetchRecentEvents(); // Refresh Recent Security Events on Dashboard
                    }
                    if (typeof fetchDashboardMetrics === 'function') {
                        fetchDashboardMetrics(); // Update dashboard metrics if logs affect them
                    }


                } else {
                    uploadStatus.textContent = `Error uploading log: ${result.error || response.statusText}`;
                    uploadStatus.style.color = 'red';
                }
            } catch (error) {
                uploadStatus.textContent = `Network error: ${error.message}`;
                uploadStatus.style.color = 'red';
                console.error('Error:', error);
            }
        });
    }

    // --- Existing Log Filtering Logic (from your project) ---
    const logFilterInput = document.getElementById('log-filter-input');
    const logSourceSelect = document.getElementById('log-source-select');
    const logLevelSelect = document.getElementById('log-level-select');
    const searchLogsBtn = document.getElementById('search-logs-btn');

    if (searchLogsBtn) { // Check if the button exists
        searchLogsBtn.addEventListener('click', () => {
            if (typeof fetchAndDisplayFilteredLogs === 'function') {
                fetchAndDisplayFilteredLogs();
            }
        });

        // Add 'change' listeners for the select dropdowns
        logSourceSelect.addEventListener('change', () => {
            if (typeof fetchAndDisplayFilteredLogs === 'function') {
                fetchAndDisplayFilteredLogs();
            }
        });
        logLevelSelect.addEventListener('change', () => {
            if (typeof fetchAndDisplayFilteredLogs === 'function') {
                fetchAndDisplayFilteredLogs();
            }
        });
    }

    // --- Assuming initial data fetch functions are called here or via navigation clicks ---
    // Example: Call these if they aren't triggered by the initial 'dashboard' click
    // if (typeof fetchDashboardMetrics === 'function') {
    //     fetchDashboardMetrics();
    // }
    // if (typeof fetchRecentEvents === 'function') {
    //     fetchRecentEvents();
    // }
    // if (typeof fetchAndDisplayFilteredLogs === 'function') {
    //     fetchAndDisplayFilteredLogs();
    // }
    // if (typeof fetchAndDisplayAlerts === 'function') {
    //     fetchAndDisplayAlerts();
    // }

    // --- Dashboard Specifics (ensure these are present or imported from api.js) ---
    // Example placeholders, if your dashboard update logic is in main.js
    // You likely have these functions already, ensure they are correctly defined
    // or imported from api.js or utils.js.
    // function fetchDashboardMetrics() { /* ... implementation ... */ }
    // function fetchRecentEvents() { /* ... implementation ... */ }
    // function renderAlertsTrendChart(data) { /* ... implementation ... */ }
    // function updateEventVolumeByType(data) { /* ... implementation ... */ }

    // --- Alerts Specifics (ensure these are present or imported from api.js) ---
    // function fetchAndDisplayAlerts() { /* ... implementation ... */ }
    // function updateAlertStatus(alertId, newStatus) { /* ... implementation ... */ }

    // --- Reports Specifics (ensure these are present or imported from api.js) ---
    const generateDailyReportBtn = document.getElementById('generate-daily-report-btn');
    const generateComplianceReportBtn = document.getElementById('generate-compliance-report-btn');
    const complianceStandardSelect = document.getElementById('compliance-standard-select');
    const reportOutput = document.getElementById('report-output');

    if (generateDailyReportBtn) {
        generateDailyReportBtn.addEventListener('click', async () => {
            // Your existing logic for daily report
            try {
                const response = await fetch('/api/reports/daily_summary');
                const data = await response.json();
                reportOutput.classList.remove('hidden');
                reportOutput.querySelector('pre').textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                console.error('Error fetching daily report:', error);
                reportOutput.classList.remove('hidden');
                reportOutput.querySelector('pre').textContent = 'Error fetching report.';
            }
        });
    }

    if (generateComplianceReportBtn) {
        generateComplianceReportBtn.addEventListener('click', async () => {
            // Your existing logic for compliance report
            const standard = complianceStandardSelect.value;
            try {
                const response = await fetch('/api/reports/compliance_audit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ standard: standard })
                });
                const data = await response.json();
                reportOutput.classList.remove('hidden');
                reportOutput.querySelector('pre').textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                console.error('Error fetching compliance report:', error);
                reportOutput.classList.remove('hidden');
                reportOutput.querySelector('pre').textContent = 'Error fetching report.';
            }
        });
    }
});

// IMPORTANT: Ensure functions like fetchAndDisplayFilteredLogs, fetchRecentEvents,
// fetchDashboardMetrics, and fetchAndDisplayAlerts are defined and accessible
// within the scope where they are called. If they are in `src/api.js`, make sure
// they are exported and properly imported/used in `main.js`, or are global.
// For this example, assuming they are either globally accessible or defined in main.js.

// Example placeholder for fetchAndDisplayFilteredLogs if it's not defined elsewhere:
async function fetchAndDisplayFilteredLogs() {
    const filterText = document.getElementById('log-filter-input').value;
    const source = document.getElementById('log-source-select').value;
    const level = document.getElementById('log-level-select').value;
    const logExplorerViewer = document.getElementById('log-explorer-viewer');

    logExplorerViewer.innerHTML = '<p class="text-gray-500">Loading logs...</p>'; // Loading indicator

    try {
        const response = await fetch('/api/logs/filter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filter_text: filterText,
                source: source,
                level: level
            })
        });
        const logs = await response.json();

        if (logs.length === 0) {
            logExplorerViewer.innerHTML = '<p class="text-gray-500">No logs found matching your criteria.</p>';
        } else {
            logExplorerViewer.innerHTML = ''; // Clear previous logs
            logs.forEach(log => {
                const logEntryDiv = document.createElement('div');
                // Basic styling, you can enhance this
                logEntryDiv.className = 'log-entry p-2 border-b border-gray-800 last:border-b-0 hover:bg-gray-800';
                logEntryDiv.innerHTML = `
                    <span class="text-blue-400">[${new Date(log.timestamp).toLocaleString()}]</span>
                    <span class="text-purple-400">[${log.level}]</span>
                    <span class="text-green-400">${log.source}:</span>
                    <span class="text-gray-300">${log.message}</span>
                    ${log.host ? `<span class="text-orange-400"> (Host: ${log.host})</span>` : ''}
                    ${log.source_ip_host ? `<span class="text-yellow-400"> (Source IP: ${log.source_ip_host})</span>` : ''}
                `;
                logExplorerViewer.appendChild(logEntryDiv);
            });
        }
    } catch (error) {
        console.error('Error fetching filtered logs:', error);
        logExplorerViewer.innerHTML = '<p class="text-red-500">Failed to load logs. Please try again.</p>';
    }
}


// Example placeholder for fetchRecentEvents if it's not defined elsewhere:
async function fetchRecentEvents() {
    const recentEventsLogViewer = document.getElementById('recent-events-log-viewer');
    try {
        const response = await fetch('/api/logs/recent');
        const logs = await response.json();
        recentEventsLogViewer.innerHTML = ''; // Clear existing
        if (logs.length === 0) {
            recentEventsLogViewer.innerHTML = '<p class="text-gray-500">No recent events.</p>';
        } else {
            logs.forEach(log => {
                const logElement = document.createElement('div');
                // Format as [TIMESTAMP] [LEVEL] MESSAGE
                logElement.textContent = `[${new Date(log.timestamp).toLocaleString()}] [${log.level}] ${log.message}`;
                recentEventsLogViewer.appendChild(logElement);
            });
        }
    } catch (error) {
        console.error('Error fetching recent events:', error);
        recentEventsLogViewer.innerHTML = '<p class="text-red-500">Failed to load recent events.</p>';
    }
}

// Example placeholder for fetchDashboardMetrics if it's not defined elsewhere:
async function fetchDashboardMetrics() {
    try {
        const response = await fetch('/api/dashboard/metrics');
        const data = await response.json();

        document.getElementById('critical-alerts-count').textContent = data.critical_alerts_count;
        document.getElementById('eps-count').textContent = data.eps_count;
        document.getElementById('unassigned-alerts-count').textContent = data.unassigned_alerts_count;

        const topSourcesList = document.getElementById('top-sources-list');
        topSourcesList.innerHTML = '';
        if (data.top_sources && data.top_sources.length > 0) {
            data.top_sources.forEach(source => {
                const li = document.createElement('li');
                li.textContent = `${source.name} (${source.percentage}%)`;
                topSourcesList.appendChild(li);
            });
        } else {
            topSourcesList.innerHTML = '<li>No top sources data.</li>';
        }

        // Update event volume by type
        const eventVolumeData = data.event_volume_by_type || { INFO: 0, WARN: 0, ALERT_CRITICAL: 0, OTHER: 0 };
        const totalVolume = eventVolumeData.INFO + eventVolumeData.WARN + eventVolumeData.ALERT_CRITICAL + eventVolumeData.OTHER;

        const updateBar = (idPrefix, percentage) => {
            const bar = document.getElementById(`${idPrefix}-bar`);
            const percentSpan = document.getElementById(`${idPrefix}-percent`);
            if (bar && percentSpan) {
                bar.style.width = `${percentage}%`;
                percentSpan.textContent = `${idPrefix.toUpperCase().replace('_', '/')}: ${percentage}%`;
            }
        };

        if (totalVolume > 0) {
            updateBar('info', Math.round((eventVolumeData.INFO / totalVolume) * 100));
            updateBar('warn', Math.round((eventVolumeData.WARN / totalVolume) * 100));
            updateBar('alert-critical', Math.round((eventVolumeData.ALERT_CRITICAL / totalVolume) * 100));
            updateBar('other', Math.round((eventVolumeData.OTHER / totalVolume) * 100));
        } else {
            // Reset if no data
            updateBar('info', 0);
            updateBar('warn', 0);
            updateBar('alert-critical', 0);
            updateBar('other', 0);
        }

        // Render Alerts Trend Chart (assuming you have a function for this)
        // You might need to add specific charting library code for this.
        // For simplicity, let's just make sure data is passed if the function exists.
        if (typeof renderAlertsTrendChart === 'function' && data.alert_trend_data) {
             renderAlertsTrendChart(data.alert_trend_data);
        }

    } catch (error) {
        console.error('Error fetching dashboard metrics:', error);
    }
}

// Example placeholder for fetchAndDisplayAlerts if it's not defined elsewhere:
async function fetchAndDisplayAlerts() {
    const alertsTableBody = document.getElementById('alerts-table-body');
    try {
        const response = await fetch('/api/alerts/open');
        const alerts = await response.json();
        alertsTableBody.innerHTML = ''; // Clear existing alerts

        if (alerts.length === 0) {
            alertsTableBody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-gray-500">No open alerts.</td></tr>';
        } else {
            alerts.forEach(alert => {
                const tr = document.createElement('tr');
                tr.className = 'bg-gray-800 hover:bg-gray-700 transition-colors duration-200';
                tr.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium ${getSeverityColorClass(alert.severity)}">${alert.severity}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${new Date(alert.timestamp).toLocaleString()}</td>
                    <td class="px-6 py-4 text-sm text-gray-300 max-w-xs truncate" title="${alert.description}">${alert.description}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${alert.source_ip_host || 'N/A'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${alert.status}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <select class="status-select bg-gray-600 border border-gray-500 rounded-md py-1 px-2 text-white" data-alert-id="${alert._id}">
                            <option value="Open" ${alert.status === 'Open' ? 'selected' : ''}>Open</option>
                            <option value="Investigating" ${alert.status === 'Investigating' ? 'selected' : ''}>Investigating</option>
                            <option value="Closed" ${alert.status === 'Closed' ? 'selected' : ''}>Closed</option>
                        </select>
                    </td>
                `;
                alertsTableBody.appendChild(tr);
            });

            // Add event listeners for status changes
            alertsTableBody.querySelectorAll('.status-select').forEach(select => {
                select.addEventListener('change', async (event) => {
                    const alertId = event.target.dataset.alertId;
                    const newStatus = event.target.value;
                    await updateAlertStatus(alertId, newStatus);
                    fetchAndDisplayAlerts(); // Refresh alerts after update
                    fetchDashboardMetrics(); // Also refresh dashboard for alert counts
                });
            });
        }
    } catch (error) {
        console.error('Error fetching alerts:', error);
        alertsTableBody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-red-500">Failed to load alerts.</td></tr>';
    }
}

async function updateAlertStatus(alertId, newStatus) {
    try {
        const response = await fetch(`/api/alerts/${alertId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const result = await response.json();
        if (!response.ok) {
            console.error('Failed to update alert status:', result.message);
            // Optionally, provide user feedback here
        }
    } catch (error) {
        console.error('Network error updating alert status:', error);
    }
}

// Helper for alert severity colors
function getSeverityColorClass(severity) {
    switch (severity.toLowerCase()) {
        case 'critical': return 'text-red-500';
        case 'high': return 'text-orange-500';
        case 'medium': return 'text-yellow-500';
        case 'low': return 'text-blue-400';
        default: return 'text-gray-400';
    }
}

// Placeholder for renderAlertsTrendChart if you want to implement it later with a charting library
function renderAlertsTrendChart(data) {
    const chartContainer = document.getElementById('alerts-line-chart');
    if (!chartContainer) return; // Exit if container not found

    // Clear previous elements
    chartContainer.innerHTML = '';

    // Simple visualization: create dots for each data point
    const maxVal = Math.max(...data);
    data.forEach((val, index) => {
        const dot = document.createElement('div');
        // Calculate position based on index and value
        const leftPos = (index / (data.length - 1)) * 100; // Spread evenly
        const bottomPos = (val / maxVal) * 90; // Scale to height, leave some padding
        dot.style.cssText = `
            position: absolute;
            left: ${leftPos}%;
            bottom: ${bottomPos}%;
            width: 8px;
            height: 8px;
            background-color: #3B82F6; /* Blue-500 */
            border-radius: 50%;
            transform: translate(-50%, 50%); /* Center the dot */
            z-index: 10;
        `;
        chartContainer.appendChild(dot);

        // Optional: Draw connecting lines (more complex, consider a charting library for production)
        if (index > 0) {
            const prevVal = data[index - 1];
            const prevLeftPos = ((index - 1) / (data.length - 1)) * 100;
            const prevBottomPos = (prevVal / maxVal) * 90;

            const line = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            line.style.cssText = `
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                overflow: visible;
                z-index: 5;
            `;
            line.innerHTML = `
                <line x1="${prevLeftPos}%" y1="${100 - prevBottomPos}%"
                      x2="${leftPos}%" y2="${100 - bottomPos}%"
                      stroke="#60A5FA" stroke-width="2" />
            `; // Lighter blue for the line
            chartContainer.appendChild(line);
        }
    });
}