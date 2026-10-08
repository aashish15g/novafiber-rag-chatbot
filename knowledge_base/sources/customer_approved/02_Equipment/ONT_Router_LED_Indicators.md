# ONT and router LED reference
Article ID: NF-EQ-001
Version: 1.0
Status: Approved
Effective date: 2026-10-07
Last reviewed: 2026-10-07
Next review: 2027-01-07
Category: equipment
Topic: indicator_lights
Audience: customer_assistant
Classification: public
Owner: Network Equipment
Applies to: Fictional NF-ONT-100 and NF-RTR-200 only
Related articles: NF-TS-001, NF-TS-002, NF-EQ-002, NF-EQ-004

## 1. Device scope and interpretation
This reference describes NovaFiber's fictional NF-ONT-100 optical network terminal and NF-RTR-200 Wi-Fi router. It is not a manual for real third-party equipment. Read the device label before interpreting an LED; behavior varies by model and firmware. Nova must not infer an optical fault from a router's generic red status light. Record the device model, indicator name, color, and whether the light is steady or blinking.

## 2. NF-ONT-100 Power and optical lights
Power steady green means the ONT has power; Power off means no detected power or a device/power fault. PON steady green means registered on the optical network. PON blinking green during startup means registration is in progress; allow up to five minutes. PON off while Power is on, or blinking beyond five minutes, needs support diagnosis. LOS off is normal. LOS blinking red means optical signal loss; use NF-TS-002 and leave fiber connectors untouched. The reference does not identify where the optical fault occurred.

## 3. NF-ONT-100 LAN indication
LAN steady green means an Ethernet link to the router exists; blinking green indicates traffic and is normal. LAN off means no Ethernet link is detected, which can result from the router being off or the accessible Ethernet uplink being disconnected. Check router power and the Ethernet plugs at ONT LAN and router WAN, without unplugging optical fiber. A LAN light by itself does not prove internet access or account authorization.

## 4. NF-RTR-200 WAN and Internet lights
Power steady green means powered on. WAN green, steady or blinking, means an Ethernet uplink is present; blinking represents traffic. WAN off means no link is detected. Internet steady green means the router's service check reports connectivity; Internet amber or off means internet service is not established. If optical registration is normal but Internet is amber, follow NF-TS-001. Do not enter provider provisioning details, alter WAN authentication, or connect a computer directly to the ONT to bypass the router.

## 5. NF-RTR-200 Wi-Fi and startup behavior
Wi-Fi green means at least one wireless band is enabled; blinking can indicate wireless traffic. Wi-Fi off means wireless service may be disabled even when wired internet works. The router normally completes startup within two minutes after the ONT is ready. Use NF-EQ-002 for the customer settings page and NF-EQ-003 for band selection. The router has no LOS or PON indicator; those belong to the ONT. A blinking traffic light is not automatically an error.

## 6. When to stop and request support
Persistent red LOS, abnormal PON after the startup allowance, inability to power equipment safely, or repeated uncommanded reboots requires support. Liquid damage, a burning smell, exposed fiber, or electrical damage means stop use and avoid handling unsafe components. Do not open either device or factory-reset it without an authorized support procedure. For other model names, consult the correct manufacturer's manual; these fictional LED meanings should not be transferred to unrelated equipment.
