# Sleep Sweet Spot
### From wearable data to better everyday decisions

**Rogelio Moreno Guinea | Exploratory longitudinal data analysis | October 2026**

> Data rarely speaks for itself. Context turns information into decisions.

## Why this project exists

For a decade, I collected sleep metrics without knowing what to do with each daily report. A video about biphasic sleep brought back memories of nights in which I woke up and slept again. But memorable interruptions are not a representative sample of every night.

The initial hypothesis became a broader investigation:

**What can changing wearable measurements reveal about sleep patterns, and how can that knowledge improve the choices we make during waking life?**

The goal is not to maximize sleep duration, REM or Deep. It is to understand the **two-way relationship between daytime activity and sleep**, test competing explanations, and evaluate actions that may improve daytime functioning.

## What we have learned so far

### 1. Going to sleep later does not imply waking proportionally later

In **2,058 eligible Apple Watch sleep windows (2020–2026)**, a one-hour later recorded onset was associated with approximately **30 minutes less recorded sleep** and a **24-minute later final sleep time**, in descriptive models adjusted for calendar variables.

| Recorded sleep onset (local) | Share with ≥5 h | Share with ≥7 h |
| :-- | --: | --: |
| 20:00–21:59 | 99.1% | 75.9% |
| 22:00–23:59 | 94.7% | 53.3% |
| 00:00–01:59 | 85.7% | 22.1% |
| 02:00–04:59 | 53.9% | 4.3% |

**Decision implication:** as a social evening continues, I can now ask whether staying longer is worth potentially having less sleep. I may still choose to stay. Better information changes the *decision frame*, not necessarily the choice.

**Important:** five hours is an illustrative threshold for analyzing distributions, **not** a recommended minimum or an established threshold of healthy daytime performance. These frequencies are associations, not intervention success probabilities.

### 2. A short night is not automatically paid back the next night

Among **219 complete three-night sequences** starting below five hours, the observed median durations were **4 h 30 min → 6 h 51 min → 6 h 47 min**. The return toward typical duration is not proof of full recovery; regression to the mean is an alternative explanation.

**Decision implication:** it would be unwise to assume an unusually short night is guaranteed to be fully compensated.

### 3. A remembered split night does not establish habitual biphasic sleep

Under one explicitly defined episode rule (≥60 minutes between sleep episodes, with ≥60 minutes of sleep on both sides), **105 of 1,377** windows in a stricter **2022–2026 staged-sleep cohort** met the split criterion. The frequency changes with the gap definition.

**Decision implication:** compare interruptions by onset time, episodes and subsequent functioning rather than diagnosing a habit from memorable events.

### 4. Ten years do not mean one measurement system

| Era | Recorded observation | Key limitation |
| --- | --- | --- |
| 2016 onward | Clock / time in bed | Time in bed is not measured sleep |
| 2018 onward | Sleep++ estimated intervals | App methods differ from later Watch estimates |
| 2020 onward | Apple Watch sleep estimates | No detailed stage architecture initially |
| September 2022 onward | Watch Core, Deep, REM and Awake estimates | Stage detection and algorithms can change |

**Decision implication:** do not treat apparent trends across device eras as purely physiological changes. Each analysis must document its sources and comparability.

## How the investigation works

1. **Observe and question.** Begin with lived experience and possible explanations, not a predetermined conclusion.
2. **Audit measurement.** Track data sources, gaps, intervals, timezone metadata, overlap, stage coverage and device eras.
3. **Explore hypotheses.** Examine timing, continuity, split episodes, subsequent nights and physiological measures with appropriately defined cohorts.
4. **Test robustness.** Vary episode rules, cohort eligibility and calendar adjustments; distinguish unmeasured time from recorded Awake.
5. **Identify choices.** Translate a finding into a concrete, personally relevant decision or explain why it is not actionable.
6. **Evaluate the outcome.** Since October 15, 2026, a *private* prospective diary has recorded daytime energy, mental clarity, sleepiness, waking experience and context. Both directions matter: **day → night → next day**.

The diary is too new to demonstrate a personal optimal sleep duration or the impact of any proposed intervention.

## Reproducibility without exposing personal health records

This repository includes a **synthetic Python demonstration** and automated checks. No real night-level records or personal diary content are included. The fictional example demonstrates grouping by sleep onset and pairing actual consecutive calendar days. It **does not generate or reproduce** the private research estimates above.

Run locally with Python 3.9 or newer:

```bash
python demo_synthetic.py
python -m unittest discover -s tests -v
```

The historical aggregate findings came from a separate private Apple Health analysis. The underlying participant-level data are intentionally not public, so independent reproduction of those specific estimates requires access to the protected data. Synthetic test success validates code examples, not physiological validity.

## What this project does **not** establish

- That five, six or seven hours are sufficient for this individual, much less for others.
- That later bedtime **causes** worse next-day functioning.
- That more REM or Deep is necessarily better, or can be reliably controlled at will.
- That an association with heart rate, HRV, lunar phase or a supplement proves its effect.
- That an observational single-participant analysis can be generalized to another person's sleep.

## Next investigation

Link the **day before**, the **night**, and the **following day** as separate time-indexed observations. Explore patterns of sleep onset, duration, continuity, activities and fatigue; then evaluate potential actions against daytime functioning and enjoyment, rather than a single device score.

This is a **living case study**: publication of defensible findings comes before any claim of a personalized sweet spot.

**Skills demonstrated:** Python, longitudinal analytics, measurement auditing, exploratory statistics, sensitivity analysis, privacy-aware research design, and translation of evidence into decisions.

---

*Single-participant, exploratory, non-clinical research. Historical data cut off October 1, 2026. Never upload private Apple Health exports, individual sleep tables, identifiable events or prospective diary entries to this repository.*