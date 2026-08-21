// =========================================================================
// Task: verify whether the wind turbines with the given FIDs have land cover data (FROM-GLC10 2017)
// =========================================================================

// 1. Define the FID list to check (1-31)
var target_fids = [];
for (var i = 1; i <= 31; i++) {
  target_fids.push(i);
}

// 2. Data preparation
// -------------------------------------------------------------------------
// !!! Replace this with your actual wind turbine data Asset ID !!!
var wind_fc = ee.FeatureCollection("users/ruiduobao/Wind_Farm_Asset_ID"); 
// -------------------------------------------------------------------------

var from_col = ee.ImageCollection("projects/sat-io/open-datasets/FROM-GLC10");
var from_2017 = from_col.mosaic().rename('class_code');

// 3. Filter the target features
var target_fc = wind_fc.filter(ee.Filter.inList('fid', target_fids));

print('Checking the following FIDs:', target_fids);
print('Number of matched features:', target_fc.size());

// 4. Run the statistical check
var check_results = target_fc.map(function(feat) {
  var fid = feat.get('fid');
  var geom = feat.geometry();
  
  // Try to compute the pixel frequency distribution within the region
  var stats = from_2017.reduceRegion({
    reducer: ee.Reducer.frequencyHistogram(),
    geometry: geom,
    scale: 10,
    maxPixels: 1e9,
    bestEffort: true,
    tileScale: 4
  });
  
  // Get the histogram result; if there is no data, this will be null or an empty dictionary
  var histogram = stats.get('class_code');
  
  return feat.set({
    'check_fid': fid,
    'found_histogram': histogram,
    'has_data': ee.Algorithms.If(histogram, 'YES', 'NO')
  });
});

// 5. Print the results
print('Detailed check results:', check_results.select(['check_fid', 'has_data', 'found_histogram']));

// 6. Visual verification
// Center the map on the first target feature
Map.centerObject(target_fc.first(), 14);

// Load the land cover layer (random colors for easier distinction)
Map.addLayer(from_2017.randomVisualizer(), {}, 'FROM-GLC 2017');

// Load the target wind turbine locations (highlighted in red)
Map.addLayer(target_fc.style({color: 'red', width: 2, fillColor: '00000000'}), {}, 'Target Wind Turbines (FID 1-31)');

// Note:
// If 'found_histogram' in the Console is null or 'has_data' is 'NO',
// and the red polygon area on the map indeed shows no land cover color (possibly transparent/black),
// this confirms that these regions indeed have no data.
