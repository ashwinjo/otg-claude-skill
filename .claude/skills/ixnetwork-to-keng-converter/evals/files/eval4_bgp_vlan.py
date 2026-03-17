# IxNetwork RestPy BGP Configuration with VLAN Support
# 2-port BGP test with VLAN tagging

from ixnetwork_restpy.testplatform import TestPlatform

tp = TestPlatform('10.36.231.231', rest_port=443, userName='admin', password='admin')
session_assistant = tp.Sessions.add().Ixnetwork

# Port mapping
portMap = session_assistant.PortMapAssistant()
portMap.Map('10.36.231.231', CardId=9, PortId=2, Name='Port_1')
portMap.Map('10.36.231.231', CardId=9, PortId=1, Name='Port_2')
portMap.Connect(forceTakePortOwnership=True)

vports = session_assistant.Vport.find()

# Create Topology 1
topology1 = session_assistant.Topology.add(Name='Topo1', Ports=vports[0])
devgrp1 = topology1.DeviceGroup.add(Name='DG1', Multiplier=1)

# L2 with VLAN
ethernet1 = devgrp1.Ethernet.add(Name='Eth1')
ethernet1.EnableVlans.Single(True)

vlan1 = ethernet1.Vlan.add(Name='VLAN100')
vlan1.VlanId.Single(100)

# L3 within VLAN
ipv4_1 = ethernet1.Ipv4.add(Name='Ipv41')
ipv4_1.Address.Single('192.168.100.1')
ipv4_1.GatewayIp.Single('192.168.100.254')

# BGP on VLAN
bgp1 = ipv4_1.BgpIpv4Peer.add(Name='BGPPeer1')
bgp1.DutIp.Single('192.168.100.254')
bgp1.Type.Single('external')
bgp1.LocalAs2Bytes.Single(65001)

# Create Topology 2
topology2 = session_assistant.Topology.add(Name='Topo2', Ports=vports[1])
devgrp2 = topology2.DeviceGroup.add(Name='DG2', Multiplier=1)

# L2 with VLAN
ethernet2 = devgrp2.Ethernet.add(Name='Eth1')
ethernet2.EnableVlans.Single(True)

vlan2 = ethernet2.Vlan.add(Name='VLAN100')
vlan2.VlanId.Single(100)

# L3 within VLAN
ipv4_2 = ethernet2.Ipv4.add(Name='Ipv41')
ipv4_2.Address.Single('192.168.100.254')
ipv4_2.GatewayIp.Single('192.168.100.1')

# BGP on VLAN
bgp2 = ipv4_2.BgpIpv4Peer.add(Name='BGPPeer2')
bgp2.DutIp.Single('192.168.100.1')
bgp2.Type.Single('external')
bgp2.LocalAs2Bytes.Single(65002)

# Traffic on VLAN
trafficItem = session_assistant.Traffic.TrafficItem.add(
    Name='VLAN Traffic',
    BiDirectional=True,
    TrafficType='ipv4'
)
trafficItem.EndpointSet.add(Sources=devgrp1, Destinations=devgrp2)
trafficItem.Generate()

# This config should succeed in conversion
# Skill should report:
# ✅ BGP peering converted successfully
# ✅ VLAN configuration converted
# ✅ Traffic flows converted
