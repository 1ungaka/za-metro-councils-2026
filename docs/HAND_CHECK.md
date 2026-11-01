# Hand-Check Worksheet

Work through this with pen and paper, using a calculator. Cover the answers, and do not move on
until you can derive each step without notes. Every number is real and comes from this project.

## 1. The seat rule: Nelson Mandela Bay, 2021

The rule comes from Schedule 1, items 12 and 13, of the Municipal Structures Act. The council has
120 seats. All parties together won 523,343 valid votes on the PR and ward ballots combined.

**Step 1: the quota.** Work out Q = floor(A / B) + 1.

Answer: 523,343 / 120 = 4,361.19, so Q = 4,361 + 1 = 4,362. The IEC's report says 4,362.

**Step 2: the first round.** Divide each party's votes by Q, and keep the whole number.

| Party | Votes | Votes / Q | Round one seats | Surplus |
| --- | --- | --- | --- | --- |
| DA | 210,007 | ? | ? | ? |
| ANC | 207,443 | ? | ? | ? |
| EFF | 33,662 | ? | ? | ? |
| Northern Alliance | 11,225 | ? | ? | ? |

Answer: DA 48.145 gives 48 with surplus 0.145. ANC 47.557 gives 47 with surplus 0.557. EFF 7.717
gives 7 with surplus 0.717. Northern Alliance 2.573 gives 2 with surplus 0.573.

**Step 3: the remaining seats.** All parties together took 111 seats in round one. How many are
left, and which surpluses take them?

Answer: 9 seats remain, and they go to the nine largest surpluses. The ANC's 0.557 ranks ninth, so
it takes the last seat and reaches 48. The next surplus, 0.300, gets nothing. The DA's 0.145 is far
too small, so it stays on 48.

**The point for your paper.** The ANC had fewer votes but tied the DA on 48 seats, because the last
seat was decided by a remainder. Vote shares do not map smoothly to seats, and this is why the
model applies the exact rule to every simulated election.

**Check your understanding.** Why is the 1 added to the quota? What would happen if two parties had
exactly equal surpluses? What is item 16 for, and why can it be ignored here?

## 2. Why ward wins do not change a party's total

A party's total seats come from its combined votes. Ward wins are subtracted from that total, and
the rest are filled from its list. In 2021 the DA won 23 wards in Nelson Mandela Bay and the ANC
won 37, yet both ended on 48 seats.

**Question.** How many list seats did each party get?

Answer: DA 48 - 23 = 25, and ANC 48 - 37 = 11.

**The point for your paper.** This is why the forecast does not need a model of every ward. The
exception is a party winning more wards than its total entitlement, and that did not happen in any
of the 10 councils checked.

## 3. Fundamentals: the ANC in Johannesburg

The ANC had 33.82% in the 2021 local election and 34.06% in the 2024 national election. The weight
on the local result is 0.45.

**Step 1.** Work out f = 0.45 y + 0.55 z.

Answer: 0.45(33.82) + 0.55(34.06) = 33.95%.

**Step 2.** The final figure is 32.04%, not 33.95%. Why does it fall?

Answer: MK had no 2021 local result, so it keeps its full 2024 share, and the same goes for other
parties present in only one election. The blended shares then sum to more than 100%, so all of them
are rescaled. The ANC is pulled down by that rescaling. Work out the sum this implies:
33.95 / 32.04 = 1.06, so the raw shares summed to about 106%.

**Be ready to defend this.** A reader could argue that this new-party rule is arbitrary, so know why
halving MK would be worse.

## 4. The poll update: the ANC in Johannesburg

Everything is on the log scale, because shares are compositional. Use natural logs.

| Quantity | Symbol | Value |
| --- | --- | --- |
| Prior mean | m = ln(0.3204) | -1.1382 |
| Prior spread, from the backtest | a | 0.2464 |
| Poll mean, weighted by sample | p | -1.4834 |
| Variance of the poll mean | b^2 | 0.01435 |

**Step 1: the precisions.** Work out 1 / a^2 and 1 / b^2.

Answer: 16.47 and 69.70.

**Step 2: the posterior mean.** Work out (16.47 m + 69.70 p) / (16.47 + 69.70).

Answer: -1.4174, which is a share of e^(-1.4174) = 24.2% before closure.

**Step 3: the weight on the polls.** Work out 69.70 / (16.47 + 69.70).

Answer: 81%. Polls dominate in Johannesburg, because there are four of them and the prior is wide.
With one poll the weight falls, and with none it is zero.

**Check your understanding.** Show that the posterior of a normal prior and a normal likelihood is
normal, with precisions that add. Why does this project work on log shares and not raw shares?
Why is the common poll error of 0.10 added at all, and what happens to b^2 if it is removed?

## 5. Closure and the simulation

Each simulated election draws one log share per party, takes exponentials, and divides by their
sum. Then the exact seat rule from section 1 runs. Probabilities are simply counts: the chance of
no majority is the share of 200,000 draws in which no party reaches the needed seats.

**Question.** Why must the draws be divided by their sum, and why does this make the parties'
errors negatively related even though they were drawn independently?

## 6. Questions a lecturer may ask

Be able to answer each of these in your own words.

1. What is the single weakest assumption in this forecast?
2. Why is the backtest not evidence that the poll update works?
3. What would change your Buffalo City estimate most?
4. Why treat the metros as independent, and what claims does that rule out?
5. How will you score this forecast after the results? Name the measure.
6. The backtest used one election. Why should anyone trust the weight of 0.45?
