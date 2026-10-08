# Outage verification, updates, and customer communication
Article ID: NF-SP-004
Version: 1.0
Status: Approved
Effective date: 2026-10-07
Last reviewed: 2026-10-07
Next review: 2027-01-07
Category: support_operations
Topic: incident_communication
Audience: internal_support
Classification: internal
Owner: Network Operations
Applies to: Fictional NovaFiber incident communications team
Related articles: NF-SP-001, NF-SP-002, NF-BP-003, NF-TS-002

## 1. Static guidance is not current outage evidence
This restricted staff procedure contains no live outage notice. Keep it out of customer retrieval. Current affected services, geography, incident timestamps, estimates, and restoration status belong in an authenticated outage system or approved live status feed. Do not turn an old PDF, customer report, or sample incident into a claim that an outage is happening now. Nova's current MVP has no live outage integration and must say it cannot check real-time status.

## 2. Verify before announcing an incident
Network Operations verifies correlated alarms or service observations and creates an incident record with a unique reference, owner, start time, affected scope, and verification timestamp. Distinguish a suspected issue from a confirmed provider-network fault. An individual red LOS report is insufficient to declare a regional outage. When the scope is uncertain, communicate the confirmed limitations instead of guessing a neighborhood list. Customer identifying details and internal infrastructure identifiers must not appear in public notices.

## 3. Initial customer update structure
An approved notice identifies the affected service scope at an appropriate public level, when disruption was confirmed, what customers may observe, the operational action underway, and the next update time. Only include a restoration estimate if Network Operations supplied it, with the time it was last assessed and a clear statement that it is an estimate. If no estimate exists, say it is being assessed and provide the next update commitment. Never invent a one-hour or same-day restoration promise.

## 4. Ongoing and planned updates
For a verified P1 incident, target customer updates at least hourly or sooner for a material change, matching the continuous incident workflow in NF-SP-002. If an update time will be missed, issue a revised update commitment. For planned maintenance, aim to notify affected customers at least 48 hours in advance when feasible, with the planned window in the service-address local timezone. Emergency work may not allow that notice. Planned maintenance notices are schedules, not proof of an active unplanned outage, and any credit decision still follows the verified eligibility in NF-BP-003.

## 5. Restoration and credit questions
Announce restoration only after operational checks confirm recovery, recording restoration time and remaining affected exceptions. Customers whose individual service still fails need a linked diagnostic follow-up rather than repeated generic outage reassurance. Credit eligibility requires a continuous verified provider-network outage of at least four hours, requested within 30 calendar days after restoration. Use the base-subscription/hour formula in NF-BP-003; do not promise a full-month refund or apply a credit merely because a notice was published. Avoid duplicate outage credits and unused-service refunds for the same period.

## 6. Audit and chatbot boundary
Retain approved notices, change timestamps, incident references, and decisions in the operational record. Retire stale live notices from current-status views without deleting the audit history. The knowledge base may retain this procedure but must not become a live incident database. Customer answers should use customer-approved troubleshooting plus authenticated live data once an authorized integration exists. Until then, Nova must direct current-status questions to verified support and refrain from claiming that it checked, confirmed, or resolved an outage.
