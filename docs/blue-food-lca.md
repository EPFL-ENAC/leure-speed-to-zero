# Blue food LCA: Swiss domestic freshwater fish

Written 2026-09-20. Model code: `tcaf_model` on branch `feat/blue-food-lca` (branched from `tcaf` at `a725082`), worktree `~/Documents/transition-compass-model-feat-blue-food-lca` (commit `f10c9d5`). The app changes are on `feat/tcaf-deployment`. Neither is pushed.

## What it adds

The True Cost environment total now includes the LCA cost of fish **produced in Switzerland**. Before, fish had no LCA at all. Imports are not covered (over 90% of Swiss freshwater-fish supply), so the new series is a domestic-production cost, not the environmental cost of Swiss fish consumption.

New output variable: `tcaf_lca_cost_ffish` [CHF]. It is included in `tcaf_lca_cost_total`, in the 14 `tcaf_lca_cost_<impact>` series and in `tcaf_true-cost_total`. Nothing else in the TCAF output changed (checked variable by variable against a run of the unmodified model).

## Production tab, Blue food sub-tab

Six charts, route `/production/blue-food` (`config/subtabs/production.json`), all Swiss freshwater fish:

| Chart                                               | Outputs                                                                                                      |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Production by method [t]                            | `tcaf_fish_production_aquaculture`, `tcaf_fish_production_capture`                                           |
| Supply: Swiss production and imports [t]            | the two above and `tcaf_fish_import` (demand not met by domestic production, 48,000 t in 2022 = FBS imports) |
| Self-sufficiency ratio [%]                          | `tcaf_fish_ssr`                                                                                              |
| Environmental cost by method [million CHF]          | `tcaf_fish_cost_aquaculture`, `tcaf_fish_cost_capture`                                                       |
| Environmental cost by impact category [million CHF] | `tcaf_fish_cost_<impact>` (14)                                                                               |
| GHG emissions [t CO2-eq]                            | `tcaf_fish_ghg_aquaculture`, `tcaf_fish_ghg_capture`                                                         |

Wiring: the fish outputs are built in `TCAF_fish_TPE_interface` (model). The Production tab's backend run did not include the TCAF module, so `backend/model_config.json` now lists `TCAF` in the tcaf profile's `production` sectors, and `leversStore.ts` merges the TCAF results into the Production data. The tab therefore also runs the TCAF module, which the other Production sub-tabs do not need.

To see it in the running app the backend must import the model branch `feat/blue-food-lca` (merge it into `tcaf`, or point `TCM_PATH` at the worktree) and restart, since `model_config.json` is read at startup.

## Granularity

|        | Model                                                             | TCAF_fisheries_aquaculture                                    | Used here                               |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------- | --------------------------------------- |
| Food   | FBS groups `dfish`, `ffish`, `pfish`, `oth-aq-animals`, `seafood` | ISSCAAP group (~30)                                           | `ffish` only                            |
| Method | none for fish                                                     | `fisheries_no_trawl`, `fisheries_bottom_trawl`, `aquaculture` | `aquaculture`, `capture`                |
| Impact | 14 ReCiPe categories, physical, monetized in CHF by the model     | same 14, monetized in EUR                                     | physical values, monetized by the model |

Swiss production (FishStatJ 2022, 3,956 t of finfish) is all FBS Freshwater Fish, which contains FishStatJ's freshwater and diadromous divisions. So no demersal or pelagic category has Swiss production, and bottom trawl does not occur.

`seafood` is left out. Its Swiss production is 30 t of farmed shrimp (0.75% of Swiss output), and I could not confirm from the repo which FBS items the model's `seafood-seafood` category holds (the item-to-category dictionary is not in the repo).

## Calculation (`TCAF_fish_lca_workflow`, `tcaf_module.py`)

1. **Demand.** `agr_demand` [kcal] for `seafood-ffish` from dietary-habits. It is the same calibrated, adherence-weighted demand crop and livestock receive, passed through a new `food-demand` key of the dietary-habits to TCAF interface.
2. **Tonnes.** demand / 690,000 kcal per t (`cdm_kcal`, `seafood-ffish`). The FBS food quantity of fish is in live-weight equivalent (Swiss FBS gives about 0.61 kcal/g), so these tonnes are whole fish, on the same basis as the LCA processes (per kg at landing or farm gate). **No edible-fraction step is needed**, unlike what I first proposed.
3. **Domestic production** = tonnes x SSR. SSR = FBS production / (food + feed + processed), the formula the livestock module uses. FBSH for 1990 to 2013 (two decimals), FBS from 2014 (rounded to 1,000 t). Forecast years hold the 2019-2023 mean, 7.8%.
4. **Split.** Wild capture is held at its FishStatJ tonnage (annual to 2023, then the 2019-2023 mean, 1,471 t). Aquaculture is the rest. Lake catch does not follow diet levers, so a growing domestic production is all aquaculture.
5. **Impacts** = production [kg] x impact per kg, monetized per category with the model's CHF factors.

Kept out of `TCAF_lca_workflow` on purpose: that function calibrates GHG against the IPCC agriculture inventory (cat. 3), which does not contain fisheries or aquaculture.

## LCA values (kg live weight)

Built by `TCAF_fish_preprocessing.py`; the audit table is `data/blue-food/fish_lca_ch_ffish_basis.csv`.

- **Aquaculture**, 2.95 kg CO2e/kg, CHF 10.4/kg. Per Swiss ISSCAAP group, the fisheries project's rule: mean of the group's own aquaculture processes if it has any, else the mean of the observed groups of the same division (`division_pooled`). Groups weighted by mean Swiss aquaculture tonnage 2018-2022:
  - salmons and trouts (1,475 t): 7 processes, observed;
  - misc. freshwater fishes, mostly perch (728 t): pooled, which means **tilapia** (extensive pond, 4.6 kg CO2e/kg). This is the largest judgement call: no perch process exists;
  - sturgeons (45 t) and misc. diadromous (0.6 t): pooled from salmon and trout.
- **Capture**, 2.37 kg CO2e/kg, CHF 1.9/kg. Proxy: the one passive-gear finfish process (common sole, trammel net, France), standing for small-boat lake fishing with no feed. A single-process proxy.

Cross-check against the fisheries project: salmon and trout aquaculture 11.95 EUR per kg whole there, weighted Swiss aquaculture 10.4 CHF here; trammel net 1.98 EUR there, 1.86 CHF here.

## Results (default levers)

|                            | 1990  | 2010  | 2022  | 2023  | 2030  | 2050  |
| -------------------------- | ----- | ----- | ----- | ----- | ----- | ----- |
| Domestic production, t     | 4,230 | 3,166 | 4,000 | 4,403 | 5,395 | 7,932 |
| of which aquaculture, t    | 1,072 | 1,065 | 2,514 | 2,879 | 3,924 | 6,461 |
| Fish LCA cost, million CHF | 17.0  | 15.0  | 28.9  | 32.7  | 43.4  | 69.9  |
| Share of LCA total         | 0.6%  | 0.6%  | 1.2%  | 1.3%  | 1.9%  | 5.3%  |

Historical production reproduces FBS production exactly (4,230 t in 1990, 2,760 t in 2000, 4,000 t in 2022), and the capture part follows FishStatJ. The 2050 share rises because default-lever fish demand grows while the other categories fall.

## Things to know

- **Water consumption is 71% of the aquaculture cost** (CHF 7.35 of 10.38 per kg). It comes from the trout and salmon processes and the scarce-water monetization factor. Worth a look before the number is quoted.
- The Swiss capture LCA and the perch value are proxies. Weigh the fish cost as an order of magnitude, not a Swiss-specific LCA.
- FBS is rounded to 1,000 t from 2014, so the annual SSR is noisy (3 or 4 kt of production). The forecast uses a five-year mean.
- `dietary-habits_to_TCAF.pickle` is used only by the standalone module run. The old pickle holds different diet values from a fresh run at default levers, so I kept it and only added the `food-demand` key. The app uses the live interface.
- If `food-demand` or the fish inputs are missing, TCAF prints `TCAF: fish LCA skipped` and leaves fish out.

## Regenerating

Inputs are CSVs in `tcaf_model/_database/pre_processing/TCAF/data/blue-food/`. That folder is git-ignored by the repo's `pre_processing/.gitignore` (`*.csv`), so they are local files; force-add them if they should be tracked (about 30 KB).

```bash
cd tcaf_model/_database/pre_processing/TCAF
# FAOSTAT bulk files: https://bulks-faostat.fao.org/production/  (the API now needs a token)
python TCAF_fish_extract_inputs.py <TCAF_fisheries_aquaculture> <FBS_Normalized.csv> <FBSH_Normalized.csv>
python TCAF_fish_preprocessing.py     # adds fxa["fish"] to TCAF.pickle, nothing else
```

`TCAF_preprocessing.py` cannot be re-run here (its raw LCIA files are not in the repo), which is why the fish inputs extend the pickle instead of going through it.
