// AI Cliché Detection Suite — Electron shell.
// M0: window over the local suite.  M1a: auto-start/stop the model sidecar.
// (M1b will swap the sidecar to a bundled ONNX runtime; M2 packages it to an installer.)
const { app, BrowserWindow, Menu, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

// dev: the ai-cliche-db folder one level up. packaged: extraResources land in resources/suite.
const SUITE_ROOT = app.isPackaged ? path.join(process.resourcesPath, 'suite') : path.join(__dirname, '..');
const MODEL_SCRIPT = path.join(SUITE_ROOT, 'server', 'perplexity_server.py');
// where to find a python that can run the model. Bundled ONNX python (M2) is tried first,
// then the ComfyUI embedded python (this machine), then the PATH python.
const PY_CANDIDATES = [
  path.join(SUITE_ROOT, 'server', 'pyenv', 'python.exe'),      // future bundled env (M2)
  'D:\\AI\\ComfyUI_windows_portable\\python_embeded\\python.exe',
  'python',
];

let win = null;
let modelProc = null;
let modelState = 'off';                                         // off | starting | on

function findPython() {
  for (const p of PY_CANDIDATES) {
    if (p === 'python' || fs.existsSync(p)) return p;
  }
  return null;
}

function modelHealth(cb) {
  const req = http.get('http://127.0.0.1:8770/health', { timeout: 1500 }, (res) => {
    res.resume(); cb(res.statusCode === 200);
  });
  req.on('error', () => cb(false));
  req.on('timeout', () => { req.destroy(); cb(false); });
}

function startModel() {
  modelHealth((up) => {
    if (up) { modelState = 'on'; return; }                     // already running (manual start) — reuse
    const py = findPython();
    if (!py || !fs.existsSync(MODEL_SCRIPT)) {
      modelState = 'off';
      console.warn('[suite] model python/script not found — tools run on stylometry + DB only.');
      return;
    }
    modelState = 'starting';
    try {
      const modelsDir = path.join(SUITE_ROOT, 'server', 'models');
      const env = { ...process.env };
      if (fs.existsSync(modelsDir)) { env.HF_HOME = modelsDir; env.HF_HUB_OFFLINE = '1'; env.TRANSFORMERS_OFFLINE = '1'; }
      modelProc = spawn(py, [MODEL_SCRIPT], {
        cwd: path.join(SUITE_ROOT, 'server'), windowsHide: true, env,
        stdio: ['ignore', 'ignore', 'ignore'],
      });
      modelProc.on('exit', () => { modelProc = null; modelState = 'off'; });
      modelProc.on('error', (e) => { modelProc = null; modelState = 'off'; console.warn('[suite] model spawn failed:', e.message); });
      // poll until the model finishes loading, just to update our state
      let tries = 0;
      const poll = setInterval(() => {
        tries++;
        modelHealth((u) => { if (u) { modelState = 'on'; clearInterval(poll); } });
        if (tries > 40) clearInterval(poll);                   // ~80s cap
      }, 2000);
    } catch (e) {
      modelState = 'off'; console.warn('[suite] model spawn threw:', e.message);
    }
  });
}

function stopModel() {
  if (modelProc) { try { modelProc.kill(); } catch (e) {} modelProc = null; }
  modelState = 'off';
}

function createWindow() {
  win = new BrowserWindow({
    width: 1320, height: 880, minWidth: 900, minHeight: 600,
    backgroundColor: '#0b0e14', title: 'AI Cliché Detection Suite',
    autoHideMenuBar: true,
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  });
  win.loadFile(path.join(SUITE_ROOT, 'index.html'));
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) { shell.openExternal(url); return { action: 'deny' }; }
    return { action: 'allow' };
  });
  win.on('closed', () => { win = null; });
}

function buildMenu() {
  const tools = [
    ['Complete (all-in-one)', 'apps/complete.html'],
    ['Song Compare', 'apps/song-compare.html'],
    ['Song Forensics', 'apps/song-forensics.html'],
    ['AI Detector', 'apps/ai-detector.html'],
    ['Cliché Catcher', 'apps/cliche-catcher.html'],
    ['Lyric Check', 'apps/lyric-check.html'],
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    {
      label: 'Suite',
      submenu: [
        { label: 'Home / Launcher', accelerator: 'CmdOrCtrl+H', click: () => win && win.loadFile(path.join(SUITE_ROOT, 'index.html')) },
        { type: 'separator' },
        ...tools.map(([label, rel]) => ({ label, click: () => win && win.loadFile(path.join(SUITE_ROOT, rel)) })),
        { type: 'separator' },
        { label: 'Open exports folder', click: () => shell.openPath(path.join(SUITE_ROOT, 'exports')) },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'Model',
      submenu: [
        { label: 'Restart local model', click: () => { stopModel(); setTimeout(startModel, 400); } },
        { label: 'Stop local model', click: () => stopModel() },
        { label: 'Status…', click: () => modelHealth((u) => { const { dialog } = require('electron'); dialog.showMessageBox(win, { message: u ? 'Local model: ON (localhost:8770)' : 'Local model: off — tools run on stylometry + database.', buttons: ['OK'] }); }) },
      ],
    },
    { label: 'View', submenu: [{ role: 'reload' }, { role: 'forceReload' }, { role: 'toggleDevTools' }, { type: 'separator' }, { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' }, { type: 'separator' }, { role: 'togglefullscreen' }] },
  ]));
}

app.whenReady().then(() => {
  buildMenu();
  startModel();                                                // auto-start the model with the app
  createWindow();
  app.on('activate', () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});

app.on('before-quit', stopModel);                              // auto-stop the model on quit
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
