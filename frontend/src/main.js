// frontend/src/main.js

document.addEventListener('DOMContentLoaded', () => {
    // --- UI Element Selectors ---
    const navLinks = document.querySelectorAll('aside nav ul li a');
    const sections = document.querySelectorAll('main section');
    const recentEventsLogViewer = document.getElementById('recent-events-log-viewer');
    const logExplorerViewer = document.getElementById('log-explorer-viewer');
    const alertsTableBody = document.getElementById('alerts-table-body');
    const criticalAlertsCount = document.getElementById('critical-alerts-count');
    const epsCount = document.getElementById('eps-count');
    const topSourcesList = document.getElementById('top-sources-list');
    const unassignedAlertsCount = document.getElementById('unassigned-alerts-count');
    const alertsLineChart = document.getElementById('alerts-line-chart');

    // Event Volume Chart elements
    const infoBar = document.getElementById('info-bar');
    const warnBar = document.getElementById('warn-bar');
    const alertCriticalBar = document.getElementById('alert-critical-bar');
    const otherBar = document.getElementById('other-bar');
    const infoPercent = document.getElementById('info-percent');
    const warnPercent = document.getElementById('warn-percent');
    const alertCriticalPercent = document.getElementById('alert-critical-percent');
    const otherPercent = document.getElementById('other-percent');


    // Log filtering elements
    const logFilterInput = document.getElementById('log-filter-input');
    const logSourceSelect = document.getElementById('log-source-select');
    const logLevelSelect = document.getElementById('log-level-select');
    const searchLogsBtn = document.getElementById('search-logs-btn');

    // Report generation elements
    const generateDailyReportBtn = document.getElementById('generate-daily-report-btn');
    const generateComplianceReportBtn = document.getElementById('generate-compliance-report-btn');
    const complianceStandardSelect = document.getElementById('compliance-standard-select');
    const reportOutput = document.getElementById('report-output');
    const reportOutputPre = reportOutput.querySelector('pre');


    // --- Global Data Store (mimics backend state, would be fetched from API) ---
    // In a real application, this data would be fetched from the backend API,
    // not managed locally in the frontend like this.
    let currentLogs = [];
    let currentAlerts = [];
    let alertTrendData = Array(7).fill(0); // For the line chart


    // --- Core UI Update Functions ---

    /**
     * Updates the Dashboard's key metrics cards and chart.
     */
    async function updateDashboardMetrics() {
        try {
            const metrics = await api.getDashboardMetrics();
            if (metrics) {
                criticalAlertsCount.textContent = metrics.critical_alerts_count;
                epsCount.textContent = metrics.eps_count.toLocaleString();
                unassignedAlertsCount.textContent = metrics.unassigned_alerts_count;

                // Update Top Event Sources
                topSourcesList.innerHTML = '';
                if (metrics.top_sources && metrics.top_sources.length > 0) {
                    metrics.top_sources.forEach(source => {
                        const li = document.createElement('li');
                        li.textContent = `${source.name} (${source.percentage}%)`;
                        topSourcesList.appendChild(li);
                    });
                } else {
                    topSourcesList.innerHTML = '<li class="text-gray-500">No recent sources</li>';
                }

                // Update Alert Trend Chart data
                alertTrendData = metrics.alert_trend_data;
                updateAlertsLineChart();

                // Update Event Volume by Type (placeholder logic)
                // In a real app, this data would also come from the backend,
                // perhaps aggregated by log level.
                const totalEvents = metrics.alert_trend_data.reduce((sum, val) => sum + val, 0); // Placeholder
                const infoRatio = 0.6;
                const warnRatio = 0.2;
                const alertCriticalRatio = 0.1;
                const otherRatio = 0.1;

                infoBar.style.width = `${infoRatio * 100}%`;
                warnBar.style.width = `${warnRatio * 100}%`;
                alertCriticalBar.style.width = `${alertCriticalRatio * 100}%`;
                otherBar.style.width = `${otherRatio * 100}%`;

                infoPercent.textContent = `INFO: ${Math.round(infoRatio * 100)}%`;
                warnPercent.textContent = `WARN: ${Math.round(warnRatio * 100)}%`;
                alertCriticalPercent.textContent = `ALERT/CRITICAL: ${Math.round(alertCriticalRatio * 100)}%`;
                otherPercent.textContent = `OTHER: ${Math.round(otherRatio * 100)}%`;

            }
        } catch (error) {
            console.error('Failed to fetch dashboard metrics:', error);
            // Optionally display an error message on the UI
        }
    }


    /**
     * Updates the Recent Events section on the Dashboard with new logs.
     * @param {Object} newLog - The new log entry to prepend (optional, for live updates).
     */
    async function updateRecentEvents(newLog = null) {
        if (!newLog) { // Full refresh if no specific new log provided
            try {
                currentLogs = await api.getRecentLogs();
                recentEventsLogViewer.innerHTML = ''; // Clear previous entries
                currentLogs.forEach(log => {
                    const p = document.createElement('p');
                    p.innerHTML = `<span class="text-blue-400">[${utils.formatDateTime(new Date(log.timestamp))}]</span> <span class="${utils.getLogLevelColor(log.level)}">[${log.level}]</span> ${log.message}`;
                    recentEventsLogViewer.appendChild(p);
                });
            } catch (error) {
                console.error('Failed to fetch recent logs:', error);
            }
        } else {
            // Prepend new log with animation
            const p = document.createElement('p');
            p.innerHTML = `<span class="text-blue-400">[${utils.formatDateTime(new Date(newLog.timestamp))}]</span> <span class="${utils.getLogLevelColor(newLog.level)}">[${newLog.level}]</span> ${newLog.message}`;
            p.classList.add('log-entry-animated');

            if (recentEventsLogViewer.firstChild) {
                recentEventsLogViewer.insertBefore(p, recentEventsLogViewer.firstChild);
            } else {
                recentEventsLogViewer.appendChild(p);
            }

            // Keep log list size manageable (e.g., max 10 entries)
            while (recentEventsLogViewer.children.length > 10) {
                recentEventsLogViewer.removeChild(recentEventsLogViewer.lastChild);
            }
        }
        recentEventsLogViewer.scrollTop = 0; // Keep at top to show newest
    }

    /**
     * Populates the Log Explorer section based on current filters.
     */
    async function populateLogExplorer() {
        logExplorerViewer.innerHTML = '<p class="text-gray-500">Loading logs...</p>';
        try {
            const filterText = logFilterInput.value.toLowerCase();
            const source = logSourceSelect.value;
            const level = logLevelSelect.value;

            const filteredLogs = await api.filterLogs({
                filter_text: filterText,
                source: source,
                level: level
            });

            logExplorerViewer.innerHTML = ''; // Clear loading message
            if (filteredLogs.length === 0) {
                logExplorerViewer.innerHTML = '<p class="text-gray-500">No logs found matching your criteria.</p>';
            } else {
                filteredLogs.forEach(log => {
                    const p = document.createElement('p');
                    p.innerHTML = `<span class="text-blue-400">[${utils.formatDateTime(new Date(log.timestamp))}]</span> <span class="${utils.getLogLevelColor(log.level)}">[${log.level}]</span> <span class="text-gray-500">[${log.source}]</span> ${log.message}`;
                    logExplorerViewer.appendChild(p);
                });
            }
        } catch (error) {
            console.error('Failed to fetch filtered logs:', error);
            logExplorerViewer.innerHTML = '<p class="text-red-400">Error loading logs. Please try again.</p>';
        }
    }

    /**
     * Populates the Alerts Table.
     */
    async function populateAlertsTable() {
        alertsTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-4">Loading alerts...</td></tr>';
        try {
            currentAlerts = await api.getOpenAlerts();
            alertsTableBody.innerHTML = ''; // Clear loading message

            if (currentAlerts.length === 0) {
                alertsTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-4">No active alerts.</td></tr>';
            } else {
                currentAlerts.forEach(alert => {
                    const tr = document.createElement('tr');
                    tr.classList.add('hover:bg-gray-700', 'transition-colors', 'duration-150');
                    tr.innerHTML = `
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${utils.getSeverityBadgeColor(alert.severity)}">${alert.severity}</span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${utils.formatDateTime(new Date(alert.timestamp))}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${alert.description}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-300">${alert.source_ip_host || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${utils.getAlertStatusColor(alert.status)}">${alert.status}</span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            ${alert.status === 'Open' ? `<button data-alert-id="${alert._id}" class="resolve-alert-btn text-blue-400 hover:text-blue-600">Resolve</button>` : 'N/A'}
                        </td>
                    `;
                    alertsTableBody.appendChild(tr);
                });

                // Add event listeners to newly created resolve buttons
                alertsTableBody.querySelectorAll('.resolve-alert-btn').forEach(button => {
                    button.addEventListener('click', async (e) => {
                        const alertId = e.target.dataset.alertId;
                        console.log(`Attempting to resolve alert: ${alertId}`);
                        const result = await api.updateAlertStatus(alertId, 'Closed');
                        if (result.success) {
                            alert('Alert resolved successfully!');
                            populateAlertsTable(); // Refresh the table
                            updateDashboardMetrics(); // Update dashboard counts
                        } else {
                            alert(`Failed to resolve alert: ${result.message}`);
                        }
                    });
                });
            }
        } catch (error) {
            console.error('Failed to fetch alerts:', error);
            alertsTableBody.innerHTML = '<tr><td colspan="6" class="text-red-400 text-center py-4">Error loading alerts. Please try again.</td></tr>';
        }
    }

    /**
     * Draws or redraws the Alerts Trend Line Chart.
     */
    function updateAlertsLineChart() {
        alertsLineChart.innerHTML = ''; // Clear previous elements
        const data = alertTrendData;
        const maxVal = Math.max(...data, 1); // Ensure division by zero is avoided
        const chartHeight = alertsLineChart.clientHeight;
        const chartWidth = alertsLineChart.clientWidth;
        const padding = 20; // Padding from chart edges

        const effectiveHeight = chartHeight - 2 * padding;
        const effectiveWidth = chartWidth - 2 * padding;

        if (data.length <= 1) { // Not enough data for a line chart
            alertsLineChart.innerHTML = '<p class="text-gray-500 text-center pt-8">Not enough data to draw trend.</p>';
            return;
        }

        const pointInterval = effectiveWidth / (data.length - 1);

        let previousX = 0;
        let previousY = effectiveHeight; // Starting from bottom (Y-axis inverted for drawing)

        data.forEach((val, index) => {
            const x = index * pointInterval + padding;
            const y = effectiveHeight - (val / maxVal) * effectiveHeight + padding; // Invert Y for drawing from bottom

            // Create Dot
            const dot = document.createElement('div');
            dot.classList.add('line-chart-dot');
            dot.style.setProperty('--dot-bottom', `${y}px`);
            dot.style.setProperty('--dot-left', `${x}px`);
            alertsLineChart.appendChild(dot);

            // Create Line segment (from previous point to current)
            if (index > 0) {
                const line = document.createElement('div');
                line.classList.add('line-chart-line');

                const dx = x - previousX;
                const dy = y - previousY;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const angle = Math.atan2(dy, dx) * 180 / Math.PI;

                line.style.setProperty('--line-left', `${previousX}px`);
                line.style.setProperty('--line-bottom', `${previousY}px`);
                line.style.setProperty('--line-width', `${distance}px`);
                line.style.transform = `rotate(${angle}deg)`;
                alertsLineChart.appendChild(line);
            }

            previousX = x;
            previousY = y;
        });
    }


    // --- Section Navigation Logic ---

    /**
     * Shows a specific section of the dashboard and updates the active navigation link.
     * @param {string} sectionId - The ID of the section to show (e.g., 'dashboard-section').
     */
    function showSection(sectionId) {
        sections.forEach(section => {
            section.classList.add('hidden');
            section.classList.remove('active-section');
        });
        document.getElementById(sectionId).classList.remove('hidden');
        document.getElementById(sectionId).classList.add('active-section');

        navLinks.forEach(link => {
            link.classList.remove('active-link', 'bg-blue-600', 'bg-blue-700', 'font-semibold');
        });
        const currentNavLink = document.querySelector(`[data-section="${sectionId.replace('-section', '')}"]`);
        if (currentNavLink) {
            currentNavLink.classList.add('active-link', 'bg-blue-600', 'font-semibold');
        }

        // Update content when switching sections
        switch (sectionId) {
            case 'dashboard-section':
                updateDashboardMetrics();
                updateRecentEvents(); // Initial load of recent events
                updateAlertsLineChart();
                reportOutput.classList.add('hidden'); // Hide report output if shown
                break;
            case 'logs-section':
                populateLogExplorer();
                reportOutput.classList.add('hidden');
                break;
            case 'alerts-section':
                populateAlertsTable();
                reportOutput.classList.add('hidden');
                break;
            case 'reports-section':
                 reportOutput.classList.add('hidden'); // Hide any previous report output
                 reportOutputPre.textContent = '';
                break;
        }
    }


    // --- Event Listeners ---

    // Sidebar navigation clicks
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.target.closest('a').dataset.section;
            showSection(`${section}-section`);
        });
    });

    // Log Explorer search/filter events
    searchLogsBtn.addEventListener('click', populateLogExplorer);
    logFilterInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            populateLogExplorer();
        }
    });
    logSourceSelect.addEventListener('change', populateLogExplorer);
    logLevelSelect.addEventListener('change', populateLogExplorer);

    // Report generation buttons
    generateDailyReportBtn.addEventListener('click', async () => {
        reportOutputPre.textContent = 'Generating daily security summary...';
        reportOutput.classList.remove('hidden');
        try {
            const report = await api.generateDailySecuritySummary();
            reportOutputPre.textContent = JSON.stringify(report, null, 2);
        } catch (error) {
            console.error('Error generating daily report:', error);
            reportOutputPre.textContent = 'Error generating report. Please check backend logs.';
            reportOutputPre.classList.add('text-red-400');
        }
    });

    generateComplianceReportBtn.addEventListener('click', async () => {
        const standard = complianceStandardSelect.value;
        reportOutputPre.textContent = `Generating ${standard} compliance audit report...`;
        reportOutput.classList.remove('hidden');
        try {
            const report = await api.generateComplianceAuditReport(standard);
            reportOutputPre.textContent = JSON.stringify(report, null, 2);
        } catch (error) {
            console.error('Error generating compliance report:', error);
            reportOutputPre.textContent = 'Error generating report. Please check backend logs.';
            reportOutputPre.classList.add('text-red-400');
        }
    });


    // --- Initialization ---

    // Initial load: show dashboard section and fetch initial data
    showSection('dashboard-section');

    // Set up a periodic refresh for dashboard metrics and recent events
    // In a real-time SIEM, this might be handled via WebSockets for instant updates.
    setInterval(() => {
        updateDashboardMetrics();
        // For recent events, we'll assume the backend sends new logs frequently
        // via a separate mechanism (e.g., WebSocket), so updateRecentEvents(newLog)
        // would be called on new log reception. For now, it periodically refreshes.
        updateRecentEvents();
    }, 5000); // Refresh every 5 seconds
});

