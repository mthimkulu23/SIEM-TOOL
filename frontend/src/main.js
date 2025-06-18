// frontend/src/main.js

import { fetchApiData } from './api.js'; // Only fetchApiData is needed from api.js directly
import { renderChart, updateChart } from './utils.js'; // Chart rendering utilities

document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.getElementById('main-content');
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('main section'); // Select all sections

    // Function to render partials (views)
    async function renderPartial(viewName) {
        try {
            // Fetch HTML for the view
            const response = await fetch(`/src/views/${viewName}.html`);
            if (!response.ok) {
                throw new Error(`Failed to load view: ${viewName}.html`);
            }
            mainContent.innerHTML = await response.text();
            
            // Execute view-specific JavaScript after HTML is loaded
            await executeViewScript(viewName); 
            // Setup event listeners for elements *within* the newly loaded view
            setupEventListenersForCurrentView(viewName); 
        } catch (error) {
            console.error('Error rendering partial:', error);
            mainContent.innerHTML = `<p class="text-red-500">Error loading content. Please try again.</p>`;
        }
    }

    // Function to execute JavaScript for the loaded view (e.g., fetching data)
    async function executeViewScript(viewName) {
        switch (viewName) {
            case 'dashboard':
                await loadDashboardData();
                break;
            case 'logs': 
                await loadLogsExplorerData();
                break;
            case 'alerts': 
                await loadAlertsCenterData();
                break;
            case 'reports': 
                await loadSecurityReportsData();
                break;
        }
    }

    // Function to set up event listeners for dynamically loaded content
    // This is called *after* the HTML for a view is loaded into main-content
    function setupEventListenersForCurrentView(viewName) {
        if (viewName === 'logs') {
            const sendLogButton = document.getElementById('sendLogButton');
            const logInput = document.getElementById('logInput');
            const uploadStatus = document.getElementById('uploadStatus');

            if (sendLogButton) {
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

                        const response = await fetchApiData('/logs/ingest', {
                            method: 'POST',
                            body: JSON.stringify({ raw_log: rawLog }),
                        });

                        if (response && response.log_id) { 
                            uploadStatus.textContent = `Log uploaded successfully! Log ID: ${response.log_id}`;
                            uploadStatus.style.color = 'green';
                            logInput.value = ''; 

                            // Refresh relevant dashboard/logs/alerts data after ingestion
                            // Await these calls to ensure data is updated before user sees it
                            await loadLogsExplorerData(); 
                            await loadDashboardData();    
                            await loadAlertsCenterData(); 
                        } else {
                            uploadStatus.textContent = `Error uploading log: ${response.error || 'Unknown error'}`;
                            uploadStatus.style.color = 'red';
                        }
                    } catch (error) {
                        uploadStatus.textContent = `Network error: ${error.message}`;
                        uploadStatus.style.color = 'red';
                        console.error('Error:', error);
                    }
                });
            }

            const logFilterInput = document.getElementById('log-filter-input');
            const logSourceSelect = document.getElementById('log-source-select');
            const logLevelSelect = document.getElementById('log-level-select');
            const searchLogsBtn = document.getElementById('search-logs-btn');

            const applyLogFilters = async () => {
                const filterText = logFilterInput.value;
                const source = logSourceSelect.value;
                const level = logLevelSelect.value;
                await fetchAndDisplayFilteredLogs(filterText, source, level);
            };

            if (searchLogsBtn) {
                searchLogsBtn.addEventListener('click', applyLogFilters);
            }
            if (logSourceSelect) {
                logSourceSelect.addEventListener('change', applyLogFilters);
            }
            if (logLevelSelect) {
                logLevelSelect.addEventListener('change', applyLogFilters);
            }

        } else if (viewName === 'alerts') {
             const alertsTableBody = document.getElementById('alerts-table-body');
            if (alertsTableBody) {
                alertsTableBody.addEventListener('change', async (event) => {
                    if (event.target.classList.contains('alert-status-select')) {
                        const alertId = event.target.dataset.alertId;
                        const newStatus = event.target.value;
                        console.log(`Attempting to update alert ${alertId} to status ${newStatus}`);
                        try {
                            const response = await fetchApiData(`/alerts/${alertId}/status`, {
                                method: 'PUT',
                                body: JSON.stringify({ status: newStatus })
                            });
                            if (response.success) {
                                console.log(`Alert ${alertId} status updated to ${newStatus}`);
                                await loadAlertsCenterData(); 
                                await loadDashboardData(); 
                            } else {
                                console.error(`Failed to update alert ${alertId} status: ${response.message}`);
                                alert(`Failed to update alert status: ${response.message}`); 
                            }
                        } catch (error) {
                            console.error(`Error updating alert status for ${alertId}:`, error);
                            alert(`Error updating alert status: ${error.message}`); 
                        }
                    }
                });
            }
        } else if (viewName === 'reports') {
            const generateDailyReportBtn = document.getElementById('generate-daily-report-btn');
            const generateComplianceReportBtn = document.getElementById('generate-compliance-report-btn');
            const complianceStandardSelect = document.getElementById('compliance-standard-select');
            const reportOutput = document.getElementById('report-output');

            if (generateDailyReportBtn) {
                generateDailyReportBtn.addEventListener('click', async () => {
                    try {
                        const data = await fetchApiData('/reports/daily_summary');
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
                    const standard = complianceStandardSelect.value;
                    try {
                        const data = await fetchApiData('/reports/compliance_audit', {
                            method: 'POST',
                            body: JSON.stringify({ standard: standard })
                        });
                        reportOutput.classList.remove('hidden');
                        reportOutput.querySelector('pre').textContent = JSON.stringify(data, null, 2);
                    } catch (error) {
                        console.error('Error fetching compliance report:', error);
                        reportOutput.classList.remove('hidden');
                        reportOutput.querySelector('pre').textContent = 'Error fetching report.';
                    }
                });
            }
        }
    }


    // --- Core Navigation Logic (Initial setup) ---
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetViewName = link.dataset.section; // 'dashboard', 'logs', 'alerts', 'reports'

            navLinks.forEach(nav => nav.classList.remove('active-link'));
            link.classList.add('active-link');

            // Render the partial view
            renderPartial(targetViewName);
        });
    });

    // Initial page load: Render the dashboard
    const initialActiveLink = document.querySelector('nav a[data-section="dashboard"]');
    if (initialActiveLink) {
        initialActiveLink.click(); // Simulate a click to load dashboard initially
    }


    // --- Dashboard View Functions ---
    async function loadDashboardData() {
        console.log("Loading dashboard data...");
        try {
            const metrics = await fetchApiData('/dashboard/metrics');
            if (metrics) {
                // Corrected IDs to match kebab-case in HTML
                document.getElementById('critical-alerts-count').textContent = metrics.critical_alerts_count;
                document.getElementById('eps-count').textContent = metrics.eps_count;
                document.getElementById('unassigned-alerts-count').textContent = metrics.unassigned_alerts_count;

                const topSourcesList = document.getElementById('top-sources-list'); // Corrected ID
                if (topSourcesList) {
                    topSourcesList.innerHTML = '';
                    metrics.top_sources.forEach(source => {
                        const li = document.createElement('li');
                        li.textContent = `${source.name} (${source.percentage}%)`;
                        topSourcesList.appendChild(li);
                    });
                }

                // --- Update Event Volume by Type (Bar Chart simulation) ---
                // The HTML uses progress bars, so we'll update those directly
                const eventVolumeData = metrics.event_volume_by_type;
                if (eventVolumeData) {
                    // Update INFO
                    const infoPercent = eventVolumeData.INFO || 0;
                    document.getElementById('info-bar').style.width = `${infoPercent}%`;
                    document.getElementById('info-percent').textContent = `INFO: ${infoPercent}%`;

                    // Update WARN
                    const warnPercent = eventVolumeData.WARN || 0;
                    document.getElementById('warn-bar').style.width = `${warnPercent}%`;
                    document.getElementById('warn-percent').textContent = `WARN: ${warnPercent}%`;

                    // Update ALERT/CRITICAL (map CRITICAL from backend to ALERT/CRITICAL)
                    const criticalPercent = (eventVolumeData.CRITICAL || 0) + (eventVolumeData['ALERT-CRITICAL'] || 0); // Include ALERT-CRITICAL if backend sends it
                    document.getElementById('alert-critical-bar').style.width = `${criticalPercent}%`;
                    document.getElementById('alert-critical-percent').textContent = `ALERT/CRITICAL: ${criticalPercent}%`;

                    // Update AUTH_FAILED
                    const authFailedPercent = eventVolumeData.AUTH_FAILED || 0;
                    const authFailedBar = document.getElementById('auth-failed-bar');
                    const authFailedPercentSpan = document.getElementById('auth-failed-percent');
                    if (authFailedBar && authFailedPercentSpan) { // Only update if elements exist in HTML
                        authFailedBar.style.width = `${authFailedPercent}%`;
                        authFailedPercentSpan.textContent = `AUTH_FAILED: ${authFailedPercent}%`;
                    } else if (authFailedPercent > 0) {
                         console.warn("WARNING: 'AUTH_FAILED' event volume is present but no dedicated bar/percentage elements found in dashboard.html. Please add elements with IDs 'auth-failed-bar' and 'auth-failed-percent'.");
                    }

                    // Update OTHER
                    let otherPercent = eventVolumeData.OTHER || 0;
                    document.getElementById('other-bar').style.width = `${otherPercent}%`;
                    document.getElementById('other-percent').textContent = `OTHER: ${otherPercent}%`;
                }
                console.log("DEBUG (Frontend): Event Volume Data processed:", metrics.event_volume_by_type);


                // --- Update Alerts Trend (Line Chart) ---
                const alertsTrendCanvasDiv = document.getElementById('alerts-line-chart'); // Target the div
                if (alertsTrendCanvasDiv) {
                    // Create a canvas element inside the div if it doesn't exist
                    let chartCanvas = alertsTrendCanvasDiv.querySelector('canvas');
                    if (!chartCanvas) {
                        chartCanvas = document.createElement('canvas');
                        // Set basic styling for the canvas if needed, e.g., for responsiveness
                        chartCanvas.style.width = '100%';
                        chartCanvas.style.height = '100%';
                        alertsTrendCanvasDiv.appendChild(chartCanvas);
                    }

                    if (typeof renderChart === 'function' && typeof updateChart === 'function') {
                        const chartData = {
                            labels: ['6h Ago', '', '', '', '', '', 'Now'],
                            datasets: [{
                                label: 'Alerts Count',
                                data: metrics.alert_trend_data,
                                borderColor: 'rgb(75, 192, 192)',
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                tension: 0.1,
                                fill: true,
                            }]
                        };

                        if (!chartCanvas.chartInstance) {
                             chartCanvas.chartInstance = renderChart(chartCanvas, chartData, 'line');
                        } else {
                            updateChart(chartCanvas.chartInstance, chartData);
                        }
                    } else {
                        console.warn("WARNING: renderChart/updateChart functions not found. Chart.js might not be loaded or utils.js is incorrect.");
                        const trendText = document.createElement('p');
                        trendText.textContent = `Alert Trend Data: [${metrics.alert_trend_data.join(', ')}]`;
                        alertsTrendCanvasDiv.innerHTML = ''; // Clear div
                        alertsTrendCanvasDiv.appendChild(trendText);
                    }
                }
            }
            
            // --- Fetch and display Recent Security Events (Logs) ---
            console.log("Loading recent security events (logs).");
            const recentLogs = await fetchApiData('/logs/recent');
            const recentEventsLogViewer = document.getElementById('recent-events-log-viewer'); // The div container

            if (recentEventsLogViewer) {
                recentEventsLogViewer.innerHTML = ''; // Clear existing content

                if (recentLogs && recentLogs.length > 0) {
                    // Dynamically create a table inside the div
                    const table = document.createElement('table');
                    table.className = 'min-w-full divide-y divide-gray-700 rounded-xl overflow-hidden'; // Tailwind classes

                    const thead = document.createElement('thead');
                    thead.className = 'bg-gray-700';
                    thead.innerHTML = `
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Time</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Host</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Source</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Level</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Message</th>
                        </tr>
                    `;
                    table.appendChild(thead);

                    const tbody = document.createElement('tbody');
                    tbody.className = 'divide-y divide-gray-700'; // Tailwind classes
                    recentLogs.forEach(log => {
                        const row = tbody.insertRow();
                        row.insertCell().textContent = log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A';
                        row.insertCell().textContent = log.host || 'N/A';
                        row.insertCell().textContent = log.source || 'N/A';
                        row.insertCell().textContent = log.level || 'N/A';
                        row.insertCell().textContent = log.message || 'N/A';
                    });
                    table.appendChild(tbody);
                    recentEventsLogViewer.appendChild(table);

                } else {
                    const p = document.createElement('p');
                    p.textContent = 'No recent security events found.';
                    p.className = 'text-center text-gray-500 py-4';
                    recentEventsLogViewer.appendChild(p);
                }
            }

        } catch (error) {
            console.error("Error loading dashboard data:", error);
            // Optionally display a user-friendly error message on the dashboard
        }
    }

    // --- Logs Explorer View Functions ---
    async function loadLogsExplorerData() {
        console.log("Loading Logs Explorer data...");
        await fetchAndDisplayFilteredLogs(); // Call with default filters on load
    }

    async function fetchAndDisplayFilteredLogs(filterText = '', source = 'All', level = 'All') {
        const logsTableBody = document.getElementById('log-explorer-viewer'); // Target the div
        if (!logsTableBody) {
            console.error("Logs explorer viewer element not found.");
            return;
        }
        logsTableBody.innerHTML = ''; // Clear existing content

        try {
            const logs = await fetchApiData('/logs/filter', {
                method: 'POST',
                body: JSON.stringify({ filter_text: filterText, source: source, level: level })
            });

            if (logs && logs.length > 0) {
                 // Dynamically create a table inside the div
                const table = document.createElement('table');
                table.className = 'min-w-full divide-y divide-gray-700 rounded-xl overflow-hidden'; // Tailwind classes

                const thead = document.createElement('thead');
                thead.className = 'bg-gray-700';
                thead.innerHTML = `
                    <tr>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Time</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Host</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Source</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Level</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Message</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Source IP</th>
                        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Destination IP</th>
                    </tr>
                `;
                table.appendChild(thead);

                const tbody = document.createElement('tbody');
                tbody.className = 'divide-y divide-gray-700'; // Tailwind classes
                logs.forEach(log => {
                    const row = tbody.insertRow();
                    row.insertCell().textContent = log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A';
                    row.insertCell().textContent = log.host || 'N/A';
                    row.insertCell().textContent = log.source || 'N/A';
                    row.insertCell().textContent = log.level || 'N/A';
                    row.insertCell().textContent = log.message || 'N/A';
                    row.insertCell().textContent = log.source_ip_host || 'N/A';
                    row.insertCell().textContent = log.destination_ip_host || 'N/A';
                });
                table.appendChild(tbody);
                logsTableBody.appendChild(table);

            } else {
                const p = document.createElement('p');
                p.textContent = 'No logs found matching your criteria.';
                p.className = 'text-center text-gray-500 py-4';
                logsTableBody.appendChild(p);
            }
        } catch (error) {
            console.error("Error fetching filtered logs:", error);
            logsTableBody.innerHTML = `<p class="text-red-500 text-center py-4">Error loading logs. Please try again.</p>`;
        }
    }


    // --- Alerts Center View Functions ---
    async function loadAlertsCenterData() {
        console.log("Loading Alerts Center data...");
        const alertsTableBody = document.getElementById('alerts-table-body');
        if (!alertsTableBody) {
            console.error("Alerts table body element not found.");
            return;
        }
        alertsTableBody.innerHTML = ''; // Clear existing rows

        try {
            const alerts = await fetchApiData('/alerts/open');
            if (alerts && alerts.length > 0) {
                alerts.forEach(alert => {
                    const row = alertsTableBody.insertRow();
                    row.insertCell().textContent = alert.severity || 'N/A';
                    row.insertCell().textContent = alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'N/A';
                    row.insertCell().textContent = alert.description || 'N/A';
                    row.insertCell().textContent = alert.source_ip_host || 'N/A';
                    row.insertCell().textContent = alert.status || 'N/A';

                    // Action cell with a dropdown for status update
                    const actionCell = row.insertCell();
                    const select = document.createElement('select');
                    select.className = 'alert-status-select p-2 rounded-md bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-200';
                    select.dataset.alertId = alert._id; // Store MongoDB _id for updating

                    ['Open', 'Investigating', 'Closed'].forEach(statusOption => {
                        const option = document.createElement('option');
                        option.value = statusOption;
                        option.textContent = statusOption;
                        if (statusOption === alert.status) {
                            option.selected = true;
                        }
                        select.appendChild(option);
                    });
                    actionCell.appendChild(select);
                });
            } else {
                const row = alertsTableBody.insertRow();
                const cell = row.insertCell();
                cell.colSpan = 6;
                cell.textContent = 'No open alerts found.';
                cell.className = 'text-center text-gray-500 py-4';
            }
        } catch (error) {
            console.error("Error loading alerts data:", error);
            alertsTableBody.innerHTML = `<p class="text-red-500 text-center py-4">Error loading alerts. Please try again.</p>`;
        }
    }

    // --- Security Reports View Functions ---
    async function loadSecurityReportsData() {
        console.log("Loading Security Reports view...");
        // The event listeners for buttons are set up in setupEventListenersForCurrentView
        // No initial data fetch needed here, as reports are generated on button click.
    }
});
