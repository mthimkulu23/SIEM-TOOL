// frontend/src/main.js

// Imports must be at the top level of the module
import { fetchApiData } from './api.js';
import { renderChart, updateChart } from './utils.js';

console.log("main.js: Script file started parsing."); // Very first log

try {
    console.log("main.js: Imports successful."); // Log after imports

    document.addEventListener('DOMContentLoaded', () => {
        console.log("main.js: DOMContentLoaded event fired."); // Log when DOM is ready

        try {
            const navLinks = document.querySelectorAll('nav a[data-section]'); 
            const sections = document.querySelectorAll('main section'); 

            console.log(`main.js: Found ${navLinks.length} navigation links.`); 
            if (navLinks.length === 0) {
                console.error("main.js: No navigation links found with 'nav a[data-section]' selector!");
            }

            // Function to show/hide sections (content already exists in index.html)
            function showSection(targetSectionId) {
                console.log(`main.js: Showing section: ${targetSectionId}`);
                sections.forEach(section => {
                    if (section.id === targetSectionId) {
                        section.classList.remove('hidden');
                        section.classList.add('active-section');
                    } else {
                        section.classList.add('hidden');
                        section.classList.remove('active-section');
                    }
                });
            }

            // Function to load data for a specific view and set up its listeners
            async function loadViewAndSetupListeners(viewName) {
                console.log(`main.js: Loading data and setting up listeners for view: ${viewName}`);
                switch (viewName) {
                    case 'dashboard':
                        await loadDashboardData();
                        break;
                    case 'logs': 
                        await loadLogsExplorerData();
                        setupLogsEventListeners(); // Setup listeners *after* data is potentially loaded
                        break;
                    case 'alerts': 
                        await loadAlertsCenterData();
                        setupAlertsEventListeners(); // Setup listeners *after* data is potentially loaded
                        break;
                    case 'reports': 
                        // Reports don't load data initially, just set up listeners
                        setupReportsEventListeners();
                        break;
                    default:
                        console.warn(`main.js: No data loading function for view: ${viewName}`);
                }
            }
            
            // --- Separate Listener Setup Functions for Each Section ---
            // These functions are designed to be called when their respective section
            // becomes active, ensuring listeners are attached to elements that are visible/relevant.
            // Using `onclick` and `onchange` properties directly helps avoid duplicate listeners.

            function setupLogsEventListeners() {
                console.log("main.js: Setting up logs event listeners.");
                const sendLogButton = document.getElementById('sendLogButton');
                const logInput = document.getElementById('logInput');
                const uploadStatus = document.getElementById('uploadStatus');

                if (sendLogButton) {
                    sendLogButton.onclick = async () => {
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
                            console.error('main.js: Error in sendLogButton click:', error);
                        }
                    };
                } else { console.warn("main.js: sendLogButton not found for logs view."); }

                const logFilterInput = document.getElementById('log-filter-input');
                const logSourceSelect = document.getElementById('log-source-select');
                const logLevelSelect = document.getElementById('log-level-select');
                const searchLogsBtn = document.getElementById('search-logs-btn');

                const applyLogFilters = async () => {
                    console.log("main.js: Applying log filters.");
                    const filterText = logFilterInput ? logFilterInput.value : '';
                    const source = logSourceSelect ? logSourceSelect.value : 'All';
                    const level = logLevelSelect ? logLevelSelect.value : 'All';
                    await fetchAndDisplayFilteredLogs(filterText, source, level);
                };

                if (searchLogsBtn) { searchLogsBtn.onclick = applyLogFilters; } else { console.warn("main.js: searchLogsBtn not found for logs view."); }
                if (logSourceSelect) { logSourceSelect.onchange = applyLogFilters; } else { console.warn("main.js: logSourceSelect not found for logs view."); }
                if (logLevelSelect) { logLevelSelect.onchange = applyLogFilters; } else { console.warn("main.js: logLevelSelect not found for logs view."); }
            }

            function setupAlertsEventListeners() {
                console.log("main.js: Setting up alerts event listeners.");
                const alertsTableBody = document.getElementById('alerts-table-body');
                if (alertsTableBody) {
                    // Check if onchange is already assigned to avoid multiple listeners
                    if (alertsTableBody.onchange === null) {
                        alertsTableBody.onchange = async (event) => {
                            if (event.target.classList.contains('alert-status-select')) {
                                const alertId = event.target.dataset.alertId;
                                const newStatus = event.target.value;
                                console.log(`main.js: Attempting to update alert ${alertId} to status ${newStatus}`);
                                try {
                                    const response = await fetchApiData(`/alerts/${alertId}/status`, {
                                        method: 'PUT',
                                        body: JSON.stringify({ status: newStatus })
                                    });
                                    if (response.success) {
                                        console.log(`main.js: Alert ${alertId} status updated to ${newStatus}`);
                                        await loadAlertsCenterData(); 
                                        await loadDashboardData(); 
                                    } else {
                                        console.error(`main.js: Failed to update alert ${alertId} status: ${response.message}`);
                                        // Using browser's alert for simplicity; consider custom modal for production
                                        alert(`Failed to update alert status: ${response.message}`); 
                                    }
                                } catch (error) {
                                    console.error(`main.js: Error updating alert status for ${alertId}:`, error);
                                    alert(`Error updating alert status: ${error.message}`); 
                                }
                            }
                        };
                    }
                } else { console.warn("main.js: alertsTableBody not found for alerts view."); }
            }

            function setupReportsEventListeners() {
                console.log("main.js: Setting up reports event listeners.");
                const generateDailyReportBtn = document.getElementById('generate-daily-report-btn');
                const generateComplianceReportBtn = document.getElementById('generate-compliance-report-btn');
                const complianceStandardSelect = document.getElementById('compliance-standard-select');
                const reportOutput = document.getElementById('report-output');

                if (generateDailyReportBtn) {
                    generateDailyReportBtn.onclick = async () => {
                        console.log("main.js: Generating daily report.");
                        try {
                            const data = await fetchApiData('/reports/daily_summary');
                            reportOutput.classList.remove('hidden');
                            reportOutput.querySelector('pre').textContent = JSON.stringify(data, null, 2);
                            console.log("main.js: Daily report generated.");
                        } catch (error) {
                            console.error('main.js: Error fetching daily report:', error);
                            reportOutput.classList.remove('hidden');
                            reportOutput.querySelector('pre').textContent = 'Error fetching report.';
                        }
                    };
                } else { console.warn("main.js: generateDailyReportBtn not found for reports view."); }

                if (generateComplianceReportBtn) {
                    generateComplianceReportBtn.onclick = async () => {
                        console.log("main.js: Generating compliance report.");
                        const standard = complianceStandardSelect.value;
                        try {
                            const data = await fetchApiData('/reports/compliance_audit', {
                                method: 'POST',
                                body: JSON.stringify({ standard: standard })
                            });
                            reportOutput.classList.remove('hidden');
                            reportOutput.querySelector('pre').textContent = JSON.stringify(data, null, 2);
                            console.log("main.js: Compliance report generated.");
                        } catch (error) {
                            console.error('main.js: Error fetching compliance report:', error);
                            reportOutput.classList.remove('hidden');
                            reportOutput.querySelector('pre').textContent = 'Error fetching report.';
                        }
                    };
                } else { console.warn("main.js: generateComplianceReportBtn not found for reports view."); }
            }


            // --- Core Navigation Logic (Initial setup) ---
            navLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const targetViewName = link.dataset.section; // 'dashboard', 'logs', 'alerts', 'reports'
                    console.log(`main.js: Navigation click - target section: ${targetViewName}`);

                    // Remove 'active-link' from all nav links and add to the clicked one
                    navLinks.forEach(nav => nav.classList.remove('active-link'));
                    link.classList.add('active-link');

                    // Show the relevant section and then load its data and setup listeners
                    showSection(`${targetViewName}-section`); 
                    loadViewAndSetupListeners(targetViewName); // Calls the specific data loading function
                });
            });

            // Initial page load: Simulate a click on the Dashboard link
            const initialActiveLink = document.querySelector('nav a[data-section="dashboard"]');
            if (initialActiveLink) {
                console.log("main.js: Simulating initial click on Dashboard link.");
                initialActiveLink.click(); 
            } else {
                console.error("main.js: Initial dashboard link not found (selector 'nav a[data-section=\"dashboard\"]' failed)!");
            }


            // --- Dashboard View Functions ---
            async function loadDashboardData() {
                console.log("main.js: Loading dashboard data...");
                try {
                    const metrics = await fetchApiData('/dashboard/metrics');
                    if (metrics) {
                        console.log("main.js: Dashboard metrics received:", metrics);

                        // Update dashboard cards
                        document.getElementById('critical-alerts-count').textContent = metrics.critical_alerts_count;
                        document.getElementById('eps-count').textContent = metrics.eps_count;
                        document.getElementById('unassigned-alerts-count').textContent = metrics.unassigned_alerts_count;

                        // Update Top Event Sources List
                        const topSourcesList = document.getElementById('top-sources-list');
                        if (topSourcesList) {
                            topSourcesList.innerHTML = '';
                            metrics.top_sources.forEach(source => {
                                const li = document.createElement('li');
                                li.textContent = `${source.name} (${source.percentage}%)`;
                                topSourcesList.appendChild(li);
                            });
                        } else {
                            console.warn("main.js: top-sources-list element not found.");
                        }

                        // Update Event Volume by Type (progress bars)
                        const eventVolumeData = metrics.event_volume_by_type;
                        if (eventVolumeData) {
                            // Helper to safely update bars
                            const updateBar = (idPrefix, value, label) => {
                                const bar = document.getElementById(`${idPrefix}-bar`);
                                const percentSpan = document.getElementById(`${idPrefix}-percent`);
                                if (bar && percentSpan) {
                                    bar.style.width = `${value}%`;
                                    percentSpan.textContent = `${label}: ${value}%`;
                                } else {
                                    console.warn(`main.js: Element with id '${idPrefix}-bar' or '${idPrefix}-percent' not found.`);
                                }
                            };

                            updateBar('info', eventVolumeData.INFO || 0, 'INFO');
                            updateBar('warn', eventVolumeData.WARN || 0, 'WARN');
                            updateBar('alert-critical', (eventVolumeData.CRITICAL || 0) + (eventVolumeData['ALERT-CRITICAL'] || 0), 'ALERT/CRITICAL');
                            updateBar('auth-failed', eventVolumeData.AUTH_FAILED || 0, 'AUTH_FAILED');
                            updateBar('other', eventVolumeData.OTHER || 0, 'OTHER');
                            
                        } else {
                            console.warn("main.js: eventVolumeData not found in metrics.");
                        }
                        console.log("main.js: DEBUG (Frontend): Event Volume Data processed:", metrics.event_volume_by_type);


                        // Update Alerts Trend (Chart.js)
                        const alertsTrendCanvasDiv = document.getElementById('alerts-line-chart');
                        if (alertsTrendCanvasDiv) {
                            let chartCanvas = alertsTrendCanvasDiv.querySelector('canvas');
                            if (!chartCanvas) {
                                console.log("main.js: Creating new canvas for alerts trend chart.");
                                chartCanvas = document.createElement('canvas');
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
                                     console.log("main.js: Rendered new alerts trend chart.");
                                } else {
                                    updateChart(chartCanvas.chartInstance, chartData);
                                    console.log("main.js: Updated existing alerts trend chart.");
                                }
                            } else {
                                console.warn("main.js: WARNING: renderChart/updateChart functions not found. Chart.js might not be loaded or utils.js is incorrect.");
                                const trendText = document.createElement('p');
                                trendText.textContent = `Alert Trend Data: [${metrics.alert_trend_data.join(', ')}]`;
                                alertsTrendCanvasDiv.innerHTML = '';
                                alertsTrendCanvasDiv.appendChild(trendText);
                            }
                        } else {
                            console.warn("main.js: alerts-line-chart element not found.");
                        }
                    } else {
                        console.warn("main.js: No metrics received from /dashboard/metrics API.");
                    }
                    
                    console.log("main.js: Loading recent security events (logs).");
                    const recentLogs = await fetchApiData('/logs/recent');
                    const recentEventsLogViewer = document.getElementById('recent-events-log-viewer');

                    if (recentEventsLogViewer) {
                        recentEventsLogViewer.innerHTML = '';

                        if (recentLogs && recentLogs.length > 0) {
                            console.log(`main.js: Received ${recentLogs.length} recent logs.`);
                            const table = document.createElement('table');
                            table.className = 'min-w-full divide-y divide-gray-700 rounded-xl overflow-hidden';

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
                            tbody.className = 'divide-y divide-gray-700';
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
                            console.log("main.js: No recent security events found.");
                            const p = document.createElement('p');
                            p.textContent = 'No recent security events found.';
                            p.className = 'text-center text-gray-500 py-4';
                            recentEventsLogViewer.appendChild(p);
                        }
                    } else {
                        console.error("main.js: recent-events-log-viewer element not found.");
                    }

                } catch (error) {
                    console.error("main.js: Error in loadDashboardData:", error);
                }
            }

            // --- Logs Explorer View Functions ---
            async function loadLogsExplorerData() {
                console.log("main.js: Loading Logs Explorer data...");
                await fetchAndDisplayFilteredLogs();
            }

            async function fetchAndDisplayFilteredLogs(filterText = '', source = 'All', level = 'All') {
                const logsTableBody = document.getElementById('log-explorer-viewer');
                if (!logsTableBody) {
                    console.error("main.js: Logs explorer viewer element not found for filter.");
                    return;
                }
                logsTableBody.innerHTML = '';

                try {
                    const logs = await fetchApiData('/logs/filter', {
                        method: 'POST',
                        body: JSON.stringify({ filter_text: filterText, source: source, level: level })
                    });

                    if (logs && logs.length > 0) {
                        console.log(`main.js: Received ${logs.length} filtered logs.`);
                        const table = document.createElement('table');
                        table.className = 'min-w-full divide-y divide-gray-700 rounded-xl overflow-hidden';

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
                        tbody.className = 'divide-y divide-gray-700';
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
                        console.log("main.js: No logs found matching filter criteria.");
                        const p = document.createElement('p');
                        p.textContent = 'No logs found matching your criteria.';
                        p.className = 'text-center text-gray-500 py-4';
                        logsTableBody.appendChild(p);
                    }
                } catch (error) {
                    console.error("main.js: Error fetching filtered logs:", error);
                    logsTableBody.innerHTML = `<p class="text-red-500 text-center py-4">Error loading logs. Please try again.</p>`;
                }
            }


            // --- Alerts Center View Functions ---
            async function loadAlertsCenterData() {
                console.log("main.js: Loading Alerts Center data...");
                const alertsTableBody = document.getElementById('alerts-table-body');
                if (!alertsTableBody) {
                    console.error("main.js: Alerts table body element not found.");
                    return;
                }
                alertsTableBody.innerHTML = '';

                try {
                    const alerts = await fetchApiData('/alerts/open');
                    if (alerts && alerts.length > 0) {
                        console.log(`main.js: Received ${alerts.length} open alerts.`);
                        alerts.forEach(alert => {
                            const row = alertsTableBody.insertRow();
                            row.insertCell().textContent = alert.severity || 'N/A';
                            row.insertCell().textContent = alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'N/A';
                            row.insertCell().textContent = alert.description || 'N/A';
                            row.insertCell().textContent = alert.source_ip_host || 'N/A';
                            row.insertCell().textContent = alert.status || 'N/A';

                            const actionCell = row.insertCell();
                            const select = document.createElement('select');
                            select.className = 'alert-status-select p-2 rounded-md bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-200';
                            select.dataset.alertId = alert._id;

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
                        console.log("main.js: No open alerts found.");
                        const row = alertsTableBody.insertRow();
                        const cell = row.insertCell();
                        cell.colSpan = 6;
                        cell.textContent = 'No open alerts found.';
                        cell.className = 'text-center text-gray-500 py-4';
                    }
                } catch (error) {
                    console.error("main.js: Error loading alerts data:", error);
                    alertsTableBody.innerHTML = `<p class="text-red-500 text-center py-4">Error loading alerts. Please try again.</p>`;
                }
            }

            // --- Security Reports View Functions ---
            async function loadSecurityReportsData() {
                console.log("main.js: Loading Security Reports view...");
            }

        } catch (domError) {
            console.error("main.js: Error within DOMContentLoaded listener:", domError);
        }
    });

} catch (globalError) {
    console.error("main.js: Global script error (before DOMContentLoaded):", globalError);
}
