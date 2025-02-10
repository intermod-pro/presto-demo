import matplotlib.pyplot as plt
import numpy as np

from presto.spectral import Spectral, SpecMode

import utils

# get IP address as argument from the command line
# you can also set it explicitly, e.g.:
# ADDRESS = "192.168.20.02"
# PORT = None  # default setting
ADDRESS, PORT = utils.address_port_from_cli()

IN_PORT_1 = 1
IN_PORT_2 = 2
OUT_PORT_1 = 1
OUT_PORT_2 = 2

LO_FREQ = 1.5e9

with Spectral(nr_inputs=2, address=ADDRESS, port=PORT, ext_ref_clk=False) as spec:
    spec.hardware.set_dac_current([OUT_PORT_1, OUT_PORT_2], 40_500)  # μA, 2250 to 40500
    spec.hardware.set_inv_sinc([OUT_PORT_1, OUT_PORT_2], 0)
    spec.hardware.set_adc_attenuation([IN_PORT_1, IN_PORT_2], 0.0)

    spec.hardware.configure_mixer(
        freq=LO_FREQ,
        in_ports=[IN_PORT_1, IN_PORT_2],
        out_ports=[OUT_PORT_1, OUT_PORT_2],
    )

    period = spec.tune_period(1.0e-6)

    f1 = 0.0
    a1 = 0.5
    p1 = 0.0
    spec.output_multicos(OUT_PORT_1, period, f1, a1, p1)

    f2 = [-110.0e6, +120.0e6]
    a2 = [0.1, 0.2]
    p2 = [0.0, 0.0]
    spec.output_multicos(OUT_PORT_2, period, f2, a2, p2)

    spec.setup_delay(pre_delay=300e-9, start_delay=0.0, end_delay=0.0)

    res = spec.measure(SpecMode.FftAvg, [IN_PORT_1, IN_PORT_2], 1000, period)

# frequencies in MHz
x = np.fft.fftshift(res.freqs) / 1.0e6
# data in dBFS
y0 = np.fft.fftshift(res.to_db()[0])
y1 = np.fft.fftshift(res.to_db()[1])

fig, ax = plt.subplots(tight_layout=True, figsize=(6, 2.5))
ax.plot(x, y0, "C0", label="port %i" % (IN_PORT_1))
ax.plot(x, y1, "C1", label="port %i" % (IN_PORT_2))
ax.set_xlabel("Offset frequency [MHz]")
ax.set_ylabel("Amplitude [dBFS]")
ax.set_title("Center frequency 1.5 GHz")
ax.grid()
ax.legend()
utils.show(plt, fig)
