# Modelling Decisions to Review

Every judgement in the forecast is listed here so that it can be checked and defended.
`Evidence` means the data settled it. `Judgement` means it is an assumption and could be argued.

| Decision | Choice | Basis |
| --- | --- | --- |
| Seat rule | Quota, floor, largest surplus, ties to most votes | Evidence: rebuilds all 10 official IEC seat reports exactly |
| Council sizes | 270, 214, 224, 120, 100 | Evidence: IEC 2021 seat reports and identical 2026 IEC ward lists |
| Votes that count | PR plus ward votes of parties with a PR list | Evidence: needed to match the IEC totals |
| Blend weight | 0.45 local, 0.55 national | Evidence, thin: one election, stable at 0.40-0.50 across leave-one-metro-out |
| Prior spread | 0.25 log points for established parties, 0.48 for others | Evidence, thin: 2021 backtest errors |
| Polls used | Latest from each pollster, August to October 2026 | Judgement: all ten checked, see `data/external/polls.csv` |
| Poll weights | By sample size. Ipsos samples are implied by its published margins | Evidence: Ipsos has about 277 in Johannesburg and 158 in Tshwane, against about 1,000 for others |
| Partial polls | Used as published, with unlisted groups missing | Judgement |
| Common poll error | 0.10 log points | Judgement: the pollsters' spread cannot reveal a shared miss. Sensitivity: 0.05 and 0.20 |
| Buffalo City | No published poll figures, so it borrows Nelson Mandela Bay's poll shift | Judgement: the largest single influence on its result. Sensitivity: none, or all four metros |
| Small parties | OTHER split by mean 2021 and 2024 shares, with Dirichlet noise | Judgement |
| Metros | Treated independently | Judgement: statements across metros would need correlated errors |

## Not modelled

- Turnout. Differential turnout is absorbed in the vote-share uncertainty.
- Overhang. A party winning more wards than its entitlement is ignored. It did not occur in any
  of the 10 councils checked, and total seats depend only on combined votes unless it occurs. The
  margin was only 2 seats in Johannesburg and Ekurhuleni in 2021, so this is a real risk in 2026.
- Coalition politics. "Reaches a majority" is arithmetic, and says nothing about who would agree
  to govern together.

## Known weaknesses

- The backtest is one election. The blend beat both baselines, but only modestly.
- The backtest cannot test the poll update, because this project has no 2021 metro polls.
- Ipsos says the ANC in Buffalo City "may fall short of an outright majority" but withheld the
  figures because the margin of error is too large. That points to the upper end of the
  Buffalo City range. It is reported as context and is not a model input.
- Ipsos also says the ANC leads the DA narrowly in Ekurhuleni, while MarkData has the DA ahead.
  Only MarkData's figures enter the model, so the forecast's near-even race there may be sensitive
  to this one poll.
- The polls measure different groups. MarkData reports likely voters, while Ipsos, SABI and the
  Social Research Foundation report registered voters.
- The latest Social Research Foundation metro samples are not published, so the previous wave's
  sizes are used. Some smaller-party figures rest on Wikipedia alone, as noted in `polls.csv`.
- Pollsters may have a house lean. Critics say the Social Research Foundation and SABI lean to the
  DA, and this was not adjusted for, though the between-pollster spread widens the uncertainty.
