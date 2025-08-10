// Map functionality for SafePath application
class SafePathMap {
    constructor() {
        this.map = null;
        this.userLocation = null;
        this.crimeMarkers = [];
        this.routeLayer = null;
        this.currentLocationMarker = null;
        
        this.initializeMap();
        this.setupEventListeners();
    }
    
    initializeMap() {
        // Initialize Leaflet map centered on India
        this.map = L.map('crimeMap').setView([20.5937, 78.9629], 5);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);
        
        // Add click event for area information
        this.map.on('click', (e) => {
            this.showAreaInfo(e.latlng.lat, e.latlng.lng);
        });
        
        // Try to get user's current location
        this.getCurrentLocation();
    }
    
    setupEventListeners() {
        // Map controls
        document.getElementById('refreshMap').addEventListener('click', () => {
            this.loadCrimeData();
        });
        
        document.getElementById('radiusFilter').addEventListener('change', () => {
            this.loadCrimeData();
        });
        
        document.getElementById('limitFilter').addEventListener('change', () => {
            this.loadCrimeData();
        });
    }
    
    getCurrentLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    
                    this.userLocation = { lat, lng };
                    this.updateUserLocationMarker(lat, lng);
                    this.map.setView([lat, lng], 12);
                    this.loadCrimeData();
                },
                (error) => {
                    console.error('Geolocation error:', error);
                    this.showError('Unable to get your location. Showing default view.');
                    this.loadCrimeData();
                }
            );
        } else {
            this.showError('Geolocation is not supported by this browser.');
            this.loadCrimeData();
        }
    }
    
    updateUserLocationMarker(lat, lng) {
        if (this.currentLocationMarker) {
            this.map.removeLayer(this.currentLocationMarker);
        }
        
        this.currentLocationMarker = L.marker([lat, lng], {
            icon: L.divIcon({
                className: 'current-location-marker',
                html: '<div style="background-color: #007bff; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px rgba(0,123,255,0.5);"></div>',
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            })
        }).addTo(this.map);
        
        this.currentLocationMarker.bindPopup(
            '<strong>Your Current Location</strong><br>' +
            `Lat: ${lat.toFixed(6)}<br>` +
            `Lng: ${lng.toFixed(6)}`
        );
    }
    
    loadCrimeData() {
        const radius = document.getElementById('radiusFilter').value;
        const limit = document.getElementById('limitFilter').value;
        
        let url = '/api/crime-data?limit=' + limit;
        
        if (this.userLocation) {
            url += `&lat=${this.userLocation.lat}&lng=${this.userLocation.lng}&radius=${radius}`;
        }
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.displayCrimeMarkers(data.crimes);
                } else {
                    this.showError('Failed to load crime data: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error loading crime data:', error);
                this.showError('Network error while loading crime data');
            });
    }
    
    displayCrimeMarkers(crimes) {
        // Clear existing markers
        this.crimeMarkers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.crimeMarkers = [];
        
        // Add new markers
        crimes.forEach(crime => {
            const marker = this.createCrimeMarker(crime);
            marker.addTo(this.map);
            this.crimeMarkers.push(marker);
        });
        
        console.log(`Displayed ${crimes.length} crime markers`);
    }
    
    createCrimeMarker(crime) {
        // Determine marker color based on severity
        let color = '#28a745'; // Low severity - green
        if (crime.severity >= 4) {
            color = '#dc3545'; // High severity - red
        } else if (crime.severity >= 2) {
            color = '#ffc107'; // Medium severity - yellow
        }
        
        const marker = L.circleMarker([crime.latitude, crime.longitude], {
            radius: 4 + crime.severity,
            fillColor: color,
            color: '#fff',
            weight: 1,
            opacity: 0.8,
            fillOpacity: 0.6
        });
        
        // Create popup content
        const popupContent = `
            <div style="color: #fff;">
                <strong>${crime.crime_type}</strong><br>
                <span class="crime-badge crime-${crime.crime_type.toLowerCase().replace(' ', '-')}">
                    Severity: ${crime.severity}/5
                </span><br>
                <small>
                    <i class="fas fa-calendar me-1"></i>${new Date(crime.timestamp).toLocaleString()}<br>
                    <i class="fas fa-map-marker-alt me-1"></i>${crime.area_name || 'Unknown Area'}<br>
                    <i class="fas fa-info-circle me-1"></i>${crime.description || 'No description available'}
                </small>
            </div>
        `;
        
        marker.bindPopup(popupContent);
        
        return marker;
    }
    
    showAreaInfo(lat, lng) {
        const areaInfoDiv = document.getElementById('areaInfo');
        areaInfoDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-primary"></div> Loading area information...';
        
        // Get crime risk for the clicked location
        fetch('/api/current-location-risk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                latitude: lat,
                longitude: lng
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const riskClass = data.risk_level.toLowerCase();
                const crimeStats = data.crime_stats;
                
                areaInfoDiv.innerHTML = `
                    <div class="area-info-content">
                        <h6 class="text-white mb-3">
                            <i class="fas fa-map-marker-alt me-2"></i>
                            Location: ${lat.toFixed(4)}, ${lng.toFixed(4)}
                        </h6>
                        
                        <div class="mb-3">
                            <label class="text-muted">Risk Level:</label>
                            <div class="risk-${riskClass} d-inline-block">
                                ${data.risk_level} (${data.risk_score}/10)
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="text-muted">Area Statistics (1km radius):</label>
                            <ul class="list-unstyled mt-2">
                                <li class="text-white">
                                    <i class="fas fa-exclamation-triangle me-2 text-warning"></i>
                                    Total Crimes: ${crimeStats.total_crimes}
                                </li>
                                <li class="text-white">
                                    <i class="fas fa-clock me-2 text-info"></i>
                                    Recent (30d): ${crimeStats.recent_crimes}
                                </li>
                                <li class="text-white">
                                    <i class="fas fa-chart-line me-2 text-secondary"></i>
                                    Avg Severity: ${crimeStats.avg_severity}/5
                                </li>
                            </ul>
                        </div>
                        
                        ${crimeStats.total_crimes > 0 ? `
                        <div class="mb-3">
                            <label class="text-muted">Common Crime Types:</label>
                            <div class="mt-2">
                                ${Object.entries(crimeStats.crime_types)
                                    .sort((a, b) => b[1] - a[1])
                                    .slice(0, 3)
                                    .map(([type, count]) => `
                                        <span class="crime-badge crime-${type.toLowerCase().replace(' ', '-')}">
                                            ${type}: ${count}
                                        </span>
                                    `).join('')}
                            </div>
                        </div>
                        ` : ''}
                        
                        <button class="btn btn-sm btn-primary w-100" onclick="safePath.useAsRoutePoint(${lat}, ${lng})">
                            <i class="fas fa-route me-1"></i>Use as Route Point
                        </button>
                    </div>
                `;
            } else {
                areaInfoDiv.innerHTML = `
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load area information
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error getting area info:', error);
            areaInfoDiv.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Network error loading area information
                </div>
            `;
        });
    }
    
    displayRoute(routeData) {
        // Clear existing route
        if (this.routeLayer) {
            this.map.removeLayer(this.routeLayer);
        }
        
        // Create route line
        const routePoints = routeData.route_points.map(point => [point.lat, point.lng]);
        
        this.routeLayer = L.polyline(routePoints, {
            color: this.getRouteColor(routeData.risk_score),
            weight: 4,
            opacity: 0.8
        }).addTo(this.map);
        
        // Add markers for start and end points
        const startMarker = L.marker([routePoints[0][0], routePoints[0][1]], {
            icon: L.divIcon({
                className: 'route-marker',
                html: '<div style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; font-weight: bold;">START</div>',
                iconSize: [40, 20],
                iconAnchor: [20, 10]
            })
        }).addTo(this.map);
        
        const endMarker = L.marker([routePoints[routePoints.length-1][0], routePoints[routePoints.length-1][1]], {
            icon: L.divIcon({
                className: 'route-marker',
                html: '<div style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px; font-weight: bold;">END</div>',
                iconSize: [30, 20],
                iconAnchor: [15, 10]
            })
        }).addTo(this.map);
        
        // Fit map to route bounds
        this.map.fitBounds(this.routeLayer.getBounds(), { padding: [20, 20] });
        
        // Add route info popup
        const midPoint = routePoints[Math.floor(routePoints.length / 2)];
        L.popup()
            .setLatLng(midPoint)
            .setContent(`
                <div style="color: #fff;">
                    <strong>Safe Route</strong><br>
                    Risk Score: ${routeData.risk_score}/10<br>
                    Distance: ${routeData.distance_km} km
                </div>
            `)
            .openOn(this.map);
    }
    
    getRouteColor(riskScore) {
        if (riskScore < 3) return '#28a745'; // Low risk - green
        if (riskScore < 6) return '#ffc107'; // Medium risk - yellow
        return '#dc3545'; // High risk - red
    }
    
    useAsRoutePoint(lat, lng) {
        // Fill the route form with clicked coordinates
        const activeInput = document.querySelector('#routeForm input:focus');
        
        if (activeInput && activeInput.id.includes('Lat')) {
            activeInput.value = lat.toFixed(6);
            // Find corresponding longitude input
            const lngInput = document.getElementById(activeInput.id.replace('Lat', 'Lng'));
            if (lngInput) {
                lngInput.value = lng.toFixed(6);
            }
        } else {
            // Default to start location
            document.getElementById('startLat').value = lat.toFixed(6);
            document.getElementById('startLng').value = lng.toFixed(6);
        }
        
        this.showSuccess('Coordinates added to route form');
    }
    
    showError(message) {
        console.error(message);
        // You could also show a toast notification here
    }
    
    showSuccess(message) {
        console.log(message);
        // You could also show a toast notification here
    }
}

// Global map instance
let safePathMap;

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    safePathMap = new SafePathMap();
    
    // Make map instance globally available
    window.safePath = safePathMap;
});
