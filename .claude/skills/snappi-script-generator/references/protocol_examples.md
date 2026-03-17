# Snappi Protocol Configuration Examples

Reference examples extracted from: https://github.com/open-traffic-generator/snappi

**Table of Contents:**
1. BGP Configuration (IPv4)
2. BGP Configuration (IPv6 + Dual Stack)
3. ISIS Configuration
4. LACP LAG Configuration
5. VLAN Tagged Traffic
6. QinQ (Double-Tagged VLAN)
7. BGP with Route Aggregation
8. BGP Communities and Attributes
9. Traffic Rate Patterns
10. Metrics Filtering Examples

---

## 1. BGP Configuration (IPv4)

From: `tests/test_device_stack.py`

```python
config = api.config()
p1, p2 = config.ports.port(name='p1').port(name='p2')

# Device setup
d = config.devices.device(name='d')[0]
e = d.ethernets.ethernet()[0]
e.connection.port_name = p1.name
e.name = 'eth1'
e.mac = '00:01:00:00:00:01'

# IPv4 addressing
i4 = e.ipv4_addresses.ipv4()[0]
i4.name = 'ipv4_1'
i4.address = '1.1.1.1'
i4.gateway = '1.1.1.2'
i4.prefix = 24

# BGP configuration
d.bgp.router_id = "192.168.1.1"
b4 = d.bgp.ipv4_interfaces.v4interface()[0]
b4.ipv4_name = i4.name

# BGP peer
peer = b4.peers.v4peer()[0]
peer.name = "bgp_peer_v4"
peer.peer_address = '1.1.1.2'
peer.as_number = 65001
peer.as_type = peer.IBGP

# Advertise routes
route_range = peer.v4_routes.v4routerange(name="routes_v4")[0]
route_range.addresses.v4address(address='10.0.0.1', prefix=32, count=100, step=1)

api.set_config(config)
```

**Key Points:**
- Router ID is global per device
- IPv4 interface references IPv4 address by name
- Peers reference interface by index or name
- Routes configured per peer
- AS type: EBGP or IBGP

---

## 2. BGP Configuration (IPv6 + Dual Stack)

From: `tests/test_device_stack.py`

```python
# Continue from previous device setup

# IPv6 addressing
i6 = e.ipv6_addresses.ipv6()[0]
i6.name = 'ipv6_1'
i6.address = '2001::1'
i6.gateway = '2001::2'
i6.prefix = 64

# BGP IPv6 interface
b6 = d.bgp.ipv6_interfaces.v6interface()[0]
b6.ipv6_name = i6.name

# BGP IPv6 peer
peer_v6 = b6.peers.v6peer()[0]
peer_v6.peer_address = '2001::2'
peer_v6.as_number = 65001
peer_v6.as_type = 'ibgp'
peer_v6.name = "bgp_peer_v6"

# Advertise IPv6 routes
route_range_v6 = peer_v6.v6_routes.v6routerange(name="routes_v6")[0]
route_range_v6.addresses.v6address(address='2001:1::1', prefix=64, count=100, step=1)
```

---

## 3. ISIS Configuration

**Pattern from OTG specification:**

```python
config = api.config()
p1 = config.ports.port(name='p1')[0]

# Device setup
d = config.devices.device(name='isis_device')[0]
e = d.ethernets.ethernet()[0]
e.connection.port_name = p1.name
e.mac = '00:00:00:00:00:01'

# IPv4 addressing
i4 = e.ipv4_addresses.ipv4()[0]
i4.address = '10.0.0.1'
i4.gateway = '10.0.0.2'
i4.prefix = 24

# ISIS configuration
isis = d.isis
isis.name = 'isis_device'
isis.system_id = '0000000000001'  # 6-byte system ID

# ISIS interface
isis_int = isis.interfaces.interface()[0]
isis_int.ethernet_name = e.name
isis_int.level_type = isis_int.LEVEL_1_2
isis_int.hello_interval = 10
isis_int.dead_interval = 30

# ISIS router
router = isis.routers.router()[0]
router.name = 'isis_router'

# ISIS route
route = router.ipv4_routes.ipv4route()[0]
route.address = '192.168.0.0'
route.prefix = 24

api.set_config(config)
```

---

## 4. LACP LAG Configuration

From: `tests/test_lag.py`

```python
config = api.config()

# Create ports to be aggregated
p1, p2, p3 = (config.ports
    .port(name='p1')
    .port(name='p2')
    .port(name='p3')
)

# Create LAG
lag = config.lags.lag(name='lag1')[0]
lacp = lag.protocol.lacp

# Configure LACP
lacp.actor_system_id = '00:00:0A:00:00:01'  # System MAC
lacp.actor_key = 1                           # LAG number

# Add ports to LAG
for port in config.ports:
    lag_port = lag.ports.port(port_name=port.name)[0]
    lag_port.ethernet.name = f'eth_{port.name}'
    lag_port.ethernet.mac = '00:00:01:00:00:01'
    lag_port.lacp.actor_port_number = 10

# Device on LAG
d = config.devices.device(name='device_on_lag')[0]
e = d.ethernets.ethernet()[0]
e.connection.lag_name = lag.name  # Connect to LAG
e.mac = '00:00:02:00:00:01'

# IP on device
i4 = e.ipv4_addresses.ipv4()[0]
i4.address = '192.168.1.1'
i4.gateway = '192.168.1.2'
```

---

## 5. VLAN Tagged Traffic

```python
config = api.config()
p1, p2 = config.ports.port(name='p1').port(name='p2')

# Device with VLAN
d = config.devices.device(name='vlan_device')[0]
e = d.ethernets.ethernet()[0]
e.connection.port_name = p1.name
e.mac = '00:00:00:00:00:01'

# VLAN interface
vlan = e.vlans.vlan()[0]
vlan.vlan_id = 100
vlan.name = 'vlan_100'

# IP on VLAN
i4 = vlan.ipv4_addresses.ipv4()[0]
i4.address = '10.0.100.1'
i4.gateway = '10.0.100.254'

# Flow with VLAN header
flow = config.flows.flow(name='flow_vlan')[0]
flow.tx_rx.port.tx_name = p1.name
flow.tx_rx.port.rx_name = p2.name
flow.packet.ethernet().vlan().ipv4().udp()

# Configure headers
eth = flow.packet[0]
eth.src.value = '00:00:00:00:00:01'

vlan_hdr = flow.packet[1]
vlan_hdr.id.value = '100'
vlan_hdr.priority = 5

flow.rate.pps = 1000
```

---

## 6. QinQ (Double-Tagged VLAN)

```python
# Device with QinQ
d = config.devices.device(name='qinq_device')[0]
e = d.ethernets.ethernet()[0]
e.connection.port_name = p1.name

# Outer VLAN
outer = e.vlans.vlan()[0]
outer.vlan_id = 200

# Inner VLAN
inner = outer.vlans.vlan()[0]
inner.vlan_id = 300

# IP on inner VLAN
i4 = inner.ipv4_addresses.ipv4()[0]
i4.address = '10.0.30.1'

# Flow with QinQ
flow = config.flows.flow(name='flow_qinq')[0]
flow.packet.ethernet().vlan().vlan().ipv4()

vlan1 = flow.packet[1]
vlan1.id.value = '200'

vlan2 = flow.packet[2]
vlan2.id.value = '300'
```

---

## 7. BGP with Route Aggregation

```python
# Multiple route pools per peer
peer = b4.peers.v4peer()[0]

# Primary pool
r1 = peer.v4_routes.v4routerange(name="pool1")[0]
r1.addresses.v4address(address='10.0.0.0', prefix=24, count=256, step=1)

# Secondary pool
r2 = peer.v4_routes.v4routerange(name="pool2")[0]
r2.addresses.v4address(address='20.0.0.0', prefix=24, count=256, step=1)

# AS path
r1.as_path.as_set_mode = r1.as_path.INCLUDE_AS_SEQ
r1.as_path.as_path_segments.bgpaspathsegment(as_numbers=[65001, 65002])
```

---

## 8. BGP Communities and Attributes

```python
# Standard community
community = route_range.communities.communities()[0]
community.as_number = 100
community.value = 1

# Extended community
ext_comm = route_range.ext_communities.ext_community()[0]
ext_comm.type = ext_comm.EXTENDED_COMMUNITY_TYPE_ROUTE_TARGET
ext_comm.as_number = 100
ext_comm.value = 200

# MED
route_range.multi_exit_discriminator = 100

# Local preference
route_range.local_preference = 200
```

---

## 9. Traffic Rate Patterns

```python
# Packets per second
flow.rate.pps = 1000

# Percentage of line rate
flow.rate.percentage = 50

# Bytes per second
flow.rate.bps = 1000000

# Continuous traffic
flow.duration.continuous.gap = 12

# Fixed packets
flow.duration.fixed_packets.packets = 1000000

# Fixed seconds
flow.duration.fixed_seconds.seconds = 60
```

---

## 10. Metrics Filtering Examples

```python
# Port metrics
req = snappi.MetricsRequest()
req.choice = req.PORT
res = api.get_metrics(req)

# Flow metrics
req.choice = req.FLOW
res = api.get_metrics(req)

# Device metrics
req.choice = req.DEVICE
res = api.get_metrics(req)
```

