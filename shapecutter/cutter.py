"""Cut gridded raster datasets to shapely geometries."""

import numpy as np
from shapely.geometry import box

from .providers import select_best_data_provider, select_best_geometry_provider


def _get_2d_field_and_dims(cube):
    """Get a 2D horizontal field, and the horizontal coord dims, from an nD cube."""
    # XXX for the cube data provider eventually?
    cube_x_coord, = cube.coords(axis='X', dim_coords=True)
    cube_y_coord, = cube.coords(axis='Y', dim_coords=True)
    cube_x_coord_name = cube_x_coord.name()
    cube_y_coord_name = cube_y_coord.name()
    cube_x_coord_dim, = cube.coord_dims(cube_x_coord)
    cube_y_coord_dim, = cube.coord_dims(cube_y_coord)
    field_2d = cube.slices([cube_y_coord_name, cube_x_coord_name]).next()
    coord_2d_dims = sorted([cube_y_coord_dim, cube_x_coord_dim])
    return field_2d, coord_2d_dims


def _dateline_centre(max_x):
    """
    Determine if the dateline is at the centre of the horizontal coord system.
    If it is, the interval of the x coord is (0, 360)deg.       --> result: True
    If it isn't, the interval of the x coord is (-180, 180)deg. --> result: False
    
    """
    return max_x > 180


class Cutter(object):
    """Cut raster data around a shapely geometry."""
    def __init__(self, data_source, geometry_source,
                 ignore_errors=True):
        """
        Set up a cutter to cut data out of `data_source` from geometries
        provided by `geometry_source`.

        """
        self.data_source = data_source
        self.geometry_source = geometry_source
        self.ignore_errors = ignore_errors

        # TODO: fully implement.
        self.data_provider = select_best_data_provider(data_source)
        self.geometry_provider = select_best_geometry_provider(geometry_source)

    def _translate_to_geometry(self, geometry_ref):
        """Translate the x-coord of a dataset to match the x-coord interval of the geometry."""
        geom_xmax = self.geometry_provider.get_named_bound(geometry_ref, 'maxx')
        xc_name = self.data_provider.coords(axis="x", dim_coords=True)[0].name()
        cube_xmax = self.data_provider.coord(xc_name).points[-1]
        geom_x_dateline_centre = _dateline_centre(geom_xmax)
        cube_x_dateline_centre = _dateline_centre(cube_xmax)

        if geom_x_dateline_centre != cube_x_dateline_centre:
            if cube_x_dateline_centre:
                translation_kwarg = {xc_name: (-180, 180)}
            else:
                translation_kwarg = {xc_name: (0, 360)}
            self.data_provider.translate(translation_kwarg)

    def geometry_bbox_dataset(self, geometry_ref):
        """
        Extract a subset from a cube at the extent of the bounding box
        of the geometry.

        XXX not done: CRS handling.

        """
        self._translate_to_geometry(geometry_ref)

        xc_name = self.data_provider.coords(axis="x", dim_coords=True)[0].name()
        yc_name = self.data_provider.coords(axis="y", dim_coords=True)[0].name()

        min_x, min_y, max_x, max_y = self.geometry_provider.get_bounds_points(geometry_ref)

        coord_values = {xc_name: lambda cell: min_x <= cell <= max_x,
                        yc_name: lambda cell: min_y <= cell <= max_y}
        return self.data_provider.extract(coord_values)

    def geometry_boundary_mask(self, dataset, geometry_ref):
        """
        Generate a 2D horizontal mask for the dataset based on the boundary
        of the geometry.

        Note: the geometry is assumed to be provided by a geodataframe.

        TODO: cache boundary masks for specific geometries.

        """
        # self._translate_to_geometry(dataset, geometry_ref)

        x_coord = dataset.coords(axis="x", dim_coords=True)[0]
        y_coord = dataset.coords(axis="y", dim_coords=True)[0]

        # XXX this may be improvable: perhaps by iterating over cells in a 2D slice directly?
        geometry = self.geometry_provider[geometry_ref]
        x_shape, = x_coord.shape
        y_shape, = y_coord.shape
        x_points, y_points = np.meshgrid(np.arange(x_shape), np.arange(y_shape))
        flat_mask = []
        for (xi, yi) in zip(x_points.reshape(-1), y_points.reshape(-1)):
            x_lo, x_hi = x_coord[xi].bounds[0]
            y_lo, y_hi = y_coord[yi].bounds[0]
            cell = box(x_lo, y_lo, x_hi, y_hi)
            mask_point = geometry.intersects(cell)
            flat_mask.append(mask_point)

        return np.array(flat_mask).reshape(dataset.shape[-2:])

    def _cut_to_boundary(self, subset, geometry_ref):
        """Mask `subset` tightly to the geometry of the polygon."""
        try:
            _, dims_2d = _get_2d_field_and_dims(subset)
            mask_2d = self.geometry_boundary_mask(subset, geometry_ref)
        except:
            if self.ignore_errors:
                result = None
            else:
                raise
        else:
            result = self.data_provider.apply_mask(subset, mask_2d, dims_2d)
        return result

    def cut_dataset(self, geometry_ref, to="bbox"):
        """
        Subset the input cube to the boundary of the shapefile geometry.

        This is a two-step process:
        1. Cut the cube to the bounding box of the shapefile geoetry
        2. (optional, only if `to` == "boundary")
           Mask the cut cube from (1.) to the boundary of the shapefile geometry.

        This two-step process is *much* faster than going directly to masking, as
        far fewer cells are compared to the geometry in step (2) this way.

        """
        # 1. extract subset to the shapefile's bounding box.
        subset = self.geometry_bbox_dataset(geometry_ref)

        if to == "bbox":
            result = subset
        elif to == "boundary":
            # 2. mask the subset to the shapefile boundary.
            # XXX cache the boundary cutting?
            result = self._cut_to_boundary(subset, geometry_ref)
        else:
            emsg = f"`to` must be one of ['bbox', 'boundary'], got {to}."
            raise ValueError(emsg)

        return result