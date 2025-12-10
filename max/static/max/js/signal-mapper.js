/**
 * Signal Mapper Main Application
 *
 * Coordinates WebSocket connection, measurement collection, and heatmap rendering.
 */

import { WebSocketConnection } from './ws-connection.js';
import { MeasurementCollector } from './measurement-collector.js';
import { HeatmapRenderer } from './heatmap-renderer.js';

class SignalMapper {
    constructor(sessionId) {
        this.map = null;
        this.wsConnection = new WebSocketConnection();
        this.collector = null;
        this.heatmapRenderer = null;
        this.sessionId = sessionId;
        this.targetNodeId = null;
        this.repeaters = [];
        this.currentStep = 1;
        this.locationShared = false;
    }

    /**
     * Initialize the application
     */
    async init() {
        // Initialize Leaflet map - centered on Vancouver, BC
        this.map = L.map('map').setView([49.2827, -123.1207], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(this.map);

        // Initialize heatmap renderer
        this.heatmapRenderer = new HeatmapRenderer(this.map);

        // Set up event handlers
        this.setupEventHandlers();

        // Check for pre-selected node from query parameter
        const urlParams = new URLSearchParams(window.location.search);
        const preSelectedNodeId = urlParams.get('node');
        if (preSelectedNodeId) {
            this.targetNodeId = parseInt(preSelectedNodeId);
        }

        // Load repeaters for dropdown
        await this.loadRepeaters();

        // Initialize step states
        this.initializeSteps();

        // Request location permission
        this.requestLocation();
    }

    /**
     * Initialize step states based on current progress
     */
    initializeSteps() {
        // Hide collection section initially - only show when step 3 is complete
        document.getElementById('collection-section').style.display = 'none';

        // Step 1: Repeater selection
        if (this.targetNodeId) {
            // Show selected repeater name in the status
            // ID is at feature.id, not feature.properties.id
            const repeater = this.repeaters.find(r => Number(r.id) === Number(this.targetNodeId));

            const repeaterName = repeater ? (repeater.properties.name || repeater.properties.mesh_identity) : 'Selected';

            this.completeStep(1, repeaterName);
            this.currentStep = 2;

            // Hide the dropdown content completely
            document.getElementById('content-repeater').style.display = 'none';
            document.getElementById('content-repeater-selected').style.display = 'none';
        } else {
            this.setActiveStep(1);
        }

        this.updateStepDisplay();
    }

    /**
     * Set a step as active
     */
    setActiveStep(stepNumber) {
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active');
        });

        const stepElement = document.querySelector(`[data-step="${stepNumber}"]`);
        if (stepElement) {
            stepElement.classList.add('active');
        }

        this.currentStep = stepNumber;
    }

    /**
     * Mark a step as completed
     */
    completeStep(stepNumber, statusText) {
        const stepElement = document.querySelector(`[data-step="${stepNumber}"]`);
        const statusElement = document.getElementById(`status-${this.getStepName(stepNumber)}`);

        if (stepElement) {
            stepElement.classList.add('completed');
            stepElement.classList.remove('active');
        }

        if (statusElement) {
            statusElement.textContent = statusText;
        }
    }

    /**
     * Get step name from number
     */
    getStepName(stepNumber) {
        const names = ['', 'repeater', 'location', 'radio', 'collect'];
        return names[stepNumber];
    }

    /**
     * Update step display
     */
    updateStepDisplay() {
        this.setActiveStep(this.currentStep);
    }

    /**
     * Request user location
     */
    requestLocation() {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.locationShared = true;
                    this.completeStep(2, 'Enabled');
                    this.map.setView(
                        [position.coords.latitude, position.coords.longitude],
                        15
                    );

                    if (this.currentStep === 2) {
                        this.currentStep = 3;
                        this.updateStepDisplay();
                    }
                },
                (error) => {
                    console.warn('Could not get user location:', error);
                    document.getElementById('status-location').textContent = 'Permission needed';
                }
            );
        } else {
            document.getElementById('status-location').textContent = 'Not supported';
        }
    }

    /**
     * Setup UI event handlers
     */
    setupEventHandlers() {
        // Pi Connection
        document.getElementById('btn-connect').addEventListener('click', () => this.connectToPi());

        // Repeater selection - redirect to URL with node parameter
        document.getElementById('repeater-select').addEventListener('change', (e) => {
            const nodeId = e.target.value;
            if (nodeId && nodeId !== 'undefined' && nodeId !== '') {
                // Redirect to same page with node parameter
                window.location.href = `/mapper/?node=${nodeId}`;
            }
        });

        // Collection mode toggle
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                const mode = e.target.value;
                const continuousOptions = document.getElementById('continuous-options');
                const btnCollect = document.getElementById('btn-collect');
                const btnStart = document.getElementById('btn-start-continuous');
                const btnStop = document.getElementById('btn-stop-continuous');

                if (mode === 'continuous') {
                    continuousOptions.style.display = 'block';
                    btnCollect.style.display = 'none';
                    btnStart.style.display = 'block';
                    btnStop.style.display = 'none';
                } else {
                    continuousOptions.style.display = 'none';
                    btnCollect.style.display = 'block';
                    btnStart.style.display = 'none';
                    btnStop.style.display = 'none';
                }
            });
        });

        // Manual collection
        document.getElementById('btn-collect').addEventListener('click', () => this.collectManual());

        // Continuous collection
        document.getElementById('btn-start-continuous').addEventListener('click', () => this.startContinuous());
        document.getElementById('btn-stop-continuous').addEventListener('click', () => this.stopContinuous());
    }

    /**
     * Connect to Pi via WebSocket
     */
    async connectToPi() {
        const btn = document.getElementById('btn-connect');
        const status = document.getElementById('status-radio');

        try {
            btn.disabled = true;
            btn.textContent = 'Connecting...';
            status.textContent = 'Connecting...';

            // Connect via WebSocket
            await this.wsConnection.connect();

            // Remove the button and hide the step content
            document.getElementById('content-radio').style.display = 'none';
            this.showMessage('Connected! GPS streaming started.', 'success');

            // Mark step complete
            this.completeStep(3, 'Connected');

            // Remove active state from all steps since setup is complete
            document.querySelectorAll('.step').forEach(step => {
                step.classList.remove('active');
            });

            // Show collection section now that all steps are complete
            document.getElementById('collection-section').style.display = 'block';

            // Load existing heatmap data for this repeater
            await this.loadAndDisplayHeatmap();

        } catch (error) {
            console.error('Connection failed:', error);
            status.textContent = 'Failed';
            btn.textContent = 'Retry Connection';
            btn.disabled = false;

            this.showMessage(`Connection failed: ${error.message}`, 'error');
        }
    }

    /**
     * Load available repeaters from API
     */
    async loadRepeaters() {
        try {
            const response = await fetch('/api/v1/nodes/?role=0&is_active=true');
            const data = await response.json();

            // API returns paginated results with structure: { count, results: { features: [...] } }
            const features = data.results?.features || data.features;

            if (features && features.length > 0) {
                this.repeaters = features;
                this.populateRepeaterDropdown();
            } else {
                this.showMessage('No active repeaters found in database. Add some via admin first.', 'warning');
            }

        } catch (error) {
            console.error('Failed to load repeaters:', error);
            this.showMessage('Failed to load repeaters. Check console for details.', 'error');
        }
    }

    /**
     * Populate repeater dropdown
     */
    populateRepeaterDropdown() {
        const select = document.getElementById('repeater-select');
        select.innerHTML = '<option value="">-- Select Repeater --</option>';

        this.repeaters.forEach(feature => {
            const props = feature.properties;
            const option = document.createElement('option');
            // ID is at feature.id, not feature.properties.id
            option.value = String(feature.id);
            option.textContent = props.name || props.mesh_identity;

            // Pre-select if this is the target node
            if (this.targetNodeId && feature.id === this.targetNodeId) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }

    /**
     * Collect single manual measurement
     */
    async collectManual() {
        if (!this.targetNodeId) {
            this.showMessage('Please select a target repeater first', 'warning');
            return;
        }

        const btn = document.getElementById('btn-collect');

        try {
            btn.disabled = true;
            btn.textContent = 'Collecting...';

            if (!this.collector) {
                this.collector = new MeasurementCollector(
                    this.wsConnection,
                    this.targetNodeId,
                    this.sessionId
                );
                this.collector.onMeasurement = (data) => this.updateSessionInfo(data);
            }

            await this.collector.collectOnce();
            this.showMessage('Measurement collected successfully!', 'success');

        } catch (error) {
            console.error('Collection failed:', error);
            this.showMessage(`Collection failed: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Collect Now';
        }
    }

    /**
     * Start continuous collection
     */
    startContinuous() {
        if (!this.targetNodeId) {
            this.showMessage('Please select a target repeater first', 'warning');
            return;
        }

        const interval = parseInt(document.getElementById('interval').value);
        const btnStart = document.getElementById('btn-start-continuous');
        const btnStop = document.getElementById('btn-stop-continuous');

        if (!this.collector) {
            this.collector = new MeasurementCollector(
                this.wsConnection,
                this.targetNodeId,
                this.sessionId
            );
            this.collector.onMeasurement = (data) => this.updateSessionInfo(data);
        }

        this.collector.setInterval(interval);
        this.collector.startContinuous();

        btnStart.style.display = 'none';
        btnStop.style.display = 'block';

        this.showMessage(`Continuous collection started (every ${interval}s)`, 'success');
    }

    /**
     * Stop continuous collection
     */
    stopContinuous() {
        if (this.collector) {
            this.collector.stop();
        }

        const btnStart = document.getElementById('btn-start-continuous');
        const btnStop = document.getElementById('btn-stop-continuous');

        btnStart.style.display = 'block';
        btnStop.style.display = 'none';

        this.showMessage('Continuous collection stopped', 'info');
    }

    /**
     * Update session info display
     */
    updateSessionInfo(data) {
        document.getElementById('measurement-count').textContent = data.count;
        document.getElementById('last-rssi').textContent = data.rssi;
        document.getElementById('last-snr').textContent = data.snr;

        // Auto-refresh heatmap with new data
        this.loadAndDisplayHeatmap();
    }

    /**
     * Load and display heatmap automatically
     */
    async loadAndDisplayHeatmap() {
        if (!this.targetNodeId) {
            return;
        }

        try {
            await this.heatmapRenderer.loadData(this.targetNodeId);
            this.heatmapRenderer.render();

            const count = this.heatmapRenderer.measurements.length;
            console.log(`Heatmap updated with ${count} measurements`);

        } catch (error) {
            console.error('Failed to load heatmap:', error);
        }
    }

    /**
     * Show status message
     */
    showMessage(text, type = 'info') {
        const container = document.getElementById('status-messages');
        const message = document.createElement('div');
        message.className = `message ${type}`;
        message.textContent = text;

        container.appendChild(message);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    }

}

// Export SignalMapper
export { SignalMapper };
