# IxNetwork RestPy OSPF Configuration Example
# This config uses OSPF which is NOT supported in OTG/KENG
# Skill should detect this and report conversion impossible

from ixnetwork_restpy.testplatform import TestPlatform

tp = TestPlatform('10.36.231.231', rest_port=443, userName='admin', password='admin')
session_assistant = tp.Sessions.add().Ixnetwork

# Port mapping
portMap = session_assistant.PortMapAssistant()
portMap.Map('10.36.231.231', CardId=9, PortId=2, Name='Port_1')
portMap.Connect(forceTakePortOwnership=True)

vports = session_assistant.Vport.find()

# Create Topology
topology = session_assistant.Topology.add(Name='Topo1', Ports=vports[0])
devgrp = topology.DeviceGroup.add(Name='DG1', Multiplier=1)

# L2/L3
ethernet = devgrp.Ethernet.add(Name='Eth1')
ipv4 = ethernet.Ipv4.add(Name='Ipv41')
ipv4.Address.Single('192.168.1.1')
ipv4.GatewayIp.Single('192.168.1.254')

# OSPF - NOT SUPPORTED IN OTG
ospf = ipv4.OspfIpv4.add(Name='OSPFv2')
ospf.RouterId.Single('192.168.1.1')
ospf.AreaId.Single('0.0.0.0')
ospf.NetworkType.Single('pointToPoint')

# This config should fail conversion because OSPF is not supported
# Skill should report:
# ❌ OSPF protocol (Severity: CRITICAL - blocking)
# Reason: OTG MVP only supports BGP routing protocol
