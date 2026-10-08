# No internet connection: safe first checks
Article ID: NF-TS-001
Version: 1.0
Status: Approved
Effective date: 2026-10-07
Last reviewed: 2026-10-07
Next review: 2027-01-07
Category: troubleshooting
Topic: complete_connection_loss
Audience: customer_assistant
Classification: approved_support
Owner: Technical Support
Applies to: NovaFiber residential service; NF-ONT-100 and NF-RTR-200
Related articles: NF-TS-002, NF-TS-005, NF-EQ-001, NF-EQ-004

## 1. Recognize a complete connection loss
Use this procedure when no household device can browse or use internet applications. A single failing device or website is not proof that the fiber connection is down. NovaFiber's ONT receives the fiber signal; the router distributes that connection over Ethernet and Wi-Fi. A powered router can still broadcast Wi-Fi while the upstream connection is unavailable.

## 2. Record symptoms before changing anything
Check whether one device or all devices are affected, whether both wired and Wi-Fi connections fail, when the problem started, and the Power, PON, LOS, WAN, and Internet indicator states. Note recent power interruptions, cable movement, or equipment changes. Do not share an account password, payment-card number, Wi-Fi password, or authentication code with a chatbot. Current regional outages and account suspension status require a verified support channel; Nova cannot look them up.

## 3. Select the correct diagnostic path
If LOS is red or PON never becomes steady green, follow NF-TS-002. Do not perform repeated restarts or disconnect optical connectors. If Power is off, check the supplied adapter and a known-working outlet; do not open the device. If the fiber indicators are normal but only Wi-Fi devices fail, follow NF-TS-005. A damaged cable, burning smell, liquid exposure, or unusually hot equipment requires stopping use and seeking support; do not handle unsafe equipment.

## 4. Restart safely only when permitted
When Power and PON are normal, LOS is off, and no damaged equipment is visible, one controlled restart may be tried. Turn off the router, then the ONT using their power switches or power adapters. Leave fiber connectors untouched. Wait 30 seconds. Power on the ONT and allow up to five minutes for PON to become steady green. If optical indicators remain abnormal, stop and follow NF-TS-002. Otherwise power on the router, wait up to two minutes, then test one website on a wired device and one Wi-Fi device. A factory reset is not a restart and is not an approved customer troubleshooting step.

## 5. Request help when checks fail
If all devices still fail after the permitted checks, contact NovaFiber through the verified support contact in the account portal or service agreement. Provide the symptom, onset time, indicator states, and checks completed. If an outage is confirmed by support, follow the announced update instead of requesting duplicate appointments. Technician appointments depend on diagnosis and available slots; the chatbot cannot dispatch anyone or promise a repair time.

## 6. Expected outcome and evidence
A successful recovery means more than a Wi-Fi symbol: at least one device can load multiple websites. If service returns only briefly, record the recurrence and use NF-TS-004. Keep the diagnostic record separate from account credentials. Related references: NF-EQ-001 for device-specific LEDs; NF-EQ-004 for fiber safety; NF-TS-002 for optical faults; NF-TS-005 for Wi-Fi-only failures.
