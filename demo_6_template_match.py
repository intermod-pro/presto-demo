"""Template matching demo.

Output a series of pulses with varying amplitude and phase.
Load input templates to implement IQ demodulation by means of template matching.
Plot the results in the IQ plane.

Connect Out 9 to In 9.
"""

import matplotlib.pyplot as plt
import numpy as np

from presto import pulsed

import utils

INPUT_PORT = 1
OUTPUT_PORT = 1
freq = 100e6  # Hz

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
    # Note: storing is used to look at the raw time data, it's not necessarily
    # linked to template matching.
    pls.setup_store(INPUT_PORT, 2e-6)

    ######################################################################
    # Sinewave generator, template as envelope

    # The template defines the envelope, specify that it is an envelope
    # for carrier generator 1.
    # This template will be scaled by the final output scaler.
    N = pulsed.MAX_TEMPLATE_LEN
    t = np.arange(N) / pls.get_fs("dac")
    s = np.hanning(N)  # use the Hanning window as envelope shape
    template_1 = pls.setup_template(
        output_port=OUTPUT_PORT,
        group=0,
        template=s,
        envelope=True,
    )

    # setup a list of frequencies for carrier generator 1
    # Use the same frequency in all entries, but rotate phase
    NFREQ = pulsed.MAX_LUT_ENTRIES
    f = freq * np.ones(NFREQ)
    p = np.linspace(0, 4 * 2 * np.pi, NFREQ)
    pls.setup_freq_lut(
        output_ports=OUTPUT_PORT,
        group=0,
        frequencies=f,
        phases=p,
    )

    # setup a list of scales, decrease the scale with every iteration
    NSCALES = NFREQ  # use same number of steps as for the frequency
    scales = np.linspace(1.0, 0.01, NSCALES)
    pls.setup_scale_lut(
        output_ports=OUTPUT_PORT,
        group=0,
        scales=scales,
    )

    ######################################################################
    # Match templates, use a sine and a cosine at the same frequency as
    # the generated pulse to get a point in the I/Q-plane
    # Length of the match is half the length of the generated pulse
    t = np.arange(pulsed.MAX_TEMPLATE_LEN // 2) / pls.get_fs("adc")
    tc = np.cos(2 * np.pi * freq * t)
    ts = -np.sin(2 * np.pi * freq * t)
    match_pair = pls.setup_template_matching_pair(INPUT_PORT, tc, ts)

    ######################################################################
    # define the sequence of pulses and data stores in time
    # At the end of the time sequence, increment frequency and scale index.
    T = 0.0
    pls.reset_phase(T, OUTPUT_PORT)
    pls.output_pulse(T, template_1)
    pls.store(T)

    # Perform a template match near the center of the output pulse
    T = 0.25e-6 + 210e-9
    pls.match(T, match_pair)

    # after the pulse, jump to next frequency and next scale.
    # Both are set to increment every time.
    T = 5e-6
    pls.next_frequency(T, OUTPUT_PORT)
    pls.next_scale(T, OUTPUT_PORT)

    # Repeat the time sequence over the entire lookup tables.
    # Both frequency and scale are incremented every time
    pls.run(period=10e-6, repeat_count=NFREQ, num_averages=1)
    t_arr, data = pls.get_store_data()

    match_data = pls.get_template_matching_data(match_pair)

# Plot a few of the time traces
fig1, ax1 = plt.subplots(8, sharex=True, sharey=True, tight_layout=True, figsize=(12.8, 9.6))
for i in range(8):
    ax1[i].plot(1e6 * t_arr, data[i * 64, 0, :])
    ax1[i].axis("off")
utils.show(plt, fig1)

# Plot template match data as points in the I/Q plane
fig2, ax2 = plt.subplots(tight_layout=True)
ax2.axhline(0, c="tab:gray", alpha=0.25)
ax2.axvline(0, c="tab:gray", alpha=0.25)
ax2.scatter(
    match_data[0] / len(tc),  # I quadrature
    match_data[1] / len(ts),  # Q quadrature
    c=np.linspace(0, 1, pulsed.MAX_LUT_ENTRIES),
    cmap="viridis",
)
ax2.set_aspect("equal")
ax2.set_xlabel("I quadrature")
ax2.set_ylabel("Q quadrature")
ax2.grid()
utils.show(plt, fig2)
