# Snappi Test Assertion Patterns

Comprehensive patterns for validating test results and protocol convergence.

---

## 1. BGP Session Assertions

### Pattern 1: Simple Session Count

```python
# Assertion definition
assertions = [
    {
        "type": "bgp_sessions",
        "expected_value": 2,
        "operator": "equals"
    }
]

# Validation logic
def validate_bgp_sessions(api, expected):
    """Check BGP session count"""
    req = snappi.MetricsRequest()
    req.choice = req.DEVICE
    res = api.get_metrics(req)

    bgp_up = 0
    for metric in res.device_metrics:
        if hasattr(metric, 'bgp_session'):
            for session in metric.bgp_session:
                if session.session_state == 'up':
                    bgp_up += 1

    return bgp_up == expected, bgp_up
```

### Pattern 2: Per-Device BGP Sessions

```python
# Assertion: Each device has exactly 1 BGP session up
assertions = [
    {
        "type": "bgp_sessions",
        "device_name": "device_P1",
        "expected_value": 1,
        "operator": "equals"
    },
    {
        "type": "bgp_sessions",
        "device_name": "device_P2",
        "expected_value": 1,
        "operator": "equals"
    }
]

# Validation logic
def validate_bgp_by_device(api, device_name, expected):
    """Check BGP sessions for specific device"""
    req = snappi.MetricsRequest()
    req.choice = req.DEVICE
    res = api.get_metrics(req)

    for metric in res.device_metrics:
        if metric.name == device_name and hasattr(metric, 'bgp_session'):
            bgp_up = len([s for s in metric.bgp_session if s.session_state == 'up'])
            return bgp_up == expected, bgp_up

    return False, 0
```

### Pattern 3: BGP Session Timeout Detection

```python
# Assertion: All BGP sessions must be up (failure if any timeout/down)
def validate_bgp_convergence(api, timeout_seconds=30, check_interval=1):
    """Wait for BGP convergence with timeout"""
    start = time.time()

    while time.time() - start < timeout_seconds:
        req = snappi.MetricsRequest()
        req.choice = req.DEVICE
        res = api.get_metrics(req)

        all_up = True
        for metric in res.device_metrics:
            if hasattr(metric, 'bgp_session'):
                for session in metric.bgp_session:
                    if session.session_state != 'up':
                        all_up = False

        if all_up:
            return True, "All BGP sessions converged"

        time.sleep(check_interval)

    return False, "BGP convergence timeout"
```

---

## 2. ISIS Adjacency Assertions

### Pattern 1: Adjacency Count

```python
assertions = [
    {
        "type": "isis_adjacencies",
        "expected_value": 2,
        "operator": "equals"
    }
]

def validate_isis_adjacencies(api, expected):
    """Check ISIS adjacency count"""
    req = snappi.MetricsRequest()
    req.choice = req.DEVICE
    res = api.get_metrics(req)

    adjacencies = 0
    for metric in res.device_metrics:
        if hasattr(metric, 'isis_interface'):
            for interface in metric.isis_interface:
                # Sum Level 1 and Level 2 adjacencies
                adjacencies += getattr(interface, 'level1_adjacency_count', 0)
                adjacencies += getattr(interface, 'level2_adjacency_count', 0)

    return adjacencies == expected, adjacencies
```

### Pattern 2: ISIS Interface State

```python
def validate_isis_interface_state(api, expected_state='up'):
    """Check ISIS interface state"""
    req = snappi.MetricsRequest()
    req.choice = req.DEVICE
    res = api.get_metrics(req)

    all_up = True
    for metric in res.device_metrics:
        if hasattr(metric, 'isis_interface'):
            for interface in metric.isis_interface:
                state = getattr(interface, 'interface_state', None)
                if state != expected_state:
                    all_up = False
                    print(f"ISIS interface {interface.name}: {state}")

    return all_up
```

---

## 3. Packet Loss Assertions

### Pattern 1: Overall Packet Loss

```python
assertions = [
    {
        "type": "packet_loss",
        "expected_value": 0.01,  # < 0.01% loss
        "operator": "less_than"
    }
]

def validate_packet_loss(api, max_loss_pct):
    """Check overall packet loss"""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    total_tx = 0
    total_rx = 0

    for metric in res.flow_metrics:
        total_tx += metric.frames_tx
        total_rx += metric.frames_rx

    loss_pct = ((total_tx - total_rx) / total_tx * 100) if total_tx > 0 else 0
    passed = loss_pct < max_loss_pct

    return passed, loss_pct
```

### Pattern 2: Per-Flow Packet Loss

```python
def validate_flow_loss(api, flow_name, max_loss_pct):
    """Check packet loss for specific flow"""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    for metric in res.flow_metrics:
        if metric.name == flow_name:
            tx = metric.frames_tx
            rx = metric.frames_rx
            loss_pct = ((tx - rx) / tx * 100) if tx > 0 else 0
            passed = loss_pct < max_loss_pct

            return passed, loss_pct

    return False, "Flow not found"
```

### Pattern 3: Zero Packet Loss

```python
def validate_no_loss(api):
    """Check for zero packet loss (strict)"""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    for metric in res.flow_metrics:
        if metric.frames_tx != metric.frames_rx:
            loss = metric.frames_tx - metric.frames_rx
            print(f"Loss on {metric.name}: {loss} frames")
            return False, loss

    return True, 0
```

---

## 4. Flow Frame Count Assertions

### Pattern 1: Minimum Frames Transmitted

```python
assertions = [
    {
        "type": "flow_frames_transmitted",
        "flow_name": "flow_p1_to_p2",
        "expected_value": 100000,
        "operator": "greater_than"
    }
]

def validate_flow_tx_frames(api, flow_name, min_frames):
    """Check minimum frames transmitted on flow"""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    for metric in res.flow_metrics:
        if metric.name == flow_name:
            tx_frames = metric.frames_tx
            passed = tx_frames > min_frames

            return passed, tx_frames

    return False, "Flow not found"
```

### Pattern 2: Frames Received Check

```python
assertions = [
    {
        "type": "flow_frames_received",
        "flow_name": "flow_p1_to_p2",
        "expected_value": 100000,
        "operator": "greater_than"
    }
]

def validate_flow_rx_frames(api, flow_name, min_frames):
    """Check minimum frames received on flow"""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    for metric in res.flow_metrics:
        if metric.name == flow_name:
            rx_frames = metric.frames_rx
            passed = rx_frames > min_frames

            return passed, rx_frames

    return False, "Flow not found"
```

### Pattern 3: Frame Match (Tx == Rx)

```python
def validate_frame_match(api, flow_name):
    """Check that all transmitted frames were received"""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    for metric in res.flow_metrics:
        if metric.name == flow_name:
            match = metric.frames_tx == metric.frames_rx
            delta = abs(metric.frames_tx - metric.frames_rx)

            return match, delta

    return False, "Flow not found"
```

---

## 5. Latency Assertions

### Pattern 1: Average Latency

```python
assertions = [
    {
        "type": "flow_latency_avg",
        "flow_name": "flow_p1_to_p2",
        "expected_value": 10000,  # 10 microseconds in nanoseconds
        "operator": "less_than"
    }
]

def validate_avg_latency(api, flow_name, max_latency_ns):
    """Check average latency"""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    for metric in res.flow_metrics:
        if metric.name == flow_name:
            avg_lat_ns = metric.avg_latency_ns
            passed = avg_lat_ns < max_latency_ns

            return passed, avg_lat_ns

    return False, "Flow not found"
```

### Pattern 2: Max Latency (Jitter)

```python
def validate_max_latency(api, flow_name, max_latency_ns):
    """Check maximum latency (jitter)"""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    for metric in res.flow_metrics:
        if metric.name == flow_name:
            max_lat_ns = metric.max_latency_ns
            passed = max_lat_ns < max_latency_ns

            return passed, max_lat_ns

    return False, "Flow not found"
```

### Pattern 3: Latency Range

```python
def validate_latency_range(api, flow_name, min_ns, max_ns):
    """Check latency is within range"""
    req = snappi.MetricsRequest()
    req.choice = req.FLOW
    res = api.get_metrics(req)

    for metric in res.flow_metrics:
        if metric.name == flow_name:
            avg_lat = metric.avg_latency_ns
            min_lat = metric.min_latency_ns
            max_lat = metric.max_latency_ns

            in_range = (min_ns <= avg_lat <= max_ns)

            return in_range, {
                "min": min_lat,
                "avg": avg_lat,
                "max": max_lat
            }

    return False, "Flow not found"
```

---

## 6. Port-Level Assertions

### Pattern 1: Port Frame Count

```python
assertions = [
    {
        "type": "port_frames_transmitted",
        "port_name": "P1",
        "expected_value": 500000,
        "operator": "greater_than"
    }
]

def validate_port_tx_frames(api, port_name, min_frames):
    """Check frames transmitted on port"""
    req = snappi.MetricsRequest()
    req.choice = req.PORT
    res = api.get_metrics(req)

    for metric in res.port_metrics:
        if metric.name == port_name:
            tx_frames = metric.frames_tx
            passed = tx_frames > min_frames

            return passed, tx_frames

    return False, "Port not found"
```

### Pattern 2: Port Error Count

```python
def validate_port_errors(api, port_name, max_errors=0):
    """Check for port transmission errors"""
    req = snappi.MetricsRequest()
    req.choice = req.PORT
    res = api.get_metrics(req)

    for metric in res.port_metrics:
        if metric.name == port_name:
            error_count = metric.frames_rx_error or 0
            passed = error_count <= max_errors

            return passed, error_count

    return False, "Port not found"
```

### Pattern 3: Port Link Status

```python
def validate_port_link(api, port_name, expected_state='up'):
    """Check port link status"""
    req = snappi.MetricsRequest()
    req.choice = req.PORT
    res = api.get_metrics(req)

    for metric in res.port_metrics:
        if metric.name == port_name:
            link_state = getattr(metric, 'link_state', 'unknown')
            passed = link_state.lower() == expected_state.lower()

            return passed, link_state

    return False, "Port not found"
```

---

## 7. Complex Composite Assertions

### Pattern 1: Multi-Protocol Convergence

```python
def validate_multi_protocol_convergence(api, timeout=60):
    """Wait for all protocols to converge"""
    start = time.time()

    while time.time() - start < timeout:
        req = snappi.MetricsRequest()
        req.choice = req.DEVICE
        res = api.get_metrics(req)

        all_converged = True
        status = {}

        for metric in res.device_metrics:
            # BGP check
            bgp_up = 0
            if hasattr(metric, 'bgp_session'):
                bgp_up = len([s for s in metric.bgp_session if s.session_state == 'up'])

            # ISIS check
            isis_adj = 0
            if hasattr(metric, 'isis_interface'):
                for iface in metric.isis_interface:
                    isis_adj += getattr(iface, 'level1_adjacency_count', 0)
                    isis_adj += getattr(iface, 'level2_adjacency_count', 0)

            status[metric.name] = {
                'bgp_sessions': bgp_up,
                'isis_adjacencies': isis_adj
            }

            if bgp_up == 0 and isis_adj == 0:
                all_converged = False

        if all_converged and any(v['bgp_sessions'] > 0 or v['isis_adjacencies'] > 0 for v in status.values()):
            return True, status

        time.sleep(1)

    return False, status
```

### Pattern 2: End-to-End Test Validation

```python
def validate_end_to_end(api, config):
    """Comprehensive test validation"""
    results = {
        'protocols': {},
        'flows': {},
        'ports': {},
        'passed': True
    }

    # Check protocols
    req = snappi.MetricsRequest()
    req.choice = req.DEVICE
    device_res = api.get_metrics(req)

    for metric in device_res.device_metrics:
        bgp_up = 0
        if hasattr(metric, 'bgp_session'):
            bgp_up = len([s for s in metric.bgp_session if s.session_state == 'up'])

        results['protocols'][metric.name] = {
            'bgp_sessions': bgp_up,
            'converged': bgp_up > 0
        }

        if bgp_up == 0:
            results['passed'] = False

    # Check flows
    req.choice = req.FLOW
    flow_res = api.get_metrics(req)

    for metric in flow_res.flow_metrics:
        loss_pct = ((metric.frames_tx - metric.frames_rx) / metric.frames_tx * 100) \
                   if metric.frames_tx > 0 else 0

        results['flows'][metric.name] = {
            'tx': metric.frames_tx,
            'rx': metric.frames_rx,
            'loss_pct': loss_pct,
            'passed': loss_pct < 0.01  # < 0.01% acceptable
        }

        if loss_pct >= 0.01:
            results['passed'] = False

    # Check ports
    req.choice = req.PORT
    port_res = api.get_metrics(req)

    for metric in port_res.port_metrics:
        link_state = getattr(metric, 'link_state', 'unknown')

        results['ports'][metric.name] = {
            'link_state': link_state,
            'tx_frames': metric.frames_tx,
            'rx_frames': metric.frames_rx,
            'passed': link_state.lower() == 'up'
        }

        if link_state.lower() != 'up':
            results['passed'] = False

    return results['passed'], results
```

---

## 8. Assertion Operators

### Pattern 1: Basic Operators

```python
def evaluate_assertion(actual, expected, operator):
    """Evaluate assertion with operator"""
    if operator == "equals":
        return actual == expected
    elif operator == "greater_than":
        return actual > expected
    elif operator == "greater_than_or_equal":
        return actual >= expected
    elif operator == "less_than":
        return actual < expected
    elif operator == "less_than_or_equal":
        return actual <= expected
    elif operator == "not_equals":
        return actual != expected
    elif operator == "in_range":
        # Expects expected to be tuple (min, max)
        return expected[0] <= actual <= expected[1]
    else:
        raise ValueError(f"Unknown operator: {operator}")
```

### Pattern 2: Assertion Validation Framework

```python
def validate_all_assertions(api, assertions):
    """Validate all assertions"""
    results = []
    all_passed = True

    for assertion in assertions:
        assertion_type = assertion.get('type')
        expected = assertion.get('expected_value')
        operator = assertion.get('operator')

        try:
            if assertion_type == 'bgp_sessions':
                passed, actual = validate_bgp_sessions(api, expected)
            elif assertion_type == 'isis_adjacencies':
                passed, actual = validate_isis_adjacencies(api, expected)
            elif assertion_type == 'packet_loss':
                passed, actual = validate_packet_loss(api, expected)
            elif assertion_type == 'flow_frames_transmitted':
                passed, actual = validate_flow_tx_frames(
                    api, assertion.get('flow_name'), expected
                )
            else:
                passed, actual = False, "Unknown assertion type"

            results.append({
                'type': assertion_type,
                'expected': expected,
                'operator': operator,
                'actual': actual,
                'passed': passed
            })

            if not passed:
                all_passed = False

        except Exception as e:
            results.append({
                'type': assertion_type,
                'error': str(e),
                'passed': False
            })
            all_passed = False

    return all_passed, results
```

---

## Best Practices

1. **Always wait for convergence** before checking protocol sessions
2. **Aggregate metrics** across all flows for overall statistics
3. **Use appropriate timeouts** for protocol convergence (typically 30-60s)
4. **Check both TX and RX** to detect one-directional failures
5. **Validate at multiple levels**: port → flow → protocol
6. **Log actual values** for failed assertions (help debugging)
7. **Use strict assertions** for critical tests, lenient for stress tests
8. **Check link state** before checking metrics
9. **Differentiate timeout vs failure** in assertion logic
10. **Persist results** to JSON for CI/CD integration

