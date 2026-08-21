// =========================================================================
// Task: compute slope statistics for solar sites (mean + graded counts)
// Data source: NASADEM (30m)
// =========================================================================

// 1. Data preparation
var solar_fc = ee.FeatureCollection("projects/casproject-476115/assets/SOLAOR_POWER_2018_2024");

// Load DEM and compute slope
var nasadem = ee.Image("NASA/NASADEM_HGT/001");
var elevation = nasadem.select('elevation');
var slope = ee.Terrain.slope(elevation); // result unit is degrees

// 2. Build the graded mask (corresponding to the methodology in your paper)
// Level 1: < 5°   (value 1)
// Level 2: 5-15°  (value 2)
// Level 3: > 15°  (value 3)
var slope_class = ee.Image(0)
    .where(slope.lt(5), 1)
    .where(slope.gte(5).and(slope.lte(15)), 2)
    .where(slope.gt(15), 3)
    .rename('class_code');

// 3. Generic statistics function
var computeSlopeStats = function(feature) {
  var geom = feature.geometry();
  
  // --- A. Compute the mean slope (Scalar) ---
  var meanDict = slope.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geom,
    scale: 30,  // strictly use 30m for slope
    maxPixels: 1e9,
    bestEffort: true // allow automatic scale adjustment for very large areas to prevent errors
  });
  
  // --- B. Compute the graded pixel counts (Grouped Count) ---
  // Build the statistics image: band0=count(1), band1=class_code
  var count_img = ee.Image.constant(1).rename('pixel_count').float()
      .addBands(slope_class);
      
  var hist_stats = count_img.reduceRegion({
    reducer: ee.Reducer.sum().group({
      groupField: 1,       // group by slope_class (1,2,3)
      groupName: 'level',
    }),
    geometry: geom,
    scale: 30,             // strictly match the DEM resolution
    maxPixels: 1e9,
    bestEffort: true
  });
  
  var groups_list = ee.List(hist_stats.get('groups'));

  // Set the attributes to return
  return feature.set({
    'fid': feature.get('fid'),       // make sure to keep the ID
    'avg_slope': meanDict.get('slope'), // mean slope
    'slope_hist_json': ee.String.encodeJSON(groups_list) // graded counts JSON
  });
};

// 4. Batch export logic (reusing your previous logic)

var BATCH_SIZE = 2000; // slope computation is faster than LandCover, so the batch can be slightly larger
var total_count = solar_fc.size().getInfo(); 
var num_batches = Math.ceil(total_count / BATCH_SIZE);

print('Total Features:', total_count);
print('Generating ' + num_batches + ' batches for Slope Analysis...');

var solar_list = solar_fc.toList(total_count);

for (var i = 0; i < num_batches; i++) {
  var start_idx = i * BATCH_SIZE;
  var end_idx = start_idx + BATCH_SIZE; 
  
  var batch_fc = ee.FeatureCollection(solar_list.slice(start_idx, end_idx));
  
  // Map the computation function
  var processed_slope = batch_fc.map(computeSlopeStats);
  
  Export.table.toDrive({
    collection: processed_slope,
    description: 'SOLAR_Slope_Stats_Batch_' + (i + 1),
    folder: 'GEE_solar_Analysis_2018_2024', // recommended to use the same folder
    fileFormat: 'CSV',
    selectors: ['fid', 'avg_slope', 'slope_hist_json'] // only export the needed fields
  });
}
