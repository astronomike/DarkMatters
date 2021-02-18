#cython: language_level=3
from scipy.integrate import quad
from scipy.optimize import newton,bisect
import numpy as np
try:
    from wimp_tools import tools#,environments
except:
    import wimp_tools.tools as tools

def rho_crit(z,cos_env):
    """
    Critical density for FRLW universe given by cos_env
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [Msol Mpc^-3]
    """
    return 1e9*2.7755e-2/hubble_z(z,cos_env)**2

def omega_m(z,cos_env):
    """
    Matter density parameter at z
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    return 1.0/(1.0 + (1.0-cos_env.w_m)/cos_env.w_m/(1+z)**(3))

def delta_c(z,cos_env):
    """
    Density ratio of pertubation at collapse in FRLW universe at z
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    x = 1.0 - omega_m(z,cos_env)
    return (18.0*np.pi**2 - 82.0*x - 39.0*x**2)/omega_m(z,cos_env)

def cvir(M,z,cos_env):
    """
    Halo concentration fitting function
        ---------------------------
        Parameters
        ---------------------------
        M       - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    return 9.0/(1.0+z)*(M/1.3e13*cos_env.h)**(-0.13)

def cvir_p12_param(M,z,cos_env):
    """
    Parameteric halo concentration from Sanchez-Conde & Prada 2013
        ---------------------------
        Parameters
        ---------------------------
        M       - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    c = np.array([37.5153,-1.5093,1.636e-2,3.66e-4,-2.89237e-5,5.32e-7])
    cv = 0.0
    for i in range(0,len(c)):
        cv += c[i]*np.log(M*cos_env.h)**i
    return cv

def cvir_p12(M,z,cosmo):
    """
    Halo concentration from Sanchez-Conde & Prada 2013
        ---------------------------
        Parameters
        ---------------------------
        M       - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    a = 1.0/(1+z)
    x = (cosmo.w_l/cosmo.w_m)**(1.0/3)*a
    y = x/a #this ensures b1 and b0 are unity at z = 0
    b0 = cmin(x,y)
    b1 = smin(x,y)
    sigma_p = b1*sigma_param(M,z,cosmo)
    A = 2.881;b=1.257;c=1.022;d=0.060
    csig = A*((sigma_p/b)**c + 1)*np.exp(d/sigma_p**2)
    return b0*csig

def sigma_param(M,z,cosmo):
    """
    Overdensity sigma from Sanchez-Conde & Prada 2013
        ---------------------------
        Parameters
        ---------------------------
        M       - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    a = 1.0/(1+z)
    y = (M*cosmo.h/1.0e12)**(-1)
    return glinear(z,cosmo)*16.9*y**(0.41)/(1+1.102*y**(0.2)+6.22*y**(0.333))

def smin(x,y):
    """
    Ratio function for cvir_p12
        ---------------------------
        Parameters
        ---------------------------
        x - Required : (float)
        y - Required : (float)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    s0 = 1.047;s1 = 1.646;beta = 7.386;x1 = 0.526 #fitting parameters
    return (s0 + (s1-s0)*(np.arctan(beta*(x-x1))/np.pi+0.5))/(s0 + (s1-s0)*(np.arctan(beta*(y-x1))/np.pi+0.5))

def cmin(x,y):
    """
    Ratio function for cvir_p12
        ---------------------------
        Parameters
        ---------------------------
        x - Required : (float)
        y - Required : (float)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    c0 = 3.681;c1 = 5.033;alpha = 6.948;x0 = 0.424 #fitting parameters
    return (c0 + (c1-c0)*(np.arctan(alpha*(x-x0))/np.pi+0.5))/(c0 + (c1-c0)*(np.arctan(alpha*(y-x0))/np.pi+0.5))

def rvir(M,z,cos_env):
    """
    Virial radius
        ---------------------------
        Parameters
        ---------------------------
        M       - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [Mpc]
    """
    return (0.75*M/(np.pi*delta_c(z,cos_env)*rho_crit(z,cos_env)))**(1.0/3.0) #in Mpc

def mvir_from_rvir(r,z,cos_env):
    """
    Virial mass
        ---------------------------
        Parameters
        ---------------------------
        r       - Required : halo virial radius [Mpc] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [Msol]
    """
    return 4*np.pi/3.0*delta_c(z,cos_env)*rho_crit(z,cos_env)*r**3

def rvir_ps(M,z,cos_env):
    """
    Virial radius in Press-Schechter
        ---------------------------
        Parameters
        ---------------------------
        M       - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [Mpc]
    """
    return (0.75*M/(np.pi*omega_m(z,cos_env)*rho_crit(z,cos_env)))**(1.0/3.0) #in Mpc

def rcore(M,z,cos_env):
    """
    Halo scale radius
        ---------------------------
        Parameters
        ---------------------------
        M       - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [Mpc]
    """
    return rvir(M,z,cos_env)/cvir_munoz(M,z,cos_env)

def rhos(cv,z,cos_env):
    """
    Characteristic halo density for NFW halo relative to critical density
        ---------------------------
        Parameters
        ---------------------------
        cv      - Required : halo virial concentration (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    return delta_c(z,cos_env)/3.0*cv**3/(np.log(cv+1.0) - cv/(1.0+cv))

def hubble_z(z,cos_env):
    """
    1.0/Hubble parameter at z
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [km^-1 s Mpc]
    """
    H0 = 100.0
    w_k = 1 - cos_env.w_m - cos_env.w_l
    return (H0*cos_env.h*np.sqrt(cos_env.w_m*(1.0+z)**3+w_k*(1+z)**2+cos_env.w_l))**(-1)

def dist_co_move(z,cos_env):
    """
    Co-moving distance to z 
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [Mpc]
    """
    c = 2.99792458e5 #km s^-1
    w_k = 1 - cos_env.w_m - cos_env.w_l
    dc = quad(hubble_z,0,z,args=(cos_env))[0]*c
    dh = c/(100*cos_env.h)
    if(w_k == 0.0):
        dcm = dc
    elif(w_k > 0.0):
        dcm = dh/np.sqrt(w_k)*np.sinh(np.sqrt(w_k)*dc/dh)
    elif(w_k < 0.0):
        dcm = dh/np.sqrt(-w_k)*np.sinh(np.sqrt(-w_k)*dc/dh)
    return dcm

def dist_luminosity(z,cos_env):
    """
    Luminosity distance to z
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [Mpc]
    """
    return (1.0+z)*dist_co_move(z,cos_env)

def dist_angular(z,cos_env):
    """
    Angular diameter distance to z
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [Mpc]
    """
    return dist_co_move(z,cos_env)/(1.0+z)

def pspec(k,z,cos_env):
    """
    Matter perturbation power spectrum
        ---------------------------
        Parameters
        ---------------------------
        k       - Required : perturbation wavenumber [Mpc^-1] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [?]
    """
    q = k/(omega_m(z,cos_env)*cos_env.h**2)
    return k*(np.log(1+2.34*q)/(2.34*q)/(1 + 3.89*q + (16.1*q)**2 + (5.46*q)**3+(6.71*q)**4)**0.25)**2

def window(x):
    """
    Top-hat window function in Fourier space
        ---------------------------
        Parameters
        ---------------------------
        x - Required : (float)
        ---------------------------
        Output
        ---------------------------
        float [Mpc]
    """
    return 3*(np.sin(x) - x*np.cos(x))/x**3

def sigma_l(r,l,rc,rmin,z,cos_env):
    #z is redshift, h is H(0) in 100 Mpc s^-1 km^-1, w_m is matter density parameter at z = 0
    """
    Average excess mass with a sphere of radius r
        ---------------------------
        Parameters
        ---------------------------
        r       - Required : sphere radius [Mpc] (float) 
        l       - Required : moment of the distribution
        rc      - Required : cutoff radius [Mpc] (float) 
        rmin    - Required : minimum radius [Mpc] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [?]
    """
    n = 101
    kmax = 1.0/rmin
    kcut = 1.0/rc
    kmin = 1.0e-8*kmax
    kset = np.zeros(n,dtype=float)
    kint = np.zeros(n,dtype=float)
    kset = np.logspace(np.log10(kmin),np.log10(kmax),num=n)
    kint = 0.5*kset**(2*(1+l))*pspec(kset,z,cos_env)*window(kset*r)**2*np.exp(-kset/kcut)/np.pi**2
    return tools.Integrate(kint,kset)

def sigma_l_pl(r,l,rc,rmin,z,cos_env):
    """
    Average excess mass with a sphere of radius r - power-law matter spectrum only
        ---------------------------
        Parameters
        ---------------------------
        r       - Required : sphere radius [Mpc] (float) 
        l       - Required : moment of the distribution
        rc      - Required : cutoff radius [Mpc] (float) 
        rmin    - Required : minimum radius [Mpc] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [?]
    """
    n = 1001
    pn = 1
    kmax = 1.0/rmin
    kcut = 1.0/rc
    kmin = 1.0e-12*kmax
    kint = np.zeros(n,dtype=float)
    kset = np.logspace(np.log10(kmin),np.log10(kmax),num=n)
    kint = 0.5*kset**(2*(1+l)+pn)*window(kset*r)**2/np.pi**2#*np.exp(-kset/kcut)
    return tools.Integrate(kint,kset)

def glinear(z,cos_env):
    """
    Linear growth factor at z
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    g = 1.0
    if(cos_env.w_l == 0.0 and cos_env.w_m == 1.0):
        g = (1+z)**(-1)
    elif(cos_env.w_m < 1.0 and cos_env.w_l == 0.0):
        x0 = (1.0/cos_env.w_m - 1)
        x = x0/(1+z)
        Ax = 1 + 3/x + 3*np.sqrt(1+x)/x**1.5*np.log(np.sqrt(1+x)-np.sqrt(x))
        Ax0 = 1 + 3/x0 + 3*np.sqrt(1+x0)/x0**1.5*np.log(np.sqrt(1+x0)-np.sqrt(x0))
        g = Ax/Ax0
    elif(cos_env.w_l > 0 and cos_env.w_l == 1.0 - cos_env.w_m):
        om = omega_m(z,cos_env)
        om0 = omega_m(0.0,cos_env)
        ol = 1.0 - om
        ol0 = 1.0 - om0
        #this approximation very closely matches true expression commented out below
        N = 2.5*om0*(om0**(4.0/7) - ol0 + (1 + 0.5*om0)*(1 + 1.0/70*ol0))**(-1)
        g = 2.5*om*(om**(4.0/7) - ol + (1 + 0.5*om)*(1 + 1.0/70*ol))**(-1)/(1 + z)/N
        #x0 = (2*(1.0/w_m - 1))**(1.0/3)
        #x = x0/(1+z)
        #xset = linspace(0,x,num=101)
        #x0set = linspace(0,x0,num=101)
        #aset = (xset/(xset**3+2))**1.5
        #a0set = (x0set/(x0set**3+2))**1.5
        #Ax = np.sqrt(x**3 + 2)/x**1.5*tools.Integrate(aset,xset)
        #Ax0 = np.sqrt(x0**3 + 2)/x0**1.5*tools.Integrate(a0set,x0set)
        #ga = Ax/Ax0
    return g

def omega_m_lahav(z,cos_env):
    """
    Matter density parameter at z from Lahav?
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    return cos_env.w_m*(cos_env.w_m*(1+z)**3-(cos_env.w_m + cos_env.w_l-1.0)*(1+z)**2+cos_env.w_l)**(-2)*(1+z)**3

def growth(z,cos_env):
    """
    Parametrised growth factor at z
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    g = 1.0
    om = omega_m_lahav(z,cos_env)
    return om**0.6 + 1.0/70*(1-0.5*om*(1+om))

def density_contrast(z,sigma,cosmo):
    """
    Difference between density contrast of sigma perturbation and critical value
        ---------------------------
        Parameters
        ---------------------------
        z       - Required : redshift (float)
        sigma   - Required : excess mass in spherical perturbation (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    dsc = 1.686
    return glinear(z,cosmo)*sigma - dsc

def get_zc_secant(Mvir,cosmo):
    """
    Find collapse redshift (density contrast = 1.686) for Mvir mass perturbation (secant method)
        ---------------------------
        Parameters
        ---------------------------
        M       - Required : halo virial mass [Msol] (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    f = 0.015
    m = f*Mvir
    r8 = 8/cosmo.h
    z0 = 0.0
    rcut = (3*1.0e-6/(4*np.pi*omega_m(z0,cosmo)*rho_crit(z0,cosmo)))**(1.0/3)
    r = (3*m/(4*np.pi*omega_m(z0,cosmo)*rho_crit(z0,cosmo)))**(1.0/3)
    sig8 = sigma_l(r8,0,rcut,rcut,z0,cosmo)/0.897**2
    sig = np.sqrt(sigma_l(r,0,rcut,rcut,z0,cosmo)/sig8)
    return newton(density_contrast,1.0,args=(sig,cosmo))

def get_zc(Mvir,cos_env):
    """
    Find collapse redshift (density contrast = 1.686) for Mvir mass perturbation (bisection method)
        ---------------------------
        Parameters
        ---------------------------
        M       - Required : halo virial mass [Msol] (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    f = 0.015
    k = 0
    zret = -1
    dsc = 1.686
    tol = 1.0e-2
    m = f*Mvir
    z1 = 0.0
    z2 = 100.0
    z3 = (z1+z2)*0.5
    r8 = 8/cos_env.h
    z0 = 0.0
    rcut = (3*1.0e-6/(4*np.pi*omega_m(z0,cos_env)*rho_crit(z0,cos_env)))**(1.0/3)
    r = (3*m/(4*np.pi*omega_m(z0,cos_env)*rho_crit(z0,cos_env)))**(1.0/3)
    sig8 = sigma_l(r8,0,rcut,rcut,z0,cos_env)/0.897**2
    sig = np.sqrt(sigma_l(r,0,rcut,rcut,z0,cos_env)/sig8)
    d3 = glinear(z3,cos_env)*sig - dsc
    d2 = glinear(z2,cos_env)*sig - dsc
    d1 = glinear(z1,cos_env)*sig - dsc
#    print d1,d2,d3
    if((abs(d1) <= tol) or (abs(d2) <= tol) or (abs(d3) <= tol)):
        if(abs(d1) <= tol):
            zret = z1
        if(abs(d2) <= tol):
            zret = z2
        if(abs(d3) <= tol):
            zret = z3
    else:
        found = False
        while(not found and k < 51):
            z3 = (z1+z2)*0.5

            d1 = glinear(z1,cos_env)*sig - dsc
            d2 = glinear(z2,cos_env)*sig - dsc
            d3 = glinear(z3,cos_env)*sig - dsc
            if(abs(d1) <= tol):
                zret = z1
                found  = True
            elif(abs(d2) <= tol):
                zret = z2
                found  = True
            elif(abs(d3) <= tol):
                zret = z3
                found  = True
            elif(d3/d1 < 0):
                z2 = z3
            elif(d3/d2 < 0):
                z1 = z3
            k += 1
    return zret

def cvir_sig(Mvir,z,cos_env):
    """
    Halo concentration from Bullock 2001
        ---------------------------
        Parameters
        ---------------------------
        Mvir    - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    return 4*(1+get_zc_secant(Mvir,cos_env))/(1+z)

def cvir_cpu(Mvir,z,cos_env):
    """
    Halo concentration used in Colafrancesco, Profumo, & Ullio 2006
        ---------------------------
        Parameters
        ---------------------------
        Mvir    - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    zc = get_zc_secant(Mvir,cos_env)
    return (delta_c(zc,cos_env)*omega_m(z,cos_env)/delta_c(z,cos_env)/omega_m(zc,cos_env))**(1.0/3)*(1+zc)/(1+z)

def cvir_munoz(Mvir,z,cos_env):
    """
    Halo concentration from Munoz
        ---------------------------
        Parameters
        ---------------------------
        Mvir    - Required : halo virial mass [Msol] (float)
        z       - Required : redshift (float)
        cos_env - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float []
    """
    w = 0.029
    m = 0.097
    alpha = -110.001
    beta = 2469.72
    gamma = 16.885
    a = w*z - m
    b = alpha/(z+gamma) + beta/(z+gamma)**2
    logc = a*np.log10(Mvir*cos_env.h) + b
    return 10**(logc)

def tLookback(z,cosmo):
    """
    Lookback time to z
        ---------------------------
        Parameters
        ---------------------------
        z     - Required : redshift (float)
        cosmo - Required : cosmology environment (cosmology_env)
        ---------------------------
        Output
        ---------------------------
        float [s]
    """
    zset = np.logspace(-3,np.log10(z),num=1000)
    inverseEset = hubble_z(zset,cosmo)*cosmo.h*100.0
    mpcToKm = 3.086e19
    tH = 1.0/cosmo.h*1e-2*mpcToKm #in s
    return tools.Integrate(1.0/(1+zset)*inverseEset,zset)*tH
