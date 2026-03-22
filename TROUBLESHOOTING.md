# Troubleshooting Guide

Common issues, root causes, and solutions for the KENG OTG Traffic Testing Plugin.

---

## Quick Checklist

Before diving into specific issues, verify these basics:

```bash
# 1. Plugin installed?
ls ~/.claude/plugins/kengotg/plugin.json

# 2. Commands accessible?
/kengotg-keng-help

# 3. Docker running (if needed)?
docker ps

# 4. Python 3.9+?
python3 --version

# 5. Network connectivity?
ping -c 1 8.8.8.8
```

---

## Deployment Issues

### Port 8443 Already in Use

**Symptom:** Container fails to start, "port 8443: Address already in use"

**Root Cause:** Another container (or process) is using port 8443

**Solutions:**

Option 1 — Stop existing Ixia-c container:
```bash
docker ps | grep ixia
docker stop <container-id>
docker rm <container-id>
```

Option 2 — Use cleanup command:
```bash
/kengotg-cleanup
```

Option 3 — Check what's using the port:
```bash
lsof -i :8443
# Kill the process if it's stale
kill -9 <pid>
```

Option 4 — Deploy on different port:
Contact agent with: `"Deploy Ixia-c on port 8444 instead of 8443"`

**Prevention:** Always run `/kengotg-cleanup` before fresh deployments.

---

### Docker Permission Denied

**Symptom:** `docker: permission denied while trying to connect to the Docker daemon`

**Root Cause:** User is not in the `docker` group

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply changes immediately (or logout/login)
newgrp docker

# Verify
docker ps
```

**Prevention:** Add yourself to docker group after installing Docker.

---

### Docker Daemon Not Running

**Symptom:** `Cannot connect to Docker daemon at unix:///var/run/docker.sock`

**Solution:**

Linux:
```bash
sudo systemctl start docker
sudo systemctl enable docker  # Auto-start on boot
```

macOS:
```bash
# Start Docker Desktop, or:
open /Applications/Docker.app
```

**Verification:**
```bash
docker ps
docker images | head
```

---

### Containerlab: "No such file or directory"

**Symptom:** `containerlab: command not found` or "Failed to find container executable"

**Root Cause:** Containerlab not installed or not in PATH

**Solution:**
```bash
# Install Containerlab
bash -c "$(curl -sL https://get.containerlab.dev)"

# Verify
containerlab version

# Check PATH
which containerlab
```

---

### Insufficient Disk Space

**Symptom:** "No space left on device" during container pull or deployment

**Solution:**
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a  # Remove unused images
docker volume prune      # Remove unused volumes
docker container prune   # Remove stopped containers
```

---

## Configuration Issues

### Port Mapping Mismatch

**Symptom:** Script fails to connect: `Connection refused at localhost:5555`

**Root Cause:** Port mapping between deployment and config doesn't align

**Solutions:**

1. Verify deployment output:
```bash
# Check deployed ports
docker inspect <container-id> | grep PortBindings
```

2. Regenerate config with correct ports:
```bash
# Get actual port mapping
docker ps | grep ixia

# Run `/kengotg-create-test` and provide correct port information
```

3. Manual alignment:
- Get deployment output: `port_mapping.json`
- Verify port names match in config
- Regenerate script with aligned config

**Prevention:** Always pass deployment output to next step (agent orchestration does this automatically).

---

### OTG Config Schema Validation Fails

**Symptom:** `OTG config invalid: violates openapi.yaml schema`

**Root Cause:** Generated config contains unsupported fields or invalid values

**Solutions:**

1. Check schema validation:
```bash
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

2. Validate against openapi.yaml:
```bash
python3 << 'EOF'
import json, yaml
with open('openapi.yaml') as f:
    schema = yaml.safe_load(f)
with open('otg_config.json') as f:
    config = json.load(f)
# Manually verify against schema
EOF
```

3. Regenerate with simpler scenario:
- Start with BGP-only config (no complex traffic)
- Add features incrementally
- Test after each addition

4. Check for unsupported protocols:
- IxNetwork conversion may skip unsupported protocols
- Check conversion report for warnings

---

### Empty or Null Port Locations

**Symptom:** Script fails: `Port location is None/null`

**Root Cause:** Infrastructure deployment didn't return port mapping

**Solution:**
```bash
# 1. Check infrastructure deployment output
docker inspect <ixia-c-id> | grep -A 20 "PortBindings"

# 2. Manually build port_mapping.json
cat > port_mapping.json << 'EOF'
{
  "te1": "localhost:5555",
  "te2": "localhost:5556"
}
EOF

# 3. Regenerate script with explicit port mapping
```

**Prevention:** Use orchestration commands (`/kengotg-create-test`) which handle this automatically.

---

## Script Execution Issues

### Python Import Errors: "No module named 'snappi'"

**Symptom:** `ModuleNotFoundError: No module named 'snappi'`

**Solution:**
```bash
# Install Snappi
pip install snappi>=0.9.0

# Verify
python3 -c "import snappi; print(snappi.__version__)"

# If using venv, activate it first
source ~/.venv/bin/activate
pip install snappi>=0.9.0
```

---

### Python Version Errors

**Symptom:** `SyntaxError` or `TypeError: unsupported operand type(s)`

**Root Cause:** Script generated for Python 3.9+, but older version in use

**Solution:**
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Install/upgrade Python
# macOS
brew install python@3.9

# Linux
sudo apt-get install python3.9

# Verify
python3.9 --version
python3.9 test_*.py
```

---

### Connection Refused: "Cannot reach localhost:8443"

**Symptom:** Script fails: `Connection refused (localhost:8443)`

**Root Cause:** Ixia-c controller not running or not accessible

**Solutions:**

1. Verify container is running:
```bash
docker ps | grep ixia-c-control
# Should show running container
```

2. Verify port is listening:
```bash
netstat -tlnp | grep 8443
# Should show port listening
```

3. Check controller logs:
```bash
docker logs <controller-container-id>
```

4. Redeploy infrastructure:
```bash
/kengotg-cleanup
/kengotg-deploy-ixia
```

---

### BGP Session Not Establishing

**Symptom:** BGP metrics show "0 Sessions Established"

**Root Cause:** Likely misalignment of IP addresses, AS numbers, or port configuration

**Solutions:**

1. Verify BGP config:
```bash
# Check config has correct AS numbers, IPs, neighbors
cat otg_config.json | jq '.devices[].bgp'
```

2. Check script output:
```bash
# Run with verbose output
python3 test_bgp.py 2>&1 | head -50
```

3. Verify port connectivity:
```bash
# Ensure both ports are up and connected
docker exec <container> ip link show
```

4. Validate against topology:
- Ensure 2+ ports with different subnets
- Verify AS numbers differ between peers
- Check no IP conflicts

---

### Script Hangs or Times Out

**Symptom:** Script runs but doesn't complete, or "timeout waiting for BGP sessions"

**Root Cause:** Likely infrastructure not fully initialized or protocol startup too slow

**Solutions:**

1. Increase timeout in script:
```python
# In generated script, find:
time.sleep(30)  # Wait for BGP to establish
# Change to:
time.sleep(60)  # Give more time
```

2. Check infrastructure health:
```bash
# Wait for traffic engines to be ready
docker ps -a | grep traffic-engine
# All should be healthy/running
```

3. Monitor with separate terminal:
```bash
# In another terminal, watch container logs
docker logs -f <ixia-c-id>
```

4. Reduce test complexity:
- Start with 2 ports, 1 session
- Add complexity incrementally

---

## Migration Issues

### IxNetwork Config Not Found or Unreadable

**Symptom:** `/ixnetwork-to-keng-converter` fails to read file

**Root Cause:** File path incorrect or format unsupported

**Solutions:**

1. Verify file exists and is readable:
```bash
file /path/to/config.json
cat /path/to/config.json | head
```

2. Supported formats:
- IxNetwork JSON config files (.json)
- IxNetwork RestPy Python code (.py)

3. Try inline paste instead:
```bash
# Copy file contents and paste directly into /ixnetwork-to-keng-converter
```

---

### Unsupported IxNetwork Features

**Symptom:** Conversion report lists "unsupported features" with "blocker" severity

**Root Cause:** IxNetwork config uses features not available in OTG

**Solution:**

1. Check conversion report:
```bash
# Look for "blockers" in the report
# Examples: Multicast, QoS, advanced encapsulation
```

2. Simplify IxNetwork config:
- Remove unsupported features
- Keep core protocols (BGP, Ethernet, IPv4, VLAN)
- Test with simplified version first

3. Use as reference only:
- If migration not feasible, use IxNetwork config as requirements
- Manually build OTG config with `/kengotg-otg-gen`

---

## Command Issues

### Commands Not Visible or Recognized

**Symptom:** `/kengotg-*` command not found

**Root Cause:** Plugin not loaded or commands directory missing

**Solutions:**

1. Reload Claude Code:
```bash
claude --reload
claude --clear-cache
```

2. Verify commands directory:
```bash
ls -la ~/.claude/plugins/kengotg/.claude/commands/
# Should show: *.md files for each command
```

3. Restart Claude Code:
```bash
# Exit and re-open Claude Code application
```

---

### "Ambiguous command" or "Multiple matches"

**Symptom:** `/kengotg` matches multiple commands

**Solution:** Use full command name:
```bash
/kengotg-create-test     # Instead of /kengotg
/kengotg-show-skills
/kengotg-deploy-ixia
```

---

## Agent Invocation Issues

### Agent Timeout or No Response

**Symptom:** Agent doesn't respond within expected time

**Root Cause:** Complex operation taking longer than timeout, or network issues

**Solutions:**

1. Check Claude Code timeout setting:
```bash
claude --settings
# Look for "timeout" setting, increase to 300+ seconds
```

2. Check system resources:
```bash
top -n 1 | head -20  # CPU/memory usage
free -h              # Available memory
```

3. Retry operation:
```bash
# Wait a moment and try again
# Or simplify input (fewer ports, simpler config)
```

---

### Agent Returns Unexpected Output

**Symptom:** Agent output doesn't match expected format (missing JSON, malformed config)

**Root Cause:** Agent confusion, ambiguous intent, or parsing error

**Solution:**

1. Check agent specification:
```bash
cat .claude/agents/<agent-name>.md
# Review expected inputs/outputs
```

2. Clarify intent in new request:
- Be more specific about requirements
- Provide examples or templates
- Avoid ambiguous language

3. Check evaluation test cases:
```bash
cat .claude/agents/eval-sets/<agent>-eval.json
# Review successful question patterns
```

---

## General Troubleshooting

### "Permission Denied" Errors

```bash
# Check file permissions
ls -la <file>

# Fix ownership if needed
sudo chown $USER:$USER ~/.claude/plugins/kengotg -R

# Fix permissions
chmod +x ~/.claude/plugins/kengotg/.claude/agents/*.sh
```

### "Command not found" Errors

```bash
# Verify PATH includes necessary directories
echo $PATH

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

### Stale State or Cached Data

```bash
# Clear Claude Code cache
claude --clear-cache

# Remove generated files
rm -f otg_config.json config.yaml port_mapping.json

# Full cleanup
/kengotg-cleanup
```

---

## Reporting Issues

If you encounter a problem not listed here:

### 1. Collect Diagnostic Information
```bash
# System info
uname -a
python3 --version
docker --version

# Plugin info
ls -la ~/.claude/plugins/kengotg/

# Recent errors (last 50 lines)
# Copy relevant error messages
```

### 2. Create a Minimal Reproducible Example
- Simplify your test case to smallest failing scenario
- Document exact steps to reproduce
- Include input files/configs

### 3. Submit Issue
- [GitHub Issues](https://github.com/anthropics/claude-code/issues)
- Include diagnostics from step 1
- Include reproducible example from step 2

---

## FAQ

**Q: Do I need all 4 agents for a test?**
A: No. Use only what you need:
- Just config? → otg-config-generator-agent
- Just deployment? → ixia-c-deployment-agent
- Full pipeline? → All 3 sequentially

**Q: Can I run multiple tests in parallel?**
A: Yes, but on different ports/containers. Clean up between test runs with `/kengotg-cleanup`.

**Q: What's the minimum test setup?**
A: 2 ports, 1 protocol (BGP/ISIS/etc), deployed Ixia-c. Start simple, add complexity.

**Q: How do I debug a failed Snappi script?**
A: Add debug prints, check Docker logs, verify port mapping, increase timeouts.

**Q: Does this work on Windows?**
A: Windows 10/11 with WSL2 is supported. Follow Linux installation inside WSL.

---

## Support Resources

- **Documentation:** [README.md](README.md), [CLAUDE.md](CLAUDE.md), [AGENT_ORCHESTRATION_PLAN.md](AGENT_ORCHESTRATION_PLAN.md)
- **Quick Start:** `/kengotg-keng-help`
- **Skills Reference:** `/kengotg-show-skills`
- **Agent Reference:** `/kengotg-show-agents`
- **Examples:** `/kengotg-examples`
- **GitHub Issues:** [Report a Bug](https://github.com/anthropics/claude-code/issues)

---

**Still stuck?** Run `/help` for general Claude Code assistance or check the logs with verbose output enabled.
