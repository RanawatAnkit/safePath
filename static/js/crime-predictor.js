// Crime prediction and application logic for SafePath
class CrimePredictor {
    constructor() {
        this.charts = {};
        this.currentLocation = null;
        
        this.initializeApp();
        this.setupEventListeners();
        this.loadStatistics();
    }
    
    initializeApp() {
        console.log('SafePath Crime Predictor initialized');
        
        // Initialize any required components
        this.setupCharts();
    }
    
    setupEventListeners() {
        // Current location risk assessment
        document.getElementById('getCurrentLocation').addEventListener('click', () => {
            this.getCurrentLocationRisk();
        });
        
        
        
        // Use current location button
        document.getElementById('useCurrentLocation').addEventListener('click', () => {
            this.useCurrentLocationForRoute();
        });
        
        // Smooth scrolling for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
    
    getCurrentLocationRisk() {
        this.showLoading();
        
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    
                    this.currentLocation = { lat, lng };
                    this.assessLocationRisk(lat, lng);
                },
                (error) => {
                    this.hideLoading();
                    this.showError('Unable to get your location. Please enable location services.');
                    console.error('Geolocation error:', error);
                }
            );
        } else {
            this.hideLoading();
            this.showError('Geolocation is not supported by this browser.');
        }
    }
    
    assessLocationRisk(lat, lng) {
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
            this.hideLoading();
            
            if (data.success) {
                this.displayLocationRisk(data, lat, lng);
            } else {
                this.showError('Failed to assess location risk: ' + data.error);
            }
        })
        .catch(error => {
            this.hideLoading();
            console.error('Error assessing location risk:', error);
            this.showError('Network error while assessing location risk');
        });
    }
    
    displayLocationRisk(riskData, lat, lng) {
        const riskDisplay = document.getElementById('currentRiskDisplay');
        const riskLevel = riskData.risk_level.toLowerCase();
        const crimeStats = riskData.crime_stats;
        
        riskDisplay.innerHTML = `
            <div class="risk-assessment fade-in">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="text-muted">Risk Score:</span>
                    <span class="risk-${riskLevel} fw-bold">${riskData.risk_score}/10</span>
                </div>
                
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="text-muted">Risk Level:</span>
                    <span class="risk-${riskLevel} fw-bold">${riskData.risk_level}</span>
                </div>
                
                <hr class="border-secondary">
                
                <div class="small">
                    <div class="d-flex justify-content-between mb-1">
                        <span class="text-muted">Nearby Crimes:</span>
                        <span class="text-white">${crimeStats.total_crimes}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-1">
                        <span class="text-muted">Recent (30d):</span>
                        <span class="text-white">${crimeStats.recent_crimes}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span class="text-muted">Avg Severity:</span>
                        <span class="text-white">${crimeStats.avg_severity}/5</span>
                    </div>
                </div>
                
                <div class="text-center">
                    <small class="text-muted">
                        <i class="fas fa-map-marker-alt me-1"></i>
                        ${lat.toFixed(4)}, ${lng.toFixed(4)}
                    </small>
                </div>
                
                ${this.getRiskRecommendation(riskData.risk_level)}
            </div>
        `;
        
        // Update map if available
        if (window.safePathMap) {
            window.safePathMap.updateUserLocationMarker(lat, lng);
        }
    }
    
    getRiskRecommendation(riskLevel) {
        const recommendations = {
            'Low': {
                icon: 'fas fa-check-circle text-success',
                text: 'This area appears to be relatively safe. Continue with normal precautions.'
            },
            'Medium': {
                icon: 'fas fa-exclamation-triangle text-warning',
                text: 'Exercise increased caution in this area. Stay alert and avoid isolated areas.'
            },
            'High': {
                icon: 'fas fa-exclamation-circle text-danger',
                text: 'High risk area detected. Consider avoiding or use extra safety measures.'
            }
        };
        
        const rec = recommendations[riskLevel] || recommendations['Medium'];
        
        return `
            <div class="mt-3 p-2 rounded" style="background-color: rgba(108, 117, 125, 0.1);">
                <div class="d-flex align-items-start">
                    <i class="${rec.icon} me-2 mt-1"></i>
                    <small class="text-white">${rec.text}</small>
                </div>
            </div>
        `;
    }
    
    calculateSafeRoute() {
        const startLat = parseFloat(document.getElementById('startLat').value);
        const startLng = parseFloat(document.getElementById('startLng').value);
        const endLat = parseFloat(document.getElementById('endLat').value);
        const endLng = parseFloat(document.getElementById('endLng').value);
        
        if (isNaN(startLat) || isNaN(startLng) || isNaN(endLat) || isNaN(endLng)) {
            this.showError('Please enter valid coordinates for both start and end points.');
            return;
        }
        
        this.showLoading();
        
        fetch('/api/safe-route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                start_lat: startLat,
                start_lng: startLng,
                end_lat: endLat,
                end_lng: endLng
            })
        })
        .then(response => response.json())
        .then(data => {
            this.hideLoading();
            
            if (data.success) {
                this.displayRouteResult(data);
                
                // Display route on map if available
                if (window.safePathMap) {
                    window.safePathMap.displayRoute(data);
                }
            } else {
                this.showError('Failed to calculate safe route: ' + data.error);
            }
        })
        .catch(error => {
            this.hideLoading();
            console.error('Error calculating safe route:', error);
            this.showError('Network error while calculating safe route');
        });
    }
    
    displayRouteResult(routeData) {
        const resultDiv = document.getElementById('routeResult');
        const detailsDiv = document.getElementById('routeDetails');
        
        const riskLevel = this.getRiskLevelFromScore(routeData.risk_score);
        const riskClass = riskLevel.toLowerCase();
        
        detailsDiv.innerHTML = `
            <div class="route-result-content fade-in">
                <div class="row g-3">
                    <div class="col-md-4">
                        <div class="text-center p-3 rounded" style="background-color: rgba(108, 117, 125, 0.1);">
                            <i class="fas fa-route fa-2x text-primary mb-2"></i>
                            <div class="text-white fw-bold">${routeData.distance_km} km</div>
                            <small class="text-muted">Total Distance</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center p-3 rounded" style="background-color: rgba(108, 117, 125, 0.1);">
                            <i class="fas fa-shield-alt fa-2x text-${riskClass === 'low' ? 'success' : riskClass === 'medium' ? 'warning' : 'danger'} mb-2"></i>
                            <div class="risk-${riskClass} fw-bold">${routeData.risk_score}/10</div>
                            <small class="text-muted">Risk Score</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center p-3 rounded" style="background-color: rgba(108, 117, 125, 0.1);">
                            <i class="fas fa-map-marked-alt fa-2x text-info mb-2"></i>
                            <div class="text-white fw-bold">${routeData.route_points.length}</div>
                            <small class="text-muted">Waypoints</small>
                        </div>
                    </div>
                </div>
                
                <div class="mt-3 p-3 rounded risk-${riskClass}" style="background-color: rgba(108, 117, 125, 0.1);">
                    <div class="d-flex align-items-center">
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>Route Assessment: ${riskLevel} Risk</strong>
                    </div>
                    <small class="d-block mt-1">
                        ${this.getRouteRecommendation(riskLevel)}
                    </small>
                </div>
                
                <div class="mt-3 text-center">
                    <button class="btn btn-primary me-2" onclick="crimePredictor.scrollToMap()">
                        <i class="fas fa-eye me-1"></i>View on Map
                    </button>
                    <button class="btn btn-secondary" onclick="crimePredictor.clearRoute()">
                        <i class="fas fa-trash me-1"></i>Clear Route
                    </button>
                </div>
            </div>
        `;
        
        resultDiv.style.display = 'block';
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    getRiskLevelFromScore(score) {
        if (score < 3) return 'Low';
        if (score < 6) return 'Medium';
        return 'High';
    }
    
    getRouteRecommendation(riskLevel) {
        const recommendations = {
            'Low': 'This route passes through relatively safe areas. Standard safety precautions are sufficient.',
            'Medium': 'This route has some areas of concern. Stay alert, especially during nighttime travel.',
            'High': 'This route passes through high-risk areas. Consider alternative routes or additional safety measures.'
        };
        
        return recommendations[riskLevel] || recommendations['Medium'];
    }
    
    useCurrentLocationForRoute() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    document.getElementById('startLat').value = position.coords.latitude.toFixed(6);
                    document.getElementById('startLng').value = position.coords.longitude.toFixed(6);
                    this.showSuccess('Current location set as starting point');
                },
                (error) => {
                    this.showError('Unable to get your current location');
                    console.error('Geolocation error:', error);
                }
            );
        } else {
            this.showError('Geolocation is not supported by this browser');
        }
    }
    
    loadStatistics() {
        fetch('/api/crime-stats')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(data)
                    this.updateDashboard(data);
                } else {
                    console.error('Failed to load statistics:', data.error);
                }
            })
            .catch(error => {
                console.error('Error loading statistics:', error);
            });
    }
    
    updateDashboard(stats) {
        document.getElementById('totalCrimes').textContent = stats.total_crimes.toLocaleString();
        document.getElementById('recentCrimes').textContent = stats.recent_crimes.toLocaleString();
        
        // Calculate overall risk level based on recent crime activity
        const riskPercentage = (stats.recent_crimes / stats.total_crimes) * 100;
        let overallRisk = 'Low';
        if (riskPercentage > 5) overallRisk = 'High';
        else if (riskPercentage > 2) overallRisk = 'Medium';
        
        document.getElementById('riskLevel').textContent = overallRisk;
        document.getElementById('safeRoutes').textContent = Math.floor(stats.total_crimes / 10); // Estimated
    }
    
    setupCharts() {
        // Chart functionality removed per user request
    }
    
    scrollToMap() {
        document.getElementById('map-section').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }
    
    clearRoute() {
        document.getElementById('routeForm').reset();
        document.getElementById('routeResult').style.display = 'none';
        
        // Clear route from map
        if (window.safePathMap && window.safePathMap.routeLayer) {
            window.safePathMap.map.removeLayer(window.safePathMap.routeLayer);
            window.safePathMap.routeLayer = null;
        }
    }
    
    showLoading() {
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        modal.show();
    }
    
    hideLoading() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (modal) {
            modal.hide();
        }
    }
    
    showError(message) {
        // Create a temporary error alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
    
    showSuccess(message) {
        // Create a temporary success alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        alertDiv.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 3000);
    }
}

// Global crime predictor instance
let crimePredictor;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    crimePredictor = new CrimePredictor();
});
