// EXP 02B — Ground Station Coordinates & Spatial Distribution


// candidate ground monitoring coordinates

var stations = ee.FeatureCollection([

  ee.Feature(
    ee.Geometry.Point([73.892743, 18.675076]),
    {
      name: 'Alandi',
      operator: 'IITM'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.848956, 18.640051]),
    {
      name: 'Bhosari',
      operator: 'IITM'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.749976, 18.605770]),
    {
      name: 'Bhumkar Nagar',
      operator: 'IITM'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.852193, 18.459883]),
    {
      name: 'Dhankawadi',
      operator: 'IITM'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.927532, 18.501793]),
    {
      name: 'Hadapsar',
      operator: 'IITM'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.816553, 18.501174]),
    {
      name: 'Karve Road',
      operator: 'MPCB'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.854155, 18.454450]),
    {
      name: 'Katraj Dairy',
      operator: 'MPCB'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.927715, 18.573040]),
    {
      name: 'Mhada Colony',
      operator: 'IITM'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.805454, 18.536457]),
    {
      name: 'Panchawati/Pashan',
      operator: 'IITM'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.849598, 18.530085]),
    {
      name: 'Revenue Colony/Shivajinagar',
      operator: 'IITM'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.826908, 18.547056]),
    {
      name: 'SPPU',
      operator: 'MPCB'
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.763966, 18.664282]),
    {
      name: 'Transport Nagar/Nigdi',
      operator: 'IITM'
    }
  )

]);


// display stations

Map.addLayer(
  stations,
  {
    color: 'red'
  },
  'Candidate Ground Stations'
);

Map.centerObject(stations, 11);

// print info

print(
  'Candidate ground stations:',
  stations
);

print(
  'Number of candidate stations:',
  stations.size()
);


// geographic extent

var bounds = stations.geometry().bounds();

print(
  'Network bounding box:',
  bounds
);

// network centroid

var centroid = stations.geometry().centroid();

print(
  'Network centroid:',
  centroid
);
