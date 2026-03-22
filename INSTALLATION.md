# Installation Guide

Complete setup instructions for the KENG OTG Traffic Testing Plugin.

---

## Prerequisites

Before installing, ensure you have:

### System Requirements
- **OS:** Linux or macOS (Windows with WSL2 supported)
- **Memory:** 4GB+ RAM (8GB+ recommended for Ixia-c deployments)
- **Disk:** 10GB+ free space
- **Network:** Stable internet connection (for Docker image pulls)

### Required Software

#### 1. Claude Code v1.0+
Install Claude Code:
```bash
curl -fsSL https://install.claude.ai | bash
```

Verify installation:
```bash
claude --version
```

#### 2. Docker (for Infrastructure Deployment)
If using `ixia-c-deployment` or `/kengotg-deploy-ixia`:

```bash
# macOS (Homebrew)
brew install docker

# Linux (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker $USER
```

Verify:
```bash
docker --version
docker ps  # Should return container list (no errors)
```

**Note:** If you get permission errors, add your user to the docker group:
```bash
sudo usermod -aG docker $USER
# Log out and back in, or:
newgrp docker
```

#### 3. Containerlab (Optional, for Topology-Based Deployments)
If using containerized topologies:

```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

Verify:
```bash
containerlab version
```

#### 4. Python 3.9+
For Snappi script generation and execution:

```bash
# macOS
brew install python@3.9

# Linux
sudo apt-get install python3.9 python3-pip

# Verify
python3 --version
```

---

## Installation Methods

### Method 1: Install from Local Directory (Recommended for Development)

```bash
# Navigate to plugin directory
cd /path/to/kengotg

# Install as Claude Code plugin
claude code install .

# Or manually copy to Claude's plugin directory:
mkdir -p ~/.claude/plugins
cp -r . ~/.claude/plugins/kengotg
```

### Method 2: Install from Git Repository

```bash
# Clone the repository
git clone https://github.com/anthropics/claude-code.git
cd claude-code/plugins/kengotg

# Install
claude code install .
```

### Method 3: Manual Installation

```bash
# Copy plugin files
mkdir -p ~/.claude/plugins/kengotg
cp -r .claude/commands ~/.claude/plugins/kengotg/
cp -r .claude/agents ~/.claude/plugins/kengotg/
cp -r .claude/skills ~/.claude/plugins/kengotg/
cp *.md openapi.yaml plugin.json ~/.claude/plugins/kengotg/
```

---

## Post-Installation Verification

### 1. Verify Plugin Discovery
```bash
claude --list-plugins
# Should show: kengotg (KENG OTG Traffic Testing)
```

### 2. Run Help Command
```bash
/kengotg-keng-help
# Should display: Plugin overview & quick start
```

### 3. Test Skill Discovery
```bash
/kengotg-show-skills
# Should list: 5 production-ready skills
```

### 4. Test Agent Discovery
```bash
/kengotg-show-agents
# Should list: 4 intelligent subagents
```

### 5. Verify Docker Integration (Optional)
```bash
docker ps
# Should return container list without errors
```

---

## First-Time Setup: Quick Start Workflow

After installation, try one of these workflows:

### Quick Path: BGP Test in 2 Minutes
```bash
/kengotg-quick-bgp-test 4 ports
```
Creates a BGP test with 4 ports, deploys Ixia-c, generates script.

### Full Path: Custom Test
```bash
/kengotg-create-test
# Follow interactive prompts to:
# 1. Describe your test scenario
# 2. Deploy infrastructure
# 3. Generate OTG config
# 4. Generate Snappi script
# 5. Execute test
```

### Learning Path: Explore Examples
```bash
/kengotg-keng-help          # Understand the plugin
/kengotg-show-skills        # See what's available
/kengotg-examples           # Find a matching scenario
/kengotg-show-architecture  # Understand architecture
```

---

## Configuration

### Environment Variables (Optional)

Set these to customize behavior:

```bash
# OTG Schema location (optional)
export OTG_SCHEMA_PATH="/path/to/openapi.yaml"

# Ixia-c Controller URL (optional, defaults to localhost:8443)
export IXIA_C_URL="https://localhost:8443"

# Timeout for infrastructure deployment (seconds)
export IXIA_C_DEPLOY_TIMEOUT="300"

# Enable debug logging
export CLAUDE_DEBUG=1
```

Add to `~/.bashrc` or `~/.zshrc` to persist:
```bash
echo 'export OTG_SCHEMA_PATH="/home/ubuntu/otg-claude-skill/openapi.yaml"' >> ~/.bashrc
source ~/.bashrc
```

### Plugin Settings (Optional)

Configure via Claude Code settings:
```bash
claude --settings
```

Key settings:
- **Model:** Use Opus 4.6 or Sonnet 4.6 for best results
- **Timeout:** Set to 120+ seconds for large deployments
- **Permissions:** Ensure Docker and Bash commands are allowed

---

## Troubleshooting Installation Issues

### Issue: "Plugin not found" after installation

**Solution:**
```bash
# 1. Verify plugin location
ls -la ~/.claude/plugins/kengotg/plugin.json

# 2. Reload Claude Code
claude --clear-cache
claude --reload

# 3. Check for syntax errors in plugin.json
python3 -m json.tool plugin.json
```

### Issue: Docker permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Verify
docker ps
```

### Issue: "Command not found: /kengotg-*"

**Solution:**
```bash
# 1. Verify commands directory
ls -la ~/.claude/plugins/kengotg/.claude/commands/

# 2. Check COMMANDS.md exists
ls -la ~/.claude/plugins/kengotg/.claude/commands/COMMANDS.md

# 3. Reload Claude
claude --reload
```

### Issue: Port 8443 already in use

**Solution:**
```bash
# Option 1: Stop existing container
docker ps | grep ixia-c
docker stop <container-id>

# Option 2: Use cleanup command
/kengotg-cleanup

# Option 3: Check what's using port 8443
lsof -i :8443
```

### Issue: "Python version" errors

**Solution:**
```bash
# Install Python 3.9+
python3 --version

# If needed, create venv
python3 -m venv ~/.venv
source ~/.venv/bin/activate

# Install Snappi
pip install snappi>=0.9.0
```

---

## Dependency Installation

### For Snappi Script Execution

Install the Snappi SDK:
```bash
pip install snappi>=0.9.0
```

Verify:
```bash
python3 -c "import snappi; print(snappi.__version__)"
```

### For IxNetwork Migration

Install REST client:
```bash
pip install requests>=2.28.0 pyyaml>=6.0
```

### For All Features

Install all dependencies:
```bash
pip install snappi>=0.9.0 requests>=2.28.0 pyyaml>=6.0
```

---

## System Integration

### Add Claude Code to PATH (Optional)

```bash
# If not already in PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Configure IDE Integration (Optional)

#### VS Code
```json
{
  "editor.codeLens": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python"
  }
}
```

---

## Verification Checklist

After installation, verify these work:

- [ ] `claude --version` returns v1.0+
- [ ] `docker --version` returns v20.10+
- [ ] `python3 --version` returns v3.9+
- [ ] `which containerlab` shows path (optional)
- [ ] `ls ~/.claude/plugins/kengotg/plugin.json` shows file
- [ ] `/kengotg-keng-help` displays without errors
- [ ] `/kengotg-show-skills` lists 5 skills
- [ ] `/kengotg-show-agents` lists 4 agents
- [ ] `docker ps` shows containers (if Docker available)

---

## Uninstallation

To remove the plugin:

```bash
# Option 1: Via Claude Code
claude code uninstall kengotg

# Option 2: Manual removal
rm -rf ~/.claude/plugins/kengotg
```

Clean up leftover containers:
```bash
/kengotg-cleanup
```

---

## Getting Help

### Documentation
- **Start here:** `README.md`
- **Architecture:** `AGENT_ORCHESTRATION_PLAN.md`
- **Troubleshooting:** `TROUBLESHOOTING.md` (this file)
- **Skills:** Run `/kengotg-show-skills`
- **Agents:** Run `/kengotg-show-agents`

### Support
- **Issues:** [GitHub Issues](https://github.com/anthropics/claude-code/issues)
- **Discussions:** [GitHub Discussions](https://github.com/anthropics/claude-code/discussions)
- **Quick Help:** Run `/kengotg-keng-help` or `/help`

---

## Next Steps

1. **Run verification:** `./verify-install.sh` (if provided)
2. **Explore examples:** `/kengotg-examples`
3. **Try quick BGP test:** `/kengotg-quick-bgp-test 4 ports`
4. **Build custom test:** `/kengotg-create-test`

---

**Installation complete!** You're ready to use the KENG OTG Traffic Testing Plugin. Start with `/kengotg-keng-help` for an overview.
