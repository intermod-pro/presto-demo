"""Demonstrate simple use of multifrequency lockin measurements

Drive some signals with different detuning from df and measure
the effect of this detuning with a multifrequency sweep.

Normally Lockin.tune can be used to make sure that all frequencies
are tuned to df, but in this example detuning is used to generate
something interesting in loopback.

Connect output port 9 to input port 9, optionally monitor output
with oscilloscope on port 10.
"""

import numpy as np
import matplotlib.pyplot as plt

from presto import lockin
from presto.utils import untwist_downconversion

import utils


# address of the instrument used
ADDRESS, PORT = utils.address_port_from_cli()

# input port used in this measurement
INPUT_PORT = 1

# output ports used in this meeasurement
# A group of frequencies can be output on any number of ports,
# output one for loopback and one for monitoring witn oscilloscope.
OUTPUT_PORTS = [1, 2]

# Use a high df when sweeping to cover a wide frequency range with a
# resonable number of points
df = 100e3

# Measure 60 input frequencies simultaneously
nr_freq = 60

# with 50 iterations each measuring 60 frequencies we cover 300 MHz
# at 100 kHz df
nr_iter = 50

# Do this measurement at 800 MHz + if frequencies
# (upper sideband will be used)
mix_f = 800e6

# Store 1000 pixels for every measurement,
NSTORE = 1000

# and use the last 900 of them for averaging to lower the noise floor
NAVERAGE = 900


fig, ax = plt.subplots(tight_layout=True)
fig.show()

# Create an instance of the Lockin class to access the instrument
# Use the digital mixers for both ADC and DAC, 6.4 GSPS for the
# DAC and 3.2 GSPS for the ADC
with lockin.Lockin(
    ext_ref_clk=False,
    address=ADDRESS,
    port=PORT,
    adc_mode=lockin.AdcMode.Mixed,
    dac_mode=lockin.DacMode.Mixed,
) as lck:
    # Setup output to drive a few tones at different frequencies and
    # with different detuning with respect to df
    N = 6
    fout = np.arange(N) * 50e6 + 25e6
    fdet = np.array([0, 10, 100, 1000, 10000, 50000])

    # Add an output group with N frequencies. This group can be output on
    # any number of ports. More output groups can be added, and each group
    # can target any port set. Multiple groups can be output on the same port.
    output_group = lck.add_output_group(OUTPUT_PORTS, nr_freq=N)
    output_group.set_frequencies(fout + fdet)
    output_group.set_amplitudes(
        [
            1.0 / N,
        ]
        * N
    )
    output_group.set_phases(
        [
            0,
        ]
        * N,
        [
            -np.pi / 2,
        ]
        * N,
    )  # upper sideband

    # the frequencies to measure
    f_raw = np.arange(nr_freq * nr_iter) * df + df
    comb_f, df = lck.tune(f_raw, df)
    comb_a = np.ones(nr_freq) / nr_freq

    # Set up the digital mixers for adc and dac to mix the IF signals
    # with a carrier, the outputs was setup to drive the upper sideband.
    lck.hardware.configure_mixer(mix_f, in_ports=INPUT_PORT, out_ports=OUTPUT_PORTS)

    # Set df used in this measurement
    lck.set_df(df)

    # Create an input group. An input group can only be connected to one
    # input. To measure at multiple inputs, create more groups.
    # The total number of frequencies available is limited, depending one
    # the instrument version used and the number of output frequencies used.
    input_group = lck.add_input_group(INPUT_PORT, nr_freq)

    # run nr_iter measurements
    for i in range(nr_iter):
        # the frequencies measured are updated every iteration
        # the meeasurement is interleaved to make it easier to see
        # effects of drifts during the sweep
        input_group.set_frequencies(comb_f[i::nr_iter])
        lck.apply_settings()

        # During apply_settings all outputs are turned off and on which causes a
        # transient behaviour in the system. For sensitive measurements, give the
        # outputs/inputs some time to stabilize. An option (for lower df measurements)
        # is to capture pixels during this time and see the system stabilize.
        lck.hardware.sleep(0.1, False)

        # Measure a number of pixels
        pixel_dict = lck.get_pixels(NSTORE)
        freq, pixel_i, pixel_q = pixel_dict[INPUT_PORT]
        lsb, hsb = untwist_downconversion(pixel_i, pixel_q)
        # plot the high sideband
        ax.plot(mix_f + freq, 20 * np.log10(np.mean(np.abs(hsb[-NAVERAGE:]), axis=0)), "b.")
        fig.canvas.draw()
        plt.pause(0.1)
        print(f"{i}/{nr_iter}")

    # Set all outputs to 0
    output_group.set_amplitudes(0)
    lck.apply_settings()
