
# NB!   update_diversion() in channels_base.py is now COMMENTED OUT.
#
#--------------------------------------------------------------------
# Copyright (c) 2001-2023, Scott D. Peckham
#
# Aug 2023. Improved print_final_report() mass balance info.
#           Careful to distinguish between volumes that are
#           domain-time integrals of fluxes and volumes that
#           are domain_integrals for storage quantities.
# Oct 2021. Added CREATE_MEDIA_FILES, CREATE_INDICATORS.
#           Added set_missing_cfg_options().
#           Modified CFG file and finalize().
# May 2020. Wrote "vol_str()" for print_final_report()          
# Jan 2013. Revised handling of input/output names.
# Oct 2012. CSDMS Standard Names and BMI.
# May 2012. Q_outlet -> Q_outlet[0]   (5/19/12)
# May 2010. Changes to initialize() and read_cfg_file()
# Feb 2010. Channels comp. now calls dp.update() itself.)
# Apr, May, July, August 2009
# Jan 2009. Converted from IDL.
#
#--------------------------------------------------------------------
#
#  class topoflow_driver      (inherits from BMI_base.py)
#
#      get_component_name()
#      get_attribute()          # (10/26/11)
#      get_input_var_names()    # (5/16/12, Bolton)
#      get_output_var_names()   # (5/16/12, Bolton)
#      get_var_name()           # (5/16/12, Bolton)
#      get_var_units()          # (5/16/12, Bolton)
#      ---------------------
#      set_constants()
#      set_missing_cfg_options()  # (2021-10-24)
#      run_model()
#      initialize()
#      update()
#      finalize()
#      -----------------------------------
#      check_finished()
#      check_steady_state()   ###
#      check_interrupt()
#      -----------------------------------
#      initialize_time_vars()
#      initialize_stop_vars()
#      initialize_mass_totals()       # (OBSOLETE ??)
#      initialize_GUI()               # (commented out)
#      initialize_hydrograph_plot()   # (commented out)
#      -----------------------------------
#      update_mass_totals()           # (OBSOLETE ??)
#      update_hydrograph_plot()
#      -----------------------------------
#      vol_str()
#      print_final_report()
#      print_mins_and_maxes()
#      print_uniform_precip_data()
#      print_dimless_number_data()
#      print_mass_balance_report()
#
#-----------------------------------------------------------------------

import numpy as np
import os, os.path
import time

from topoflow.utils import BMI_base
from topoflow.utils import indicators        # (2021-10-24)
from topoflow.utils import visualize as vis  # (2021-10-24)

# These are very old; replace them soon.
from topoflow.utils.tf_utils import TF_String, TF_Version

#-----------------------------------------------------------------------
class topoflow_driver( BMI_base.BMI_component ):

    #-------------------------------------------------------------------
    # Don't define an __init__() function.
    # We need to inherit the BMI_base.__init__()
    #-------------------------------------------------------------------
    _att_map = {
        'model_name':         'TopoFlow_Driver',
        'version':            '3.1',
        'author_name':        'Scott D. Peckham',
        'grid_type':          'uniform',
        'time_step_type':     'fixed',
        'step_method':        'explicit',
        #-------------------------------------------------------------
        'comp_name':          'TopoFlow',
        'model_family':       'TopoFlow',
        'cfg_template_file':  'TopoFlow.cfg.in',
        'cfg_extension':      '_topoflow.cfg',
        'cmt_var_prefix':     '/TopoFlow/Input/Var/',
        'gui_xml_file':       '/home/csdms/cca/topoflow/3.1/src/share/cmt/gui/TopoFlow.xml',
        'dialog_title':       'TopoFlow: Driver Parameters',
        'time_units':         'seconds' }

    #------------------------------------------------------------------------------
    # (2/3/13) Added "channel_model__time_step" since it is needed by
    # both the TopoFlow driver (topoflow.py) and Diversions (diversion_base.py).
    # But source and sink files provide "dt" for Diversions, so check.
    #------------------------------------------------------------------------------
    _input_var_names = [
        'atmosphere_water__domain_time_integral_of_precipitation_leq-volume_flux', # vol_P
        'atmosphere_water__domain_time_max_of_precipitation_leq-volume_flux',    # P_max@meteorology
        'basin_outlet_water_flow__half_of_fanning_friction_factor',              # f_outlet@channels
        'basin_outlet_water_x-section__mean_depth',                              # d_outlet@channels
        'basin_outlet_water_x-section__peak_time_of_depth',                      # Td_peak@channels
        'basin_outlet_water_x-section__peak_time_of_volume_flow_rate',           # T_peak@channels
        'basin_outlet_water_x-section__peak_time_of_volume_flux',                # Tu_peak@channels
        'basin_outlet_water_x-section__time_integral_of_volume_flow_rate',       # vol_Q
        'basin_outlet_water_x-section__time_max_of_mean_depth',                  # d_peak@channels
        'basin_outlet_water_x-section__time_max_of_volume_flow_rate',            # Q_peak@channels
        'basin_outlet_water_x-section__time_max_of_volume_flux',                 # u_peak@channels
        'basin_outlet_water_x-section__volume_flow_rate',                        # Q_outlet@channels
        'basin_outlet_water_x-section__volume_flux',                             # u_outlet@channels
        'channel_bottom_water_flow__domain_max_of_log_law_roughness_length',     # z0val_max@channels
        'channel_bottom_water_flow__domain_min_of_log_law_roughness_length',     # z0val_min@channels
        ## 'channel_model__time_step',  ####################### (no longer needed?)
        'channel_water_flow__domain_max_of_manning_n_parameter',                 # nval_max@channels
        'channel_water_flow__domain_min_of_manning_n_parameter',                 # nval_min@channels
        #-----------------------------------------------------
        # These might only be available at the end of run ??
        # These are now over the entire domain (or DEM).
        #-----------------------------------------------------
        'channel_water_x-section__domain_max_of_mean_depth',                     # d_max
        'channel_water_x-section__domain_max_of_volume_flow_rate',               # Q_max
        'channel_water_x-section__domain_max_of_volume_flux',                    # u_max
        'channel_water_x-section__domain_min_of_mean_depth',                     # d_min
        'channel_water_x-section__domain_min_of_volume_flow_rate',               # Q_min
        'channel_water_x-section__domain_min_of_volume_flux',                    # u_min
#         'snowpack__domain_max_of_depth',                                       # hs_max
#         'snowpack__domain_min_of_depth',                                       # hs_min
        #-----------------------------------------------------------       
        'glacier_ice__domain_time_integral_of_melt_volume_flux',                 # vol_MR
        'land_surface_water__baseflow_volume_flux',                              # GW
        'land_surface_water__domain_time_integral_of_baseflow_volume_flux',      # vol_GW
        'land_surface_water__domain_time_integral_of_evaporation_volume_flux',   # vol_ET
        'land_surface_water__domain_time_integral_of_runoff_volume_flux',        # vol_R
        'land_surface_water__runoff_volume_flux',                                # R
        'snowpack__initial_domain_integral_of_liquid-equivalent_depth',          # vol_swe_start
        'snowpack__domain_integral_of_liquid-equivalent_depth',                  # vol_swe
        'snowpack__domain_time_integral_of_melt_volume_flux',                    # vol_SM
        'soil_surface_water__domain_time_integral_of_infiltration_volume_flux',  # vol_IN
        'soil_water__initial_domain_integral_of_volume_fraction',                # vol_soil_start
        'soil_water__domain_integral_of_volume_fraction',                        # vol_soil     
        'soil_water_sat-zone_top__domain_time_integral_of_recharge_volume_flux', # vol_Rg
        #-----------------------------------------------------------
        'channel_water_x-section__boundary_time_integral_of_volume_flow_rate',   # vol_edge
        'river-network_channel_water__initial_volume',                           # vol_chan_start
        'river-network_channel_water__volume',                                   # vol_chan
        #'land_surface_water__initial_area_integral_of_depth' ]                  # vol_flood_start
        'land_surface_water__area_integral_of_depth' ]                           # vol_flood
        
        #----------------------------------------------------------------
        # The TopoFlow driver no longer needs to get the time_steps of
        # the other model components; this is now the framework's job.
        # That means it can't include them in its final report.
        #----------------------------------------------------------------
##        'channel:model__time_step',     # dt@channels
##        'diversion:model__time_step',
##        'evap:model_time_step',
##        'ice:model_time_step',
##        'infil:model__time_step',
##        'meteorology:model__time_step',
##        'satzone:model__time_step',
##        'snow:model__time_step' ]

    _output_var_names = [
        'model__time_step' ]   # dt

    _var_name_map = {
        'atmosphere_water__domain_time_integral_of_precipitation_leq-volume_flux': 'vol_P',
        'atmosphere_water__domain_time_max_of_precipitation_leq-volume_flux':      'P_max',
        'basin_outlet_water_flow__half_of_fanning_friction_factor':          'f_outlet', 
        'basin_outlet_water_x-section__mean_depth':                          'd_outlet',
        'basin_outlet_water_x-section__peak_time_of_depth':                  'Td_peak',
        'basin_outlet_water_x-section__peak_time_of_volume_flow_rate':       'T_peak',
        'basin_outlet_water_x-section__peak_time_of_volume_flux':            'Tu_peak',
        'basin_outlet_water_x-section__time_integral_of_volume_flow_rate':   'vol_Q',
        'basin_outlet_water_x-section__time_max_of_mean_depth':              'd_peak',
        'basin_outlet_water_x-section__time_max_of_volume_flow_rate':        'Q_peak',
        'basin_outlet_water_x-section__time_max_of_volume_flux':             'u_peak',
        'basin_outlet_water_x-section__volume_flow_rate':                    'Q_outlet',
        'basin_outlet_water_x-section__volume_flux':                         'u_outlet', 
        'channel_bottom_water_flow__domain_max_of_log_law_roughness_length': 'z0val_max',
        'channel_bottom_water_flow__domain_min_of_log_law_roughness_length': 'z0val_min',   
        ## 'channel_model__time_step':                                          'channel_dt', ## (2/3/13)
        'channel_water_flow__domain_max_of_manning_n_parameter':             'nval_max',
        'channel_water_flow__domain_min_of_manning_n_parameter':             'nval_min',        
        #-------------------------------------------------------
        # These 6 might only be available at the end of run ??
        #-------------------------------------------------------
        'channel_water_x-section__domain_max_of_mean_depth':                     'd_max',
        'channel_water_x-section__domain_max_of_volume_flow_rate':               'Q_max',
        'channel_water_x-section__domain_max_of_volume_flux':                    'u_max',
        'channel_water_x-section__domain_min_of_mean_depth':                     'd_min',
        'channel_water_x-section__domain_min_of_volume_flow_rate':               'Q_min',
        'channel_water_x-section__domain_min_of_volume_flux':                    'u_min',
#         'snowpack__domain_max_of_depth':                                       'hs_max',
#         'snowpack__domain_min_of_depth':                                       'hs_min',
        #------------------------------------------------------------                
        'glacier_ice__domain_time_integral_of_melt_volume_flux':                 'vol_MR',
        'land_surface_water__baseflow_volume_flux':                              'GW',
        'land_surface_water__domain_time_integral_of_baseflow_volume_flux':      'vol_GW',
        'land_surface_water__domain_time_integral_of_evaporation_volume_flux':   'vol_ET',
        'land_surface_water__domain_time_integral_of_runoff_volume_flux':        'vol_R',
        'land_surface_water__runoff_volume_flux':                                'R',
        'snowpack__initial_domain_integral_of_liquid-equivalent_depth':          'vol_swe_start',        
        'snowpack__domain_integral_of_liquid-equivalent_depth':                  'vol_swe',
        'snowpack__domain_time_integral_of_melt_volume_flux':                    'vol_SM',       
        'soil_surface_water__domain_time_integral_of_infiltration_volume_flux':  'vol_IN',
        'soil_water__initial_domain_integral_of_volume_fraction':                'vol_soil_start', 
        'soil_water__domain_integral_of_volume_fraction':                        'vol_soil',    
        'soil_water_sat-zone_top__domain_time_integral_of_recharge_volume_flux': 'vol_Rg',
        #---------------------
        'model__time_step':                                      'dt',
        #------------------------------------------------------------------
        # Note: vol_chan and vol_flood are DEM-sized grids for the volume
        # of water in each grid cell channel and each grid cell extent.
        # In all other components, variables starting with "vol_" are
        # scalars that hold area-time integrals of fluxes or area
        # integrals of stored quantities.  Here, those end in "_sum" or
        # "sum0".  (2023-09-01)
        #------------------------------------------------------------------ 
        'channel_water_x-section__boundary_time_integral_of_volume_flow_rate': 'vol_edge',   
        'river-network_channel_water__initial_volume' :       'vol_chan_sum0',
        'river-network_channel_water__volume':                'vol_chan_sum',
        'land_surface_water__initial_area_integral_of_depth': 'vol_flood_sum0',   
        'land_surface_water__area_integral_of_depth':         'vol_flood_sum' }       

            
    _var_units_map = {
        'atmosphere_water__domain_time_integral_of_precipitation_leq-volume_flux': 'm3',
        'atmosphere_water__domain_time_max_of_precipitation_leq-volume_flux':      'm s-1',
        'basin_outlet_water_flow__half_of_fanning_friction_factor':                '1',
        'basin_outlet_water_x-section__mean_depth':                                'm',
        'basin_outlet_water_x-section__peak_time_of_depth':                        'min',
        'basin_outlet_water_x-section__peak_time_of_volume_flow_rate':             'min',
        'basin_outlet_water_x-section__peak_time_of_volume_flux':                  'min',
        'basin_outlet_water_x-section__time_integral_of_volume_flow_rate':         'm3',
        'basin_outlet_water_x-section__time_max_of_mean_depth':                    'm',
        'basin_outlet_water_x-section__time_max_of_volume_flow_rate':              'm3 s-1',
        'basin_outlet_water_x-section__time_max_of_volume_flux':                   'm s-1',
        'basin_outlet_water_x-section__volume_flow_rate':                          'm3 s-1',
        'basin_outlet_water_x-section__volume_flux':                               'm s-1',
        'channel_bottom_water_flow__domain_max_of_log_law_roughness_length':       'm',
        'channel_bottom_water_flow__domain_min_of_log_law_roughness_length':       'm',        
        ## 'channel_model__time_step':                                                's', ### (2/3/13)
        'channel_water_flow__domain_max_of_manning_n_parameter':                   'm-1/3 s',        
        'channel_water_flow__domain_min_of_manning_n_parameter':                   'm-1/3 s',
        #-----------------------------------------------------
        # These might only be available at the end of run ??
        #-----------------------------------------------------
        'channel_water_x-section__domain_max_of_mean_depth':                       'm',
        'channel_water_x-section__domain_max_of_volume_flow_rate':                 'm3 s-1',
        'channel_water_x-section__domain_max_of_volume_flux':                      'm s-1',
        'channel_water_x-section__domain_min_of_mean_depth':                       'm',
        'channel_water_x-section__domain_min_of_volume_flow_rate':                 'm3 s-1',
        'channel_water_x-section__domain_min_of_volume_flux':                      'm s-1',
#         'snowpack__domain_max_of_depth':                                         'm',
#         'snowpack__domain_min_of_depth':                                         'm',
        #------------------------------------------------------------                
        'glacier_ice__domain_time_integral_of_melt_volume_flux':                   'm3',
        'land_surface_water__baseflow_volume_flux':                                'm s-1',
        'land_surface_water__domain_time_integral_of_baseflow_volume_flux':        'm3',
        'land_surface_water__domain_time_integral_of_evaporation_volume_flux':     'm3',
        'land_surface_water__domain_time_integral_of_runoff_volume_flux':          'm3',
        'land_surface_water__runoff_volume_flux':                                  'm s-1',
        'network_channel_water__volume':                                           'm3',
        'snowpack__initial_domain_integral_of_liquid-equivalent_depth':            'm3',
        'snowpack__domain_integral_of_liquid-equivalent_depth':                    'm3',
        'snowpack__domain_time_integral_of_melt_volume_flux':                      'm3',        
        'soil_surface_water__domain_time_integral_of_infiltration_volume_flux':    'm3',
        'soil_water__initial_domain_integral_of_volume_fraction':                  'm3',
        'soil_water__domain_integral_of_volume_fraction':                          'm3',
        'soil_water_sat-zone_top__domain_time_integral_of_recharge_volume_flux':   'm3',
        #----------------------------
        'model__time_step': 's',
        #----------------------------------------------------------------------------
        'channel_water_x-section__boundary_time_integral_of_volume_flow_rate': 'm3',  
        'river-network_channel_water__initial_volume' : 'm3',
        'river-network_channel_water__volume':          'm3',
        'land_surface_water__initial_area_integral_of_depth': 'm3',
        'land_surface_water__area_integral_of_depth':         'm3'  }  
    
    #------------------------------------------------    
    # Return NumPy string arrays vs. Python lists ?
    #------------------------------------------------
    ## _input_var_names  = np.array( _input_var_names )
    ## _output_var_names = np.array( _output_var_names )

    #-------------------------------------------------------------------
    def get_component_name(self):
  
        return 'TopoFlow_Driver'  ##### TopoFlow_Run_Monitor,  Report_Maker?

    #   get_component_name()           
    #-------------------------------------------------------------------
    def get_attribute(self, att_name):

        try:
            return self._att_map[ att_name.lower() ]
        except:
            print('###################################################')
            print(' ERROR: Could not find attribute: ' + att_name)
            print('###################################################')
            print(' ')

    #   get_attribute()
    #-------------------------------------------------------------------
    def get_input_var_names(self):

        #--------------------------------------------------------
        # Note: These are currently variables needed from other
        #       components vs. those read from files or GUI.
        #--------------------------------------------------------   
        return self._input_var_names
    
    #   get_input_var_names()
    #-------------------------------------------------------------------
    def get_output_var_names(self):
 
        return self._output_var_names
    
    #   get_output_var_names()
    #-------------------------------------------------------------------
    def get_var_name(self, long_var_name):
            
        return self._var_name_map[ long_var_name ]

    #   get_var_name()
    #-------------------------------------------------------------------
    def get_var_units(self, long_var_name):

        return self._var_units_map[ long_var_name ]
   
    #   get_var_units()
    #-------------------------------------------------------------------
    def set_constants(self):

        #------------------------
        # Define some constants
        #------------------------
        self.mps_to_mmph = np.float64(3600000)   # [m/s] to [mm/hr]

        #------------------------------------------
        # Moved these from __init__() on 5/17/12.
        #------------------------------------------
        self.OK           = True
        self.comment      = None
        self.WRITE_LOG    = True
        self.VERBOSE      = False
        self.PLOT         = False
       
    #   set_constants() 
    #-------------------------------------------------------------------
    def set_missing_cfg_options(self):

        #--------------------------------------------------------
        # (2021-10-24) Added CREATE_INDICATORS flag to CFG file
        # to create a set of indicators (netCDF) at end.
        #--------------------------------------------------------
        if not(hasattr(self, 'COMPUTE_STAT_GRIDS')):
            self.COMPUTE_STAT_GRIDS = False
            
        #--------------------------------------------------------
        # (2021-10-24) Added CREATE_INDICATORS flag to CFG file
        # to create a set of indicators (netCDF) at end.
        #--------------------------------------------------------
        if not(hasattr(self, 'CREATE_INDICATORS')):
            self.CREATE_INDICATORS = False
            
        #-----------------------------------------------------
        # (2021-10-24) Added CREATE_MEDIA_FILES flag to CFG
        # file to create a set of media files at the end.
        #-----------------------------------------------------
        if not(hasattr(self, 'CREATE_MEDIA_FILES')):
            self.CREATE_MEDIA_FILES = False  

        #--------------------------------------------------------
        # (2021-11-18) Added media_directory due to Dojo issue.
        #--------------------------------------------------------
        if not(hasattr(self, 'media_directory')):
            self.media_directory = os.path.expanduser('~/media/') 

   
    #   set_missing_cfg_options()      
    #-------------------------------------------------------------------
    def initialize(self, cfg_file=None, mode="nondriver",
                   SILENT=False):

        #------------------------------------------------------
        # Note:  If using as a CCA component, then we need to
        #        call "get_cca_ports()" before calling this
        #        "initialize()" method in the component's CCA
        #        Impl file.
        #------------------------------------------------------
        self.SILENT = SILENT
        if not(self.SILENT):
            print()
            print('TopoFlow component: Initializing...')
        
        self.status     = 'initializing'  # (OpenMI 2.0 convention)
        self.mode       = mode
        self.cfg_file   = cfg_file
        
        #-----------------------------------------------
        # Load component parameters from a config file
        #-----------------------------------------------
        self.set_constants()
        self.initialize_config_vars()
        self.set_missing_cfg_options()  # (2021-10-24)
        # self.read_grid_info()    # NOW IN initialize_config_vars()
        self.initialize_basin_vars()  # (5/14/10)

        #--------------------------------
        # Has component been disabled ?
        #--------------------------------
        if (self.comp_status.lower() == 'disabled'):
            if not(self.SILENT):
                print('TopoFlow Main component: Disabled in CFG file.')
            self.DONE = True
            self.status = 'initialized.'
            return
        
        dc = (self.out_directory + self.case_prefix)
        self.comment_file = dc + '_comments.txt'
        self.log_file     = dc + '.log'

        #-----------------------
        # Initialize variables
        #-----------------------
        self.initialize_time_vars()  # (uses cp.dt from above)
        self.initialize_stop_vars()   #### (do this with CFG file ?)
    
        #---------------------
        # Open the logfile ?      *** (Append or overwrite ??)
        #---------------------
        if (self.WRITE_LOG):
            if (self.log_file == None):
                self.log_file = (self.case_prefix + '_LOG.txt')
            self.log_unit = open(self.log_file, 'w')
            
            if not(self.SILENT):
                print('Opening log file:')
                print('    log_file = ' + self.log_file)

        #----------------------
        # Print start message
        #----------------------
        if not(self.SILENT):
            print('Starting TopoFlow model run...')
            ## hline = ''.ljust(60, '-')
            ## print(hline)
        self.status = 'initialized'
        
    #   initialize()        
    #-------------------------------------------------------------            
    ## def update(self, dt=-1.0, time_seconds=None):
    def update(self, dt=-1.0):

        #--------------------------------------------------
        # Note:  This method no longer calls the update()
        # methods of other components; this is now taken
        # care of by the EMELI framework, regardless of
        # which component is the "driver". (2/4/13)
        #--------------------------------------------------
        # Note:  In "*_topoflow.cfg", should set dt to
        # smallest value of other components, otherwise
        # print_time_and_value() may not report info at
        # the requested time interval (e.g. 0.5 secs).
        #--------------------------------------------------
                
        #-------------------------------
        # Check for interrupt by user ?
        #-------------------------------
        # OK = self.check_interrupt()
        # if not(OK):
        #    self.status = 'stopped'
        #    return
        
        # self.DEBUG = True  ########################

        #--------------------------------
        # Has component been disabled ?
        #--------------------------------
        if (self.comp_status.lower() == 'disabled'):
            # Note: self.status should be 'initialized'.
            return
       
        self.status = 'updating'
        OK = True
        if (self.mode == 'driver') and not(self.SILENT):
            self.print_time_and_value(self.Q_outlet, 'Q_out', '[m^3/s]',
                                      interval=0.5)  # [seconds]
            
        ## self.update_hydrograph_plot()
       
        #-------------------------
        # Increment the timestep
        #-------------------------------------------------------
        # Note that the update_time() method in BMI_base.py
        # calls "check_finished()".  There is a simple version
        # of "check_finished()" in BMI_base.py and another
        # version in this file that supports more general
        # stopping conditions, including "steady state".
        #------------------------------------------------------   
        self.update_time( dt )
        self.status = 'updated'
        
    #   update()          
    #-------------------------------------------------------------            
    def finalize(self):

        #--------------------------------
        # Has component been disabled ?
        #--------------------------------
        if (self.comp_status.lower() == 'disabled'):
            # Note: self.status should be 'initialized'.
            return
        self.status = 'finalizing'

        #--------------------------------------------
        # This is called by the update() method.
        # We'd like to force another output, but it
        # is now based on elapsed time.  10/29/11.
        #--------------------------------------------        
        # if (self.mode == 'driver'):
        #     self.print_time_and_value(self.Q_outlet, 'Q_out', '[m^3/s]')
 
        if not(self.SILENT):
            print('=======================')
            print('Simulation complete.')
            print('=======================')
            print()
        
        #----------------
        # Print reports
        #----------------
        if not(self.SILENT):
            self.print_final_report()
##        self.print_mins_and_maxes( FINAL=True )   # (Moved into final report.)
##        self.print_uniform_precip_data()  # (not ready yet)
##        self.print_mass_balance_report()  # (not ready yet)

        #--------------------
        # Close the logfile
        #--------------------
        if (self.WRITE_LOG):
            ## print '###  Closing log file.'
            self.log_unit.close()

        #----------------------
        # Print final message
        #----------------------
        if not(self.SILENT):
            print('Finished.' + '  (' + self.case_prefix + ')')
            print()
        self.status = 'finalized'

        #--------------------------------------------------   
        # Option to create a set of indicator grid stacks
        #--------------------------------------------------
        if (self.CREATE_INDICATORS):
            ## print('#### misc_directory =', self.misc_directory )
            ## print('#### COMPUTE_STAT_GRIDS = ', self.COMPUTE_STAT_GRIDS )
            indicators.create_indicator_grid_stacks(
                       case_prefix=self.case_prefix,
                       output_dir=self.out_directory,
                       pop_dir=self.misc_directory,
                       compute_stat_grids=self.COMPUTE_STAT_GRIDS,
                       OVERWRITE_OK=self.OVERWRITE_OK)

        #------------------------------------------------  
        # Option to create a set of visualization files
        #------------------------------------------------            
        if (self.CREATE_MEDIA_FILES):
            vis.create_media_files(
                output_dir=self.out_directory,
                media_dir=self.media_directory,  # 2021-11-18
                topo_dir=self.topo_directory,
                met_dir=self.met_directory,
                misc_dir=self.misc_directory,
                site_prefix=self.site_prefix,
                case_prefix=self.case_prefix,
                DEM_ncols=self.grid_info.nx,   ######
                DEM_nrows=self.grid_info.ny,   ######
                movie_fps=10,
                start_date=self.time_info.start_date,
                end_date=self.time_info.end_date,
                time_interval_hours=1,
                STAT_MOVIES=self.COMPUTE_STAT_GRIDS)
                ## time_interval_hours=6)   # Assuming CHIRPS 6hr rain.        
                #### OVERWRITE_OK=self.OVERWRITE_OK)
 
    #----------------------------------------------------------------   
    # Note:  There is a Jupyter notebook that can be used after a
    #        successful model run to re-create the indicator and
    #        media files: TopoFlow_Redo_Indicators_and_Media.ipynb.
    #----------------------------------------------------------------
                     
    #   finalize()
    #-------------------------------------------------------------            
    def check_finished(self):

        #------------------------------------------------------ 
        # Notes: This version of "check_finished()" overrides
        #        the simpler one that all components inherit
        #        from BMI_base.py.
        #------------------------------------------------------ 
        
        #---------------------------------
        # Methods to stop the simulation
        #---------------------------------
        if (self.stop_method == 'Q_peak_fraction'):
            #----------------------------------------------------
            # Run until the outlet hydrograph drops to less
            # than "Qp_fraction" of the peak value before that.
            #----------------------------------------------------  
            FALLING_LIMB = (self.Q_last > self.Q_outlet)
            
##            if (FALLING_LIMB):  print "ON FALLING LIMB..."
##            print 'self.Q_last  =', self.Q_last
##            print 'self.Q_outlet =', self.Q_outlet
##            print ' '
            
            #--------------------------------------------------------
            # With DYNAMIC_WAVE, it is possible for some reason for
            # Q_outlet to drop back to zero early in the simulation
            # so that model run ends right away.  (2/13/07)
            # Uncomment the debugging section below.
            #--------------------------------------------------------
            if (FALLING_LIMB):
                Q_stop   = (self.Q_peak * self.Qp_fraction)
                self.DONE = (self.Q_outlet <= Q_stop) and \
                            (self.Q_outlet > 0)

            if (self.DONE and not(self.SILENT)):
                stop_str = str(self.Qp_fraction) + '.\n'
                print('Stopping: Reached Q_peak fraction = ' + stop_str)
                
##            print 'FALLING_LIMB   =', FALLING_LIMB
##            print 'Q_last         =', self.Q_last
##            print 'Q_peak         =', self.Q_peak
##            print 'Qpeak_fraction =', self.Qp_fraction
##            print ' '
            
                #--------------
                # For testing
                #--------------
                #if (DONE):
                #    print 'Q_last         =', self.Q_last
                #    print 'Q_peak         =', self.Q_peak
                #    print 'Qpeak_fraction =', self.Qp_fraction
                #    print 'Q[self.outlet_ID]   =', Q_outlet
                #    print 'Q_stop         =', Q_stop
                #    print ' '

        elif (self.stop_method == 'Until_model_time'):
            #--------------------------------------------------
            # Run until specified "stopping time", in minutes
            #--------------------------------------------------
            self.DONE = (self.time_min >= self.T_stop)  # [minutes]
            if (self.DONE and not(self.SILENT)):
                stop_str = str(self.T_stop) + '.\n'
                print('Stopping: Reached stop time = ' + stop_str)
        elif (self.stop_method == 'Until_n_steps'):
            #--------------------------------------
            # Run for a specified number of steps
            #--------------------------------------
            self.DONE = (self.time_index >= self.n_steps)
            if (self.DONE and not(self.SILENT)):
                stop_str = str(self.n_steps) + '.\n'
                print('Stopping: Reached number of steps = ' + stop_str)
        else:
            raise RuntimeError('No match found for expression')

        #--------------------------------------------------------------
        # This model run is finished if the user-selected stopping
        # condition has been reached (above) OR if the model appears
        # to have reached a steady-state condition with discharge,
        # OR if the channel component has failed for some reason.
        # (2/4/13)
        #--------------------------------------------------------------
        FINISHED = self.DONE
        STEADY   = self.check_steady_state()
        # FAILED = (self.cp.get_status() == 'failed')  ###### FIX SOON (5/18/12)
        FAILED   = False
        if (FAILED):
            if (self.DEBUG): print('CHANNELS.update() failed.')
            self.status   = 'failed'
            ### self.Q_outlet = np.float64(0)   # (why is this here?)
        ### self.Q_last = self.Q_outlet
        self.Q_last = self.Q_outlet.copy()  ## (2/7/13)
        self.DONE   = (FINISHED or STEADY or FAILED)

        return self.DONE
      
    #   check_finished()
    #-------------------------------------------------------------------
    def check_steady_state(self):

        #-------------------------------------------------------
        # Notes:  See "initialize_stop_vars()" for definitions
        #         of steady_tol, nonzero_tol, n_same_max and
        #         Q_last.
        #-------------------------------------------------------
        STEADY = False
    
        #------------------------------------------
        # Count number of steps with same Q-value
        #------------------------------------------
        delta_Q = np.absolute(self.Q_outlet - self.Q_last)
        if ( delta_Q <= self.steady_tol ):
            ## print '(time_index, dQ) =', self.time_index, delta_Q
            self.n_same += 1
        else:
            self.n_same  = 0
        
        #------------------------------------
        # Check for steady-state, with Q > 0
        #------------------------------------
        if (self.stop_method == 'Q_peak_fraction') and \
           (self.Q_outlet > self.nonzero_tol) and \
           (self.n_same   > self.n_same_max):

            STEADY = True
            if not(self.DONE):   # (5/19/12. No message if already done.)
                msg = ['-----------------------------------------------------------', \
                       'WARNING: It appears that discharge, Q, has reached', \
                       '         a steady-state condition.', \
                       '         Discharge at outlet near: ' + str(self.Q_outlet), \
                       '             for ' + str(self.n_same) + ' timesteps.', \
                       '         Aborting model run.', \
                       '-----------------------------------------------------------', \
                       ' ']
                       ### 'Do you want to continue anyway ?', ' '])
                for line in msg:
                    print(line)

            
            ## answer = GUI_Message(msg, QUESTION=True)
            ## DONE = (answer.lower() == 'no')
            ## if not(DONE):    
            ##     n_same = int32(0)
            ##
            #print('****************************************************')
            #print('Aborting model run: ')
            #print('Discharge, Q, has reached steady-state.')
            #print('****************************************************')
            #msg = [ $
            #'WARNING:  Route_Flow aborted.', ' ',$
            #'Discharge, Q, has reached steady-state. ', ' ']
            #GUI_Error_Message, msg
            #STEADY = True
        
        #-----------------------------------------------
        # (3/20/07) Commented out, since user can now
        # press any key to stop the model run.  Note
        # that Q-value can remain zero for a long time
        # if everything is infiltrating or snow depth
        # is building, etc.
        #-----------------------------------------------
        # Check for unchanging Q-value of zero ?
        #-----------------------------------------
        #if (STOP_METHOD eq 0b) AND (Q_peak eq 0.0) AND (n_same gt nn) then begin
        #    msg = [' ', $
        #    'ERROR: ', ' ', $
        #    'Discharge at outlet is zero for all times. ', ' ',$
        #    'Is there a runoff-producing process ? ', ' ']
        #    print('*************************************************')
        #    print( msg[1] )
        #    print( msg[3] )
        #    print('*************************************************')
        #    print()
        #    GUI_Error_Message, msg
        #    DONE = 1b
        #endif
          
        return STEADY
    
    #   check_steady_state
    #-------------------------------------------------------------
    def check_interrupt(self):

        #------------------------------------------------------------
        #( 3/21/07) This method checks for a keyboard interrupt
        # after a fixed amount of real time has elapsed.  This
        # works much better than using something like (n mod n_check)
        # since it avoids checking fast runs too often (which slows
        # down performance) or slow runs too seldom (which means the
        # user can't interrupt the run).  It only checks the elapsed
        # time once each time through the loop, however, so the time
        # required for one pass imposes a lower bound.
        #------------------------------------------------------------
        elapsed_time = (time.time() - self.last_check_time)
        if (elapsed_time > 2):    
            #print,'****************************************************'
            #print,'Checking interrupt: n = ' + TF_String(n)
            #print,'****************************************************'

            ########################################
            ##  REPLACE WITH THE CODE ITSELF
            ########################################
            ## Check_Interrupt(STOP_ID, OK)
            OK = True  # (over-ridden, for now)
            
            if not(OK):
                self.finalize()
                ## if not(self.SILENT)):
                print()
                print('----------------------------------')
                print(' Simulation terminated by user.')
                print('----------------------------------')
                return

            self.last_check_time = time.time()

    #   check_interrupt()
    #-------------------------------------------------------------
    def initialize_time_vars(self):

        #------------------
        # Start the clock
        #------------------
        self.start_time = time.time()

        #--------------------------------
        # Initialize the time variables
        #--------------------------------        
        self.time_units = 'seconds'
        self.time_index = np.int32(0)
        self.time       = np.float64(0)
        self.DONE       = False
        
        self.time_sec   = np.float64(0)
        self.time_min   = np.float64(0)

        self.last_check_time  = time.time()  # (for check_interrupt() )
        self.last_print_time  = time.time()  # (for print_time_and_value() )
        self.last_plot_time   = np.float64(0)   # (for update_hydrograph_plot() )

        #---------------------------------------
        # Set the model run timestep to that
        # of the "channel_flow" process [secs]
        #---------------------------------------
        ### self.dt = self.channel_dt  # (5/17/12.  New framework approach.)
        
    #   initialize_time_vars()
    #-------------------------------------------------------------
    def initialize_stop_vars(self):

        if not(self.SILENT):
            print('Setting stop method to: ' + self.stop_method)

        #---------------------------------------------------------
        # Define some constants for "check_steady_state() method
        #----------------------------------------------------------------
        # Best value of tolerance also depends on the time step.
        # For "plane" case, result changed with timestep = 2 or 4 secs.
        #----------------------------------------------------------------
        # "Optimal" value of steady_tol was found by trial and error.
        #----------------------------------------------------------------        
        self.steady_tol  = np.float64(1E-5)
        self.nonzero_tol = np.float64(1E-5)
        #self.nonzero_tol = 1e-6      #(worked better for "plane" case with step=2s)
        self.n_same      = np.int32(0)
        self.n_same_max  = np.int32(499) # (a number of time steps)

        #-------------------------------------------------------------- 
        # Note: Q_last will be compared to Q_outlet later, so we
        #       must use copy() method for them to ever be different.
        #       Q_outlet is a mutable scalar reference from channels.
        #--------------------------------------------------------------        
        self.Q_last = self.Q_outlet.copy()
        
        if (self.stop_method == 'Q_peak_fraction'):
            #----------------------------------------------------
            # Run until the outlet hydrograph drops to less
            # than "Qp_fraction" of the peak value before that.
            #----------------------------------------------------
            T_stop = 0
            Tstr   = '  [min]'
        elif (self.stop_method == 'Until_model_time'):
            #--------------------------------------------------
            # Run until specified "stopping time", in minutes
            #--------------------------------------------------
            T_stop = self.T_stop_model
            mstr   = ('%10.2f' % T_stop)
            Tstr   = ' of ' + mstr + '  [min]'
        elif (self.stop_method == 'Until_n_steps'):
            #--------------------------------------
            # Run for a specified number of steps
            #--------------------------------------
            n_steps = self.n_steps
            T_stop  = (n_steps * self.dt / np.float64(60))   #[sec] -> [min]
            mstr    = ('%10.2f' % T_stop)
            Tstr   = ' of ' + mstr + '  [min]'
        else:
            print('ERROR: Invalid stopping method.')
            return

        self.T_stop = T_stop
        self.Tstr   = Tstr
            
    #   initialize_stop_vars()       
    #-------------------------------------------------------------
##    def initialize_gui(self):
##        
##        #-----------------------------------------
##        # Set various widget IDs and info
##        # (should this be called by __init__ ??)
##        #-----------------------------------------
##        self.leader_ID  = np.int32(0)
##        self.base_ID    = int32(0)
##        self.start_ID   = int32(0)
##        self.stop_ID    = int32(0)
##        self.draw_ID    = int32(0)
##        self.win_num    = int32(0)   ########
##        self.temp_winID = int32(-1)
##        self.npanels    = npanels
##        self.panel_IDs  = zeros([npanels], dtype='int32')
##        
##        self.stop_method_ID = int32(0)  #####
##
##        #----------------------------------------
##        # Option to plot hydrograph dynamically
##        #----------------------------------------
##        if (self.PLOT):
##            self.initialize_hydrograph_plot()
##
##    #   initialize_gui()
    #-------------------------------------------------------------
##    def initialize_hydrograph_plot(self):
##        
##        #------------------------------------------------------
##        # NB! Get the window number for the draw widget.
##        #     This assumes that a small draw window has been
##        #     added in the output log panel.  See the function
##        #     called GUI_Stopping in GUI_main.pro.
##        #------------------------------------------------------
##        # NB! Rainbow + white color table was loaded earlier
##        #     by GUI_Stopping, so black=0 and white=255.
##        #------------------------------------------------------
##        ## Initialize_Hydrograph_Window(DRAW_ID, win_num)
##        
##        self.nQ = int32(0)
##        self.nQ_init = int16(1000)
##        nQ_max = self.nQ_init
##        self.tvals = zeros([nQ_max], dtype='float32')
##        self.Qvals = zeros([nQ_max], dtype='float32')  
##
##    #   initialize_hydrograph_plot()
    #-------------------------------------------------------------
    def update_hydrograph_plot(self):
        
        #-----------------------------------------
        # Plot hydrograph up until now (3/22/07)
        #-----------------------------------------
        # plus sign (psym=1), point (psym=3)
        #-----------------------------------------
        elapsed_plot_time = (self.time_min - self.last_plot_time)
        if (self.PLOT and (elapsed_plot_time > 1.0)):    
            #------------------------------------
            # Report an "instantaneous" Q value
            #------------------------------------
            ########################
            nQ      = self.nQ
            nQ_init = self.nQ_init
            tvals   = self.tvals
            Qvals   = self.Qvals
            ########################
            Q_main_out = Pixel_Var(self.cp.Q, self.outlet_ID)   ########
            self.tvals[nQ] = self.time_min
            self.Qvals[nQ] = Q_main_out
            matplotlib.pyplot.figure( self.win_num + 1 )
            matplotlib.pyplot.plot(tvals[0:nQ+1], Qvals[0:nQ+1], \
                                   color='k', marker='.')
            matplotlib.pyplot.axes(axisbg='w')
            matplotlib.pyplot.ylim(np.array(0, np.float64(1.03) * Qvals.max()))
            matplotlib.pyplot.show()  #**** -1
            time.sleep( np.float64(0.005) )  #[seconds]
            nQ = (nQ + np.int32(1))
            if (nQ == self.nQ_max):
                ## Use np.concatenate() here ??
                tvals = array([tvals, np.zeros([nQ_init], dtype='float32')])
                Qvals = array([Qvals, np.zeros([nQ_init], dtype='float32')])
                self.nQ_max = np.size(tvals)
            self.last_plot_time = self.time_min
            ########################
            self.nQ     = nQ
            self.tvals  = tvals
            self.Qvals  = Qvals
            ########################

    #   update_hydrograph_plot()
    #-------------------------------------------------------------
    def vol_str( self, value ):
    
        if (np.abs(value) < 1e6):
            return (str(value) + ' [m^3]')
        else:
            new_val = (value / 1e6)
            return (str(new_val) + ' x 10^6 [m^3]')

    #   vol_str()
    #-------------------------------------------------------------
    def print_final_report(self, comp_name='TopoFlow',
                           mode='nondriver'):

        #------------------------------------------------------
        # NB! This overrides BMI_base.print_final_report(),
        # so it must have the same arguments. (10/27/11)
        #------------------------------------------------------
        
        #------------------------------------
        # Gather information for the report
        #------------------------------------
        NAME      = self.site_prefix
        COMMENT   = self.comment
        T_stop    = self.T_stop
        Q_final   = self.Q_outlet
        T_final   = self.time_min
        outlet_ID = self.outlet_ID
        n_steps   = self.time_index
        # outlet_col = (outlet_ID % self.nx)   ## (may need this)
        # outlet_row = (outlet_ID / self.nx)

        #---------------------------------------
        # New framework method with 0-d numpy
        # arrays for mutable scalars (2/7/13).
        #---------------------------------------
        Q_peak     = self.Q_peak
        T_peak     = self.T_peak
        u_peak     = self.u_peak
        Tu_peak    = self.Tu_peak
        d_peak     = self.d_peak
        Td_peak    = self.Td_peak
        #--------------------------
        P_max      = self.P_max
        #--------------------------
        vol_P  = self.vol_P   ##### maybe:  vol_sum_P
        vol_Q  = self.vol_Q   ##### maybe:  vol_sum_Q
        vol_SM = self.vol_SM
        vol_MR = self.vol_MR
        vol_ET = self.vol_ET
        vol_IN = self.vol_IN
        vol_Rg = self.vol_Rg
        vol_GW = self.vol_GW
        vol_R  = self.vol_R
        vol_edge = self.vol_edge
        #------------------------------------------------------------------
        # Note: vol_chan and vol_flood are DEM-sized grids for the volume
        # of water in each grid cell channel and each grid cell extent.
        # In all other components, variables starting with "vol_" are
        # scalars that hold area-time integrals of fluxes or area
        # integrals of stored quantities.  Here, those end in "_sum" or
        # "sum0".  (2023-09-01)
        #------------------------------------------------------------------
        vol_chan_start  = self.vol_chan_sum0
        vol_chan_final  = self.vol_chan_sum
        #--------------------------------------
        vol_flood_start = 0.0  ## placeholder
        vol_flood_final = self.vol_flood_sum
        #--------------------------------------
        vol_soil_start  = self.vol_soil_start      
        vol_soil_final  = self.vol_soil
        #--------------------------------------
        vol_swe_start   = self.vol_swe_start
        vol_swe_final   = self.vol_swe
        #--------------------------------------        
        basin_area = self.basin_area
          
        #----------------------------
        # Construct run time string
        #----------------------------
        run_time = (time.time() - self.start_time)
        if (run_time > 60):
            run_time = run_time / np.float64(60)
            rt_units = ' [min]'
        else:
            rt_units = ' [sec]'
        run_time_str = str(run_time) + rt_units

        #-----------------------------------------------      
        # Prepare to save report as a list of strings
        #-----------------------------------------------
        report = list()  ############# (NEW: 11/15/16)

        #-------------------
        # Build the report
        #-------------------
        hline = ''.ljust(60, '-')
        report.append( hline )
        report.append( TF_Version() )
        report.append( time.asctime() )  #####
        report.append(' ')
        # report.append('Simulated Hydrograph for ' + NAME)
        report.append('Input directory:      ' + self.in_directory)
        report.append('Output directory:     ' + self.out_directory)
        report.append('Site prefix:          ' + self.site_prefix)
        report.append('Case prefix:          ' + self.case_prefix)
        if (COMMENT is not None):
            report.append(' ')
            report.append( COMMENT )
        
        report.append(' ')
        report.append('Simulated time:      ' + str(T_final) + ' [min]')
        report.append('Program run time:    ' + run_time_str)
        report.append(' ')
        report.append('Number of timesteps: ' + str(n_steps))
        report.append('Number of columns:   ' + str(self.nx) )
        report.append('Number of rows:      ' + str(self.ny) )
        report.append(' ')

        if (self.stop_method == 'Until_model_time'):    
            report.append('T_stop:            ' + str(T_stop) + ' [min]')
            report.append(' ')
        report.append('Main outlet ID:    ' + str(outlet_ID) + ' (row, col)')
        report.append('Basin_area:        ' + str(basin_area) + ' [km^2] ')
        #*** report.append('Basin_length:      ' + TF_String(basin_length) + ' [m]')
        report.append(' ')
            
        if (hasattr(self, 'nval_min')):
            if (self.nval_min != -1):
                report.append("Min Manning's n:   " + str(self.nval_min))
                report.append("Max Manning's n:   " + str(self.nval_max))

        if (hasattr(self, 'z0val_min')):
            if (self.z0val_min != -1):
                report.append("Min z0 value:      " + str(self.z0val_min) + ' [m]')
                report.append("Max z0 value:      " + str(self.z0val_max) + ' [m]')
            
        report.append(' ')
        report.append('Q_final:           ' + str(Q_final) + ' [m^3/s]')
        report.append('Q_peak:            ' + str(Q_peak)  + ' [m^3/s]')
        report.append('Q_peak_time:       ' + str(T_peak)  + ' [min]')
        report.append('u_peak:            ' + str(u_peak)  + ' [m/s]')
        report.append('u_peak_time:       ' + str(Tu_peak) + ' [min]')
        report.append('d_peak:            ' + str(d_peak)  + ' [m]')
        report.append('d_peak_time:       ' + str(Td_peak) + ' [min]')
        report.append(' ')
            
        #--------------------------------
        # Print the maximum precip rate
        #--------------------------------
        MPR = (P_max * self.mps_to_mmph)   # ([m/s] -> [mm/hr])
        report.append('Max(precip rate):  ' + str(MPR) + ' [mm/hr]')
        report.append(' ')
    
        #------------------------------------------------
        # Print the area_time integrals over entire DEM
        #------------------------------------------------
        vol_in  = (vol_P + vol_SM + vol_MR + vol_GW)
        vol_out = (vol_IN + vol_ET + vol_edge)
        ## report.append('Total accumulated volumes over entire DEM: (fluxes)')
        report.append('Total flux volumes:  Area-time integrals over the DEM:')
        report.append('___Input fluxes___:')
        report.append('  vol_P    (precip):       ' + self.vol_str(vol_P)    + '  (incl. leq snowfall)')
        report.append('  vol_SM   (snowmelt):     ' + self.vol_str(vol_SM))
        report.append('  vol_MR   (icemelt):      ' + self.vol_str(vol_MR))
        report.append('  vol_GW   (baseflow):     ' + self.vol_str(vol_GW))
        report.append('  vol_in   (total):        ' + self.vol_str(vol_in)   + '  (P + SM + MR + GW)')
        report.append('___Output fluxes___:')
        report.append('  vol_ET   (evaporation):  ' + self.vol_str(vol_ET))
        report.append('  vol_IN   (infiltration): ' + self.vol_str(vol_IN))
        report.append('  vol_Rg   (recharge):     ' + self.vol_str(vol_Rg)   + '  (bottom loss)')
        report.append('  vol_Q    (discharge):    ' + self.vol_str(vol_Q)    + '  (main basin outlet)')
        report.append('  vol_edge (boundary):     ' + self.vol_str(vol_edge) + '  (tot. boundary discharge)' )
        report.append('  vol_out  (total):        ' + self.vol_str(vol_out)  + '  (IN + ET + edge_out)')
        report.append('___Net flux___:')
        report.append('  vol_R    (runoff):       ' + self.vol_str(vol_R)    + '  R = (P+SM+MR+GW) - (ET+IN)')
        report.append(' ')

        #-----------------------------------------------------
        # Print area integrals over domain (forms of storage
        #-----------------------------------------------------
        vol_stored_start  = vol_chan_start
        vol_stored_start += vol_soil_start
        vol_stored_start += vol_swe_start
        vol_stored_start += vol_flood_start
        #--------------------------------------
        ## report.append('Total accumulated volumes over entire DEM: (storage)')
        report.append('Total storage volumes:  Area-integrals over the DEM:')
        report.append('___Initial storage volumes___:')
        report.append('vol_soil_start (subsurface): ' + self.vol_str(vol_soil_start)) 
        report.append('vol_chan_start (channels):   ' + self.vol_str(vol_chan_start))
        report.append('vol_flood_start (surface):   ' + self.vol_str(vol_flood_start))
        report.append('vol_swe_start  (snowpack):   ' + self.vol_str(vol_swe_start))
        report.append('vol_start      (total):      ' + self.vol_str(vol_stored_start))
        #------------------------------------------------------------------------------
        vol_stored_final  = vol_chan_final
        vol_stored_final += vol_soil_final
        vol_stored_final += vol_swe_final
        vol_stored_final += vol_flood_final
        #--------------------------------------
        report.append('___Final storage volumes___:')      
        report.append('vol_soil_final (subsurface): ' + self.vol_str(vol_soil_final)) 
        report.append('vol_chan_final (channels):   ' + self.vol_str(vol_chan_final))
        report.append('vol_flood_final (surface):   ' + self.vol_str(vol_flood_final))
        report.append('vol_swe_final  (snowpack):   ' + self.vol_str(vol_swe_final))
        report.append('vol_final      (total):      ' + self.vol_str(vol_stored_final))
        #------------------------------------------------------------------------------
        vol_stored_change = (vol_stored_final - vol_stored_start)
        report.append('vol_change      (total):     ' + self.vol_str(vol_stored_change))
        report.append(' ')

        #---------------------------------------------
        # Print mass balance check (over entire DEM)
        #---------------------------------------------
        # Storage equation (mass conservation):
        # (vol_in - vol_out) = change in vol stored
        #---------------------------------------------
        vol_error = (vol_in - vol_out) - vol_stored_change
        report.append('Mass balance check:')
        report.append('volume in         = ' + self.vol_str(vol_in) )
        report.append('volume out        = ' + self.vol_str(vol_out) )
        report.append('change in storage = ' + self.vol_str(vol_stored_change) )
        if (vol_error > 0):
            msg_prefix = 'volume gain error = '
        else:
            msg_prefix = 'volume loss error = '
        report.append(msg_prefix + self.vol_str(vol_error) )
        report.append('vol_error/ vol_in = ' + str(vol_error / vol_in) )
        report.append(' ')

        #----------------------------------        
        # Print the report to the console
        #----------------------------------
        for line in report:
            print(line)

        #----------------------------------
        # Print the report to a logfile ?
        #----------------------------------
        if (self.WRITE_LOG):
            for line in report:
                self.log_unit.write( line + '\n' )

        self.print_mins_and_maxes( FINAL=True )

        if (self.WRITE_LOG):
            #------------------------------------------------
            # This line is printed to console in finalize()
            #------------------------------------------------
            self.log_unit.write( 'Finished. (' + self.case_prefix + ')\n' )
            self.log_unit.write( '\n' )
      
    #   print_final_report()
    #-------------------------------------------------------------
    def print_mins_and_maxes(self, FINAL=False):

        #-------------------------------
        # New framework method, 2/6/13
        #-------------------------------
        Q_min = self.Q_min
        Q_max = self.Q_max
        u_min = self.u_min
        u_max = self.u_max
        d_min = self.d_min
        d_max = self.d_max
        
        f1 = '(F14.4)'   #(2/12/07)
        
        Qstr = TF_String( Q_min, FORMAT=f1 )
        Qstr = Qstr + ', ' + TF_String( Q_max, FORMAT=f1 )
        #----------------------------------------------------
        ustr = TF_String( u_min, FORMAT=f1 )
        ustr = ustr + ', ' + TF_String( u_max, FORMAT=f1 )
        #----------------------------------------------------
        dstr = TF_String( d_min, FORMAT=f1 )
        dstr = dstr + ', ' + TF_String( d_max, FORMAT=f1 )

        #-----------------------------------------------      
        # Prepare to save report as a list of strings
        #-----------------------------------------------
        report = list()  ############# (NEW: 11/15/16)
        
        if (FINAL):    
            report.append('Final grid mins and maxes:')
        else:    
            report.append('------------------------------------------')
        report.append('Min(Q), Max(Q):   ' + Qstr + ' [m^3/s]')
        report.append('Min(u), Max(u):   ' + ustr + ' [m/s]')
        report.append('Min(d), Max(d):   ' + dstr + ' [m]')
        report.append(' ')

        #----------------------------------        
        # Print the report to the console
        #----------------------------------
        for line in report:
            print(line)

        #----------------------------------
        # Print the report to a logfile ?
        #----------------------------------
        if (self.WRITE_LOG):
            for line in report:
                self.log_unit.write( line + '\n' )
        
    #   print_mins_and_maxes()
    #-------------------------------------------------------------
#     def print_uniform_precip_data(self):
# 
#         ## precip_method = self.pp.method
#         precip_method = 2
#         
#         #---------------------------------------------------
#         # Precip method 1 is special and spatially uniform
#         #---------------------------------------------------
#         if (precip_method == 1):
#             rates = (self.pp.method1_rates * self.mps_to_mmph)    #[m/s] -> [mm/hr]
#             durs  = self.pp.method1_durations      
#             nr    = np.size(rates)
# 
#             if (nr > 1): 
#                 rstr = str(rates[0])
#                 dstr = str(durs[0])
#                 for m in range(1, nr):
#                     rstr += ('  ' + str(rates[m]))
#                     dstr += ('  ' + str(durs[m]))
#             else:
#                 rstr = TF_String(rates)
#                 dstr = TF_String(durs)
#         elif (precip_method == 2) and \
#              (self.pp.rate_type == 0) and \
#              (self.pp.duration_type == 0):
#                 rstr = TF_String(self.pp.rate * self.mps_to_mmph)
#                 dstr = TF_String(self.pp.duration)
#         else:
#             #------------------------------------------------
#             # Could have uniform precip with method 2 where
#             # values are stored in a text file and read in
#             # one by one.  Could read that file here.
#             #------------------------------------------------
#             return
#             
#         #-------------------------------------
#         # This is too verbose in most cases?
#         #------------------------------------- 
#         # print('Uniform precip. rate information: ')
#         # print('Precip. rate:     ' + rstr + ' [mm/hr]' )
#         # print('Duration:         ' + dstr + ' [min]' )
#         # print()
#         
#         #----------------------
#         # Write to log file ?
#         #----------------------
#         if (self.WRITE_LOG):
#             log_unit = self.log_unit
#             log_unit.write("Uniform precip. rate information: \n")
#             log_unit.write('Precip. rate:     ' + rstr + " [mm/hr]\n")
#             log_unit.write('Duration:         ' + dstr + " [min]\n")
#             log_unit.write("\n")
#         
#     #   print_uniform_precip_data()
    #-------------------------------------------------------------
    def print_dimless_number_data(self, basin_length):
 
##        rates     = self.pp.rates
##        durations = self.pp.durations     
##        rates     = self.mp.P
##        durations = self.mp.dt

        ###########################################
        # Updated for new framework (2/5/13),
        # but still need dt@met for durations !!
        ###########################################
        rates     = self.P
        durations = self.dt
        
        nd        = np.size(durations)
        T_peak    = self.T_peak
        log_unit  = self.log_unit
        
        #-------------------------------------
        # Compute some dimensionless numbers
        # that characterize the hydrograph
        #-------------------------------------
        TAU_P = (self.T_peak / durations)
        TAU_F = (self.T_final / durations)
        PSI   = (basin_length / (rates[0] * durations[0] * np.float64(60)))
        
        tpstr = str(TAU_P[0])
        tfstr = str(TAU_F[0])
        for m in range(1, nd):
            tpstr = (tpstr + '  ' + str(TAU_P[m]))
            tfstr = (tfstr + '  ' + str(TAU_F[m]))
        
        #----------------------------------------
        # Make predictions for Q_peak and T_peak
        #-----------------------------------------
        Q_peak_pred = (np.float64(0.2) * rates[0] * (basin_length) ** np.float64(2) / np.float64(3))
        T_peak_pred = (np.float64(3) * durations[0])
        
        if not(self.SILENT):
            print('Dimensionless number information:\n')
            print('T_peak /Duration: ' + tpstr + "\n")
            print('T_final/Duration: ' + tfstr + "\n") 
            print('Psi=L/(R*TD):     ' + str(PSI) + ' [unitless]\n')
            print()
            print('Q_peak predicted: ' + str(Q_peak_pred) + ' [m^3/s]\n')
            print('T_peak predicted: ' + str(T_peak_pred) + ' (min]\n')
            print()
        
        #----------------------
        # Write to log file ?
        #----------------------
        if (self.WRITE_LOG):    
            self.log_unit.write('Dimensionless number information:\n')   
            self.log_unit.write('T_peak /Duration: ' + tpstr + "\n")
            self.log_unit.write('T_final/Duration: ' + tfstr + "\n")
            self.log_unit.write("\n")
            #printf,LU,'Psi=L/(R*TD):     ' + strPSI) + ' [unitless]'
            #printf,LU,' '
            #printf,LU,'Q_peak predicted: ' + str(Q_peak_pred) + ' [m^3/s]'
            #printf,LU,'T_peak predicted: ' + str(T_peak_pred) + ' [min]'
            #printf,LU,' '
                  
    #   print_dimless_number_data()
    #-------------------------------------------------------------
#     def print_mass_balance_report(self):            
#
#     #   print_mass_balance_report()
    #-------------------------------------------------------------

    


