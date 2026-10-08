# Frequent disconnections: capture and isolate the fault
Article ID: NF-TS-004
Version: 1.0
Status: Approved
Effective date: 2026-10-07
Last reviewed: 2026-10-07
Next review: 2027-01-07
Category: troubleshooting
Topic: intermittent_connection
Audience: customer_assistant
Classification: approved_support
Owner: Technical Support
Applies to: NovaFiber residential fiber and supplied equipment
Related articles: NF-TS-002, NF-TS-003, NF-TS-005, NF-EQ-004

## 1. Recognize an intermittent connection
Use this article when internet access repeatedly stops and recovers, including dropouts during calls, streaming, or gaming. Distinguish losing the Wi-Fi network from remaining connected to Wi-Fi while internet access disappears. A dropped application session alone is not proof of a broadband dropout. Record whether other websites and devices fail at the same moment.

## 2. Capture a short incident record
For each observed incident, note local time, approximate duration, affected devices, wired/Wi-Fi connection, and ONT/router indicator changes. If useful, record two or three incidents over 24 hours, but do not wait to seek support for severe disruption. Note router/ONT restarts, recent equipment moves, new devices, or electrical interruptions. A screenshot of a generic connection error is useful; exclude private messages, passwords, and account codes.

## 3. Choose a branch using concurrent symptoms
If Power indicators turn off during each drop, inspect the supplied power connection and outlet for a loose accessible adapter; do not repair wiring. If LOS flashes red or PON loses its normal steady green state, stop restart experiments and follow NF-TS-002. If a wired device stays online while Wi-Fi devices drop, examine Wi-Fi coverage and interference using NF-EQ-003. If only one device drops, check that device's network settings or seek device-vendor guidance before declaring a line fault.

## 4. Use limited corrective checks
With normal optical indicators and no visible damage, a single controlled restart following NF-TS-001 may be tried. Place the router upright in a ventilated, open location and keep its vents unobstructed. Inspect accessible Ethernet plugs for a loose fit without touching the fiber connector. Try a known-good Ethernet cable if available. Do not factory-reset equipment, install unofficial firmware, disable security protections, or perform continuous automated resets. Excessive restarts erase useful fault timing and can delay diagnosis.

## 5. Escalate repeated or unsafe symptoms
Contact verified support if two or more all-device outages occur within 24 hours, if a single unexplained disconnection lasts more than 15 minutes, or if the connection remains unusable. These are reporting thresholds, not reasons to deny earlier help. Visible damaged fiber, liquid exposure, a burning smell, or overheating warrants immediate stop-and-report behavior. Provide incident times, indicator states, and completed checks so support can correlate operational records and decide whether replacement or a visit is needed.

## 6. Confirm improvement without inventing a cause
After a change, observe whether the same symptoms recur under ordinary use and record the outcome. Support may need longer monitoring to isolate an intermittent network or equipment problem. Nova cannot see historical line alarms or confirm a live outage, and must not promise that a restart permanently fixed the fault. Normal optical lights plus poor throughput should lead to NF-TS-003, while Wi-Fi-only failures should lead to NF-TS-005.
