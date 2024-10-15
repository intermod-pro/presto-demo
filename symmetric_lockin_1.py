# -*- coding: utf-8 -*-
"""Drive a frequency comb with 192 tones equally spaced between 2254 MHz and 2445 MHz. All tones
have same amplitude and random (fixed) phase. Acquire some raw lock-in measurements at 1 MHz rate,
and some mean and standard deviation at 4 kHz rate. Compare the results and plot.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import firwin

from presto.hardware import AdcMode, DacMode
from presto import lockin

import utils

ADDRESS, PORT = utils.address_port_from_cli()

# ******************************
# *** define some parameters ***
# ******************************

INPUT_PORT = 1
OUTPUT_PORT = 1  # can be a list

# 1 MHz, demodulation rate
DF = 1.0 * 1e6
# 2.1 GHz, frequency of numerically-controlled oscillator for up/down-conversion
NCO_FREQ = 0.5 * 1e9
# 192 IF frequencies between 154 MHz and 345 MHz
IF_FREQ_ARR = 250e6 + 1e6 * np.arange(-96, 96)
NR_FREQS = len(IF_FREQ_ARR)
# drive amplitude in full-scale units, i.e. 1.0 is 100%
AMP = 0.707
# equal amplitude on all tones in the comb
AMP_ARR = np.full(NR_FREQS, AMP / NR_FREQS)
# and random phase
PHASE_ARR = 2 * np.pi * np.random.random_sample(NR_FREQS)

# low-pass filter demodulated data with 80 kHz BW
LP_CUTOFF = 80e3
# calculate mean and std in chunks of 250 "raw" measurements
NSUM = 250
# acquire 100 measurements of mean and std
NR_MEAS = 100
# there will be 100 * 250 = 25k "raw" measurements
NR_RAW_MEAS = NR_MEAS * NSUM

# add noise to output to improve linearity at small amplitudes
DITHER = True
# select analog output range (min 2_250 uA, max 40_500 uA)
DAC_CURRENT = 40_500
# select configuration for AD and DA converters
CONVERTER_CONFIGURATION = {
    "adc_mode": AdcMode.Mixed,  # use digital downconversion
    "dac_mode": DacMode.Mixed,  # use digital upconversion
}

# ********************************
# *** Initialize the interface ***
# ********************************

# This will connect to the hardware
with lockin.SymmetricLockin(address=ADDRESS, port=PORT, **CONVERTER_CONFIGURATION) as lck:
    # ***********************************
    # *** Configure hardware features ***
    # ***********************************

    # set digital-step attenuator on the input to 0 dB (max 27 dB)
    lck.hardware.set_adc_attenuation(INPUT_PORT, 0.0)
    # set variable output power on the output
    lck.hardware.set_dac_current(OUTPUT_PORT, DAC_CURRENT)
    # configure up- and down-conversion digital mixers
    lck.hardware.configure_mixer(NCO_FREQ, in_ports=INPUT_PORT, out_ports=OUTPUT_PORT)

    # **********************************
    # *** Configure lock-in features ***
    # **********************************

    # demodulation rate
    lck.set_df(DF)
    # make outputs free-running (because we are not tuning the frequencies)
    lck.set_phase_reset(True)
    # add dithering to outputs
    lck.set_dither(DITHER, OUTPUT_PORT)

    # output a 100ns-wide trigger on digital port 1 every "summing window"
    # i.e. every time a mean and std calculation is performed on a chunk
    # of lock-in packets
    lck.set_trigger_out(2, delay=0.0, width=100e-9)

    # create an input-output group of tones
    sg = lck.add_symmetric_group(INPUT_PORT, OUTPUT_PORT, NR_FREQS)
    # and configure it with frequencies, amplitudes and phase
    sg.set_frequencies(IF_FREQ_ARR).set_amplitudes(AMP_ARR).set_phases(PHASE_ARR)

    # **********************
    # *** Apply settings ***
    # **********************

    # actually upload parameters to the hardware and apply settings
    lck.apply_settings()
    lck.hardware.sleep(10)

    # the frequency comb will be output starting from now!

    # *****************************
    # *** Perform measurements ****
    # *****************************
    fir_coeffs = firwin(43, LP_CUTOFF, fs=lck.get_df())

    # Acquire 25k lock-in packets at 1 MHz rate with ~100 kHz low-pass filter
    _, data_raw = lck.get_pixels(
        n=NR_RAW_MEAS,
        summed=False,  # "raw" lock-in measurements
        fir_coeffs=fir_coeffs,  # low-pass filter
    )[INPUT_PORT]

    # Acquire 100 mean and std measurements at 4 kHz rate = 1 MHz / 250
    _, data_mean, data_std = lck.get_pixels(
        n=NR_MEAS,
        fir_coeffs=fir_coeffs,  # low-pass filter
        summed=True,  # calculate mean and standard deviation...
        nsum=NSUM,  # ...on chunks of 250 lock-in packets each
    )[INPUT_PORT]

    # *******************************************************
    # *** Shut down outputs at the end of the measurement ***
    # *******************************************************
    sg.set_amplitudes(0.0)
    lck.set_trigger_out(0)
    lck.apply_settings()

# Exited `with` block: connection to Presto is now closed

# data_raw, data_mean and data_std are NumPy arrays
# with shape (nr_measurements, nr_frequencies)
assert data_raw.shape == (NR_RAW_MEAS, NR_FREQS)
assert data_mean.shape == (NR_MEAS, NR_FREQS)
assert data_std.shape == (NR_MEAS, NR_FREQS)
# and complex data type for data_raw and data_mean, and real for data_std
assert data_raw.dtype == np.complex64
assert data_mean.dtype == np.complex64
assert data_std.dtype == np.complex64
data_std = np.abs(data_std)

# *****************************
# *** Analyze and plot data ***
# *****************************

# "manually" calculate mean and standard deviation of raw data
# in chunks of 250 measurements
# and compare to mean and std calculated by Presto
manual_mean = np.zeros((NR_MEAS, NR_FREQS), np.complex128)
manual_std = np.zeros((NR_MEAS, NR_FREQS), np.float64)
data2 = np.reshape(data_raw, (NR_MEAS, NSUM, NR_FREQS))
for i in range(NR_MEAS):
    manual_mean[i] = np.mean(data2[i, :, :], axis=0)
    manual_std[i] = np.std(data2[i, :, :], axis=0)

# plot values for 1st frequency only
FREQ_IDX = 0

# time array for plotting
time_arr = np.arange(NR_MEAS) * (NSUM / lck.get_df())

fig1, ax1 = plt.subplots(3, 1, sharex=True, tight_layout=True)
ax11, ax12, ax13 = ax1
ax11.plot(1e3 * time_arr, manual_mean[:, FREQ_IDX].real, label="manual")
ax11.plot(1e3 * time_arr, data_mean[:, FREQ_IDX].real, label="presto")
ax12.plot(1e3 * time_arr, manual_mean[:, FREQ_IDX].imag)
ax12.plot(1e3 * time_arr, data_mean[:, FREQ_IDX].imag)
ax13.plot(1e3 * time_arr, manual_std[:, FREQ_IDX])
ax13.plot(1e3 * time_arr, data_std[:, FREQ_IDX])
ax11.set_ylabel("Mean, real")
ax12.set_ylabel("Mean, imag")
ax13.set_ylabel("Std")
ax13.set_xlabel("Time [ms]")
ax11.legend(ncol=2)
utils.show(plt, fig1)
