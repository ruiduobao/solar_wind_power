var wind_fc = ee.FeatureCollection("projects/casproject-476115/assets/WIND_power_2018_2024");
// =========================================================================
// Task: count the ESRI and FROM-GLC10 (2017) land cover area and pixel counts within wind farm extents
// =========================================================================

// 1. Data preparation

// --- ESRI Global Land Cover (2017) ---
var esri_col = ee.ImageCollection("projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS");
var esri_2017 = esri_col.filterDate('2017-01-01', '2017-12-31')
    .mosaic()
    .rename('class_code');

// --- FROM-GLC10 (2017) ---
// Fix: removed .filterBounds(wind_fc.geometry())
// Note: mosaic directly; reduceRegion requests data on demand, do not manually merge large geometries for filtering
var from_col = ee.ImageCollection("projects/sat-io/open-datasets/FROM-GLC10");
var from_2017 = from_col
    .mosaic()
    .rename('class_code');

// 2. Generic statistics function
var computeStats = function(image, feature) {
  // Build the statistics image: band0=count(1), band1=area, band2=class_code
  var stats_img = ee.Image.constant(1).rename('pixel_count').float()
      .addBands(ee.Image.pixelArea().rename('area_sqm'))
      .addBands(image);

  var geom = feature.geometry(); 

  // Grouped statistics
  var stats = stats_img.reduceRegion({
    reducer: ee.Reducer.sum().repeat(2).group({
      groupField: 2,       // group by class_code
      groupName: 'code',
    }),
    geometry: geom,
    scale: 10,             
    maxPixels: 1e9,
    tileScale: 4, // suggestion: slightly increase tileScale to prevent memory overflow for a single large wind farm
    bestEffort: true
  });

  var groups_list = ee.List(stats.get('groups'));
  
  return feature.set({
    'stats_json': ee.String.encodeJSON(groups_list)
  });
};

// 3. Batch export logic

// Suggestion: polygon data is computationally heavy, reduce the Batch Size to avoid task timeouts or memory overflow
var BATCH_SIZE = 1000; 
var total_count = wind_fc.size().getInfo(); 
var num_batches = Math.ceil(total_count / BATCH_SIZE);

print('Total Features:', total_count);
print('Generating ' + num_batches + ' batches per dataset...');

var wind_list = wind_fc.toList(total_count);

for (var i = 0; i < num_batches; i++) {
  var start_idx = i * BATCH_SIZE;
  var end_idx = start_idx + BATCH_SIZE; 
  
  var batch_fc = ee.FeatureCollection(wind_list.slice(start_idx, end_idx));
  
  // -----------------------------------------------------
  // Task A: Export ESRI 2017 statistics
  // -----------------------------------------------------
  var processed_esri = batch_fc.map(function(feat) {
    return computeStats(esri_2017, feat);
  });
  
  Export.table.toDrive({
    collection: processed_esri,
    description: 'ESRI_2017_Stats_For2018_2024_Batch_' + (i + 1),
    folder: 'GEE_Wind_Analysis_2018_2024',
    fileFormat: 'CSV',
    selectors: ['fid', 'stats_json'] 
  });

  // -----------------------------------------------------
  // Task B: Export FROM-GLC10 2017 statistics
  // -----------------------------------------------------
  var processed_from = batch_fc.map(function(feat) {
    return computeStats(from_2017, feat);
  });

  Export.table.toDrive({
    collection: processed_from,
    description: 'FROM_2017_Stats_For2018_2024_Batch_' + (i + 1),
    folder: 'GEE_Wind_Analysis_2018_2024',
    fileFormat: 'CSV',
    selectors: ['fid', 'stats_json'] 
  });
}