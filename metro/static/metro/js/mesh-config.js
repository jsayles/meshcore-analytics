/**
 * Mesh Configuration Interface
 * Manages discovery and selection of mesh repeaters
 */

class MeshConfig {
    constructor() {
        this.myRepeaters = [];
        this.discoveredRepeaters = [];
        this.favoriteKeys = new Set();
        this.discovering = false;
        this.currentPage = 1;
        this.pageSize = 50;
        this.searchTerm = '';
    }

    async init() {
        console.log('Initializing Mesh Configuration');
        this.setupEventHandlers();

        // Load my repeaters first, then auto-discover
        await this.loadMyRepeaters();
        await this.discoverNodes();
    }

    setupEventHandlers() {
        // Search input
        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.currentPage = 1;
            this.renderDiscoveredRepeaters();
        });

        // Pagination
        document.getElementById('prev-page').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.renderDiscoveredRepeaters();
            }
        });

        document.getElementById('next-page').addEventListener('click', () => {
            const totalPages = this.getTotalPages();
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.renderDiscoveredRepeaters();
            }
        });
    }

    async loadMyRepeaters() {
        try {
            const response = await fetch('/api/v1/nodes/?role=0'); // 0 = REPEATER
            const data = await response.json();
            this.myRepeaters = data.results?.features || [];
            this.renderMyRepeaters();
        } catch (error) {
            console.error('Failed to load repeaters:', error);
        }
    }

    async discoverNodes() {
        if (this.discovering) {
            console.log('Discovery already in progress');
            return;
        }

        this.discovering = true;

        try {
            const response = await fetch('/api/v1/nodes/discover/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ timeout: 30 })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Discovery failed: ${response.statusText}`);
            }

            const data = await response.json();
            this.discoveredRepeaters = data.nodes;

            console.log(`API returned ${data.nodes.length} nodes:`, data.nodes);
            console.log(`Discovered ${this.discoveredRepeaters.length} new repeaters`);

            this.currentPage = 1;
            this.renderDiscoveredRepeaters();

        } catch (error) {
            console.error('Discovery error:', error);
            alert(`Discovery failed: ${error.message}`);
        } finally {
            this.discovering = false;
        }
    }

    renderMyRepeaters() {
        const container = document.getElementById('my-repeaters-list');

        if (this.myRepeaters.length === 0) {
            container.innerHTML = '<div class="empty-state">No repeaters selected. Add some from the list below.</div>';
            return;
        }

        const html = this.myRepeaters.map(repeater => {
            const props = repeater.properties;
            const lastSeen = new Date(props.last_seen).toLocaleString();

            return `
                <div class="repeater-item" data-id="${repeater.id}">
                    <div class="name">${props.name || 'Unnamed'}</div>
                    <div class="mesh-id">${props.mesh_identity}</div>
                    <div class="last-seen">${lastSeen}</div>
                    <button class="btn btn-danger btn-sm remove-btn" onclick="window.meshConfig.removeRepeater(${repeater.id})">
                        Remove
                    </button>
                </div>
            `;
        }).join('');

        container.innerHTML = html;
    }

    renderDiscoveredRepeaters() {
        const tbody = document.getElementById('discovered-repeaters-body');

        // Filter by search term only (API already filtered out database nodes)
        let filtered = this.discoveredRepeaters.filter(node => {
            if (this.searchTerm) {
                const name = (node.name || node.mesh_identity).toLowerCase();
                const meshId = node.mesh_identity.toLowerCase();
                return name.includes(this.searchTerm) || meshId.includes(this.searchTerm);
            }
            return true;
        });

        // Sort: favorites first, then by SNR
        filtered.sort((a, b) => {
            const aFav = this.favoriteKeys.has(a.mesh_identity);
            const bFav = this.favoriteKeys.has(b.mesh_identity);
            if (aFav && !bFav) return -1;
            if (!aFav && bFav) return 1;
            return b.snr - a.snr;
        });

        // Paginate
        const start = (this.currentPage - 1) * this.pageSize;
        const end = start + this.pageSize;
        const page = filtered.slice(start, end);

        // Render rows
        if (page.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No repeaters found</td></tr>';
        } else {
            const html = page.map(node => {
                const isFavorite = this.favoriteKeys.has(node.mesh_identity);
                const starClass = isFavorite ? 'favorited' : '';

                return `
                    <tr>
                        <td>
                            <span class="star-icon ${starClass}" onclick="window.meshConfig.toggleFavorite('${node.mesh_identity}')">
                                ${isFavorite ? '★' : '☆'}
                            </span>
                        </td>
                        <td class="name-cell">${node.name || node.mesh_identity.substr(0, 8)}</td>
                        <td class="mesh-id-cell">${node.mesh_identity}</td>
                        <td>${node.snr.toFixed(1)} dB</td>
                        <td>${node.rssi} dBm</td>
                        <td>${node.path_len}</td>
                        <td>
                            <button class="btn btn-primary btn-sm" onclick='window.meshConfig.addRepeater(${JSON.stringify(node)})'>Add</button>
                        </td>
                    </tr>
                `;
            }).join('');
            tbody.innerHTML = html;
        }

        // Update pagination
        this.updatePagination(filtered.length);
    }

    updatePagination(totalCount) {
        const totalPages = Math.ceil(totalCount / this.pageSize);
        document.getElementById('page-info').textContent = `Page ${this.currentPage} of ${totalPages} (${totalCount} repeaters)`;

        document.getElementById('prev-page').disabled = this.currentPage === 1;
        document.getElementById('next-page').disabled = this.currentPage >= totalPages;
    }

    getTotalPages() {
        let filtered = this.discoveredRepeaters.filter(node => {
            if (!this.searchTerm) return true;
            const name = (node.name || node.mesh_identity).toLowerCase();
            const meshId = node.mesh_identity.toLowerCase();
            return name.includes(this.searchTerm) || meshId.includes(this.searchTerm);
        });
        return Math.ceil(filtered.length / this.pageSize);
    }

    toggleFavorite(meshIdentity) {
        if (this.favoriteKeys.has(meshIdentity)) {
            this.favoriteKeys.delete(meshIdentity);
        } else {
            this.favoriteKeys.add(meshIdentity);
        }
        this.renderDiscoveredRepeaters();
    }

    async addRepeater(nodeData) {
        try {
            const response = await fetch('/api/v1/nodes/add_node/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(nodeData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to add repeater');
            }

            console.log('Repeater added successfully');

            // Reload my repeaters and re-render discovered list
            await this.loadMyRepeaters();
            this.renderDiscoveredRepeaters();

        } catch (error) {
            console.error('Error adding repeater:', error);
            alert(`Failed to add repeater: ${error.message}`);
        }
    }

    async removeRepeater(nodeId) {
        if (!confirm('Remove this repeater?')) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/nodes/${nodeId}/`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                throw new Error('Failed to remove repeater');
            }

            console.log('Repeater removed successfully');

            // Reload my repeaters and re-render discovered list
            await this.loadMyRepeaters();
            this.renderDiscoveredRepeaters();

        } catch (error) {
            console.error('Error removing repeater:', error);
            alert(`Failed to remove repeater: ${error.message}`);
        }
    }
}

export { MeshConfig };
