""" Do a bi-dimentional sweep with frequency and amplitude.

Connect Out 1 to In 1.
"""
import matplotlib.pyplot as plt
import numpy as np

from vivace import pulsed

input_port = 1
output_port = 1

ADDRESS = "192.168.42.50"  # set address/hostname of Vivace here
EXT_REF = False  # set to True to use external 10 MHz reference

with pulsed.Pulsed(ext_ref_clk=EXT_REF, address=ADDRESS) as pls:
    ######################################################################
    # Select inputs to store and the duration of each store
    pls.set_store_ports(input_port)
    pls.set_store_duration(2e-6)

    ######################################################################
    # Sinewave generator, template as envelope

    # The template defines the envelope, specify that it is an envelope
    # for carrier generator 1. This template will be scaled
    N = pulsed.MAX_TEMPLATE_LEN
    t = np.arange(N) / pls.sampling_freq
    s = np.hanning(N)
    template_1 = pls.setup_template(output_port, s, envelope=1, use_scale=True)

    # setup a list of frequencies for carrier generator 1
    NFREQ = 8
    f = np.logspace(6, 8, NFREQ)
    p = np.zeros(NFREQ)
    pls.setup_freq_lut(output_ports=output_port,
                       carrier=1,
                       frequencies=f,
                       phases=p)

    # setup a list of scales
    NSCALES = 8
    scales = np.linspace(1.0, .01, 8)
    pls.setup_scale_lut(output_ports=output_port,
                        scales=scales,
                        repeat_count=NFREQ)

    ######################################################################
    # define the sequence of pulses and data stores in time
    # At the end of the time sequence, increment frequency and scale index.
    # Since repeat_count for the scale lut is 8, scale index will actually
    # not increment every time, but only every 8 runs.
    # The frequency will increment every time, and wrap around every 8 runs.
    T = 0.0
    pls.output_pulse(T, template_1)
    pls.store(T)
    T = 5e-6
    pls.next_frequency(T, output_port)
    pls.next_scale(T, output_port)

    # repeat the time sequence 64 times. Run the total sequence 100 times and average the results.
    t_arr, data = pls.perform_measurement(period=10e-6,
                                          repeat_count=NFREQ * NSCALES,
                                          num_averages=100)

fig, ax = plt.subplots(8, 8, sharex=True, sharey=True, tight_layout=True, figsize=(12.8, 9.6))
for freq in range(NFREQ):
    for scale in range(NSCALES):
        ax[freq, scale].plot(1e6 * t_arr, data[scale * NFREQ + freq, 0, :])
        ax[freq, scale].axis('off')
fig.show()
