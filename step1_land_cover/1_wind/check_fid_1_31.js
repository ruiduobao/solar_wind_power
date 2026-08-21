// =========================================================================
// 任务：验证指定 FID 的风机是否存在土地覆盖数据 (FROM-GLC10 2017)
// =========================================================================

// 1. 定义要检查的 FID 列表 (1-31)
var target_fids = [];
for (var i = 1; i <= 31; i++) {
  target_fids.push(i);
}

// 2. 数据准备
// -------------------------------------------------------------------------
// !!! 请将此处替换为您实际的风机数据 Asset ID !!!
var wind_fc = ee.FeatureCollection("users/ruiduobao/Wind_Farm_Asset_ID"); 
// -------------------------------------------------------------------------

var from_col = ee.ImageCollection("projects/sat-io/open-datasets/FROM-GLC10");
var from_2017 = from_col.mosaic().rename('class_code');

// 3. 筛选目标 Feature
var target_fc = wind_fc.filter(ee.Filter.inList('fid', target_fids));

print('正在检查以下 FID:', target_fids);
print('找到对应要素数量:', target_fc.size());

// 4. 执行统计检查
var check_results = target_fc.map(function(feat) {
  var fid = feat.get('fid');
  var geom = feat.geometry();
  
  // 尝试计算区域内的像素频率分布
  var stats = from_2017.reduceRegion({
    reducer: ee.Reducer.frequencyHistogram(),
    geometry: geom,
    scale: 10,
    maxPixels: 1e9,
    bestEffort: true,
    tileScale: 4
  });
  
  // 获取直方图结果，如果没有数据，这里会是 null 或者空字典
  var histogram = stats.get('class_code');
  
  return feat.set({
    'check_fid': fid,
    'found_histogram': histogram,
    'has_data': ee.Algorithms.If(histogram, 'YES', 'NO')
  });
});

// 5. 打印结果
print('详细检查结果:', check_results.select(['check_fid', 'has_data', 'found_histogram']));

// 6. 可视化验证
// 将地图中心定位到第一个目标要素
Map.centerObject(target_fc.first(), 14);

// 加载土地覆盖图层 (随机配色以便区分)
Map.addLayer(from_2017.randomVisualizer(), {}, 'FROM-GLC 2017');

// 加载目标风机位置 (红色高亮)
Map.addLayer(target_fc.style({color: 'red', width: 2, fillColor: '00000000'}), {}, 'Target Wind Turbines (FID 1-31)');

// 提示：
// 如果 Console 中的 'found_histogram' 为 null 或 'has_data' 为 'NO'，
// 且地图上看到红框区域确实没有土地覆盖颜色（可能是透明/黑色），
// 则证实了这些区域确实没有数据。
