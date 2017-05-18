#!/usr/bin/env python
# -*- coding: utf-8 -*-   

############################################################
import numpy as np
import multiprocessing
from vaspwfc import vaspwfc

############################################################

def nac_from_vaspwfc(waveA, waveB, gamma=True,
                     dt=1.0, ikpt=1, ispin=1):
    '''
    Calculate Nonadiabatic Couplings (NAC) from two WAVECARs
    <psi_i(t)| d/dt |(psi_j(t))> ~=~
                                    (<psi_i(t)|psi_j(t+dt)> -
                                     <psi_j(t)|psi_i(t+dt)>) / (2dt)
    inputs:
        waveA:  path of WAVECAR A
        waveB:  path of WAVECAR B
        gamma:  gamma version wavecar
        dt:     ionic time step, in [fs]          
        ikpt:   which k-point, starting from 1
        ispin:  which spin, 1 or 2

    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    !!!! Note, this method is way too slow than fortran code !!!!
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    '''

    phi_i = vaspwfc(waveA)      # wavecar at t
    phi_j = vaspwfc(waveB)      # wavecar at t + dt

    print 'Calculating NACs between <%s> and <%s>' % (waveA, waveB)

    assert phi_i._nbands == phi_j._nbands, '#bands not match!'
    assert phi_i._nplws[ikpt-1] == phi_j._nplws[ikpt-1], '#nplws not match!'

    nbands = phi_i._nbands
    nacType = np.float if gamma else np.complex
    nacs = np.zeros((nbands, nbands), dtype=nacType)

    for ii in range(nbands):
        for jj in range(ii):
            ib1 = ii + 1
            ib2 = jj + 1

            ci_t   = phi_i.readBandCoeff(ispin, ikpt, ib1, norm=True)
            cj_t   = phi_i.readBandCoeff(ispin, ikpt, ib2, norm=True)

            ci_tdt = phi_j.readBandCoeff(ispin, ikpt, ib1, norm=True)
            cj_tdt = phi_j.readBandCoeff(ispin, ikpt, ib2, norm=True)

            tmp = np.sum(ci_t.conj() * cj_tdt) - np.sum(cj_t.conj() * ci_tdt)

            nacs[ii,jj] = tmp.real if gamma else tmp
            nacs[jj,ii] = -nacs[ii,jj]

    # EnT = (phi_i._bands[ispin-1,ikpt-1,:] + phi_j._bands[ispin-1,ikpt-1,:]) / 2.
    EnT = phi_i._bands[ispin-1,ikpt-1,:]

    # close the wavecar
    phi_i._wfc.close()
    phi_j._wfc.close()

    return EnT, nacs / (2 * dt)

############################################################
# a test
############################################################

if __name__ == '__main__':
    WaveCars = ['./run/%03d/WAVECAR' % (ii + 1) for ii in range(10)]

    ii = 1
    for w1, w2 in zip(WaveCars[:-1], WaveCars[1:]):
        et, nac = nac_from_vaspwfc(w1, w2)

        np.savetxt('run/%03d/eig.txt' % ii, et)
        np.savetxt('run/%03d/nac.txt' % ii, nac)
        
        ii += 1
        if ii > 1: break