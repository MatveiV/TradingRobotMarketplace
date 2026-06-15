import { useState, useRef } from "react";
import { X, Upload, Globe, Play, CheckCircle, AlertCircle, Loader, Plug } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { customFetch } from "@/lib/api-client/custom-fetch";

interface Props {
  strategyId: number;
  strategyName: string;
  open: boolean;
  onClose: () => void;
}

type TabMode = "connect" | "upload";

export default function DeployDialog({ strategyId, strategyName, open, onClose }: Props) {
  const [mode, setMode] = useState<TabMode>("connect");
  const [mtVersion, setMtVersion] = useState<4 | 5>(4);
  const [robotFile, setRobotFile] = useState<File | null>(null);
  const [setFile, setSetFile] = useState<File | null>(null);
  const [downloadUrl, setDownloadUrl] = useState("");
  const [accountLogin, setAccountLogin] = useState("");
  const [accountPassword, setAccountPassword] = useState("");
  const [accountServer, setAccountServer] = useState("");
  const [tradeSymbol, setTradeSymbol] = useState("EURUSD");
  const [tradePeriod, setTradePeriod] = useState("H1");
  const [terminalPath, setTerminalPath] = useState("");
  const [deploying, setDeploying] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [error, setError] = useState("");
  const robotRef = useRef<HTMLInputElement>(null);
  const setRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  const addLog = (msg: string) => setLog(prev => [...prev, msg]);

  const handleConnect = async () => {
    setError("");
    setLog([]);
    setDeploying(true);

    try {
      if (mode === "upload") {
        if (!robotFile) { setError("Select robot file (.ex4 / .ex5)"); setDeploying(false); return; }
        addLog(`Uploading ${robotFile.name}...`);
        const fd = new FormData();
        fd.append("file", robotFile);
        fd.append("mt_version", String(mtVersion));
        const uploadRes = await customFetch(`/api/strategies/${strategyId}/deploy/upload`, { method: "POST", body: fd });
        addLog(`Uploaded: ${(uploadRes as any).filename}`);
      }

      if (downloadUrl) {
        addLog(`Downloading from ${downloadUrl}...`);
        const fd2 = new FormData();
        fd2.append("url", downloadUrl);
        fd2.append("filename", downloadUrl.split("/").pop() || "robot.ex4");
        fd2.append("mt_version", String(mtVersion));
        const dlRes = await customFetch(`/api/strategies/${strategyId}/deploy/url`, { method: "POST", body: fd2 });
        addLog(`Downloaded: ${(dlRes as any).filename}`);
      }

      addLog("Connecting strategy to account...");
      const fd3 = new FormData();
      fd3.append("account_login", accountLogin);
      fd3.append("account_password", accountPassword);
      fd3.append("account_server", accountServer);
      fd3.append("mt_version", String(mtVersion));
      fd3.append("trade_symbol", tradeSymbol);
      fd3.append("trade_period", tradePeriod);
      fd3.append("terminal_path", terminalPath);
      const res = await customFetch(`/api/strategies/${strategyId}/connect-account`, { method: "POST", body: fd3 });
      const msg = (res as any).message || "Connected successfully";
      addLog(msg);
      addLog("Done! MetaTrader is launching...");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Connection failed";
      setError(msg);
      addLog(`Error: ${msg}`);
    } finally {
      setDeploying(false);
    }
  };

  const statusIcon = (msg: string) => {
    if (msg.startsWith("Error") || msg.startsWith("Connected") || msg.startsWith("Done")) {
      return msg.startsWith("Error") ? "error" : "ok";
    }
    return "pending";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold">Connect: {strategyName}</h2>
          <button onClick={() => { setLog([]); setError(""); onClose(); }} className="p-1 rounded-full hover:bg-gray-100 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* MT Version */}
          <div>
            <Label>MetaTrader Version</Label>
            <div className="flex gap-3 mt-1.5">
              <button onClick={() => setMtVersion(4)}
                className={`flex-1 py-2.5 rounded-lg border text-sm font-medium transition-colors ${mtVersion === 4 ? "bg-[#111] text-white border-[#111]" : "bg-white hover:bg-gray-50"}`}>MT4</button>
              <button onClick={() => setMtVersion(5)}
                className={`flex-1 py-2.5 rounded-lg border text-sm font-medium transition-colors ${mtVersion === 5 ? "bg-[#111] text-white border-[#111]" : "bg-white hover:bg-gray-50"}`}>MT5</button>
            </div>
          </div>

          {/* Mode tabs */}
          <div>
            <Label>Robot file source</Label>
            <div className="flex gap-3 mt-1.5">
              <button onClick={() => setMode("connect")}
                className={`flex items-center gap-2 flex-1 py-2.5 rounded-lg border text-sm font-medium transition-colors ${mode === "connect" ? "bg-[#111] text-white border-[#111]" : "bg-white hover:bg-gray-50"}`}>
                <Plug className="w-4 h-4" />Use strategy files
              </button>
              <button onClick={() => setMode("upload")}
                className={`flex items-center gap-2 flex-1 py-2.5 rounded-lg border text-sm font-medium transition-colors ${mode === "upload" ? "bg-[#111] text-white border-[#111]" : "bg-white hover:bg-gray-50"}`}>
                <Upload className="w-4 h-4" />Upload own files
              </button>
            </div>
          </div>

          {mode === "upload" && (
            <div className="space-y-3">
              <div>
                <Label>Robot file (.ex4 / .ex5)</Label>
                <div onClick={() => robotRef.current?.click()}
                  className="mt-1.5 border-2 border-dashed rounded-lg p-4 text-center cursor-pointer hover:bg-gray-50 transition-colors">
                  {robotFile ? (
                    <div className="flex items-center justify-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-positive" />
                      <span className="font-medium">{robotFile.name}</span>
                      <span className="text-muted-foreground">({(robotFile.size / 1024).toFixed(1)} KB)</span>
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      <Upload className="w-6 h-6 mx-auto mb-1 opacity-50" />
                      Click to select .ex4 / .ex5 file
                    </div>
                  )}
                  <input ref={robotRef} type="file" accept=".ex4,.ex5" className="hidden" onChange={e => setRobotFile(e.target.files?.[0] || null)} />
                </div>
              </div>
              <div>
                <Label>Settings file (.set) — optional</Label>
                <div onClick={() => setRef.current?.click()}
                  className="mt-1.5 border-2 border-dashed rounded-lg p-4 text-center cursor-pointer hover:bg-gray-50 transition-colors">
                  {setFile ? (
                    <div className="flex items-center justify-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-positive" />
                      <span className="font-medium">{setFile.name}</span>
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      <Upload className="w-5 h-5 mx-auto mb-1 opacity-50" />
                      Click to select .set file
                    </div>
                  )}
                  <input ref={setRef} type="file" accept=".set" className="hidden" onChange={e => setSetFile(e.target.files?.[0] || null)} />
                </div>
              </div>
              <div>
                <Label>Or download URL</Label>
                <Input placeholder="https://example.com/robot.ex4" value={downloadUrl} onChange={e => setDownloadUrl(e.target.value)} />
              </div>
            </div>
          )}

          {/* Account credentials */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Plug className="w-4 h-4" /> Trading Account
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label className="text-xs">Login</Label>
                <Input className="mt-1" placeholder="Login" value={accountLogin} onChange={e => setAccountLogin(e.target.value)} />
              </div>
              <div>
                <Label className="text-xs">Password</Label>
                <Input className="mt-1" type="password" placeholder="Password" value={accountPassword} onChange={e => setAccountPassword(e.target.value)} />
              </div>
              <div>
                <Label className="text-xs">Server</Label>
                <Input className="mt-1" placeholder="Server" value={accountServer} onChange={e => setAccountServer(e.target.value)} />
              </div>
            </div>
          </div>

          {/* Chart settings */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="text-sm font-medium">Chart Settings</div>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label className="text-xs">Symbol</Label>
                <Input className="mt-1" value={tradeSymbol} onChange={e => setTradeSymbol(e.target.value)} />
              </div>
              <div>
                <Label className="text-xs">Period</Label>
                <select className="mt-1 w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm"
                  value={tradePeriod} onChange={e => setTradePeriod(e.target.value)}>
                  <option value="M1">M1</option><option value="M5">M5</option><option value="M15">M15</option>
                  <option value="M30">M30</option><option value="H1">H1</option><option value="H4">H4</option>
                  <option value="D1">D1</option><option value="W1">W1</option><option value="MN">MN</option>
                </select>
              </div>
              <div>
                <Label className="text-xs">Terminal path</Label>
                <Input className="mt-1" placeholder="Auto" value={terminalPath} onChange={e => setTerminalPath(e.target.value)} />
              </div>
            </div>
          </div>

          {/* Log */}
          {log.length > 0 && (
            <div className="border rounded-lg p-4 space-y-1.5 bg-gray-50/50 text-sm">
              <div className="text-xs font-medium uppercase tracking-wider text-muted-foreground mb-2">Deployment Log</div>
              {log.map((msg, i) => (
                <div key={i} className="flex items-start gap-2">
                  {msg.startsWith("Error") ? <AlertCircle className="w-3.5 h-3.5 text-destructive mt-0.5 shrink-0" />
                    : msg.startsWith("Done") ? <CheckCircle className="w-3.5 h-3.5 text-positive mt-0.5 shrink-0" />
                    : <Loader className="w-3.5 h-3.5 animate-spin text-muted-foreground mt-0.5 shrink-0" />}
                  <span className={msg.startsWith("Error") ? "text-destructive" : ""}>{msg}</span>
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="text-sm text-destructive bg-destructive/5 rounded-lg p-3 border border-destructive/10">{error}</div>
          )}

          <div className="flex gap-3 pt-2">
            <Button variant="outline" className="flex-1" onClick={() => { setLog([]); setError(""); onClose(); }} disabled={deploying}>Cancel</Button>
            <Button className="flex-1 bg-[#111] hover:bg-black/90 gap-2" onClick={handleConnect} disabled={deploying}>
              {deploying ? <><Loader className="w-4 h-4 animate-spin" /> Connecting...</>
                : <><Plug className="w-4 h-4" /> Connect to MT{mtVersion}</>}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
