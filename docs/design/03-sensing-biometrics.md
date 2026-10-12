# Cover Sensing & Biometrics

## Three sensing options (pick one per kit)
| Option | Tier | Parts | Presence | HR / breathing | Notes |
|---|---|---|---|---|---|
| `load_cells` | 0 | 4 load cells under the bed legs + HX711 (ESPHome) | proven in many DIY builds | plausible at 80 SPS, **unproven here** | No sensor in the bed at all; also gives weight. Both sleepers share one signal. |
| `pneumatic` | 0 | air tube/bladder under the mattress + pressure sensor | yes | principle used by commercial sleep analyzers | Untested under a water mat. One vendor warns its sensor may not work on waterbeds. |
| `piezo_grid` | 1 | 9 piezo strips per side + simultaneous-sampling ADC on the cover sensor board | yes | best expected signal | Needs the Tier 1 cover board (no off-the-shelf multi-channel breakout). Our own layout choice. |

Measuring which option works under a water mat is one of the most valuable contributions right now.

The rest of this page describes the `piezo_grid` reference design.

## Sensors (per side)
| Sensor | Count | Purpose | Notes |
|---|---|---|---|
| Piezo film strips (PVDF, e.g. LDT-type, 30–60 cm long) | 9 in a 3×3 grid under the torso area | ballistocardiography (BCG): heart rate, HRV, breathing, movement | 9 per side matches Pod 6's public sensor count. A grid tolerates sleeping position and partner crossover better than 1–2 strips. |
| Capacitive electrodes (conductive fabric) | 3 | presence, rough position | MCU's built-in touch peripheral or an FDC2214-class sensor |
| NTC on the supply/return lines in the cover | 2 | actual delivered temperature | cross-check against hub sensors |
| Ambient temp/RH (SHT4x) | 1 (shared) | room temperature, dew point | lives in the hub or the cover sensor board |

## Signal chain
- Piezo → charge amplifier / high-impedance buffer → 0.5–25 Hz band-pass → 16-bit ADC.
- Sampling: 500 Hz per channel, all 18 channels simultaneously.
  - 18 ch × 500 Hz × 2 B = 18 kB/s raw. With OPL framing this fits easily on RS-485 at 921600 baud.
  - `SensorBlock` in `obc.protocol` carries 50 samples per frame (10 frames/s/side).
- Cover MCU: RP2040, with PIO driving an external multi-channel ADC (e.g. ADS131M08 ×3) for simultaneous sampling.
- Galvanic: everything is SELV. The RS-485 transceiver is isolated (ISO1410-class) to keep hub ground noise
  out of the piezo front end.

## Algorithms (on the hub SBC, Python/NumPy first, Rust later if needed)
1. **Presence:** capacitance above a baseline plus nonzero piezo RMS. Baseline auto-calibrates while the bed is empty.
2. **Channel selection:** per 30 s window, pick the channels with the best signal quality index (spectral peak
   prominence in the 0.7–2.5 Hz HR band). With 9 channels, roughly one or two always sit under the heart area.
3. **Heart rate:** band-pass 0.7–10 Hz, J-peak detection with template matching, then HR and RMSSD (HRV) from
   inter-beat intervals. Only accept windows without movement.
4. **Breathing:** low-pass < 0.7 Hz, peak counting or autocorrelation.
5. **Movement / restlessness:** broadband energy bursts; also used to gate HR.
6. **Sleep staging (later):** HR, HRV, breathing and movement → classifier. Start rule-based; any ML model
   must be trained on openly licensed data and documented.

Prior art for the BCG part: free-sleep's biometrics (HeartPy-based) for Pod 3–5 shows hobby-grade HR/BR works.
We reimplement, we don't copy.

## Not a medical device
Values are for comfort and automation only. The UI must say so.
