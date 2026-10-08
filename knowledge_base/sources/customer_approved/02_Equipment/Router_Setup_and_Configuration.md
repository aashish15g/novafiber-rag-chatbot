# Router setup and customer configuration
Article ID: NF-EQ-002
Version: 1.0
Status: Approved
Effective date: 2026-10-07
Last reviewed: 2026-10-07
Next review: 2027-01-07
Category: equipment
Topic: router_setup
Audience: customer_assistant
Classification: public
Owner: Network Equipment
Applies to: Fictional NF-RTR-200 with NF-ONT-100
Related articles: NF-EQ-001, NF-EQ-003, NF-EQ-004, NF-TS-005

## 1. What customers may configure
NovaFiber completes fiber installation and ONT activation through an authorized technician. Customers may connect devices, choose Wi-Fi names and passwords, enable the guest network, and improve router placement. Customers must not change optical provisioning, WAN authentication, VLAN settings, bridge mode, or provider firmware. This article contains no shared administrator password, provider credential, or activation secret.

## 2. Connect equipment after installation
Leave the installed fiber cable and optical connector undisturbed. Connect the ONT's Ethernet LAN port to the router's WAN port using the supplied Ethernet cable. Use the supplied power adapters. Power on the ONT and wait up to five minutes for steady green PON with LOS off, then power on the router and wait up to two minutes. If optical indicators do not normalize, stop and follow NF-TS-002. Wired devices connect to the router's LAN ports, not directly to the ONT.

## 3. Choose safe placement and initial Wi-Fi
Place the router in an open, central, raised location with ventilation. Avoid metal cabinets, floor corners, and placement behind large appliances. Connect using the unique Wi-Fi name and password on the installed equipment label or customer handover record. Verify that the label belongs to your router. Do not send the password or a photograph of the full label to Nova, and do not reuse a banking or email password for Wi-Fi.

## 4. Change customer settings locally
On a device connected to the router, use the local management address and unique administrator credentials shown in the equipment handover instructions. No universal address or password is prescribed here. Enter credentials only into the verified local device interface. Set a descriptive network name that does not expose an address or full personal name, and a unique Wi-Fi password of at least 12 characters. Use WPA2-AES or WPA3-Personal where supported. Changing the Wi-Fi password disconnects devices until they reconnect with the new password.

## 5. Guest access and equipment replacement
For visitors, enable a separate guest network using its own password and local-network isolation if available. Do not share the router administrator credential. If a management password is lost, contact verified NovaFiber support; a chatbot cannot reset it. Supplied equipment is loaned. For a fault not caused by misuse, support diagnoses it before arranging a no-charge standard replacement. Customer-caused damage or non-return charges follow NF-BP-003 and NF-GF-001, not an automatic fee for every reported fault.

## 6. Restart versus factory reset
A controlled power restart preserves settings and is described in NF-TS-001. Pressing a reset pin/button may erase settings and is not an approved first-line customer action. Do not install unofficial firmware or expose the management interface to the internet. If Wi-Fi connects without internet, use NF-TS-005; if Wi-Fi range is weak, use NF-EQ-003. The assistant explains steps but cannot log into equipment or change settings on the customer's behalf.
