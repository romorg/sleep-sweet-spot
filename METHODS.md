# Methods: retrospective Stage 1

**Fixed historical data cutoff:** October 1, 2026. Raw sleep-related Apple Health export spans September 2016 through the last overnight window on September 30 / October 1, 2026. The code is participant-agnostic and does not impose this cutoff on someone else's export; it describes the analyzed historical snapshot.

## Measurement inventory

The export contained 60,903 sleep-interval records from several Health sources. Hardware, source application, device label, Apple Health measurement category and software generation must not be conflated. An Apple Watch may have been worn throughout while a given Clock record was recorded by an iPhone. There is no verified mapping of every interval to an exact retail Watch model; source labels are not proof of hardware model.

Sleep++ is a third-party Apple Watch sleep-analysis app with its own estimated intervals. Its *AsleepUnspecified* data cannot be reinterpreted as Watch *Core/Deep/REM* without new evidence. Time in bed (InBed) is not equivalent to recorded sleep.

## Operational window construction

- Read a **sleep-only** JSON export of Apple Health sleep intervals (never upload a complete Health export to a public repository).
- Convert timestamp offsets to UTC for elapsed duration; use valid `HKTimeZone` IANA metadata for local civil hours. Flag timezone and measurement-source changes.
- Keep Watch-labeled recognized asleep/awake categories for main estimates. Drop exact duplicate intervals. Reconcile overlaps with a time sweep; stage-specific records supersede overlapping AsleepUnspecified, and contradictory detailed stages trigger a conflict flag.
- Group intervals by **local noon-to-noon windows**. Each window may include multiple episodes, and is not asserted to be one continuous physiological night. A small number of records can cross the boundary and require sensitivity checks.
- Compute sleep as the union of sleep-stage intervals and Awake from explicitly labeled Awake segments. **Unmeasured time inside the span is distinct from Awake**. Neither time in bed, sleep onset latency, nor post-final-awakening wakefulness are measured here.
- A qualifying **timing** window has first recorded onset between 20:00 and 04:59, total recorded sleep between 180 and 960 minutes, recorded span at most 960 minutes and no pre-specified special exclusion. This yields **2,058** windows from 2020–2026, with 1,933 consecutive-date pairs and 1,817 complete triples.
- Consecutive pairs require exact calendar-day adjacency. Missing days are **not** imputed. There are **36** timezone-label changes and **3** source-label changes among the 1,933 pairs. One main-cohort window finishes across the following local noon; sensitivity excluding it barely alters the main regression, but the case remains documented as a measurement boundary.
- A qualifying **staged** window requires at least three recorded hours, a span no longer than 16 hours, at least **95%** of recorded sleep assigned to Core/Deep/REM (not AsleepUnspecified), and no incompatible detailed-stage conflicts. **1,381** staged windows meet those conditions for September 2022–September 2026 without individual date exclusions. They are **not the same cohort** as the 2,058 timing windows.

## Episodes and robustness

A split event requires a gap of at least a defined threshold between recorded sleep episodes, with **at least 60 minutes of recorded sleep before and after** that gap. Thresholds compared: 60, 90, and 120 minutes. A recorded sleep gap does not prove continuous wakefulness. The analysis reports counts under all thresholds, not a clinical diagnosis.

## Timing model

Ordinary least squares models recorded duration and final observed sleep time as functions of the first recorded sleep hour with calendar-year, month, and weekday indicators. Exploratory 95% intervals use month-year clustered uncertainty (73 clusters). These estimates are **descriptive**. Sleeping later, duration and final sleep time are mechanically connected. Neither coefficient identifies a causal impact of bedtime on health or functioning.

The pipeline checks stage consistency, missing intervals, timezone boundaries, source shifts, and neighboring calendar dates with synthetic unit tests. Passing unit tests does not independently verify the protected empirical input.

## Reproduction limit

The publicly shared tables reproduce the displayed counts, shares and transition chart, but **not** the adjusted regression, interval sweep or stage exclusions from first principles. Those need the participant's raw sleep-only intervals (not public) or an equivalent export provided by a willing analyst. The code and synthetic demonstrations show methodological implementation rather than publishing private per-night records.
