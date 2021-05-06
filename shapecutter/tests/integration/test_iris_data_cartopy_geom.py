"""
Test shapecutter with:
  * data source: Iris Cube
  * geometry source: Cartopy Shapereader

"""

import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import iris
import iris.quickplot as qplt
import matplotlib.pyplot as plt

from shapecutter.cutter import Cutter


def plot(dataset, geometry):
    ax = plt.axes(projection=ccrs.LambertConformal())
    ax.coastlines()
    qplt.pcolormesh(dataset[0])
    ax.add_geometries([geometry],
                      crs=ccrs.PlateCarree(), facecolor="none", edgecolor='r')
    plt.show()


def main(state_name):
    # Load raster data and geometries, and define geometry selection keys.
    a1b_cube = iris.load_cube(iris.sample_data_path("a1b_north_america.nc"))
    us_states_name = shpreader.natural_earth(
        category="cultural",
        name="admin_1_states_provinces")
    us_states = shpreader.Reader(us_states_name)
    geometry_keys = {"name": state_name}

    # Construct a Cutter instance to test and extract the target geometry for plotting.
    cutter = Cutter(a1b_cube, us_states, ignore_errors=False)
    tgt_geometry = cutter.geometry_provider[geometry_keys]

    # Test 1: cut to geometry bbox and plot for visual check.
    bbox_cube = cutter.cut_dataset(geometry_keys)
    plot(bbox_cube, tgt_geometry)

    # Test 2: cut to geometry boundary and plot for visual check.
    boundary_cube = cutter.cut_dataset(geometry_keys, to="boundary")
    plot(boundary_cube, tgt_geometry)


if __name__ == '__main__':
    state_name = "Indiana"
    main(state_name)
