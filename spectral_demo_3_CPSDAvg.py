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

IN_PORTS = [IN_PORT_1, IN_PORT_2]
OUT_PORTS = [OUT_PORT_1, OUT_PORT_2]

LO_FREQ = 1.5e9


with Spectral(nr_inputs=len(IN_PORTS), address=ADDRESS, port=PORT, ext_ref_clk=False) as spec:
    # configure 1.5 GHz carrier for up- and down-conversion
    spec.hardware.configure_mixer(1.5e9, in_ports=IN_PORTS, out_ports=OUT_PORTS)

    # 1 MHz resolution in FFT
    period = spec.tune_period(1.0e-6)

    # generate random data and output from first port
    def random_complex(ns):
        rng = np.random.default_rng()
        real = 2.0 * rng.random(ns) - 1.0
        imag = 2.0 * rng.random(ns) - 1.0
        return real + 1j * imag

    duration = 10 * period
    nr_samples = int(round(duration * spec.get_fs("dac")))
    data1 = 0.1 * random_complex(nr_samples)
    spec.output_waveform(OUT_PORTS[0], data1)

    # output same data on second port,
    # but delayed by 100 samples (100 ns)
    data2 = np.roll(data1, 100)
    spec.output_waveform(OUT_PORTS[1], data2)

    spec.setup_delay(pre_delay=300e-9, start_delay=0.0, end_delay=0.0)

    # measure cross power spectral density (CPSD) data
    # averaged 1000 times
    res = spec.measure(SpecMode.Cpsd, IN_PORTS, 1000, period)

x, y = res.to_correlation()
fig, ax = plt.subplots(tight_layout=True, figsize=(6, 2.5))
ax.plot(1e9 * x, np.real(y[0]), "C0", label="real")
ax.plot(1e9 * x, np.imag(y[0]), "C1", label="imag")
ax.set_xlabel("Time lag [ns]")
ax.set_ylabel("Correlation [arb. units]")
ax.grid()
plt.legend()
utils.show(plt, fig)
