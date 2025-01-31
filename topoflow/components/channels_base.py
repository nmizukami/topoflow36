"""
This file defines a "base class" for channel flow components as well
as functions used by most or all channel flow methods.  That is, all
channel flow components inherit methods from this class.  The methods
of this class should be over-ridden as necessary (especially the
update_velocity() method) for different methods of modeling channel
flow.  This class, in turn, inherits from the "BMI base class" in
BMI_base.py.

See channels_kinematic_wav.py, channels_diffusive_wave.py, and
channels_dynamic_wave.py.  Each of these has a MANNING or LAW_OF_WALL
flag in their CFG file.
"""
#------------------------------------------------------------------------
# NB!   update_diversion() is currently COMMENTED OUT.
#
#------------------------------------------------------------------------
#  Copyright (c) 2001-2023, Scott D. Peckham
#
#  Aug 2023.  Changed how vol_chan_sum0 is computed for clarity.
#  Jul 2021.  Added ATTENUATE option for flashy hydrographs.
#             Added min_baseflow_flux cfg parameter.
#  Jul 2020.  Separate initialize_input_file_vars().
#  Apr 2020.  Added set_new_defaults(), disable_all_output().
#  Oct 2019.  Added FLOOD_OPTION and CHECK_STABILITY flags.
#  Sep 2014.  Wrote new update_diversions().
#             New standard names and BMI updates and testing.
#  Nov 2013.  Converted TopoFlow to a Python package.
#  Feb 2013.  Adapted to use EMELI framework.
#  Jan 2013.  Shared scalar doubles are now 0D numpy arrays.
#             This makes them mutable and allows components with
#             a reference to them to see them change.
#             So far:  Q_outlet, Q_peak, Q_min...
#  Jan 2013.  Revised handling of input/output names.
#  Oct 2012.  CSDMS Standard Names and BMI.
#  May 2012.  Commented out diversions.update() for now.  #######
#  May 2012.  Shared scalar doubles are now 1-element 1D numpy arrays.
#             This makes them mutable and allows components with
#             a reference to them to see them change.
#             So far:  Q_outlet, Q_peak, Q_min...
#  May 2010.  Changes to initialize() and read_cfg_file()
#  Mar 2010.  Changed codes to code, widths to width,
#             angles to angle, nvals to nval, z0vals to z0val,
#             slopes to slope (for GUI tools and consistency
#             across all process components)
#  Aug 2009.  Updates.
#  Jul 2009.  Updates.
#  May 2009.  Updates.
#  Jan 2009.  Converted from IDL.

#-----------------------------------------------------------------------
#  NB!     In the CFG file, change MANNING and LAW_OF_WALL flags to
#          a single string entry like "friction method".   #########
#-----------------------------------------------------------------------
#  Notes:  Set self.u in manning and law_of_wall functions ??
#          Update friction factor in manning() and law_of_wall() ?
#          Double check how Rh is used in law_of_the_wall().

#          d8_flow has "flow_grids", but this one has "codes".
#          Make sure values are not stored twice.
#-----------------------------------------------------------------------

#-----------------------------------------------------------------------
#  NOTES:  This file defines a "base class" for channelized flow
#          components as well as functions used by most or
#          all channel flow methods.  The methods of this class
#          (especially "update_velocity") should be over-ridden as
#          necessary for different methods of modeling channelized
#          flow.  See channels_kinematic_wave.py,
#          channels_diffusive_wave.py and channels_dynamic_wave.py.
#-----------------------------------------------------------------------
#  NOTES:  update_free_surface_slope() is called by the
#          update_velocity() methods of channels_diffusive_wave.py
#          and channels_dynamic_wave.py.
#-----------------------------------------------------------------------
#
#  class channels_component
#
#      ## get_attribute()        # (defined in each channel component)
#      get_input_var_names()     # (5/15/12)
#      get_output_var_names()    # (5/15/12)
#      get_var_name()            # (5/15/12)
#      get_var_units()           # (5/15/12)
#-----------------------------
#      set_constants()
#      set_missing_cfg_options()   # (4/29/20)
#      initialize()
#      update()
#      finalize()
#      set_computed_input_vars()   # (5/11/10)
#----------------------------------
#      initialize_input_file_vars()     # (7/3/20)
#      initialize_d8_vars()
#      initialize_computed_vars()
#      initialize_diversion_vars()      # (9/22/14)
#      initialize_outlet_values()
#      initialize_peak_values()
#      initialize_min_and_max_values()  # (2/3/13)
#-------------------------------------
#      update_flood_d8_vars()        # (9/17/19, for flooding)  ########
#      update_R()
#      update_R_integral()
#      update_discharge()
#      update_flood_discharge()      # (2022-05-05)
#      update_flood_discharge_OPTION1() # (9/20/19)
#      update_diversions()           # (9/22/14)
#      update_flow_volume()
#      update_flood_volume()
#      update_flood_volume_OPTION1() # (9/20/19)
#      update_channel_depth()        # (9/16/19, update)
#      update_flood_depth()          # (2022-05-05)
#      update_flood_depth_OPTION1()  # (9/20/19)
#      update_flood_depth_OPTION2()  # (2022-05-05)
#      update_free_surface_slope()
#      update_shear_stress()        # (9/9/14, depth-slope product)
#      update_shear_speed()         # (9/9/14)
#      update_trapezoid_Rh()
#      update_friction_factor()     # (9/9/14)
#----------------------------------
#      update_velocity()            # (override as needed)
#      update_velocity_on_edges()
#      update_froude_number()       # (9/9/14)
#----------------------------------
#      update_outlet_values()
#      update_peak_values()         # (at the main outlet)
#      update_Q_out_integral()      # (moved here from basins.py)
#      update_edge_values()         # (2020-06-15; centralized)
#      update_mins_and_maxes()      # (don't add into update())
#      update_total_channel_water_volume()    # (9/17/19)
#      update_total_flood_water_volume()      # (9/17/19, 5/7/22)
#      check_flow_depth()
#      check_flow_velocity()
#----------------------------------
#      open_input_files()
#      read_input_files()
#      close_input_files()
#----------------------------------
#      update_outfile_names()
#      bundle_output_files()        # (9/21/14. Not used yet)
#      disable_all_output()         # (04/29/20)
#      open_output_files()
#      write_output_files()
#      close_output_files()
#      save_grids()
#      save_pixel_values()
#----------------------------------
#      manning_formula()
#      law_of_the_wall()
#      print_status_report()
#      remove_bad_slopes() 

#  Functions:               # (stand-alone versions of these)
#      Trapezoid_Rh()
#      Manning_Formula()
#      Law_of_the_Wall()
    
#-----------------------------------------------------------------------

import numpy as np
import copy, os, os.path, sys

from topoflow.utils import BMI_base
from topoflow.utils import file_utils
from topoflow.utils import model_input
from topoflow.utils import model_output
from topoflow.utils import ncgs_files
from topoflow.utils import ncts_files
from topoflow.utils import rtg_files
from topoflow.utils import text_ts_files
from topoflow.utils import tf_utils
from topoflow.utils import parameterize    # (2021-12-13)

#-------------------------------------------------------
# NOTE:  Do not import "d8_base" itself, it won't work
#-------------------------------------------------------
from topoflow.components import d8_global as d8_base    # (11/11/16)
## from topoflow.utils import tf_d8_base as d8_base

#-----------------------------------------------------------------------
class channels_component( BMI_base.BMI_component ):

    #-----------------------------------------------------------
    # Note: rainfall_volume_flux *must* be liquid-only precip.
    #-----------------------------------------------------------        
    _input_var_names = [
        'atmosphere_water__rainfall_volume_flux',          # (P_rain)
        'glacier_ice__melt_volume_flux',                   # (MR)
        'land_surface_water__baseflow_volume_flux',        # (GW)
        'land_surface_water__evaporation_volume_flux',     # (ET)
        'soil_surface_water__infiltration_volume_flux',    # (IN)
        'snowpack__melt_volume_flux',                      # (SM)
        'water-liquid__mass-per-volume_density' ]          # (rho_H2O)
        #------------------------------------------------------------------
#         'canals__count',                                   # n_canals
#         'canals_entrance__x_coordinate',                   # canals_in_x
#         'canals_entrance__y_coordinate',                   # canals_in_y
#         'canals_entrance_water__volume_fraction',          # Q_canals_fraction
#         'canals_exit__x_coordinate',                       # canals_out_x
#         'canals_exit__y_coordinate',                       # canals_out_y
#         'canals_exit_water__volume_flow_rate',             # Q_canals_out
#         'sinks__count',                                    # n_sinks
#         'sinks__x_coordinate',                             # sinks_x
#         'sinks__y_coordinate',                             # sinks_y
#         'sinks_water__volume_flow_rate',                   # Q_sinks
#         'sources__count',                                  # n_sources
#         'sources__x_coordinate',                           # sources_x
#         'sources__y_coordinate',                           # sources_y
#         'sources_water__volume_flow_rate' ]                # Q_sources
        
    #----------------------------------
    # Maybe add these out_vars later.
    #----------------------------------
    #  ['time_sec', 'time_min' ]
    
    _output_var_names = [
        'basin_outlet_water_flow__half_of_fanning_friction_factor',        # f_outlet
        'basin_outlet_water_x-section__mean_depth',                        # d_outlet
        'basin_outlet_water_x-section__peak_time_of_depth',                # Td_peak
        'basin_outlet_water_x-section__peak_time_of_volume_flow_rate',     # T_peak
        'basin_outlet_water_x-section__peak_time_of_volume_flux',          # Tu_peak
        'basin_outlet_water_x-section__time_integral_of_volume_flow_rate', # vol_Q
        'basin_outlet_water_x-section__time_max_of_mean_depth',            # d_peak
        'basin_outlet_water_x-section__time_max_of_volume_flow_rate',      # Q_peak
        'basin_outlet_water_x-section__time_max_of_volume_flux',           # u_peak
        'basin_outlet_water_x-section__volume_flow_rate',                  # Q_outlet
        'basin_outlet_water_x-section__volume_flux',                       # u_outlet
         #--------------------------------------------------
        'canals_entrance_water__volume_flow_rate',                         # Q_canals_in 
         #-------------------------------------------------- 
        'channel_bottom_surface__slope',                           # S_bed 
        'channel_bottom_water_flow__domain_max_of_log_law_roughness_length',  # z0val_max
        'channel_bottom_water_flow__domain_min_of_log_law_roughness_length',  # z0val_min
        'channel_bottom_water_flow__log_law_roughness_length',                # z0val
        'channel_bottom_water_flow__magnitude_of_shear_stress',    # tau
        'channel_bottom_water_flow__shear_speed',                  # u_star
        'channel_centerline__sinuosity',                           # sinu
        'channel_water__volume',                                   # vol
        'channel_water_flow__froude_number',                       # froude
        'channel_water_flow__half_of_fanning_friction_factor',     # f
        'channel_water_flow__domain_max_of_manning_n_parameter',   # nval_max
        'channel_water_flow__domain_min_of_manning_n_parameter',   # nval_min
        'channel_water_flow__manning_n_parameter',                 # nval
        'channel_water_surface__slope',                            # S_free
        #---------------------------------------------------
        # These might only be available at the end of run.
        #---------------------------------------------------
        'channel_water_x-section__domain_max_of_mean_depth',       # d_max
        'channel_water_x-section__domain_min_of_mean_depth',       # d_min
        'channel_water_x-section__domain_max_of_volume_flow_rate', # Q_max
        'channel_water_x-section__domain_min_of_volume_flow_rate', # Q_min
        'channel_water_x-section__domain_max_of_volume_flux',      # u_max
        'channel_water_x-section__domain_min_of_volume_flux',      # u_min
        #---------------------------------------------------------------------    
        'channel_water_x-section__hydraulic_radius',               # Rh
        'channel_water_x-section__initial_mean_depth',             # d0
        'channel_water_x-section__mean_depth',                     # d
        'channel_water_x-section__volume_flow_rate',               # Q  
        'channel_water_x-section__volume_flux',                    # u
        'channel_water_x-section__wetted_area',                    # A_wet
        'channel_water_x-section__wetted_perimeter',               # P_wet
        #######   Next one added for flooding:  2019-09-16.  ########
        'channel_water_x-section_top__width',                      # w_top
        'channel_x-section_trapezoid_bottom__width',               # width
        'channel_x-section_trapezoid_side__flare_angle',           # angle
        #######   Next one added for flooding:  2019-09-16.  ########
        'land_surface_water__depth',                               # df
        'land_surface_water__runoff_volume_flux',                  # R  
        'land_surface_water__domain_time_integral_of_runoff_volume_flux', # vol_R   
        'model__time_step',                                        # dt
        'model_grid_cell__area',                                   # da
        #---------------------------------------------------------------------
        'channel_water_x-section__boundary_time_integral_of_volume_flow_rate', # vol_edge
        'river-network_channel_water__initial_volume',             # vol_chan_sum0
        'river-network_channel_water__volume',                     # vol_chan_sum
        'land_surface_water__area_integral_of_depth'  ]            # vol_flood_sum
        ################################################

    # These come from input files, not from other components
    _config_var_names = [
        'channel_bottom_water_flow__log_law_roughness_length',     # z0val
        'channel_centerline__sinuosity',                           # sinu
        'channel_water_flow__manning_n_parameter',                 # nval
        'channel_water_x-section__bankfull_depth',                 # d_bankfull, NEW
        'channel_water_x-section__bankfull_width',                 # w_bankfull, NEW
        'channel_water_x-section__initial_mean_depth',             # d0
        # 'channel_water_x-section_top__width',                    # w_top
        'channel_x-section_trapezoid_bottom__width',               # width
        'channel_x-section_trapezoid_side__flare_angle',           # angle
        # Next two vars can be obtained from d8 component.
#         'land_surface__elevation',                                # DEM
#         'land_surface__slope',                                    # S_bed
        'land_surface_water__depth' ]                               # df
            
    _var_name_map = {
        'atmosphere_water__rainfall_volume_flux':              'P_rain',
        'glacier_ice__melt_volume_flux':                       'MR',
#         'land_surface__elevation':                             'DEM',
#         'land_surface__slope':                                 'S_bed',
        'land_surface_water__baseflow_volume_flux':            'GW',
        'land_surface_water__evaporation_volume_flux':         'ET',
        'soil_surface_water__infiltration_volume_flux':        'IN',
        'snowpack__melt_volume_flux':                          'SM',
        'water-liquid__mass-per-volume_density':               'rho_H2O',
        #------------------------------------------------------------------------
        'basin_outlet_water_flow__half_of_fanning_friction_factor':'f_outlet',
        'basin_outlet_water_x-section__mean_depth':                'd_outlet',
        'basin_outlet_water_x-section__peak_time_of_depth':            'Td_peak',
        'basin_outlet_water_x-section__peak_time_of_volume_flow_rate': 'T_peak',
        'basin_outlet_water_x-section__peak_time_of_volume_flux':      'Tu_peak',
        'basin_outlet_water_x-section__volume_flow_rate':            'Q_outlet',
        'basin_outlet_water_x-section__volume_flux':                 'u_outlet',
        'basin_outlet_water_x-section__time_integral_of_volume_flow_rate': 'vol_Q',
        'basin_outlet_water_x-section__time_max_of_mean_depth':      'd_peak',
        'basin_outlet_water_x-section__time_max_of_volume_flow_rate':'Q_peak',
        'basin_outlet_water_x-section__time_max_of_volume_flux':     'u_peak',
        #--------------------------------------------------------------------------
        'canals_entrance_water__volume_flow_rate':                 'Q_canals_in', 
        #--------------------------------------------------------------------------    
        'channel_bottom_surface__slope':                           'S_bed',
        'channel_bottom_water_flow__domain_max_of_log_law_roughness_length': 'z0val_max',
        'channel_bottom_water_flow__domain_min_of_log_law_roughness_length': 'z0val_min',
        'channel_bottom_water_flow__log_law_roughness_length':     'z0val',
        'channel_bottom_water_flow__magnitude_of_shear_stress':    'tau',
        'channel_bottom_water_flow__shear_speed':                  'u_star',
        'channel_centerline__sinuosity':                           'sinu',
        'channel_water__volume':                                   'vol',
        'channel_water_flow__domain_max_of_manning_n_parameter':   'nval_max',
        'channel_water_flow__domain_min_of_manning_n_parameter':   'nval_min',
        'channel_water_flow__froude_number':                       'froude',
        'channel_water_flow__half_of_fanning_friction_factor':     'f',
        'channel_water_flow__manning_n_parameter':                 'nval',
        'channel_water_surface__slope':                            'S_free',
        #-----------------------------------------------------------------------
        'channel_water_x-section__domain_max_of_mean_depth':       'd_max',
        'channel_water_x-section__domain_min_of_mean_depth':       'd_min',
        'channel_water_x-section__domain_max_of_volume_flow_rate': 'Q_max',
        'channel_water_x-section__domain_min_of_volume_flow_rate': 'Q_min',
        'channel_water_x-section__domain_max_of_volume_flux':      'u_max',
        'channel_water_x-section__domain_min_of_volume_flux':      'u_min',
        #-----------------------------------------------------------------------      
        'channel_water_x-section__hydraulic_radius':               'Rh',
        'channel_water_x-section__initial_mean_depth':             'd0',
        'channel_water_x-section__mean_depth':                     'd',
        'channel_water_x-section__volume_flow_rate':               'Q',                
        'channel_water_x-section__volume_flux':                    'u',
        'channel_water_x-section__wetted_area':                    'A_wet',
        'channel_water_x-section__wetted_perimeter':               'P_wet',
        ## 'channel_water_x-section_top__width':                   # (not used)
        'channel_x-section_trapezoid_bottom__width':               'width',   ####
        'channel_x-section_trapezoid_side__flare_angle':           'angle',   ####
        'land_surface_water__depth':                               'df',
        'land_surface_water__domain_time_integral_of_runoff_volume_flux': 'vol_R',
        'land_surface_water__runoff_volume_flux':                  'R',
        'model__time_step':                                        'dt',
        'model_grid_cell__area':                                   'da',
        #------------------------------------------------------------------
        'canals__count':                          'n_canals',
        'canals_entrance__x_coordinate':          'canals_in_x',
        'canals_entrance__y_coordinate':          'canals_in_y',
        'canals_entrance_water__volume_fraction': 'Q_canals_fraction',
        'canals_exit__x_coordinate':              'canals_out_x',
        'canals_exit__y_coordinate':              'canals_out_y',
        'canals_exit_water__volume_flow_rate':    'Q_canals_out',
        'sinks__count':                           'n_sinks',
        'sinks__x_coordinate':                    'sinks_x',
        'sinks__y_coordinate':                    'sinks_y',
        'sinks_water__volume_flow_rate':          'Q_sinks',
        'sources__count':                         'n_sources',
        'sources__x_coordinate':                  'sources_x',
        'sources__y_coordinate':                  'sources_y',
        'sources_water__volume_flow_rate':        'Q_sources',
        #------------------------------------------------------------------
        # Note: vol_chan and vol_flood are DEM-sized grids for the volume
        # of water in each grid cell channel and each grid cell extent.
        # In all other components, variables starting with "vol_" are
        # scalars that hold area-time integrals of fluxes or area
        # integrals of stored quantities.  Here, those end in "_sum" or
        # "sum0".  (2023-09-01)
        #------------------------------------------------------------------        
        'channel_water_x-section__boundary_time_integral_of_volume_flow_rate': 'vol_edge',
        'river-network_channel_water__initial_volume':  'vol_chan_sum0',
        'river-network_channel_water__volume':          'vol_chan_sum',
        'land_surface_water__area_integral_of_depth':   'vol_flood_sum' }
        #####################################

    _var_units_map = {
        'atmosphere_water__rainfall_volume_flux':              'm s-1',
        'glacier_ice__melt_volume_flux':                       'm s-1',
        ## 'land_surface__elevation':                          'm',
        ## 'land_surface__slope':                              '1',
        'land_surface_water__baseflow_volume_flux':            'm s-1',
        'land_surface_water__evaporation_volume_flux':         'm s-1',
        'soil_surface_water__infiltration_volume_flux':        'm s-1',
        'snowpack__melt_volume_flux':                          'm s-1',
        'water-liquid__mass-per-volume_density':               'kg m-3',
        #--------------------------------------------------------------------------- 
        'basin_outlet_water_flow__half_of_fanning_friction_factor':        '1',       
        'basin_outlet_water_x-section__mean_depth':                        'm',
        'basin_outlet_water_x-section__peak_time_of_depth':                'min',
        'basin_outlet_water_x-section__peak_time_of_volume_flow_rate':     'min',
        'basin_outlet_water_x-section__peak_time_of_volume_flux':          'min',        
        'basin_outlet_water_x-section__time_integral_of_volume_flow_rate': 'm3',
        'basin_outlet_water_x-section__time_max_of_mean_depth':            'm',
        'basin_outlet_water_x-section__time_max_of_volume_flow_rate':      'm3 s-1',
        'basin_outlet_water_x-section__time_max_of_volume_flux':           'm s-1',
        'basin_outlet_water_x-section__volume_flow_rate':                  'm3 s-1',
        'basin_outlet_water_x-section__volume_flux':                       'm s-1',
        #---------------------------------------------------------------------------
        'canals_entrance_water__volume_flow_rate':                 'm3 s-1', 
        #---------------------------------------------------------------------------  
        'channel_bottom_surface__slope':                           '1',
        'channel_bottom_water_flow__domain_max_of_log_law_roughness_length':  'm',
        'channel_bottom_water_flow__domain_min_of_log_law_roughness_length':  'm',
        'channel_bottom_water_flow__log_law_roughness_length':     'm',
        'channel_bottom_water_flow__magnitude_of_shear_stress':    'kg m-1 s-2',
        'channel_bottom_water_flow__shear_speed':                  'm s-1',
        'channel_centerline__sinuosity':                           '1',    
        'channel_water__volume':                                   'm3', 
        'channel_water_flow__froude_number':                       '1',
        'channel_water_flow__half_of_fanning_friction_factor':     '1',               
        'channel_water_flow__manning_n_parameter':                 'm-1/3 s',
        'channel_water_flow__domain_max_of_manning_n_parameter':   'm-1/3 s',
        'channel_water_flow__domain_min_of_manning_n_parameter':   'm-1/3 s',
        'channel_water_surface__slope':                            '1',
        #--------------------------------------------------------------------
        'channel_water_x-section__domain_max_of_mean_depth':       'm',
        'channel_water_x-section__domain_min_of_mean_depth':       'm',
        'channel_water_x-section__domain_max_of_volume_flow_rate': 'm3 s-1',
        'channel_water_x-section__domain_min_of_volume_flow_rate': 'm3 s-1',
        'channel_water_x-section__domain_max_of_volume_flux':      'm s-1',
        'channel_water_x-section__domain_min_of_volume_flux':      'm s-1',
        #--------------------------------------------------------------------
        'channel_water_x-section__hydraulic_radius':               'm',
        'channel_water_x-section__initial_mean_depth':             'm',
        'channel_water_x-section__mean_depth':                     'm',
        'channel_water_x-section__volume_flow_rate':               'm3 s-1',
        'channel_water_x-section__volume_flux':                    'm s-1',
        'channel_water_x-section__wetted_area':                    'm2',
        'channel_water_x-section__wetted_perimeter':               'm',
        'channel_x-section_trapezoid_bottom__width':               'm',
        'channel_x-section_trapezoid_side__flare_angle':           'rad', # CHECKED 
        'land_surface_water__depth':                               'm',
        'land_surface_water__domain_time_integral_of_runoff_volume_flux': 'm3',  
        'land_surface_water__runoff_volume_flux':                  'm s-1',      
        'model__time_step':                                        's',
        'model_grid_cell__area':                                   'm2',
        #------------------------------------------------------------------
        'canals__count':                          '1',
        'canals_entrance__x_coordinate':          'm',
        'canals_entrance__y_coordinate':          'm',
        'canals_entrance_water__volume_fraction': '1',
        'canals_exit__x_coordinate':              'm',
        'canals_exit__y_coordinate':              'm',
        'canals_exit_water__volume_flow_rate':    'm3 s-1',
        'sinks__count':                           '1',
        'sinks__x_coordinate':                    'm',
        'sinks__y_coordinate':                    'm',
        'sinks_water__volume_flow_rate':          'm3 s-1',
        'sources__count':                         '1',
        'sources__x_coordinate':                  'm',
        'sources__y_coordinate':                  'm',
        'sources_water__volume_flow_rate':        'm3 s-1',
        #------------------------------------------------------------
        'channel_water_x-section__boundary_time_integral_of_volume_flow_rate': 'm3',
        'river-network_channel_water__initial_volume': 'm3',
        'river-network_channel_water__volume':         'm3',
        'land_surface_water__area_integral_of_depth':  'm3'  }
        #####################################

    #------------------------------------------------    
    # Return NumPy string arrays vs. Python lists ?
    #------------------------------------------------
    ## _input_var_names  = np.array( _input_var_names )
    ## _output_var_names = np.array( _output_var_names )
        
    #-------------------------------------------------------------------
    def get_input_var_names(self):

        #--------------------------------------------------------
        # Note: These are currently variables needed from other
        #       components vs. those read from files or GUI.
        #--------------------------------------------------------   
        return np.array( self._input_var_names )
    
    #   get_input_var_names()
    #-------------------------------------------------------------------
    def get_output_var_names(self):
 
        return np.array( self._output_var_names )
    
    #   get_output_var_names()
    #-------------------------------------------------------------------
#     def get_config_var_names(self):
#  
#         # New, proposed BMI function
#         return self._config_var_names
#     
#     #   get_config_var_names()
    #-------------------------------------------------------------------
    def get_var_name(self, long_var_name):
            
        return self._var_name_map[ long_var_name ]

    #   get_var_name()
    #-------------------------------------------------------------------
    def get_var_units(self, long_var_name):

        return self._var_units_map[ long_var_name ]
   
    #   get_var_units()
    #-------------------------------------------------------------------
##    def get_var_type(self, long_var_name):
##
##        #---------------------------------------
##        # So far, all vars have type "double",
##        # but use the one in BMI_base instead.
##        #---------------------------------------
##        return 'float64'
##    
##    #   get_var_type()
    #-------------------------------------------------------------------
    def set_constants(self):

        #------------------------
        # Define some constants
        #------------------------
        self.g           = np.float64(9.81)    # (gravitation const.)
        self.aval        = np.float64(0.476)   # (integration const.)
        self.kappa       = np.float64(0.408)   # (von Karman's const.)
        self.law_const   = np.sqrt(self.g) / self.kappa
        self.one_third   = np.float64(1.0) / 3.0        
        self.two_thirds  = np.float64(2.0) / 3.0
        self.deg_to_rad  = np.pi / np.float64( 180 )
        self.rad_to_deg  = np.float64(180) / np.pi
        self.mmph_to_mps = 1.0 / (3600.0 * 1000.0)
        
    #   set_constants()
    #-------------------------------------------------------------------
    def set_missing_cfg_options(self):    

        #------------------------------------------------------
        # (2019-10-08) Added CHECK_STABILITY flag to CFG file
        # so stability check be turned off to increase speed.
        #------------------------------------------------------
        if not(hasattr(self, 'CHECK_STABILITY')):
            self.CHECK_STABILITY = True
             
        #--------------------------------------------------------------        
        # (2019-10-03) Added FLOOD_OPTION flag to CFG file.
        # If not(FLOOD_OPTION), don't write flood depths (all zeros).
        #--------------------------------------------------------------
        # Make sure CFG file has "d_flood_gs_file" vs. "df_gs_file".
        #--------------------------------------------------------------
        if not(hasattr(self, 'FLOOD_OPTION')):
            self.FLOOD_OPTION    = False
            self.SAVE_DF_GRIDS   = False
            self.SAVE_DF_PIXELS  = False
            ## self.d_flood_gs_file = ''
            ## self.d_flood_ts_file = ''
            
        #-------------------------------------------------       
        # (2021-07-23) Added ATTENUATE flag to CFG file.
        #------------------------------------------------- 
        if not(hasattr(self, 'ATTENUATE')):
            self.ATTENUATE = False

        #-----------------------------------------------       
        # (2021-07-24) Added baseflow_min to CFG file.
        #----------------------------------------------- 
        if not(hasattr(self, 'min_baseflow_flux')):
            self.min_baseflow_flux = 0.0  # [mmph]
        self.min_baseflow_flux_mps = self.min_baseflow_flux * self.mmph_to_mps
        self.vol_GW = 0.0   # [m3]

        #--------------------------------------------- 
        # Also new in 2019, not in older CFG files
        # Not used then, but still need to be set.
        # Need to be set if FLOOD_OPTION is False ??
        #---------------------------------------------
        if not(hasattr(self, 'd_bankfull_type')):
            self.d_bankfull_type = 'Scalar'  # or Grid
            self.d_bankfull = 10.0  # [meters]
            self.d_bankfull_file = ''

        #-------------------------------------------------------       
        # (2021-12-13) Added CREATE_CHANNEL_FILES to CFG file.
        #-------------------------------------------------------
        if not(hasattr(self, 'CREATE_CHANNEL_FILES')):
            self.CREATE_CHANNEL_FILES = False
        #---------------------------------------------------
        if (self.CREATE_CHANNEL_FILES == True):
            if not(hasattr(self, 'max_river_width')):
                self.max_river_width = 140.0   # [meters]
            if not(hasattr(self, 'channel_width_power')):
                self.channel_width_power = 0.5
            if not(hasattr(self, 'min_manning_n')):
                self.min_manning_n = 0.03
            if not(hasattr(self, 'max_manning_n')):
                self.max_manning_n = 0.2
            if not(hasattr(self, 'max_bankfull_depth')):
                self.max_bankfull_depth = 8.0  # [meters]
            if not(hasattr(self, 'bankfull_depth_power')):
                self.bankfull_depth_power = 0.4

        #------------------------------------------------      
        # (2022-02-15) Added optional scale "factors"
        # passed to update_var() in read_input_files().
        #------------------------------------------------
        if not(hasattr(self, 'slope_factor')):
            self.slope_factor = 1.0
        if not(hasattr(self, 'nval_factor')):
            self.nval_factor = 1.0
        if not(hasattr(self, 'z0val_factor')):
            self.z0val_factor = 1.0
        if not(hasattr(self, 'width_factor')):
            self.width_factor = 1.0
        if not(hasattr(self, 'angle_factor')):
            self.angle_factor = 1.0
        if not(hasattr(self, 'sinu_factor')):
            self.sinu_factor = 1.0
        if not(hasattr(self, 'd0_factor')):
            self.d0_factor = 1.0
        if not(hasattr(self, 'd_bankfull_factor')):
            self.d_bankfull_factor = 1.0
                            
    #   set_missing_cfg_options()
    #-------------------------------------------------------------------
    def initialize(self, cfg_file=None, mode="nondriver", SILENT=False): 

        self.SILENT = SILENT
        if not(self.SILENT):
            print(' ')
            print('Channels component: Initializing...')
        
        self.status   = 'initializing'  # (OpenMI 2.0 convention)
        self.mode     = mode
        self.cfg_file = cfg_file
        
        #-----------------------------------------------
        # Load component parameters from a config file
        #-----------------------------------------------
        self.set_constants()       # (12/7/09)
        # print 'CHANNELS calling initialize_config_vars()...'
        self.initialize_config_vars()
        self.set_missing_cfg_options()  # (2020-04-29)

        # New option, see set_missing_cfg_options().
        if not(self.FLOOD_OPTION):
            self.SAVE_DF_GRIDS  = False  # (still needed here)
            self.SAVE_DF_PIXELS = False
            self.d_flood_gs_file = ''
            self.d_flood_ts_file = ''

        #------------------------------------------------------------
        # Must call read_grid_info() after initialize_config_vars()
        #------------------------------------------------------------
        # print 'CHANNELS calling read_grid_info()...'
        #### self.read_grid_info()    # NOW IN initialize_config_vars()

        #------------------------------------------------------------
        #print 'CHANNELS calling initialize_basin_vars()...'
        self.initialize_basin_vars()  # (5/14/10)
        #-----------------------------------------
        # This must come before "Disabled" test.
        #-----------------------------------------
        # print 'CHANNELS calling initialize_time_vars()...'
        self.initialize_time_vars()
        
        #----------------------------------
        # Has component been turned off ?
        #----------------------------------
        if (self.comp_status.lower() == 'disabled'):
            if not(self.SILENT):
                print('Channels component: Disabled in CFG file.')
            self.disable_all_output()   # (04/29/2020)
            self.DONE = True
            self.status = 'initialized'  # (OpenMI 2.0 convention) 
            return

##        print '################################################'
##        print 'min(d0), max(d0) =', self.d0.min(), self.d0.max()
##        print '################################################'
   
        #--------------------------------------------------------
        # Since only Grid type is allowed, these are not set in
        # the CFG file, but need to be defined for next part.
        #--------------------------------------------------------
        self.code_type  = 'Grid'  # (may not need this one)
        self.slope_type = 'Grid'

        #----------------------------------------
        # Initialize vars to be read from files
        #----------------------------------------
        self.initialize_input_file_vars()
  
        #------------------------------------------------------
        # Must now do this before read_input_files (11/11/16) 
        #------------------------------------------------------
        if not(self.SILENT):
            print('CHANNELS calling initialize_d8_vars()...')
        self.initialize_d8_vars()  # (depend on D8 flow grid)

        #---------------------------------------------------
        # Option to create channel geometry files from the
        # new D8 total contributing area (TCA) grid file
        #-------------------------------------------------------
        # topo_dir is appended to all input & output filenames
        #-------------------------------------------------------
        if (self.CREATE_CHANNEL_FILES):
            site_prefix = self.site_prefix
            self.d8_area_file = site_prefix + '_d8-area.rtg'

            #-------------------------------------------------
            # Create width_file from TCA file & CFG params
            # NOTE! This may overwrite existing width file!
            #-------------------------------------------------
            # os.chdir( topo_dir )  # not needed
            width_file = site_prefix + '_chan-w.rtg'
            parameterize.get_grid_from_TCA(site_prefix=site_prefix,
                         topo_dir=self.topo_directory,
                         area_file=self.d8_area_file,
                         out_file=self.width_file,  #### use different name?
                         g1=self.max_river_width,
                         p=self.channel_width_power)        

            #--------------------------------------------------
            # Create manning_file from TCA file & CFG params
            # NOTE! This may overwrite existing manning file!
            #--------------------------------------------------
            manning_file = site_prefix + '_chan-n.rtg'
            parameterize.get_grid_from_TCA(site_prefix=site_prefix,
                         topo_dir=self.topo_directory,
                         area_file=self.d8_area_file,
                         out_file=self.manning_file,   #### use different name?
                         g1=self.min_manning_n,
                         g2=self.max_manning_n )
             
            #------------------------------------------------
            # Create dbank_file from TCA file & CFG params
            # NOTE! This may overwrite existing dbank file!
            #------------------------------------------------
            ## dbank_file = site_prefix + '_d-bank.rtg'
            d_bankfull_file = self.d_bankfull_file
            parameterize.get_grid_from_TCA(site_prefix=self.site_prefix,
                    topo_dir=self.topo_directory,
                    area_file=self.d8_area_file,
                    out_file=d_bankfull_file,     #### use different name?
                    ## out_file=self.dbank_file,  #### use different name?
                    g1=self.max_bankfull_depth,
                    p=self.bankfull_depth_power )
                                                                                        
        #---------------------------------------------
        # Open input files needed to initialize vars 
        #---------------------------------------------
        # Can't move read_input_files() to start of
        # update(), since initial values needed here.
        #---------------------------------------------
        # print 'CHANNELS calling open_input_files()...'
        self.open_input_files()
        if not(self.SILENT):
            print('CHANNELS calling read_input_files()...')
        self.read_input_files()

        #--------------------------------------------
        # Set any input variables that are computed
        #--------------------------------------------------
        # NOTE:  Must be called AFTER read_input_files().
        #--------------------------------------------------
        if not(self.SILENT):
            print('CHANNELS calling set_computed_input_vars()...')
        self.set_computed_input_vars()
        
        #-----------------------
        # Initialize variables
        #-----------------------
        ## print 'CHANNELS calling initialize_d8_vars()...'
        ## self.initialize_d8_vars()  # (depend on D8 flow grid)
        if not(self.SILENT):
            print('CHANNELS calling initialize_computed_vars()...')
        self.initialize_computed_vars()

        #--------------------------------------------------
        # (5/12/10) I think this is obsolete now.
        #--------------------------------------------------
        # Make sure self.Q_ts_file is not NULL (12/22/05)  
        # This is only output file that is set by default
        # and is still NULL if user hasn't opened the
        # output var dialog for the channel process.
        #--------------------------------------------------
##        if (self.SAVE_Q_PIXELS and (self.Q_ts_file == '')):    
##            self.Q_ts_file = (self.case_prefix + '_0D-Q.txt')       

        self.open_output_files()
        self.status = 'initialized'  # (OpenMI 2.0 convention) 
        
    #   initialize()
    #-------------------------------------------------------------------
    def update(self, dt=-1.0):

        #---------------------------------------------
        # Note that u and d from previous time step
        # must be used on RHS of the equations here.
        #---------------------------------------------
        ## DEBUG = True
        DEBUG = False

        #--------------------------------
        # Has component been disabled ?
        #--------------------------------
        if (self.comp_status.lower() == 'disabled'):
            # Note: self.status should be 'initialized'.
            return

        #-------------------------------------------------------
        # There may be times where we want to call this method
        # even if component is not the driver.  But note that
        # the TopoFlow driver also makes this same call.
        #-------------------------------------------------------
        if (self.mode == 'driver') and not(self.SILENT):
            self.print_time_and_value(self.Q_outlet, 'Q_out', '[m^3/s]')
                                      ### interval=0.5)  # [seconds]

        #-------------------------------------------
        # Read from files as needed to update vars 
        #-----------------------------------------------------
        # NB! This is currently not needed for the "channel
        # process" because values don't change over time and
        # read_input_files() is called by initialize().
        # NB! read_input_files() is called in initialize().
        #-----------------------------------------------------
        # if (self.time_index > 0):
        #     if (DEBUG): print('#### Calling read_input_files()...')
        #     self.read_input_files()
        
        #-------------------------
        # Update computed values
        #--------------------------------------------------------------
        # Note:  Next part is needed for the original flood option
        #        where overbank flow could have its own D8 flow grid.
        #        This option is referred to as OPTION1 in this file.
        #        Comment out for "rectangle over trapezoid" method.
        #--------------------------------------------------------------        
#         if (self.FLOOD_OPTION):
#             if (DEBUG): print('#### Calling update_flood_d8_vars()...')
#             self.update_flood_d8_vars()  # (2019-09-17)
        #------------------------------------------------------------       
        if (DEBUG): print('#### Calling update_R()...')
        self.update_R()
        if (DEBUG): print('#### Calling update_R_integral()...')
        self.update_R_integral()
        if (DEBUG): print('#### Calling update_channel_discharge()...')
        self.update_channel_discharge()
        #------------------------------------------------------------
        if (self.FLOOD_OPTION):
            if (DEBUG): print('#### Calling update_flood_discharge()...')
            self.update_flood_discharge()   ############ (2019-09-20)
            if (DEBUG): print('#### Calling update_discharge()...')
            self.update_discharge()
        if (DEBUG): print('#### Calling update_diversions()...')
        self.update_diversions()
        if (DEBUG): print('#### Calling update_flow_volume()...')
        self.update_flow_volume()
        #------------------------------------------------------------
        if (self.FLOOD_OPTION):
            if (DEBUG): print('#### Calling update_channel_volume()...')
            self.update_channel_volume()  ############
            if (DEBUG): print('#### Calling update_flood_volume()...')
            self.update_flood_volume()     ############ (2019-09-20)
        if (DEBUG): print('#### Calling update_channel_depth()...')
        self.update_channel_depth()
        #------------------------------------------------------------
        if (self.FLOOD_OPTION):
            if (DEBUG): print('#### Calling update_flood_depth()...')
            self.update_flood_depth()      ############ (2019-09-20)
        #-----------------------------------------------------------------
        if not(self.DYNAMIC_WAVE):
            if (DEBUG): print('#### Calling update_trapezoid_Rh()...')
            self.update_trapezoid_Rh()
            # print 'Rhmin, Rhmax =', self.Rh.min(), self.Rh.max()a
        #-----------------------------------------------------------------
        # (9/9/14) Moved this here from update_velocity() methods.
        #-----------------------------------------------------------------        
        if not(self.KINEMATIC_WAVE):
            if (DEBUG): print('#### Calling update_free_surface_slope()...') 
            self.update_free_surface_slope()
        if (DEBUG): print('#### Calling update_shear_stress()...')
        self.update_shear_stress()
        if (DEBUG): print('#### Calling update_shear_speed()...')
        self.update_shear_speed()  
        #-----------------------------------------------------------------
        # Must update friction factor before velocity for DYNAMIC_WAVE.
        #-----------------------------------------------------------------        
        if (DEBUG): print('#### Calling update_friction_factor()...')
        self.update_friction_factor()      
        #-----------------------------------------------------------------          
        if (DEBUG): print('#### Calling update_velocity()...')
        self.update_velocity()
        self.update_velocity_on_edges()     # (set to zero)
        if (DEBUG): print('#### Calling update_froude_number()...')
        self.update_froude_number()
        #-----------------------------------------------------------------
##        print 'Rmin, Rmax =', self.R.min(), self.R.max()
##        print 'Qmin,  Qmax =',  self.Q.min(), self.Q.max()
##        print 'umin,  umax =',  self.u.min(), self.u.max()
##        print 'dmin,  dmax =',  self.d.min(), self.d.max()
##        print 'nmin,  nmax =',  self.nval.min(), self.nval.max()
##        print 'Rhmin, Rhmax =', self.Rh.min(), self.Rh.max()
##        print 'Smin,  Smax =',  self.S_bed.min(), self.S_bed.max()
        if (DEBUG): print('#### Calling update_outlet_values()...')
        self.update_outlet_values()
        if (DEBUG): print('#### Calling update peak values()...')
        self.update_peak_values()
        if (DEBUG): print('#### Calling update_Q_out_integral()...')
        self.update_Q_out_integral()
        if (DEBUG): print('#### Calling update_edge_values()...')
        self.update_edge_values()
        
        #---------------------------------------------
        # This takes extra time and is now done
        # only at the end, in finalize().  (8/19/13)
        #---------------------------------------------
        ## self.update_mins_and_maxes()

        #--------------------------------------------------
        # Check computed values (but not if known stable)
        #--------------------------------------------------
        if (self.CHECK_STABILITY):
            D_OK = self.check_flow_depth()
            U_OK = self.check_flow_velocity()
            ## U_OK = self.check_flow_velocity( CNEG=False )  ############
            OK   = (D_OK and U_OK)
        else:
            OK = True

        #----------------------------------------------
        # Write user-specified data to output files ?
        #----------------------------------------------
        # Components use own self.time_sec by default.
        #-----------------------------------------------
        if (DEBUG): print('#### Calling write_output_files()...')
        self.write_output_files()
        ## self.write_output_files( time_seconds )

        #-----------------------------
        # Update internal clock
        # after write_output_files()
        #-----------------------------
        if (DEBUG): print('#### Calling update_time()')
        self.update_time( dt )
        
        if (OK):
            self.status = 'updated'  # (OpenMI 2.0 convention)
        else:
            self.status = 'failed'
            self.DONE   = True
            
    #   update()
    #-------------------------------------------------------------------
    def finalize(self):

        #--------------------------------
        # Has component been disabled ?
        #--------------------------------
        if (self.comp_status.lower() == 'disabled'):
            # Note: self.status should be 'initialized'.
            return
 
        #---------------------------------------------------
        # We can compute mins and maxes in the final grids
        # here, but the framework will not then pass them
        # to any component (e.g. topoflow_driver) that may
        # need them.
        #---------------------------------------------------
        # Water flowing to noflow_IDs is tracked while the
        # model is running, not in finalize().
        #---------------------------------------------------
        self.status = 'finalizing'
        self.update_total_channel_water_volume()  ## (9/17/19)
        self.update_total_flood_water_volume()    ## (9/17/19)
        self.update_mins_and_maxes( REPORT=False )  ## (2/6/13)
        if not(self.SILENT):
            self.print_final_report(comp_name='Channels component')
        self.close_input_files()    # TopoFlow input "data streams"
        self.close_output_files()
        self.status = 'finalized'
        
    #   finalize()
    #-------------------------------------------------------------------
    def set_computed_input_vars(self):

        #---------------------------------------------------------------    
        # Note: The initialize() method calls initialize_config_vars()
        #       (in BMI_base.py), which calls this method at the end.
        #--------------------------------------------------------------
        cfg_extension = self.get_attribute( 'cfg_extension' ).lower()
        # cfg_extension = self.get_cfg_extension().lower()
        self.KINEMATIC_WAVE = ("kinematic" in cfg_extension)
        self.DIFFUSIVE_WAVE = ("diffusive" in cfg_extension)
        self.DYNAMIC_WAVE   = ("dynamic"   in cfg_extension)
                 
        #-------------------------------------------
        # These currently can't be set to anything
        # else in the GUI, but need to be defined.
        #-------------------------------------------
        self.code_type  = 'Grid'
        self.slope_type = 'Grid'  # (shouldn't need this)

        #---------------------------------------------------------
        # Make sure that all "save_dts" are larger or equal to
        # the specified process dt.  There is no point in saving
        # results more often than they change.
        # Issue a message to this effect if any are smaller ??
        #---------------------------------------------------------
        if (self.save_grid_dt < self.dt):
            print('--------------------------------------------------')
            print('NOTE:  save_grid_dt read from CFG file is less')
            print('       than the channel component timestep, dt.')
            print('       Will write grids at interval dt instead.')
            print('--------------------------------------------------')
            print()
        if (self.save_pixels_dt < self.dt):
            print('--------------------------------------------------')
            print('NOTE:  save_pixels_dt read from CFG file is less')
            print('       than the channel component timestep, dt.')
            print('       Will write values at interval dt instead.')
            print('--------------------------------------------------')
            print()            
        self.save_grid_dt   = np.maximum(self.save_grid_dt,   self.dt)
        self.save_pixels_dt = np.maximum(self.save_pixels_dt, self.dt)
        
    #   set_computed_input_vars()
    #-------------------------------------------------------------------
    def initialize_input_file_vars(self):    
    
        #---------------------------------------------------
        # Initialize vars to be read from files (11/16/16)
        #---------------------------------------------------
        # Need this in order to use "bmi.update_var()".
        #----------------------------------------------------------
        # NOTE: read_config_file() sets these to '0.0' if they
        #       are not type "Scalar", so self has the attribute.
        #----------------------------------------------------------
        dtype = 'float64'
        if (self.slope_type.lower() != 'scalar'):
            self.slope = self.initialize_var(self.slope_type, dtype=dtype)
        if (self.width_type.lower() != 'scalar'):
            self.width = self.initialize_var(self.width_type, dtype=dtype)
        if (self.angle_type.lower() != 'scalar'):
            self.angle = self.initialize_var(self.angle_type, dtype=dtype)
        if (self.sinu_type.lower() != 'scalar'):
            self.sinu  = self.initialize_var(self.sinu_type,  dtype=dtype)
        if (self.d0_type.lower() != 'scalar'):
            self.d0    = self.initialize_var(self.d0_type,    dtype=dtype)
        #-------------------------------------------------------------------------------- 
        if (self.d_bankfull_type.lower() != 'scalar'):
            self.d_bankfull = self.initialize_var(self.d_bankfull_type, dtype=dtype)  
#         if (self.w_bankfull_type.lower() != 'scalar'):
#             self.w_bankfull = self.initialize_var(self.w_bankfull_type, dtype=dtype)    
        #-------------------------------------------------------------------------------- 
        if (self.MANNING):
            if (self.nval_type.lower() != 'scalar'):   
                self.nval  = self.initialize_var(self.nval_type, dtype=dtype)
        if (self.LAW_OF_WALL):
            if (self.z0val_type.lower() != 'scalar'):      
                self.z0val = self.initialize_var(self.z0val_type, dtype=dtype)
                
    #   initialize_input_file_vars()
    #-------------------------------------------------------------------
    def initialize_d8_vars(self):

        #---------------------------------------------
        # Compute and store a variety of (static) D8
        # flow grid variables.  Embed structure into
        # the "channel_base" component.
        #---------------------------------------------
        self.d8 = d8_base.d8_component()

        #--------------------------------------------------        
        # We don't need any of this now.  See Note below.
        #--------------------------------------------------
#         self.d8.site_prefix  = self.site_prefix
#         self.d8.case_prefix  = self.case_prefix
#         self.d8.in_directory = self.in_directory
#         self.d8.cfg_directory = self.cfg_directory

        #--------------------------------------------------         
        # D8 component builds its cfg filename from these  
        #-------------------------------------------------------------
        # (2/11/2017) The initialize() method in d8_base.py now
        # uses case_prefix (vs. site_prefix) for its CFG file:
        # <site_prefix>_d8_global.cfg.  This is to prevent confusion
        # since this was the only CFG file that used site_prefix.
        #-------------------------------------------------------------
        # Note:  This D8 component is serving a channels component
        #        that has already been instantiated and knows its
        #        directory and prefix information.  So we can build
        #        the correct D8 cfg_file name from that info.  It
        #        will then read path_info CFG file to get other info.
        #-------------------------------------------------------------
        cfg_file = (self.case_prefix + '_d8_global.cfg')
        cfg_file = (self.cfg_directory + cfg_file)
        self.d8.initialize( cfg_file=cfg_file, SILENT=self.SILENT, \
                            REPORT=self.REPORT )
        
        #---------------------------------------------------
        # The next 2 "update" calls are needed when we use
        # the new "d8_base.py", but are not needed when
        # using the older "tf_d8_base.py".      
        #---------------------------------------------------
        self.d8.update(self.time, REPORT=self.REPORT)

        #----------------------------------------------------------- 
        # Note: This is also needed, but is not done by default in
        #       d8.update() because it hurts performance of Erode.
        #----------------------------------------------------------- 
        self.d8.update_noflow_IDs(REPORT=self.REPORT)

        #-------------------------------------------------------- 
        # Initialize separate set of d8 vars for flooding.
        # NOTE!  d8f is really only needed for OPTION1 flooding
        #        method, but is still used in a few places
        #        whenever (self.FLOOD_OPTION) is on.
        #--------------------------------------------------------
        if (self.FLOOD_OPTION): 
            d8f = copy.copy( self.d8 )  # (or use "copy.deepcopy"?)
            d8f.FILL_PITS_IN_Z0 = False
            d8f.LINK_FLATS      = False
            self.d8f = d8f

    #   initialize_d8_vars()
    #-------------------------------------------------------------
    def initialize_computed_vars(self):

        #--------------------------------------------------------
        # (5/17/12) If MANNING, we need to set z0vals to -1 so
        # they are always defined for use with EMELI framework.
        #--------------------------------------------------------
        # BMI_base.read_config_file() reads "float" scalars as
        # numpy "float64" data type.  Applying np.float64()
        # will break references.
        #--------------------------------------------------------
        dtype = 'float64'
        if (self.MANNING):
            if (self.nval is not None):
                self.nval_min = self.nval.min()
                self.nval_max = self.nval.max()
                if not(self.SILENT):
                    print('    min(nval)       = ' + str(self.nval_min) )
                    print('    max(nval)       = ' + str(self.nval_max) )
            #-------------------------------------------------------------
            self.z0val     = self.initialize_scalar(-1, dtype=dtype)
            self.z0val_min = self.initialize_scalar(-1, dtype=dtype)
            self.z0val_max = self.initialize_scalar(-1, dtype=dtype)
            
        if (self.LAW_OF_WALL):
            if (self.z0val is not None):
                self.z0val_min = self.z0val.min()
                self.z0val_max = self.z0val.max()
                if not(self.SILENT):
                    print('    min(z0val)      = ' + str(self.z0val_min) )
                    print('    max(z0val)      = ' + str(self.z0val_max) )
            #-------------------------------------------------------------
            self.nval      = self.initialize_scalar(-1, dtype=dtype)
            self.nval_min  = self.initialize_scalar(-1, dtype=dtype)
            self.nval_max  = self.initialize_scalar(-1, dtype=dtype)

        #------------------------------------------------------------           
        # If neither set, use a constant velocity?  (Test: 5/18/15)
        #------------------------------------------------------------
        if not(self.MANNING) and not(self.LAW_OF_WALL):
            print('#### WARNING: In CFG file, MANNING=0 and LAW_OF_WALL=0.')
            #-------------------------------------------------------------
            self.z0val     = self.initialize_scalar(-1, dtype=dtype)
            self.z0val_min = self.initialize_scalar(-1, dtype=dtype)
            self.z0val_max = self.initialize_scalar(-1, dtype=dtype)
            #-------------------------------------------------------------            
            self.nval      = self.initialize_scalar(-1, dtype=dtype)
            self.nval_min  = self.initialize_scalar(-1, dtype=dtype)
            self.nval_max  = self.initialize_scalar(-1, dtype=dtype)

        #-----------------------------------------------
        # Convert bank angles from degrees to radians. 
        #-------------------------------------------------
        # This is now done here in all cases.  Before,
        # when bank angles were given as a GRID, this was
        # done in read_input_files().  Then realized that
        # that conversion didn't occur for SCALAR angle.
        # This caused "denom" later to be negative.
        # (Fixed on: 2019-10-08.)
        #-------------------------------------------------
        self.angle *= self.deg_to_rad   # [radians] 
            
#         if (self.angle_type.lower() == 'scalar'):
#             self.angle *= self.deg_to_rad   # [radians]   

        #--------------------------------------------------------
        # Trapezoid bottom width (width) may be zero on 4 edges
        # of DEM, but this can result in a "divide by zero"
        # error later on, so need to adjust.
        #--------------------------------------------------------
        w1 = ( self.width == 0 )   # (boolean array)
        n1 = w1.sum()
        if (n1 > 0):
            self.width[w1] = self.d8.dw[w1]

        #-----------------------------------------------
        # Print mins and maxes of some other variables
        # that were initialized by read_input_files().
        #-----------------------------------------------
        if not(self.SILENT):
            ## print('    min(slope)      = ' + str(self.slope.min()) )
            ## print('    max(slope)      = ' + str(self.slope.max()) )
            print('    min(width)      = ' + str(self.width.min()) )
            print('    max(width)      = ' + str(self.width.max()) )
            print('    min(angle)      = ' + str(self.angle.min() * self.rad_to_deg) + ' [deg]')
            print('    max(angle)      = ' + str(self.angle.max() * self.rad_to_deg) + ' [deg]')
            print('    min(sinuosity)  = ' + str(self.sinu.min()) )
            print('    max(sinuosity)  = ' + str(self.sinu.max()) )
            print('    min(init_depth) = ' + str(self.d0.min()) )
            print('    max(init_depth) = ' + str(self.d0.max()) )

        #------------------------------------------------
        # 8/29/05.  Multiply ds by (unitless) sinuosity
        # Orig. ds is used by subsurface flow
        #------------------------------------------------
        # NB!  We should also divide slopes in S_bed by
        # the sinuosity, as now done here.
        #----------------------------------------------------
        # NB!  This saves a modified version of ds that
        #      is only used within the "channels" component.
        #      The original "ds" is stored within the
        #      topoflow model component and is used for
        #      subsurface flow, etc.
        #----------------------------------------------------
        ### self.d8.ds_chan = (self.sinu * ds)
        ### self.ds = (self.sinu * self.d8.ds)
        self.d8.ds = (self.sinu * self.d8.ds)

        ###################################################
        ###################################################
        ### S_bed = (S_bed / self.sinu)     #*************
        self.slope = (self.slope / self.sinu)
        self.S_bed  = self.slope
        self.S_free = self.S_bed.copy()  # (2020-04-29)

        ###################################################
        ###################################################
        
        #---------------------------
        # Initialize spatial grids
        #-----------------------------------------------
        # NB!  It is not a good idea to initialize the
        # water depth grid to a nonzero scalar value.
        #-----------------------------------------------
        if not(self.SILENT):
            print('Initializing u, f, d grids...')
        self.u = self.initialize_grid( 0, dtype=dtype )
        self.f = self.initialize_grid( 0, dtype=dtype )
        self.d = self.initialize_grid( 0, dtype=dtype )
        self.d += self.d0  # (Add initial depth, if any.)

        #------------------------------------------
        # Use a constant velocity (Test: 5/18/15)
        #------------------------------------------
        # if not(self.MANNING) and not(self.LAW_OF_WALL):
        #    ## self.u[:] = 1.5  # [m/s]
        #    self.u[:] = 3.0  # [m/s]
            
        #########################################################
        # Add this on (2/3/13) so make the TF driver happy
        # during its initialize when it gets reference to R.
        # But in "update_R()", be careful not to break the ref.
        # "Q" may be subject to the same issue.
        #########################################################
        self.R  = self.initialize_grid( 0, dtype=dtype )
      
        ##############################################################################
        # seconds_per_year = 3600 * 24 * 365 = 31,536,000
        # mm_per_meter     = 1000
        ##############################################################################
        # baseflow_rate     = 250.0   # [mm per year],  was 230.0
        # baseflow_rate_mps = baseflow_rate / (31536000.0 * 1000.0)  #[m/s]
        # self.GW_init = np.zeros([self.ny, self.nx], dtype=dtype)
        # self.GW_init += baseflow_rate_mps
        ##############################################################################

        #---------------------------------------------------
        # Initialize new grids. Is this needed?  (9/13/14)
        #---------------------------------------------------
        self.tau    = self.initialize_grid( 0, dtype=dtype )
        self.u_star = self.initialize_grid( 0, dtype=dtype)
        self.froude = self.initialize_grid( 0, dtype=dtype )
                        
        #---------------------------------------
        # These are used to check mass balance
        #---------------------------------------
        # vol_edge is total flow to noflow_IDs.
        #----------------------------------------
        self.vol_R    = self.initialize_scalar( 0, dtype=dtype)
        self.vol_Q    = self.initialize_scalar( 0, dtype=dtype)
        #------------------------------------------------------------- 
        self.vol_edge      = self.initialize_scalar( 0, dtype=dtype)
        self.vol_chan_sum  = self.initialize_scalar( 0, dtype=dtype)
        self.vol_chan_sum0 = self.initialize_scalar( 0, dtype=dtype)  
        self.vol_flood_sum = self.initialize_scalar( 0, dtype=dtype) 

        #-------------------------------------------
        # Make sure all slopes are valid & nonzero
        # since otherwise flow will accumulate
        #-------------------------------------------
        if (self.KINEMATIC_WAVE):    
            self.remove_bad_slopes()      #(3/8/07. Only Kin Wave case)
            #----------------------------------------------
            # Use "get_new_slope_grid()" in new_slopes.py
            # instead of "remove_bad_slopes()".
            # Or change "slope_grid" in the CFG file.
            #----------------------------------------------
            ## self.get_new_slope_grid()
            
        #------------------------------------------------
        # Initial volume of channel water in each pixel
        #-----------------------------------------------------------
        # Note: angles were read as degrees & converted to radians
        # vol_chan_sum0 = initial water volume in all channels
        #-----------------------------------------------------------
        L2            = self.d * np.tan(self.angle)
        self.A_wet    = self.d * (self.width + L2)
        self.P_wet    = self.width + (np.float64(2) * self.d / np.cos(self.angle) )
        self.vol_chan = self.A_wet * self.d8.ds   # [m3]
        self.update_total_channel_water_volume()
        self.vol_chan_sum0 = self.vol_chan_sum.copy()
        ### self.vol_chan_sum0 = self.vol_chan.sum()
        
        #--------------------------------------------       
        # Used to reduce flashiness of hydrograph
        # with a Nash linear reservoir, or similar.
        #--------------------------------------------
        self.vol_stored = self.initialize_grid(0, dtype=dtype)
        self.u_overland = 0.01  # (m/s)   # not used currently

        #-----------------------------------------
        # Added these new variables for flooding
        # Starting in Sep. 2019.
        #----------------------------------------------------
        # Q  = total discharge
        # Qc = channel flow discharge
        # Qf = overbank (flood) flood discharge
        #----------------------------------------------------
        # vol = vol_chan + vol_flood
        # width_ratio = floodplain width to channel width
        # It is used for "rectangle over trapezoid" method
        #   which assumes Qc and Qf use same D8 codes.
        # Rosgen says width_ratio in about (3, 10).
        # Value of 5 worked well for Omo River, Ethiopia.
        #----------------------------------------------------
        self.Qc      = self.initialize_grid( 0, dtype=dtype )
        self.d_flood = self.initialize_grid( 0, dtype=dtype )
        if (self.FLOOD_OPTION):
            self.vol = self.vol_chan.copy()
            self.Qf  = self.initialize_grid( 0, dtype=dtype )
            self.Q   = self.initialize_grid( 0, dtype=dtype )
            self.flood_manning_n = 0.10  ##########
            self.width_ratio = 5.0 
        else:
            self.Q   = self.Qc   # (2 names for same thing)
            self.vol = self.vol_chan   # (synonym)
        
        #---------------------------------------------------------
        # Volume of water in channel when bankfull  (2019-09-16)
        # Note that w_bankfull is not used here, but:
        #   w_bankfull = width + (2 * d_bankfull * tan(angle))
        #   width = w_bankfull - (2 * d_bankfull * tan(angle))
        #---------------------------------------------------------
        # Ac = area of trapezoid with bottom width, w, depth, d,
        #      and flare angle, a
        #    = area of rectangle 1 (w * d) +
        #      area of rectangle 2 (two triangles, d^2 * tan(a)
        # L3 = "bank width" (zero if angle = 0)
        #--------------------------------------------------------- 
        L3                = self.d_bankfull * np.tan(self.angle)
        Ac_bankfull       = self.d_bankfull * (self.width + L3)
        self.vol_bankfull = Ac_bankfull * self.d8.ds
        self.vol_flood = self.initialize_grid( 0, dtype=dtype) 

        #-------------------------------------------------------        
        # Note: depth is often zero at the start of a run, and
        # both width and then P_wet are also zero in places.
        # Therefore initialize Rh as shown.
        #-------------------------------------------------------
        self.Rh = self.initialize_grid( 0, dtype=dtype )
        ## self.Rh = self.A_wet / self.P_wet   # [m]
        ## print 'P_wet.min() =', self.P_wet.min()
        ## print 'width.min() =', self.width.min()

        ## self.initialize_diversion_vars()    # (9/22/14)
        self.initialize_outlet_values()
        self.initialize_peak_values()
        self.initialize_min_and_max_values()  ## (2/3/13)

    #   initialize_computed_vars()
    #-------------------------------------------------------------
    def initialize_diversion_vars(self):

        #-----------------------------------------
        # Compute source IDs from xy coordinates
        #-----------------------------------------
        source_rows     = np.int32( self.sources_y / self.ny )
        source_cols     = np.int32( self.sources_x / self.nx )
        self.source_IDs = (source_rows, source_cols)
        ## self.source_IDs = (source_rows * self.nx) + source_cols
   
        #---------------------------------------
        # Compute sink IDs from xy coordinates
        #---------------------------------------
        sink_rows     = np.int32( self.sinks_y / self.ny )
        sink_cols     = np.int32( self.sinks_x / self.nx )
        self.sink_IDs = (sink_rows, sink_cols)
        ## self.sink_IDs = (sink_rows * self.nx) + sink_cols
        
        #-------------------------------------------------
        # Compute canal entrance IDs from xy coordinates
        #-------------------------------------------------
        canal_in_rows     = np.int32( self.canals_in_y / self.ny )
        canal_in_cols     = np.int32( self.canals_in_x / self.nx )
        self.canal_in_IDs = (canal_in_rows, canal_in_cols)
        ## self.canal_in_IDs = (canal_in_rows * self.nx) + canal_in_cols
        
        #---------------------------------------------
        # Compute canal exit IDs from xy coordinates
        #---------------------------------------------
        canal_out_rows     = np.int32( self.canals_out_y / self.ny )
        canal_out_cols     = np.int32( self.canals_out_x / self.nx )
        self.canal_out_IDs = (canal_out_rows, canal_out_cols)
        ## self.canal_out_IDs = (canal_out_rows * self.nx) + canal_out_cols

        #--------------------------------------------------
        # This will be computed from Q_canal_fraction and
        # self.Q and then passed back to Diversions
        #--------------------------------------------------
        self.Q_canals_in = np.array( self.n_sources, dtype='float64' )

    #   initialize_diversion_vars()
    #-------------------------------------------------------------------
    def initialize_outlet_values(self):

        #---------------------------------------------------
        # Note:  These are retrieved and used by TopoFlow
        #        for the stopping condition.  TopoFlow
        #        receives a reference to these, but in
        #        order to see the values change they need
        #        to be stored as mutable, 1D numpy arrays.
        #---------------------------------------------------
        # Note:  Q_last is internal to TopoFlow.
        #--------------------------------------------------- 
        dtype = 'float64'       
        # self.Q_outlet = self.Q[ self.outlet_ID ]
        self.Q_outlet = self.initialize_scalar(0, dtype=dtype)
        self.u_outlet = self.initialize_scalar(0, dtype=dtype)
        self.d_outlet = self.initialize_scalar(0, dtype=dtype)
        self.f_outlet = self.initialize_scalar(0, dtype=dtype)
          
    #   initialize_outlet_values()  
    #-------------------------------------------------------------------
    def initialize_peak_values(self):

        #-------------------------
        # Initialize peak values
        #-------------------------
        dtype = 'float64'
        self.Q_peak  = self.initialize_scalar(0, dtype=dtype)
        self.T_peak  = self.initialize_scalar(0, dtype=dtype)
        self.u_peak  = self.initialize_scalar(0, dtype=dtype)
        self.Tu_peak = self.initialize_scalar(0, dtype=dtype) 
        self.d_peak  = self.initialize_scalar(0, dtype=dtype)
        self.Td_peak = self.initialize_scalar(0, dtype=dtype)

    #   initialize_peak_values()
    #-------------------------------------------------------------------
    def initialize_min_and_max_values(self):

        #-------------------------------
        # Initialize min & max values
        # (2/3/13), for new framework.
        #-------------------------------
        v = 1e6
        dtype = 'float64'
        self.Q_min = self.initialize_scalar(v,  dtype=dtype)
        self.Q_max = self.initialize_scalar(-v, dtype=dtype)
        self.u_min = self.initialize_scalar(v,  dtype=dtype)
        self.u_max = self.initialize_scalar(-v, dtype=dtype)
        self.d_min = self.initialize_scalar(v,  dtype=dtype)
        self.d_max = self.initialize_scalar(-v, dtype=dtype)

    #   initialize_min_and_max_values() 
    #-------------------------------------------------------------------
    def update_flood_d8_vars(self):

        #---------------------------------------------------------    
        # Note:  Use free-surface gradient of d_flood to compute
        #        flow to neighbors.  (209-09-17)
        #---------------------------------------------------------
        # Note:  self.d_flood is used to compute self.Q.
        #---------------------------------------------------------
        self.FLOODING = (self.d_flood.max() > 0)
        if not(self.FLOODING):
            d8f = copy.copy( self.d8 )
            d8f.SILENT          = True
            d8f.FILL_PITS_IN_Z0 = False
            d8f.LINK_FLATS      = False
            self.d8f = d8f
            return

        #-------------------------------------------------------- 
        # Use (DEM + d_flood) to compute a free-surface gradient
        # and update all of the D8 vars.
        # self.d8f.d8_grid gives the D8 flow codes
        #--------------------------------------------------------        
        z_free = (self.d8.DEM + self.d_flood)
        #---------------------------------------
        self.d8f.update_flow_grid( DEM=z_free )    ######
        self.d8f.update_parent_ID_grid()
        self.d8f.update_parent_IDs()     # (needed for gradients)
        self.d8f.update_flow_from_IDs()
        self.d8f.update_flow_to_IDs()
        self.d8f.update_noflow_IDs()  # (needed to fill depressions naturally)
        self.d8f.update_flow_width_grid()   # (dw)
        self.d8f.update_flow_length_grid()  # (ds)
        ### self.d8f.update_area_grid()
        #-----------------------------------------------------------
        # NOTE: While z_free was passed to update_flow_grid(), it
        # is not saved in d8f as self.DEM.  It probably should be,
        # since update_slope_grid() uses self.DEM.  Then should
        # use d8f.S in Manning formula for "flood velocity", uf.
        # See update_flood_discharge() where uf is computed.
        # May have issue with slopes of zero, however.
        #-----------------------------------------------------------
        # self.d8f.DEM = z_free  ### Should we do this ??
        # self.d8f.update_slope_grid()
    
    #   update_flood_d8_vars()
    #-------------------------------------------------------------------
    # def update_excess_rainrate(self):
    def update_R(self):

        #----------------------------------------
        # Compute the "excess rainrate", R.
        # Each term must have same units: [m/s]
        # Sum = net gain/loss rate over pixel.
        #----------------------------------------------------
        # R can be positive or negative.  If negative, then
        # water is removed from the surface at rate R until
        # surface water is consumed.
        #--------------------------------------------------------------
        # P  = precip_rate   [m/s]  (converted by read_input_data()).
        # SM = snowmelt rate [m/s]
        # GW = seep rate     [m/s]  (water_table intersects surface)
        # ET = evap rate     [m/s]
        # IN = infil rate    [m/s]
        # MR = icemelt rate  [m/s]

        #-------------------------------------------------------------
        # NB!  Don't do this here, because vol_GW won't get to the
        #      TopoFlow driver component for mass balance check.
        #      Try to achieve this with a new satzone component.
        #-------------------------------------------------------------
        # Enforce min_baseflow_flux for GW ? (2021-07-24) (in-place)
        # Note: min_baseflow_flux is a uniform volume_flux.
        # Note: min_baseflow discharge = min_baseflow_flux * area
        #-------------------------------------------------------------
#         if (self.min_baseflow_flux > 0):
#             np.maximum( self.GW, self.min_baseflow_flux_mps, self.GW)
# 
#             #------------------------------------------------
#             # Update mass total for GW, sum over all pixels
#             #------------------------------------------------   
#             volume = np.double(self.GW * self.da * self.dt)  # [m^3]
#             if (np.size( volume ) == 1):
#                 self.vol_GW += (volume * self.rti.n_pixels)
#             else:
#                 self.vol_GW += np.sum(volume)

        #------------------------------------------------------
        # Option for a fixed fraction of P_rain to infiltrate
        # and get used as Rg in satzone_attenuate.py
        # If ATTENUATE is not in CFG file, it is set in:
        # set_missing_cfg_options().
        #------------------------------------------------------
#         imin = self.IN.min()
#         if (imin == 0) and (self.ATTENUATE):
#             fraction = 0.9
#             self.IN  = self.P_rain * fraction 
   
        #------------------------------------------------------
        # Volume fluxes from different processes are obtained
        # via BMI from other process model components.
        #------------------------------------------------------     
        P  = self.P_rain  # (This is now liquid-only precip. 9/14/14)
        SM = self.SM   # (snowmelt_volume_flux)
        GW = self.GW   # (baseflow_volume_flux or seepage_rate)
        ET = self.ET   # (ET_volume_flux;  potential vs. actual)
        IN = self.IN   # (surface_infiltration_volume_flux)
        MR = self.MR   # (icemelt_volume_flux)
        
##        if (self.DEBUG):
##            print 'At time:', self.time_min, ', P =', P, '[m/s]'

        #--------------------------------------
        # Compute actual ET from potential ET
        #---------------------------------------------------
        # NB!  R can be negative and will result in a loss
        #      of water volume in update_volume().
        #      But can't evaporate water if not present.
        #---------------------------------------------------
        w = (self.vol < (ET * self.dt))
        if (ET.ndim == self.vol.ndim):
            ET[w] = 0.0
        else:
            ET = 0.0

        #--------------
        # For testing
        #-------------- 
#         print('type(P)  =', type(P))
#         print('type(SM) =', type(SM))
#         print('type(GW) =', type(GW))
#         print('type(ET) =', type(ET))
#         print('type(IN) =', type(IN))
#         print('type(MR) =', type(MR))
     
#         print( '(Pmin,  Pmax)  = ' + str(P.min())  + ', ' + str(P.max()) )
#         print( '(SMmin, SMmax) = ' + str(SM.min()) + ', ' + str(SM.max()) )
#         print( '(GWmin, GWmax) = ' + str(GW.min()) + ', ' + str(GW.max()) )
#         print( '(ETmin, ETmax) = ' + str(ET.min()) + ', ' + str(ET.max()) )
#         print( '(INmin, INmax) = ' + str(IN.min()) + ', ' + str(IN.max()) )
#         print( '(MRmin, MRmax) = ' + str(MR.min()) + ', ' + str(MR.max()) )
#         print( ' ' )
        
        self.R = (P + SM + GW + MR) - (ET + IN)
        
#         print('### time_index =', self.time_index)    
#         print('### R =', self.R)
#         print()

    #   update_R()
    #-------------------------------------------------------------------
    def update_R_integral(self):

        #-----------------------------------------------
        # Update mass total for R, sum over all pixels
        #---------------------------------------------------------------
        # Note:  Typically, chan_dt < met_dt, so that vol_R is updated
        # more frequently than vol_P.  Since EMELI performs linear
        # interpolation in time, integrals may be slightly different.
        #---------------------------------------------------------------  
        volume = np.double(self.R * self.da * self.dt)  # [m^3]
        if (np.size(volume) == 1):
            self.vol_R += (volume * self.rti.n_pixels)
        else:
            self.vol_R += np.sum(volume)

    #   update_R_integral()           
    #-------------------------------------------------------------------  
    def update_channel_discharge(self):

        #---------------------------------------------------------
        # The discharge grid, Q, gives the flux of water _out_
        # of each grid cell.  This entire amount then flows
        # into one of the 8 neighbor grid cells, as indicated
        # by the D8 flow code. The update_flow_volume() function
        # is called right after this one in update() and uses
        # the Q grid.
        #---------------------------------------------------------
        # 7/15/05.  The cross-sectional area of a trapezoid is
        # given by:    Ac = d * (w + (d * tan(theta))),
        # where w is the bottom width.  If we were to
        # use: Ac = w * d, then we'd have Ac=0 when w=0.
        # We also need angle units to be radians.
        #---------------------------------------------------------
  
        #-----------------------------
        # Compute the discharge grid
        #------------------------------------------------------ 
        # A_wet is initialized in initialize_computed_vars().
        # A_wet is updated in update_trapezoid_Rh().
        #------------------------------------------------------     
        self.Qc[:] = self.u * self.A_wet   # (2/19/13, in place)

    #   update_channel_discharge()
    #-------------------------------------------------------------------  
    def update_flood_discharge(self):

        #------------------------------------------
        # Find grid cells with & without flooding
        #--------------------------------------------
        # Note: uf=0 when d_flood=0, and then Qf=0.
        #       So we should not need w1 and w2,
        #       as long as d_flood >= 0.
        #       See update_flood_depth().
        #--------------------------------------------
        ## w1 = (self.d_flood > 0)  # (array of True or False)
        ## w2 = np.invert( w1 )

        #-----------------------------------------------------
        # Looks like we need S_free to include flood depth.    
        # Otherwise, if Sf happens to very small in some grid
        # cell, it can cause water to "pile up", resulting in
        # a very large flood depth in that cell.
        #-----------------------------------------------------        
        if (self.KINEMATIC_WAVE):
            Sf = self.S_bed
        else:
            Sf = self.S_free
            
        #-------------------------------
        # Compute flood water velocity
        #-------------------------------
        nf  = self.flood_manning_n
        Rhf = self.d_flood
        Sfp = np.abs(Sf)
        uf  = (Rhf ** self.two_thirds) * np.sqrt(Sfp) / nf
        #-------------------------------------------------
        # Should we allow flood velocity to be negative,
        # so we can capture backwater effects?
        #-------------------------------------------------
        # w1 = (Sf < 0)
        # uf[ w1 ] *= -1   #######################
                
        #------------------------------------------------
        # Compute discharge due to overbank flow
        # See manning_formula() function in this file.
        #------------------------------------------------
        n  = self.width_ratio  # (floodplain to channel)
        Af = n * self.width * self.d_flood
        self.Qf[:] = uf * Af  # (in place)
        #------------------------------------------
        ## self.Qf[ w1 ] = uf[ w1 ] * Af[ w1 ]  # (in place)   
        ## self.Qf[ w2 ] = 0.0

    #   update_flood_discharge()
    #------------------------------------------------------------------- 
    def update_flood_discharge_OPTION1(self):
       
        #--------------------------------------------
        # Find grid cells with & without flooding
        #--------------------------------------------
        # Note: uf=0 when d_flood=0, and then Qf=0.
        #       So we should not need w1 and w2,
        #       as long as d_flood >= 0.
        #       See update_flood_depth().
        #--------------------------------------------
#         w1 = (self.d_flood > 0)  # (array of True or False)
#         w2 = np.invert( w1 )

        #-------------------------------
        # Compute flood water velocity
        #---------------------------------------------------
        # Note:  S_bed is channel slope of the DEM, but D8
        #        flow direction for flooding is based on
        #        slope of z_free = (DEM + d_flood).
        #        See update_flood_d8_vars().
        #---------------------------------------------------
        ### Sf  = self.d8f.S        
        Sf  = self.S_bed
        nf  = self.flood_manning_n
        Rhf = self.d_flood
        uf  = (Rhf ** self.two_thirds) * np.sqrt(Sf) / nf
        
        #---------------------------------------------------
        # (2019-09-16)  Add discharge due to overbank flow
        # See manning_formula() function in this file.
        #---------------------------------------------------
        Af = (self.d8f.dw * self.d_flood)    ##### CHECK dw
        self.Q[:] = uf * Af   # (in place)
        #---------------------------------------------------
#         self.Qf[ w1 ] = uf[ w1 ] * Af[ w1 ]  # (in place)   
#         self.Qf[ w2 ] = 0.0

    #   update_flood_discharge_OPTION1()
    #-------------------------------------------------------------------   
    def update_discharge(self):

        #------------------------------------------------------------    
        # Note:  This is not finished yet.  The fact that channel
        #        flow and overbank flooding flow can have different
        #        D8 flow directions, with the flooding flow direction
        #        switching back and forth, can result in an oscillation
        #        or spikiness in the hydrograph.  It is not yet
        #        clear how to best handle this.  Reducing the timestep
        #        does not seem to resolve the issue.  However, flood
        #        depths seem to be well-behaved.
        #------------------------------------------------------------
        if (self.FLOOD_OPTION):
            #------------------------------------------             
            # Look at where the 2 D8 flow grids align
            # First part here with w1 is solid.
            #------------------------------------------            
            # w1 = (self.d8.d8_grid == self.d8f.d8_grid)
            # w2 = np.invert( w1 )
            ## self.Q[ w1 ] = self.Qc[ w1 ] + self.Qf[ w1 ]
            #--------------------------------------------------
            # Not sure how to handle w2 grid cells.  This
            # just makes it easy to see where the D8 flow
            # directions differ, at places in main channels.
            #--------------------------------------------------
            ## self.Q[ w2 ] = 0.0
            
            # This part with w1 is also solid.
#             w1 = (self.Qf == 0)
#             w2 = np.invert( w1 )
#             self.Q[ w1 ] = self.Qc[ w1 ]
            
            #-----------------------------------------------------
            # This is correct if the D8 flow grids for Qc and
            # Qf are the same.  It isn't 100% correct otherwise.
            #-----------------------------------------------------
            self.Q[:] = self.Qc + self.Qf
 
            #---------------------------------------------------------            
            # This gives smoother hydrographs in main channels (with
            # some spikes still), but has Q=0 for most grid cells.
            #--------------------------------------------------------- 
            ## self.Q[:] = self.Qf

            #-------------------------------------------------
            # A compromise, but hydrograph still has spikes, 
            # even with timestep of 1 second for Treynor.
            #-------------------------------------------------
            # np.maximum( self.Qc, self.Qf, self.Q)  # (in place)
 
            #---------------------------------------------------
            # Average with previous time step to smooth spikes,
            # thought due to switching of flow direction.
            # Hydrographs are much smoother.
            #----------------------------------------------------
#             Q2 = (self.Qc[ w2 ] + self.Qf[ w2 ])
#             Q3 = (self.Q[ w2 ] + Q2) / 2.0
#             self.Q[ w2 ] = Q3
            ### self.Q[ w2 ] = (self.Qc + self.Qf) / 2.0  # (in place)

            # For another idea             
            ## self.Q[ self.d8f.parent_IDs ]

            ### self.Q[ w2 ] = self.Qc[ w2 ]  + self.Qf[ w2 ]/2.0   ###############
            ### self.Q[ w2 ] = self.Qc[ w2 ]   ####################
            
            ## self.Q[:] = self.Qc + self.Qf
        else:
            # Set self.Q = self.Qc in initialize().
            dum = 0

    #   update_discharge()
    #-------------------------------------------------------------------
    def update_diversions(self):

        #--------------------------------------------------------------    
        # Note: The Channel component requests the following input
        #       vars from the Diversions component by including
        #       them in its "get_input_vars()":
        #       (1) Q_sources, Q_sources_x, Q_sources_y
        #       (2) Q_sinks,   Q_sinks_x, Q_sinks_y
        #       (3) Q_canals_out, Q_canals_out_x, Q_canals_out_y
        #       (4) Q_canals_fraction, Q_canals_in_x, Q_canals_in_y.
        
        #       source_IDs are computed from (x,y) coordinates during
        #       initialize().
        #
        #       Diversions component needs to get Q_canals_in from the
        #       Channel component.
        #--------------------------------------------------------------
        # Note: This *must* be called after update_discharge() and
        #       before update_flow_volume().
        #--------------------------------------------------------------
        # Note: The Q grid stores the volume flow rate *leaving* each
        #       grid cell in the domain.  For sources, an extra amount
        #       is leaving the cell which can flow into its D8 parent
        #       cell.  For sinks, a lesser amount is leaving the cell
        #       toward the D8 parent.
        #--------------------------------------------------------------
        # Note: It is not enough to just update Q and then call the
        #       update_flow_volume() method.  This is because it
        #       won't update the volume in the channels in the grid
        #       cells that the extra discharge is leaving from.
        #--------------------------------------------------------------
        # If a grid cell contains a "source", then an additional Q
        # will flow *into* that grid cell and increase flow volume.
        #-------------------------------------------------------------- 

        #-------------------------------------------------------------         
        # This is not fully tested but runs.  However, the Diversion
        # vars are still computed even when Diversions component is
        # disabled. So it slows things down somewhat.
        #-------------------------------------------------------------              
        return
        ########################
        ########################
        
        #----------------------------------------            
        # Update Q and vol due to point sources
        #----------------------------------------
        ## if (hasattr(self, 'source_IDs')): 
        if (self.n_sources > 0): 
            self.Q[ self.source_IDs ]   += self.Q_sources
            self.vol[ self.source_IDs ] += (self.Q_sources * self.dt)

        #--------------------------------------            
        # Update Q and vol due to point sinks
        #--------------------------------------
        ## if (hasattr(self, 'sink_IDs')):
        if (self.n_sinks > 0): 
            self.Q[ self.sink_IDs ]   -= self.Q_sinks
            self.vol[ self.sink_IDs ] -= (self.Q_sinks * self.dt)
 
        #---------------------------------------            
        # Update Q and vol due to point canals
        #---------------------------------------    
        ## if (hasattr(self, 'canal_in_IDs')):
        if (self.n_canals > 0):   
            #-----------------------------------------------------------------
            # Q grid was just modified.  Apply the canal diversion fractions
            # to compute the volume flow rate into upstream ends of canals.
            #-----------------------------------------------------------------
            Q_canals_in = self.Q_canals_fraction * self.Q[ self.canal_in_IDs ]
            self.Q_canals_in = Q_canals_in

            #----------------------------------------------------        
            # Update Q and vol due to losses at canal entrances
            #----------------------------------------------------
            self.Q[ self.canal_in_IDs ]   -= Q_canals_in
            self.vol[ self.canal_in_IDs ] -= (Q_canals_in * self.dt)        

            #-------------------------------------------------       
            # Update Q and vol due to gains at canal exits.
            # Diversions component accounts for travel time.
            #-------------------------------------------------        
            self.Q[ self.canal_out_IDs ]   += self.Q_canals_out
            self.vol[ self.canal_out_IDs ] += (self.Q_canals_out * self.dt)    
        
    #   update_diversions()
    #-------------------------------------------------------------------
    def update_flow_volume(self):

        #---------------------------------------------------------
        # Notes: Update the TOTAL volume (channel, flood, etc.).
        #        This function must be called after
        #        update_discharge() and update_diversions().
        #---------------------------------------------------------        
        # Notes: Q   = surface discharge  [m^3/s]
        #        R   = excess precip. rate  [m/s]
        #        da  = pixel area  [m^2]
        #        dt  = channel flow timestep  [s]
        #        vol = total volume of water in pixel [m^3]
        #        v2  = temp version of vol
        #        w1  = IDs of pixels that...
        #        p1  = IDs of parent pixels that...
        #---------------------------------------------------------
        dt = self.dt  # [seconds]

        #----------------------------------------------------
        # Add contribution (or loss ?) from excess rainrate
        #----------------------------------------------------
        # Contributions over entire grid cell from rainfall,
        # snowmelt, icemelt and baseflow (minus losses from
        # evaporation and infiltration) are assumed to flow
        # into the channel within the grid cell.
        # Note that R is allowed to be negative.
        #----------------------------------------------------        
        # self.vol += (self.R * self.da) * dt   # (in place)

        #----------------------------------------------------------
        # (2020-11-08) This new approach is an effort to add
        # realism and prevent flashiness in the hydrograph.
        # Rain water must flow across cell to reach channel.
        # u_overland is taken to be constant.
        # t_drain is time for all water in cell to reach channel.
        #---------------------------------------------------------- 
#         self.vol_stored += (self.R * self.da) * dt  # (in place)
#         dy = self.rti.yres * (92.6/3)   # (m = arcsec * (m/arcsec))
#         t_drain   = dy / (2 * self.u_overland)
#         Q_sides   = self.vol_stored / t_drain
#         ## Q_sides   = np.sqrt( self.vol_stored) / 2000.0
#         vol_sides = Q_sides * dt
#         self.vol += vol_sides
#         self.vol_stored -= vol_sides
#         np.maximum( self.vol_stored, 0.0, self.vol_stored )  # (in place)

        #----------------------------------------------------------
        # (2020-11-09) This new approach is an effort to add
        # realism and prevent flashiness in the hydrograph.
        # Rain water must flow across cell to reach channel.
        #---------------------------------------------------------- 
#         self.vol_stored += (self.R * self.da) * dt  # (in place)
#         Q_sides = 3.0  # (m3/s)
#         vol_sides = np.minimum( Q_sides * dt, self.vol_stored)
#         self.vol += vol_sides
#         self.vol_stored -= vol_sides
#         np.maximum( self.vol_stored, 0.0, self.vol_stored )  # (in place)

        #----------------------------------------------------------
        # (2020-03-08) This new approach is an effort to add
        # realism and prevent flashiness in the hydrograph.
        # Rain water must flow across cell to reach channel.
        # It is derived from the water tank model, using the
        # outlet velocity formula, v_out(t)=sqrt[2 g h(t)]
        # and eliminating h(t) in favor of V(t), the volume.
        # Also A_out is taken to be c * sqrt(A_top), where c
        # is either 1 or sqrt(2).
        # Q_sides(t) = c * sqrt[2 g V(t)]
        #----------------------------------------------------------
#         self.vol_stored += (self.R * self.da) * dt  # (in place)
#         c = 1.0
#         depth_cell = (self.vol_stored / self.da)
#         ## depth_cell = 0.001   # (THIS REDUCES FLASHINESS A BIT)
#         ## depth_cell = 0.0001   # (THIS REDUCES FLASHINESS MORE)
#         c2 = c * depth_cell
#         g = self.g  # [m/s2]
#         Q_sides = c2 * np.sqrt(2 * g * self.vol_stored)  # [m3/s]
#         vol_sides = np.minimum( Q_sides * dt, self.vol_stored)
#         #----------------
#         # For debugging
#         #----------------
#         # print('Cell = (row,col) = (1:3,1)')
#         # print('Q_sides      =', Q_sides[1:3,1])
#         # print('Q_sides * dt =', Q_sides[1:3,1] * dt )
#         # print('vol_stored   =', self.vol_stored[1:3,1])
#         # print('vol_sides    =', vol_sides[1:3,1])
#         # print('=======================================================')
#         
#         self.vol += vol_sides
#         self.vol_stored -= vol_sides
#         np.maximum( self.vol_stored, 0.0, self.vol_stored )  # (in place)
#         tank_depth = (self.vol_stored / self.da)
#         if (tank_depth.max() > 1.0):
#             print('### WARNING:  Tank depth exceeds 1 meter.')
#             print()

        #----------------------------------------------------------
        # (2021-05-10) This new approach is an effort to add
        # realism and prevent flashiness in the hydrograph.
        # Rain water must flow across cell to reach channel.
        # Assume that all water will reach channel in n days.
        # Q_sides is always a fraction of vol_stored.
        # Increase n_days to close the time lag and smooth.
        #----------------------------------------------------------
        # (2022-04-08) This appears to be equivalent to using the
        # Nash model (linear reservoir) for each grid cell.
        # In that model, K is a first order storage coefficient
        # with units of time that relates storage to discharge
        # via Q(t) = S(t) / K.  Here, Q=Q_sides, S=vol_stored,
        # and K = t_drain.
        #----------------------------------------------------------
        # An improvement would be to express K (or t_drain) in
        # terms of K_sat (e.g. from ISRIC SoilGrids data).
        # Maybe:  t_drain = L / K_sat, where L is the horizontal
        # travel distance in the subsurface before emerging.
        # Perhaps take L to be proportional to grid cell size, dx.
        # If L = 2 * dx, then flow should be added to D8 parent.
        # If t_drain = 3600 * 24 * 50 =  4,320,000 and
        # L = 1852 meters (60 arcsec * 92.5 m / 3 arcsec), then
        # "K_sat" = L / t_drain = 1852 / 4320000 = 0.000429 m/s
        # For sandy loam: K_sat ~ 5 cm/hr
        # (5 cm/hr) x (1 m / 100 cm) x (1 hr / 3600 sec) = 0.000014
        #-------------------------------------------------------------
        # See "fraction" option in update_R() function.  #######
        # This currently routes all "R" through a linear reservoir.
        #-------------------------------------------------------------                
        if (self.ATTENUATE):
            self.vol_stored += (self.R * self.da) * dt  # (in place)
            ## n_days  = 20.0  # Getting closer to observed
            n_days  = 50.0
            t_drain = 3600.0 * 24.0 * n_days  # (seconds)
            Q_sides = (self.vol_stored / t_drain)   # (m3/s)
            vol_sides = np.minimum( Q_sides * dt, self.vol_stored)
            self.vol += vol_sides
            self.vol_stored -= vol_sides
            np.maximum( self.vol_stored, 0.0, self.vol_stored )  # (in place)
        else:
            self.vol += (self.R * self.da) * dt  # (in place)

        #-----------------------------------------
        # Add contributions from neighbor pixels
        #-------------------------------------------------------------
        # Each grid cell passes flow to *one* downstream neighbor.
        # Note that multiple grid cells can flow toward a given grid
        # cell, so a grid cell ID may occur in d8.p1 and d8.p2, etc.
        #-------------------------------------------------------------      
#         if (self.d8.p1_OK):    
#             self.vol[ self.d8.p1 ] += (dt * self.Qc[self.d8.w1])
#         if (self.d8.p2_OK):    
#             self.vol[ self.d8.p2 ] += (dt * self.Qc[self.d8.w2])
#         if (self.d8.p3_OK):    
#             self.vol[ self.d8.p3 ] += (dt * self.Qc[self.d8.w3])
#         if (self.d8.p4_OK):    
#             self.vol[ self.d8.p4 ] += (dt * self.Qc[self.d8.w4])
#         if (self.d8.p5_OK):    
#             self.vol[ self.d8.p5 ] += (dt * self.Qc[self.d8.w5])
#         if (self.d8.p6_OK):    
#             self.vol[ self.d8.p6 ] += (dt * self.Qc[self.d8.w6])
#         if (self.d8.p7_OK):    
#             self.vol[ self.d8.p7 ] += (dt * self.Qc[self.d8.w7])
#         if (self.d8.p8_OK):    
#             self.vol[ self.d8.p8 ] += (dt * self.Qc[self.d8.w8])
        #-------------------------------------------------------------
        # Note:  We should be updating the TOTAL volume before we
        # partition it to channel and overbank flow.
        # And this assumes Q is TOTAL discharge.
        #-------------------------------------------------------------      
        if (self.d8.p1_OK):    
            self.vol[ self.d8.p1 ] += (dt * self.Q[self.d8.w1])
        if (self.d8.p2_OK):    
            self.vol[ self.d8.p2 ] += (dt * self.Q[self.d8.w2])
        if (self.d8.p3_OK):    
            self.vol[ self.d8.p3 ] += (dt * self.Q[self.d8.w3])
        if (self.d8.p4_OK):    
            self.vol[ self.d8.p4 ] += (dt * self.Q[self.d8.w4])
        if (self.d8.p5_OK):    
            self.vol[ self.d8.p5 ] += (dt * self.Q[self.d8.w5])
        if (self.d8.p6_OK):    
            self.vol[ self.d8.p6 ] += (dt * self.Q[self.d8.w6])
        if (self.d8.p7_OK):    
            self.vol[ self.d8.p7 ] += (dt * self.Q[self.d8.w7])
        if (self.d8.p8_OK):    
            self.vol[ self.d8.p8 ] += (dt * self.Q[self.d8.w8])

        #----------------------------------------------------
        # Subtract the amount that flows out to D8 neighbor
        #----------------------------------------------------
        # self.vol -= (self.Qc * dt)  # (in place)
        #----------------------------------------------------
        self.vol -= (self.Q * dt)  # (in place)
           
        #--------------------------------------------------------
        # While R can be positive or negative, the surface flow
        # volume must always be nonnegative. This also ensures
        # that the flow depth is nonnegative.  (7/13/06)
        #--------------------------------------------------------
        ## self.vol = np.maximum(self.vol, 0.0)
        ## self.vol[:] = np.maximum(self.vol, 0.0)  # (2/19/13)
        np.maximum( self.vol, 0.0, self.vol )  # (in place)
        
    #   update_flow_volume()
    #-------------------------------------------------------------------
    def update_channel_volume(self):

        #------------------------------------------------
        # Note:  Only call this if (self.FLOOD_OPTION )
        #------------------------------------------------
        np.minimum( self.vol, self.vol_bankfull, self.vol_chan)

    #   update_channel_volume()
    #-------------------------------------------------------------------
    def update_flood_volume(self):

        #---------------------------------------------------------
        # Channel volume at bankfull, called vol_bankfull, is
        # computed in initialize().  If total water volume,
        # self.vol exceeds this threshold, overbank flow occurs
        # into the floodplain, and this excess volume is used to
        # compute the flood depth, d_flood.  This partitioning
        # of water volume between channel and floodplain is
        # assumed to occur within one time step.  This could be
        # a source of numerical instability.   
        #----------------------------------------------------------
        # NOTE: Actual water depth in the middle of the channel
        # during flooding is channel depth + flood depth, when
        # using "rectangle over trapezoid" approach.
        #---------------------------------------------------------- 
        dvol = (self.vol - self.vol_bankfull)
        np.maximum( dvol, 0.0, self.vol_flood)  # (in place)

        #----------------------------------------------------------
        # If self.vol is not total volume but only channel volume,
        # then we would need to use the next line.  Otherwise,
        # the channel takes an amount up to vol_bankfull that is
        # used to compute channel water depth.
        #----------------------------------------------------------       
        # np.minimum(self.vol, self.vol_bankfull, self.vol )  # (in place)
 
    #   update_flood_volume()
    #-------------------------------------------------------------------
    def update_flood_volume_OPTION1(self):

        dt = self.dt  # [seconds]

        #---------------------------------------------------------
        # Excess water volume from overbank flow acts as a source
        # of water in the cell, that adds to whatever volume of
        # water is already there.  Channel volume at bankfull,
        # called vol_bankfull, is computed in initialize().       
        # D8 child cells with a higher free-surface may add to
        # the amount in a cell, and this total is reduced by
        # whatever amount flows to the D8 parent cell.
        #----------------------------------------------------------
        dvol = (self.vol - self.vol_bankfull)
        self.vol_flood += np.maximum(dvol, 0.0)
        # Next command does something different.
        ## np.maximum( dvol, 0.0, self.vol_flood)  # (in place)

        #--------------------------------------------------------------
        # Wherever vol > vol_bankfull, the channel volume computed
        # by update_flow_volume() is wrong and should instead be
        # the bankfull volume. Extra water volume is put into d_flood.
        #--------------------------------------------------------------
        np.minimum(self.vol, self.vol_bankfull, self.vol )  # (in place)
        
        #-----------------------------------------
        # Add contributions from neighbor pixels
        #-------------------------------------------------------------
        # Each grid cell passes flow to *one* downstream neighbor.
        # Note that multiple grid cells can flow toward a given grid
        # cell, so a grid cell ID may occur in d8.p1 and d8.p2, etc.
        #-------------------------------------------------------------       
        if (self.d8f.p1_OK):    
            self.vol_flood[ self.d8f.p1 ] += (dt * self.Qf[self.d8f.w1])
        if (self.d8f.p2_OK):    
            self.vol_flood[ self.d8f.p2 ] += (dt * self.Qf[self.d8f.w2])
        if (self.d8f.p3_OK):    
            self.vol_flood[ self.d8f.p3 ] += (dt * self.Qf[self.d8f.w3])
        if (self.d8f.p4_OK):    
            self.vol_flood[ self.d8f.p4 ] += (dt * self.Qf[self.d8f.w4])
        if (self.d8f.p5_OK):    
            self.vol_flood[ self.d8f.p5 ] += (dt * self.Qf[self.d8f.w5])
        if (self.d8f.p6_OK):    
            self.vol_flood[ self.d8f.p6 ] += (dt * self.Qf[self.d8f.w6])
        if (self.d8f.p7_OK):    
            self.vol_flood[ self.d8f.p7 ] += (dt * self.Qf[self.d8f.w7])
        if (self.d8f.p8_OK):    
            self.vol_flood[ self.d8f.p8 ] += (dt * self.Qf[self.d8f.w8])

        #----------------------------------------------------
        # Subtract the amount that flows out to D8 neighbor
        #----------------------------------------------------
        self.vol_flood -= (self.Qf * dt)  # (in place)
   
        #--------------------------------------------------------
        # While R can be positive or negative, the surface flow
        # volume must always be nonnegative. This also ensures
        # that the flow depth is nonnegative.  (7/13/06)
        #--------------------------------------------------------
        np.maximum( self.vol_flood, 0.0, self.vol_flood )   # (in place)
 
    #   update_flood_volume_OPTION1()
    #-------------------------------------------------------------------
    def update_channel_depth(self):

        #------------------------------------------------------------
        # Notes: 2019-09/16.  This function replaces the one above
        #        now called "update_channel_depth_OLD().
        #        This version supports overbank flow and flooding.
        #------------------------------------------------------------        
        # Notes: 7/18/05.  Modified to use the equation for volume
        #        of a trapezoidal channel:  vol = Ac * ds, where
        #        Ac=d*[w + d*tan(t)], and to solve the resulting
        #        quadratic (discarding neg. root) for new depth, d.

        #        8/29/05.  Now original ds is used for subsurface
        #        flow and there is a ds_chan which can include a
        #        sinuosity greater than 1.  This may be especially
        #        important for larger pixel sizes.

        #        Removed (ds > 1) here which was only meant to
        #        avoid a "divide by zero" error at pixels where
        #        (ds eq 0).  This isn't necessary since the
        #        Flow_Lengths function in utils_TF.pro never
        #        returns a value of zero.
        #----------------------------------------------------------
        #        Modified to avoid double where calls, which
        #        reduced cProfile run time for this method from
        #        1.391 to 0.644.  (9/23/14)
        #----------------------------------------------------------
        # Commented this out on (2/18/10) because it doesn't
        #           seem to be used anywhere now.  Checked all
        #           of the Channels components.
        #----------------------------------------------------------        
        # self.d_last = self.d.copy()

        #-----------------------------------        
        # Make some local aliases and vars
        #-----------------------------------------------------------
        # Note: angles were read as degrees & converted to radians
        #-----------------------------------------------------------
        vol    = self.vol_chan
        d      = self.d
        width  = self.width  ###
        angle  = self.angle
        SCALAR_ANGLES = (np.size(angle) == 1)

        #-----------------------------------------------        
        # Now compute the water depth in the channels.
        #-----------------------------------------------
        # Is "angle" a scalar or a grid ?
        #----------------------------------
        if (SCALAR_ANGLES):
            if (angle == 0.0):    
                d = vol / (width * self.d8.ds)
            else:
                denom = 2.0 * np.tan(angle)
                arg   = 2.0 * denom * vol / self.d8.ds
                arg  += width**(2.0)
                d     = (np.sqrt(arg) - width) / denom
                
                # For debugging
#                 print('angle       = ' + str(angle) )
#                 print('denom.min() = ' + str(denom.min()) ) 
#                 print('denom.max() = ' + str(denom.max()) ) 
#                 print('ds.min()    = ' + str(self.d8.ds.min()) ) 
#                 print('ds.max()    = ' + str(self.d8.ds.max()) )                
#                 print('arg.min()   = ' + str(arg.min()) )
#                 print('arg.max()   = ' + str(arg.max()) )
#                 d     = (np.sqrt(arg) - width) / denom
        else:
            #-----------------------------------------------------
            # Pixels where angle is 0 must be handled separately
            #-----------------------------------------------------
            w1 = ( angle == 0 )  # (arrays of True or False)
            w2 = np.invert( w1 )
            #-----------------------------------
            A_top = width[w1] * self.d8.ds[w1]    
            d[w1] = vol[w1] / A_top
            #-----------------------------------               
            denom  = 2.0 * np.tan(angle[w2])
            arg    = 2.0 * denom * vol[w2] / self.d8.ds[w2]
            arg   += width[w2]**(2.0)
            d[w2] = (np.sqrt(arg) - width[w2]) / denom

        #------------------------------------------------------------
        # Wherever vol > vol_bankfull, the flow depth just computed
        # is wrong and should instead be the bankfull depth.
        # Extra water volume has already been put into d_flood.
        #------------------------------------------------------------
        #### d[ wb1 ] = self.d_bankfull[ wb1 ]

        #------------------------------------------
        # See new "update_edge_values()" method.
        #------------------------------------------
        # Set depth values on edges to zero since
        # they become spikes (no outflow) 7/15/06
        #------------------------------------------------
        # NB!  This destroys mass, and will affect the
        #      mass balance calculations.
        #------------------------------------------------       
        # NB!  Since flooding now uses the free-surface
        # gradient (DEM + d_flood), we should not set it
        # to zero at interior noflow_IDs.
        #-------------------------------------------------
        ## d[ self.d8.noflow_IDs ] = 0.0  # (was needed for Baro)

        #------------------------------------------------
        # 4/19/06.  Force flow depth to be nonnegative ?
        #           A flow depth of zero is okay.
        #------------------------------------------------
        # This seems to be needed with the non-Richards
        # infiltration routines when starting with zero
        # depth everywhere, since all water infiltrates
        # for some period of time.  It also seems to be
        # needed more for short rainfall records to
        # avoid a negative flow depth error.
        #------------------------------------------------
        # 7/13/06.  Still needed for Richards method
        #------------------------------------------------ 
        # Uncomment next blocks for testing
        #------------------------------------------------             
#         dmin = self.d.min()
#         dmax = self.d.max()
#         print('dmin, dmax =', dmin, ', ', dmax)
        #------------------------------------------------ 
#         dmin = self.d.min()
#         if (dmin < 0):
#             print('WARNING:  In update_channel_depth(),' )
#             print('          Negative depths found.')
#             sys.exit()
        #------------------------------------------------
        np.maximum(d, 0.0, self.d)  # (2/19/13, in place)

        #-----------------------------------------------
        # Any negative depths were set to zero above.
        # But zero depths cause divide-by-zero errors,
        # so save those locations for later use.        
        #     self.froude is set to 0 where d = 0.
        #     self.f (friction factor) is also.
        #-----------------------------------------------
        self.d_is_pos  = (self.d > 0)
        self.d_is_zero = np.invert( self.d_is_pos )

    #   update_channel_depth()
    #-------------------------------------------------------------------
    def update_flood_depth(self):

        #---------------------------------------------------------
        # Notes: This version assumes a flat floodplain whose
        #        width is a multiple of the channel bottom width.
        #        There is a rectangle of this width above the
        #        channel trapezoid. (2022-05-05)
        #---------------------------------------------------------
        #        Assume flow direction during flooding is same
        #        as in-bank flow.
        #---------------------------------------------------------
        
        #-------------------------------------------------------       
        #  Compute the "flood depth" as follows:
        #
        #  Let vol_f = excess water volume (over bankfull)
        #  Let Af = floodplain cross-section area
        #  Let df = d_flood = water depth in flat flood plain
        #  Let wf = floodplain width
        #  Let ds = length of channel in grid cell
        #
        #  vol_f = Af * ds
        #  wf = n * width    (width = channel bottom width)
        #  Af = df * wf
        #  df = Af / wf = (vol_f/ds) / (n * width)
        #  df = vol_f / (n * width * ds)
        #-------------------------------------------------------
        #  n is typically in (3, 10) based on one source.
        #  Floodplain width must not exceed grid cell size.
        #-------------------------------------------------------
        n = self.width_ratio  # (default is 5.0)
        denom = (n * self.width * self.d8.ds)
        d_flood = self.vol_flood / denom

        #-------------------------------------------
        # Force flood depth to be nonnegative ?
        # A flow depth of zero is normal and okay.
        #-------------------------------------------
        np.maximum(d_flood, 0.0, self.d_flood)  # (in place)

        # For testing
#         df_max = d_flood.max()
#         if (df_max > 15):
#             print('### WARNING: d_flood.max() > 15.')

        #-----------------------------------------------
        # Any negative depths were set to zero above.
        # But zero depths cause divide-by-zero errors,
        # so save those locations for later use.        
        #     self.froude is set to 0 where d = 0.
        #     self.f (friction factor) is also.
        #-----------------------------------------------
#         self.d_is_pos  = (self.d > 0)
#         self.d_is_zero = np.invert( self.d_is_pos )

    #   update_flood_depth()
    #-------------------------------------------------------------------
    def update_flood_depth_OPTION1(self):

        #-----------------------------------------------------------
        # Notes: This is the original approach to
        #        update_flood_depth() where overbank flow is
        #        spread evenly over grid cells and can have its
        #        own D8 flow direction.
        #-----------------------------------------------------------
        # Wherever vol > vol_bankfull, the flow depth computed by
        # update_channel_depth() is wrong and should instead be the
        # bankfull depth.  Extra water volume is put into d_flood.
        #-----------------------------------------------------------
        # Note:  This shouldn't be necessary now.
        #-----------------------------------------------------------
        # np.minimum(self.d, self.d_bankfull, self.d )  # (in place)

        #----------------------------------------------------------
        # (2019-09-16)  Compute the overbank/flooding depth.       
        # Channel volume at bankfull is computed in initialize().
        #----------------------------------------------------------
        # Remember that "width" is the trapezoid bottom width.
        # In addition, w_bankfull is not used here, but:
        #    w_bankfull = width + (2 * d_bankfull * tan(angle))
        #    width = w_bankfull - (2 * d_bankfull * tan(angle))
        # If we know any 3 of these 4 vars, we can compute the
        # 4th one. So assume d_bankfull, angle & width are known.
        # HOWEVER, values of w_bankfull found by remote sensing
        # may be more accurate than values of d_bankfull.
        #----------------------------------------------------------
        # Depending on grid cell size, it may be unrealistic to
        # assume flood plain spans the entire grid cell.
        #----------------------------------------------------------        
        SCALAR_DA = (np.size(self.d8.da) == 1) 
        d_flood   = self.d_flood
        vol_flood = self.vol_flood

        w1 = (vol_flood > 0)   # (boolean array)
        w2 = np.invert( w1 )
        if (SCALAR_DA):
            d_flood[ w1 ] = vol_flood[ w1 ] / self.d8.da
        else:
            d_flood[ w1 ] = vol_flood[ w1 ] / self.d8.da[ w1 ]
        d_flood[ w2 ] = 0.0
        self.d_flood[:] = d_flood   # write in place 
        
        #-------------------------------------------
        # See: update_edge_values() for noflow_IDs
        #-------------------------------------------    

    #   update_flood_depth_OPTION1()
    #-------------------------------------------------------------------
    def update_flood_depth_OPTION2(self):

        #---------------------------------------------------------
        # Notes: 2022-05-05.  This is an alternate approach to
        #        update_flood_depth().
        #        This version is based on a "double trapezoid",
        #        where the top width of the channel trapezoid
        #        is the bottom width of the floodplain trapezoid.
        #        The floodplain "tilts" toward the channel with
        #        a slope of tan(alpha) where alpha should be
        #        fairly small but cannot be zero (a scalar).
        #        But this allows floodplain to become very wide.
        #---------------------------------------------------------
        #        Assume flow direction during flooding is same
        #        as in-bank flow.
        #---------------------------------------------------------
                                
        #-----------------------------------        
        # Make some local aliases and vars
        #-----------------------------------------------------------
        # Note: angles were read as degrees & converted to radians
        #-----------------------------------------------------------
        angle = self.angle
        L1    = self.d_bankfull * np.tan(angle)
        w_top = self.width + (2 * L1)  # top width channel trapezoid
        
        #----------------------------------------------------------       
        #  Now compute the "flood depth" as follows:
        #
        #  Let vol_f = excess water volume.
        #  Let Af = floodplain trapezoid area (cross-section)
        #  Let df = d_flood = max water height above channel bank
        #  Let ds = length of channel in grid cell
        #  Let alpha  = floodplain tilt angle > 0
        #  tan(alpha) = floodplain slope toward channel = df/L1
        #
        #  vol_f  = Af * ds
        #  L1 = df / tan(alpha)
        #  Af = df * (w_top + L1)
        #     = df * (w_top + df/tan(alpha))
        #  vol_f / ds = df * w_top + (df^2)/tan(alpha)
        #  a*(df^2) + b*df + c = 0
        #  a = 1/tan(alpha), b=w_top, c = -vol_f/ds
        #  Solve this quadratic for df.
        #----------------------------------------------------------
        #  Relate floodplain width to top channel width.
        #  floodplain width must not exceed grid cell size.
        #----------------------------------------------------------
        #  Let wf = floodplain width
        #  wf = w_top + 2*L1 = w_top + 2*df/tan(alpha)
        #  Let wf = n * w_top.
        #  n = 1 + 2*df/[ tan(alpha) * w_top ]
        #  Solve for alpha.
        #  [tan(alpha) * w_top ] = (2 * df) / (n-1)
        #  tan(alpha) = (2 * df) / [w_top * (n-1)]
        #  So if df = 2 and n=5:
        #  tan(alpha) = 4 / [w_top * 4] = 1 / w_top
        #----------------------------------------------------------
        alpha = 0.1    # arctan(0.001) = 0.001
        arg  = w_top**(2.0)
        arg += 4 * vol_f / (self.d8.ds * tan(alpha))
        denom = 2 / tan(alpha)
        d_flood = (np.sqrt(arg) - w_top) / denom

        #-------------------------------------------
        # Force flood depth to be nonnegative ?
        # A flow depth of zero is normal and okay.
        #-------------------------------------------
        np.maximum(d_flood, 0.0, self.d_flood)  # (in place)

        #-----------------------------------------------
        # Any negative depths were set to zero above.
        # But zero depths cause divide-by-zero errors,
        # so save those locations for later use.        
        #     self.froude is set to 0 where d = 0.
        #     self.f (friction factor) is also.
        #-----------------------------------------------
#         self.d_is_pos  = (self.d > 0)
#         self.d_is_zero = np.invert( self.d_is_pos )

    #   update_flood_depth_OPTION2()
    #-------------------------------------------------------------------
    def update_free_surface_slope(self):

        #-----------------------------------------------------------
        # Notes:  It is assumed that the flow directions don't
        #         change even though the free surface is changing.
        #-----------------------------------------------------------
        # NB!  This only applies when the same D8 flow code is
        #      used for the channel and the floodplain.
        #      See "z_free" above for "OPTION1".
        #-----------------------------------------------------------
        if (self.FLOOD_OPTION):
            #----------------------------------------------------
            # Added this for "rectangle over trapezoid" option.
            # Without this, d_flood can have "spikes".
            # Need a flag to set the "floodplain option".
            #----------------------------------------------------
            total_d = (self.d + self.d_flood)
            delta_d = total_d - total_d[ self.d8.parent_IDs ]
            self.S_free[:] = self.S_bed + (delta_d / self.d8.ds)
            #----------------------------------------------------
            ## if (OPTION1) then do something else...
            #----------------------------------------------------
        else:
            delta_d = (self.d - self.d[self.d8.parent_IDs])
            self.S_free[:] = self.S_bed + (delta_d / self.d8.ds)
        
        #--------------------------------------------
        # Don't do this; negative slopes are needed
        # to decelerate flow in dynamic wave case
        # and for backwater effects.
        #--------------------------------------------
        # Set negative slopes to zero
        #------------------------------
        ###  self.S_free = np.maximum(self.S_free, 0)

    #   update_free_surface_slope()
    #-------------------------------------------------------------------
    def update_shear_stress(self):

        #--------------------------------------------------------
        # Notes: 9/9/14.  Added so shear stress could be shared.
        #        This uses the depth-slope product.
        #--------------------------------------------------------
        if (self.KINEMATIC_WAVE):
            slope = self.S_bed
        else:
            slope = np.abs( self.S_free )
        self.tau[:] = self.rho_H2O * self.g * self.d * slope
               
    #   update_shear_stress()
    #-------------------------------------------------------------------
    def update_shear_speed(self):

        #--------------------------------------------------------
        # Notes: 9/9/14.  Added so shear speed could be shared.
        #--------------------------------------------------------
        self.u_star[:] = np.sqrt( self.tau / self.rho_H2O )
               
    #   update_shear_speed()
    #-------------------------------------------------------------------
    def update_trapezoid_Rh(self):

        #-------------------------------------------------------------
        # Notes: Compute the hydraulic radius of a trapezoid that:
        #          (1) has a bed width of wb >= 0 (0 for triangular)
        #          (2) has a bank angle of theta (0 for rectangular)
        #          (3) is filled with water to a depth of d.
        #        The units of wb and d are meters.  The units of
        #        theta are assumed to be degrees and are converted.
        #-------------------------------------------------------------
        # NB!    wb should never be zero, so P_wet can never be 0,
        #        which would produce a NaN (divide by zero).
        #-------------------------------------------------------------
        #        See Notes for TF_Tan function in utils_TF.pro
        #            AW = d * (wb + (d * TF_Tan(theta_rad)) )
        #-------------------------------------------------------------
        # 9/9/14.  Bug fix.  Angles were already in radians but
        #          were converted to radians again.
        #--------------------------------------------------------------

        #---------------------------------------------------------
        # Compute hydraulic radius grid for trapezoidal channels
        #-----------------------------------------------------------
        # Note: angles were read as degrees & converted to radians
        #-----------------------------------------------------------
        d     = self.d        # (local synonyms)
        wb    = self.width    # (trapezoid bottom width)
        L2    = d * np.tan( self.angle )          
        A_wet = d * (wb + L2)      
        P_wet = wb + (np.float64(2) * d / np.cos(self.angle) )

        #---------------------------------------------------
        # At noflow_IDs (e.g. edges) P_wet may be zero
        # so do this to avoid "divide by zero". (10/29/11)
        #---------------------------------------------------
        P_wet[ self.d8.noflow_IDs ] = np.float64(1)
        Rh = (A_wet / P_wet)
        #--------------------------------
        # w = np.where(P_wet == 0)
        # print 'In update_trapezoid_Rh():'
        # print '   P_wet= 0 at', w[0].size, 'cells'

        #---------------------------------------------------
        # Override Rh for overland flow, where d_flood > 0
        # (2019-09-18)
        #---------------------------------------------------
#         w1 = (self.d_flood > 0)  # (array of True or False)
#         Rh[ w1 ] = self.d_flood[ w1 ]   #########################################

        #------------------------------------
        # Force edge pixels to have Rh = 0.
        # This will make u = 0 there also.
        #------------------------------------
        Rh[ self.d8.noflow_IDs ] = np.float64(0)        
##        w  = np.where(wb <= 0)
##        nw = np.size(w[0])
##        if (nw > 0): Rh[w] = np.float64(0)
        
        self.Rh[:]    = Rh
        self.A_wet[:] = A_wet   ## (Now shared: 9/9/14)
        self.P_wet[:] = P_wet   ## (Now shared: 9/9/14)

        #---------------
        # For testing
        #--------------
##        print 'dmin, dmax =', d.min(),  d.max()
##        print 'wmin, wmax =', wb.min(), wb.max()
##        print 'amin, amax =', self.angle.min(), self.angle.max()

    #   update_trapezoid_Rh()
    #-------------------------------------------------------------------
    def update_friction_factor(self):    

        #----------------------------------------    
        # Note:  Added on 9/9/14 to streamline.
        #----------------------------------------------------------
        # Note:  f  = half of the Fanning friction factor
        #        d  = flow depth [m]
        #        z0 = roughness length
        #        S  = bed slope (assumed equal to friction slope)
        #        g  = 9.81 = gravitation constant [m/s^2]
        #---------------------------------------------------------       
        #        For law of the wall:
        #        kappa = 0.41 = von Karman's constant
        #        aval  = 0.48 = integration constant

        #        law_const  = sqrt(g)/kappa = 7.6393d
        #        smoothness = (aval / z0) * d
        #        f = (kappa / alog(smoothness))^2d
        #        tau_bed = rho_w * f * u^2 = rho_w * g * d * S

        #        d, S, and z0 can be arrays.

        #        To make default z0 correspond to default
        #        Manning's n, can use this approximation:
        #        z0 = a * (2.34 * sqrt(9.81) * n / kappa)^6d
        #        For n=0.03, this gives: z0 = 0.011417
        #########################################################
        #        However, for n=0.3, it gives: z0 = 11417.413
        #        which is 11.4 km!  So the approximation only
        #        holds within some range of values.
        #--------------------------------------------------------

        ###############################################################
        # cProfile:  This method took: 0.369 secs for topoflow_test()
        ###############################################################            
        #--------------------------------------
        # Find where (d <= 0).  g=good, b=bad
        #-------------------------------------- 
        wg = self.d_is_pos
        wb = self.d_is_zero
#         wg = ( self.d > 0 )
#         wb = np.invert( wg )
        
        #-----------------------------
        # Compute f for Manning case
        #-----------------------------------------
        # This makes f=0 and du=0 where (d <= 0)
        #-----------------------------------------
        if (self.MANNING):
            #---------------------------------------------
            # (2020-11-05)  Allow nval to be Scalar.
            #---------------------------------------------
            if (self.nval.size > 1):
                n2 = self.nval[wg] ** np.float64(2)
            else:
                n2 = self.nval ** np.float64(2)
            #---------------------------------------------
            ### n2 = self.nval ** np.float64(2)
            ### self.f[ wg ] = self.g * (n2[wg] / (self.d[wg] ** self.one_third))
            #---------------------------------------------
            self.f[ wg ] = self.g * (n2 / (self.d[wg] ** self.one_third))            
            self.f[ wb ] = np.float64(0)
 
        #---------------------------------
        # Compute f for Law of Wall case
        #---------------------------------
        if (self.LAW_OF_WALL):
            #------------------------------------------------
            # Make sure (smoothness > 1) before taking log.
            # Should issue a warning if this is used.
            #------------------------------------------------
            smoothness = (self.aval / self.z0val) * self.d
            np.maximum(smoothness, np.float64(1.1), smoothness)  # (in place)
            self.f[wg] = (self.kappa / np.log(smoothness[wg])) ** np.float64(2)
            self.f[wb] = np.float64(0)

        ##############################################################
        # cProfile:  This method took: 0.93 secs for topoflow_test()
        ##############################################################        
#         #--------------------------------------
#         # Find where (d <= 0).  g=good, b=bad
#         #-------------------------------------- 
#         wg = np.where( self.d > 0 )
#         ng = np.size( wg[0])
#         wb = np.where( self.d <= 0 )
#         nb = np.size( wb[0] )
# 
#         #-----------------------------
#         # Compute f for Manning case
#         #-----------------------------------------
#           # This makes f=0 and du=0 where (d <= 0)
#           #-----------------------------------------
#         if (self.MANNING):
#             n2 = self.nval ** np.float64(2)  
#             if (ng != 0):
#                 self.f[wg] = self.g * (n2[wg] / (self.d[wg] ** self.one_third))
#             if (nb != 0):
#                 self.f[wb] = np.float64(0)
# 
#         #---------------------------------
#         # Compute f for Law of Wall case
#         #---------------------------------
#         if (self.LAW_OF_WALL):
#             #------------------------------------------------
#             # Make sure (smoothness > 1) before taking log.
#             # Should issue a warning if this is used.
#             #------------------------------------------------
#             smoothness = (self.aval / self.z0val) * self.d
#             np.maximum(smoothness, np.float64(1.1), smoothness)  # (in place)
#             ## smoothness = np.maximum(smoothness, np.float64(1.1))
#             if (ng != 0):
#                 self.f[wg] = (self.kappa / np.log(smoothness[wg])) ** np.float64(2)
#             if (nb != 0):
#                 self.f[wb] = np.float64(0)                       

        #---------------------------------------------
        # We could share the Fanning friction factor
        #---------------------------------------------
        ### self.fanning = (np.float64(2) * self.f)

    #   update_friction_factor()       
    #-------------------------------------------------------------------
    def update_velocity(self):

        #---------------------------------------------------------
        # Note: Do nothing now unless this method is overridden
        #       by a particular method of computing velocity
        #       in a channel component that inherits from
        #       channels_base.py.
        #---------------------------------------------------------
        print("Warning: update_velocity() method is inactive.")
        
        # print 'KINEMATIC WAVE =', self.KINEMATIC_WAVE
        # print 'DIFFUSIVE WAVE =', self.DIFFUSIVE_WAVE
        # print 'DYNAMIC WAVE   =', self.DYNAMIC_WAVE

    #   update_velocity()
    #-------------------------------------------------------------------
    def update_velocity_on_edges(self):

        #---------------------------------
        # Force edge pixels to have u=0.
        #----------------------------------------
        # Large slope around 1 flows into small
        # slope & leads to a negative velocity.
        #------------------------------------------------------
        # Whenever flow direction is undefined (i.e. noflow),
        # the velocity should be zero.  Not just on edges.
        #------------------------------------------------------
        self.u[ self.d8.noflow_IDs ] = np.float64(0)
        ### self.u[ self.d8.edge_IDs ] = np.float64(0)
        
    #   update_velocity_on_edges()
    #-------------------------------------------------------------------
    def update_froude_number(self):

        #----------------------------------------------------------
        # Notes: 9/9/14.  Added so Froude number could be shared.
        # This use of wg & wb reduced cProfile time from:
        # 0.644 sec to: 0.121.  (9/23/14)
        #----------------------------------------------------------
        # g = good, b = bad
        #-------------------- 
        wg = self.d_is_pos
        wb = self.d_is_zero

        self.froude[ wg ] = self.u[wg] / np.sqrt( self.g * self.d[wg] )       
        self.froude[ wb ] = np.float64(0)
               
    #   update_froude_number()
    #-------------------------------------------------------------
    def update_outlet_values(self):
        
        #-------------------------------------------------
        # Save computed values at outlet, which are used
        # by the TopoFlow driver.
        #-----------------------------------------------------
        # Note that Q_outlet, etc. are defined as 0D numpy
        # arrays to make them "mutable scalars" (i.e.
        # this allows changes to be seen by other components
        # who have a reference.  To preserve the reference,
        # however, we must use fill() to assign a new value.
        #-----------------------------------------------------
        Q_outlet = self.Q[ self.outlet_ID ]
        u_outlet = self.u[ self.outlet_ID ]
        d_outlet = self.d[ self.outlet_ID ]
        f_outlet = self.f[ self.outlet_ID ]
    
        self.Q_outlet.fill( Q_outlet )
        self.u_outlet.fill( u_outlet )
        self.d_outlet.fill( d_outlet )
        self.f_outlet.fill( f_outlet )
        
    #   update_outlet_values()
    #-------------------------------------------------------------
    def update_peak_values(self):

        #-------------------------------------------
        # Using "fill" saves new values "in-place"
        # and preserves "mutable scalars".
        #-------------------------------------------
        if (self.Q_outlet > self.Q_peak):    
            self.Q_peak.fill( self.Q_outlet )
            self.T_peak.fill( self.time_min )      # (time to peak)
        #---------------------------------------
        if (self.u_outlet > self.u_peak):
            self.u_peak.fill( self.u_outlet )
            self.Tu_peak.fill( self.time_min )
        #---------------------------------------
        if (self.d_outlet > self.d_peak):    
            self.d_peak.fill(  self.d_outlet )
            self.Td_peak.fill( self.time_min )

    #   update_peak_values()
    #-------------------------------------------------------------
    def update_Q_out_integral(self):

        #--------------------------------------------------------
        # Note: Renamed "volume_out" to "vol_Q" for consistency
        # with vol_P, vol_SM, vol_IN, vol_ET, etc. (5/18/12)
        #--------------------------------------------------------
        self.vol_Q += (self.Q_outlet * self.dt)  ## 5/19/12.

    #   update_Q_out_integral()
    #-------------------------------------------------------------
    def update_edge_values(self):

        #-------------------------------------------------------
        # Note: D8 noflow_IDs identify grid cells with a D8
        #       flow code of zero (undefined flow direction).
        #       There is no flow *from* noflow_IDs.
        #-------------------------------------------------------
        # Zero out water depths & volumes at noflow_IDs.
        # Otherwise, it builds up to create a spike.
        #-------------------------------------------------------
        # Note: Rh, u, d, d_flood already zeroed at noflow_IDs.
        #-------------------------------------------------------
        # update_flow_volume() updated the net volume for
        # every grid cell, including the noflow_IDs.
        # But the noflow_IDs have no outflow, only inflow.
        # Save volume added after time step, then zero out.
        #-------------------------------------------------------
        # Now, since adding "rectangle over trapezoid" floodplain
        # method, self.vol is TOTAL volume (channel + floodplain).
        # So don't add vol_flood to vol_edge or will get
        # double counting and incorrect mass balance report.
        #-------------------------------------------------------        
        vol = self.vol   # (from R, and flow in and out)
        noflow_IDs     = self.d8.noflow_IDs
        vol_edge       = vol[ noflow_IDs ].sum()
        self.vol_edge += vol_edge
        #----------------------------------------------  
        self.vol[ noflow_IDs ] = 0.0   ## (important)
        self.d[ noflow_IDs ]   = 0.0
        
        if (self.FLOOD_OPTION):
            #---------------------------------------------
            # Only needed next block for OPTION1 method.
            # Can cause double counting. See note above.
            # Notice use of self.d8f for flood vars
            #---------------------------------------------
            # vol_flood      = self.vol_flood
            # noflow_IDs2    = self.d8f.noflow_IDs
            # vol_edge2      = vol_flood[ noflow_IDs2 ].sum()
            # self.vol_edge += vol_edge2
            # self.vol_flood[ noflow_IDs2 ] = 0.0
            # self.d_flood[ noflow_IDs2 ]   = 0.0
            #--------------------------------------------
            self.vol_flood[ noflow_IDs ] = 0.0
            self.d_flood[ noflow_IDs ]   = 0.0

    #   update_edge_values()
    #-------------------------------------------------------------
    def update_mins_and_maxes(self, REPORT=False):

        #-------------------------------------------------------
        # Note:  Only call this at the end, not from update().
        #-------------------------------------------------------
        
        #--------------------------------------
        # Get mins and max over entire domain
        #--------------------------------------
##        Q_min = self.Q.min()
##        Q_max = self.Q.max()
##        #---------------------
##        u_min = self.u.min()
##        u_max = self.u.max()        
##        #---------------------
##        d_min = self.d.min()
##        d_max = self.d.max()
        
        #--------------------------------------------
        # Exclude values on the edges.
        # Have d8.edge_IDs, but not interior IDs.
        #--------------------------------------------
        nx_lim = (self.nx - 1)
        ny_lim = (self.ny - 1)
        Q_min = self.Q[1:ny_lim,1:nx_lim].min()
        Q_max = self.Q[1:ny_lim,1:nx_lim].max()
        #-------------------------------------------------
        u_min = self.u[1:ny_lim,1:nx_lim].min()
        u_max = self.u[1:ny_lim,1:nx_lim].max()       
        #-------------------------------------------------
        d_min = self.d[1:ny_lim,1:nx_lim].min()
        d_max = self.d[1:ny_lim,1:nx_lim].max()

        #-------------------------------------------------
        # (2/6/13) This preserves "mutable scalars" that
        # can be accessed as refs by other components.
        #-------------------------------------------------
        if (Q_min < self.Q_min):
            self.Q_min.fill( Q_min )
        if (Q_max > self.Q_max):
            self.Q_max.fill( Q_max )
        #------------------------------
        if (u_min < self.u_min):
            self.u_min.fill( u_min )
        if (u_max > self.u_max):
            self.u_max.fill( u_max )
        #------------------------------
        if (d_min < self.d_min):
            self.d_min.fill( d_min )
        if (d_max > self.d_max):
            self.d_max.fill( d_max )
        
        #-------------------------------------------------
        # (2/6/13) This preserves "mutable scalars" that
        # can be accessed as refs by other components.
        #-------------------------------------------------        
##        self.Q_min.fill( np.minimum( self.Q_min, Q_min ) )
##        self.Q_max.fill( np.maximum( self.Q_max, Q_max ) )
##        #---------------------------------------------------
##        self.u_min.fill( np.minimum( self.u_min, u_min ) )
##        self.u_max.fill( np.maximum( self.u_max, u_max ) )
##        #---------------------------------------------------
##        self.d_min.fill( np.minimum( self.d_min, d_min ) )
##        self.d_max.fill( np.maximum( self.d_max, d_max ) )

        #-------------------------------------------------
        # (2/6/13) This preserves "mutable scalars" that
        # can be accessed as refs by other components.
        #-------------------------------------------------        
##        self.Q_min.fill( min( self.Q_min, Q_min ) )
##        self.Q_max.fill( max( self.Q_max, Q_max ) )
##        #---------------------------------------------------
##        self.u_min.fill( min( self.u_min, u_min ) )
##        self.u_max.fill( max( self.u_max, u_max ) )
##        #---------------------------------------------------
##        self.d_min.fill( min( self.d_min, d_min ) )
##        self.d_max.fill( max( self.d_max, d_max ) )
        
        #----------------------------------------------
        # (2/6/13) This produces "immutable scalars".
        #----------------------------------------------
##        self.Q_min = self.Q.min()
##        self.Q_max = self.Q.max()
##        self.u_min = self.u.min()
##        self.u_max = self.u.max()
##        self.d_min = self.d.min()
##        self.d_max = self.d.max()

        if (REPORT):
            print('In channels_base.update_mins_and_maxes():')
            print('(dmin, dmax) =', self.d_min, self.d_max)
            print('(umin, umax) =', self.u_min, self.u_max)
            print('(Qmin, Qmax) =', self.Q_min, self.Q_max)
            print(' ')
            
    #   update_mins_and_maxes()
    #-------------------------------------------------------------
    def update_total_channel_water_volume(self, REPORT=False):

        #----------------------------------------------------   
        # Note:  Compute the total volume of water in all
        #        channels for the entire DEM.  Can use this
        #        in the final mass balance reporting.
        #        (2019-09-17)
        #----------------------------------------------------
        # Note:  This should be called from finalize().
        #----------------------------------------------------
        # Note:  If d0>0, then we have vol_chan_sum0 > 0.
        #----------------------------------------------------

        #---------------------------------------------        
        # This is also done in update_edge_values().
        # But this one only called in finalize().
        #---------------------------------------------
        # Water can build up at noflow_IDs, whether
        # on DEM edges or anywhere flow code is 0.
        #---------------------------------------------
        ## vol[ self.d8.noflow_IDs ] = 0.0
        #### vol[ self.d8.edge_IDs ] = 0.0
       
        vol_chan_sum = np.sum( self.vol_chan )
        self.vol_chan_sum.fill( vol_chan_sum )
   
    #   update_total_channel_water_volume()
    #-------------------------------------------------------------
    def update_total_flood_water_volume(self, REPORT=False):

        #----------------------------------------------------   
        # Note:  Compute the total volume of flood water in
        #        all grid cells for the entire DEM.  Use
        #        this in the final mass balance reporting.
        #        (2019-09-17)
        #----------------------------------------------------
        # Note:  This should be called from finalize().
        #----------------------------------------------------

        #--------------------------------------------
        # Water can build up at noflow_IDs, whether
        # on DEM edges or anywhere flow code is 0.
        #--------------------------------------------
        # But better to zero out as we go, so these
        # values aren't in the saved grids ??
        #--------------------------------------------
        # vol_flood[ self.d8.noflow_IDs ] = 0.0
        ## vol_flood[ self.d8.edge_IDs ] = 0.0 

        #--------------------------------------       
        # Compute total volume of flood water
        #--------------------------------------         
        vol_flood_sum = np.sum( self.vol_flood )   #######
        self.vol_flood_sum.fill( vol_flood_sum )
 
    #   update_total_flood_water_volume()
    #-------------------------------------------------------------------
    def check_flow_depth_LAST(self):

        OK = True
        d  = self.d
        dt = self.dt
        nx = self.nx   #################
        
        #---------------------------------
        # All all flow depths positive ?
        #---------------------------------  
        wbad = np.where( np.logical_or( d < 0.0, np.logical_not(np.isfinite(d)) ))
        nbad = np.size( wbad[0] )       
        if (nbad == 0):    
            return OK

        OK = False
        dmin = d[wbad].min()
        star_line = '*******************************************'
        
        msg = [ star_line, \
               'ERROR: Simulation aborted.', ' ', \
               'Negative or NaN depth found: ' + str(dmin), \
               'Time step may be too large.', \
               'Time step:      ' + str(dt) + ' [s]' ]

        for k in range(len(msg)):
            print(msg[k])
        
        #-------------------------------------------
        # If not too many, print actual velocities
        #-------------------------------------------
        if (nbad < 30):          
            brow = wbad[0][0]
            bcol = wbad[1][0]
##            badi = wbad[0]
##            bcol = (badi % nx)
##            brow = (badi / nx)
            crstr = str(bcol) + ', ' + str(brow)

            msg = [' ', '(Column, Row):  ' + crstr, \
                   'Flow depth:     ' + str(d[brow, bcol])]
            for k in range(len(msg)):
                print(msg[k])

        print(star_line) 
        print(' ')
        raise RuntimeError('Negative depth found.')  # (11/16/16)

        return OK

    #   check_flow_depth_LAST()
    #-------------------------------------------------------------------
    def check_flow_depth(self):

        OK = True
        d  = self.d
        dt = self.dt
        nx = self.nx   #################
        
        #---------------------------------
        # Are any flow depths negative ?
        #---------------------------------
        wneg = np.where( d < 0.0 )
        nneg = np.size( wneg[0] )
        #-----------------------------
        # Are any flow depths NaNs ?
        #-----------------------------
        wnan = np.where( np.isnan(d) )
        nnan = np.size( wnan[0] )
        #-----------------------------
        # Are any flow depths Infs ?
        #-----------------------------
        winf = np.where( np.isinf(d) )
        ninf = np.size( winf[0] )
        #----------------------------------
        # Option to allow NaN but not Inf
        #----------------------------------
        if (nneg == 0) and (ninf == 0):
            return OK
        OK = False
        #-------------------------------------------------- 
#         if (nneg == 0) and (nnan == 0) and (ninf == 0):
#             return OK
#         OK = False

        #----------------------------------
        # Print informative error message
        #----------------------------------
        star_line = '*******************************************'
        print( star_line )           
        print('ERROR: Simulation aborted.')
        print(' ')
        #--------------------------------------------------------        
        if (nneg > 0):
            dmin = d[ wneg ].min()
            str1 = 'Found ' + str(nneg) + ' negative depths.'
            str2 = '  Smallest negative depth = ' + str(dmin)
            print( str1 )
            print( str2 )
        #--------------------------------------------------------
        if (nnan > 0):
            str3 = 'Found ' + str(nnan) + ' NaN depths.'
            print( str3 )
        #--------------------------------------------------------
        if (ninf > 0):
            str4 = 'Found ' + str(ninf) + ' infinite depths.'
            print( str4 )
        #------------------------------------
        # Option to allow NaNs on the edges
        #------------------------------------
        print( 'Time step may be too large for stability.' )
        print( 'Time step:      ' + str(dt) + ' [s]' )
        print( 'Try reducing timestep in channels CFG file.' )
        print( star_line )
        print( ' ' )
            
        #-------------------------------------------
        # If not too many, print actual depths
        #-------------------------------------------
#         if (nbad < 30):          
#             brow = wbad[0][0]
#             bcol = wbad[1][0]
# ##            badi = wbad[0]
# ##            bcol = (badi % nx)
# ##            brow = (badi / nx)
#             crstr = str(bcol) + ', ' + str(brow)
# 
#             msg = [' ', '(Column, Row):  ' + crstr, \
#                    'Flow depth:     ' + str(d[brow, bcol])]
#             for k in range(len(msg)):
#                 print(msg[k])
#         print(star_line) 
#         print(' ')

        raise RuntimeError('Negative or NaN depth found.')  # (11/16/16)

        return OK

    #   check_flow_depth()
    #-------------------------------------------------------------------
    def check_flow_velocity_LAST(self):

        OK = True
        u  = self.u
        dt = self.dt
        nx = self.nx
        
        #--------------------------------
        # Are all velocities positive ?
        #--------------------------------
        wbad = np.where( np.logical_or( u < 0.0, np.logical_not(np.isfinite(u)) ))
        nbad = np.size( wbad[0] )
        if (nbad == 0):    
            return OK

        OK = False
        umin = u[wbad].min()
        star_line = '*******************************************'
        msg = [ star_line, \
               'ERROR: Simulation aborted.', ' ', \
               'Negative or NaN velocity found: ' + str(umin), \
               'Time step may be too large.', \
               'Time step:      ' + str(dt) + ' [s]']
        for k in range(len(msg)):
            print(msg[k])

        #-------------------------------------------
        # If not too many, print actual velocities
        #-------------------------------------------
        if (nbad < 30):
            brow = wbad[0][0]
            bcol = wbad[1][0]
##            badi = wbad[0]
##            bcol = (badi % nx)
##            brow = (badi / nx)
            crstr = str(bcol) + ', ' + str(brow)

            msg = [' ', '(Column, Row):  ' + crstr, \
                   'Velocity:       ' + str(u[brow, bcol])]
            for k in range(len(msg)):
                print(msg[k])

        print(star_line)
        print(' ')
        raise RuntimeError('Negative or NaN velocity found.')  # (11/16/16)

        return OK

            
##        umin = u[wbad].min()
##        badi = wbad[0]
##        bcol = (badi % nx)
##        brow = (badi / nx)
##        crstr = str(bcol) + ', ' + str(brow)
##        msg = np.array([' ', \
##                     '*******************************************', \
##                     'ERROR: Simulation aborted.', ' ', \
##                     'Negative velocity found: ' + str(umin), \
##                     'Time step may be too large.', ' ', \
##                     '(Column, Row):  ' + crstr, \
##                     'Velocity:       ' + str(u[badi]), \
##                     'Time step:      ' + str(dt) + ' [s]', \
##                     '*******************************************', ' '])
##        for k in xrange( np.size(msg) ):
##            print msg[k]

##        return OK                          


    #   check_flow_velocity_LAST()
    #-------------------------------------------------------------------
    def check_flow_velocity(self, CNEG=True, CNAN=True, CINF=True):

        OK = True
        u  = self.u
        dt = self.dt
        nx = self.nx
        nneg = 0
        nnan = 0
        ninf = 0

        #---------------------------------
        # Are any flow depths negative ?
        #---------------------------------
        if (CNEG):
            wneg = (u < 0.0)
            nneg = wneg.sum()
            # wneg = np.where( u < 0.0 )
            # nneg = np.size( wneg[0] )
        #-----------------------------
        # Are any flow depths NaNs ?
        #-----------------------------
        if (CNAN):
            wnan = np.isnan(u)
            nnan = wnan.sum()
            # wnan = np.where( np.isnan(u) )
            # nnan = np.size( wnan[0] )
        #-----------------------------
        # Are any flow depths Infs ?
        #-----------------------------
        if (CINF):
            winf = np.isinf(u)
            ninf = winf.sum()
            # winf = np.where( np.isinf(u) )
            # ninf = np.size( winf[0] )

        if (nneg == 0) and (nnan == 0) and (ninf == 0):
            return OK
        OK = False

        #----------------------------------
        # Option to allow NaN but not Inf
        #----------------------------------
#         if (nneg == 0) and (ninf == 0):
#             return OK
#         OK = False 

        #----------------------------------
        # Print informative error message
        #----------------------------------
        star_line = '*******************************************'
        print( star_line )           
        print('ERROR: Simulation aborted.')
        print(' ')
        #--------------------------------------------------------        
        if (CNEG and (nneg > 0)):
            umin = u[ wneg ].min()
            str1 = 'Found ' + str(nneg) + ' negative velocities.'
            str2 = '  Smallest negative velocity = ' + str(umin)
            print( str1 )
            print( str2 )
        #--------------------------------------------------------
        if (CNAN and (nnan > 0)):
            str3 = 'Found ' + str(nnan) + ' NaN velocities.'
            print( str3 )
        #--------------------------------------------------------
        if (CINF and (ninf > 0)):
            str4 = 'Found ' + str(ninf) + ' infinite velocities.'
            print( str4 )
        #------------------------------------
        # Option to allow NaNs on the edges
        #------------------------------------
        print( 'Time step may be too large for stability.' )
        print( 'Time step:      ' + str(dt) + ' [s]' )
        print( 'Try reducing timestep in channels CFG file.' )
        print( star_line )
        print( ' ' )
        
        raise RuntimeError('Found bad velocities.')  # (11/16/16)

        return OK


##        umin = u[wbad].min()
##        badi = wbad[0]
##        bcol = (badi % nx)
##        brow = (badi / nx)
##        crstr = str(bcol) + ', ' + str(brow)
##        msg = np.array([' ', \
##                     '*******************************************', \
##                     'ERROR: Simulation aborted.', ' ', \
##                     'Negative velocity found: ' + str(umin), \
##                     'Time step may be too large.', ' ', \
##                     '(Column, Row):  ' + crstr, \
##                     'Velocity:       ' + str(u[badi]), \
##                     'Time step:      ' + str(dt) + ' [s]', \
##                     '*******************************************', ' '])
##        for k in xrange( np.size(msg) ):
##            print msg[k]

##        return OK                          


    #   check_flow_velocity()
    #-------------------------------------------------------------------  
    def open_input_files(self):

        #------------------------------------------------------
        # This method uses prepend_directory() in BMI_base.py
        # which uses both eval and exec.
        #------------------------------------------------------
#         in_files = ['slope_file', 'nval_file', 'z0val_file',
#                     'width_file', 'angle_file', 'sinu_file',
#                     'd0_file', 'd_bankfull_file' ]
#         self.prepend_directory( in_files, INPUT=True )

        #------------------------------------------------------
        # This avoids eval/exec, but is brute-force
        # 2020-05-03. Changed in_directory to topo_directory.
        # See set_directories() in BMI_base.py.
        #------------------------------------------------------
        self.slope_file = (self.topo_directory + self.slope_file)
        self.nval_file  = (self.topo_directory + self.nval_file)
        self.z0val_file = (self.topo_directory + self.z0val_file)        
        self.width_file = (self.topo_directory + self.width_file)
        self.angle_file = (self.topo_directory + self.angle_file)
        self.sinu_file  = (self.topo_directory + self.sinu_file) 
        self.d0_file    = (self.topo_directory + self.d0_file)
        self.d_bankfull_file = (self.topo_directory + self.d_bankfull_file) 

        #----------------------------------------------        
        # Open all input files and store file objects
        #----------------------------------------------                
        #self.code_unit = model_input.open_file(self.code_type,  self.code_file)
        self.slope_unit = model_input.open_file(self.slope_type, self.slope_file)
        if (self.MANNING):
            self.nval_unit  = model_input.open_file(self.nval_type,  self.nval_file)
        if (self.LAW_OF_WALL):
            self.z0val_unit = model_input.open_file(self.z0val_type, self.z0val_file)
        self.width_unit = model_input.open_file(self.width_type, self.width_file)
        self.angle_unit = model_input.open_file(self.angle_type, self.angle_file)
        self.sinu_unit  = model_input.open_file(self.sinu_type,  self.sinu_file)
        self.d0_unit    = model_input.open_file(self.d0_type,    self.d0_file)
        self.d_bankfull_unit = model_input.open_file(self.d_bankfull_type, self.d_bankfull_file)

    #   open_input_files()
    #-------------------------------------------------------------------  
    def read_input_files(self):

        #-------------------------------------------------------    
        # Note:  All grids are assumed to have same dimensions
        #        as the DEM.
        #-------------------------------------------------------
        rti = self.rti
 
        #-------------------------------------------------------
        # All grids are assumed to have a data type of float32
        # as stored in their binary grid file.
        #-------------------------------------------------------
        # If EOF is reached, model_input.read_next() does not
        # change the value of the scalar or grid.
        #-------------------------------------------------------
        # Note:  Added 3rd "factor" argument to update_var on
        #        2022-02-15.  See set_missing_cfg_options().
        #-------------------------------------------------------
        slope = model_input.read_next(self.slope_unit, self.slope_type, rti)
        if (slope is not None):
            self.update_var( 'slope', slope, self.slope_factor )
        
        if (self.MANNING):
            nval = model_input.read_next(self.nval_unit, self.nval_type, rti)
            if (nval is not None):
                self.update_var( 'nval', nval, self.nval_factor )

        if (self.LAW_OF_WALL):
            z0val = model_input.read_next(self.z0val_unit, self.z0val_type, rti)
            if (z0val is not None):
                self.update_var( 'z0val', z0val, self.z0val_factor )
 
        width = model_input.read_next(self.width_unit, self.width_type, rti)
        if (width is not None):
            #----------------------------------------------------
            # See "initialize_computed_vars()" for adjustments.
            #----------------------------------------------------
            self.update_var( 'width', width, self.width_factor )

        angle = model_input.read_next(self.angle_unit, self.angle_type, rti)
        if (angle is not None):
            #----------------------------------------------------
            # See "initialize_computed_vars()" for adjustments,
            # i.e. convert bank angles from degrees to radians.           
            #----------------------------------------------------
            self.update_var( 'angle', angle, self.angle_factor )
                
        sinu = model_input.read_next(self.sinu_unit, self.sinu_type, rti)
        if (sinu is not None):
            self.update_var( 'sinu', sinu, self.sinu_factor )
                        
        d0 = model_input.read_next(self.d0_unit, self.d0_type, rti)
        if (d0 is not None):
            self.update_var( 'd0', d0, self.d0_factor )

        # (2019-09-16) #
        d_bankfull = model_input.read_next(self.d_bankfull_unit, self.d_bankfull_type, rti)
        if (d_bankfull is not None):
            self.update_var( 'd_bankfull', d_bankfull, self.d_bankfull_factor )

    #   read_input_files()        
    #-------------------------------------------------------------------  
#     def read_input_files_last(self):
# 
#         #----------------------------------------------------
#         # The D8 flow codes are always a grid, size of DEM.
#         #----------------------------------------------------
#         # NB! model_input.py also has a read_grid() function.
#         #----------------------------------------------------        
#         rti = self.rti
# ##        print 'Reading D8 flow grid (in CHANNELS)...'
# ##        self.code = rtg_files.read_grid(self.code_file, rti,
# ##                                        RTG_type='BYTE')
# ##        print ' '
#         
#         #-------------------------------------------------------
#         # All grids are assumed to have a data type of float32.
#         #-------------------------------------------------------
#         slope = model_input.read_next(self.slope_unit, self.slope_type, rti)
#         if (slope is not None):
#             self.slope = slope
#             ## print '    min(slope) =', slope.min()
#             ## print '    max(slope) =', slope.max()
#         
#         # If EOF was reached, hopefully numpy's "fromfile"
#         # returns None, so that the stored value will be
#         # the last value that was read.
# 
#         if (self.MANNING):
#             nval = model_input.read_next(self.nval_unit, self.nval_type, rti)
#             if (nval is not None):
# #                 if (self.nval_type.lower() == 'scalar'):
# #                     self.update_scalar( 'nval', nval )
# #                 else:
# #                     self.nval = nval
#                 self.nval     = nval
#                 self.nval_min = nval.min()
#                 self.nval_max = nval.max()
#                 print '    min(nval) =', self.nval_min
#                 print '    max(nval) =', self.nval_max
# 
#         if (self.LAW_OF_WALL):
#             z0val = model_input.read_next(self.z0val_unit, self.z0val_type, rti)
#             if (z0val is not None):
#                 self.z0val     = z0val
#                 self.z0val_min = z0val.min()
#                 self.z0val_max = z0val.max()
#                 print '    min(z0val) =', self.z0val_min
#                 print '    max(z0val) =', self.z0val_max
#         
#         width = model_input.read_next(self.width_unit, self.width_type, rti)
#         if (width is not None):
#             #-------------------------------------------------------
#             # Width can be zero on 4 edges, but this can result in
#             # a "divide by zero" error later on, so need to adjust.
#             #-------------------------------------------------------
#             w1 = ( width == 0 )  # (arrays of True or False)
#             width[w1] = self.d8.dw[w1]
#             self.width = width
#             print '    min(width) =', width.min()
#             print '    max(width) =', width.max()
# 
#         angle = model_input.read_next(self.angle_unit, self.angle_type, rti)
#         if (angle is not None):
#             print '    min(angle) =', angle.min(), ' [deg]'
#             print '    max(angle) =', angle.max(), ' [deg]'
#             #-----------------------------------------------
#             # Convert bank angles from degrees to radians. 
#             #-----------------------------------------------
#             self.angle = angle * self.deg_to_rad  # [radians]
#             ### self.angle = angle  # (before 9/9/14)
# 
#         sinu = model_input.read_next(self.sinu_unit, self.sinu_type, rti)
#         if (sinu is not None):
#             self.sinu = sinu
#             print '    min(sinuosity) =', sinu.min()
#             print '    max(sinuosity) =', sinu.max()
#         
#         d0 = model_input.read_next(self.d0_unit, self.d0_type, rti)
#         if (d0 is not None):
#             self.d0 = d0
#             print '    min(d0) =', d0.min()
#             print '    max(d0) =', d0.max()
# 
#         ## code = model_input.read_grid(self.code_unit, \
#         ##                            self.code_type, rti, dtype='uint8')
#         ## if (code is not None): self.code = code
# 
#     #   read_input_files_last()     
    #-------------------------------------------------------------------  
    def close_input_files(self):

        if (self.comp_status.lower() == 'disabled'):
            return  # (2021-07-27)

        #-------------------------------------------------
        # NB!  self.code_unit was never defined as read.
        #-------------------------------------------------
        # if (self.code_type.lower() != 'scalar'): self.code_unit.close()

        if (self.slope_type.lower() != 'scalar'): self.slope_unit.close()
        if (self.MANNING):
            if (self.nval_type.lower() != 'scalar'): self.nval_unit.close()
        if (self.LAW_OF_WALL):
           if (self.z0val_type.lower() != 'scalar'): self.z0val_unit.close()
        if (self.width_type.lower() != 'scalar'): self.width_unit.close()
        if (self.angle_type.lower() != 'scalar'): self.angle_unit.close()
        if (self.sinu_type.lower()  != 'scalar'): self.sinu_unit.close()
        if (self.d0_type.lower()    != 'scalar'): self.d0_unit.close()
        if (self.d_bankfull_type.lower() != 'scalar'): self.d_bankfull_unit.close()

    #   close_input_files()       
    #-------------------------------------------------------------------  
    def update_outfile_names(self):

        #-------------------------------------------------
        # Notes:  Append out_directory to outfile names.
        #-------------------------------------------------
        self.Q_gs_file  = (self.out_directory + self.Q_gs_file)
        self.u_gs_file  = (self.out_directory + self.u_gs_file)
        self.d_gs_file  = (self.out_directory + self.d_gs_file) 
        self.f_gs_file  = (self.out_directory + self.f_gs_file)
        self.d_flood_gs_file = (self.out_directory + self.d_flood_gs_file) 
        #--------------------------------------------------------
        self.Q_ts_file  = (self.out_directory + self.Q_ts_file)
        self.u_ts_file  = (self.out_directory + self.u_ts_file) 
        self.d_ts_file  = (self.out_directory + self.d_ts_file) 
        self.f_ts_file  = (self.out_directory + self.f_ts_file) 
        self.d_flood_ts_file = (self.out_directory + self.d_flood_ts_file) 
        
    #   update_outfile_names()
    #-------------------------------------------------------------------  
#     def bundle_output_files(self):    
# 
#         ###################################################
#         # NOT READY YET. Need "get_long_name()" and a new
#         # version of "get_var_units".  (9/21/14)
#         ###################################################
#                 
#         #-------------------------------------------------------------       
#         # Bundle the output file info into an array for convenience.
#         # Then we just need one open_output_files(), in BMI_base.py,
#         # and one close_output_files().  Less to maintain. (9/21/14)
#         #-------------------------------------------------------------        
#         # gs = grid stack, ts = time series, ps = profile series.
#         #-------------------------------------------------------------
#         self.out_files = [
#         {var_name:'Q', 
#         save_gs:self.SAVE_Q_GRIDS,  gs_file:self.Q_gs_file,
#         save_ts:self.SAVE_Q_PIXELS, ts_file:self.Q_ts_file, 
#         long_name:get_long_name('Q'), units_name:get_var_units('Q')}, 
#         #-----------------------------------------------------------------
#         {var_name:'u',
#         save_gs:self.SAVE_U_GRIDS,  gs_file:self.u_gs_file,
#         save_ts:self.SAVE_U_PIXELS, ts_file:self.u_ts_file,
#         long_name:get_long_name('u'), units_name:get_var_units('u')},
#         #-----------------------------------------------------------------
#         {var_name:'d',
#         save_gs:self.SAVE_D_GRIDS,  gs_file:self.d_gs_file,
#         save_ts:self.SAVE_D_PIXELS, ts_file:self.d_ts_file,
#         long_name:get_long_name('d'), units_name:get_var_units('d')}, 
#         #-----------------------------------------------------------------
#         {var_name:'f',
#         save_gs:self.SAVE_F_GRIDS,  gs_file:self.f_gs_file,
#         save_ts:self.SAVE_F_PIXELS, ts_file:self.f_ts_file,
#         long_name:get_long_name('f'), units_name:get_var_units('f')},
#         #-----------------------------------------------------------------
#         {var_name:'d_flood',
#         save_gs:self.SAVE_DF_GRIDS,  gs_file:self.d_flood_gs_file,
#         save_ts:self.SAVE_DF_PIXELS, ts_file:self.d_flood_ts_file,
#         long_name:get_long_name('d_flood'), units_name:get_var_units('d_flood')} ]
#                                 
#     #   bundle_output_files
    #------------------------------------------------------------------- 
    def disable_all_output(self):
    
        self.SAVE_Q_GRIDS  = False
        self.SAVE_U_GRIDS  = False
        self.SAVE_D_GRIDS  = False
        self.SAVE_F_GRIDS  = False
        self.SAVE_DF_GRIDS = False
        #----------------------------
        self.SAVE_Q_PIXELS  = False
        self.SAVE_U_PIXELS  = False
        self.SAVE_D_PIXELS  = False
        self.SAVE_F_PIXELS  = False
        self.SAVE_DF_PIXELS = False
        
    #   disable_all_output()
    #-------------------------------------------------------------------  
    def open_output_files(self):

        model_output.check_netcdf( SILENT=self.SILENT )
        self.update_outfile_names()
        ## self.bundle_output_files()
        

##        print 'self.SAVE_Q_GRIDS =', self.SAVE_Q_GRIDS
##        print 'self.SAVE_U_GRIDS =', self.SAVE_U_GRIDS
##        print 'self.SAVE_D_GRIDS =', self.SAVE_D_GRIDS
##        print 'self.SAVE_F_GRIDS =', self.SAVE_F_GRIDS
##        #---------------------------------------------------
##        print 'self.SAVE_Q_PIXELS =', self.SAVE_Q_PIXELS
##        print 'self.SAVE_U_PIXELS =', self.SAVE_U_PIXELS
##        print 'self.SAVE_D_PIXELS =', self.SAVE_D_PIXELS
##        print 'self.SAVE_F_PIXELS =', self.SAVE_F_PIXELS

#         IDs = self.outlet_IDs
#         for k in xrange( len(self.out_files) ):
#             #--------------------------------------
#             # Open new files to write grid stacks
#             #--------------------------------------
#             if (self.out_files[k].save_gs):
#                 model_output.open_new_gs_file( self, self.out_files[k], self.rti )
#             #--------------------------------------
#             # Open new files to write time series
#             #--------------------------------------
#             if (self.out_files[k].save_ts):
#                 model_output.open_new_ts_file( self, self.out_files[k], IDs )
                                                          
        #--------------------------------------
        # Open new files to write grid stacks
        #--------------------------------------
        if (self.SAVE_Q_GRIDS):   
            model_output.open_new_gs_file( self, self.Q_gs_file, self.rti,
                                           var_name='Q',
                                           long_name='volumetric_discharge',
                                           units_name='m^3/s')
            
        if (self.SAVE_U_GRIDS):    
            model_output.open_new_gs_file( self, self.u_gs_file, self.rti,
                                           var_name='u',
                                           long_name='mean_channel_flow_velocity',
                                           units_name='m/s')
        
        if (self.SAVE_D_GRIDS):    
            model_output.open_new_gs_file( self, self.d_gs_file, self.rti,
                                           var_name='d',
                                           long_name='max_channel_flow_depth',
                                           units_name='m')

        if (self.SAVE_F_GRIDS):    
            model_output.open_new_gs_file( self, self.f_gs_file, self.rti,
                                           var_name='f',
                                           long_name='friction_factor',
                                           units_name='none')
 
        if (self.SAVE_DF_GRIDS):    
            model_output.open_new_gs_file( self, self.d_flood_gs_file, self.rti,
                                           var_name='d_flood',
                                           long_name='land_surface_water__depth',
                                           units_name='m')
                                                                          
        #--------------------------------------
        # Open new files to write time series
        #--------------------------------------
        IDs = self.outlet_IDs
        ## print('##################### Outlet IDs =', IDs)
        if (self.SAVE_Q_PIXELS):  
            model_output.open_new_ts_file( self, self.Q_ts_file, IDs,
                                           var_name='Q',
                                           long_name='volumetric_discharge',
                                           units_name='m^3/s')
                                          
        if (self.SAVE_U_PIXELS):
            model_output.open_new_ts_file( self, self.u_ts_file, IDs,
                                           var_name='u',
                                           long_name='mean_channel_flow_velocity',
                                           units_name='m/s')
                                          
        if (self.SAVE_D_PIXELS):    
            model_output.open_new_ts_file( self, self.d_ts_file, IDs,
                                           var_name='d',
                                           long_name='max_channel_flow_depth',
                                           units_name='m')
            
        if (self.SAVE_F_PIXELS):    
            model_output.open_new_ts_file( self, self.f_ts_file, IDs,
                                           var_name='f',
                                           long_name='friction_factor',
                                           units_name='none')

        if (self.SAVE_DF_PIXELS):    
            model_output.open_new_ts_file( self, self.d_flood_ts_file, IDs,
                                           var_name='d_flood',
                                           long_name='land_surface_water__depth',
                                           units_name='m')
                                                   
    #   open_output_files()
    #-------------------------------------------------------------------  
    def write_output_files(self, time_seconds=None):

        #---------------------------------------------------------
        # Notes:  This function was written to use only model
        #         time (maybe from a caller) in seconds, and
        #         the save_grid_dt and save_pixels_dt parameters
        #         read by read_cfg_file().
        #
        #         read_cfg_file() makes sure that all of
        #         the "save_dts" are larger than or equal to the
        #         process dt.
        #---------------------------------------------------------
        #-----------------------------------------
        # Allows time to be passed from a caller
        #-----------------------------------------
        if (time_seconds is None):
            time_seconds = self.time_sec
        model_time = int(time_seconds)
        
        #----------------------------------------
        # Save computed values at sampled times
        #----------------------------------------
        if (model_time % int(self.save_grid_dt) == 0):
            ## print('###### SAVING CHANNEL GRIDS: model_time =', model_time )
            ## print()
            self.save_grids()
        if (model_time % int(self.save_pixels_dt) == 0):
            #-----------------------------------------------------
            # Note: If dt = 250 sec, and save_pixels_dt = 600,
            #       values will only be printed every 3000 secs.
            #-----------------------------------------------------
            # print('model_time =', model_time, '[sec]')
            # print('time_min   =', self.time_min, '[min]')
            # print('save_pixels_dt =', self.save_pixels_dt, '[sec]')
            self.save_pixel_values()

        #----------------------------------------
        # Save computed values at sampled times
        #----------------------------------------
##        if ((self.time_index % self.grid_save_step) == 0):
##             self.save_grids()
##        if ((self.time_index % self.pixel_save_step) == 0):
##             self.save_pixel_values()
        
    #   write_output_files()
    #-------------------------------------------------------------------  
    def close_output_files(self):

        if (self.SAVE_Q_GRIDS):  model_output.close_gs_file( self, 'Q')   
        if (self.SAVE_U_GRIDS):  model_output.close_gs_file( self, 'u')  
        if (self.SAVE_D_GRIDS):  model_output.close_gs_file( self, 'd')   
        if (self.SAVE_F_GRIDS):  model_output.close_gs_file( self, 'f')
        if (self.SAVE_DF_GRIDS): model_output.close_gs_file( self, 'd_flood')
        #---------------------------------------------------------------
        if (self.SAVE_Q_PIXELS):  model_output.close_ts_file( self, 'Q')   
        if (self.SAVE_U_PIXELS):  model_output.close_ts_file( self, 'u')    
        if (self.SAVE_D_PIXELS):  model_output.close_ts_file( self, 'd')    
        if (self.SAVE_F_PIXELS):  model_output.close_ts_file( self, 'f')
        if (self.SAVE_DF_PIXELS): model_output.close_ts_file( self, 'd_flood')
                
    #   close_output_files()              
    #-------------------------------------------------------------------  
    def save_grids(self):
        
        #-----------------------------------
        # Save grid stack to a netCDF file
        #---------------------------------------------
        # Note that add_grid() methods will convert
        # var from scalar to grid now, if necessary.
        #---------------------------------------------    
        if (self.SAVE_Q_GRIDS):
            model_output.add_grid( self, self.Q, 'Q', self.time_min )
            
        if (self.SAVE_U_GRIDS):
            model_output.add_grid( self, self.u, 'u', self.time_min )
            
        if (self.SAVE_D_GRIDS):
            model_output.add_grid( self, self.d, 'd', self.time_min )

        if (self.SAVE_F_GRIDS):
            model_output.add_grid( self, self.f, 'f', self.time_min )     

        if (self.SAVE_DF_GRIDS):
            model_output.add_grid( self, self.d_flood, 'd_flood', self.time_min )   
            
    #   save_grids()
    #-------------------------------------------------------------------  
    def save_pixel_values(self):   ##### save_time_series_data(self)  #######
        
        IDs  = self.outlet_IDs
        time = self.time_min       #####

        #-------------
        # New method
        #-------------
        if (self.SAVE_Q_PIXELS):
            model_output.add_values_at_IDs( self, time, self.Q, 'Q', IDs )
                                              
        if (self.SAVE_U_PIXELS):
            model_output.add_values_at_IDs( self, time, self.u, 'u', IDs )
            
        if (self.SAVE_D_PIXELS):
            model_output.add_values_at_IDs( self, time, self.d, 'd', IDs )
            
        if (self.SAVE_F_PIXELS):
            model_output.add_values_at_IDs( self, time, self.f, 'f', IDs )

        if (self.SAVE_DF_PIXELS):
            model_output.add_values_at_IDs( self, time, self.d_flood, 'd_flood', IDs )
                    
    #   save_pixel_values()
    #-------------------------------------------------------------------
    def manning_formula(self):

        #---------------------------------------------------------
        # Notes: R = (A/P) = hydraulic radius [m]
        #        N = Manning's roughness coefficient
        #            (usually in the range 0.012 to 0.035)
        #        S = bed slope or free slope

        #        R,S, and N may be 2D arrays.

        #        If length units are all *feet*, then an extra
        #        factor of 1.49 must be applied.  If units are
        #        meters, no such factor is needed.

        #        Note that Q = Ac * u, where Ac is cross-section
        #        area.  For a trapezoid, Ac does not equal w*d.
        #---------------------------------------------------------
        if (self.KINEMATIC_WAVE):
            S = self.S_bed
        else:
            S = self.S_free

        S2 = np.abs(S)   ###### (2022-05-06)
        u = (self.Rh ** self.two_thirds) * np.sqrt(S2) / self.nval

        #----------------------------------------------        
        # Allow negative velocities and backflow in
        # case of diffusive or dynamic wave?
        #----------------------------------------------
        # Remember that Q = u * Ac out of each cell
        # to its D8 parent.  So if u<0, a grid cell
        # is removing volume from its D8 parent cell.
        #----------------------------------------------
#         if not(self.KINEMATIC_WAVE):  # (2022-05-06)
#             w1 = (S < 0)
#             u[w1] *= -1

        #--------------------------------------------------------
        # Add a hydraulic jump option for when u gets too big ?
        # A velocity larger than about 4 m/s is unlikely.
        #--------------------------------------------------------
        return u
        
    #   manning_formula()
    #-------------------------------------------------------------------
    def law_of_the_wall(self):

        #---------------------------------------------------------
        # Notes: u  = flow velocity  [m/s]
        #        d  = flow depth [m]
        #        z0 = roughness length
        #        S  = bed slope or free slope

        #        g     = 9.81 = gravitation constant [m/s^2]
        #        kappa = 0.41 = von Karman's constant
        #        aval  = 0.48 = integration constant

        #        law_const  = sqrt(g)/kappa = 7.6393d
        #        smoothness = (aval / z0) * d
        #        f = (kappa / alog(smoothness))^2d
        #        tau_bed = rho_w * f * u^2 = rho_w * g * d * S

        #        d, S, and z0 can be arrays.

        #        To make default z0 correspond to default
        #        Manning's n, can use this approximation:
        #        z0 = a * (2.34 * sqrt(9.81) * n / kappa)^6d
        #        For n=0.03, this gives: z0 = 0.011417
        #########################################################
        #        However, for n=0.3, it gives: z0 = 11417.413
        #        which is 11.4 km!  So the approximation only
        #        holds within some range of values.
        #--------------------------------------------------------
        if (self.KINEMATIC_WAVE):
            S = self.S_bed
        else:
            S = self.S_free

        smoothness = (self.aval / self.z0val) * self.d
          
        #------------------------------------------------
        # Make sure (smoothness > 1) before taking log.
        # Should issue a warning if this is used.
        #------------------------------------------------
        smoothness = np.maximum(smoothness, np.float64(1.1))

        S2 = np.abs(S)    
        u = self.law_const * np.sqrt(self.Rh * S2) * np.log(smoothness)

        #--------------------------------------------        
        # Allow negative velocities and backflow in
        # case of diffusive or dynamic wave?
        #----------------------------------------------
        # Remember that Q = u * Ac out of each cell
        # to its D8 parent.  So if u<0, a grid cell
        # is removing volume from its D8 parent cell.
        #----------------------------------------------
#         if not(self.KINEMATIC_WAVE):  # (2022-05-06)
#             w1 = (S < 0)
#             u[w1] *= -1

        return u
    
    #   law_of_the_wall()
    #-------------------------------------------------------------------
    def print_status_report(self): 

        #----------------------------------------------------
        # Wherever depth is less than z0, assume that water
        # is not flowing and set u and Q to zero.
        # However, we also need (d gt 0) to avoid a divide
        # by zero problem, even when numerators are zero.
        #----------------------------------------------------
        # FLOWING = (d > (z0/aval))
        #*** FLOWING[noflow_IDs] = False    ;******
        
        wflow    = np.where( FLOWING != 0 )
        n_flow   = np.size( wflow[0] )
        n_pixels = self.rti.n_pixels
        percent  = np.float64(100.0) * (np.float64(n_flow) / n_pixels)
        fstr = ('%5.1f' % percent) + '%'
        # fstr = idl_func.string(percent, format='(F5.1)').strip() + '%'
        print(' Percentage of pixels with flow = ' + fstr)
        print(' ')

        self.update_mins_and_maxes(REPORT=True)
 
        wmax  = np.where(self.Q == self.Q_max)
        nwmax = np.size(wmax[0])
        print(' Max(Q) occurs at: ' + str( wmax[0] ))
        #print,' Max attained at ', nwmax, ' pixels.'
        print(' ')
        print('-------------------------------------------------')

    #   print_status_report() 
    #-------------------------------------------------------------------
#     def remove_bad_slopes0(self, FLOAT=False):
# 
#         #------------------------------------------------------------
#         # Notes: The main purpose of this routine is to find
#         #        pixels that have nonpositive slopes and replace
#         #        then with the smallest value that occurs anywhere
#         #        in the input slope grid.  For example, pixels on
#         #        the edges of the DEM will have a slope of zero.
# 
#         #        With the Kinematic Wave option, flow cannot leave
#         #        a pixel that has a slope of zero and the depth
#         #        increases in an unrealistic manner to create a
#         #        spike in the depth grid.
# 
#         #        It would be better, of course, if there were
#         #        no zero-slope pixels in the DEM.  We could use
#         #        an "Imposed gradient DEM" to get slopes or some
#         #        method of "profile smoothing".
# 
#         #        It is possible for the flow code to be nonzero
#         #        at a pixel that has NaN for its slope. For these
#         #        pixels, we also set the slope to our min value.
# 
#         #        7/18/05. Broke this out into separate procedure.
#         #------------------------------------------------------------
# 
#         #-----------------------------------
#         # Are there any "bad" pixels ?
#         # If not, return with no messages.
#         #-----------------------------------  
#         wb = np.where(np.logical_or((self.slope <= 0.0), \
#                               np.logical_not(np.isfinite(self.slope))))
#         nbad = np.size(wb[0])
#         print('size(slope) = ' + str(np.size(self.slope)) )
#         print('size(wb) = ' + str(nbad) )
#         
#         wg = np.where(np.invert(np.logical_or((self.slope <= 0.0), \
#                                      np.logical_not(np.isfinite(self.slope)))))
#         ngood = np.size(wg[0])
#         if (nbad == 0) or (ngood == 0):
#             return
#         
#         #---------------------------------------------
#         # Find smallest positive value in slope grid
#         # and replace the "bad" values with smin.
#         #---------------------------------------------
#         print('-------------------------------------------------')
#         print('WARNING: Zero or negative slopes found.')
#         print('         Replacing them with smallest slope.')
#         print('         Use "Profile smoothing tool" instead.')
#         S_min = self.slope[wg].min()
#         S_max = self.slope[wg].max()
#         print('         min(S) = ' + str(S_min))
#         print('         max(S) = ' + str(S_max))
#         print('-------------------------------------------------')
#         print(' ')
#         self.slope[wb] = S_min
#         
#         #--------------------------------
#         # Convert data type to double ?
#         #--------------------------------
#         if (FLOAT):    
#             self.slope = np.float32(self.slope)
#         else:    
#             self.slope = np.float64(self.slope)
#         
#     #   remove_bad_slopes0()
    #-------------------------------------------------------------------
    def remove_bad_slopes(self, FLOAT=False):

        #------------------------------------------------------------
        # Notes: The main purpose of this routine is to find
        #        pixels that have nonpositive slopes and replace
        #        then with the smallest value that occurs anywhere
        #        in the input slope grid.  For example, pixels on
        #        the edges of the DEM will have a slope of zero.

        #        With the Kinematic Wave option, flow cannot leave
        #        a pixel that has a slope of zero and the depth
        #        increases in an unrealistic manner to create a
        #        spike in the depth grid.

        #        It would be better, of course, if there were
        #        no zero-slope pixels in the DEM.  We could use
        #        an "Imposed gradient DEM" to get slopes or some
        #        method of "profile smoothing".

        #        It is possible for the flow code to be nonzero
        #        at a pixel that has NaN for its slope. For these
        #        pixels, we also set the slope to our min value.

        #        7/18/05. Broke this out into separate procedure.
        #------------------------------------------------------------

        #------------------------
        # Are any slopes Nans ?
        #------------------------
        wnan = np.where( np.isnan( self.slope ) )
        nnan = np.size( wnan[0] )
        #------------------------
        # Are any slopes zero ?
        #------------------------
        wzero = np.where( self.slope == 0.0 )
        nzero = np.size( wzero[0] )
        #-------------------------------
        # Are any slopes negative ?
        #-------------------------------
        wneg = np.where( self.slope < 0.0 )
        nneg = np.size( wneg[0] )
        #-------------------------------
        # Are any slopes infinite ?
        #-------------------------------
        winf = np.where( np.isinf( self.slope ) )
        ninf = np.size( winf[0] )
        #----------------------------
        nbad = (nnan + nneg + ninf + nzero)
        if (nbad == 0):
            return

        #---------------------------       
        # Merge "wheres" into wbad
        #---------------------------
        S_shape = self.slope.shape
        bad = np.zeros( S_shape, dtype='bool' )
        if (nnan > 0): bad[ wnan ] = True
        if (nzero >0): bad[ wzero] = True
        if (nneg > 0): bad[ wneg ] = True
        if (ninf > 0): bad[ winf ] = True
        good = np.invert( bad )

        #---------------------------------------------
        # Find smallest positive value in slope grid
        # and replace the "bad" values with smin.
        #---------------------------------------------
        S_min = self.slope[ good ].min()
        S_max = self.slope[ good ].max()
        self.slope[ bad ] = S_min        
                   
        #--------------------
        # Print information
        #--------------------
        if not(self.SILENT):
            print('Total number of slope values = ' + str(np.size(self.slope)) )
            print('Number of zero values        = ' + str(nzero) + ' (maybe edge)' )
            print('Number of negative values    = ' + str(nneg) )
            print('Number of NaN values         = ' + str(nnan) )
            print('Number of infinite values    = ' + str(ninf) )
            print('-------------------------------------------------')
            print('WARNING: Zero, negative or NaN slopes found.')
            print('         Replacing them with smallest slope.')
            print('         Consider using "new_slopes.py" instead.')
            print('         min(S) = ' + str(S_min))
            print('         max(S) = ' + str(S_max))
            print('-------------------------------------------------')
            print()

        #--------------------------------
        # Convert data type to double ?
        #--------------------------------
        if (FLOAT):    
            self.slope = np.float32(self.slope)
        else:    
            self.slope = np.float64(self.slope)
        
    #   remove_bad_slopes
    #-------------------------------------------------------------------
    
#-------------------------------------------------------------------
def Trapezoid_Rh(d, wb, theta):

    #-------------------------------------------------------------
    # Notes: Compute the hydraulic radius of a trapezoid that:
    #          (1) has a bed width of wb >= 0 (0 for triangular)
    #          (2) has a bank angle of theta (0 for rectangular)
    #          (3) is filled with water to a depth of d.
    #        The units of wb and d are meters.  The units of
    #        theta are assumed to be degrees and are converted.
    #-------------------------------------------------------------
    # NB!    wb should never be zero, so PW can never be 0,
    #        which would produce a NaN (divide by zero).
    #-------------------------------------------------------------
    #        See Notes for TF_Tan function in utils_TF.pro
    #            AW = d * (wb + (d * TF_Tan(theta_rad)) )
    #-------------------------------------------------------------    
    theta_rad = (theta * np.pi / 180.0)
    
    AW = d * (wb + (d * np.tan(theta_rad)) )      
    PW = wb + (np.float64(2) * d / np.cos(theta_rad) )
    Rh = (AW / PW)

    w  = np.where(wb <= 0)
    nw = np.size(w[0])
    
    return Rh

#   Trapezoid_Rh()
#-------------------------------------------------------------------
def Manning_Formula(Rh, S, nval):

    #---------------------------------------------------------
    # Notes: R = (A/P) = hydraulic radius [m]
    #        N = Manning's roughness coefficient
    #            (usually in the range 0.012 to 0.035)
    #        S = bed slope (assumed equal to friction slope)

    #        R,S, and N may be 2D arrays.

    #        If length units are all *feet*, then an extra
    #        factor of 1.49 must be applied.  If units are
    #        meters, no such factor is needed.

    #        Note that Q = Ac * u, where Ac is cross-section
    #        area.  For a trapezoid, Ac does not equal w*d.
    #---------------------------------------------------------
    ##  if (N is None): N = np.float64(0.03)

    two_thirds = np.float64(2) / 3.0
    
    u = (Rh ** two_thirds) * np.sqrt(S) / nval
    
    #------------------------------
    # Add a hydraulic jump option
    # for when u gets too big ??
    #------------------------------
    
    return u

#   Manning_Formula()
#-------------------------------------------------------------------
def Law_of_the_Wall(d, Rh, S, z0val):

    #---------------------------------------------------------
    # Notes: u  = flow velocity  [m/s]
    #        d  = flow depth [m]
    #        z0 = roughness height
    #        S  = bed slope (assumed equal to friction slope)

    #        g     = 9.81 = gravitation constant [m/s^2]
    #        kappa = 0.41 = von Karman's constant
    #        aval  = 0.48 = integration constant

    #        sqrt(g)/kappa = 7.6393d
    #        smoothness = (aval / z0) * d
    #        f = (kappa / alog(smoothness))^2d
    #        tau_bed = rho_w * f * u^2 = rho_w * g * d * S

    #        d, S, and z0 can be arrays.

    #        To make default z0 correspond to default
    #        Manning's n, can use this approximation:
    #        z0 = a * (2.34 * sqrt(9.81) * n / kappa)^6d
    #        For n=0.03, this gives: z0 = 0.011417
    #        However, for n=0.3, it gives: z0 = 11417.413
    #        which is 11.4 km!  So the approximation only
    #        holds within some range of values.
    #--------------------------------------------------------
##        if (self.z0val is None):    
##            self.z0val = np.float64(0.011417)   # (about 1 cm)

    #------------------------
    # Define some constants
    #------------------------
    g          = np.float64(9.81)    # (gravitation const.)
    aval       = np.float64(0.476)   # (integration const.)
    kappa      = np.float64(0.408)   # (von Karman's const.)
    law_const  = np.sqrt(g) / kappa
        
    smoothness = (aval / z0val) * d
      
    #-----------------------------
    # Make sure (smoothness > 1)
    #-----------------------------
    smoothness = np.maximum(smoothness, np.float64(1.1))

    u = law_const * np.sqrt(Rh * S) * np.log(smoothness)
    
    #------------------------------
    # Add a hydraulic jump option
    # for when u gets too big ??
    #------------------------------
    
    return u

#   Law_of_the_Wall()
#-------------------------------------------------------------------                 
