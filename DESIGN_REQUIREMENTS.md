# Design requirements and model traceability

These are **project design targets**, not published Hoover Dam operating
requirements. They came from the associated classroom design work and must be
validated with a teacher, project sponsor or cited engineering source before
being presented as external requirements.

| Proposed target or limit | Current simulator support | Evidence produced | Work still required |
| --- | --- | --- | --- |
| Divert at least 70% of targeted sediment | Partial | Removed volume and initial grid volume | Define the target region and diversion mechanism |
| Deliver at least 90% of diverted sediment to an outlet | Not modeled | None | Model transport, blockage and outlet capture |
| Lose less than 5% of process water | Not modeled | None | Add pump, flow and water-balance models |
| Increase turbidity by no more than 25 NTU after 5 minutes | Not modeled | None | Add plume physics and a calibrated turbidity sensor model |
| Reject particles larger than 2 mm | Not modeled | None | Add a particle-size distribution and separator model |
| Operate in water deeper than 40 cm | Not modeled | None | Add bathymetry, water surface and vehicle clearance |
| Test for more than 30 minutes | Partial | IR-SIM simulation time | Add a formal endurance scenario and failure criteria |
| Act on deposits thicker than 10 cm | Supported | Sediment thickness grid and noisy samples | Add a configurable action threshold to route planning |

## What can be claimed now

The software can compare navigation routes, sampled map coverage, travel
distance and simulated volume removed from a synthetic sediment field. It also
shows that the IR-SIM robot can follow the generated routes.

It cannot currently demonstrate sediment diversion efficiency, outlet delivery,
water conservation, turbidity compliance, particle rejection or suitability
for Hoover Dam. Those require additional physical models and real calibration
data.

## Recommended next engineering iteration

1. Import a cited bathymetric or sediment-survey raster instead of using only a
   synthetic field.
2. Add a target-region mask and a configurable 0.10 m action threshold.
3. Track material through removal, transport and outlet-capture states so the
   70% and 90% targets become measurable.
4. Add water balance and turbidity-plume models before evaluating the 5% and
   25 NTU targets.
5. Build a 30-minute endurance test with sensor dropout, actuator degradation
   and route-recovery cases.