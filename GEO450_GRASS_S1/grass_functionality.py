import sys
from GEO450_GRASS_S1.support_functions import *
from grass_session import Session, get_grass_gisbase
from grass_session import Session
import grass.script as gscript
import grass.script.setup as gsetup
from grass.pygrass.modules import Module


def GRASSBIN_import():
    """
    ...
    :return:
    """
    # general GRASS setup
    # input your Windows path
    grass7bin_win = r'C:/OSGeo4W64/bin/grass79.bat'
    # set your Linux grass version
    grass7bin_lin = GRASS_data.grass_version

    if sys.platform.startswith('linux'):
        # we assume that the GRASS GIS start script is available and in the PATH
        # query GRASS 7 itself for its GISBASE
        grass7bin = grass7bin_lin
    elif sys.platform.startswith('win'):
        grass7bin = grass7bin_win
    return grass7bin


def grass_setup():
    """
    ...
    :return:
    """
    location_name = GRASS_data.location_name
    crs = GRASS_data.crs

    grassbin = GRASSBIN_import()
    os.environ['GRASSBIN'] = grassbin
    gisbase = get_grass_gisbase()
    os.environ['GISBASE'] = gisbase
    sys.path.append(os.path.join(os.environ['GISBASE'], 'bin'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'lib'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'scripts'))
    sys.path.append(os.path.join(os.environ['GISBASE'], 'etc', 'python'))

    # set folder to proj_lib:
    os.environ['PROJ_LIB'] = '/usr/share/proj'

    gisdb = Paths.grass_path
    mapset = "PERMANENT"
    ##################################################################################
    # open a GRASS session and create the mapset if it does not yet exist
    with Session(gisdb=gisdb,
                 location=GRASS_data.location_name,
                 create_opts='EPSG:' + crs) as session:
        pass
    ##################################################################################
    # launch session
    gsetup.init(gisbase, gisdb, location_name, mapset)
    print(f"Current GRASS GIS 7 environment: {gscript.gisenv()}")


def import_shapefile(path_to_shape, overwrite_bool):
    """
    imports the boundary of the area of investigation
    :param path_to_shape: string
        Path to folder, where the shapefile is
    :param overwrite_bool: bool
        Option of True or False, but True is strongly recommended!
    :return:
    """
    ogrimport = Module("v.in.ogr")
    ogrimport(path_to_shape, overwrite=overwrite_bool)


def sen_download(start_time, end_time, sort_by):
    """
    TODO: ADD DOCSTRINGS!!!
    :param start_time:
    :param end_time:
    :param sort_by:
    :return:
    """
    sentineldownload = Module("i.sentinel.download")
    sentineldownload(
        ### Linux folder ###
        settings="/home/user/Desktop/GRASS Jena Workshop/settings.txt",
        output=Paths.send_down_path,
        ### Windows folder ###
        # settings="/home/user/Desktop/GRASS Jena Workshop/settings.txt",
        # output="F:/GEO450_GRASS/Data/sentinel/test_GEO450",
        map="jena_boundary@PERMANENT",
        area_relation="Contains",
        producttype="GRD",
        start=start_time,
        end=end_time,
        sort=sort_by,
        order="asc")


def sen_download_new(start_time, end_time, sort_by, relative_orbit_number):
    """
    TODO: ADD DOCSTRINGS!!!
    :param start_time:
    :param end_time:
    :param sort_by:
    :param relative_orbit_number:
    :return:
    """
    sentineldownload = Module("i.sentinel.download")
    sentineldownload(
        ### Linux folder ###
        settings="/home/user/Desktop/GRASS Jena Workshop/settings.txt",
        output=Paths.send_down_path,
        ### Windows folder ###
        # settings="/home/user/Desktop/GRASS Jena Workshop/settings.txt",
        # output="F:/GEO450_GRASS/Data/sentinel/test_GEO450",
        map="jena_boundary@PERMANENT",
        area_relation="Contains",
        producttype="GRD",
        start=start_time,
        end=end_time,
        sort=sort_by,
        order="desc",
        ### added capability for specific "relativeorbitnumber", needs changes to i.sentinel.download.py first!!! ###
        relativeorbitnumber=relative_orbit_number)


def pyroSAR_processing(start_time, target_resolution, target_CRS, terrain_flat_bool, remove_therm_noise_bool):
    """
    aims at providing a complete solution for the scalable organization and processing of SAR satellite data
    Copyright by John Truckenbrodt
    TODO: ADD DOCSTRINGS!!!
    :param start_time:
    :param target_resolution:
    :param target_CRS:
    :param terrain_flat_bool:
    :param remove_therm_noise_bool:
    :return:
    """
    from datetime import datetime
    from pyroSAR.snap.util import geocode

    sentinel_file_list = extract_files_to_list(Paths.send_down_path, datatype=".zip")
    for l, file in enumerate(sentinel_file_list):
        geocode(infile=file, outdir=Paths.sen_processed_path, tr=target_resolution, t_srs=target_CRS,
                terrainFlattening=terrain_flat_bool, removeS1ThermalNoise=remove_therm_noise_bool)

        interval_time = datetime.now()
        print("file " + str(l + 1) + " of " + str(len(sentinel_file_list) + 1) + " processed in " + str(
            interval_time - start_time) + " Hr:min:sec")
    subset_processed_data()


def subset_import(overwrite_bool, output, polarization_type):
    """
    imports the subsetted raster files into GRASS GIS, renames it into "rasterfile XX" and writes a text file for
    further processing (especially for the creation of a space time cube (see create_stc function below))
    :param overwrite_bool: bool
        Option of True or False, but True is strongly recommended!
    :param output: string
        Output name for every single rasterfile of the space-time-cube
    :param polarization_type: list
        Choice between cross-polarization (VH) and/or co-polarization (VV) -> example: ["VH", "VV"]
    """

    for pol in polarization_type:
        file_list = extract_files_to_list(path_to_folder=Paths.subset_path, datatype=".tif")
        string = "IW___"
        cut_list = []
        for i in file_list:
            if i.__contains__(string):
                cut_list.append(i[i.index(string) + 7:])
        cut_list.sort()

        sub_list = [j for j in file_list if pol in j]
        filelist_path = os.path.join(Paths.main_path, ("sentinel-filelist" + pol + ".txt"))
        for i, tifs in enumerate(sub_list):
            print(tifs)
            sensubsetlimport = Module("r.in.gdal")
            sensubsetlimport(input=tifs,
                             output=output + pol + str(i),
                             memory=500,
                             offset=0,
                             num_digits=0,
                             overwrite=overwrite_bool)

        with open(filelist_path, "w") as f:
            i = -1
            for item in cut_list:
                polarization = pol
                if item.__contains__(pol):
                    i = i + 1
                    f.write(output + pol + str(i) + "|" + item[:4] + "-" +
                            item[4:6] + "-" +
                            item[6:8] + " " +
                            # For minute resolution
                            #item[9:11] + ":" +
                            #item[11:13] +
                            "|" +
                            item[16:18] + "\n")


def create_stc(overwrite_bool, output, polarization_type, stc_info_bool, stc_statistics_bool):
    """
    creates and registers a space time cube for Sentinel time series analysis purposes and shows metadata information
    :param overwrite_bool: bool
        Option of True or False, but True is strongly recommended!
    :param output: string
        Name of the space-time-cube to create & analyze in GRASS GIS
    :param polarization_type: list
        Choice between cross-polarization (VH) and/or co-polarization (VV) -> example: ["VH", "VV"]
    :param stc_info_bool: bool
        Option of True or False, returns temporal and spatial informations about the stc
    :param stc_statistics_bool: bool
        Option of True or False, returns temporal and spatial statistics about every single raster scene of the stc
    :return:
    """
    for pol in polarization_type:
        create_stc = Module("t.create")
        create_stc(overwrite=overwrite_bool,
                   output=output + pol,
                   type="strds",
                   temporaltype="absolute",
                   semantictype="mean",
                   title="stc",
                   description="stc")

        register_stc = Module("t.register")
        register_stc(overwrite=overwrite_bool,
                     input=output + pol,
                     type="raster",
                     file=os.path.join(Paths.main_path, ("sentinel-filelist" + pol + ".txt")),
                     separator="pipe")

        if stc_info_bool == True:
            info_stc = Module("t.info")
            info_stc(input=output + pol, type="strds")

    if stc_statistics_bool == True:
        for pol in polarization_type:
            stc_statistics = Module("t.rast.univar")
            stc_statistics(flags='er',
                    overwrite=True,
                    input=output + pol,
                    separator="pipe")


def visualize_stc(output, polarization_type, stc_animation_bool, stc_timeline_bool):
    """
    visualizes the input space-time-cubes according to user-dependent purposes
    :param output: string
        Name of the space-time-cube to vizualize in GRASS GIS
    :param polarization_type: list
        Choice between cross-polarization (VH) and/or co-polarization (VV) -> example: ["VH", "VV"]
    :param stc_animation_bool: bool
        Option of True or False, animates temporally the space-time-cube with GRASS Animation Tool
    :param stc_timeline_bool: bool
        Option of True or False, returns a timeline plot with all downloaded dates with GRASS Timeline Tool
    :return:
    """
    for pol in polarization_type:
        if stc_animation_bool == True:
            if len(polarization_type) > 1:
                stc_animation = Module("g.gui.animation")
                print("----------------- " + str(polarization_type[0]) + " Time Series Animation" + " -----------------")
                stc_animation(strds=(output + polarization_type[0]))
                print("----------------- " + str(polarization_type[1]) + " Time Series Animation" + " -----------------")
                stc_animation(strds=(output + polarization_type[1]))
            else:
                stc_animation = Module("g.gui.animation")
                print("----------------- " + str(pol) + " Time Series Animation" + " -----------------")
                stc_animation(strds=output+pol)

        if stc_timeline_bool == True:
            print("----------------------- " + "Timeline Plot" + " ----------------------")
            if len(polarization_type) > 1:
                stc_timeline = Module("g.gui.timeline")
                stc_timeline(inputs=(output + polarization_type[0], output + polarization_type[1]))
            else:
                stc_timeline = Module("g.gui.timeline")
                stc_timeline(inputs=(output + pol))


def t_rast_algebra(basename, layername,  expression, overwrite_bool):
    """
    TODO: add docstring and add r.mapcalc
    :param basename:
    :param layername:
    :param expression:
    :param overwrite_bool:
    :return:
    """
    g_list_output(overwrite_bool)
    t_list_output(overwrite_bool)
    acive_strds = open(os.path.join(Paths.main_path, "t_list_output"))
    strds_list = acive_strds.readlines()
    active_raster = open(os.path.join(Paths.main_path, "g_list_output"))
    raster = active_raster.read()
    raster_list = list(raster.split(sep=","))
    for raster in raster_list:
        if basename in raster:
            g_remove(raster_name=raster)
    for strds in strds_list:
        if layername in strds:
            t_remove(strds_name=strds)
    raster_algebra = Module("t.rast.algebra")
    raster_algebra(flags='sng',
                   expression=layername + expression,
                   basename=basename,
                   suffix="num",
                   nprocs=1)


def raster_report(overwrite_bool):
    """
    TODO: DOENST WORK YET!
    :return:
    """
    raster_report = Module("r.report")
    raster_report(overwrite=overwrite_bool,
                  map="product13_0@PERMANENT",
                  units="k",
                  null_value="*",
                  page_length=0,
                  page_width=79,
                  nsteps=10)
