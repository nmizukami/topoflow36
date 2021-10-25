#   
#  Copyright (c) 2020, Scott D. Peckham
#
#  Note: This file contains a set of functions for visualizing the
#        contents of output files in netCDF format
#        (e.g. TopoFlow or Stochastic Conflict Model)
#
#  Oct 2021.  create_visualization_files().
#  Sep 2021.  Added LAND_SEA_BACKDROP option: show_grid_as_image() 
#  May 2020.  Moved all routines from Jupyter notebook called
#             TopoFlow_Visualization.ipynb to here.
#             Tested all of them in the Jupyter notebook.
#
#--------------------------------------------------------------------
#
#  Define some stretch functions for 2D color images:
#  normalize_grid()
#  histogram_equalize()
#  power_stretch0()
#  power_stretch1()
#  power_stretch2()
#  power_stretch3()
#  log_stretch()
#  linear_stretch()
#  stretch_grid()
#
#  Define functions to show grids as color images:
#  read_grid_from_nc_file()
#  read_and_show_rtg()
#  show_grid_as_image()
#  save_grid_stack_as_images()
#  save_rts_as_images()
#
#  Define some plotting functions:
#  plot_time_series()
#  plot_z_profile()
#  save_profile_series_as_images()
#
#  Create movies from set of images:
#     (works for grid images, profile images, etc.)
#  create_movie_from_images()
#
#  From Richards 1D Equation Jupyter notebook
#  plot_data()
#  plot_soil_profile()
#
#  Next function will be called from a Dojo Docker container
#      after topoflow_driver.finalize() to create images
#      and movies from netCDF output files.
#
#  create_visualization_files()    2021-10
#  delete_png_files()              2021-10
#
#--------------------------------------------------------------------
# import os.path
# import shutil

import glob, os, os.path
import numpy as np

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap
import imageio

from topoflow.utils import ncgs_files
from topoflow.utils import ncts_files
from topoflow.utils import ncps_files
from topoflow.utils import rtg_files
from topoflow.utils import rts_files

#--------------------------------------------------------------------
def normalize_grid( grid ): 

    gmin = grid.min()
    gmax = grid.max()

    if (gmin != gmax):
        norm = (grid - gmin) / (gmax - gmin)
    else:
        # Avoid divide by zero
        norm = np.zeros( grid.shape, dtype=grid.dtype )
    return norm

#   normalize_grid()
#--------------------------------------------------------------------
def histogram_equalize( grid, PLOT_NCS=False):

    #  https://docs.scipy.org/doc/numpy/reference/generated/numpy.histogram.html
    (hist, bin_edges) = np.histogram( grid, bins=256)
    # hmin = hist.min()
    # hmax = hist.max()

    cs  = hist.cumsum()
    ncs = (cs - cs.min()) / (cs.max() - cs.min())
    ncs.astype('uint8');
    ############## ncs.astype('uint8') # no semi-colon at end ??????????
    if (PLOT_NCS):
        plt.plot( ncs )

    flat = grid.flatten()
    flat2 = np.uint8( 255 * (flat - flat.min()) / (flat.max() - flat.min()) )
    grid2 = ncs[ flat2 ].reshape( grid.shape )
    return grid2

#   histogram_equalize()
#--------------------------------------------------------------------
def power_stretch0( grid, p ):

    norm = normalize_grid( grid )
    
    return norm**p
    
#   power_stretch0()
#--------------------------------------------------------------------
def power_stretch1( grid, p ):
    return grid**p
    
#   power_stretch1()
#--------------------------------------------------------------------
def power_stretch2( grid, a=1000, b=0.5):

    # Note: Try a=1000 and b=0.5
    norm = normalize_grid( grid )
    return (1 - (1 + a * norm)**(-b))
    
#   power_stretch2()
#--------------------------------------------------------------------
def power_stretch3( grid, a=1, b=2):

    # Note:  Try a=1, b=2 (shape of a quarter circle)
    norm = normalize_grid( grid )
    return (1 - (1 - norm**a)**b)**(1/b)
    
#   power_stretch3()
#--------------------------------------------------------------------
def log_stretch( grid, a=1 ):
    return np.log( (a * grid) + 1 )
    
#   log_stretch()
#--------------------------------------------------------------------
def linear_stretch( grid ):

    norm = normalize_grid( grid )
    return norm
   
#   linear_stretch()
#--------------------------------------------------------------------
def stretch_grid( grid, stretch, a=1, b=2, p=0.5 ):

    name = stretch
    if   (name == 'hist_equal'):
        grid2 = histogram_equalize( grid, PLOT_NCS=False)    
    elif (name == 'linear'):
        grid2 = linear_stretch(grid)
    elif (name == 'log'):
        grid2 = log_stretch( grid, a=a )
    elif (name == 'power'):
        grid2 = power_stretch0( grid, p=p )
    elif (name == 'power1'): 
        # Try:  p = 0.3   
        grid2 = power_stretch1( grid, p)
    elif (name == 'power2'):
        # Try:  a=1000, b=0.5.
        grid2 = power_stretch2( grid, a=a, b=b )
    elif (name == 'power3'):        
        # Try:  a=1, b=2.
        grid2 = power_stretch3( grid, a=a, b=b)
    else:
        print('### SORRY, Unknown stretch =', name)
        return grid

    return grid2
 
#   stretch_grid()
#--------------------------------------------------------------------
#--------------------------------------------------------------------
def read_grid_from_nc_file( nc_file, time_index=1, REPORT=True ):

    # Typical 2D nc files
    # nc_file = case_prefix + '_2D-Q.nc'
    # nc_file = case_prefix + '_2D-d-flood.nc'

    if ('_2D' not in nc_file):
        print('ERROR: This function is only for TopoFlow "2D" files.') 
        return
            
    ncgs = ncgs_files.ncgs_file()
    ncgs.open_file( nc_file )
    var_name_list = ncgs.get_var_names()
    if (REPORT):
        print('var_names in netCDF file =' )
        print( var_name_list )

    #----------------------------         
    # Determine valid var_index
    #-----------------------------------------
    # Old: 0=time, 1=X, 2=Y, 3=V
    # New: 0=time, 1=datetime, 2=X, 3=Y, 4=V
    #-----------------------------------------
    var_index = 1
    other_vars = ['time','datetime','X','Y','Z']
    while (True):
        var_name = var_name_list[ var_index ]
        if (var_name not in other_vars):
            break
        var_index += 1    
    ### var_index = 3   # 0=time, 1=X, 2=Y, 3=V  ###############
    ### var_name  = var_name_list[ var_index ]
    long_name = ncgs.get_var_long_name( var_name )
    var_units = ncgs.get_var_units( var_name )
    n_grids   = ncgs.ncgs_unit.variables[ var_name ].n_grids

    if (REPORT):
        print('long_name =', long_name)
        print('var_name  =', var_name)
        print('var_units =', var_units)
        print('n_grids   =', n_grids)

    #--------------------------------------------
    # Use these to set "extent" in plt.imshow()
    #--------------------------------------------
    minlon = ncgs.ncgs_unit.variables['X'].geospatial_lon_min
    maxlon = ncgs.ncgs_unit.variables['X'].geospatial_lon_max
    minlat = ncgs.ncgs_unit.variables['Y'].geospatial_lat_min
    maxlat = ncgs.ncgs_unit.variables['Y'].geospatial_lat_max
    extent = [minlon, maxlon, minlat, maxlat]
    
    #----------------------------------------------
    # Read grid from nc_file for given time_index
    #----------------------------------------------
    grid = ncgs.get_grid( var_name, time_index )
    
    if (REPORT):
        print( 'extent = ')
        print( extent )
        print( 'grid shape =', grid.shape )
        print( 'min(grid)  =', grid.min() )
        print( 'max(grid)  =', grid.max() )

    ncgs.close_file()
    return (grid, long_name, extent)
    
#   read_grid_from_nc_file()
#--------------------------------------------------------------------
def read_and_show_rtg( rtg_filename, long_name, VERBOSE=True,
                       cmap='jet', BLACK_ZERO=False,
                       stretch='hist_equal',
                       a=1, b=2, p=0.5, im_file=None,
                       xsize=8, ysize=8, dpi=None ):
    
    rtg = rtg_files.rtg_file()
    OK  = rtg.open_file( rtg_filename )
    if not(OK):
        print('Sorry, Could not open RTG file:')
        print( rtg_filename )
        return
    
    grid   = rtg.read_grid( VERBOSE=VERBOSE )
    extent = rtg.get_bounds()
    rtg.close_file()

    if (VERBOSE):
        print('Byte swap needed =', rtg.byte_swap_needed())
        print('Reading grid from RTG file...')
        print('extent =', extent)
        print('min(grid), max(grid) =', grid.min(), grid.max())
        print('Finished.')
        print()

    show_grid_as_image( grid, long_name, extent=extent, cmap=cmap,
                        BLACK_ZERO=BLACK_ZERO, stretch=stretch,
                        a=a, b=b, p=p, im_file=im_file,
                        xsize=xsize, ysize=ysize, dpi=dpi)
                              
#   read_and_show_rtg()
#--------------------------------------------------------------------
def show_grid_as_image( grid, long_name, extent=None,
                        cmap='rainbow', BLACK_ZERO=False,
                        LAND_SEA_BACKDROP=False,
                        stretch='power3',
                        a=1, b=2, p=0.5,
                        NO_SHOW=False, im_file=None,
                        xsize=8, ysize=8, dpi=None): 

    # Note:  extent = [minlon, maxlon, minlat, maxlat]
    
    #-------------------------
    # Other color map names
    #--------------------------------------------
    # hsv, jet, gist_rainbow (reverse rainbow),
    # gist_ncar, gist_stern
    #--------------------------------------------    

    #--------------------------
    # Other stretch functions
    #--------------------------
    grid2 = stretch_grid( grid, stretch, a=a, b=b, p=p )
#     if (stretch == 'power_stretch3'):
#         grid2 = power_stretch3( grid, a=0.5 )
#     elif (stretch == 'power_stretch1a'):   
#         grid2 = power_stretch1( grid, 0.5)
#     elif (stretch == 'power_stretch1b'):
#         grid2 = power_stretch1( grid, 0.2)
#     elif (stretch == 'power_stretch2'):
#         grid2 = power_stretch2( grid )
#     elif (stretch == 'log_stretch'):
#         grid2 = log_stretch( grid )
#     elif (stretch == 'hist_equal'):
#         grid2 = histogram_equalize( grid, PLOT_NCS=True)
#     else:
#         print('SORRY, Unknown stretch =', stretch)
#         return 

    #---------------------------------------
    # Modify the colormap (0 = black) ?
    # cmap is name of colormap, a string
    #--------------------------------------------------------
    # cmap arg to imshow can be name (as str) or cmap array
    # 4th entry is opacity, or alpha channel (I think)
    #--------------------------------------------------------
    # See: "Creating listed colormaps" section at:
    # https://matplotlib.org/3.1.0/tutorials/colors/
    #         colormap-manipulation.html
    #--------------------------------------------------------
    # "Land green" = #c6e5bc = (198, 229, 188)
    # "Sea blue"   = #aad3df = (170, 211, 223)
    #--------------------------------------------------------
    if (BLACK_ZERO):
        n_colors = 256
        color_map  = cm.get_cmap( cmap, n_colors )
        new_colors = color_map( np.linspace(0, 1, n_colors) )
        black = np.array([0.0, 0.0, 0.0, 1.0])
        new_colors[0,:] = black
        new_cmap = ListedColormap( new_colors )
    elif (LAND_SEA_BACKDROP):
        n_colors = 256
        color_map  = cm.get_cmap( cmap, n_colors )
        new_colors = color_map( np.linspace(0, 1, n_colors) )
        land_green = np.array([198, 229, 188, 256]) / 256.0
        sea_blue   = np.array([170, 211, 223, 256]) / 256.0
        new_colors[0,:]   = land_green
        new_colors[255,:] = sea_blue
        new_cmap = ListedColormap( new_colors )
    else:
        new_cmap = cmap
    
    #----------------------------
    # Set up and show the image
    #----------------------------
    # figure = plt.figure(1, figsize=(xsize, ysize))
    fig, ax = plt.subplots( figsize=(xsize, ysize), dpi=dpi)
    im_title = long_name.replace('_', ' ').title()
    ax.set_title( im_title )
    ax.set_xlabel('Longitude [deg]')
    ax.set_ylabel('Latitude [deg]')

    gmin = grid2.min()
    gmax = grid2.max()

    im = ax.imshow(grid2, interpolation='nearest', cmap=new_cmap,
                   vmin=gmin, vmax=gmax, extent=extent)

    #--------------------------------------------------------        
    # NOTE!  Must save before "showing" or get blank image.
    #        File format is inferred from extension.
    #        e.g. TMP_Image.png, TMP_Image.jpg.
    #--------------------------------------------------------
    if (im_file is not None):  
        plt.savefig( im_file )
    else:
        plt.show()   # Ignore NO_SHOW arg for now.   
    #-----------------------------------------------
#     if (im_file is not None):  
#         plt.savefig( im_file )
#     if not(NO_SHOW):
#         plt.show()
 
    plt.close()
        
#   Information on matplotlib color maps
#   https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
# 
#   Information on matplotlib.pyplot.imshow
#   https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.imshow.html
# 
#   Information on matplotlib.pyplot.savefig
#   https://matplotlib.org/3.1.0/api/_as_gen/matplotlib.pyplot.savefig.html
# 
#   plt.savefig(fname, dpi=None, facecolor='w', edgecolor='w',
#               orientation='portrait', papertype=None, format=None,
#               transparent=False, bbox_inches=None, pad_inches=0.1,
#               frameon=None, metadata=None)
  
#   show_grid_as_image()
#--------------------------------------------------------------------
def save_grid_stack_as_images( nc_file, png_dir, extent=None,
              stretch='power3', a=1, b=2, p=0.5,
              cmap='rainbow', REPORT=True,
              xsize=6, ysize=6, dpi=192 ):

    # Example nc_files:
    # nc_file = case_prefix + '_2D-Q.nc'
    # nc_file = case_prefix + '_2D-d-flood.nc'

    if ('_2D' not in nc_file):
        print('ERROR: This function is only for TopoFlow "2D" files.') 
        return

    ncgs = ncgs_files.ncgs_file()        
    ncgs.open_file( nc_file )
    var_name_list = ncgs.get_var_names( no_dim_vars=True )  ####
    var_index = 0   # (dim vars are now excluded)
    var_name  = var_name_list[ var_index ]
    long_name = ncgs.get_var_long_name( var_name )
    n_grids   = ncgs.ncgs_unit.variables[var_name].n_grids

    im_title = long_name.replace('_', ' ').title()
    im_file_prefix = 'TF_Grid_Movie_Frame_'
    time_pad_map = {1:'0000', 2:'000', 3:'00', 4:'0', 5:''}
    cmap = 'rainbow'

    if (REPORT):
        print('Creating images from grid stack in nc_file:')
        print('  ' + nc_file )
        print('  ' + 'var name  =', var_name)
        print('  ' + 'long name =', long_name)
        print('  ' + 'n_grids   =', n_grids)
        print('This may take a few minutes.')
        print('Working...')
        
    time_index = 0
    while (True):
        # print('time index =', time_index )
        try:
            grid = ncgs.get_grid( var_name, time_index )
        except:
            break
        time_index += 1

        #----------------------------------------    
        # Build a filename for this image/frame
        #----------------------------------------
        tstr = str(time_index)
        pad = time_pad_map[ len(tstr) ]
        time_str = (pad + tstr)
        im_file = im_file_prefix + time_str + '.png' 
        im_file = (png_dir + '/' + im_file)
                
        show_grid_as_image( grid, long_name, cmap=cmap,
                            stretch=stretch, a=a, b=b, p=p, 
                            extent=extent,
                            NO_SHOW=True, im_file=im_file,
                            xsize=xsize, ysize=ysize, dpi=dpi )
                            
    ncgs.close_file()
    tstr = str(time_index)
    print('Finished saving grid images to PNG files.')
    print('   Number of files = ' + tstr)
    print()

#   save_grid_stack_as_images()
#--------------------------------------------------------------------
def save_rts_as_images( rts_file, png_dir, extent=None,
                        long_name='River Discharge',
                        stretch='power3', a=1, b=2, p=0.5,
                        cmap='rainbow', BLACK_ZERO=False,
                        REPORT=True,
                        xsize=6, ysize=6, dpi=192):

    # Example rts_files:
    # rts_file = case_prefix + '_2D-Q.rts'
    # rts_file = case_prefix + '_2D-d-flood.rts'

    if ('.rts' not in rts_file):
        print('ERROR: This function is only for RTS files.') 
        return

    rts = rts_files.rts_file()
    OK  = rts.open_file( rts_file )
    if not(OK):
        print('Could not open RTS file.')
        return
    n_grids = rts.number_of_grids()
    print('Byte swap needed =', rts.byte_swap_needed())

    if (extent is None):
        extent = rts.get_bounds()

    im_title = long_name.replace('_', ' ').title()
    im_file_prefix = 'TF_RTS_Movie_Frame_'
    time_pad_map = {1:'0000', 2:'000', 3:'00', 4:'0', 5:''}

    if (REPORT):
        print('Creating images from grid stack in rts_file:')
        print('  ' + rts_file )
        print('  ' + 'long name =', long_name)
        print('  ' + 'n_grids   =', n_grids)
        print('  ' + 'extent    =', extent)
        print('This may take a few minutes.')
        print('Working...')
        
    time_index = 0
    rts_min = 1e12
    rts_max = 1e-12

    while (True):
        # print('time index =', time_index )
        try:
            grid = rts.read_grid( time_index )   # alias to get_grid()
            gmin = grid.min()
            gmax = grid.max()
            rts_min = min( rts_min, gmin )
            rts_max = max( rts_max, gmax )
        except:
            break
        time_index += 1

        #----------------------------------------    
        # Build a filename for this image/frame
        #----------------------------------------
        tstr = str(time_index)
        pad = time_pad_map[ len(tstr) ]
        time_str = (pad + tstr)
        im_file = im_file_prefix + time_str + '.png' 
        im_file = (png_dir + '/' + im_file)
                
        show_grid_as_image( grid, long_name, cmap=cmap,
                            stretch=stretch, a=a, b=b, p=p,
                            BLACK_ZERO=BLACK_ZERO, extent=extent,
                            NO_SHOW=True, im_file=im_file,
                            xsize=xsize, ysize=ysize, dpi=dpi )

    rts.close_file()
    print('min(rts), max(rts) =', rts_min, rts_max)
    tstr = str(time_index)
    print('Finished saving grid images to PNG files.')
    print('   Number of files = ' + tstr)  
    print()

#   save_rts_as_images()
#--------------------------------------------------------------------
def plot_time_series(nc_file, output_dir=None, var_index=0,
                     marker=',', REPORT=True, xsize=11, ysize=6,
                     im_file=None):

    # Example nc_files:
    # nc_file = case_prefix + '_0D-Q.nc'
    # nc_file = case_prefix + '_0D-d-flood.nc'

    #----------------------------------------------------
    # Possible plot point markers:
    # https://matplotlib.org/3.1.1/api/markers_api.html
    #----------------------------------------------------
    # marker = ','  # pixel
    # marker = '.'  # point (small circle)
    # marker = 'o'  # circle
    # marker = '+'
    # marker = 'x'

    if ('_0D' not in nc_file):
        print('ERROR: This function is only for TopoFlow "OD" files.') 
        return
       
    if (output_dir is not None):
        os.chdir( output_dir )

    ncts = ncts_files.ncts_file()
    ncts.open_file( nc_file )
    var_name_list = ncts.get_var_names( no_dim_vars=True )
    lon_list      = ncts.get_var_lons()
    lat_list      = ncts.get_var_lats()

    var_name = var_name_list[ var_index ]

    if (REPORT):
        print( 'var_names in netCDF file =' )
        print( var_name_list )
        print( 'var longitudes =')
        print( lon_list )
        print( 'var latitudes =')
        print( lat_list )
        print()

    # (series, times) = ncts.get_series( var_name )
    # long_name = series.long_name
    # v_units   = series.units
    # values    = np.array( series )
    #-----------------------------------------
    ts_values = ncts.get_values( var_name )
    ts_times  = ncts.get_times()
    long_name = ts_values.long_name
    v_units   = ts_values.units
    t_units   = ts_times.units
    values    = ts_values[:]
    times     = ts_times[:]
    # values    = np.array( ts_values )
    # times     = np.array( ts_times )

    if (t_units == 'minutes'):
        # times = times / 60.0
        # t_units = 'hours'
        times = times / (60.0 * 24)
        t_units = 'days'

    # For testing
    ####################
    # print(' max value =', values.max())
    # print(' min value =', values.min())
    # print(' values[-50:-1] =', values[-50:-1])
    # print(' times[-50:-1]  =', times[-50:-1])
    # print()
    
    # ymin = values.min()
    ymin = 0.0
    ymax = values.max()

    figure = plt.figure(1, figsize=(xsize, ysize))
    # fig, ax = plt.subplots( figsize=(xsize, ysize))

    y_name = long_name.replace('_', ' ').title()

    plt.plot( times, values, marker=marker)
    plt.xlabel( 'Time' + ' [' + t_units + ']' )
    plt.ylabel( y_name + ' [' + v_units + ']' )
    plt.ylim( np.array(ymin, ymax) )

    #--------------------------------------------------------        
    # NOTE!  Must save before "showing" or get blank image.
    #        File format is inferred from extension.
    #        e.g. TMP_Image.png, TMP_Image.jpg.
    #--------------------------------------------------------
    if (im_file is not None):  
        plt.savefig( im_file )
    else:
        plt.show()
    plt.close()        

    ncts.close_file()
    
#   plot_time_series()
#--------------------------------------------------------------------
def plot_z_profile(nc_file, time_index=50,
                   output_dir=None, marker=',',
                   REPORT=True, xsize=11, ysize=6):

    # Example nc_files:
    # nc_file = case_prefix + '_1D-q.nc'
    # nc_file = case_prefix + '_1D-p.nc'
    # nc_file = case_prefix + '_1D-K.nc'
    # nc_file = case_prefix + '_1D-v.nc'

    #----------------------------------------------------
    # Possible plot point markers:
    # https://matplotlib.org/3.1.1/api/markers_api.html
    #----------------------------------------------------
    # marker = ','  # pixel
    # marker = '.'  # point (small circle)
    # marker = 'o'  # circle
    # marker = '+'
    # marker = 'x'

    if ('_1D' not in nc_file):
        print('ERROR: This function is only for TopoFlow "1D" files.') 
        return
       
    if (output_dir is not None):
        os.chdir( output_dir )
 
    ncps = ncps_files.ncps_file()
    ncps.open_file( nc_file )
    var_name_list = ncps.get_var_names()
    lon_list      = ncps.get_var_lons()
    lat_list      = ncps.get_var_lats()

    var_index = 2  #### 0 = time, 1 = z, 2 = var
    var_name = var_name_list[ var_index ]

    if (REPORT):
        print( 'var_names in netCDF file =' )
        print( var_name_list )
        print( 'var longitudes =')
        print( lon_list )
        print( 'var latitudes =')
        print( lat_list )
        print()

    # (profile, z, time) = ncps.get_profile(var_name, time_index)

    (profiles, z, times) = ncps.get_profiles(var_name)
    long_name = profiles.long_name
    v_units   = profiles.units
    z_units   = z.units
    # t_units   = times.units

    profile    = profiles[ time_index]
    time       = times[ time_index ]
    values     = np.array( profile )
    z_values   = np.array( z )
    # times     = np.array( times )
    # values = profile[:]   # also works
    # times  = times[:]    # also works

    # if (t_units == 'minutes'):
    #     # times = times / 60.0
    #     # t_units = 'hours'
    #     times = times / (60.0 * 24)
    #     t_units = 'days'

    # ymin = 0.0
    ymin = values.min()
    ymax = values.max()

    figure = plt.figure(1, figsize=(11,6))
    # fig, ax = plt.subplots( figsize=(11,6))

    y_name = long_name.replace('_', ' ').title()

    plt.plot( z_values, values, marker=marker)
    plt.xlabel( 'Depth' + ' [' + z_units + ']' )
    plt.ylabel( y_name + ' [' + v_units + ']' )
    plt.ylim( np.array(ymin, ymax) )

    plt.show()

    ncps.close_file()
         
#   plot_z_profile()
#--------------------------------------------------------------------
def save_profile_series_as_images(nc_file, png_dir=None,
                 ymin=None, ymax=None, marker=',', REPORT=True,
                 xsize=11, ysize=6, dpi=192):

    # Examples of nc_files:
    # nc_file = case_prefix + '_1D-q.nc'
    # nc_file = case_prefix + '_1D-p.nc'
    # nc_file = case_prefix + '_1D-v.nc'
    # nc_file = case_prefix + '_1D-K.nc'

    if (png_dir is None):
        print('ERROR: PNG directory is not set.')
        return
    
    # If ymin or ymax is set, it is used for all plots
    ALL_SAME_YMIN = (ymin is not None)
    ALL_SAME_YMAX = (ymax is not None)
         
    ncps = ncps_files.ncps_file()
    ncps.open_file( nc_file )
    var_name_list = ncps.get_var_names()
    var_index = 2   #### 0 = time, 1 = z, 2 = var
    var_name  = var_name_list[ var_index ]
    long_name = ncps.get_var_long_name( var_name )
    ##  svo_name = ncps.get_var_svo_name( var_name )

    y_name = long_name.replace('_', ' ').title()

    im_title = long_name.replace('_', ' ').title()
    im_file_prefix = 'TF_Profile_Movie_Frame_'
    time_pad_map = {1:'0000', 2:'000', 3:'00', 4:'0', 5:''}
    ## cmap = 'rainbow'

    #---------------------------------
    # Read all of the profiles, etc.
    #---------------------------------
    try:
        (profiles, z, times) = ncps.get_profiles( var_name )
        n_profiles = len( profiles )  ########
        long_name = profiles.long_name
        v_units   = profiles.units
        z_values  = np.array( z )
        z_units   = z.units
        # t_units   = times.units
    except:
        print('ERROR: Could not read profiles from file:')
        print( nc_file )
        return
                   
    if (REPORT):
        print('Creating images from z profiles in nc_file:')
        print('  ' + nc_file )
        print('  ' + 'var name  =', var_name)
        print('  ' + 'long_name =', long_name )
        ## print('  ' + 'svo_name  =', svo_name )
        print('  ' + 'Number of profiles =', n_profiles )
        print('This may take a few minutes.')
        print('Working...')

    for time_index in range(n_profiles):
        # print('time index =', time_index )
        profile   = profiles[ time_index ]
        time      = times[ time_index ]
        time_index += 1
 
        values = np.array( profile )
        if not(ALL_SAME_YMIN):
            ymin = values.min()
        if not(ALL_SAME_YMAX):
            ymax = values.max()

        fig, ax = plt.subplots( figsize=(xsize, ysize), dpi=dpi) 
        ax.set_title( im_title )   
        plt.plot( z_values, values, marker=marker)
        plt.xlabel( 'Depth' + ' [' + z_units + ']' )
        plt.ylabel( y_name + ' [' + v_units + ']' )
        plt.ylim( ymin, ymax )

        #-------------------------------------------        
        # Using np.array() like this doesn't work.
        #-------------------------------------------
        ### plt.ylim( np.array(ymin, ymax) )

        #------------------------------------------        
        # Don't show each plot as it is generated
        #------------------------------------------
        ## plt.show()

        #------------------------------------------
        # Build a filename for this image/frame
        #------------------------------------------
        tstr = str(time_index)
        pad = time_pad_map[ len(tstr) ]
        time_str = (pad + tstr)
        im_file = im_file_prefix + time_str + '.png' 
        im_file = (png_dir + '/' + im_file)

        plt.savefig( im_file )
        plt.close()

    ncps.close_file()
    tstr = str(time_index)
    print('Finished saving profile images to PNG files.')
    print('   Number of files = ' + tstr)
    print()
    
#   save_profile_series_as_images()
#--------------------------------------------------------------------
#--------------------------------------------------------------------
def create_movie_from_images( mp4_file, png_dir, fps=10, REPORT=True):

    #----------------------------------------
    # png_dir  = directory with PNG files
    # mp4_file = case_prefix + '_Movie.mp4'
    # fps      = frames per second
    #----------------------------------------
    im_file_list = sorted( glob.glob( png_dir + '/*.png' ) )
    n_frames = len( im_file_list )

    if (REPORT):
        print('Creating movie from PNG files.')
        print('   Number of PNG files =', n_frames)
        ## print('This may take a few minutes.')
        print('   Working...')

    #---------------------------------------------------------------        
    # Note:  The default codec for imageio is "libx264", which
    #        is widely used and supports mp4; H.264 codec.
    #        You can request  "mpeg4" also, and it works.
    #        If you use Get Info on an MP4, the More Info section
    #        give codecs for these as:  "H.264" or "MPEG-4 Video".
    #        If I copy an MP4 to: topoflow36/movies on GitHub,
    #        I can't get them to play in Jupyter notebook or lab.
    #        See the notebook:  MP4_Video_Test.ipynb for more info.
    # https://imageio.readthedocs.io/en/stable/format_ffmpeg.html
    #----------------------------------------------------------------
    writer = imageio.get_writer( mp4_file, fps=fps )
    ## writer = imageio.get_writer( mp4_file, fps=fps, codec='mpeg4' )
        
    for im_file in im_file_list:
        writer.append_data(imageio.imread( im_file ))
    writer.close()
   
    if (REPORT): 
        print('Finished creating movie, MP4 format.')
        print('  ' + mp4_file)
        print()

#   create_movie_from_images()
#--------------------------------------------------------------------
def plot_data( x, y, y2=None, xmin=None, xmax=None, ymin=None, ymax=None,
               x_name='x', x_units='', marker=',', title=None,
               y_name='y', y_units='',
               x_size=8,   y_size=4):

    figure = plt.figure(1, figsize=(x_size, y_size))
    # fig, ax = plt.subplots( figsize=(x_size, y_size))

    # Set the plot point marker
    # https://matplotlib.org/3.1.1/api/markers_api.html
    # marker = ','  # pixel
    # marker = '.'  # point (small circle)
    # marker = 'o'  # circle
    # marker = '+'
    # marker = 'x'

    #if (ymin is None):
    #    ymin = y.min()
    #if (ymax is None):
    #    ymax = y.max()
    #if (ymax - ymin < 0.1):
    #    ymin = ymin - 0.5
    #    ymax = ymin + 0.5

    # x_name2 = x_name.replace('_', ' ').title()
    # y_name2 = y_name.replace('_', ' ').title()
        
    plt.plot( x, y, marker=marker)
    if (y2 is not None):
        plt.plot(x, y2, marker=marker)

    plt.xlabel( x_name + ' [' + x_units + ']' )
    plt.ylabel( y_name + ' [' + y_units + ']' )
    if (title is not None):
        plt.title( title )

    plt.ylim( ymin, ymax )
    plt.xlim( xmin, xmax )
    #-------------------------------------
    # This may be necessary depending on
    # the data type of ymin, ymax
    #-------------------------------------
    ## plt.ylim( np.array([ymin, ymax]) )
    ## plt.xlim( np.array([xmin, xmax]) )
    plt.show()

#   plot_data()
#----------------------------------------------------------------------------   
def plot_soil_profile( z, var, var_name='theta', qs=None,
                       MMPH=True, SWAP_AXES=False ):

    if (var_name == 'K') or (var_name == 'v'):
        if (MMPH):
            y = var * (1000.0 * 3600.0)
            y_units = 'mmph'
        else:
            y = var
            y_units = 'm/s'
    else:
        y = var
    #----------------------------------------------
    x       = z
    ymin    = y.min()   # default
    ymax    = y.max()   # default
    x_name  = 'z'
    x_units = 'm'
    y_name  = var_name
    #----------------------------------------------
    if (var_name == 'theta'):
        y_units = '1'
        ymin = 0.0
        ymax = qs + 0.01
    elif (var_name == 'psi'):
        y_units = 'm'
    elif (var_name == 'K'):
        pass
    elif (var_name == 'v'):
        pass
    else:
        y_units = '1'
    #-----------------------------------------
    if not(SWAP_AXES):
        plot_data( x, y, ymin=ymin, ymax=ymax,
                   x_name=x_name, x_units=x_units,
                   y_name=y_name, y_units=y_units)
    else:
        plot_data( y, -x, xmin=ymin, xmax=ymax,
                   x_name=y_name, x_units=y_units,
                   y_name=x_name, y_units=x_units)

#   plot_soil_profile()
#----------------------------------------------------------------------------
def create_visualization_files( output_dir=None, topo_dir=None,
                                site_prefix=None, case_prefix='Test1',
                                movie_fps=10):

    #------------------------------------------------
    # Write a separate function to create movies
    # from the rainfall grid stacks (RTS format) ??
    #------------------------------------------------
    if (output_dir is None):
        print('SORRY, output_dir argument is required.')
        print()
        return
    os.chdir(output_dir)

    if (topo_dir is None):
        print('SORRY, topo_dir argument is required.')
        print()
        return
        
    if (site_prefix is None):
        print('SORRY, site_prefix argument is required.')
        print()
        return
               
    #-----------------------------
    # Setup required directories
    #-----------------------------
    temp_png_dir = output_dir + 'temp_png/'
    if not(os.path.exists( temp_png_dir )):
        os.mkdir( temp_png_dir )
    #-----------------------------------------
    movie_dir = output_dir + 'movies/'
    if not(os.path.exists( movie_dir )):
        os.mkdir( movie_dir )
    #-----------------------------------------
    image_dir = output_dir + 'images/'
    if not(os.path.exists( image_dir )):
        os.mkdir( image_dir )
                
    #---------------------------------------------
    # Create time series plot for all "0D" files
    # e.g. Discharge, Flood Depth, etc.
    # marker=',' means to use pixel as marker
    #---------------------------------------------    
    nc0D_file_list = glob.glob('*0D*nc')
    for nc_file in nc0D_file_list:
        im_file = nc_file.replace('.nc', '.png')
        im_path = (image_dir + im_file)
        var_index = 0   # (dimension vars are now excluded)
        plot_time_series(nc_file, output_dir=output_dir,
                         var_index=var_index, marker=',',
                         REPORT=True, xsize=11, ysize=6,
                         im_file=im_path)
    
    #-----------------------------------------    
    # Create images for several single grids
    #-----------------------------------------
    rtg_extensions = ['_DEM.rtg', '_slope.rtg', '_d8-area.rtg']
    rtg_file_list  = [site_prefix + ext for ext in rtg_extensions]
    long_name_list = ['land_surface_elevation', 'land_surface_slope',
                      'total_contributing_area']
    k = 0
    for rtg_file in rtg_file_list:
        if (rtg_file.endswith('_d8-area.rtg')):
            stretch = 'power3'
        else:
            stretch = 'hist_equal'
        #--------------------------------------------------
        im_file   = rtg_file.replace('.rtg', '.png')
        im_path   = (image_dir + im_file)
        rtg_path  = (topo_dir + rtg_file)
        long_name = long_name_list[k]
        k += 1
        read_and_show_rtg( rtg_path, long_name, cmap='jet',
                           ### BLACK_ZERO=False,
                           stretch=stretch, VERBOSE=True,
                           xsize=7, ysize=7, dpi=None,
                           im_file=im_path)
        print('Finished saving grid as image.')
        print('  ' + im_path )
        print()
             
    #----------------------------------------------
    # Create set of images and movie for all "2D"
    # files which contain grid stacks
    # e.g. *_2D-Q.nc, *_2D-d-flood.nc'
    #----------------------------------------------
    nc2D_file_list = glob.glob('*2D*nc')
    for nc_file in nc2D_file_list:
        #------------------------------------------
        # Change the stretch for specific files ?
        #------------------------------------------
#         if nc_file.endswith('d-flood.nc'):
#             cur_stretch = 'power3'
#             stretch = 'hist_equal'
            
        #------------------------------------
        # First, create a set of PNG images
        #------------------------------------
        save_grid_stack_as_images( nc_file, temp_png_dir,
                                   ##### extent=None,  # auto-computed
                                   stretch='power3', a=1, b=2, p=0.5,
                                   cmap='rainbow', REPORT=True,
                                   xsize=8, ysize=8, dpi=192)

        #----------------------------------------------
        # Create movie from set of images in temp_png
        #----------------------------------------------
        # movie_fps = "frames per second"
        mp4_file = nc_file.replace('.nc', '.mp4')
        mp4_path = (movie_dir + mp4_file)
        create_movie_from_images( mp4_path, temp_png_dir,
                                  fps=movie_fps, REPORT=True)

        #-----------------------------------
        # Delete all PNG files in temp_png
        #-----------------------------------
        ## time.sleep( 0.5 )  # Is this needed?
        delete_png_files( temp_png_dir )
  

#   create_visualization_files()
#----------------------------------------------------------------------------
def delete_png_files( temp_png_dir ):

    png_files = glob.glob( temp_png_dir + '*.png' )
    for file in png_files:
        try:
           os.remove( file )
        except OSError as e:
            print("Error: %s : %s" % (file, e.strerror)) 

    print('Finished deleting PNG files in:')
    print('  ' + temp_png_dir)
    print()

#   delete_png_files()
#----------------------------------------------------------------------------
#----------------------------------------------------------------------------
# FOR AN IDEA IN THE VISUALIZATION NOTEBOOK.
#----------------------------------------------------------------------------
# import glob, os, os.path, shutil
# 
# class dataset_info():
#     
#     def __init__(self, name='Baro'):  
#         self.home_dir = os.path.expanduser("~")
#         if (name.lower() == 'baro'):
#             #-------------------------------------------------
#             # Baro River, with mouth near Gambella, Ethiopia
#             #-------------------------------------------------
#             self.site_prefix = 'Baro-Gam_60sec'
#             self.case_prefix = 'Test1'
#             ## self.case_prefix = 'Test2'
#             self.test_dir    = self.home_dir + '/TF_Tests3/'           ########
#         elif (name.lower() == 'treynor'):
#             #-------------------------------------------------
#             # Treynor River, in Iowa (part of Nishnabotna R.)
#             #-------------------------------------------------
#             self.site_prefix = 'Treynor'
#             self.case_prefix = 'June_20_67'
#             # self.case_prefix = 'June_07_67'
#             self.test_dir    = self.home_dir + '/TF_Output/'
#     
#         self.basin_dir  = self.test_dir + self.site_prefix + '/'    
#         self.output_dir = self.basin_dir    ######
#         self.topo_dir   = self.basin_dir + '__topo/'
#         self.met_dir    = self.basin_dir + '__met/'
#         self.soil_dir   = self.basin_dir + '__soil/'
# 
#         print('Home directory   =', self.home_dir)
#         print('Basin directory  =', self.basin_dir)
#         print('Output directory =', self.output_dir)
# 
#         os.chdir( self.output_dir )  ##########
# 
# ds = dataset_info( name='Baro' )

#----------------------------------------------------------------------------
   