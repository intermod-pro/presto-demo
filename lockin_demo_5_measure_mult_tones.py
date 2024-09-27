from presto import lockin, utils
from presto.hardware import AdcMode, DacMode
from matplotlib import pyplot as plt
import numpy as np


ADDRESS = "192.168.20.20"  # Presto's IP address
EXT_REF_CLK = False  # set to True to lock to an external 10 MHz reference
DAC_CURRENT = 40_500  # sets analog output range, 2250 to 40500

OUTPUT_PORT = 1  # 1 to 16, can be a list

LO_FREQ = 0.24 * 1e9  # Hz, local oscilator frequency, 0 to 10 GHz
IF_FREQS = [100e6, 0, 50e6]  # Hz, intermediate frequency, 0 to 500 MHz
AMPS = [0.2, 0.5, 0.3]  # full-scale units, output amplitude, 0.0 to 1.0
PHASES = [np.pi / 4, 0.0, np.pi / 2]  # rad
PHASES_Q = [3 * np.pi / 4, -np.pi / 2, 0.0]
# rad, +np.pi/2 for low sideband; -np.pi/2 for high sideband
OUTPUT_PORT_2 = 2

LO_FREQ_2 = 2 * 1e9  # Hz
IF_FREQS_2 = [0]  # Hz
AMPS_2 = [1.0]  # full-scale units
PHASES_2 = [0.0]  # rad
PHASES_Q_2 = [0.0]  # rad
DF = 1e3  # Hz, frequency resolution, 1 Hz to 1 MHz

INPUT_PORT = 1
IF_FREQS_IN = [0.0, 50e6]

with lockin.Lockin(
    address=ADDRESS,
    ext_ref_clk=EXT_REF_CLK,
    adc_mode=AdcMode.Mixed,
    dac_mode=DacMode.Mixed,
) as lck:
    lck.hardware.set_adc_attenuation(INPUT_PORT, 0)
    lck.hardware.set_dac_current(OUTPUT_PORT, DAC_CURRENT)
    lck.hardware.set_inv_sinc(OUTPUT_PORT, 0)
    lck.hardware.configure_mixer(LO_FREQ, out_ports=OUTPUT_PORT, in_ports=INPUT_PORT)
    lck.hardware.set_dac_current(OUTPUT_PORT_2, DAC_CURRENT)
    lck.hardware.set_inv_sinc(OUTPUT_PORT_2, 0)
    lck.hardware.configure_mixer(LO_FREQ_2, out_ports=OUTPUT_PORT_2)

    lck.set_df(DF)

    og = lck.add_output_group(OUTPUT_PORT, len(IF_FREQS))  # port, number of frequencies
    og.set_frequencies(IF_FREQS)  # IF frequency
    og.set_amplitudes(AMPS)  # amplitude
    og.set_phases(PHASES, PHASES_Q)  # phase on I and Q port of the digtal IQ mixer

    og_2 = lck.add_output_group(OUTPUT_PORT_2, len(IF_FREQS_2))
    og_2.set_frequencies(IF_FREQS_2)
    og_2.set_amplitudes(AMPS_2)
    og_2.set_phases(PHASES_2, PHASES_Q_2)

    ig = lck.add_input_group(INPUT_PORT, len(IF_FREQS_IN))  # port, number of frequencies
    ig.set_frequencies(IF_FREQS_IN)

    lck.apply_settings()
    pixel_dict = lck.get_pixels(100)

    og.set_amplitudes(0)
    og_2.set_amplitudes(0)
    lck.apply_settings()

freq, pixel_i, pixel_q = pixel_dict[INPUT_PORT]
lsb, hsb = utils.untwist_downconversion(pixel_i, pixel_q)
fig, ax = plt.subplots(tight_layout=True, figsize=(6, 2.5))
ax.plot((LO_FREQ + np.array(IF_FREQS_IN)) * 1e-6, np.mean(np.real(hsb), axis=0), "C0o", label="re")
ax.plot((LO_FREQ + np.array(IF_FREQS_IN)) * 1e-6, np.mean(np.imag(hsb), axis=0), "C1o", label="im")
ax.legend()
ax.set_xlabel("Frequency (MHz)")
ax.set_ylabel("Amplitude (FS)")
plt.show()
