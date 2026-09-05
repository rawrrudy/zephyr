// EXP-01 AOD Quantification

// temp study area

var studyArea = ee.Geometry.Rectangle([
  73.70, 18.35,
  73.95, 18.65
]);

// load MODIS MAIAC AOD

var aodCollection = ee.ImageCollection(
  'MODIS/061/MCD19A2_GRANULES'
)
.filterBounds(studyArea)
.filterDate('2025-01-01', '2025-02-01');

// apply best quality QA mask

function maskBestQuality(image) {

  var qa = image.select('AOD_QA');

  // 8-11 contain the AOD quality flag
  var aodQuality = qa
    .rightShift(8)
    .bitwiseAnd(15);

  // best quality retrievals
  var mask = aodQuality.eq(0);

  // convert stored AOD to physical AOD
  var aod = image
    .select('Optical_Depth_055')
    .multiply(0.001)
    .updateMask(mask)
    .rename('AOD_055');

  return aod.copyProperties(
    image,
    ['system:time_start']
  );
}

// apply QA function

var cleanAOD = aodCollection.map(maskBestQuality);

// create january mean AOD

var januaryAOD = cleanAOD
  .mean()
  .clip(studyArea);

// calculate stats

var statistics = januaryAOD.reduceRegion({

  reducer: ee.Reducer.mean()
    .combine({
      reducer2: ee.Reducer.minMax(),
      sharedInputs: true
    })
    .combine({
      reducer2: ee.Reducer.stdDev(),
      sharedInputs: true
    }),

  geometry: studyArea,

  scale: 1000,

  maxPixels: 1e8

});

// count valid pixels

var validPixels = januaryAOD
  .mask()
  .reduceRegion({

    reducer: ee.Reducer.sum(),

    geometry: studyArea,

    scale: 1000,

    maxPixels: 1e8

  });

// print results

print(
  ee.Dictionary({
    mean_AOD: statistics.get('AOD_055_mean'),
    minimum_AOD: statistics.get('AOD_055_min'),
    maximum_AOD: statistics.get('AOD_055_max'),
    standard_deviation: statistics.get('AOD_055_stdDev'),
    valid_pixel_count: validPixels.get('AOD_055')
  })
);

// display AOD

Map.centerObject(studyArea, 10);

Map.addLayer(
  januaryAOD,
  {
    min: 0,
    max: 1,
    palette: [
      'blue',
      'cyan',
      'green',
      'yellow',
      'orange',
      'red'
    ]
  },
  'January 2025 AOD'
);

Map.addLayer(
  studyArea,
  {},
  'Study Area'
);
