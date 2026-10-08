# Wi-Fi connected but websites do not load
Article ID: NF-TS-005
Version: 1.0
Status: Approved
Effective date: 2026-10-07
Last reviewed: 2026-10-07
Next review: 2027-01-07
Category: troubleshooting
Topic: wifi_no_internet
Audience: customer_assistant
Classification: approved_support
Owner: Technical Support
Applies to: NovaFiber NF-RTR-200 and household Wi-Fi devices
Related articles: NF-TS-001, NF-TS-002, NF-EQ-002, NF-EQ-003

## 1. Understand the symptom
A Wi-Fi connection confirms the device can communicate with the router, not that the router has internet service. Use this article when the Wi-Fi name is visible and connected but websites or applications fail. Check two unrelated websites and, if available, a second device. If only one website fails while others work, check that service's status instead of resetting broadband equipment.

## 2. Compare one device with the whole home
If only one device fails, confirm its Wi-Fi connection is to the intended NovaFiber network, not a disconnected extender or old hotspot. Toggle Wi-Fi off and on, then restart that device if appropriate. If you know the correct Wi-Fi password, forgetting and reconnecting to the network may help; do not share the password with Nova. Check whether an optional VPN or custom proxy is blocking that device. Restore the device's normal automatic IP/DNS settings only if you understand how to undo prior custom settings; do not disable security software.

## 3. Check optical and router indicators
If multiple devices fail, check NF-ONT-100 Power/PON/LOS and NF-RTR-200 WAN/Internet indicators. Red LOS or abnormal PON follows NF-TS-002. Normal optical registration with router Internet amber or off follows NF-TS-001. WAN off can indicate the Ethernet uplink is not established; inspect the accessible Ethernet connection between ONT LAN and router WAN without disturbing fiber. Use the supplied ports rather than changing the router into bridge mode.

## 4. Use a wired comparison when available
Connect a capable device to a router LAN port with Ethernet, keeping the ONT connection unchanged. If wired browsing succeeds, the fiber service is reachable and Wi-Fi/device configuration is the next focus. If both wired and Wi-Fi browsing fail, contact support after the permitted checks. Do not connect directly to the ONT, enter provider provisioning credentials, or perform a factory reset. If indicators are normal and safe, one controlled restart using NF-TS-001 may be tried.

## 5. Escalate with relevant evidence
Report whether one or all devices fail, whether a wired comparison worked, indicator states, the start time, and any recent network-setting changes. Account suspension and current outage status need a verified support check. Nova cannot inspect an account or confirm an outage. Do not claim that a DNS problem, unpaid bill, or cable fault is confirmed just because the device shows 'No internet'. The same symptom has several possible causes.

## 6. Validate recovery and follow related guidance
Confirm that multiple unrelated websites load after a change. A Wi-Fi signal icon by itself is insufficient. If internet works but is slow, use NF-TS-003 and NF-EQ-003. If the issue repeatedly returns, record incidents using NF-TS-004. Router password and network-name changes are described in NF-EQ-002; changing the password is not a general fix for upstream internet loss.
