# IxNetwork RestPy BGP Configuration Example
# 2-port BGP test with bidirectional traffic

from ixnetwork_restpy.testplatform import TestPlatform

# Setup
tp = TestPlatform('10.36.231.231', rest_port=443, userName='admin', password='admin')
session_assistant = tp.Sessions.add().Ixnetwork

# Port mapping
portMap = session_assistant.PortMapAssistant()
portMap.Map('10.36.231.231', CardId=9, PortId=2, Name='Port_1')
portMap.Map('10.36.231.231', CardId=9, PortId=1, Name='Port_2')
portMap.Connect(forceTakePortOwnership=True)

# Get vports
vports = session_assistant.Vport.find()

# Create Topology 1 (on Port_1)
topology1 = session_assistant.Topology.add(Name='Topo1', Ports=vports[0])
devgrp1 = topology1.DeviceGroup.add(Name='DG1', Multiplier=2)

# L2 - Ethernet
ethernet1 = devgrp1.Ethernet.add(Name='Eth1')
ethernet1.Mac.Increment(start_value='00:11:22:33:44:01', step_value='00:00:00:00:00:01')

# L3 - IPv4
ipv4_1 = ethernet1.Ipv4.add(Name='Ipv41')
ipv4_1.Address.Increment(start_value='1.1.1.4', step_value='0.0.0.1')
ipv4_1.GatewayIp.Increment(start_value='1.1.1.1', step_value='0.0.0.0')

# BGP Peer
bgp1 = ipv4_1.BgpIpv4Peer.add(Name='BGPPeer1')
bgp1.DutIp.Increment(start_value='1.1.1.1', step_value='0.0.0.1')
bgp1.Type.Single('external')
bgp1.LocalAs2Bytes.Increment(start_value=101, step_value=0)
bgp1.SessionInfo.Multiplier = 2

# BGP Network Group (routes to advertise)
networkGroup1 = devgrp1.NetworkGroup.add(Name='BGP-Routes1', Multiplier=100)
ipv4PrefixPool1 = networkGroup1.Ipv4PrefixPools.add(NumberOfAddresses=1)
ipv4PrefixPool1.NetworkAddress.Increment(start_value='10.10.0.1', step_value='0.0.0.1')
ipv4PrefixPool1.PrefixLength.Single(32)

# Create Topology 2 (on Port_2)
topology2 = session_assistant.Topology.add(Name='Topo2', Ports=vports[1])
devgrp2 = topology2.DeviceGroup.add(Name='DG2', Multiplier=2)

# L2 - Ethernet
ethernet2 = devgrp2.Ethernet.add(Name='Eth1')
ethernet2.Mac.Increment(start_value='00:11:22:33:44:02', step_value='00:00:00:00:00:01')

# L3 - IPv4
ipv4_2 = ethernet2.Ipv4.add(Name='Ipv41')
ipv4_2.Address.Increment(start_value='1.1.1.1', step_value='0.0.0.1')
ipv4_2.GatewayIp.Increment(start_value='1.1.1.4', step_value='0.0.0.0')

# BGP Peer
bgp2 = ipv4_2.BgpIpv4Peer.add(Name='BGPPeer2')
bgp2.DutIp.Increment(start_value='1.1.1.4', step_value='0.0.0.1')
bgp2.Type.Single('external')
bgp2.LocalAs2Bytes.Increment(start_value=102, step_value=0)
bgp2.SessionInfo.Multiplier = 2

# BGP Network Group (routes to advertise)
networkGroup2 = devgrp2.NetworkGroup.add(Name='BGP-Routes2', Multiplier=100)
ipv4PrefixPool2 = networkGroup2.Ipv4PrefixPools.add(NumberOfAddresses=1)
ipv4PrefixPool2.NetworkAddress.Increment(start_value='20.10.0.1', step_value='0.0.0.1')
ipv4PrefixPool2.PrefixLength.Single(32)

# Traffic Configuration
trafficItem = session_assistant.Traffic.TrafficItem.add(
    Name='BGP Traffic',
    BiDirectional=True,
    TrafficType='ipv4',
    TrackingType=['sourceDestEndpointPair0']
)
trafficItem.EndpointSet.add(Sources=networkGroup1, Destinations=networkGroup2)
trafficItem.ConfigElement.FrameRate.Rate = 13888889
trafficItem.ConfigElement.TransmissionControl.FrameCount = 0

# Start protocols
session_assistant.StartAllProtocols(Arg1=True)

# Generate and start traffic
trafficItem.Generate()
session_assistant.Traffic.StartStatelessTraffic()

# Note: This is configuration-only. Actual execution would continue with:
# session_assistant.Traffic.StopStatelessTraffic()
# session_assistant.StopAllProtocols(Arg1='sync')
