-- Test Classification Queries for Dashboard #6
-- Purpose: Validate incident classification logic before dashboard creation

-- Test 1: Primary Classification (Cloud, Telecommunications, Networking)
SELECT 'PRIMARY CLASSIFICATION TEST' as test_name;

WITH classified_tickets AS (
  SELECT
    "TKT-Ticket ID",
    "TKT-Title",
    "TKT-Description",
    "TKT-Created Time",
    CASE
      -- Telecommunications (check first)
      WHEN (
        LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", ''))
        ~* '(phone|pbx|call|calling|voip|sip|3cx|teams? meeting|meeting room|conference|video call|audio|microphone|speaker|headset|dial|extension|voicemail|trunk|telecom|telephony|skype|webex|zoom|collaboration)'
      ) THEN 'Telecommunications'

      -- Networking (exclude file shares)
      WHEN (
        LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", ''))
        ~* '(vpn|firewall|switch|router|wan|lan|uplink|bandwidth|wifi|wireless|vlan|subnet|gateway|routing|meraki|cisco|switch port|cable|ethernet|network connectivity|internet down|connection lost|offline|disconnected)'
        AND LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", ''))
        !~* '(network drive|mapped drive|share|file server|nas|shared folder)'
      ) THEN 'Networking'

      -- Cloud (default + file shares)
      ELSE 'Cloud'
    END AS category
  FROM servicedesk.tickets
  WHERE "TKT-Category" <> 'Alert'
  AND "TKT-Created Time" >= '2025-07-01'
  AND "TKT-Created Time" <= '2025-10-13'
)
SELECT
  category,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM classified_tickets
GROUP BY category
ORDER BY count DESC;

-- Test 2: Networking Sub-Categories
SELECT 'NETWORKING SUB-CATEGORIES TEST' as test_name;

WITH networking_tickets AS (
  SELECT
    "TKT-Ticket ID",
    "TKT-Title",
    "TKT-Description"
  FROM servicedesk.tickets
  WHERE "TKT-Category" <> 'Alert'
  AND "TKT-Created Time" >= '2025-07-01'
  AND "TKT-Created Time" <= '2025-10-13'
  AND (
    LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", ''))
    ~* '(vpn|firewall|switch|router|wan|lan|uplink|bandwidth|wifi|wireless|vlan|subnet|gateway|routing|meraki|cisco|switch port|cable|ethernet|network connectivity|internet down|connection lost|offline|disconnected)'
    AND LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", ''))
    !~* '(network drive|mapped drive|share|file server|nas|shared folder)'
  )
)
SELECT
  CASE
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(switch|router|cisco|meraki|port)' THEN 'Switch/Router Hardware'
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(connectivity|connection|internet|offline|disconnected)' THEN 'Network Connectivity'
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(vpn|remote access|remote desktop|rdp)' THEN 'VPN/Remote Access'
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(firewall|blocked|access denied|security group)' THEN 'Firewall/Security'
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(wifi|wireless|ssid|wlan)' THEN 'Wi-Fi/Wireless'
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(dns|dhcp|name resolution|ip address)' THEN 'DNS/DHCP'
    ELSE 'Other Networking'
  END as subcategory,
  COUNT(*) as count
FROM networking_tickets
GROUP BY 1
ORDER BY count DESC;

-- Test 3: Telecommunications Sub-Categories
SELECT 'TELECOMMUNICATIONS SUB-CATEGORIES TEST' as test_name;

WITH telecom_tickets AS (
  SELECT
    "TKT-Ticket ID",
    "TKT-Title",
    "TKT-Description"
  FROM servicedesk.tickets
  WHERE "TKT-Category" <> 'Alert'
  AND "TKT-Created Time" >= '2025-07-01'
  AND "TKT-Created Time" <= '2025-10-13'
  AND (
    LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", ''))
    ~* '(phone|pbx|call|calling|voip|sip|3cx|teams? meeting|meeting room|conference|video call|audio|microphone|speaker|headset|dial|extension|voicemail|trunk|telecom|telephony|skype|webex|zoom|collaboration)'
  )
)
SELECT
  CASE
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(call|calling|dial|voip|extension|voicemail)' THEN 'Calling Issues'
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(teams|meeting|video|conference|webex|zoom)' THEN 'Teams/Video Conferencing'
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(pbx|3cx|phone system|telephony|trunk|sip)' THEN 'PBX/Phone System'
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(meeting room|room|conference room|audio|microphone|speaker)' THEN 'Meeting Room Equipment'
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(collaboration|skype|chat)' THEN 'Collaboration Tools'
    ELSE 'Other Telecom'
  END as subcategory,
  COUNT(*) as count
FROM telecom_tickets
GROUP BY 1
ORDER BY count DESC;

-- Test 4: Cloud - File Shares vs Other
SELECT 'CLOUD SUB-CATEGORIES TEST' as test_name;

WITH cloud_tickets AS (
  SELECT
    "TKT-Ticket ID",
    "TKT-Title",
    "TKT-Description"
  FROM servicedesk.tickets
  WHERE "TKT-Category" <> 'Alert'
  AND "TKT-Created Time" >= '2025-07-01'
  AND "TKT-Created Time" <= '2025-10-13'
  AND (
    -- Not Telecommunications
    LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", ''))
    !~* '(phone|pbx|call|calling|voip|sip|3cx|teams? meeting|meeting room|conference|video call|audio|microphone|speaker|headset|dial|extension|voicemail|trunk|telecom|telephony|skype|webex|zoom|collaboration)'
  )
  AND (
    -- Not Networking (or is file shares)
    LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", ''))
    !~* '(vpn|firewall|switch|router|wan|lan|uplink|bandwidth|wifi|wireless|vlan|subnet|gateway|routing|meraki|cisco|switch port|cable|ethernet|network connectivity|internet down|connection lost|offline|disconnected)'
    OR LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", ''))
    ~* '(network drive|mapped drive|share|file server|nas|shared folder)'
  )
)
SELECT
  CASE
    WHEN LOWER("TKT-Title" || ' ' || COALESCE("TKT-Description", '')) ~* '(network drive|mapped drive|share|file server|nas|shared folder)' THEN 'File Share Issues'
    ELSE 'Other Cloud Services'
  END as subcategory,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM cloud_tickets
GROUP BY 1
ORDER BY count DESC;

-- Test 5: Verify Total Count
SELECT 'TOTAL COUNT VERIFICATION' as test_name;

SELECT COUNT(*) as total_incidents
FROM servicedesk.tickets
WHERE "TKT-Category" <> 'Alert'
AND "TKT-Created Time" >= '2025-07-01'
AND "TKT-Created Time" <= '2025-10-13';
