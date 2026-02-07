# Reference: templates

## Propósito
Templates prontos para configurações comuns. O LLM usa estes como base
e ajusta conforme o pedido do usuário.

---

## SSID Templates

### Guest WiFi (PSK + Splash)
```yaml
template: ssid-guest-psk
name: "Guest-WiFi"
enabled: true
authMode: "psk"
encryptionMode: "wpa"
wpaEncryptionMode: "WPA2 only"
psk: "${GENERATED_PSK}"
splashPage: "Click-through splash page"
bandSelection: "Dual band operation with band steering"
perClientBandwidthLimitUp: 5000      # 5 Mbps
perClientBandwidthLimitDown: 5000     # 5 Mbps
ipAssignmentMode: "NAT mode"
visible: true
availableOnAllAps: true
```

### Corporate WiFi (802.1X RADIUS)
```yaml
template: ssid-corporate-8021x
name: "Corporate"
enabled: true
authMode: "8021x-radius"
encryptionMode: "wpa"
wpaEncryptionMode: "WPA2 only"
radiusServers:
  - host: "${RADIUS_IP}"
    port: 1812
    secret: "${RADIUS_SECRET}"
bandSelection: "5 GHz band only"
perClientBandwidthLimitUp: 0          # Unlimited
perClientBandwidthLimitDown: 0         # Unlimited
ipAssignmentMode: "Bridge mode"
visible: true
useVlanTagging: true
defaultVlanId: "${CORP_VLAN_ID}"
```

### IoT WiFi (PSK + Isolated)
```yaml
template: ssid-iot
name: "IoT-Devices"
enabled: true
authMode: "psk"
encryptionMode: "wpa"
wpaEncryptionMode: "WPA2 only"
psk: "${IOT_PSK}"
splashPage: "None"
bandSelection: "Dual band operation"
perClientBandwidthLimitUp: 1000       # 1 Mbps
perClientBandwidthLimitDown: 1000      # 1 Mbps
ipAssignmentMode: "Bridge mode"
visible: false                         # Hidden SSID
lanIsolationEnabled: true              # Client isolation
useVlanTagging: true
defaultVlanId: "${IOT_VLAN_ID}"
```

---

## ACL Templates

### Block Insecure Protocols
```yaml
template: acl-block-insecure
rules:
  - policy: deny
    protocol: tcp
    srcCidr: "any"
    dstCidr: "any"
    dstPort: "23"
    comment: "Block Telnet"
  - policy: deny
    protocol: tcp
    srcCidr: "any"
    dstCidr: "any"
    dstPort: "21"
    comment: "Block FTP"
  - policy: deny
    protocol: udp
    srcCidr: "any"
    dstCidr: "any"
    dstPort: "69"
    comment: "Block TFTP"
  - policy: allow
    protocol: any
    srcCidr: "any"
    dstCidr: "any"
    comment: "Allow all other traffic"
```

### Restrict Server VLAN
```yaml
template: acl-restrict-server-vlan
rules:
  - policy: allow
    protocol: tcp
    srcCidr: "${MGMT_SUBNET}"
    dstCidr: "${SERVER_SUBNET}"
    dstPort: "22"
    comment: "Allow SSH from management"
  - policy: allow
    protocol: tcp
    srcCidr: "any"
    dstCidr: "${SERVER_SUBNET}"
    dstPort: "443"
    comment: "Allow HTTPS"
  - policy: allow
    protocol: tcp
    srcCidr: "any"
    dstCidr: "${SERVER_SUBNET}"
    dstPort: "80"
    comment: "Allow HTTP"
  - policy: deny
    protocol: any
    srcCidr: "any"
    dstCidr: "${SERVER_SUBNET}"
    comment: "Deny all other to servers"
  - policy: allow
    protocol: any
    srcCidr: "any"
    dstCidr: "any"
    comment: "Allow all other traffic"
```

---

## Firewall L3 Templates

### Block Outbound to Known Bad Ports
```yaml
template: fw-block-bad-ports
rules:
  - comment: "Block Telnet outbound"
    policy: deny
    protocol: tcp
    destPort: "23"
    destCidr: "any"
    srcCidr: "any"
  - comment: "Block RDP outbound"
    policy: deny
    protocol: tcp
    destPort: "3389"
    destCidr: "any"
    srcCidr: "any"
  - comment: "Block SMB outbound"
    policy: deny
    protocol: tcp
    destPort: "445"
    destCidr: "any"
    srcCidr: "any"
  - comment: "Default Allow"
    policy: allow
    protocol: any
    destPort: "any"
    destCidr: "any"
    srcCidr: "any"
```

### Allow Specific VLAN to Internet
```yaml
template: fw-vlan-internet
rules:
  - comment: "Allow ${VLAN_NAME} DNS"
    policy: allow
    protocol: udp
    destPort: "53"
    destCidr: "any"
    srcCidr: "${VLAN_CIDR}"
  - comment: "Allow ${VLAN_NAME} HTTPS"
    policy: allow
    protocol: tcp
    destPort: "443"
    destCidr: "any"
    srcCidr: "${VLAN_CIDR}"
  - comment: "Allow ${VLAN_NAME} HTTP"
    policy: allow
    protocol: tcp
    destPort: "80"
    destCidr: "any"
    srcCidr: "${VLAN_CIDR}"
  - comment: "Deny ${VLAN_NAME} all other"
    policy: deny
    protocol: any
    destPort: "any"
    destCidr: "any"
    srcCidr: "${VLAN_CIDR}"
```

---

## VLAN Templates

### Standard VLAN
```yaml
template: vlan-standard
id: "${VLAN_ID}"
name: "${VLAN_NAME}"
subnet: "${SUBNET}"
applianceIp: "${GATEWAY_IP}"
dhcpHandling: "Run a DHCP server"
dhcpLeaseTime: "1 day"
dnsNameservers: "upstream_dns"
```

### IoT VLAN (Isolated)
```yaml
template: vlan-iot
id: "${VLAN_ID}"
name: "IoT-${LOCATION}"
subnet: "${SUBNET}"
applianceIp: "${GATEWAY_IP}"
dhcpHandling: "Run a DHCP server"
dhcpLeaseTime: "12 hours"
dnsNameservers: "${DNS_SERVERS}"
dhcpOptions:
  - code: "15"
    type: "text"
    value: "iot.local"
```

---

## NAT Templates

### 1:1 NAT for Web Server
```yaml
template: nat-1to1-webserver
name: "Web Server NAT"
lanIp: "${SERVER_INTERNAL_IP}"
publicIp: "${PUBLIC_IP}"
uplink: "internet1"
allowedInbound:
  - protocol: tcp
    destinationPorts: "443"
    allowedIps: "any"
  - protocol: tcp
    destinationPorts: "80"
    allowedIps: "any"
```

### Port Forwarding
```yaml
template: port-forwarding
name: "${SERVICE_NAME}"
lanIp: "${SERVER_INTERNAL_IP}"
localPort: "${LOCAL_PORT}"
publicPort: "${PUBLIC_PORT}"
protocol: "tcp"
uplink: "both"
allowedIps: ["any"]
```

---

## Uso dos Templates

O LLM deve:
1. Selecionar template mais próximo do pedido do usuário
2. Substituir variáveis `${...}` com valores do contexto ou perguntar ao usuário
3. Ajustar campos conforme necessário
4. Mostrar no preview antes de aplicar
