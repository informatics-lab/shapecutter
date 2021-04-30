"""Provider classes for different raster data sources."""

import iris
# import xarray as xr


class _DataProvider(object):
    def __init__(self, data_source):
        self.data_source = data_source

    def __repr__(self):
        raise NotImplemented

    def get_xmax(self):
        """Get the maximum value of the x-axis coordinate."""
        raise NotImplemented

    def get_axis_name(self, axis):
        """Get the name of the coordinate describing a particular axis."""
        raise NotImplemented

    def extract(self, keys):
        """Extract a subset from the dataset based on one or more metadata queries."""
        raise NotImplemented

    def translate(self):
        """'Roll' a dataset along its x-axis - equivalent to cube.intersection."""
        raise NotImplemented


class IrisCubeDataProvider(_DataProvider):
    """Iris Cube data provider."""
    def __init__(self, data_source):
        super().__init__(data_source)


class IrisCubeListDataProvider(_DataProvider):
    """Iris CubeList data provider."""
    def __init__(self, data_source):
        super().__init__(data_source)


class XarrayDataArrayDataProvider(_DataProvider):
    """Xarray DataArray provider."""
    def __init__(self, data_source):
        super().__init__(data_source)


class XarrayDataSetDataProvider(_DataProvider):
    """Xarray DataSet provider."""
    def __init__(self, data_source):
        super().__init__(data_source)


def select_best_data_provider(data_source):
    if isinstance(data_source, iris.cube.Cube):
        provider = IrisCubeDataProvider(data_source)
    elif isinstance(data_source, iris.cube.CubeList):
        provider = IrisCubeListDataProvider(data_source)
    else:
        raise TypeError("No suitable data provider found.")
    return provider
