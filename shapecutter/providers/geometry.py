"""Provider classes for different pythonic representations of shapely geometries."""

import cartopy.io.shapereader as shpreader
import geopandas as gpd


class _GeometryProvider(object):
    def __init__(self, geometry_source):
        self._geometry_source = geometry_source

    @property
    def geometry_source(self):
        if isinstance(self._geometry_source, str):
            # Try loading the string to make a geometry source.
            self.load(self._geometry_source)
        return self._geometry_source

    @geometry_source.setter
    def geometry_source(self, value):
        self._geometry_source = value

    def _handle_geometry_ref(self, ref):
        if isinstance(ref, dict):
            ref = list(ref.items())
        return ref[0], ref[1]

    def __repr__(self):
        raise NotImplemented

    def __getitem__(self, keys):
        raise NotImplemented

    def __getattr__(self, attr):
        return getattr(self.geometry_source, attr)

    def load(self, source):
        raise NotImplemented

    def get_bounds(self, geometry_ref):
        return self[geometry_ref].bounds

    def get_bounds_points(self, geometry_ref):
        """Get the four points [x_min, y_min, x_max, y_max] of a geometry's bounds."""
        return NotImplemented

    def get_named_bound(self, geometry_ref, bound_ref):
        """Get a named bound, for example the x-max ("maxx") bound."""
        raise NotImplemented


class CartopyGeometryProvider(_GeometryProvider):
    """Cartopy geometry provider."""
    def __init__(self, geometry_source):
        super().__init__(geometry_source)
        self._rcds = list(self.geometry_source.records())
        self._geom_lookup = {}
        self._names = ["minx", "miny", "maxx", "maxy"]  # Follows geopandas bounds names.
        self._named_bounds = {n: self._names.index(n) for n in self._names}

    def __repr__(self):
        t = self.__class__.__name__
        l = len(self._rcds)
        repr_str = f"{t} containing {l} geometries in a Cartopy FionaReader store."
        return repr_str

    def __getitem__(self, keys):
        query_key, query_val = self._handle_geometry_ref(key)
        geom_uid = f"{query_key},{query_val}"
        if geom_uid not in self._geom_lookup.keys():
            for rcd in self.geometry_source.records():
                if rcd.attributes[query_key] == query_val:
                    self._geom_lookup[geom_uid] = rcd.geometry
                    break
        return self._geom_lookup[geom_uid]

    def load(self, source):
        self.geometry_source = shpreader.Reader(source)

    def get_bounds_points(self, geometry_ref):
        """Cartopy's shapereader already returns points in this form."""
        return self.get_bounds(geometry_ref)

    def get_named_bound(self, geometry_ref, bound_ref):
        bounds = self.get_bounds(geometry_ref)
        try:
            bound_idx = self._named_bounds[bound_ref]
        except KeyError:
            emsg = f"Expected `bound_ref` to be one of {self._names}, got {bound_ref!r}."
            raise ValueError(emsg)
        return bounds[bound_idx]


class GeoPandasGeometryProvider(_GeometryProvider):
    """GeoPandas geometry provider."""
    def __init__(self, geometry_source):
        super().__init__(geometry_source)

    def __repr__(self):
        t = self.__class__.__name__
        l = len(self.geometry_source)
        repr_str = f"{t} containing {l} geometries in a GeoPandas GeoDataFrame."
        return repr_str

    def __getitem__(self, key):
        query_key, query_val = self._handle_geometry_ref(key)
        result_row = self.geometry_source[self.geometry_source[query_key] == query_val]
        return result_row.geometry

    def load(self, source):
        self.geometry_source = gpd.read_file(source)

    def get_bounds_points(self, geometry_ref):
        """GPD bounds are provided as a geodataframe, so we need to work to get the points."""
        bounds = self.get_bounds(geometry_ref)
        return bounds.loc[bounds.index[0]]

    def get_named_bound(self, geometry_ref, bound_ref):
        bounds = self.get_bounds(geometry_ref)
        return bounds.loc[bounds.index[0]][bound_ref]


def select_best_geometry_provider(geometry_source):
    if isinstance(geometry_source, shpreader.FionaReader):
        provider = CartopyGeometryProvider(geometry_source)
    elif isinstance(geometry_source, (gpd.geodataframe.GeoDataFrame, str)):
        provider = GeoPandasGeometryProvider(geometry_source)
    else:
        raise TypeError("No suitable geometry provider found.")
    return provider
