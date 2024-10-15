"""Create a long template by concatenating multiple shorter templates.

Also demonstrate the convenience method setup_long_drive.

Connect Out 9 to In 9 and Out 10 to In 10.
"""

import matplotlib.pyplot as plt
import numpy as np

from presto import pulsed

import utils

ADDRESS, PORT = utils.address_port_from_cli()
EXT_REF = False  # set to True to use external 10 MHz reference

INPUT_PORTS = [1, 2]
OUTPUT_PORTS = [1, 2]

with pulsed.Pulsed(
    ext_ref_clk=EXT_REF,
    address=ADDRESS,
    port=PORT,
    adc_mode=pulsed.AdcMode.Direct,
    dac_mode=pulsed.DacMode.Direct,
) as pls:
    ######################################################################
    # Select inputs to store and the duration of each store
    pls.setup_store(INPUT_PORTS, 9.5e-6)

    ######################################################################
    # create a long pulse using multiple templates on first port
    N = 14000  # longer than pulsed.MAX_TEMPLATE_LEN = 4088!
    t = np.arange(N) / pls.get_fs("dac")
    freq = 55e6
    data = np.sin(2 * np.pi * freq * t) * np.hanning(N)
    port = OUTPUT_PORTS[0]
    # setup_template will split the template into 4 segments
    template_1 = pls.setup_template(port, 0, data)
    pls.setup_scale_lut(port, 0, 1.0)

    ######################################################################
    # create a long pulse from sections using long_drive
    # See demo_4 for setup_freq_lut and carrier
    port = OUTPUT_PORTS[1]
    group = 0
    freq = 55e6
    phase = 0.0
    pls.setup_freq_lut(port, group, freq, phase)  # see demo_4
    pls.setup_scale_lut(port, group, 1.0)

    # a pulse with the sampe lenght, with 1 us rise time and 1 us fall time
    duration = N / pls.get_fs("dac")
    template_2 = pls.setup_long_drive(
        output_port=port,
        group=group,
        duration=duration,
        amplitude=1.0,
        rise_time=1.0e-6,
        fall_time=1.0e-6,
    )

    ######################################################################
    # define the sequence of pulses and data stores in time
    # output the long pulse and store the beginning of the pulses
    T = 0.0
    pls.select_frequency(T, 0, port, group)  # see demo_4
    pls.output_pulse(T, template_1)
    pls.output_pulse(T, template_2)
    pls.store(T)

    pls.run(period=100e-6, repeat_count=1, num_averages=1)
    t_arr, data = pls.get_store_data()

fig, ax = plt.subplots(2, sharex=True, sharey=True, tight_layout=True)
ax[0].plot(1e6 * t_arr, data[0, 0, :], label=f"port {OUTPUT_PORTS[0]}")
ax[0].legend()
ax[0].grid()
ax[1].plot(1e6 * t_arr, data[0, 1, :], label=f"port {OUTPUT_PORTS[1]}")
ax[1].legend()
ax[1].grid()
ax[1].set_xlabel("Time [us]")
utils.show(plt, fig)
