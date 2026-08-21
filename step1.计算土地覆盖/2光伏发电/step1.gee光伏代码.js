var solar_fc = ee.FeatureCollection("projects/nice-unison-474714-v5/assets/solarpower");
// =========================================================================
// SOLAR ANALYSIS: Dynamic Baseline (Year-1) vs Installation Year
// =========================================================================

// 1. Data preparation

var dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1");

// 2. Core extraction function
var computeSolarTransition = function(feature) {
  // Read the truncated field name 'constructi'
  var install_year = ee.Number(feature.get('constructi'));
  var is_early = install_year.lte(2017);
  
  // --- Step A: Build the Pre image ---
  var img_pre;
  
  // Early case (2015-2016)
  var early_mosaic = dw.filterDate('2015-06-27', '2016-12-31')
                       .sort('system:time_start', false)
                       .select('label').mosaic();
                       
  // Normal case (Year - 1)
  var normal_year = install_year.subtract(1);
  var normal_mosaic = dw.filterDate(
      ee.Date.fromYMD(normal_year, 1, 1), 
      ee.Date.fromYMD(normal_year, 12, 31)
    ).select('label').mosaic();
  
  img_pre = ee.Image(ee.Algorithms.If(is_early, early_mosaic, normal_mosaic));
  
  // --- Step B: Build the Post image (installation year) ---
  var post_mosaic = dw.filterDate(
      ee.Date.fromYMD(install_year, 1, 1), 
      ee.Date.fromYMD(install_year, 12, 31)
    ).select('label').mosaic();
    
  // --- Step C: Transition matrix and area ---
  var transition = img_pre.multiply(100).add(post_mosaic).rename('code');
  var combined = ee.Image.pixelArea().addBands(transition);
  
  var stats = combined.reduceRegion({
    reducer: ee.Reducer.sum().group({
      groupField: 1, 
      groupName: 'code',
    }),
    geometry: feature.geometry(),
    scale: 10,
    maxPixels: 1e9,
    tileScale: 4,
    bestEffort: true
  });
  
  var groups_list = ee.List(stats.get('groups'));
  
  return feature.set({
    'stats_json': ee.String.encodeJSON(groups_list),
    'type': 'solar',
    // Rename the read constructi uniformly to installation_year for output
    'installation_year': install_year 
  });
};

// 3. Batch export logic
var BATCH_SIZE = 5000;
// Filter out features with empty year (using the constructi field)
var solar_valid = solar_fc.filter(ee.Filter.notNull(['constructi']));
var total_count = solar_valid.size().getInfo();
var num_batches = Math.ceil(total_count / BATCH_SIZE);

print('Total Solar Polygons:', total_count);
print('Generating ' + num_batches + ' export tasks...');

var solar_list = solar_valid.toList(total_count);

for (var i = 0; i < num_batches; i++) {
  var start_idx = i * BATCH_SIZE;
  var end_idx = start_idx + BATCH_SIZE; 
  
  var batch_fc = ee.FeatureCollection(solar_list.slice(start_idx, end_idx));
  var processed_batch = batch_fc.map(computeSolarTransition);
  
  Export.table.toDrive({
    collection: processed_batch,
    description: 'Solar_Analysis_Batch_' + (i + 1),
    folder: 'GEE_Solar_Analysis',
    fileFormat: 'CSV',
    // === Key change: add 'fid' and output the standard 'installation_year' ===
    selectors: ['fid', 'stats_json', 'type', 'installation_year', 'country_iso_a3']
  });
}
