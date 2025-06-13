# MCP Tools Setup Checklist

## Browser Tools MCP - Quick Setup Guide

### Prerequisites
- Chrome browser with BrowserToolsMCP extension installed
- Node.js/npm available

### Step-by-Step Setup (5 minutes)

#### 1. Start Required Servers
```bash
# Terminal 1: Start MCP server (for IDE integration)
npx @agentdeskai/browser-tools-mcp@latest

# Terminal 2: Start middleware server (for browser connection)
npx @agentdeskai/browser-tools-server@latest
```

#### 2. Verify Server Status
- ✅ `browser-tools-mcp` should be running (check with `ps aux | grep browser-tools-mcp`)
- ✅ `browser-tools-server` should be running on port 3025 (check with `lsof -i :3025`)

#### 3. Activate Extension
1. Open Chrome and navigate to your target page (e.g., `localhost:8080`)
2. Open Chrome DevTools (F12 or right-click → Inspect)
3. Click on **"BrowserToolsMCP"** tab in DevTools
4. Verify connection status shows: "Connected to browser-tools-server v1.2.0 at localhost:3025"
5. **CRITICAL**: Click "Capture Screenshot" button to activate `activeTab` permission

#### 4. Test MCP Tools
Run any MCP browser tool to verify working:
- `takeScreenshot`
- `getConsoleLogs`
- `getNetworkLogs`

### Common Issues & Quick Fixes

#### Connection Errors
**Symptom**: "Failed to discover browser connector server"
**Fix**: Ensure both servers are running (step 1)

#### Permission Errors
**Symptom**: "activeTab permission is not in effect"
**Fix**: Click "Capture Screenshot" in DevTools panel (step 3.5)

#### Screenshot Timeouts
**Symptom**: "Screenshot capture timed out"
**Fixes**:
1. Ensure target tab is active/focused
2. Close all other DevTools instances (keep only one open)
3. Full restart sequence:
   ```bash
   # Quit Chrome completely
   # Ctrl+C both terminal servers
   # Restart both servers (step 1)
   # Reopen Chrome and repeat steps 2-4
   ```

#### Multiple DevTools Issue
**Fix**: Close all DevTools windows except one - extension can't handle multiple instances

### Quick Health Check Commands
```bash
# Check if servers are running
ps aux | grep browser-tools

# Check server port
lsof -i :3025

# Check MCP connection (run in IDE)
# Should return data, not connection errors
takeScreenshot
```

---

## Future Tools Section
*Add other MCP tool setup instructions here as needed*

### Tool Template
```
### [Tool Name] - Quick Setup Guide
#### Prerequisites
- List requirements

#### Step-by-Step Setup
1. Start servers/services
2. Configure connections  
3. Test functionality

#### Common Issues & Fixes
- Issue: Fix
```

---

## Notes
- This checklist was created based on troubleshooting session on 2025-06-02
- Browser Tools MCP requires TWO separate servers + manual activation
- Always test with a simple MCP call before assuming setup is complete 