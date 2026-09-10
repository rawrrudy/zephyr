// EXP-06 — FINE-SCALE CANDIDATE SITE SCREENING

// Previous experiments:
//   01 = Spatial optimization
//   02 = Candidate robustness
//   03 = Environmental context
//   04 = Road + population context
//   05 = Road hierarchy

// This experiment adds:
//   - Recent Sentinel-2 satellite context
//   - Fine scale building footprint context
//   - Building footprint density
//   - Nearest mapped building distance
//   - Candidate/building overlap screening



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


// 2. OPEN BUILDINGS V3


var buildings = ee.FeatureCollection(
  'GOOGLE/Research/open-buildings/v3/polygons'
);

// Do NOT print the entire global collection.
// It contains millions of building polygons.


// 3. RECENT SENTINEL-2 SURFACE REFLECTANCE


var s2 = ee.ImageCollection(
  'COPERNICUS/S2_SR_HARMONIZED'
)
  .filterDate(
    '2025-01-01',
    '2026-09-01'
  )
  .filterBounds(
    candidates.geometry()
      .buffer(5000)
  )
  .filter(
    ee.Filter.lt(
      'CLOUDY_PIXEL_PERCENTAGE',
      30
    )
  );

print(
  'Sentinel-2 candidate imagery count',
  s2.size()
);


// 4. SENTINEL-2 CLOUD / SHADOW MASK


function maskS2(image) {

  var scl =
    image.select('SCL');

  var mask =
    scl.neq(3)       // cloud shadow
      .and(scl.neq(8))   // medium probability cloud
      .and(scl.neq(9))   // high probability cloud
      .and(scl.neq(10))  // cirrus
      .and(scl.neq(11)); 

  return image
    .updateMask(mask)
    .divide(10000);

}


var s2Clean =
  s2.map(maskS2);


// Median composite

var s2Median =
  s2Clean.median();


// 5. BUILDING ANALYSIS


function buildingMetrics(feature) {

  var point =
    feature.geometry();


  // Buffers
  

  var buffer100 =
    point.buffer(100);

  var buffer250 =
    point.buffer(250);


  // High confidence buildings
  

  var buildings100 =
    buildings
      .filterBounds(buffer100)
      .filter(
        ee.Filter.gte(
          'confidence',
          0.75
        )
      );


  var buildings250 =
    buildings
      .filterBounds(buffer250)
      .filter(
        ee.Filter.gte(
          'confidence',
          0.75
        )
      );


  // BUILDING FOOTPRINT AREA — 100 m

  var buildingArea100 =
    ee.Number(
      buildings100
        .map(function(building) {

          var clipped =
            building.geometry()
              .intersection(
                buffer100,
                1
              );

          return ee.Feature(null, {

            area_m2:
              clipped.area(1)

          });

        })
        .aggregate_sum('area_m2')
    );


  // BUILDING FOOTPRINT AREA — 250 m


  var buildingArea250 =
    ee.Number(
      buildings250
        .map(function(building) {

          var clipped =
            building.geometry()
              .intersection(
                buffer250,
                1
              );

          return ee.Feature(null, {

            area_m2:
              clipped.area(1)

          });

        })
        .aggregate_sum('area_m2')
    );

  
  // BUFFER AREAS
  

  var area100 =
    buffer100.area(1);

  var area250 =
    buffer250.area(1);

  
  // BUILDING COVERAGE
  

  var buildingCoverage100 =
    buildingArea100
      .divide(area100)
      .multiply(100);

  var buildingCoverage250 =
    buildingArea250
      .divide(area250)
      .multiply(100);

  
  // BUILDING COUNTS
  

  var buildingCount100 =
    buildings100.size();

  var buildingCount250 =
    buildings250.size();

  
  // BUILDING DENSITY


  var area100Km2 =
    area100.divide(1e6);

  var area250Km2 =
    area250.divide(1e6);


  var buildingDensity100 =
    ee.Number(buildingCount100)
      .divide(area100Km2);

  var buildingDensity250 =
    ee.Number(buildingCount250)
      .divide(area250Km2);


  // NEAREST BUILDING


  var nearbyBuildings =
    buildings
      .filterBounds(
        point.buffer(500)
      )
      .filter(
        ee.Filter.gte(
          'confidence',
          0.75
        )
      );


  var buildingDistances =
    nearbyBuildings.map(
      function(building) {

        return ee.Feature(null, {

          distance_m:
            building.geometry()
              .distance(
                point,
                1
              )

        });

      }
    );


  var nearestBuildingDistance =
    ee.Number(
      buildingDistances
        .aggregate_min(
          'distance_m'
        )
    );


  // DOES CANDIDATE FALL INSIDE A BUILDING?


  var candidateBuildingMatches =
    buildings
      .filter(
        ee.Filter.gte(
          'confidence',
          0.75
        )
      )
      .filterBounds(point);


  var candidateBuildingCount =
    candidateBuildingMatches.size();


  var candidateInsideBuilding =
    candidateBuildingCount.gt(0);


  // RETURN RESULTS
  

  return feature.set({

    analysis_version:
      'EXP-06',

    building_dataset:
      'GOOGLE/Research/open-buildings/v3/polygons',

    sentinel_dataset:
      'COPERNICUS/S2_SR_HARMONIZED',

    building_count_100m:
      buildingCount100,

    building_count_250m:
      buildingCount250,

    building_footprint_area_100m_m2:
      buildingArea100,

    building_footprint_area_250m_m2:
      buildingArea250,

    building_coverage_100m_percent:
      buildingCoverage100,

    building_coverage_250m_percent:
      buildingCoverage250,

    building_density_100m_per_km2:
      buildingDensity100,

    building_density_250m_per_km2:
      buildingDensity250,

    nearest_building_distance_m:
      nearestBuildingDistance,

    candidate_building_match_count:
      candidateBuildingCount,

    candidate_inside_mapped_building:
      candidateInsideBuilding

  });

}


// 6. RUN ANALYSIS


var results =
  candidates.map(
    buildingMetrics
  );


print(
  '===================================================='
);

print(
  'EXP-06 RESULTS'
);

print(
  '===================================================='
);

print(results);


// 7. MAP — SENTINEL-2


Map.centerObject(
  candidates,
  13
);


Map.addLayer(
  s2Median,
  {
    bands: [
      'B4',
      'B3',
      'B2'
    ],
    min: 0.0,
    max: 0.3
  },
  'Sentinel-2 true color'
);


// 8. BUILDING VISUALIZATION


var nearbyBuildings =
  buildings
    .filterBounds(
      candidates.geometry()
        .buffer(1500)
    )
    .filter(
      ee.Filter.gte(
        'confidence',
        0.75
      )
    );


var buildingRaster =
  nearbyBuildings
    .reduceToImage(
      ['confidence'],
      ee.Reducer.max()
    );


Map.addLayer(
  buildingRaster,
  {
    min: 0.75,
    max: 1.0,
    palette: [
      '333333'
    ]
  },
  'Open Buildings'
);



// 9. CANDIDATE POINTS


Map.addLayer(
  candidates,
  {
    color: 'yellow',
    pointSize: 8
  },
  'Candidate sensors'
);



// 10. 100 m BUFFERS

var buffer100Features =
  candidates.map(
    function(feature) {

      return ee.Feature(
        feature.geometry()
          .buffer(100),
        {
          sensor:
            feature.get('sensor')
        }
      );

    }
  );


Map.addLayer(
  buffer100Features,
  {
    color: '00FFFF'
  },
  '100 m candidate buffers'
);


// 11. 250 m BUFFERS


var buffer250Features =
  candidates.map(
    function(feature) {

      return ee.Feature(
        feature.geometry()
          .buffer(250),
        {
          sensor:
            feature.get('sensor')
        }
      );

    }
  );


Map.addLayer(
  buffer250Features,
  {
    color: 'FF00FF'
  },
  '250 m candidate buffers'
);


// 12. EXPORT

Export.table.toDrive({

  collection:
    results,

  description:
    'EXP-06_Fine_Scale_Site_Screening',

  fileFormat:
    'CSV'

});


print(
  'EXP-06 export task created.'
);
