// Map functionality for SafePath application
class SafePathMap {
    constructor() {
        this.map = null;
        this.userLocation = null;
        this.crimeMarkers = [];
        this.safePlacesMarkers = [];
        this.routeLayer = null;
        this.currentLocationMarker = null;
        this.safePlacesMap = null;
        this.control=null;
        this.startMarker = null;
        this.endMarker = null;
        
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

        // Safe places event listeners
        document.getElementById('findSafePlacesBtn').addEventListener('click', () => {
            this.findSafePlacesNearMe();
        });

        document.getElementById('showAllSafePlacesBtn').addEventListener('click', () => {
            this.showAllSafePlaces();
        });

        document.getElementById('safeTypeFilter').addEventListener('change', () => {
            this.loadSafePlaces();
        });

        document.getElementById('safeRadiusFilter').addEventListener('change', () => {
            this.loadSafePlaces();
        });

        document.getElementById('findRouteBtn').addEventListener('click',()=>{
            this.createroute();
        });

        // SOS functionality (if user is authenticated)
        const quickSOSBtn = document.getElementById('quickSOSBtn');
        if (quickSOSBtn) {
            quickSOSBtn.addEventListener('click', () => {
                this.sendQuickSOS();
            });
        }
    }
    async  geocode(query){
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`;
        const res = await fetch(url);
        const data = await res.json();
        if(!data || data.length===0) throw new Error('No results');
        return L.latLng(parseFloat(data[0].lat), parseFloat(data[0].lon));
    }
    async createroute(){
        const source=document.getElementById('sourceInput').value.trim();
        const dest=document.getElementById('destinationInput').value.trim();
        if(!source || !dest) return alert('Enter both source and destination');
        console.log(source,dest)

        const srcLatLng = await this.geocode(source);
        const destLatLng = await this.geocode(dest);
        console.log(srcLatLng,destLatLng)
        

    const res = await fetch('/get_routes', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({srcLatLng, destLatLng})
    });
    const routes = await res.json();
    console.log(routes)
    // Clear previous routes
    this.map.eachLayer((layer) => { if(layer instanceof L.Polyline) this.map.removeLayer(layer); });

    // Find min and max risk
    const risks = routes.map(r => r.risk);
    const minRisk = Math.min(...risks);
    const maxRisk = Math.max(...risks);

    // Function to map risk to color
    const getColor = (risk) => {
        if (maxRisk === minRisk) return 'yellow'; // all same risk
        const ratio = (risk - minRisk) / (maxRisk - minRisk);
        if (ratio < 0.33) return 'green';
        else if (ratio < 0.66) return 'yellow';
        else return 'red';
    };

       // Remove old markers
    if (this.startMarker) {
        this.map.removeLayer(this.startMarker);
    }
    if (this.endMarker) {
        this.map.removeLayer(this.endMarker);
    }
     this.startMarker = L.marker([srcLatLng.lat, srcLatLng.lng])
        .bindPopup("Start")
        .addTo(this.map);

    // Add end marker
    this.endMarker = L.marker([destLatLng.lat, destLatLng.lng])
        .bindPopup("End")
        .addTo(this.map);

    routes.forEach((route) => {
        const color = getColor(route.risk);
        L.geoJSON(route.geometry, {color, weight:3}).addTo(this.map);
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
                    this.control=L.Routing.control({
                    waypoints: [srcLatLng, destLatLng],
                    router: L.Routing.osrmv1({
                        serviceUrl: 'https://router.project-osrm.org/route/v1',
                        profile: 'driving', // can be driving, cycling, walking
                        alternatives: true   // enable multiple routes
                    }),
                    showAlternatives: true,
                    altLineOptions: {
                        styles: [
                        { color: 'black', opacity: 0.15, weight: 9 },
                        { color: 'white', opacity: 0.8, weight: 6 },
                        { color: 'blue', opacity: 0.5, weight: 2 }
                        ]
                    },
                    routeWhileDragging: true,
                    createMarker: (i, wp) => L.marker(wp.latLng).bindPopup(i === 0 ? 'Source' : 'Destination')
                    }).addTo(this.map);
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

    // Safe Places functionality
    initializeSafePlacesMap() {
    if (this.safePlacesMap) {
        return; // already created
    }

    const container = document.getElementById('safePlacesMap');
    if (!container) {
        console.error("Safe Places container not found");
        return;
    }

    this.safePlacesMap = L.map('safePlacesMap').setView([20.5937, 78.9629], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(this.safePlacesMap);
}


    updateSafePlacesMapPlaceholder() {
        const mapDiv = document.getElementById('safePlacesMap');
        if (!this.safePlacesMap || !mapDiv) return;

        mapDiv.innerHTML = `
            <div class="d-flex align-items-center justify-content-center h-100">
                <div class="text-center text-muted">
                    <i class="fas fa-map fa-2x mb-2"></i>
                    <p>Click "Find Safe Places Near Me" to see locations on map</p>
                </div>
            </div>
        `;
    }

    findSafePlacesNearMe() {
    if (!navigator.geolocation) {
        this.showError('Geolocation is not supported by this browser');
        return;
    }

    // ✅ Initialize Safe Places map if needed
    if (!this.safePlacesMap) {
        this.initializeSafePlacesMap();
    }

    const btn = document.getElementById('findSafePlacesBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Finding Safe Places...';
    btn.disabled = true;

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            this.userLocation = { lat, lng };
            this.loadSafePlaces(lat, lng);
            
            btn.innerHTML = originalText;
            btn.disabled = false;
        },
        (error) => {
            this.showError('Unable to get your location');
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    );
}


    showAllSafePlaces() {
        this.loadSafePlaces();
    }

    async loadSafePlaces(lat = null, lng = null) {
        try {
            const params = new URLSearchParams();
            
            if (lat && lng) {
                params.append('lat', lat);
                params.append('lng', lng);
            }

            const type = document.getElementById('safeTypeFilter').value;
            if (type) params.append('type', type);

            const radius = document.getElementById('safeRadiusFilter').value;
            if (radius) params.append('radius', radius);

            params.append('limit', '50');

            const response = await fetch(`/api/safe-places?${params.toString()}`);
            const data = await response.json();

            if (data.success) {
                this.displaySafePlaces(data.places, lat, lng);
                document.getElementById('safePlacesCount').textContent = `${data.places.length} found`;
            } else {
                this.showError('Failed to load safe places: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading safe places:', error);
            this.showError('Network error loading safe places');
        }
    }

    displaySafePlaces(places, userLat = null, userLng = null) {
    if (!this.safePlacesMap) {
        console.error("Safe Places map not initialized");
        return;
    }

    // Clear old markers
    this.safePlacesMarkers.forEach(marker => this.safePlacesMap.removeLayer(marker));
    this.safePlacesMarkers = [];

    // Add user marker if available
    if (userLat && userLng) {
        const userMarker = L.marker([userLat, userLng], {
            icon: L.divIcon({
                className: 'user-location-marker',
                html: '<div style="background-color: #007bff; color: white; padding: 4px; border-radius: 50%; font-size: 12px; text-align: center; width: 20px; height: 20px; line-height: 12px;"><i class="fas fa-user"></i></div>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            })
        }).addTo(this.safePlacesMap);

        userMarker.bindPopup('Your Location');
        this.safePlacesMarkers.push(userMarker);
    }

    // Add safe places
    places.forEach(place => {
        const icon = this.getSafePlaceIcon(place.place_type);
        const marker = L.marker([place.latitude, place.longitude], {
            icon: L.divIcon({
                className: 'safe-place-marker',
                html: `<div style="background-color: ${icon.color}; color: white; padding: 4px; border-radius: 50%; font-size: 12px; text-align: center; width: 24px; height: 24px; line-height: 16px;">${icon.icon}</div>`,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            })
        }).addTo(this.safePlacesMap);

        marker.bindPopup(`
            <div style="color: #333;">
                <strong>${place.name}</strong><br>
                <small>${place.place_type.replace('_', ' ').toUpperCase()}</small><br>
                ${place.address}<br>
                ${place.phone ? `<i class="fas fa-phone"></i> ${place.phone}<br>` : ''}
                ${place.hours ? `<i class="fas fa-clock"></i> ${place.hours}<br>` : ''}
                ${place.verified ? '<span class="badge bg-success">Verified</span>' : ''}
            </div>
        `);

        this.safePlacesMarkers.push(marker);
    });

    // Fit bounds
    if (this.safePlacesMarkers.length > 0) {
        const group = new L.featureGroup(this.safePlacesMarkers);
        this.safePlacesMap.fitBounds(group.getBounds().pad(0.1));
    }

    // Update sidebar/list
    this.updateSafePlacesList(places);
}


    getSafePlaceIcon(placeType) {
        const icons = {
            'police_station': { icon: '🛡️', color: '#007bff' },
            'hospital': { icon: '🏥', color: '#dc3545' },
            'fire_station': { icon: '🚒', color: '#ff6b35' },
            'government_office': { icon: '🏛️', color: '#6f42c1' },
            'bank': { icon: '🏦', color: '#198754' },
            'school': { icon: '🏫', color: '#fd7e14' }
        };

        return icons[placeType] || { icon: '📍', color: '#6c757d' };
    }

    updateSafePlacesList(places) {
        const listContainer = document.getElementById('safePlacesList');
        
        if (places.length === 0) {
            listContainer.innerHTML = '<p class="text-muted text-center">No safe places found in this area.</p>';
            return;
        }

        const listHTML = places.map(place => `
            <div class="card bg-secondary mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="text-white mb-1">${place.name}</h6>
                            <span class="badge bg-primary me-2">${place.place_type.replace('_', ' ').toUpperCase()}</span>
                            ${place.verified ? '<span class="badge bg-success">Verified</span>' : ''}
                        </div>
                        <button class="btn btn-sm btn-outline-primary" onclick="safePathMap.focusOnPlace(${place.latitude}, ${place.longitude})">
                            <i class="fas fa-map-marker-alt"></i>
                        </button>
                    </div>
                    <p class="text-muted small mb-1 mt-2">${place.address}</p>
                    ${place.phone ? `<p class="text-muted small mb-1"><i class="fas fa-phone me-1"></i>${place.phone}</p>` : ''}
                    ${place.hours ? `<p class="text-muted small mb-0"><i class="fas fa-clock me-1"></i>${place.hours}</p>` : ''}
                </div>
            </div>
        `).join('');

        listContainer.innerHTML = listHTML;
    }

    focusOnPlace(lat, lng) {
        if (this.safePlacesMap) {
            this.safePlacesMap.setView([lat, lng], 16);
        }
    }

    async sendQuickSOS() {
        if (!navigator.geolocation) {
            this.showError('Geolocation is not supported by this browser');
            return;
        }

        const btn = document.getElementById('quickSOSBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending SOS...';
        btn.disabled = true;

        navigator.geolocation.getCurrentPosition(async (position) => {
            try {
                const response = await fetch('/api/sos/alert', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        message: 'Quick SOS alert from SafePath dashboard'
                    })
                });

                const data = await response.json();

                if (data.success) {
                    alert('SOS alert sent successfully! Emergency contacts have been notified.');
                } else {
                    alert('Failed to send SOS alert: ' + data.error);
                }
            } catch (error) {
                alert('Network error occurred while sending SOS alert');
            }

            btn.innerHTML = originalText;
            btn.disabled = false;
        }, (error) => {
            alert('Unable to get your location for SOS alert');
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    }
}

// Global map instance
let safePathMap;

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    safePathMap = new SafePathMap();
    
    // Make map instance globally available
    window.safePathMap = safePathMap;
    
    // Initialize safe places map after a short delay
    setTimeout(() => {
        if (safePathMap && document.getElementById('safePlacesMap')) {
            safePathMap.initializeSafePlacesMap();
        }
    }, 100);
    
    // Check authentication status and show/hide relevant elements
    checkAuthStatus();
});

// Authentication status check
async function checkAuthStatus() {
    const authLinks = document.getElementById('authLinks');
    const unauthLinks = document.getElementById('unauthLinks');
    const unauthLinksRegister = document.getElementById('unauthLinksRegister');
    const usernameDisplay = document.getElementById('usernameDisplay');

    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();

        if (data.authenticated) {
            if (authLinks) authLinks.classList.remove('d-none');
            if (unauthLinks) unauthLinks.classList.add('d-none');
            if (unauthLinksRegister) unauthLinksRegister.classList.add('d-none');
            if (usernameDisplay) usernameDisplay.textContent = data.user.username;
        } else {
            if (authLinks) authLinks.classList.add('d-none');
            if (unauthLinks) unauthLinks.classList.remove('d-none');
            if (unauthLinksRegister) unauthLinksRegister.classList.remove('d-none');
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
    }
}
