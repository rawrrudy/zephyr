// EXP-05 — ROAD HIERARCHY SCREENING


// 1. CANDIDATE LOCATIONS

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


// 2. GRIP4 SOUTH & EAST ASIA


var roads = ee.FeatureCollection(
  'projects/sat-io/open-datasets/GRIP4/South-East-Asia'
);

print(
  'GRIP4 South-East Asia road feature count',
  roads.size()
);


// 3. CORRECTED ROAD LENGTH FUNCTION


function roadLengthKm(collection, roadType, buffer) {

  var filtered = collection.filter(
    ee.Filter.eq('GP_RTP', roadType)
  );

  return ee.Number(
    filtered
      .map(function(road) {

        var clippedRoad =
          road.geometry().intersection(buffer, 1);

        return ee.Feature(null, {

          length_km:
            clippedRoad
              .length(1)
              .divide(1000)

        });

      })
      .aggregate_sum('length_km')
  );

}


// 4. NEAREST ROAD FUNCTION

function nearestRoadDistance(
  nearbyRoads,
  point,
  roadType
) {

  var typedRoads =
    nearbyRoads.filter(
      ee.Filter.eq('GP_RTP', roadType)
    );

  var distances =
    typedRoads.map(function(road) {

      return ee.Feature(null, {

        distance_m:
          road.geometry()
            .distance(point, 1)

      });

    });

  return ee.Number(
    distances.aggregate_min('distance_m')
  );

}


// 5. ANALYZE EACH CANDIDATE


function analyzeCandidate(feature) {

  var point = feature.geometry();


  // BUFFERS


  var buffer500 =
    point.buffer(500);

  var buffer1000 =
    point.buffer(1000);


  // ROAD COLLECTIONS
 

  var roads500 =
    roads.filterBounds(buffer500);

  var roads1000 =
    roads.filterBounds(buffer1000);


  // ROAD LENGTHS — 500 m
 

  var highway500 =
    roadLengthKm(
      roads500,
      1,
      buffer500
    );

  var primary500 =
    roadLengthKm(
      roads500,
      2,
      buffer500
    );

  var secondary500 =
    roadLengthKm(
      roads500,
      3,
      buffer500
    );

  var tertiary500 =
    roadLengthKm(
      roads500,
      4,
      buffer500
    );

  var local500 =
    roadLengthKm(
      roads500,
      5,
      buffer500
    );


  // ROAD LENGTHS — 1 km


  var highway1000 =
    roadLengthKm(
      roads1000,
      1,
      buffer1000
    );

  var primary1000 =
    roadLengthKm(
      roads1000,
      2,
      buffer1000
    );

  var secondary1000 =
    roadLengthKm(
      roads1000,
      3,
      buffer1000
    );

  var tertiary1000 =
    roadLengthKm(
      roads1000,
      4,
      buffer1000
    );

  var local1000 =
    roadLengthKm(
      roads1000,
      5,
      buffer1000
    );

  
  // MAJOR ROAD LENGTH

  // Major = highway + primary + secondary


  var major500 =
    highway500
      .add(primary500)
      .add(secondary500);

  var major1000 =
    highway1000
      .add(primary1000)
      .add(secondary1000);


  // TOTAL ROAD LENGTH
 

  var total500 =
    highway500
      .add(primary500)
      .add(secondary500)
      .add(tertiary500)
      .add(local500);

  var total1000 =
    highway1000
      .add(primary1000)
      .add(secondary1000)
      .add(tertiary1000)
      .add(local1000);


  // BUFFER AREAS


  var area500Km2 =
    buffer500
      .area(1)
      .divide(1e6);

  var area1000Km2 =
    buffer1000
      .area(1)
      .divide(1e6);


  // ROAD DENSITIES


  var majorDensity500 =
    major500
      .divide(area500Km2);

  var majorDensity1000 =
    major1000
      .divide(area1000Km2);


  var totalDensity500 =
    total500
      .divide(area500Km2);

  var totalDensity1000 =
    total1000
      .divide(area1000Km2);


  // NEAREST ROAD DISTANCES


  var nearbyRoads =
    roads.filterBounds(
      point.buffer(2000)
    );


  var nearestHighway =
    nearestRoadDistance(
      nearbyRoads,
      point,
      1
    );

  var nearestPrimary =
    nearestRoadDistance(
      nearbyRoads,
      point,
      2
    );

  var nearestSecondary =
    nearestRoadDistance(
      nearbyRoads,
      point,
      3
    );

  var nearestTertiary =
    nearestRoadDistance(
      nearbyRoads,
      point,
      4
    );

  var nearestLocal =
    nearestRoadDistance(
      nearbyRoads,
      point,
      5
    );


  // RETURN RESULTS


  return feature.set({

    analysis_version:
      'EXP-05',

    road_dataset:
      'GRIP4 South-East Asia',


    // 500 m ROAD LENGTHS


    highway_500m_km:
      highway500,

    primary_500m_km:
      primary500,

    secondary_500m_km:
      secondary500,

    tertiary_500m_km:
      tertiary500,

    local_500m_km:
      local500,

    major_500m_km:
      major500,

    total_500m_km:
      total500,


    // 500 m ROAD DENSITY


    major_road_density_500m_km_per_km2:
      majorDensity500,

    total_road_density_500m_km_per_km2:
      totalDensity500,


    // 1 km ROAD LENGTHS


    highway_1000m_km:
      highway1000,

    primary_1000m_km:
      primary1000,

    secondary_1000m_km:
      secondary1000,

    tertiary_1000m_km:
      tertiary1000,

    local_1000m_km:
      local1000,

    major_1000m_km:
      major1000,

    total_1000m_km:
      total1000,


    // 1 km ROAD DENSITY


    major_road_density_1000m_km_per_km2:
      majorDensity1000,

    total_road_density_1000m_km_per_km2:
      totalDensity1000,



    // NEAREST ROAD DISTANCES


    nearest_highway_m:
      nearestHighway,

    nearest_primary_m:
      nearestPrimary,

    nearest_secondary_m:
      nearestSecondary,

    nearest_tertiary_m:
      nearestTertiary,

    nearest_local_m:
      nearestLocal

  });

}


// 6. RUN ANALYSIS


var results =
  candidates.map(analyzeCandidate);


print(
  '===================================================='
);

print(
  'EXP-05 RESULTS'
);

print(
  '===================================================='
);

print(results);


// 7. MAP


Map.centerObject(
  candidates,
  11
);


// GRIP4 roads — dark gray for visibility.

Map.addLayer(
  roads.filterBounds(
    candidates.geometry()
      .buffer(5000)
  ),
  {
    color: '333333'
  },
  'GRIP4 roads'
);


// Candidate sensors.

Map.addLayer(
  candidates,
  {
    color: 'yellow',
    pointSize: 8
  },
  'Candidate sensors'
);


// 8. EXPORT

Export.table.toDrive({

  collection:
    results,

  description:
    'EXP-05_Road_Hierarchy_Screening',

  fileFormat:
    'CSV'

});


print(
  'EXP-05 export task created.'
);
