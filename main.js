import './style.css';
import { Map, View } from 'ol';
import { fromLonLat } from 'ol/proj';
import VectorSource from 'ol/source/Vector';
import { Vector as VectorLayer } from 'ol/layer';
import { Fill, Stroke, Style, Circle } from 'ol/style';
import GeoJSON from 'ol/format/GeoJSON';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import Overlay from 'ol/Overlay';
import Text from 'ol/style/Text';
import ImageStatic from 'ol/source/ImageStatic';
import ImageLayer from 'ol/layer/Image';

// reference to the <select> element
const variableSelect = document.getElementById('variableSelect');

// Variable to store the selected value
let variableName = variableSelect.value;

const washingtonCenter = fromLonLat([-120.5, 47.4]);


const olmap = new Map({
    target: 'olmap',
    layers: [],
    view: new View({
        center: washingtonCenter,
        zoom: 7
    })
});


// Event listener for the dropdown change event
variableSelect.addEventListener('change', function() {
    // Update the variableName with the selected value
    variableName = variableSelect.value;
    generateMap(variableName);
});

generateMap(variableName);
function generateMap(variableName) {
    olmap.getLayers().clear();
    variableName = variableName;
    const backgroundName = variableName + '_BACKGROUND.png';
    console.log(backgroundName + variableName);
    const idahoSource = new VectorSource({
        url: 'idaho.geojson',
        format: new GeoJSON()
    });

    const idahoLayer = new VectorLayer({
        source: idahoSource,
        style: new Style({
            fill: new Fill({
                color: 'white', // Set the mask color
            }),
            stroke: new Stroke({
                color: 'transparent', // Set the mask border color to transparent
                width: 0,
            }),
        }),
    });

    const oregonSource = new VectorSource({
        url: 'oregon.geojson',
        format: new GeoJSON()
    });

    const montanaSource = new VectorSource({
        url: 'montana.geojson',
        format: new GeoJSON()
    });

    const montanaLayer = new VectorLayer({
        source: montanaSource,
        style: new Style({
            fill: new Fill({
                color: 'white', // Set the mask color
            }),
            stroke: new Stroke({
                color: 'transparent', // Set the mask border color to transparent
                width: 0,
            }),
        }),
    });

    const imageExtent = ol.proj.transformExtent(
        [-124.848974, 45.543541, -116.916071, 49.002494], // WGS84 coordinates
        'EPSG:4326', // Source projection (WGS84)
        'EPSG:3857' // Target projection
    );

    const colorCodedMap = new ImageStatic({
        url: backgroundName,
        imageExtent: imageExtent
    });

// Create an Image layer using the ImageStatic source
    const colorCodedLayer = new ImageLayer({
        source: colorCodedMap
    });
    console.log('Created image layer:', colorCodedLayer);

// Add the PNG image layer as the bottom layer of the map
    olmap.addLayer(colorCodedLayer);
    console.log('Added image layer to map:', colorCodedLayer);

    const oregonLayer = new VectorLayer({
        source: oregonSource,
        style: new Style({
            fill: new Fill({
                color: 'white', // Set the mask color
            }),
            stroke: new Stroke({
                color: 'transparent', // Set the mask border color to transparent
                width: 0,
            }),
        }),
    });

    const stateBoundariesSource = new VectorSource({
        url: 'WA_State_Boundary.geojson',
        format: new GeoJSON()
    });
    const stateBoundariesLayer = new VectorLayer({
        source: stateBoundariesSource,
        style: new Style({
            stroke: new Stroke({
                color: 'black',
                width: 2
            })
        })
    });

    olmap.addLayer(stateBoundariesLayer);

    const countyBoundariesSource = new VectorSource({
        url: 'WA_County_Boundaries.geojson',
        format: new GeoJSON()
    });

    const countyBoundariesLayer = new VectorLayer({
        source: countyBoundariesSource,
        style: new Style({
            stroke: new Stroke({
                color: 'black',
                width: 0.5
            })
        })
    });

    olmap.addLayer(countyBoundariesLayer);

// Load the station data from JSON file
    fetch('station_data.json')
    .then(response => response.json())
    .then(data => {
        const features = data.map(item => {
            if (item.LABEL_FLAG === 1) {
                const coordinates = fromLonLat([parseFloat(item.LNG), parseFloat(item.LAT)]);

                const feature = new Feature({
                    geometry: new Point(coordinates)
                });

                feature.set('name', item.STATION_NAME);
                feature.set('county_id', item.COUNTY_ID);

                // Set all variables from the select list as properties on the feature
                for (const variable of variableSelect.options) {
                    const variableName = variable.value;
                    if (!isNaN(item[variableName])) {
                        feature.set(variableName, item[variableName]);
                    }
                }
                return feature;
            }
             else {
                return null; // Skip creating feature for LABEL_FLAG !== 1
            }
        }).filter(feature => feature !== null); // Filter out null features (NaN values)

            const stationsSource = new VectorSource({
                features: features
            });

            // a function to create temperature-based style
            function createStyle(feature) {
                const variable = feature.get(variableName);
                if (variable !== null) {
                    return new Style({
                        text: new Text({
                            text: variable.toString(),
                            fill: new Fill({ color: 'white' }), // Color of the text
                            stroke: new Stroke({ color: 'black', width: 2 }), // Outline of the text
                            font: 'bold 11px Arial'
                        }),
                        geometry: new Point(feature.getGeometry().getCoordinates()),
                        fill: new Fill({
                            color: 'transparent'
                        }),
                        stroke: new Stroke({
                            color: 'white',
                            width: 1
                        })
                    });
                } else {
                    // Return a style for stations with null values if needed
                    return new Style({
                        text: new Text({
                            text: '',
                            fill: new Fill({ color: 'white' }),
                            stroke: new Stroke({ color: 'black', width: 2 }),
                            font: 'bold 11px Arial'
                        }),
                        geometry: new Point(feature.getGeometry().getCoordinates()),
                        fill: new Fill({
                            color: 'transparent'
                        }),
                        stroke: new Stroke({
                            color: 'white',
                            width: 1
                        })
                    });
                }
            }

            const stationLayer = new VectorLayer({
                source: stationsSource,
                style: createStyle
            });

            // Add the mask layers on top of color-coded map layer
            olmap.addLayer(oregonLayer);
            console.log("oregon layer created", oregonLayer)
            olmap.addLayer(idahoLayer);
            console.log("idaho layer created", idahoLayer)
            olmap.addLayer(montanaLayer);
            console.log("montana layer created", montanaLayer)
            olmap.addLayer(stationLayer);
            console.log("station layer created", stationLayer)

            // Create a tooltip overlay
            const tooltipOverlay = new Overlay({
                element: document.getElementById('tooltip'),
                offset: [10, 0],
                positioning: 'bottom-left'
            });

            olmap.addOverlay(tooltipOverlay);

            olmap.on('pointermove', function (event) {
                const stationFeature = olmap.forEachFeatureAtPixel(event.pixel, function (feature) {
                    return feature;
                }, {
                    layerFilter: function (layer) {
                        return layer === stationLayer; // Only consider the station layer for station tooltips
                    }
                });

                const countyFeature = olmap.forEachFeatureAtPixel(event.pixel, function (feature) {
                    return feature;
                }, {
                    layerFilter: function (layer) {
                        return layer === countyBoundariesLayer; // Only consider the county boundaries layer for county tooltips
                    }
                });

                if (stationFeature) {
                    let tooltipHTML = '<b>' + stationFeature.get('name') + '</b><br>';
                    // Display all variables in the tooltip
                    for (const variable of variableSelect.options) {
                        const variableName = variable.value;
                        const variableValue = stationFeature.get(variableName);
                        if (variableValue !== undefined) {
                            tooltipHTML += variableName + ': ' + variableValue + '<br>';
                        }
                    }
                    tooltipOverlay.getElement().innerHTML = tooltipHTML;
                    tooltipOverlay.setPosition(event.coordinate);
                    tooltipOverlay.getElement().style.display = 'block';
                }
                else if (countyFeature) {
                    // Adjust the tooltip content for county boundaries as needed
                    tooltipOverlay.getElement().innerHTML = countyFeature.get('JURISDICT_NM') + " Border";
                    tooltipOverlay.setPosition(event.coordinate);
                    tooltipOverlay.getElement().style.display = 'block';
                } else {
                    tooltipOverlay.getElement().style.display = 'none';
                }
            });

        })
        .catch(error => {
            console.error('Error fetching JSON data:', error);
        });
}