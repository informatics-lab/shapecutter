# shapecutter integration tests

A limited amount of shapecutter testing is provided here in an integration / end-to-end style. One test module is provided per combination of defined geometry and data sources to the `Cutter` class. This currently means that only two modules are provided, for an Iris Cube data source and each of cartopy and geopandas geometry sources:

| Name | Data Source | Geometry Source |
|------|-------------|-----------------|
| test_cube_data_cartopy_geom.py | Iris Cube | Cartopy |
| test_cube_data_gpd_geom.py | Iris Cube | GeoPandas |

## Philosophy

One way or another, the primary output of this library is _visual_: raster data cut to the shape of a geometry. Visual tests are hard to automate and baking test result file into a repo is tedious, so in these tests we offload the visual checks that the library is working as expected to the developer. Sorry, developer.

### Requirements on the developer

In any case, the only thing that needs to be confirmed is:
* The sample geometry overlays the cut raster data

For:
* every integration test module provided here, and
* both visual tests per module:
  * one for a rough geometry bounding box cut, and
  * the other for a more precise cut to the outline of the geometry

As this tests all the primary functionality offered to the user by this library, this should also act as a sufficient implicit test of individual units of functionality provided by the entire library.