
import numpy as np
import constants as c
import asciidata as AD
import dust
import scipy.special as special # Needed for WD01 equations                                                         
MW_caseA_file = 'Table1.WD.dat'
LMC_avg_file  = 'Table3_LMCavg.WD.dat'
LMC_2_file    = 'Table3_LMC2.WD.dat'
SMC_file      = 'Table3_SMC.WD.dat'

def get_dist_params( R_V=3.1, bc=0.0, type='Graphite', gal='MW' ):
    """
    get_dist_params( 
    R_V [float : 3.1, 4.0, or 5.5]
    bc [float : 0,1,2,3...], 
    type [string : 'Graphite' or 'Silicate],
    gal [string : 'MW','LMC' or 'SMC'] )
    ------------------------------------------
    Returns (alpha, beta, a_t, a_c, C) : Parameters used in WD01 fits
    """
    is_MW = False

    if gal == 'MW':
        table_filename = MW_caseA_file
        is_MW = True
    elif gal == 'SMC':
        table_filename = SMC_file
    elif gal == 'LMC':
        table_filename = LMC_avg_file
    else:
        print 'Error: Galaxy type not recognized'
        return

    table_info = AD.open( table_filename )

    RV_col = table_info[0] # either a float or '--' (LMC/SMC case)
    bc_col = table_info[1].tonumpy()

    # Get index of rows associated with the input R_V value
    # R_V values are not unique, which is why I can't use a dictionary

    if is_MW:
        i_RV     = []
        count_RV = 0
        for val in RV_col:
            if val == R_V:
                i_RV.append(count_RV)
            count_RV += 1
                
        if len(i_RV) == 0:
            print 'Error: R_V value not found'
            return
    else:
        i_RV = range( len(RV_col) )

    # Get the ultimate row index for this R_V, bc combination

    # Note: if there are degenereate bc cases (which shouldn't
    # happen), the index of the last row matching (R_V,bc) will be
    # found

    i_bc     = None
    count_bc = i_RV[0]
    for val in bc_col[i_RV]:
        if val == bc:
            i_bc = count_bc
        count_bc += 1

    if i_bc == None:
        print 'Error: bc value not found'
        return

    ## Now choose the relevant columns based on grain type
    ## Remember: First index is column, second index is row

    if type == 'Graphite':
        alpha = table_info[2][i_bc]
        beta  = table_info[3][i_bc]
        a_t   = table_info[4][i_bc]
        a_c   = table_info[5][i_bc]
        C     = table_info[6][i_bc]

    elif type == 'Silicate':
        alpha = table_info[7][i_bc]
        beta  = table_info[8][i_bc]
        a_t   = table_info[9][i_bc]
        a_c   = 0.1000
        C     = table_info[10][i_bc]

    else:
        print "Error: Grain type not recognized.  Must be 'Graphite' or 'Silicate'."
        return

    result = (alpha, beta, a_t, a_c, C)

    print 'R_V   = ', table_info[0][i_bc]
    print 'bc    = ', table_info[1][i_bc]
    print 'alpha = ', alpha
    print 'beta  = ', beta
    print 'a_t   = ', a_t
    print 'a_c   = ', a_c
    print 'C     = ', C

    return result

def make_WD01_Dustspectrum( R_V=3.1, bc=0.0, rad=dust.adist(), type='Graphite', gal='MW' ):
    """
    make_WD01_Dustspectrum(
    R_V [float],
    bc [float],
    rad [np.array : grain sizes (um)],
    type [string : 'Graphite' or 'Silicate'] )
    gal [string : 'MW', 'LMC', or 'SMC'], 
    -------------------------------------------
    Returns a dust.Dustspectrum object containing a (grain sizes), nd (dn/da), and md (total mass density of dust)
    """

    if type == 'Graphite':
        rho_d = 2.2  #g cm^-3
    elif type == 'Silicate':
        rho_d = 3.8
    else:
        print 'Error: Dust type not recognized'
        return

    dist   = dust.Dustdist( rad=rad, rho=rho_d, p=4 )
    result = dust.Dustspectrum( rad=dist )

    ANGS2MICRON = 1.e-10 * 1.e6
    a    = dist.a
    a_cm = dist.a * c.micron2cm()
    NA   = np.size( a )


    (alpha, beta, a_t, a_c, C) = get_dist_params( R_V=R_V, bc=bc, type=type, gal=gal )

    if type == 'Graphite':

        mc      = 12. * 1.67e-24   # Mass of carbon atom in grams (12 m_p)                                                  
        rho     = 2.24             # g cm^-3                                                                                
        sig     = 0.4
        a_01    = 3.5*ANGS2MICRON      # 3.5 angstroms in units of microns                                                  
        a_01_cm = a_01 * c.micron2cm()
        bc1     = 0.75 * bc * 1.e-5
        B_1     = (3.0/(2*np.pi)**1.5) * np.exp(-4.5 * 0.4**2) / (rho*a_01_cm**3 * 0.4) \
            * bc1 * mc / (1 + special.erf( 3*0.4/np.sqrt(2) + np.log(a_01/3.5e-4)/(0.4*np.sqrt(2)) ) )
        
        a_02    = 30.0*ANGS2MICRON       # 30 angtroms in units of microns                                                  
        a_02_cm = a_02 * c.micron2cm()
        bc2     = 0.25 * bc * 1.e-5
        B_2     = (3.0/(2*np.pi)**1.5) * np.exp(-4.5 * 0.4**2) / (rho*a_02_cm**3 * 0.4) \
            * bc2 * mc / (1 + special.erf( 3*0.4/np.sqrt(2) + np.log(a_02/3.5e-4)/(0.4*np.sqrt(2)) ) )
        
        D       = (B_1/a_cm) * np.exp( -0.5*( np.log(a/a_01)/sig )**2 ) + \
            (B_2/a_cm) * np.exp( -0.5*( np.log(a/a_02)/sig )**2 )

        Case_vsg = np.where( a < 3.5*ANGS2MICRON )
        if np.size(Case_vsg) != 0:
            D[Case_vsg] = 0.0

        Case_g = np.zeros( NA )
        case1g = np.where( np.logical_and(a > 3.5*ANGS2MICRON, a < a_t ) )
        case2g = np.where( a >= a_t )

        if np.size(case1g) != 0:
            Case_g[case1g] = 1.0
        if np.size(case2g) != 0:
            Case_g[case2g] = np.exp( -( (a[case2g]-a_t) / a_c )**3 )

        if beta >= 0:
            F_g  = 1 + beta * a / a_t
        if beta < 0:
            F_g  = 1.0 / (1 - beta * a / a_t)

        Dist_WD01 = D + C/a_cm * (a/a_t)**alpha * F_g * Case_g  #cm^-4 per n_H

    if type == 'Silicate':

        Case_s = np.zeros( NA )
        case1s = np.where( np.logical_and( a > 3.5*ANGS2MICRON, a < a_t ) )
        case2s = np.where( a >= a_t )

        if np.size(case1s) != 0:
            Case_s[case1s] = 1.0
        if np.size(case2s) != 0:
            Case_s[case2s] = np.exp( -( (a[case2s]-a_t)/a_c )**3 )

        F_s    = np.zeros( NA )
        if beta >= 0:
            F_s = 1 + beta * a / a_t
        if beta < 0:
            F_s = 1. / (1 - beta * a / a_t)

        Dist_WD01 = C/a_cm * (a/a_t)**alpha * F_s * Case_s #cm^-4 per n_H

    ## Modify result Dustspectrum so we get a proper WD01 dist!

    mg = 4.0/3.0*np.pi*a_cm**3 * rho_d  # mass of each dust grain
    Md = c.intz( a_cm, Dist_WD01 * mg )

    result.nd = Dist_WD01 * c.micron2cm()  # cm^-3 per um per n_H
    result.md = Md

    return result
