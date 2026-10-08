# Slow internet speeds: distinguish Wi-Fi from line performance
Article ID: NF-TS-003
Version: 1.0
Status: Approved
Effective date: 2026-10-07
Last reviewed: 2026-10-07
Next review: 2027-01-07
Category: troubleshooting
Topic: throughput
Audience: customer_assistant
Classification: approved_support
Owner: Technical Support
Applies to: NovaFiber residential plans and NF-RTR-200
Related articles: NF-BP-001, NF-EQ-003, NF-TS-004

## 1. Define the performance problem
Record the subscribed plan, affected devices, wired versus Wi-Fi behavior, test times, and whether slowness affects all applications. Advertised plan rates are up to Mbps, not guaranteed Wi-Fi speeds or file-download MB/s. Roughly eight megabits equal one megabyte before protocol overhead. A slow remote website, VPN, older device, or busy household can constrain a test without proving a NovaFiber network fault.

## 2. Establish a useful baseline
Use a capable computer connected directly to a LAN port of the NF-RTR-200 with a Cat5e or better Ethernet cable. Do not connect directly to the ONT or change provisioning. Check that the computer reports a 1 Gbps Ethernet link when testing plans above 100 Mbps. A 100 Mbps link cannot measure a 300, 600, or 1000 Mbps plan properly. Pause household downloads, cloud backups, video streams, and optional VPN use during a short diagnostic test; avoid disabling security software.

## 3. Compare repeatable measurements
Run three measurements with the same speed-test service and nearby test location, several minutes apart. Record download/upload Mbps, latency, date, time, and whether the test was wired. For the Gig 1000 plan, around 940 Mbps can be a normal maximum application-level result through a 1 Gbps Ethernet link; it is not proof of under-delivery. NovaFiber's diagnostic trigger is repeated wired results below 70% of the plan's nominal rate under the controlled conditions above. This is an investigation trigger, not a contractual minimum or automatic credit entitlement.

## 4. Diagnose Wi-Fi-specific slowness
If wired performance is substantially better, test near the router on 5 GHz with a compatible device. Move the router into an open, central position away from metal cabinets and large appliances. Use 2.4 GHz for longer reach when 5 GHz is weak; a stronger signal can still have lower throughput. Walls, interference, device capability, and shared airtime affect Wi-Fi. Use NF-EQ-003 rather than assuming every slow Wi-Fi test needs a plan upgrade.

## 5. Report recurring evening degradation
For evening-only slowness, compare controlled wired tests during the affected evening period and at another time over two days when practical. Do not delay support if connectivity is unusable or the customer cannot perform tests. Supply timestamps and results, not account passwords. Support investigates line performance, equipment, local usage, and possible network congestion. The chatbot must not state that congestion is confirmed solely because the problem occurs at night.

## 6. Escalation and next evidence
Contact verified support for repeated controlled wired results below the diagnostic trigger, unexplained latency across several services, or inability to complete the checks. Send the plan name, device/link speed, sample measurements, and steps taken. Follow NF-TS-004 if the connection drops rather than merely slowing. No upgrade, speed guarantee, or refund is authorized by a test result alone; refund and outage credit rules are defined in NF-BP-003.
