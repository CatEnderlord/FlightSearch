const apiKey = "ed410cae4c0343ff9c5b69991267a9ad";
const map = L.map('map').setView([0, 0], 2);

L.tileLayer(`https://maps.geoapify.com/v1/tile/carto/{z}/{x}/{y}.png?&apiKey=${apiKey}`, {
    maxZoom: 19,
}).addTo(map);

let markers = [];
let polyline = null; // Store the great-circle polyline
let airportLines = []; // Store the red lines to airports

// Function to calculate intermediate points for a great-circle route
function getGreatCirclePoints(startLatLng, endLatLng, numPoints = 100) {
    const lat1 = startLatLng.lat * Math.PI / 180;
    const lon1 = startLatLng.lng * Math.PI / 180;
    const lat2 = endLatLng.lat * Math.PI / 180;
    const lon2 = endLatLng.lng * Math.PI / 180;

    const points = [];

    for (let i = 0; i <= numPoints; i++) {
        const f = i / numPoints;
        const A = Math.sin((1 - f) * Math.acos(Math.sin(lat1) * Math.sin(lat2) + Math.cos(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1))) / Math.sin(Math.acos(Math.sin(lat1) * Math.sin(lat2) + Math.cos(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1)));
        const B = Math.sin(f * Math.acos(Math.sin(lat1) * Math.sin(lat2) + Math.cos(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1))) / Math.sin(Math.acos(Math.sin(lat1) * Math.sin(lat2) + Math.cos(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1)));

        const x = A * Math.cos(lat1) * Math.cos(lon1) + B * Math.cos(lat2) * Math.cos(lon2);
        const y = A * Math.cos(lat1) * Math.sin(lon1) + B * Math.cos(lat2) * Math.sin(lon2);
        const z = A * Math.sin(lat1) + B * Math.sin(lat2);

        const lat = Math.atan2(z, Math.sqrt(x * x + y * y)) * 180 / Math.PI;
        const lon = Math.atan2(y, x) * 180 / Math.PI;

        points.push([lat, lon]);
    }

    return points;
}

map.on('click', function (e) {
    if (markers.length < 2) {
        const marker = L.marker([e.latlng.lat, e.latlng.lng]).addTo(map);
        markers.push(marker);
    }
});

document.getElementById('calculate').addEventListener('click', async () => {
    if (markers.length < 2) {
        alert("Please select two points on the map.");
        return;
    }

    const [start, end] = markers.map(marker => marker.getLatLng());

    // Fetch calculation data
    const response = await fetch(`/calculate?startLat=${start.lat}&startLng=${start.lng}&endLat=${end.lat}&endLng=${end.lng}`);
    const data = await response.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    // Draw the great-circle line
    const points = getGreatCirclePoints(start, end);
    if (polyline) {
        map.removeLayer(polyline); // Remove the existing great-circle polyline if any
    }
    polyline = L.polyline(points, { color: 'blue', weight: 3 }).addTo(map);

    // Draw red lines from selected points to nearest airports
    airportLines.forEach(line => map.removeLayer(line)); // Clear existing red lines
    airportLines = [];

    const startAirportCoords = [data.startAirport.lat, data.startAirport.lng];
    const endAirportCoords = [data.endAirport.lat, data.endAirport.lng];

    const startToAirportLine = L.polyline([start, startAirportCoords], { color: 'red', weight: 2 }).addTo(map);
    const endToAirportLine = L.polyline([end, endAirportCoords], { color: 'red', weight: 2 }).addTo(map);

    airportLines.push(startToAirportLine, endToAirportLine);

    // Update output details
    document.getElementById('output').innerHTML = `
        Nearest Airport to Start: ${data.startAirport.name} (${data.startAirport.code})<br>
        Nearest Airport to End: ${data.endAirport.name} (${data.endAirport.code})<br>
        Estimated Flight Time: ${data.flightTime} hours
    `;
});

// Refresh Page button functionality
document.getElementById('refresh').addEventListener('click', () => {
    location.reload();
});