"""Do a bi-dimentional sweep with frequency and amplitude.

Connect Out 9 to In 9.
"""

import matplotlib.pyplot as plt
import numpy as np

from presto import pulsed

import utils

INPUT_PORT = 1
OUTPUT_PORT = 1

ADDRESS, PORT = utils.address_port_from_cli()
EXT_REF = False  # set to True to use external 10 MHz reference

with pulsed.Pulsed(
    ext_ref_clk=EXT_REF,
    address=ADDRESS,
    adc_mode=pulsed.AdcMode.Direct,
    dac_mode=pulsed.DacMode.Direct,
) as pls:
    ######################################################################
    # Select inputs to store and the duration of each store
    pls.setup_store(INPUT_PORT, 2e-6)

    ######################################################################
    # Sinewave generator, template as envelope

    # The template defines the envelope, specify that it is an envelope
    # for carrier generator 1. This template will be scaled
    N = pulsed.MAX_TEMPLATE_LEN
    t = np.arange(N) / pls.get_fs("dac")
    s = np.hanning(N)
    template_1 = pls.setup_template(OUTPUT_PORT, 0, s, envelope=True)

    # setup a list of frequencies for carrier generator 1
    NFREQ = 4
    f = np.logspace(6, 8, NFREQ)
    p = np.zeros(NFREQ)
    pls.setup_freq_lut(output_ports=OUTPUT_PORT, group=0, frequencies=f, phases=p, axis=-1)

    # setup a list of scales
    NSCALES = 5
    scales = np.logspace(0, -1, NSCALES)
    pls.setup_scale_lut(output_ports=OUTPUT_PORT, group=0, scales=scales, axis=-2)

    ######################################################################
    # define the sequence of pulses and data stores in time
    # At the end of the time sequence, increment frequency and scale index.
    # Since `axis` for the scale lut is -2 (outer loop), scale index will actually
    # not increment every time, but only every 8 (NFREQ) runs.
    # The frequency will increment every time, and wrap around every 8 (NFREQ) runs.
    T = 0.0
    pls.reset_phase(T, OUTPUT_PORT)
    pls.output_pulse(T, template_1)
    pls.store(T)
    T += 5e-6
    pls.next_frequency(T, OUTPUT_PORT)
    pls.next_scale(T, OUTPUT_PORT)
    T += 5e-6

    # repeat the time sequence 64 times.
    # Run the total sequence 100 times and average the results.
    pls.run(period=T, repeat_count=(NSCALES, NFREQ), num_averages=100)
    t_arr, data = pls.get_store_data()

fig, ax = plt.subplots(
    NFREQ,
    NSCALES,
    sharex=True,
    sharey=True,
    tight_layout=True,
    figsize=(12.8, 9.6),
)
for freq in range(NFREQ):
    for scale in range(NSCALES):
        ax[freq, scale].plot(1e6 * t_arr, data[scale * NFREQ + freq, 0, :])
        ax[freq, scale].axis("off")
utils.show(plt, fig)
