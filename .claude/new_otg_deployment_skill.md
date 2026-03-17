Introduction

What is Ixia-c ?
A modern, powerful and API-driven traffic generator designed to cater to the needs of hyper-scalers, network hardware vendors and hobbyists alike.

Free for basic use-cases and distributed / deployed as a multi-container application consisting primarily of a controller, a traffic-engine and a protocol-engine.


Please ensure that following prerequisites are met by the setup:

At least 2 x86_64 CPU cores and 7GB RAM, preferably running Ubuntu 22.04 LTS OS
Python 3.8+ (and pip) or Go 1.19+
Docker Engine (Community Edition)

There are several implementations of OTG API.

Ixia-c: Ixia-c containerized software Traffic Engine (TE) and Protocol Engine (PE)
Ixia-c-one: a single-container package of Ixia-c for Containerlab
IxOS Hardware: Keysight Elastic Network Generator with Keysight/Ixia L23 Network Test Hardware


Infrastructure
To manage deployment of the example labs, we use one of the following tools:

- Docker Compose - general-purpose tool for defining and running multi-container Docker applications

- Containerlab - simple yet powerful specialized tool for orchestrating and managing container-based networking labs

-Ixia-c Operator – Ixia-c deployment orchestration engine compatible with K8s/KNE as well as Docker for Hybrid mode

-OpenConfig KNE – Kubernetes Network Emulation, which is a Google initiative to develop tooling for quickly setting up topologies of containers running various device OSes.

## We will focus on "Docker Compose" and "Containerlab" for the deployment of the Ixia-c.




