/**
 * HotspotConfig - WiFi Hotspot Configuration Manager
 * Handles WiFi network scanning, configuration, and connection management
 */

export class HotspotConfig {
    constructor() {
        this.apiBase = '/api/v1/hotspot';
        this.networks = [];
        this.capabilities = { can_scan: false };
    }

    /**
     * Initialize the hotspot configuration UI
     */
    async init() {
        await this.checkCapabilities();
        this.setupEventHandlers();

        // Hide scan button if not supported
        if (!this.capabilities.can_scan) {
            document.getElementById('btn-scan-networks').style.display = 'none';
        }

        await this.loadCurrentConfig();
    }

    /**
     * Check platform capabilities
     */
    async checkCapabilities() {
        try {
            const response = await fetch(`${this.apiBase}/capabilities/`);
            const data = await response.json();
            this.capabilities = data;
        } catch (error) {
            console.error('Failed to check capabilities:', error);
            this.capabilities = { can_scan: false };
        }
    }

    /**
     * Setup event handlers for UI interactions
     */
    setupEventHandlers() {
        document.getElementById('btn-scan-networks').addEventListener('click', () => this.scanNetworks());
        document.getElementById('btn-save-hotspot').addEventListener('click', () => this.saveConfiguration());
        document.getElementById('btn-connect-hotspot').addEventListener('click', () => this.connectToHotspot());

        // Sync manual SSID input with dropdown selection
        document.getElementById('network-select').addEventListener('change', (e) => {
            document.getElementById('manual-ssid-input').value = e.target.value;
        });

        document.getElementById('manual-ssid-input').addEventListener('input', (e) => {
            const select = document.getElementById('network-select');
            const matchingOption = Array.from(select.options).find(opt => opt.value === e.target.value);
            if (matchingOption) {
                select.value = e.target.value;
            } else {
                select.value = '';
            }
        });
    }

    /**
     * Load current hotspot configuration from API
     */
    async loadCurrentConfig() {
        try {
            const response = await fetch(`${this.apiBase}/config/`);
            const data = await response.json();
            this.updateStatusDisplay(data);
        } catch (error) {
            console.error('Failed to load hotspot config:', error);
            this.showMessage('Failed to load configuration', 'error');
        }
    }

    /**
     * Update status display with current config data
     */
    updateStatusDisplay(config) {
        const ssidElement = document.getElementById('hotspot-current-ssid');
        const statusElement = document.getElementById('hotspot-connection-status');
        const connectBtn = document.getElementById('btn-connect-hotspot');

        // Update SSID display
        if (config.ssid) {
            ssidElement.textContent = config.ssid;
            ssidElement.style.color = 'var(--text-color)';
        } else {
            ssidElement.textContent = 'Not configured';
            ssidElement.style.color = 'var(--muted-color)';
        }

        // Update connection status
        const connectionStatus = config.connection_status || {};
        if (connectionStatus.connected) {
            statusElement.textContent = 'Connected';
            statusElement.style.color = 'var(--success-color)';
            connectBtn.style.display = 'none';
        } else if (config.ssid) {
            statusElement.textContent = 'Disconnected';
            statusElement.style.color = 'var(--danger-color)';
            connectBtn.style.display = 'inline-block';
        } else {
            statusElement.textContent = 'Not configured';
            statusElement.style.color = 'var(--muted-color)';
            connectBtn.style.display = 'none';
        }
    }

    /**
     * Scan for available WiFi networks
     */
    async scanNetworks() {
        const btn = document.getElementById('btn-scan-networks');
        const originalText = btn.textContent;

        try {
            btn.disabled = true;
            btn.textContent = 'Scanning...';

            const response = await fetch(`${this.apiBase}/scan/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const data = await response.json();

            if (response.ok) {
                this.networks = data.networks || [];
                this.renderNetworkList();
                this.showMessage(`Found ${this.networks.length} network(s)`, 'success');
            } else {
                this.showMessage(data.error || 'Scan failed', 'error');
            }
        } catch (error) {
            console.error('Network scan failed:', error);
            this.showMessage('Network scan failed', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }

    /**
     * Render network list to dropdown
     */
    renderNetworkList() {
        const select = document.getElementById('network-select');
        const resultsDiv = document.getElementById('network-scan-results');

        // Clear existing options except the first one
        select.innerHTML = '<option value="">-- Select Network --</option>';

        if (this.networks.length === 0) {
            resultsDiv.style.display = 'none';
            return;
        }

        // Add network options with signal strength
        this.networks.forEach(network => {
            const option = document.createElement('option');
            option.value = network.ssid;
            option.textContent = `${network.ssid} (${network.signal}% signal)`;
            select.appendChild(option);
        });

        resultsDiv.style.display = 'block';
    }

    /**
     * Save hotspot configuration
     */
    async saveConfiguration() {
        const btn = document.getElementById('btn-save-hotspot');
        const ssid = document.getElementById('manual-ssid-input').value.trim();
        const password = document.getElementById('hotspot-password-input').value;

        if (!ssid) {
            this.showMessage('Please enter or select an SSID', 'error');
            return;
        }

        if (!password) {
            this.showMessage('Please enter a password', 'error');
            return;
        }

        const originalText = btn.textContent;

        try {
            btn.disabled = true;
            btn.textContent = 'Saving...';

            const response = await fetch(`${this.apiBase}/configure/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ ssid, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage(data.message || 'Configuration saved successfully', 'success');

                // Clear password field for security
                document.getElementById('hotspot-password-input').value = '';

                // Reload config to update UI
                await this.loadCurrentConfig();
            } else {
                this.showMessage(data.error || 'Configuration failed', 'error');
            }
        } catch (error) {
            console.error('Configuration save failed:', error);
            this.showMessage('Failed to save configuration', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }

    /**
     * Connect to configured hotspot
     */
    async connectToHotspot() {
        const btn = document.getElementById('btn-connect-hotspot');
        const originalText = btn.textContent;

        try {
            btn.disabled = true;
            btn.textContent = 'Connecting...';

            const response = await fetch(`${this.apiBase}/connect/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage(data.message || 'Connected successfully', 'success');
                await this.loadCurrentConfig();
            } else {
                this.showMessage(data.error || 'Connection failed', 'error');
            }
        } catch (error) {
            console.error('Connection failed:', error);
            this.showMessage('Connection failed', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }


    /**
     * Display a message to the user
     */
    showMessage(message, type = 'info') {
        // Use existing message system if available, otherwise console
        if (window.meshConfig && window.meshConfig.showMessage) {
            window.meshConfig.showMessage(message, type);
        } else {
            console.log(`[${type}] ${message}`);
        }
    }

    /**
     * Get CSRF token from cookie
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Cleanup when component is destroyed
     */
    destroy() {
        // Cleanup if needed
    }
}
