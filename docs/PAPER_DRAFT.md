# Who Can Govern? Hung-Council Probabilities for Five South African Metros in the 2026 Local Government Elections

Lunga Ngaka, University of Fort Hare

**Status: draft. Forecast figures are working values and will be replaced when the forecast is
frozen before polls open on 4 November 2026.**

## Abstract

South African metros are governed by councils whose seats follow a mixed electoral system, so
small changes in votes can decide who is able to govern. This paper gives a timestamped probabilistic
forecast for five metros in the 4 November 2026 Local Government Elections: Johannesburg, Tshwane,
Ekurhuleni, Nelson Mandela Bay and Buffalo City. Vote shares are modelled as compositional data
using a logistic-normal model that combines past results with published polls, and each of 200,000
simulated elections is passed through the exact seat allocation rule. That rule reproduces all ten
official seat calculations for these metros in 2016 and 2021. An outright majority is very unlikely
in the four metros with published polls. The DA is favoured to be the largest party in Johannesburg
and Tshwane, while Ekurhuleni and Nelson Mandela Bay are close to even. Buffalo City is the main
uncertainty: the chance that the ANC loses its majority there is 27% under the base assumption and
ranges from 18% to 47% across alternatives, because no poll figures are published for that metro.
The forecast will be scored against the declared results using a plan fixed in advance.

## 1. Introduction

Since 2016, coalition government has become common in South Africa's largest cities. Whether a
council is hung, and which parties can form a majority, matters more for how a city is run than a
party's vote share alone. Forecasts of vote share do not answer this directly, for two reasons.

First, seats are not a smooth function of votes. In Nelson Mandela Bay in 2021 the DA won 210,007
combined votes and the ANC 207,443. Both finished on 48 seats, because the ANC took the last
available seat on its remainder. Second, a single point forecast hides the uncertainty that
matters. A party on 45% may or may not be near a majority, depending on how the remaining votes
divide.

This paper therefore asks a probabilistic question. For each metro, what is the chance that no
party wins an outright majority, which party is likely to finish largest, and which coalitions are
arithmetically possible? It makes three contributions:

1. An exact implementation of the seat rule, validated against every official seat report for
   these metros in 2016 and 2021.
2. A transparent compositional model of vote shares, which combines fundamentals and polls in a
   closed form that can be checked by hand.
3. A forecast published before the election, with a scoring plan fixed in advance, so that its
   performance can be judged fairly.

## 2. The seat rule

Metro councils are elected under Schedule 1 of the Local Government: Municipal Structures Act 117
of 1998. Half of the seats are ward seats, won by plurality, and the rest come from party lists so
that the council is proportional overall. Each voter has one ward vote and one party vote.

Let $A$ be the total valid votes for all parties on both ballots, $B$ the council's seats, $C$ the
independent ward councillors elected, and $D$ the ward seats won by parties with no list. The
Electoral Commission (IEC) computes the quota

$$Q = \left\lfloor \frac{A}{B - C - D} \right\rfloor + 1.$$

A party with $v$ combined votes first receives $\lfloor v / Q \rfloor$ seats. Remaining seats go to
the parties with the largest surpluses, and equal surpluses go to the party with more votes. Ward
wins are then subtracted from each party's total, and the balance is filled from its list. A party
that wins more wards than its total entitlement keeps them and receives no list seats.

Two consequences simplify the forecast. A party's total depends on its combined votes and not on
which wards it wins, unless it exceeds its entitlement. In the ten councils examined no party did
so, and no independent won a seat, so $C = D = 0$ in all of them. The forecast therefore needs each
party's combined vote share and does not need a model of each ward.

The term $D$ appears in the IEC's published reports but not in the 2009 text of the Act used here,
which suggests a later amendment. The implementation follows the IEC's published calculation.

**Validation.** The rule was applied to the IEC's detailed results for 2016 and 2021 and compared
with its Seat Calculation Detail reports. All ten councils matched on every party's votes, the
quota, both allocation rounds and final seats. Matching required one detail that is easy to miss:
the IEC's vote total counts only parties on the PR ballot, so parties that stood only in wards must
be excluded.

## 3. Data

**Results.** Voting-district results for the 2016 and 2021 local elections and the 2019 and 2024
national elections come from the IEC. Local results use combined PR and ward votes. National results
use the national ballot.

**Council sizes.** The IEC's 2026 ward lists show 135 wards in Johannesburg, 107 in Tshwane, 112 in
Ekurhuleni, 60 in Nelson Mandela Bay and 50 in Buffalo City, unchanged from 2021. Councils therefore
have 270, 214, 224, 120 and 100 seats.

**Polls.** Ten polls with fieldwork from August to October 2026 were used, being the latest from
each pollster: four in Johannesburg, four in Tshwane, and one each in Ekurhuleni and Nelson Mandela
Bay. Figures were checked against each pollster's report or press coverage of it. Ipsos withheld
figures for Ekurhuleni, Nelson Mandela Bay and Buffalo City because of large margins of error, and
no published poll figures were found for Buffalo City.

Parties are grouped as ANC, DA, EFF, MK, PA, ActionSA, FF+ and Others.

## 4. Model

Vote shares are positive and sum to one, so they are compositional data (Aitchison, 1986). Errors
are modelled on the log scale, and each draw is returned to the simplex by dividing by its sum,
which gives a logistic-normal model.

**Fundamentals.** With $y_j$ the last local share and $z_j$ the latest national share of party $j$,

$$f_j = w\,y_j + (1 - w)\,z_j.$$

A party absent from one of the two elections takes its share from the other, so that a new party
such as MK is not halved. The shares are then rescaled to sum to one. The weight $w = 0.45$ was
chosen by minimising error in the 2021 backtest.

**Poll update.** Let $m_j = \log f_j$ with prior variance $a_j^2$. Let $p_j$ be the sample-weighted
mean of log poll shares, with variance

$$b_j^2 = \frac{s_j^2}{k_j} + c^2,$$

where $s_j$ is the pooled spread between pollsters, $k_j$ is the effective number of polls, and
$c = 0.10$ allows for an error common to all pollsters that their spread cannot reveal. The value of
$c$ is an assumption, and Section 7 varies it. The posterior for $\log$ share is normal with

$$\text{precision} = \frac{1}{a_j^2} + \frac{1}{b_j^2}, \qquad
\text{mean} = \frac{m_j / a_j^2 + p_j / b_j^2}{1 / a_j^2 + 1 / b_j^2}.$$

For the ANC in Johannesburg the polls receive 81% of the weight. The prior spread $a_j$ comes from
the backtest: 0.25 for established parties, and 0.48 for new and smaller parties, the error of the
group that contained the surprise new entrant in 2021.

**Buffalo City.** With no poll figures available, Buffalo City's prior is shifted by the difference
between polls and fundamentals in Nelson Mandela Bay, the nearest comparable metro. This is the
most consequential judgement in the forecast and Section 7 reports alternatives.

**Simulation.** For each metro, 200,000 sets of log shares are drawn from the posterior and closed.
Others is split among smaller parties using their average 2021 and 2024 shares with Dirichlet noise,
because small parties win seats on remainders. The exact seat rule is then applied to each draw.
Probabilities are the proportion of draws in which an outcome occurs.

## 5. Backtest

The fundamentals were tested by predicting 2021 using only the 2016 local and 2019 national
results.

| Method | Mean absolute error (points) |
| --- | --- |
| Blend, weight chosen on all five metros | 3.48 |
| Blend, leave-one-metro-out | 3.53 |
| National result only | 4.09 |
| Last local result only | 4.11 |

The blend beats both baselines, but modestly. Its largest errors are informative. The ANC was
over-predicted by 9.6 points on average, as its 2021 fall was not captured by earlier results.
ActionSA, a new party in 2021, was not predicted at all and won 16.2% in Johannesburg, which
contributed to an error of 6.5 points there against 0.8 in Buffalo City.

Two limits apply. This is a single election, and the backtest cannot test the poll update, because
this study has no 2021 metro polls.

## 6. Forecast

**Table 1. Council outcomes**

| Metro | Seats | Needed | No majority | ANC largest | DA largest | Tied |
| --- | --- | --- | --- | --- | --- | --- |
| Johannesburg | 270 | 136 | >99% | 4% | 95% | <1% |
| Tshwane | 214 | 108 | >99% | 9% | 89% | 2% |
| Ekurhuleni | 224 | 113 | >99% | 55% | 42% | 3% |
| Nelson Mandela Bay | 120 | 61 | >99% | 48% | 46% | 5% |
| Buffalo City | 100 | 51 | 27% | >99% | <1% | <1% |

**Table 2. Median seats with 90% ranges for the leading parties**

| Metro | ANC | DA | EFF | MK | ActionSA |
| --- | --- | --- | --- | --- | --- |
| Johannesburg | 67 (57-78) | 85 (74-97) | 29 (22-37) | 32 (22-44) | 24 (19-31) |
| Tshwane | 59 (50-68) | 71 (62-81) | 25 (20-33) | 10 (7-15) | 22 (18-28) |
| Ekurhuleni | 68 (56-81) | 66 (55-78) | 24 (17-33) | 28 (17-44) | 13 (9-17) |
| Nelson Mandela Bay | 45 (38-52) | 45 (38-52) | 10 (7-14) | 2 (1-4) | 3 (2-4) |
| Buffalo City | 55 (43-66) | 18 (12-26) | 13 (8-19) | 5 (2-10) | 4 (2-8) |

Figure 1 shows seat ranges against the majority line, Figure 2 the chance of finishing largest,
Figure 3 how polls move the forecast from fundamentals, and Figure 4 the backtest.

The main result is that the hung-council question is effectively settled in four metros. In those
four, the live questions are who finishes first and who can assemble a majority. Nelson Mandela Bay
is close to a coin flip, with a 5% chance of an exact tie for largest party, as occurred in 2021.

**Coalitions.** The only two-party pairing with a high chance of a majority in Johannesburg,
Tshwane, Ekurhuleni and Nelson Mandela Bay is ANC and DA. Other routes need three parties: for
example, DA, EFF and ActionSA reach a majority in Tshwane in 98% of simulations, DA, EFF and MK in
Johannesburg in 92%, ANC, EFF and MK in Ekurhuleni in 86%, and ANC, EFF and PA in Nelson Mandela
Bay in 52%. These are statements about arithmetic only and say nothing about who would agree to
govern together.

## 7. Sensitivity

The chance of no majority in the four polled metros stays above 92% in every variation, including
fundamentals alone. Buffalo City is different.

| Assumption for Buffalo City | Chance of no majority |
| --- | --- |
| No shift from fundamentals | 18% |
| Nelson Mandela Bay's shift (base) | 27% |
| Average shift of all four polled metros | 47% |

Ipsos reports that the ANC in Buffalo City "may fall short of an outright majority", without
publishing figures. This points towards the higher end of the range, and readers should treat 27%
as the centre of a wide range and not as a precise estimate.

Ekurhuleni is also fragile. Only one poll with figures enters the model, and it has the DA narrowly
ahead, while Ipsos describes the ANC as narrowly ahead.

## 8. Limitations

- The backtest rests on one election, and does not test the poll update.
- Pollsters report different groups. MarkData reports likely voters, and the others report
  registered voters.
- The latest Social Research Foundation metro samples are unpublished, so earlier sample sizes are
  used. Ipsos sample sizes are implied by its published margins of error.
- No adjustment is made for possible house effects.
- Turnout is not modelled separately, and differential turnout is absorbed into vote-share
  uncertainty.
- Errors are treated as independent across metros, so this paper makes no joint statements across
  cities.
- Late campaign changes after the most recent fieldwork are not captured.

## 9. Scoring plan

After the IEC declares results, the forecast will be scored as published, using these measures:

- **Brier score** for the no-majority and largest-party probabilities, compared with always
  predicting the 2021 outcome.
- **Mean absolute error** in vote share and seats, against the two baselines in Section 5.
- **Coverage** of the 90% ranges, which should contain about 90% of outcomes for party vote shares
  and seats.
- **Calibration**, reported with the caveat that five councils is too few for firm conclusions.

Any change of method after the forecast is frozen will be reported as a departure from this plan.

## Data and code

Code and processed data are available at [repository link, to add at freeze]. Raw IEC files are not
redistributed and can be downloaded with the provided script.

## Acknowledgements

[Yours to complete.]

## References

Aitchison, J. (1986). *The Statistical Analysis of Compositional Data*. Chapman and Hall.

Electoral Commission of South Africa. Municipal and national election results, and Seat Calculation
Detail reports. <https://results.elections.org.za/home/>

Ipsos South Africa (2026). Nationally, no party commands strong majority support as South Africa
heads into coalition territory ahead of the November Local Government Elections. Press release, 30
October 2026.

Local Government: Municipal Structures Act 117 of 1998, Schedule 1.

Poll reports: eNCA/MarkData (October 2026), News24/SABI Strategy Group (October 2026), Social
Research Foundation/The Common Sense (October 2026).
