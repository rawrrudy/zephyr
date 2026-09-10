// EXP-03
// CANDIDATE ENVIRONMENTAL CONTEXT SCREENING


// 1. CANDIDATE LOCATIONS

var candidates = ee.FeatureCollection([

  ee.Feature(
    ee.Geometry.Point([
      73.873300,
      18.593845
    ]),
    {
      sensor: 'Sensor_1',
      latitude: 18.593845,
      longitude: 73.873300
    }
  ),

  ee.Feature(
    ee.Geometry.Point([
      73.802151,
      18.602838
    ]),
    {
      sensor: 'Sensor_2',
      latitude: 18.602838,
      longitude: 73.802151
    }
  ),

  ee.Feature(
    ee.Geometry.Point([
      73.892273,
      18.530892
    ]),
    {
      sensor: 'Sensor_3',
      latitude: 18.530892,
      longitude: 73.892273
    }
  )

]);


print(
  'Candidate locations',
  candidates
);


// 2. ESA WORLDCOVER 2021

var worldCover = ee.ImageCollection(
  'ESA/WorldCover/v200'
).first().select('Map');


print(
  'ESA WorldCover',
  worldCover
);


// 3. GHSL BUILT UP SURFACE 2018


var ghsl = ee.Image(
  'JRC/GHSL/P2023A/GHS_BUILT_S_10m/2018'
);


var builtSurface = ghsl.select(
  'built_surface'
);


var builtSurfaceNRES = ghsl.select(
  'built_surface_nres'
);


print(
  'GHSL built-up surface',
  ghsl
);



// 4. LAND COVER CLASS NAMES


var classNames = {
  10: 'Tree cover',
  20: 'Shrubland',
  30: 'Grassland',
  40: 'Cropland',
  50: 'Built-up',
  60: 'Bare/sparse vegetation',
  70: 'Snow/ice',
  80: 'Permanent water',
  90: 'Herbaceous wetland',
  95: 'Mangroves',
  100: 'Moss/lichen'
};



// 5. FUNCTION FOR LAND COVER FRACTIONS


function landCoverFractions(
  geometry,
  scale
) {

  var histogram = worldCover.reduceRegion({

    reducer:
      ee.Reducer.frequencyHistogram(),

    geometry:
      geometry,

    scale:
      scale,

    maxPixels:
      1000000,

    bestEffort:
      true

  });


  var histogramDict = ee.Dictionary(
    histogram.get('Map')
  );


  var totalPixels = ee.Number(
    histogramDict.values().reduce(
      ee.Reducer.sum()
    )
  );


  var output = ee.Dictionary();


  Object.keys(classNames).forEach(
    function(code) {

      var count = ee.Number(
        histogramDict.get(
          String(code),
          0
        )
      );


      var fraction = count
        .divide(totalPixels)
        .multiply(100);


      output = output.set(
        'LC_' +
        classNames[code]
          .replace(/\//g, '_')
          .replace(/ /g, '_')
          .toLowerCase() +
        '_percent',

        fraction
      );

    }
  );


  return output;
}


// 6. FUNCTION FOR BUILT UP METRICS


function builtMetrics(
  geometry
) {

  // GHSL built_surface is square metres
  // of built surface per 10 m grid cell.
  //
  // A 10 m × 10 m pixel has 100 m² total area.

  var builtMean = ee.Number(
    builtSurface
      .reduceRegion({

        reducer:
          ee.Reducer.mean(),

        geometry:
          geometry,

        scale:
          10,

        maxPixels:
          1000000,

        bestEffort:
          true

      })
      .get('built_surface')
  );


  var builtFraction = builtMean
    .divide(100)
    .multiply(100);


  var nresMean = ee.Number(
    builtSurfaceNRES
      .reduceRegion({

        reducer:
          ee.Reducer.mean(),

        geometry:
          geometry,

        scale:
          10,

        maxPixels:
          1000000,

        bestEffort:
          true

      })
      .get('built_surface_nres')
  );


  return ee.Dictionary({

    built_surface_mean_m2_per_10m_cell:
      builtMean,

    estimated_built_surface_percent:
      builtFraction,

    non_residential_built_cell_fraction_percent:
      nresMean.multiply(100)

  });

}


// 7. ANALYZE EACH CANDIDATE


var results = candidates.map(
  function(feature) {

    var point =
      feature.geometry();


    
    // 500 m buffer
    

    var buffer500 =
      point.buffer(500);


    
    // 1 km buffer
    

    var buffer1000 =
      point.buffer(1000);


    
    // Land cover
    

    var lc500 =
      landCoverFractions(
        buffer500,
        10
      );


    var lc1000 =
      landCoverFractions(
        buffer1000,
        10
      );


    
    // Built environment
    

    var built500 =
      builtMetrics(
        buffer500
      );


    var built1000 =
      builtMetrics(
        buffer1000
      );


    
    // Combine results
    

    return feature
      .set(
        'radius_500m',
        ee.Dictionary(
          lc500.combine(
            built500
          )
        )
      )
      .set(
        'radius_1000m',
        ee.Dictionary(
          lc1000.combine(
            built1000
          )
        )
      );

  }
);



// 8. FLATTEN RESULTS


var flattened = results.map(
  function(feature) {

    var lc500 =
      ee.Dictionary(
        feature.get(
          'radius_500m'
        )
      );


    var lc1000 =
      ee.Dictionary(
        feature.get(
          'radius_1000m'
        )
      );


    return feature
      .set(
        lc500
      )
      .set(
        lc1000
      )
      .set(
        'analysis_version',
        'EXP-02D-G'
      )
      .set(
        'worldcover_dataset',
        'ESA/WorldCover/v200'
      )
      .set(
        'ghsl_dataset',
        'JRC/GHSL/P2023A/GHS_BUILT_S_10m/2018'
      );

  }
);



// 9. PRINT RESULTS


print(
  '================================================'
);

print(
  'EXP-02D-G RESULTS'
);

print(
  '================================================'
);


print(
  flattened
);


// 10. MAP


Map.centerObject(
  candidates,
  12
);


Map.addLayer(
  worldCover,
  {
    min: 10,
    max: 100
  },
  'ESA WorldCover 2021'
);


Map.addLayer(
  builtSurface,
  {
    min: 0,
    max: 100
  },
  'GHSL Built Surface 2018'
);


Map.addLayer(
  candidates,
  {
    color: 'FF0000'
  },
  'Optimized Candidate Sensors'
);


// Add 500 m buffers.

var buffers500 =
  candidates.map(
    function(feature) {

      return feature
        .buffer(500);

    }
  );


Map.addLayer(
  buffers500,
  {
    color: 'FFFF00'
  },
  '500 m Candidate Buffers'
);



// 11. EXPORT RESULTS


Export.table.toDrive({

  collection:
    flattened,

  description:
    'EXP-02D-G_Candidate_Environmental_Context',

  fileFormat:
    'CSV'

});


print(
  'EXP-02D-G export task created.'
);
