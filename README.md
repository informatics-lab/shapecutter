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

## Testing

See the [testing README](https://github.com/informatics-lab/shapecutter/blob/main/shapecutter/tests/integration/README.md) for more details.
