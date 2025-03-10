from presto import lockin
from presto.hardware import AdcMode, DacMode

import utils

# get IP address as argument from the command line
# you can also set it explicitly, e.g.:
# ADDRESS = "192.168.20.02"
# PORT = None  # default setting
ADDRESS, PORT = utils.address_port_from_cli()

EXT_REF_CLK = False  # set to True to lock to an external 10 MHz reference
DAC_CURRENT = 40_500  # sets analog output range, 2250 to 40500

OUTPUT_PORT = 1  # 1 to 16, can be a list

LO_FREQ = 0.24 * 1e9  # Hz, local oscilator frequency, 0 to 10 GHz
IF_FREQS = [0]  # Hz, intermediate frequency, 0 to 500 MHz
AMPS = [1.0]  # full-scale units, output amplitude, 0.0 to 1.0
PHASES = [0.0]  # rad
PHASES_Q = [0.0]  # rad
DF = 1e3  # Hz, frequency resolution, 1 Hz to 1 MHz

with lockin.Lockin(
    address=ADDRESS,
    port=PORT,
    ext_ref_clk=EXT_REF_CLK,
    adc_mode=AdcMode.Mixed,
    dac_mode=DacMode.Mixed,
) as lck:
    lck.hardware.set_dac_current(OUTPUT_PORT, DAC_CURRENT)
    lck.hardware.set_inv_sinc(OUTPUT_PORT, 0)
    lck.hardware.configure_mixer(LO_FREQ, out_ports=OUTPUT_PORT)

    lck.set_df(DF)

    og = lck.add_output_group(OUTPUT_PORT, len(IF_FREQS))  # port, number of frequencies
    og.set_frequencies(IF_FREQS)  # IF frequency
    og.set_amplitudes(AMPS)  # amplitude
    og.set_phases(PHASES, PHASES_Q)  # phase on I and Q port of the digtal IQ mixer

    lck.apply_settings()
