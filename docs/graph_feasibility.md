# Graph Analysis and GNN Feasibility Assessment

## Objective

Evaluate whether PaySim account relationships provide an explainable graph-based fraud-risk signal and whether a graph neural network is justified for this project.

## Graph representation

- **Nodes:** PaySim sender and receiver account identifiers (`nameOrig`, `nameDest`)
- **Directed edges:** Transactions from sender to receiver
- **Edge attributes:** Transaction count, total amount, average amount, historical fraud count, fraud rate, first step, and last step
- **Initial graph window:** First 200,000 chronological transaction rows, covering simulation steps 1 through 13

## Explainable NetworkX investigation graph

The NetworkX graph analysis produced:

| Metric | Result |
|---|---:|
| Transaction rows analysed | 200,000 |
| Fraud-labelled transactions in window | 147 |
| Account nodes | 294,797 |
| Directed relationships | 200,000 |
| Weakly connected components | 94,797 |
| Largest weakly connected component | 85 accounts |
| Fraud-linked relationships | 147 |

The graph was used for retrospective investigation analysis. Fraud-linked accounts and relationships are treated as investigation candidates only. Graph connectivity does not prove that accounts belong to a confirmed fraud ring.

## Leakage-safe graph features

For a transaction at simulation step \(t\), graph features were calculated using only transactions from steps strictly earlier than \(t\). No transaction at the current step was allowed to influence another transaction's features because PaySim does not provide within-step ordering.

Implemented prior-only features:

- Sender prior out-degree
- Receiver prior in-degree
- Sender prior outgoing transaction count
- Receiver prior incoming transaction count
- Prior sender-receiver transaction count
- Prior sender-receiver total amount

## Signal coverage

Within the first 200,000 chronological transactions:

| Feature | Rows with nonzero value |
|---|---:|
| Sender prior out-degree | 4 |
| Receiver prior in-degree | 85,591 |
| Sender prior outgoing transaction count | 4 |
| Receiver prior incoming transaction count | 85,591 |
| Prior sender-receiver transaction count | 0 |
| Prior sender-receiver total amount | 0 |

The recurring structure in this PaySim window is almost entirely receiver-side activity. Sender recurrence and repeated sender-receiver relationships are effectively absent.

## Fraud-rate comparison

| Graph signal availability | Transactions | Fraud cases | Fraud rate |
|---|---:|---:|---:|
| No nonzero prior graph feature | 114,406 | 113 | 0.0988% |
| At least one nonzero prior graph feature | 85,594 | 34 | 0.0397% |

Transactions with a nonzero historical graph feature had a lower observed fraud rate in this sample. Therefore, the available graph features do not support a positive graph-based fraud-risk score.

## GNN decision

A PyTorch Geometric graph neural network was not implemented for the initial delivery because the available PaySim account graph is sparse for relationship learning in the evaluated chronological window:

- Sender account reuse is rare.
- Repeated sender-receiver pairs are absent.
- The graph is highly fragmented.
- The only recurring structure, receiver-side history, is negatively associated with fraud in the observed window.
- There is no experimental evidence that a GNN would improve on the XGBoost model.

Adding a GNN without supportive data or measured improvement would introduce complexity without a defensible benefit.

## Final graph approach

The project retains:

- Explainable NetworkX account-relationship analysis.
- Historical fraud-linked relationship summaries for retrospective analyst investigation.
- Leakage-safe graph feature generation and tests.
- A documented decision not to add graph features or GNN risk to the production XGBoost score.

## Limitations

PaySim is synthetic and has limited genuine relationship context. It does not provide device, IP, geolocation, merchant, or verified customer-network information. A production fraud-ring system would require richer entity-resolution, temporal transaction histories, and externally validated investigation labels.