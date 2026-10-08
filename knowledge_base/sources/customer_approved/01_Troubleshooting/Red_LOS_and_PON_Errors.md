# Red LOS or abnormal PON: optical connection faults
Article ID: NF-TS-002
Version: 1.0
Status: Approved
Effective date: 2026-10-07
Last reviewed: 2026-10-07
Next review: 2027-01-07
Category: troubleshooting
Topic: optical_signal
Audience: customer_assistant
Classification: approved_support
Owner: Technical Support
Applies to: NovaFiber NF-ONT-100 optical network terminal
Related articles: NF-TS-001, NF-EQ-001, NF-EQ-004

## 1. Identify the optical symptom
On the fictional NF-ONT-100, LOS off and PON steady green indicate normal optical registration. A red blinking LOS indicates loss of the optical signal. PON blinking green during startup indicates registration in progress; PON off with Power on, or PON still blinking after five minutes, requires technical diagnosis. These meanings are specific to NF-ONT-100. Check the manufacturer's manual for another ONT; NovaFiber's router does not have a LOS light.

## 2. Ask safe diagnostic questions
Confirm the device model, Power state, LOS behavior, PON state, and how long the condition has lasted. Ask whether the fault followed building work, a power interruption, or visible cable damage. Ask whether all household devices lack internet. Reports from neighbors can be useful context, but they do not establish a confirmed area outage. Only the provider's operational outage system can confirm current outage status; Nova has no live access to it.

## 3. Check power and visible cable routing
Check the supplied power adapter and a functioning outlet without opening equipment. From a safe position, visually inspect accessible fiber cable routing for crushing, sharp bends, or a cable caught beneath furniture. Do not touch exposed damaged fiber or attempt repairs. Do not unplug, reseat, inspect, or clean optical connectors, remove protective caps, or look into an optical port. Do not bend cable back into shape. See NF-EQ-004 for stop conditions.

## 4. Avoid unhelpful or unsafe resets
An active red LOS fault is not a Wi-Fi password problem. Changing the SSID, switching frequency bands, or factory-resetting the router will not restore a missing optical signal. Do not repeatedly restart the ONT for a red LOS or persistent registration fault. If the ONT is already starting after a power interruption, allow one five-minute startup period. If Power is on and PON stays off, do not assume that another restart will solve it; stop customer troubleshooting and request technical support.

## 5. Escalate a persistent optical fault
If LOS remains red or PON remains abnormal after the allowed checks and startup wait, contact verified NovaFiber support. Report the model, indicators, onset time, visible cable condition, and whether multiple devices are affected. Support must check for a known outage and remote optical/registration faults before choosing a technician visit. Customers should not obtain internal diagnostic tools, optical thresholds, or provisioning instructions from the chatbot. A confirmed outage may remove the need for an individual visit until the network fault is repaired.

## 6. Recovery and limitations
When PON becomes steady green and LOS turns off, test internet access on a wired or Wi-Fi device. If connectivity still fails, continue with NF-TS-001 rather than opening the ONT. LED states alone do not prove whether a fiber splice, splitter, building cable, or ONT is faulty. Only qualified support can determine the repair. This article explains policy and safe checks; it cannot establish the current outage status or create a technical ticket.
