"""
DarkMatters module for checking input dictionaries are usuable 
"""
import os,yaml
import numpy as np
from astropy import constants
from genericpath import isdir

from .input import get_spectral_data
from .output import fatal_error,warning
from .astro_cosmo import astrophysics,cosmology

def check_cosmology(cosmo_dict):
    """
    Checks the properties of a cosmology dictionary

    Arguments
    ---------------------------
    cosmo_dict : dictionary
        Cosmology information

    Returns
    ---------------------------
    cosmo_dict : dictionary
        Cosmology information in compliance with DarkMatters requirements, code will exit if this cannot be achieved
    """
    if not type(cosmo_dict) is dict:
        fatal_error("dictionary_checks.check_cosmology() must be passed a dictionary as its argument")
    if not 'omega_m' in cosmo_dict.keys() and not 'omega_l' in cosmo_dict.keys():
        cosmo_dict['omega_m'] = 0.3089
        cosmo_dict['omega_l'] = 1 - cosmo_dict['omega_m']
    elif not 'omega_m' in cosmo_dict.keys():
        cosmo_dict['omega_m'] = 1 - cosmo_dict['omega_l']
    elif not 'omega_l' in cosmo_dict.keys():
        cosmo_dict['omega_l'] = 1 - cosmo_dict['omega_m']
    if not 'cvir_mode' in cosmo_dict.keys():
        cosmo_dict['cvir_mode'] = 'p12'
    cvir_modes = ['p12','munoz_2010','bullock_2001','cpu_2006']
    if not cosmo_dict['cvir_mode'] in cvir_modes:
        fatal_error(f"cosmo_data['cvir_mode'] = {cosmo_dict['cvir_mode']} is not valid, use one of {cvir_modes}")
    if not 'h' in cosmo_dict.keys():
        cosmo_dict['h'] = 0.6774
    return cosmo_dict

def check_magnetic(mag_dict):
    """
    Checks the properties of a magnetic field dictionary

    Arguments
    ---------------------------
    mag_dict : dictionary
        Magnetic field information

    Returns
    ---------------------------
    mag_dict : dictionary
        Magnetic Field information in compliance with DarkMatters requirements, code will exit if this cannot be achieved
    """
    if not type(mag_dict) is dict:
        fatal_error("dictionary_checks.check_magnetic() must be passed a dictionary as its argument")
    in_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"config/mag_field_profiles.yaml"),"r")
    profile_dict = yaml.load(in_file,Loader=yaml.SafeLoader)
    in_file.close()
    if 'mag_field_func' in mag_dict.keys() and mag_dict['mag_func_lock']: #No functionality implemented yet
        mag_dict['mag_profile'] = "custom"
        return mag_dict
    if not 'mag_profile' in mag_dict.keys():
        mag_dict['mag_profile'] = "flat"
    if not mag_dict['mag_profile'] in profile_dict.keys():
        fatal_error(f"mag_data variable mag_profile is required to be one of {profile_dict.keys()}")
    need_vars = profile_dict[mag_dict['mag_profile']]
    for var in need_vars:
        if not var in mag_dict.keys():
            fatal_error(f"mag_data variable {var} required for magnetic field profile {mag_dict['mag_profile']}")
        if not np.isscalar(mag_dict[var]):
            fatal_error(f"mag_data property {var} must be a scalar")
    if not mag_dict['mag_func_lock']:
        mag_dict['mag_field_func'] = astrophysics.magnetic_field_builder(mag_dict)
    if mag_dict['mag_field_func'] is None:
        fatal_error(f"No mag_field_func recipe for profile {mag_dict['mag_profile']} found in astrophysics.magnetic_field_builder()")
    return mag_dict

def check_halo(halo_dict,cosmo_dict,minimal=False):
    """
    Checks the properties of a halo dictionary

    Arguments
    ---------------------------
    halo_dict : dictionary
        Halo properties
    cosmo_dict : dictionary
        Cosmology information, must have been checked via check_cosmology

    Returns
    ---------------------------
    halo_dict : dictionary
        Halo information in compliance with DarkMatters requirements, code will exit if this cannot be achieved
    """
    if not type(halo_dict) is dict:
        fatal_error("dictionary_checks.check_halo() must be passed a dictionary as its argument")
    if ((not 'halo_z' in halo_dict.keys()) or halo_dict['halo_z'] == 0.0) and not 'halo_distance' in halo_dict.keys():
        fatal_error("Either halo_distance must be specified or halo_z must be non-zero")
    elif not 'halo_z' in halo_dict.keys():
        halo_dict['halo_z'] = 0.0
    elif not 'halo_distance' in halo_dict.keys():
        halo_dict['halo_distance'] = cosmology.dist_luminosity(halo_dict['halo_z'],cosmo_dict)
    if minimal:
        return halo_dict
    in_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"config/halo_density_profiles.yaml"),"r")
    halo_params = yaml.load(in_file,Loader=yaml.SafeLoader)
    in_file.close()
    def rho_norm(halo_dict,cosmo_dict):
        if (not "halo_norm" in halo_dict.keys()) and ("halo_norm_relative" in halo_dict.keys()):
            halo_dict['halo_norm'] = halo_dict['halo_norm_relative']*cosmology.rho_crit(halo_dict['halo_z'],cosmo_dict)
        elif ("halo_norm" in halo_dict.keys()) and (not "halo_norm_relative" in halo_dict.keys()):
            halo_dict['halo_norm_relative'] = halo_dict['halo_norm']/cosmology.rho_crit(halo_dict['halo_z'],cosmo_dict)
        else:
            halo_dict['halo_norm'] = halo_dict['halo_mvir']/astrophysics.rho_virial_int(halo_dict)
            halo_dict['halo_norm_relative'] = halo_dict['halo_norm']/cosmology.rho_crit(halo_dict['halo_z'],cosmo_dict)
        return halo_dict

    if not 'halo_weights' in halo_dict.keys():
        halo_dict['halo_weights'] = "rho"
    if not 'halo_profile' in halo_dict.keys():
        fatal_error("halo variable halo_profile is required for non J/D-factor calculations")
    
    var_set1 = ["halo_norm","halo_mvir","halo_rvir","halo_norm_relative"]
    var_set2 = ["halo_cvir","halo_scale"]
    if ((not len(set(var_set1).intersection(halo_dict.keys())) > 0) or (not len(set(var_set2).intersection(halo_dict.keys())) > 0)) and not ("halo_rvir" in halo_dict.keys() or "halo_mvir" in halo_dict.keys()):
        fatal_error(f"Halo specification requires 1 halo variable from {var_set1} and 1 from {var_set2}")
    else:
        if halo_dict['halo_profile'] not in halo_params.keys():
            fatal_error(f"Halo specification requires halo_profile from: {halo_params.keys()}")
        else:
            for x in halo_params[halo_dict['halo_profile']]:
                if not x == "none":
                    if not x in halo_dict.keys():
                        fatal_error(f"halo_profile {halo_dict['halo_profile']} requires property {x} be set")
        if halo_dict["halo_profile"] == "burkert":
            #rescale to reflect where dlnrho/dlnr = -2 (required as cvir = rvir/r_{-2})
            #isothermal, nfw, einasto all have rs = r_{-2}
            scale_mod = 1.5214
        elif halo_dict["halo_profile"] == "gnfw":
            scale_mod = 2.0 - halo_dict['halo_index']
        else:
            scale_mod = 1.0
        rs_info = "halo_scale" in halo_dict.keys() 
        rho_info = "halo_norm" in halo_dict.keys() or "halo_norm_relative" in halo_dict.keys()
        rvir_info = "halo_rvir" in halo_dict.keys() or "halo_mvir" in halo_dict.keys()
        if  rs_info and rho_info:
            if not "halo_norm_relative" in halo_dict.keys():
                halo_dict['halo_norm_relative'] = halo_dict['halo_norm']/cosmology.rho_crit(halo_dict['halo_z'],cosmo_dict)
            elif not "halo_norm" in halo_dict.keys():
                halo_dict['halo_norm'] = halo_dict['halo_norm_relative']*cosmology.rho_crit(halo_dict['halo_z'],cosmo_dict)
            if (not "halo_mvir" in halo_dict.keys()) and ("halo_rvir" in halo_dict.keys()):
                halo_dict['halo_mvir'] = halo_dict['halo_norm']*astrophysics.rho_volume_int(halo_dict)
            elif ("halo_mvir" in halo_dict.keys()) and (not "halo_rvir" in halo_dict.keys()):
                halo_dict['halo_rvir'] = cosmology.rvir_from_mvir(halo_dict['halo_mvir'],halo_dict['halo_z'],cosmo_dict)
            elif (not "halo_mvir" in halo_dict.keys()) and (not "halo_rvir" in halo_dict.keys()):
                halo_dict['halo_rvir']= astrophysics.rvir_from_rho(halo_dict,cosmo_dict)
                halo_dict['halo_mvir'] = cosmology.mvir_from_rvir(halo_dict['halo_rvir'],halo_dict['halo_z'],cosmo_dict)
            if not "halo_cvir" in halo_dict.keys():
                halo_dict['halo_cvir'] = halo_dict['halo_rvir']/halo_dict['halo_scale']/scale_mod
        elif rvir_info and rs_info:
            if not 'halo_rvir' in halo_dict.keys():
                halo_dict['halo_rvir'] = cosmology.rvir_from_mvir(halo_dict['halo_mvir'],halo_dict['halo_z'],cosmo_dict)
            if not 'halo_cvir' in halo_dict.keys():
                halo_dict['halo_cvir'] = halo_dict['halo_rvir']/halo_dict['halo_scale']/scale_mod
            if not 'halo_mvir' in halo_dict.keys():
                halo_dict['halo_mvir'] = cosmology.mvir_from_rvir(halo_dict['halo_rvir'],halo_dict['halo_z'],cosmo_dict)
            else:
                if not 'halo_rvir' in halo_dict.keys():
                    halo_dict['halo_rvir'] = cosmology.rvir_from_mvir(halo_dict['halo_mvir'],halo_dict['halo_z'],cosmo_dict)
                if not 'halo_cvir' in halo_dict.keys():
                    halo_dict['halo_cvir'] = halo_dict['halo_rvir']/halo_dict['halo_scale']/scale_mod
            halo_dict = rho_norm(halo_dict,cosmo_dict)
        elif rvir_info and 'halo_cvir' in halo_dict.keys():
            if not 'halo_mvir' in halo_dict.keys():
                halo_dict['halo_mvir'] = cosmology.mvir_from_rvir(halo_dict['halo_rvir'],halo_dict['halo_z'],cosmo_dict)
            if not 'halo_rvir' in halo_dict.keys():
                halo_dict['halo_rvir'] = cosmology.rvir_from_mvir(halo_dict['halo_mvir'],halo_dict['halo_z'],cosmo_dict)
            if not 'halo_scale' in halo_dict.keys():
                halo_dict['halo_scale'] = halo_dict['halo_rvir']/halo_dict['halo_cvir']/scale_mod
            halo_dict = rho_norm(halo_dict,cosmo_dict)
        elif rvir_info:
            if not 'halo_mvir' in halo_dict.keys():
                halo_dict['halo_mvir'] = cosmology.mvir_from_rvir(halo_dict['halo_rvir'],halo_dict['halo_z'],cosmo_dict)
            if not 'halo_rvir' in halo_dict.keys():
                halo_dict['halo_rvir'] = cosmology.rvir_from_mvir(halo_dict['halo_mvir'],halo_dict['halo_z'],cosmo_dict)
            halo_dict['halo_cvir'] = cosmology.cvir(halo_dict['halo_mvir'],halo_dict['halo_z'],cosmo_dict)
            halo_dict['halo_scale'] = halo_dict['halo_rvir']/halo_dict['halo_cvir']/scale_mod
            halo_dict = rho_norm(halo_dict,cosmo_dict)
        else:
            fatal_error(f"halo_data is underspecified by {halo_dict}")
    halo_dict['halo_density_func'] = astrophysics.halo_density_builder(halo_dict)
    if not "green_averaging_scale" in halo_dict.keys():
        halo_dict["green_averaging_scale"] = halo_dict['halo_scale']
    if halo_dict['halo_density_func'] is None:
        fatal_error(f"No halo_density_func recipe for profile {halo_dict['halo_profile']} found in astrophysics.halo_density_builder()")
    return halo_dict

def check_gas(gas_dict):
    """
    Checks the properties of a gas dictionary

    Arguments
    ---------------------------
    gas_dict : dictionary
        Gas properties

    Returns
    ---------------------------
    gas_dict : dictionary
        Gas information in compliance with DarkMatters requirements, code will exit if this cannot be achieved
    """
    if not type(gas_dict) is dict:
        fatal_error("dictionary_checks.check_gas() must be passed a dictionary as its argument")
    in_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"config/gas_density_profiles.yaml"),"r")
    gas_params = yaml.load(in_file,Loader=yaml.SafeLoader)
    in_file.close()
    if not 'gas_profile' in gas_dict.keys():
        gas_dict['gas_profile'] = "flat"
    else:
        need_vars = gas_params[gas_dict['gas_profile']]
        for var in need_vars:
            if not var in gas_dict.keys():
                print(f"gas_data variable {var} is required for magnetic field profile {gas_dict['gas_profile']}")
                fatal_error("gas_data underspecified")
    gas_dict['gas_density_func'] = astrophysics.gas_density_builder(gas_dict)
    if gas_dict['gas_density_func'] is None:
        fatal_error(f"No gas_density_func recipe for profile {gas_dict['gas_profile']} found in astrophysics.gas_density_builder()")
    return gas_dict   

def check_calculation(calc_dict):
    """
    Checks the properties of a calculation dictionary

    Arguments
    ---------------------------
    calc_dict : dictionary
        Calculation information

    Returns
    ---------------------------
    calc_dict : dictionary 
        Calculation information in compliance with DarkMatters requirements, code will exit if this cannot be achieved
    """
    if not type(calc_dict) is dict:
        fatal_error("dictionary_checks.check_calculation() must be passed a dictionary as its argument")
    calc_params = {'all_electron_modes':["adi-python","green-python","green-c"],'all_modes':["jflux","flux","sb"],"all_freqs":["radio","all","gamma","pgamma","sgamma","neutrinos_e","neutrinos_mu","neutrinos_tau"]}
    if not 'm_wimp' in calc_dict.keys():
        fatal_error("calc_dict requires the variable m_wimp be set")
    if not 'calc_mode' in calc_dict.keys() or (not calc_dict['calc_mode'] in calc_params['all_modes']):
        fatal_error(f"calc_dict requires the variable calc_mode with options: {calc_params['all_modes']}")
    if not 'freq_mode' in calc_dict.keys() or (not calc_dict['freq_mode'] in calc_params['all_freqs']):
        fatal_error(f"calc_dict requires the variable freq_mode with options: {calc_params['all_freqs']}")
    if not 'electron_mode' in calc_dict.keys():
        calc_dict['electron_mode'] = "adi-python"  
    elif calc_dict['electron_mode'] not in calc_params['all_electron_modes']:
        fatal_error(f"electron_mode can only take the values: green-python, green-c, or adi-python. Your value of {calc_dict['electron_mode']} is invalid")
    if not 'out_cgs' in calc_dict.keys():
        calc_dict['out_cgs'] = False
    if not 'f_sample_values' in calc_dict.keys(): 
        if not 'f_sample_limits' in calc_dict.keys():
            fatal_error("calc_dict requires one of the following variables: f_sample_limits, giving the minimum and maximum frequencies to be studied OR f_sample_values, an array of explicitly sampled frequencies")
        if not 'f_sample_num' in calc_dict.keys():
            calc_dict['f_sample_num'] = int((np.log10(calc_dict['f_sample_limits'][1]) - np.log10(calc_dict['f_sample_limits'][0]))/5)
        if not 'f_sample_spacing' in calc_dict.keys():
            calc_dict['f_sample_spacing'] = "log"
        if calc_dict['f_sample_spacing'] == "lin":
            calc_dict['f_sample_values'] = np.linspace(calc_dict['f_sample_limits'][0],calc_dict['f_sample_limits'][1],num=calc_dict['f_sample_num'])
        else:
            calc_dict['f_sample_values'] = np.logspace(np.log10(calc_dict['f_sample_limits'][0]),np.log10(calc_dict['f_sample_limits'][1]),num=calc_dict['f_sample_num'])
    else:
        calc_dict['f_sample_num'] = len(calc_dict['f_sample_values'])
        calc_dict['f_sample_limits'] = [calc_dict['f_sample_values'][0],calc_dict['f_sample_values'][-1]]
        calc_dict['f_sample_spacing'] = "custom"

    if not 'e_sample_num' in calc_dict.keys():
        if 'green' in calc_dict['electron_mode']:
            calc_dict['e_sample_num'] = 50
        else:
            calc_dict['e_sample_num'] = 80
    if not 'r_sample_num' in calc_dict.keys():
        if 'green' in calc_dict['electron_mode']:
            calc_dict['r_sample_num'] = 50
        else:
            calc_dict['r_sample_num'] = 80
    if not 'log10_r_sample_min_factor' in calc_dict.keys():
        calc_dict['log10_r_sample_min_factor'] = -2
    if not 'e_sample_min' in calc_dict.keys():
        calc_dict['e_sample_min'] = (constants.m_e*constants.c**2).to("GeV").value #GeV

    if calc_dict['calc_mode'] in ["flux"]:
        if (not 'calc_rmax_integrate' in calc_dict.keys()) and (not 'calc_angmax_integrate' in calc_dict.keys()):
            fatal_error(f"calc_dict requires one of the variables calc_rmax_integrate or calc_angmax_integrate for the selected mode: {calc_dict['calc_mode']}")
        elif ('calc_rmax_integrate' in calc_dict.keys()) and ('calc_angmax_integrate' in calc_dict.keys()):
            fatal_error(f"calc_dict requires ONLY one of the variables calc_rmax_integrate or calc_angmax_integrate for the selected mode: {calc_dict['calc_mode']}")

    if not calc_dict['calc_mode'] == "jflux":
        if "green" in calc_dict['electron_mode']: 
            if not 'thread_number' in calc_dict.keys():
                calc_dict['thread_number'] = 4
            if not "image_number" in calc_dict.keys():
                calc_dict['image_number'] = 30
            if (not 'electron_exec_file' in calc_dict.keys()):
                calc_dict['electron_exec_file'] = os.path.join(os.path.dirname(os.path.realpath(__file__)),"emissions/electron.x")
            if (not 'r_green_sample_num' in calc_dict.keys()):
                calc_dict['r_green_sample_num'] = 61
            if calc_dict['r_green_sample_num'] < 61:
                fatal_error("r_green_sample_num cannot be set below 61 without incurring errors")
            if (not 'e_green_sample_num' in calc_dict.keys()):
                calc_dict['e_green_sample_num'] = 401
            if calc_dict['e_green_sample_num'] < 201:
                fatal_error("e_green_sample_num cannot be set below 201 without incurring substantial errors, recommended value is 401")
            if calc_dict['e_green_sample_num'] < 401:
                warning(f"e_green_sample_num recommended value is 401 to minimize errors, you are curently using {calc_dict['e_green_sample_num']}")
            if (calc_dict['r_green_sample_num']-1)%4 != 0:
                fatal_error(f"r_green_sample_num - 1 must be divisible by 4, you provided {calc_dict['r_green_sample_num']}")
            if (calc_dict['e_green_sample_num']-1)%4 != 0:
                fatal_error(f"e_green_sample_num - 1 must be divisible by 4, you provided {calc_dict['e_green_sample_num']}")
        elif calc_dict['electron_mode'] == "adi-python":
            if not "adi_delta_ti" in calc_dict.keys():
                calc_dict['adi_delta_ti'] = 1e9 
            if not "adi_delta_t_reduction" in calc_dict.keys():
                calc_dict['adi_delta_t_reduction'] = 0.5 
            if not "adi_max_steps" in calc_dict.keys():
                calc_dict['adi_max_steps'] = 100
            if not "adi_delta_t_constant" in calc_dict.keys():
                calc_dict['adi_delta_t_constant'] = False 
            if not "adi_bench_mark_mode" in calc_dict.keys():
                calc_dict['adi_bench_mark_mode'] = False  
            if not 'adi_delta_t_min' in calc_dict.keys():
                calc_dict['adi_delta_t_min'] = 1e1  
    else:
        if not calc_dict['freq_mode'] in ["pgamma","neutrinos_mu","neutrinos_e","neutrinos_tau"]:
            fatal_error("calc_data freq_mode parameter can only be pgamma, or neutrinos_x (x= e, mu, or tau) for calc_mode jflux")
    green_only_params = ["r_green_sample_num","e_green_sample_num","thread_number","image_number"]
    adi_only_params = ["adi_delta_t_reduction","adi_delta_ti","adi_max_steps","adi_delta_t_constant","adi_bench_mark_mode","adi_delta_t_min"]
    if "green" in calc_dict['electron_mode']:
        for p in adi_only_params:
            if p in calc_dict.keys():
                calc_dict.pop(p)
    else:
        for p in green_only_params:
            if p in calc_dict.keys():
                calc_dict.pop(p)
    return calc_dict 

def check_particles(part_dict,calc_dict):
    """
    Checks the properties of a particle physics dictionary

    Arguments
    ---------------------------
    part_dict : dictionary
        Particle physics information
    calc_dict : dictionary
        Calculation information, must have been check_calculation'd first

    Returns
    ---------------------------
    part_dict : dictionary 
        Particle physics in compliance with DarkMatters requirements, code will exit if this cannot be achieved
    """
    if not type(calc_dict) is dict or not type(part_dict) is dict:
        fatal_error("dictionary_checks.check_particles() must be passed a dictionaries as its argument")
    if not 'part_model' in part_dict.keys():
        fatal_error("part_dict requires a part_model value")
    if not 'em_model' in part_dict.keys():
        part_dict['em_model'] = "annihilation"
    elif not part_dict['em_model'] in ["annihilation","decay"]:
        fatal_error("em_model must be set to either annihilation or decay")
    if not 'decay_input' in part_dict.keys():
        part_dict['decay_input'] = False
    if not 'spectrum_directory' in part_dict.keys():
        part_dict['spectrum_directory'] = os.path.join(os.path.dirname(os.path.realpath(__file__)),"particle_physics")
    if not isdir(part_dict['spectrum_directory']):
        warning(f"part_data['spectrum_directory'] = {part_dict['spectrum_directory']} is not a valid folder, using default instead")
        part_dict['spectrum_directory'] = os.path.join(os.path.dirname(os.path.realpath(__file__)),"particle_physics")
    spec_set = []
    if "neutrinos" in calc_dict['freq_mode']:
        spec_set.append(calc_dict['freq_mode'])
    if calc_dict['freq_mode'] in ["gamma","pgamma","sgamma","all"]:
        spec_set.append("gammas")
    if calc_dict['freq_mode'] in ['sgamma',"radio","all","gamma"]:
        spec_set.append("positrons")
    part_dict['d_ndx_interp'] = get_spectral_data(part_dict['spectrum_directory'],part_dict['part_model'],spec_set,mode=part_dict["em_model"])
    if 'cross_section' in part_dict.keys() and 'decay_rate' in part_dict.keys():
        fatal_error("You cannot have both a cross_section and decay_rate set for the particle physics")
    elif not 'cross_section' in part_dict.keys() and not 'decay_rate' in part_dict.keys():
        if part_dict['em_model'] == "annihilation":
            part_dict['cross_section'] = 1e-26
        else:
            part_dict['decay_rate'] = 1e-26
    return part_dict

def check_diffusion(diff_dict):
    """
    Checks the properties of a diffusion dictionary

    Arguments
    ---------------------------
    diff_dict : dictionary
        Diffusion information

    Returns
    ---------------------------
    diff_dict : dictionary
        Diffusion information in compliance with DarkMatters requirements, code will exit if this cannot be achieved
    """
    if not type(diff_dict) is dict:
        fatal_error("dictionary_checks.check_diffusion() must be passed a dictionary as its argument")
    if not 'loss_only' in diff_dict.keys():
        diff_dict['loss_only'] = False
    if not 'photon_density' in diff_dict.keys():
        diff_dict['photon_density'] = 0.0
    if not 'photon_temp' in diff_dict.keys():
        diff_dict['photon_temp'] = 2.7255
    if not 'diff_rmax' in diff_dict.keys():
        diff_dict['diff_rmax'] = "2*Rvir"
    if diff_dict['loss_only']:
        diff_dict['diff_constant'] = 0.0
    else:
        if not 'diff_constant' in diff_dict.keys():
            diff_dict['diff_constant'] = 3e28
        if not 'diff_index' in diff_dict.keys():
            diff_dict['diff_index'] = 1.0/3
    return diff_dict