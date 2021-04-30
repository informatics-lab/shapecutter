"""Cut Iris cubes to shapely geometries."""

import numpy as np

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
    def __init__(self, data_source, geometry_source):
        """
        Set up a cutter to cut data out of `data_source` from geometries
        provided by `geometry_source`.

        """
        self.data_source = data_source
        self.geometry_source = geometry_source

        # TODO: fully implement.
        # self.data_provider = select_best_data_provider(data_source)
        self.geometry_provider = select_best_geometry_provider(geometry_source)

    def _translate_cube_to_geometry(self, geometry_ref):
        """Translate the x-coord of a cube to match the x-coord interval of the geometry."""
        geom_xmax = self.geometry_provider.get_named_bound(geometry_ref, 'maxx')
        xc_name = self.data_source.coords(axis="x", dim_coords=True)[0].name()
        cube_xmax = self.data_source.coord(xc_name).points[-1]
        geom_x_dateline_centre = _dateline_centre(geom_xmax)
        cube_x_dateline_centre = _dateline_centre(cube_xmax)

        if geom_x_dateline_centre != cube_x_dateline_centre:
            if cube_x_dateline_centre:
                intersection_kwarg = {xc_name: (-180, 180)}
            else:
                intersection_kwarg = {xc_name: (0, 360)}
            result = self.data_source.intersection(**intersection_kwarg)

        return result

    def geometry_bbox_dataset(self, geometry_ref):
        """
        Extract a subset from a cube at the extent of the bounding box
        of the geometry.

        XXX not done: CRS handling.

        """
        cube = self._translate_cube_to_geometry(geometry_ref)

        xc_name = cube.coords(axis="x", dim_coords=True)[0].name()
        yc_name = cube.coords(axis="y", dim_coords=True)[0].name()

        min_x, min_y, max_x, max_y = self.geometry_provider.get_bounds_points(geometry_ref)

        coord_values = {xc_name: lambda cell: min_x <= cell <= max_x,
                        yc_name: lambda cell: min_y <= cell <= max_y}
        cstr = iris.Constraint(coord_values=coord_values)
        return cube.extract(cstr)

    def geometry_boundary_mask(self, dataset, geometry_ref):
        """
        Generate a 2D horizontal mask for the cube based on the boundary
        of the geometry.

        Note: the geometry is assumed to be provided by a geodataframe.

        TODO: cache boundary masks for specific geometries.

        """
        cube = self._translate_cube_to_geometry(dataset, geometry_ref)

        x_coord = cube.coords(axis="x", dim_coords=True)[0]
        y_coord = cube.coords(axis="y", dim_coords=True)[0]
        
        for coord in [x_coord, y_coord]:
            if not coord.has_bounds():
                coord.guess_bounds()

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

        mask_2d = np.array(flat_mask).reshape(cube.shape[-2:])
        return mask_2d

    def _cut_to_boundary(self, subset, geometry_ref):
        """Mask `subset` tightly to the geometry of the polygon."""
        try:
            cube_2d, dims_2d = _get_2d_field_and_dims(subset)
            mask_2d = geometry_boundary_mask(subset, geometry_ref)
        except:
            result = None
        else:
            full_mask = iris.util.broadcast_to_shape(mask_2d, subset.shape, dims_2d)
            new_data = np.ma.array(subset.data, mask=np.logical_not(full_mask))
            result = subset.copy(data=new_data)
        return result

    def cut_cube(self, geometry_ref, to="bbox"):
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