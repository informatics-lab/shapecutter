# shapecutter
Cut data out of raster arrays based on Shapely Polygons


## Install

Download the source or clone from GitHub, navigate to the downloaded source then use pip to run the local setup script directly:

```bash
cd shapecutter
pip install -e .
```

**Note:** this will install dependencies from pip. During testing there were some issues installing Cartopy 0.19.0 from pip. To work around this you might be better pre-installing the dependencies directly, for example by using conda:

```bash
conda create -n shapecutter -c conda-forge iris shapely geopandas
conda activate shapecutter
```

And then install shapecutter, as above.

## Usage

Shapecutter takes a gridded data source and a geometry source and returns a new dataset that is the result of cutting data out of the data source that intersects with a specified geometry in the geometry source. Two levels of cutting are provided:
1. `"bbox"` (coarse cutting): the data source is subset so that only data points that intersect (are contained by) the bounding box of the selected geometry are returned
1. `"boundary"` (fine cutting): data points that directly intersect with the selected geometry (and within the geometry's bounding box) are returned. To maintain a gridded dataset, this is implemented by masking points returned in (1.) that do not intersect the geometry.

### Cartopy and GeoPandas examples

With cartopy or GeoPandas providing a 

An example of cutting a gridded data source to a geometry provided by `cartopy`:

```python
import cartopy.io.shapereader as shpreader
import iris
import shapecutter

data_source = iris.load_cube("my_dataset.nc")
geom_source = shpreader.Reader("my_shapefile.shp")
geom_ref = "devon"  # Select a geometry from the name of a record in `geom_source`.

cutter = shapecutter.Cutter(data_source, geom_source)
# 1. coarse cutting:
bbox_cut_result = cutter.cut_dataset(geom_ref)
# 2. fine cutting:
fine_cut_result = cutter.cut_dataset(geom_ref, to="boundary")
```

An example of cutting a gridded data source to a geometry provided by `GeoPandas`:

```python
import geopandas as gpd
import iris
import shapecutter

data_source = iris.load_cube("my_dataset.nc")
geom_source = gpd.read_file("my_shapefile.shp")
geom_ref = "devon"  # Select a geometry from the name of a record in `geom_source`.

cutter = shapecutter.Cutter(data_source, geom_source)
# 1. coarse cutting:
bbox_cut_result = cutter.cut_dataset(geom_ref)
# 2. fine cutting:
fine_cut_result = cutter.cut_dataset(geom_ref, to="boundary")
```

Note that you can also pass the shapefile source directly to the `Cutter` class and let `shapecutter` load your geometry source for you:

```python
cutter = shapecutter.Cutter(data_source, "my_shapefile.shp")
```

### Shapely geometry source

If you have just a Shapely geometry instance (for example, one that you have manually constructed from a list of points), you can utilise the geometry directly. Note that in this case there is no records metadata available (it's just the single geometry) so we just supply an empty string as the geometry reference when cutting the data source to the Shapely geometry:

```python
import iris
import shapecutter
from shapely.geometry import Polygon

data_source = iris.load_cube("my_dataset.nc")
data_points = [...]
my_polygon = Polygon(data_points)

cutter = shapecutter.Cutter(data_source, my_polygon)
# 1. coarse cutting:
bbox_cut_result = cutter.cut_dataset("")
# 2. fine cutting:
fine_cut_result = cutter.cut_dataset("", to="boundary")
```


## Testing

See the [testing README](https://github.com/informatics-lab/shapecutter/blob/main/shapecutter/tests/integration/README.md) for more details.
