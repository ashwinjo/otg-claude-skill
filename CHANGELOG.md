# Changelog

All notable changes to the KENG OTG Traffic Testing Plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-03-22

### Added
- **5 Production-Ready Skills:**
  - `ixnetwork-to-keng-converter` — Migrate IxNetwork configs to OTG format with feasibility analysis
  - `otg-config-generator` — Generate OTG configurations from natural language intent
  - `snappi-script-generator` — Generate standalone Python Snappi scripts from OTG configs
  - `ixia-c-deployment` — Deploy Ixia-c via Docker Compose or Containerlab
  - `keng-licensing` — Licensing recommendations and cost estimation

- **4 Intelligent Subagents:**
  - 🔵 `ixia-c-deployment-agent` — Infrastructure provisioning
  - 🟢 `otg-config-generator-agent` — Intent to config translation
  - 🟣 `snappi-script-generator-agent` — Config to script execution
  - 🟠 `keng-licensing-agent` — Licensing advisor

- **16 Claude Commands (3 Tiers):**
  - **Section C (Help & Discovery):** 7 discovery commands
  - **Section A (Skill Shortcuts):** 5 quick-access commands
  - **Section B (Workflows):** 4 end-to-end orchestration commands

- **Comprehensive Documentation:**
  - `README.md` — Project overview, skill descriptions, workflow examples
  - `CLAUDE.md` — Claude Code integration guide and best practices
  - `AGENT_ORCHESTRATION_PLAN.md` — Detailed orchestration patterns and use cases
  - `.claude/skills/INDEX.md` — Skill discovery and technical reference
  - `.claude/agents/README.md` — Subagent specifications and workflows
  - `.claude/agents/eval-sets/` — 20 evaluation questions (5 per agent)

- **Agent Learning System:**
  - `fixes.md` — Mistake & solution log for institutional memory
  - Evaluation test cases for all agents and skills

### Features
- **Port Alignment Validation** — Automatic validation of port locations across deployment, config, and script phases
- **Standalone Script Generation** — Self-contained Snappi scripts with embedded infrastructure details
- **IxNetwork Migration** — Complete feasibility analysis and conversion to OTG format
- **Parallel Orchestration** — Run independent tasks (licensing + deployment) simultaneously
- **Multi-Protocol Support** — BGP, ISIS, LACP, LLDP, VLAN, IPv4/IPv6 traffic flows
- **Infrastructure Flexibility** — Docker Compose (simple labs) or Containerlab (topology-based)

### Documentation
- 500+ KB total documentation
- 10+ pages of detailed skill guides
- Architecture diagrams and orchestration workflows
- Troubleshooting guides and common patterns
- Real-world workflow examples

---

## [1.1.0] - 2026-03-15

### Added
- BGP b2b test pipeline with runtime fixes
- Agent learning system integration

### Fixed
- OTG schema contradictions resolved
- Port mapping alignment improved
- Cleanup command for container and veth cleanup

---

## [1.0.0] - 2026-03-10

### Added
- Initial release with core skills
- Skill evaluation framework
- Agent specifications
- Command framework foundation
- Workflow orchestration patterns

---

## Version Support Matrix

| Component | Version | Release Date | Status | Notes |
|-----------|---------|--------------|--------|-------|
| **Plugin** | 2.0.0 | 2026-03-22 | ✅ Stable | Production-ready, full feature set |
| **Skills** (5) | 1.1 | 2026-03-15 | ✅ Stable | All skills mature, comprehensive evals |
| **Agents** (4) | 1.0 | 2026-03-10 | ✅ Stable | Intelligent orchestration, 20 evals |
| **Commands** (16) | 1.0 | 2026-03-10 | ✅ Stable | Discovery, shortcuts, workflows |
| **Orchestration** | 1.0 | 2026-03-10 | ✅ Stable | Serial/parallel dispatch, port alignment |

---

## Upgrade Path

### From v1.x → v2.0
- All v1.x configurations remain compatible
- New commands and agents available immediately
- Recommended: Review AGENT_ORCHESTRATION_PLAN.md for new workflows
- No breaking changes

---

## Known Limitations

- Ixia-c deployment requires Docker/sudo access
- IxNetwork migration supports core protocols (BGP, LACP, VLAN, Ethernet, IPv4)
- Licensing calculations assume KENG standard pricing (verify with Solutions Engineer)
- Snappi scripts require Python 3.9+

---

## Roadmap

### Planned for v2.1
- [ ] Extended protocol support (OSPF, LDP, MPLS)
- [ ] Multi-pod Ixia-c deployment
- [ ] Enhanced port grouping (LAGs, VLANs)
- [ ] Traffic statistics assertion templates

### Planned for v3.0
- [ ] Web UI for visual config builder
- [ ] Integration with CI/CD pipelines
- [ ] Real-time metrics dashboard
- [ ] Multi-vendor traffic generator support

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting issues, features, and pull requests.

---

## Support & Contact

- **Issues:** Report bugs at [GitHub Issues](https://github.com/anthropics/claude-code/issues)
- **Discussions:** Ask questions at [GitHub Discussions](https://github.com/anthropics/claude-code/discussions)
- **Documentation:** Start with [README.md](README.md) or run `/kengotg-keng-help`
