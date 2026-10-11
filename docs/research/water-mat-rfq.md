# RFQ template: water mat (copy, fill the brackets, send)

Draft only. Nothing here has been sent. Replace [brackets]. Attach our channel drawing (`water-mat-drawing.pdf`, to be made) when available.

---

**Subject:** RFQ - RF/HF-welded TPU water circulation mat, 2 samples / 10 / 100 pcs

Hello [name],

We are [name], an open-source hardware project (Open Bed Climate) building a water-based bed cooling and heating system. We are looking for a manufacturer of a flexible water-circulation mat that lies on a mattress under a sheet. We would like a quote and your advice on a small first series. Please treat this as an early-stage request; we are happy to adapt the design to what your equipment can weld.

**1. Product**

- Flat water mat, active area about 90 x 200 cm (alternatively tiles of about 45 x 100 cm or 90 x 100 cm, joined outside the mat with tubing; tell us which your press can do best).
- Two ports on one short edge: supply and return, for 10 mm barbed fittings (tubing 13 mm OD / 10 mm ID).
- Water, 13-43 C, normal temperature 18-35 C. Optionally 20-30% propylene glycol/corrosion inhibitor.
- Flow 0.4-1 L/min, working pressure 0.5 bar maximum, pressure drop at 0.5 L/min target <= 5 kPa.
- Used every night, a person up to 120 kg lies on it, under a sheet. Must not kink or pinch shut; quiet (no crackling); no sharp ports.
- Our design: parallel channels or a weld-dot field, channel width 6-10 mm, weld width 6 mm or more. We will supply the weld drawing. We do not want to copy any existing commercial pad.

**2. Material**

- TPU, preferably polyether-based, plasticiser-free, Shore A 85-92.
- Either two plies of 0.20-0.35 mm film, or TPU-coated knit/woven nylon or polyester (200-400 g/m2), coating on the water side.
- Fittings: PP or nylon barbs (no aluminium).
- Please propose your standard material and tell us what you can supply with documentation.

**3. Quantities**

| Lot | Quantity |
|---|---|
| Samples | 2 pcs (for testing before any series) |
| First series | 10 pcs |
| Later volume | 100 pcs (and ask for a 500 pcs price if you have one) |

**4. Please tell us**

1. Can you make this, and what is the largest area you can weld in one press stroke? Can you weld in indexed sections for a 90 x 200 cm mat?
2. Do you accept orders of 2 and 10 pieces? What is your **MOQ** for samples and for a first series?
3. **Tooling:** price and ownership of the weld die(s), who builds them, who keeps them. Can we move the die to another manufacturer later?
4. **Prices** (EUR or USD, state Incoterm) for 2 / 10 / 100 / 500 pcs, with tooling shown separately.
5. **Lead time** for samples, for the first series, and for repeat orders.
6. **Testing you do on every unit:** pressure/leak test (we need 1.0 bar for 5 minutes), and any burst, peel or weld-strength tests on sample lots. Please send a typical test report.
7. **Certifications and documents:** ISO 9001 / ISO 13485, ISO 10993-5/-10 for the film, OEKO-TEX Standard 100, REACH SVHC declaration, RoHS/phthalate-free statement for the film and ports.
8. Material suppliers and datasheets (TPU grade, thickness, hydrolysis resistance, operating temperature).
9. Can you add a welded-on or sewn-on spacer/cover fabric or a removable washable cover? If not, which partner can?
10. Is your price for the sample paid or credited against a later series?
11. Shipping: weight and flat-pack size per mat, destination [Germany / EU].
12. Anything in the drawing that you would change so it welds reliably.

**5. Our test plan (so you know what to expect)**

Each sample goes through a 24 h leak test at 0.5 bar and 1.0 bar for 5 min, burst test at 0.1 bar/min to failure (target >= 2 bar), flow resistance at 0.5 and 1.0 L/min with and without a 75 kg load, a thermal camera check for uniform temperature, noise, 5000 fold cycles, and 14 days wet at 40 C followed by a weld peel test. We will share results with you if we find a weld problem.

**6. Open source note**

This is an open-source hardware project. The channel drawing is ours and will be published under an open licence. We would like to list manufacturers that can supply the part. Please say whether you would like to be listed (optional). This request is not a purchase order.

**Contact**

[Name], [email], [company/project], [country]
[Project page URL]

Many thanks,
[Name]

---

## Shorter version for marketplace chat (Alibaba etc.)

> Hello, we need a custom TPU water circulation pad, 90 x 200 cm (or tiles), two 10 mm barb ports, working pressure 0.5 bar, tested at 1.0 bar. We have our own drawing. Please quote 2 samples, 10 and 100 pcs. Do you accept 2-10 pcs? Please send: MOQ, die cost, sample price and lead time, TPU material datasheet (polyether, 0.2-0.35 mm), ISO 10993 or OEKO-TEX report, pressure test method. No logo, no branding. Thank you.

## Checklist before sending

- [ ] Channel drawing attached (or tell them it follows within [days])
- [ ] Decide full mat vs. tiles
- [ ] Confirm connector decision with `hardware/parts.toml` (barbs 10 mm, QDs on our hoses)
- [ ] Do not mention or copy any competitor's pad design
- [ ] Do not claim the product is a medical device
