// frontend/src/main.js
import { api } from './api.js';

let alertTrendChartInstance; // To store the Chart.js instance

// --- UI Navigation ---
const navButtons = document.querySelectorAll('nav button');
const contentSections = document.querySelectorAll('.content-section');

function showSection(sectionId) {
    contentSections.forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');

    navButtons.forEach(button => {
        button.classList.remove('active');
        if (button.id === `nav-${sectionId.replace('-section', '')}`) {
            button.classList.add('active');
        }
    });

    // Refresh data for the active section
    if (sectionId === 'dashboard-section') {
        displayDashboard();
    } else if (sectionId === 'logs-section') {
        displayLogs();
    } else if (sectionId === 'alerts-section') {
        displayAlerts();
    }
}

navButtons.forEach(button => {
    button.addEventListener('click', () => {
        const sectionId = `${button.id.replace('nav-', '')}-section`;
        showSection(sectionId);
    });
});

// --- Dashboard Functions ---
async function displayDashboard() {
    try {
        const metrics = await api.fetchDashboardMetrics();
        document.getElementById('critical-alerts-count').textContent = metrics.critical_alerts_count;
        document.getElementById('eps-count').textContent = metrics.eps_count;
        document.getElementById('unassigned-alerts-count').textContent = metrics.unassigned_alerts_count;

        const topSourcesList = document.getElementById('top-sources-list');
        topSourcesList.innerHTML = '';
        if (metrics.top_sources && metrics.top_sources.length > 0) {
            metrics.top_sources.forEach(source => {
                const li = document.createElement('li');
                li.textContent = `${source.name} (${source.percentage}%)`;
                topSourcesList.appendChild(li);
            });
        } else {
            topSourcesList.innerHTML = '<li>No log sources found.</li>';
        }

        // Render Alert Trend Chart
        if (alertTrendChartInstance) {
            alertTrendChartInstance.destroy(); // Destroy previous instance if it exists
        }
        const ctx = document.getElementById('alertTrendChart').getContext('2d');
        alertTrendChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({length: 7}, (_, i) => `Day ${i+1}`), // Simple labels for 7 days
                datasets: [{
                    label: 'Alerts Over Time',
                    data: metrics.alert_trend_data,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Allows flexible sizing
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Alerts'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Last 7 Days'
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error("Failed to load dashboard metrics:", error);
        // Display user-friendly error message on dashboard
        document.getElementById('critical-alerts-count').textContent = 'Error';
        document.getElementById('eps-count').textContent = 'Error';
        document.getElementById('unassigned-alerts-count').textContent = 'Error';
        document.getElementById('top-sources-list').innerHTML = '<li>Error loading sources.</li>';
    }
}

// --- Log Viewer Functions ---
const logFilterText = document.getElementById('log-filter-text');
const logFilterSource = document.getElementById('log-filter-source');
const logFilterLevel = document.getElementById('log-filter-level');
const applyLogFiltersButton = document.getElementById('apply-log-filters');
const logsTableBody = document.getElementById('logs-table').getElementsByTagName('tbody')[0];

async function populateSourceFilter() {
    try {
        const sources = await api.fetchLogSources();
        logFilterSource.innerHTML = ''; // Clear existing options
        sources.forEach(source => {
            const option = document.createElement('option');
            option.value = source;
            option.textContent = source;
            logFilterSource.appendChild(option);
        });
    } catch (error) {
        console.error("Failed to populate source filter:", error);
    }
}

async function displayLogs() {
    logsTableBody.innerHTML = '<tr><td colspan="7">Loading logs...</td></tr>'; // Show loading state
    try {
        const filterText = logFilterText.value;
        const source = logFilterSource.value;
        const level = logFilterLevel.value;

        const logs = await api.filterLogs(filterText, source, level);
        logsTableBody.innerHTML = ''; // Clear existing rows

        if (logs.length === 0) {
            logsTableBody.innerHTML = '<tr><td colspan="7">No logs found.</td></tr>';
            return;
        }

        logs.forEach(log => {
            const row = logsTableBody.insertRow();
            row.insertCell().textContent = new Date(log.timestamp).toLocaleString();
            row.insertCell().textContent = log.host || 'N/A';
            row.insertCell().textContent = log.source || 'N/A';
            row.insertCell().textContent = log.level || 'N/A';
            row.insertCell().textContent = log.message || 'N/A';
            row.insertCell().textContent = log.source_ip_host || 'N/A';
            row.insertCell().textContent = log.destination_ip_host || 'N/A';
        });
    } catch (error) {
        console.error("Failed to load logs:", error);
        logsTableBody.innerHTML = `<tr><td colspan="7" style="color: red;">Error loading logs: ${error.message}</td></tr>`;
    }
}

applyLogFiltersButton.addEventListener('click', displayLogs);

// --- Alert Management Functions ---
const alertsTableBody = document.getElementById('alerts-table').getElementsByTagName('tbody')[0];

async function displayAlerts() {
    alertsTableBody.innerHTML = '<tr><td colspan="6">Loading alerts...</td></tr>'; // Show loading state
    try {
        const alerts = await api.fetchOpenAlerts();
        alertsTableBody.innerHTML = ''; // Clear existing rows

        if (alerts.length === 0) {
            alertsTableBody.innerHTML = '<tr><td colspan="6">No open alerts found.</td></tr>';
            return;
        }

        alerts.forEach(alert => {
            const row = alertsTableBody.insertRow();
            row.insertCell().textContent = new Date(alert.timestamp).toLocaleString();
            row.insertCell().textContent = alert.severity || 'N/A';
            row.insertCell().textContent = alert.description || 'N/A';
            row.insertCell().textContent = alert.source_ip_host || 'N/A';
            const statusCell = row.insertCell();
            statusCell.textContent = alert.status || 'N/A';
            const actionsCell = row.insertCell();

            if (alert.status === 'Open') {
                const closeButton = document.createElement('button');
                closeButton.textContent = 'Close';
                closeButton.classList.add('status-button');
                closeButton.addEventListener('click', async () => {
                    if (confirm(`Are you sure you want to close alert: "${alert.description}"?`)) {
                        try {
                            const result = await api.updateAlertStatus(alert.id, 'Closed');
                            if (result.success) {
                                alert('Alert closed successfully!');
                                displayAlerts(); // Refresh alerts list
                            } else {
                                alert(`Failed to close alert: ${result.message}`);
                            }
                        } catch (error) {
                            alert(`Error closing alert: ${error.message}`);
                            console.error("Error closing alert:", error);
                        }
                    }
                });
                actionsCell.appendChild(closeButton);
            } else {
                statusCell.classList.add('closed');
            }
        });
    } catch (error) {
        console.error("Failed to load alerts:", error);
        alertsTableBody.innerHTML = `<tr><td colspan="6" style="color: red;">Error loading alerts: ${error.message}</td></tr>`;
    }
}

// --- Log Ingestion Function ---
const ingestLogForm = document.getElementById('ingest-log-form');
const rawLogInput = document.getElementById('raw-log-input');
const ingestMessage = document.getElementById('ingest-message');

ingestLogForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const rawLog = rawLogInput.value.trim();
    if (!rawLog) {
        ingestMessage.textContent = 'Please enter a log to ingest.';
        ingestMessage.style.color = 'orange';
        return;
    }

    ingestMessage.textContent = 'Ingesting log...';
    ingestMessage.style.color = 'black';

    try {
        const response = await api.ingestLog(rawLog);
        ingestMessage.textContent = `Success: ${response.message} (ID: ${response.log_id})`;
        ingestMessage.style.color = 'green';
        rawLogInput.value = ''; // Clear input
        // Optionally refresh logs/dashboard after ingestion
        displayDashboard();
        displayLogs();
    } catch (error) {
        ingestMessage.textContent = `Error: ${error.message}`;
        ingestMessage.style.color = 'red';
        console.error("Log ingestion failed:", error);
    }
});

// --- Reports Functions ---
const generateDailySummaryButton = document.getElementById('generate-daily-summary');
const dailySummaryOutput = document.getElementById('daily-summary-output');
const complianceStandardSelect = document.getElementById('compliance-standard');
const generateComplianceReportButton = document.getElementById('generate-compliance-report');
const complianceAuditOutput = document.getElementById('compliance-audit-output');

generateDailySummaryButton.addEventListener('click', async () => {
    dailySummaryOutput.textContent = 'Generating daily summary...';
    try {
        const report = await api.fetchDailySummaryReport();
        dailySummaryOutput.textContent = JSON.stringify(report, null, 2);
    } catch (error) {
        dailySummaryOutput.textContent = `Error generating daily summary: ${error.message}`;
        dailySummaryOutput.style.color = 'red';
        console.error("Daily summary report failed:", error);
    }
});

generateComplianceReportButton.addEventListener('click', async () => {
    const standard = complianceStandardSelect.value;
    if (!standard) {
        complianceAuditOutput.textContent = 'Please select a compliance standard.';
        complianceAuditOutput.style.color = 'orange';
        return;
    }
    complianceAuditOutput.textContent = `Generating compliance audit for ${standard}...`;
    try {
        const report = await api.fetchComplianceAuditReport(standard);
        complianceAuditOutput.textContent = JSON.stringify(report, null, 2);
    } catch (error) {
        complianceAuditOutput.textContent = `Error generating compliance audit: ${error.message}`;
        complianceAuditOutput.style.color = 'red';
        console.error("Compliance audit report failed:", error);
    }
});


// --- Initial App Load ---
document.addEventListener('DOMContentLoaded', () => {
    populateSourceFilter(); // Populate source filter early
    showSection('dashboard-section'); // Show dashboard by default
});