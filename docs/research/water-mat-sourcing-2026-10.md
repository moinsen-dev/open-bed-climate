# Water mat sourcing (researched 2026-10-11)

Goal: a thin, flexible water pad, ~90 x 200 cm per bed side, 0.4-1 L/min, 13-43 C, <= 0.5 bar, quiet, washable cover, nightly use. Quantities: 2 samples, then ~10 units, then maybe 100+.

Method: public web search and page reads only. Nobody was contacted, no forms submitted. Anything not stated on a page is marked **n/s** (not stated). All prices marked *est.* are our estimates, not quotes. Listing prices are as seen on 2026-10-11 and change.

## 1. Manufacturing methods and fit

| Method | Fit for us | Notes |
|---|---|---|
| **RF/HF-welded TPU film or TPU-coated fabric** | Best long-term. Same process as medical cold/heat therapy pads and hospital mattresses. Thin, flat, parallel channels or weld-dot pattern, no kinking tubes. | Needs a brass/aluminium weld die (tooling). Only polar plastics weld: PVC, TPU, PU (PE/PP do not). Typical RF presses have limited bed size; 90 x 200 cm usually means welding in sections or building the mat from tiles (see risk below). TPU film costs 3-6x PVC (per a 2001 MDDI article, so dated). |
| Thermoformed / hot-air / ultrasonic seam welding | Fallback when the RF bed is too small. | Hot-air and ultrasonic seams exist on long-seam TPU fabric (DERFLEX lists RF, hot-air, ultrasonic trials). Seam quality for water at 0.5 bar must be tested. |
| **Silicone or PU tubing sewn/stitched into fabric** | Fine for samples and v0; no tooling. | Documented DIY: 4 mm ID reinforced tubing in a foam topper, ~30 m per mat (TechTeamGB, in `hardware/parts.toml`). 8 mm was too stiff. A seamstress or upholstery shop can make 10 of these; lowest tooling risk, highest per-unit labour. |
| **Off-the-shelf medical hypo/hyperthermia blankets** | v0 stopgap for the bench-to-bed step. | Sizes are patient-sized (about 64 x 163-175 cm, 25 in wide), not 90 x 200. Designed for hospital pumps and Colder-type self-sealing connectors. See section 4. |
| Complete Asian "water mattress pad" systems (pad + controller) | Stopgap source of pads only if the seller will sell the pad alone. | Many listings, MOQ 1-10 sets, USD 43-220 per complete set. Pad material is often PVC or silicone tube; hose connectors proprietary. Not a dependency (parts.toml rule). |

**Biggest technical risk: size.** One 90 x 200 cm mat needs a large weld die or several welds. Ask every RF shop for its maximum press bed and whether it welds in indexed sections. The safe alternative is a **tiled design**: e.g. 4 tiles of ~45 x 100 cm (or 2 of 90 x 100), each its own small die, joined by a supply and return manifold of 13/10 mm tubing. Small dies also cost much less (see section 3).

## 2. Candidates

"Small run" column: **Yes** = the site explicitly says small quantities/prototypes; **Implied** = prototyping or "short series" language but no number; **n/s** = nothing stated.

### Europe

| # | Company | Where | What they make (from their own pages) | Small run / samples | Source |
|---|---|---|---|---|---|
| E1 | **Dr. Winkler GmbH & Co. KG** | Ainring-Mitterfelden, DE | Specialises in HF welding of plastic films. Processes soft PVC, **TPU film and TPU-coated fabrics**. Makes liquid-, air- and foam-filled pillows and covers with welded valves/connectors; medical items (anti-decubitus aids, air chambers for bed systems, physio heat packs). | n/s (no MOQ, prototype or certification statement). Phone +49 8654 8088. | https://dr-winkler-kg.de/hf-kunstoffverarbeitung/ |
| E2 | **B.u.W. Schmidt GmbH** | Garbsen (Hannover), DE | Plastic-film products for physiotherapy, rescue and human/veterinary medicine since 1961; 2025 company deck says customer-specific products are a large part of the business. HF welding and small series are *not confirmed* by sources I could open (their site returned HTTP 429). A directory entry claims HF welding of flat film, small series, OEM. | Implied (directory only; verify) | https://www.buwschmidt.com/ |
| E3 | **Arrow Medical Ltd** | Kington, Herefordshire, UK | ISO 13485:2016 contract manufacturer. RF welding of PU and PVC, medical textiles/films, multi-layer assembly, prototype support. | Implied (prototype engineering support; MOQ n/s) | https://arrowmedical.co.uk/ |
| E4 | **RF Works Ltd** | Herefordshire, UK | Search snippet: radio-frequency welding, "make prototypes and tooling for prototypes", "produce a small quantity of specials", product design and testing. *Page fetch failed (DNS), so unverified; confirm the domain before use.* | Yes (per snippet) | https://rf-works.co.uk/ |
| E5 | **Dr.Tuba** (kite/wing bladders) | "new European production facility" (country n/s) | HF-welded **90 micron German TPU** bladders, plasticizer-free, custom shapes, OEM, 24 h manufacture incl. overnight pressure test. Sport inflatables, not medical. | "Low minimum order quantities" (no number); sample policy n/s | https://drtuba.eu/content/about-our-bladders |
| E6 | **CNC Polska** (tooling only) | Marki near Warsaw, PL | Designs and makes **HF/RF welding dies and brass/aluminium electrodes** from drawings or a sample; single parts and short series; quotes "in 24-48 h". Could supply a die to any welder. | Yes (single dies) | https://cncpolska.eu/ |

### United States (for completeness)

| # | Company | Where | What they make | Small run / samples | Source |
|---|---|---|---|---|---|
| U1 | **SealWerks** | Elk Grove Village, IL | RF welding, urethane-coated fabrics, bladders, hospital bed cushions; ISO 9001:2015; "Whether you need two units or 10,000, we're here to help"; prototype services and a "pilot production program". No MOQ stated. Phone 847-439-4565. | **Yes** | https://radiofrequencywelding.com/ |
| U2 | **TPI Custom Solutions** | Ham Lake, MN | ISO 13485:2016 medical soft goods; RF welding of vinyl, nylon-coated, polyurethane, **TPU**, films; prototyping; says tooling design/lead time is **2-6 weeks**. | **Yes** (prototyping, "single prototypes") | https://tpicustomsolutions.com/what-we-do/rf-welding |
| U3 | **Genesis Plastics Welding** | Fortville, IN | ISO 13485 contract manufacturer (clean room); products include **hot and cold therapy devices**, inflatable bladders, heating blankets. Focus on PE/PP "low-loss" films; TPU not stated. | n/s | https://mep.purdue.edu/made-in-indiana/company/genesis-plastics-welding-inc |
| U4 | **Polo Custom Products** | Topeka, KS | RF welding services for OEMs; TPU/PVC films and coated fabrics; medical bags and cuffs; tooling in aluminium/brass. | n/s | https://www.polocustomproducts.com/what-we-do/film-and-fabric-welding |

(American Pacific Plastic Fabricators, Westminster CA, RF welding and sewing, ISO 9001, appeared in a directory only; not verified.)

### Asia

| # | Company | Where | What they offer | Small run / samples | Source |
|---|---|---|---|---|---|
| A1 | **Shenzhen Grand Electric Appliance Co.** | Guangdong, CN (22 yrs on Alibaba) | Water-circulation cooling/heating mattress pads with control unit; "ETL and CE" claim on listing; listings MOQ **2 sets** (USD 200-220), 10 sets (USD 180-199), 200 sets (USD 180-200). Pad-only sale not stated. | **Yes** (2-10 sets) | https://gdgrand.en.alibaba.com/productgrouplist-803299153/Cooling_and_Heating_Mattress_Pads_Single_Zone.html |
| A2 | **Ningbo Lonmon Electrical Technology** | Zhejiang, CN | Water cooling/heating mattress, e.g. 160 x 70 cm with cooling machine; MOQ **1 set**, USD 43-70. Low-end (one AliExpress-type listing states 100% PVC). Good for cheap v0 pads to test channel geometry, not for sleep quality. | **Yes** (1 set) | https://www.accio.com/plp/water-circulation-blanket |
| A3 | **Jiangmen Compass Manufacturing** | Guangdong, CN | "Electric Intelligent **TPU** water heated ... mattress with water circulation", foldable; MOQ 50 sets, USD 220-250. | Medium (50 sets) | https://www.accio.com/plp/heating-pad-for-circulation |
| A4 | **WeiSheng Packaging** (via Pietra) | location n/s | Custom **TPU water bladders**: MOQ 100, USD 2.00-2.50 each, **custom sample USD 44, 9 days**. Simple bladder, not a channel mat. One June 2025 review says they declined a small production order. | Yes (sample), MOQ 100 | https://www.pietrastudio.com/sourcing/products/tpu-water-bladder |
| A5 | **Chengdu Cryo-Push / EVERCRYO** | Sichuan, CN | TPU circulating cold-water therapy systems (knee etc.), MOQ 1 set. Shows that TPU circulating pads are standard products in China; shape/size custom is unknown. | Yes (1 set) | https://www.qweryas.com/search-cold-water-therapy |

Asian marketplaces list hundreds of "water cooling mattress" sellers. Finding a *factory* that will weld a custom 90 x 200 cm TPU pad (not resell a branded system) needs RFQs; I could not confirm any from public pages. Listings do not show the controller-free pad price.

### Materials (upstream suppliers, if a welder asks you to supply fabric)

| Company | Where | What | Source |
|---|---|---|---|
| DERFLEX | CN | Weldable TPU-coated nylon/polyester rolls, RF/hot-air trials | https://www.derflex.com/tpu-fabric-for-welding.html |
| Erez | IL | TPU/PVC coated medical fabrics, "glueable and weldable by HF and Hot Air", e.g. TPU 1101 on 70 den nylon, 215 g/m2 | https://erez-therm.com/industry/medical |
| Permali (Tuftane TPU film) | UK | Medical TPU film for HF-welded bladders | https://www.permali.co.uk/medical-tpu-film |
| Eastex Products | US | Air/water-holding TPU-coated nylon fabrics for medical inflatables | https://www.textileworld.com/textile-world/nonwovens-technical-textiles/2012/02/eastex-products-introduces-tek-air-medical-fabrics-3/ |
| Jiaxing Nanxiong | CN | Medical TPU film, ISO 10993 passed (claim), **MOQ 2000 kg**: not for us | https://www.nanxiongtpu.net/ |

## 3. Costs (mostly estimates)

Only a few real numbers were found:
- Custom TPU water bladder: USD 2.00-2.50 each at 100-1000 units, sample USD 44 (WeiSheng listing; simple small bladder).
- Complete Asian water pad + controller: USD 43-70 (low end), USD 140-220 (mid), USD 410-1200 (app-controlled, MOQ 100-600).
- Hospital disposable blankets: USD 170-280 per box of 10 (Maxi-Therm Lite, Suprememed listing, 2025).
- Brand replacement pads for consumer systems: USD 249-399 (shown only as a price anchor).
- Tooling/prototype lead time: TPI says tooling design and lead time **2-6 weeks**; industry custom-inflatable lead times 3-6 weeks (Charles & Hudson buyer guide, 2026-05).

Everything below is **our estimate**; replace with quotes.

| Item | Estimate | Reasoning |
|---|---|---|
| Weld die, small tile (~45 x 100 cm), brass/aluminium | EUR 800-2500 | Brass/alu machined die; larger area costs more |
| Weld die, full mat (~90 x 200 cm) | EUR 3000-9000 (if a press that size exists) | Few presses that large; may be sectional |
| Sample (1 pc, with or without own die) | EUR 150-600 per piece (hand-welded with shared die) up to EUR 1500 incl. die | Prototype shops often charge setup |
| Unit price at **10** | EUR 250-600 (tile build, tooling separate) | Dominated by setup and labour |
| Unit price at **100** | EUR 120-250 | Material about EUR 30-60 (TPU, 2 x 1.8 m2) plus welding labour and ports |
| Unit price at **500** | EUR 70-150 | Asia lower end, EU upper end |
| Lead time, first samples | 3-6 weeks (die 2-6 wk per TPI) | |
| Lead time, repeat production | 2-4 weeks | |

## 4. Material spec to require, and a sample test plan

### Spec (what to put in the RFQ)

- **Polymer:** TPU, **polyether-based** (hydrolysis-resistant; polyester TPU degrades in warm, wet use), plasticiser-free, Shore A 85-92.
- **Construction:** two plies of TPU film 0.20-0.35 mm, or TPU-coated knit/woven nylon or polyester (about 200-400 g/m2) with coating on the water side; top ply smooth, welded.
- **Channels:** weld pattern supplied by us (drawing). Parallel channels or weld-dot field, 6-10 mm channel width, no serpentine over 1 m, so a pinched channel doesn't stop flow. Weld width at least 6 mm.
- **Ports:** two ports at one short edge, 10 mm barbs welded in (for our 13/10 mm tubing; ID 10 mm). Alternative: cut-to-length hose stubs with 10 mm barbs. Fine for QDs afterwards: CPC non-spill or Colder-type self-sealing as already chosen in `parts.toml`. Ask for the barb material (PP or nylon, no aluminium; wet path is brass/copper only).
- **Pressure:** working 0.5 bar (50 kPa), proof test 1.0 bar for 5 min on every unit, burst not below 2 bar on samples, no seam leak.
- **Temperature:** 5-50 C continuous; weld strength must hold at 50 C.
- **Skin safety:** ISO 10993-5 (cytotoxicity) and -10 (sensitisation) for the film, or OEKO-TEX Standard 100 (class I or II) for the textile parts; REACH SVHC declaration; phthalate/halogen-free statement. Mat sits under a sheet, so skin contact is indirect, but ask.
- **Cover:** separate washable cover (cotton/polyester spacer fabric, zip, 30-40 C wash). Not part of the first RFQ.
- **Traceability:** lot number per mat, test report per unit.
- **Compliance note:** this is a hobby/open-source pad, **not a medical device**; do not claim medical use. A supplier's ISO 13485 helps quality but is not required.
- **Do not copy** any commercial pad design. We supply our own channel drawing (see `docs/research/water-mat-rfq.md`).

### Sample test plan

1. **Visual/dimension:** weld width, port position, flatness, thickness at ports.
2. **Pressure/leak:** fill, bleed air, 0.5 bar for 24 h on paper towels, then 1.0 bar for 5 min. No weeping, no weld creep.
3. **Burst (sacrificial sample):** ramp 0.1 bar/min to failure; record bar and failure place. Pass: >= 2 bar and failure not at a weld.
4. **Flow resistance:** water at 22 C, 0.5 L/min (and 1.0), measure differential pressure across the mat flat and with a 75 kg weight on 40 x 20 cm patch (pinch test). Pass: <= 5 kPa flat, <= 15 kPa under load, flow does not fall below 0.3 L/min.
5. **Thermal uniformity:** thermal camera over the top surface after 10 min at 15 C and 40 C supply, mat flat, bed-like load; max spread between inlet and outlet <= 2 K (model says ~2 K at 70 W); look for hot/cold stripes and dead zones.
6. **Noise:** water at 0.5 L/min, ear 1 m from the mat in a quiet room; record dB(A); listen for gurgling when air is trapped.
7. **Fold/durability:** 5000 fold cycles over a 50 mm radius on a flat bed and 2000 cycles of 75 kg pressing, then repeat leak test. Wet at 40 C for 14 days then peel test on a weld strip.
8. **Priming/air:** time to purge air with the mat flat and with the outlet end raised.
9. **Comfort:** sleep-test on mattress under a sheet (hand feel, crinkle noise, edge feel).

## 5. Recommendation

**For samples now (this month, minimal cost):**
1. **Cheap tubing-in-fabric build** (DIY, no tooling): finish the Solo Starter mat for bench-to-bed work. No supplier needed.
2. **One cheap Asian pad** (A1 Shenzhen Grand at 2 sets or A2 Lonmon at 1 set, about USD 45-220): buy as a thermal and flow reference and for stopgap testing. It will not be the final product, but it gives the team a real mat to compare against.
3. **Hospital blanket stopgap:** a reusable Colder-connector blanket (Maxi-Therm / Plastipad class, e.g. 24 x 60 in urethane, listing found on McKesson, price behind login) or a used Maxi-Therm. Disposable boxes of 10 cost USD 170-280. It is about 64 cm wide, which is too narrow for a full side but works for torso testing. Hospital pumps run higher pressure than ours; check ratings, and note blankets are single-patient devices.

**For ~10 units (pick two in parallel):**

- **Path A, EU RF welder with tiled design (recommended):** Dr. Winkler (E1) and Arrow Medical (E3) as first RFQs; add RF Works (E4) after verifying them. All are in Europe, TPU/PU capable (E4 unconfirmed), no import duties for you. Ask for a 2-sample run on a **shared small die** first. Order the die separately from CNC Polska (E6) if the welder wants a drawing-based quote, or have the welder source it.
- **Path B, US prototype welder (best explicit small-run language):** SealWerks (U1) or TPI (U2). Both state prototypes and tiny quantities. Costs more to ship and customs apply. Use if the EU quotes are slow or too large.
- **Path C, China custom pad run:** RFQ A1, A3 and the TPU-bladder/medical pad factories on Alibaba for 10-50 units with our drawing. Cheapest per unit but the weakest on proof of quality, ISO 10993 evidence and willingness to do 10 pcs; ask for third-party test reports and a paid sample.

**Biggest risks**
1. **Size and tooling:** a full 90 x 200 cm weld die may not exist at a small shop. Mitigation: tiled design.
2. **Small runs:** nobody quotes 10 units publicly. One review of A4 says it declined small production. Expect quotes dominated by setup.
3. **Seam reliability** over thousands of nights at 40 C: demand the durability tests above before reorder.
4. **Unverified claims:** several shops (E2, E4, U4, American Pacific) rest on directory or search snippets. Confirm before relying on them.

## Sources

All URLs are inline in the tables above. Additional: Gaymar Medi-Therm brochure (https://myagilitiimg.agilitihealth.com/userGuides/prod514_Gaymar%20Meditherm%206900%20Brochure.pdf), Stryker blanket list (https://techweb.stryker.com/Gaymar/TMP/Medi-Term/Blankets/index.html), CSZ self-sealing connectors note (https://genthermmanuals.s3.amazonaws.com/Hyper-Hypo/Maxi-Therm+Lite/newconnections.pdf), Maxi-Therm Lite price (https://www.suprememed.com/maxi-therm-lite-hyper-hypothermia-blanket-nonwoven-for-controlled-patient-warming-or-cooling-in-surgical-and-emergency-settings), Gelli-Roll sheet (http://artmedical.net/artmedical/arquivos/info-tecnicas/GelliRoll.pdf), RF tooling (https://www.polocustomproducts.com/what-we-do/film-and-fabric-welding), consumer replacement pad pricing (https://sleep.me/product/chilipad-cool-mesh-replacement).
