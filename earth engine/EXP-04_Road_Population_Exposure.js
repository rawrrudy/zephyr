
// EXP-04 — ROAD & POPULATION EXPOSURE CONTEXT
// Road dataset:
//   GRIP4 South-East Asia
// Population dataset:
//   WorldPop GP 100m population


// 1. CANDIDATE SENSOR LOCATIONS


var candidates = ee.FeatureCollection([
  ee.Feature(
    ee.Geometry.Point([73.873300, 18.593845]),
    {
      sensor: 'Sensor_1',
      latitude: 18.593845,
      longitude: 73.873300
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.802151, 18.602838]),
    {
      sensor: 'Sensor_2',
      latitude: 18.602838,
      longitude: 73.802151
    }
  ),

  ee.Feature(
    ee.Geometry.Point([73.892273, 18.530892]),
    {
      sensor: 'Sensor_3',
      latitude: 18.530892,
      longitude: 73.892273
    }
  )
]);

print('Candidate locations', candidates);


// 2. ROAD DATA — GRIP4 SOUTH & EAST ASIA


var roads = ee.FeatureCollection(
  'projects/sat-io/open-datasets/GRIP4/South-East-Asia'
);

print('GRIP4 South-East Asia road feature count', roads.size());



// 3. POPULATION DATA — WORLDPOP


var populationCollection = ee.ImageCollection(
  'WorldPop/GP/100m/pop'
);

// Use 2020 population because it is available in the dataset and provides a consistent reference year.

var population2020 = populationCollection
  .filterDate('2020-01-01', '2021-01-01')
  .select('population')
  .mosaic();

print('WorldPop 2020 population image', population2020);


// 4. BUFFER ANALYSIS FUNCTION


function analyzeCandidate(feature) {

  var point = feature.geometry();

  var sensor = feature.get('sensor');


  // 500 m buffer


  var buffer500 = point.buffer(500);

  var roads500 = roads.filterBounds(buffer500);

  // Calculate total road length in km.
  var roadLength500Km = ee.Number(
    roads500
      .map(function(road) {
        return road.set(
          'length_km',
          road.geometry().length(1).divide(1000)
        );
      })
      .aggregate_sum('length_km')
  );

  var buffer500AreaKm2 = buffer500.area(1).divide(1e6);

  var roadDensity500 = roadLength500Km
    .divide(buffer500AreaKm2);

  // Population within 500 m.
  var population500 = ee.Number(
    population2020
      .reduceRegion({
        reducer: ee.Reducer.sum(),
        geometry: buffer500,
        scale: 100,
        maxPixels: 1e8
      })
      .get('population')
  );

  var populationDensity500 = population500
    .divide(buffer500AreaKm2);



  // 1 km buffer


  var buffer1000 = point.buffer(1000);

  var roads1000 = roads.filterBounds(buffer1000);

  var roadLength1000Km = ee.Number(
    roads1000
      .map(function(road) {
        return road.set(
          'length_km',
          road.geometry().length(1).divide(1000)
        );
      })
      .aggregate_sum('length_km')
  );

  var buffer1000AreaKm2 = buffer1000.area(1).divide(1e6);

  var roadDensity1000 = roadLength1000Km
    .divide(buffer1000AreaKm2);

  var population1000 = ee.Number(
    population2020
      .reduceRegion({
        reducer: ee.Reducer.sum(),
        geometry: buffer1000,
        scale: 100,
        maxPixels: 1e8
      })
      .get('population')
  );

  var populationDensity1000 = population1000
    .divide(buffer1000AreaKm2);


  // 5. NEAREST ROAD DISTANCE
  

  // Restrict search to roads within 2 km.
  var nearbyRoads = roads.filterBounds(
    point.buffer(2000)
  );

  var roadDistances = nearbyRoads.map(function(road) {

    return ee.Feature(null, {
      distance_m: road.geometry().distance(point, 1)
    });

  });

  var nearestRoadDistance = ee.Number(
    roadDistances.aggregate_min('distance_m')
  );



  // 6. RETURN RESULT


  return feature.set({

    analysis_version: 'EXP-04',

    road_dataset:
      'GRIP4 South-East Asia',

    population_dataset:
      'WorldPop/GP/100m/pop',

    nearest_road_distance_m:
      nearestRoadDistance,

    radius_500m: ee.Dictionary({

      road_length_km:
        roadLength500Km,

      road_density_km_per_km2:
        roadDensity500,

      population:
        population500,

      population_density_per_km2:
        populationDensity500

    }),

    radius_1000m: ee.Dictionary({

      road_length_km:
        roadLength1000Km,

      road_density_km_per_km2:
        roadDensity1000,

      population:
        population1000,

      population_density_per_km2:
        populationDensity1000

    })

  });

}


// 7. RUN ANALYSIS


var results = candidates.map(analyzeCandidate);

print('====================================================');
print('EXP-04 RESULTS');
print('====================================================');

print(results);


// 8. MAP VISUALIZATION


Map.centerObject(candidates, 11);

Map.addLayer(
  roads.filterBounds(
    candidates.geometry().buffer(5000)
  ),
  {
    color: '333333'
  },
  'GRIP4 roads'
);

Map.addLayer(
  candidates,
  {
    color: 'yellow',
    pointSize: 8
  },
  'Candidate sensors'
);


// 9. EXPORT RESULTS


var flattened = results.map(function(feature) {

  var r500 = ee.Dictionary(
    feature.get('radius_500m')
  );

  var r1000 = ee.Dictionary(
    feature.get('radius_1000m')
  );

  return ee.Feature(
    feature.geometry(),
    {
      sensor:
        feature.get('sensor'),

      latitude:
        feature.get('latitude'),

      longitude:
        feature.get('longitude'),

      analysis_version:
        feature.get('analysis_version'),

      nearest_road_distance_m:
        feature.get('nearest_road_distance_m'),

      road_500m_km:
        r500.get('road_length_km'),

      road_density_500m_km_per_km2:
        r500.get('road_density_km_per_km2'),

      population_500m:
        r500.get('population'),

      population_density_500m_per_km2:
        r500.get('population_density_per_km2'),

      road_1000m_km:
        r1000.get('road_length_km'),

      road_density_1000m_km_per_km2:
        r1000.get('road_density_km_per_km2'),

      population_1000m:
        r1000.get('population'),

      population_density_1000m_per_km2:
        r1000.get('population_density_per_km2')
    }
  );

});


Export.table.toDrive({

  collection:
    flattened,

  description:
    'EXP-04_Road_Population_Exposure',

  fileFormat:
    'CSV'

});


print('EXP-04 export task created.');
