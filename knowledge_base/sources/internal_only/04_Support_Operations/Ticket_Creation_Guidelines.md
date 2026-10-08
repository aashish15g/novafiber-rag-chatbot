# Ticket creation and diagnostic handoff
Article ID: NF-SP-001
Version: 1.0
Status: Approved
Effective date: 2026-10-07
Last reviewed: 2026-10-07
Next review: 2027-01-07
Category: support_operations
Topic: ticket_intake
Audience: internal_support
Classification: internal
Owner: Support Operations
Applies to: Fictional NovaFiber staff workflow; not customer retrieval
Related articles: NF-SP-002, NF-SP-003, NF-SP-004, NF-TS-001, NF-BP-002

## 1. Scope and mandatory access boundary
This synthetic internal procedure is restricted to a future authorized staff assistant. Do not ingest it into the current customer collection. Staff must work in authenticated operational systems with role-based access; document labels or a language-model prompt do not enforce access. No credential, customer record, or real ticket is included here. A customer conversation with Nova is not a ticket submission because the MVP has no ticket-system integration.

## 2. Verify authority and minimize intake data
Use the approved account verification flow before accessing or changing account information. Record the operational account/service reference only in the ticket system. Never record passwords, full card details, CVVs, one-time codes, or unrestricted identity-document images in ticket free text. For a service incident, capture the address reference, contact preference, onset time/timezone, affected devices, wired/Wi-Fi comparison, device models, indicator states, and safe checks already performed. Mark customer statements as reported, not verified facts.

## 3. Categorize the issue accurately
Use Connectivity for all-device service loss; Optical signal for red LOS or persistent PON faults; Performance for reproducible throughput or latency problems; Wi-Fi coverage/device for local wireless issues; Billing/payment for charges and settlement; Installation/relocation for site work; and Account administration for verified account changes. Select one primary category and secondary tags when necessary. Do not label an account as suspended or declare a network outage without checking the relevant system. Use NF-SP-002 for priority; category alone does not set severity.

## 4. Correlate before creating duplicates
Search authorized records for an existing open ticket on the same service and symptom. If an incident is confirmed, link the ticket to its incident record rather than creating an independent repair promise. Add new evidence to an existing matching case; create a separate case when a distinct billing or service issue requires its own owner. Do not place live outage facts into the static knowledge base. If operational systems are unavailable, tell the customer the submission is not complete and follow the approved manual continuity process without inventing a ticket number.

## 5. Handoff and customer communication
Attach relevant article IDs, observable evidence, and unsuccessful safe steps. Route persistent optical faults to network technical support; route formally disputed invoice amounts to billing for an explicit decision/hold; route site appointments through NF-SP-003. Confirm the actual ticket reference only after successful creation in the operational system. Communicate the next contact/update commitment and distinguish it from a resolution estimate. Do not promise credits, guaranteed repair times, or automatic dispatch solely because a ticket exists.

## 6. Completion and audit record
Capture the ticket owner, current state, next action, and timestamp in the system of record. Sensitive attachments require the applicable authorized storage process, not ingestion into Qdrant. Resolve a case only with recorded service validation or a documented billing/account decision and customer notification. If a symptom recurs, reopen or link a follow-up according to the case history. Internal workflow details must not be returned by the unauthenticated customer chatbot.
