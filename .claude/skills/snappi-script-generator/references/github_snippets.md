# Snappi GitHub Code Snippets

Actual code examples extracted from the official Snappi repository:
https://github.com/open-traffic-generator/snappi

---

## Source Files Reference

| File | Purpose | Key Patterns |
|------|---------|--------------|
| `snappi.py` | Core SDK | API init, HttpTransport, exception handling |
| `test_e2e_port_flow_config.py` | End-to-end workflow | Port/flow creation, metrics, control state |
| `test_bgp_sr_te_policy.py` | BGP advanced | Device stack, BGP with routes, SR-TE |
| `test_device_stack.py` | Device setup | IPv4+IPv6, BGP dual-stack |
| `test_lag.py` | LACP aggregation | LAG creation, LACP configuration |
| `test_capture.py` | Packet capture | Capture filters, custom filters |
| `test_device_factory_methods.py` | Device methods | Factory pattern usage |

---

## 1. API Initialization from snappi.py

**Location:** `snappi/snappi.py` - `api()` function

```python
import snappi
import logging

# Basic initialization
api = snappi.api(location="https://10.36.74.26:443")

# Full initialization with all options
api = snappi.api(
    location="https://localhost:8443",
    transport="http",           # "http", "grpc", or auto-detect
    verify=False,               # Disable TLS verification for dev
    logger=None,                # Use default logger
    loglevel=logging.INFO,      # logging.WARN, INFO, DEBUG
    version_check=False,        # Skip version compatibility check
    otel_collector=None         # OpenTelemetry collector (Python 3.7+)
)
```

**Error Handling from HttpTransport:**

```python
import urllib3

# Set verify=False for self-signed certificates (development only)
api = snappi.api(location="https://localhost:8443", verify=False)

# For production: provide CA bundle
api = snappi.api(
    location="https://api.example.com:8443",
    verify="/path/to/ca-bundle.crt"
)

# This internally:
# - Disables urllib3 warnings if verify=False
# - Creates requests.Session() for connection pooling
# - Implements retry logic with exponential backoff
```

---

## 2. Config Serialization from test_e2e_port_flow_config.py

**Location:** `tests/test_e2e_port_flow_config.py` - Lines 1-50

```python
import snappi

# Create config object
config = snappi.Config()

# Deserialize from JSON string (loads)
config_json = '''
{
  "ports": [
    {"name": "p1", "location": "10.36.74.26;02;13"},
    {"name": "p2", "location": "10.36.74.26;02;14"}
  ]
}
'''
config.loads(config_json)

# Push to controller
api.set_config(config)

# Retrieve from controller
retrieved = api.get_config()

# Serialize to JSON string (dumps)
config_str = config.dumps()  # Returns JSON string
config_dict = config.dumps(format='dict')  # Returns Python dict
config_yaml = config.dumps(format='yaml')  # Returns YAML string
```

---

## 3. Port and Flow Creation from test_e2e_port_flow_config.py

**Location:** `tests/test_e2e_port_flow_config.py` - Lines 8-25

```python
import snappi

config = snappi.Config()

# Fluent API: method chaining creates objects
tx_port, rx_port = config.ports.port(
    name="Tx Port", location="10.36.74.26;02;13"
).port(
    name="Rx Port", location="10.36.74.26;02;14"
)

# Create flow and configure
flow = config.flows.flow(name="Tx -> Rx Flow")[0]
flow.tx_rx.port.tx_name = tx_port.name
flow.tx_rx.port.rx_name = rx_port.name
flow.size.fixed = 128
flow.rate.pps = 1000
flow.duration.fixed_packets.packets = 10000

# Packet header chaining
flow.packet.ethernet().vlan().ipv4().tcp()

# Access headers by index
eth = flow.packet[0]  # Ethernet
vlan = flow.packet[1]  # VLAN
ipv4 = flow.packet[2]  # IPv4
tcp = flow.packet[3]  # TCP

# Configure headers
eth.src.value = "00:00:01:00:00:01"
eth.dst.values = ["00:00:02:00:00:01", "00:00:02:00:00:02"]

ipv4.src.value = "1.1.1.1"
ipv4.src.values = ["1.1.1.1"]  # Multiple values
ipv4.src.increment.start = "1.1.1.1"
ipv4.src.increment.step = "0.0.0.1"
ipv4.src.increment.count = 10

# Decrement pattern
ipv4.dst.decrement.start = "1.1.2.200"
ipv4.dst.decrement.step = "0.0.0.1"
ipv4.dst.decrement.count = 10
```

---

## 4. BGP Device Stack from test_device_stack.py

**Location:** `tests/test_device_stack.py` - Complete example

```python
import snappi

def setup_bgp_dual_stack(api):
    config = api.config()

    # Create ports
    p1, p2 = config.ports.port(name='p1').port(name='p2')

    # Create device
    d = config.devices.device(name='d')[-1]

    # Ethernet interface
    e = d.ethernets.ethernet()[-1]
    e.connection.port_name = p1.name
    e.name = 'eth1'
    e.mac = '00:01:00:00:00:01'

    # IPv4 stack
    i4 = e.ipv4_addresses.ipv4()[-1]
    i4.name = 'ipv4_1'
    i4.address = '1.1.1.1'
    i4.gateway = '1.1.1.2'
    i4.prefix = 24  # /24 = 255.255.255.0

    # IPv6 stack
    i6 = e.ipv6_addresses.ipv6()[-1]
    i6.name = 'ipv6_1'
    i6.address = '2001::1'
    i6.gateway = '2001::2'
    i6.prefix = 64  # /64 prefix length

    # BGP router ID (global)
    d.bgp.router_id = "192.168.1.1"

    # BGP IPv4 interface
    bgp_v4 = d.bgp.ipv4_interfaces.v4interface()[-1]
    bgp_v4.ipv4_name = i4.name

    # BGP IPv4 peer
    peer_v4 = bgp_v4.peers.v4peer()[-1]
    peer_v4.name = "peer_v4"
    peer_v4.peer_address = '1.1.1.2'
    peer_v4.as_number = 10
    peer_v4.as_type = peer_v4.IBGP  # or EBGP

    # BGP IPv4 routes
    routes_v4 = peer_v4.v4_routes.v4routerange(name="routes_v4")[-1]
    routes_v4.addresses.v4address(
        address='10.0.0.0',     # Start address
        prefix=24,              # Prefix length
        count=256,              # Number of prefixes
        step=1                  # Increment step
    )

    # BGP IPv6 interface
    bgp_v6 = d.bgp.ipv6_interfaces.v6interface()[-1]
    bgp_v6.ipv6_name = i6.name

    # BGP IPv6 peer
    peer_v6 = bgp_v6.peers.v6peer()[-1]
    peer_v6.peer_address = '2001::2'
    peer_v6.as_number = 10
    peer_v6.as_type = 'ibgp'

    # BGP IPv6 routes
    routes_v6 = peer_v6.v6_routes.v6routerange(name="routes_v6")[-1]
    routes_v6.addresses.v6address(
        address='2001:1::0',
        prefix=64,
        count=100,
        step=1
    )

    api.set_config(config)
    return api
```

---

## 5. Metrics Collection from test_e2e_port_flow_config.py

**Location:** `tests/test_e2e_port_flow_config.py` - Lines 45-55

```python
import snappi

api = # ... initialized api

# Get port metrics
req = snappi.MetricsRequest()
req.choice = req.PORT
res = api.get_metrics(req)

for metric in res.port_metrics:
    print(f"Port: {metric.name}")
    print(f"  TX frames: {metric.frames_tx}")
    print(f"  RX frames: {metric.frames_rx}")
    print(f"  TX bytes: {metric.bytes_tx}")
    print(f"  RX bytes: {metric.bytes_rx}")
    print(f"  RX errors: {metric.frames_rx_error}")

# Get flow metrics
req = snappi.MetricsRequest()
req.choice = req.FLOW
res = api.get_metrics(req)

for metric in res.flow_metrics:
    print(f"Flow: {metric.name}")
    print(f"  TX frames: {metric.frames_tx}")
    print(f"  RX frames: {metric.frames_rx}")
    print(f"  Min latency (ns): {metric.min_latency_ns}")
    print(f"  Max latency (ns): {metric.max_latency_ns}")
    print(f"  Avg latency (ns): {metric.avg_latency_ns}")

# Get device metrics (protocol sessions)
req = snappi.MetricsRequest()
req.choice = req.DEVICE
res = api.get_metrics(req)

for metric in res.device_metrics:
    print(f"Device: {metric.name}")
    if hasattr(metric, 'bgp_session'):
        for session in metric.bgp_session:
            print(f"  BGP session {session.session_id}: {session.session_state}")
```

---

## 6. Traffic Control from test_e2e_port_flow_config.py

**Location:** `tests/test_e2e_port_flow_config.py` - Lines 35-42

```python
import snappi

api = # ... initialized api

# Start traffic
control_state = snappi.ControlState()
control_state.traffic.flow_transmit.state = "start"
api.set_control_state(control_state)

# Stop traffic
control_state = snappi.ControlState()
control_state.traffic.flow_transmit.state = "stop"
api.set_control_state(control_state)

# Alternative syntax (equivalent)
ts = api.control_state()
ts.state = ts.START  # or ts.STOP
api.set_transmit_state(ts)
```

---

## 7. Protocol Control from test_e2e_port_flow_config.py

```python
import snappi
import time

api = # ... initialized api

# Start all protocols
control_state = snappi.ControlState()
control_state.protocol.state = snappi.ControlState.Protocol.start
api.set_control_state(control_state)

# Wait for convergence
time.sleep(30)

# Stop all protocols
control_state = snappi.ControlState()
control_state.protocol.state = snappi.ControlState.Protocol.stop
api.set_control_state(control_state)
```

---

## 8. Packet Capture from test_capture.py

**Location:** `tests/test_capture.py` - Lines 1-50

```python
import snappi

config = snappi.Config()

# Create ports
config.ports.port(name='port1').port(name='port2')

# Create capture
capture = config.captures.capture()[0]
capture.name = 'capture1'
capture.port_names = [port.name for port in config.ports]

# Custom filter (low-level)
capture.filters.custom().custom()
src_mac_filter = capture.filters[0]
src_mac_filter.offset = 0  # Start at byte 0 (Ethernet source)
src_mac_filter.value = '000100000001'  # MAC address
src_mac_filter.mask = 'FFFFFFFFFFFF'  # All bits must match

# Or: Packet header filter chain
capture.filters.clear()
eth, vlan1, vlan2 = capture.filters.ethernet().vlan().vlan()

# Filter QinQ traffic
vlan1.id.value = '200'  # Outer VLAN
vlan1.id.mask = 'FFF'   # 12 bits for VLAN ID
vlan2.id.value = '300'  # Inner VLAN
vlan2.id.mask = 'FFF'

# Or: Specific IP filters
capture.filters.clear()
eth, ip, custom = capture.filters.ethernet().ipv4().custom()
eth.src.value = '000001000001'
eth.src.mask = 'FFFFFFFFFFFF'
custom.offset = 16  # Offset into custom payload
custom.value = '010101'
custom.mask = 'FFFFFF'

api.set_config(config)

# Retrieve captured packets
# NOTE: Capture files are saved to traffic generator storage
# Retrieve via download API or traffic generator UI
```

---

## 9. Exception Handling from snappi.py

**Location:** `snappi/snappi.py` - `HttpTransport` class

```python
import snappi
import time
import logging

logger = logging.getLogger("snappi")

# Connection with retry
def connect_with_retry(location, max_retries=3):
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt+1}/{max_retries}: Connecting to {location}")
            api = snappi.api(
                location=location,
                verify=False,  # Dev: disable TLS verification
                loglevel=logging.DEBUG
            )
            logger.info("Connected successfully")
            return api
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Connection failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to connect after {max_retries} attempts")
                raise

# Exception parsing
try:
    api.set_config(config)
except Exception as e:
    # Parse error response
    error_msg = str(e)
    logger.error(f"Config failed: {error_msg}")

    # Example error structure:
    # error_response = {
    #   'code': 400,
    #   'errors': ['Port p1 not found', 'Port p2 not found']
    # }
    raise

# TLS verification for self-signed certs
try:
    api = snappi.api(
        location="https://localhost:8443",
        verify=False  # Accept any TLS certificate
    )
except Exception as e:
    logger.error(f"TLS error: {e}")
    # Try with CA bundle
    api = snappi.api(
        location="https://localhost:8443",
        verify="/path/to/ca.crt"
    )
```

---

## 10. Factory Methods Pattern from test_device_factory_methods.py

**Location:** `tests/test_device_factory_methods.py`

```python
import snappi

config = snappi.Config()

# Factory methods return the last created object as a list item
# Accessing [0] or [-1] gets the created object

# Create device
device = config.devices.device(name='device1')[-1]

# Create Ethernet on device
eth = device.ethernets.ethernet()[-1]
eth.name = 'eth1'
eth.connection.port_name = "p1"
eth.mac = '00:00:00:00:00:00'

# Create multiple objects and chain
eth1, eth2 = (device.ethernets
    .ethernet()
    .ethernet()
)
eth1.name = 'eth1'
eth1.connection.port_name = "p1"
eth2.name = 'eth2'
eth2.connection.port_name = "p2"

# Return last N items created
ports = config.ports.port(name='p1').port(name='p2').port(name='p3')
# ports[-3], ports[-2], ports[-1] are the three ports
```

---

## 11. Advanced: SR-TE Policy from test_bgp_sr_te_policy.py

**Location:** `tests/test_bgp_sr_te_policy.py` - Segment Routing Traffic Engineering

```python
import snappi

config = snappi.Config()
p1 = config.ports.port(name='p1')[-1]

d = config.devices.device(name='d')[-1]
eth = d.ethernets.ethernet()[-1]
eth.connection.port_name = p1.name
eth.mac = '00:01:00:00:00:01'

ip = eth.ipv6_addresses.ipv6()[-1]
ip.address = '2a00:1450:f013:c03:8402:0:0:2'
ip.gateway = '2a00:1450:f013:c03:0:0:0:1'

bgp = d.bgp
bgp.router_id = '193.0.0.1'

# BGP IPv6 interface
bgp_intf = bgp.ipv6_interfaces.v6interface(ipv6_name=ip.name)[-1]

# BGP peer
peer = bgp_intf.peers.v6peer()[-1]
peer.as_number = 65511
peer.peer_address = '2001:4860:0:0:0:1c:4001:ec2'
peer.advanced.hold_time_interval = 90
peer.advanced.keep_alive_interval = 30

# SR-TE policy (Segment Routing Traffic Engineering)
for i in range(1, 501):
    policy = peer.sr_te_policies.bgpsrtepolicy()[-1]
    policy.policy_type = policy.IPV4
    policy.distinguisher = 1
    policy.color = i  # 1-500: different colors for 500 policies
    policy.ipv6_endpoint = '0:0:0:0:0:0:0:0'

    # Next hop configuration
    hop = policy.next_hop
    hop.next_hop_mode = hop.MANUAL
    hop.next_hop_address_type = hop.IPV6
    hop.ipv6_address = '2a00:1450:f013:c07:8402:0:0:2'

    # Tunnel TLV
    tunnel = policy.tunnel_tlvs.bgptunneltlv(active=True)[-1]

    # Segment list
    seglist = tunnel.segment_lists.bgpsegmentlist(active=True)[-1]
    seglist.segment_weight = 1

    # MPLS labels
    for label in [1018001, 432999, 1048333, 1048561, 432001]:
        seg = seglist.segments.bgpsegment(active=True)[-1]
        seg.segment_type = seg.MPLS_SID
        seg.mpls_label = label

    # Sub-TLVs
    tunnel.preference_sub_tlv.preference = 400
    tunnel.binding_sub_tlv.binding_sid_type = tunnel.binding_sub_tlv.FOUR_OCTET_SID
    tunnel.binding_sub_tlv.four_octet_sid = 483001

api.set_config(config)
```

---

## Key Takeaways

1. **Fluent API**: Methods return self (or created objects) for chaining
2. **Factory methods**: Return [0] or [-1] to access created objects
3. **Serialization**: `.loads()` deserialize, `.dumps()` serialize
4. **Metrics**: Separate requests for PORT, FLOW, DEVICE metrics
5. **Control state**: Separate for traffic and protocols
6. **Error handling**: Exponential backoff on connection failures
7. **Field patterns**: `.value`, `.values`, `.increment`, `.decrement`
8. **Chaining**: Packet headers, capture filters, device stacks

