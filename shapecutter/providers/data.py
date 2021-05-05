"""Provider classes for different raster data sources."""

import warnings

import iris
import numpy as np
# import xarray as xr


class _DataProvider(object):
    def __init__(self, data_source):
        self.data_source = data_source

    def __repr__(self):
        raise NotImplemented

    def __getattr__(self, attr):
        return getattr(self.data_source, attr)

    def get_xmax(self):
        """Get the maximum value of the x-axis coordinate."""
        raise NotImplemented

    def get_axis_name(self, axis):
        """Get the name of the coordinate describing a particular axis."""
        raise NotImplemented

    def extract(self, keys):
        """Extract a other from the dataset based on one or more metadata queries."""
        raise NotImplemented

    def translate(self):
        """'Roll' a dataset *in-place* along its x-axis - equivalent to cube.intersection."""
        raise NotImplemented

    def apply_mask(self, other, mask_2d, dims_2d):
        """
        Apply a 2D horizontal mask to an entire dataset by broadcasting it to the
        shape of the whole dataset.

        """
        raise NotImplemented


class IrisCubeDataProvider(_DataProvider):
    """Iris Cube data provider."""
    def __init__(self, data_source):
        super().__init__(data_source)
        self._confirm_bounds()

    def _confirm_bounds(self):
        """Ensure the cube data source has bounds set for horizontal coords."""
        x_coord, = self.data_source.coords(axis="x", dim_coords=True)
        y_coord, = self.data_source.coords(axis="y", dim_coords=True)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for coord in [x_coord, y_coord]:
                coord.guess_bounds()

    def extract(self, keys):
        cstr = iris.Constraint(coord_values=keys)
        return self.data_source.extract(cstr)

    def translate(self, translate_kwarg):
        self.data_source = self.data_source.intersection(**translate_kwarg)

    def apply_mask(self, other, mask_2d, dims_2d):
        print(f"[apply_mask] - Other shape: {other.shape}, mask_shape: {mask_2d.shape}")
        full_mask = iris.util.broadcast_to_shape(mask_2d, other.shape, dims_2d)
        new_data = np.ma.array(other.data, mask=np.logical_not(full_mask))
        return other.copy(data=new_data)


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
