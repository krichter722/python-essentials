This project provides and maintaines the following scripts and their shared code (in the `lib` directory):

# osm_postgis_transform.py
`osm_postgis_transform.py` is a wrapper around [osm2pgsql](https://github.com/openstreetmap/osm2pgsql) supporting you with starting and terminating a nested database process for a specified data directory, see `osm_postgis_transform.py --help` for details. It takes all input files accepted by `osm2pgsql` as inputs (see `man osm2pgsql` for details, e.g. gunzipped or extracted .osm files) which can be retrieved for different regions (from the planet to continents, countries down to cities or even arbitrary rectangles), see [http://wiki.openstreetmap.org/wiki/Planet.osm](OpenStreetMap Wiki) for details and download sources. Please note that importing `Planet.osm` (i.e. the complete OSM data) can take several weeks on one strong machine and should be done on a multi-node system after consulting with your system administrator if necessary.

# Installation of prerequisites
Generally if a script `x_prerequisites.py` exists it is necessary to run it in order to be able to run `x.py`. The following prerequisites installation scripts exist:

  * `osm_postgis_transform_prequisites.py`: necessary in order to be able to run `osm_postgis_transform.py`

