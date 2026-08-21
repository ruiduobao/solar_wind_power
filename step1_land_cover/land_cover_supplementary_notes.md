Dynamic World is a 10m near-real-time (NRT) Land Use/Land Cover (LULC) dataset that includes class probabilities and label information for nine classes.

Dynamic World predictions are available for the Sentinel-2 L1C collection from 2015-06-27 to present. The revisit frequency of Sentinel-2 is between 2-5 days depending on latitude. Dynamic World predictions are generated for Sentinel-2 L1C images with CLOUDY_PIXEL_PERCENTAGE <= 35%. Predictions are masked to remove clouds and cloud shadows using a combination of S2 Cloud Probability, Cloud Displacement Index, and Directional Distance Transform.

Images in the Dynamic World collection have names matching the individual Sentinel-2 L1C asset names from which they were derived, e.g:

ee.Image('COPERNICUS/S2/20160711T084022_20160711T084751_T35PKT')

has a matching Dynamic World image named: ee.Image('GOOGLE/DYNAMICWORLD/V1/20160711T084022_20160711T084751_T35PKT').

All probability bands except the "label" band collectively sum to 1.

To learn more about the Dynamic World dataset and see examples for generating composites, calculating regional statistics, and working with the time series, see the Introduction to Dynamic World tutorial series.

Given Dynamic World class estimations are derived from single images using a spatial context from a small moving window, top-1 "probabilities" for predicted land covers that are in-part defined by cover over time, like crops, can be comparatively low in the absence of obvious distinguishing features. High-return surfaces in arid climates, sand, sunglint, etc may also exhibit this phenomenon.

To select only pixels that confidently belong to a Dynamic World class, it is recommended to mask Dynamic World outputs by thresholding the estimated "probability" of the top-1 prediction.

Name	Description	Min	Max
water	
Estimated probability of complete coverage by water

0	1
trees	
Estimated probability of complete coverage by trees

0	1
grass	
Estimated probability of complete coverage by grass

0	1
flooded_vegetation	
Estimated probability of complete coverage by flooded vegetation

0	1
crops	
Estimated probability of complete coverage by crops

0	1
shrub_and_scrub	
Estimated probability of complete coverage by shrub and scrub

0	1
built	
Estimated probability of complete coverage by built

0	1
bare	
Estimated probability of complete coverage by bare

0	1
snow_and_ice	
Estimated probability of complete coverage by snow and ice

0	1
label	
Index of the band with the highest estimated probability

0	8

Image Properties
Name	Type	Description
dynamicworld_algorithm_version	String	
The version string uniquely identifying the Dynamic World model and inference process used to produce the image.

qa_algorithm_version	String	
The version string uniquely identifying the cloud masking process used to produce the image.