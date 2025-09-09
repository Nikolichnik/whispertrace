import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, Play, RefreshCcw, Database, ShieldCheck, NotebookText, Globe, Plus, BrainCircuit, Bug, WifiOff, Info } from "lucide-react";

/**
 * WhisperTrace Frontend — Single-file React UI (CORS/Network-hardened)
 *
 * Styling: Tailwind + shadcn/ui; lightweight and deployable as a static SPA.
 */

// ===== Helper types matching OpenAPI spec =====

type Corpus = { name: string; content?: string };

type SyntheticCorpusReq = { name?: string; n: number };

type WebScrapedCorpusReq = { name?: string; url: string };

type Checkpoint = {
  name: string;
  corpus: string;
  epochs?: number;
  batch_size?: number;
  learning_rate?: number;
};

type MiaReq = {
  checkpoint: string;
  corpus: string;
  batch_size?: number;
  input?: string;
};

// ===== Utilities =====

function joinUrl(base: string, path: string) {
  const b = base.replace(/\/$/, "");
  const p = path.replace(/^\//, "");
  try { return new URL(`${b}/${p}`).toString(); } catch { return `${b}/${p}`; }
}

function isCrossOrigin(base: string) {
  try { return new URL(base).origin !== window.location.origin; } catch { return true; }
}

async function withTimeout<T>(promise: Promise<T>, ms = 15000000, label = "request") {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    // @ts-ignore
    const res = await promise(ctrl.signal);
    return res;
  } finally {
    clearTimeout(t);
  }
}

function humanizeFetchError(e: any, baseUrl: string) {
  const msg = (e?.message || "Failed to fetch").toString();
  const hints: string[] = [];

  if (msg.includes("Failed to fetch") || msg.includes("abort")) {
    hints.push("• Check that the API server is running and reachable.");
    const cross = isCrossOrigin(baseUrl);
    if (cross) hints.push("• This looks cross-origin. Ensure the Flask API sends CORS headers (e.g., Flask-CORS).\n  Access-Control-Allow-Origin: <your-frontend-origin>");
    hints.push("• Verify API Base URL and port are correct.");
  }

  return `${msg}${hints.length ? "\n\nTroubleshooting:\n" + hints.join("\n") : ""}`;
}

// ===== Small fetch wrapper (explicit CORS + timeout + better errors) =====

function useApi(baseUrl: string) {
  const get = async (path: string) => {
    const url = joinUrl(baseUrl, path);
    const doFetch = async (signal?: AbortSignal) => fetch(url, { method: "GET", mode: "cors", signal });
    let res: Response;
    try {
      res = await withTimeout((signal: AbortSignal)=>doFetch(signal));
    } catch (e: any) {
      throw new Error(humanizeFetchError(e, baseUrl));
    }
    if (!res.ok) {
      let errText = `${res.status} ${res.statusText}`;
      try { const j = await res.json(); errText = j?.message || JSON.stringify(j); } catch {}
      throw new Error(errText);
    }
    return res.json();
  };

  const post = async (path: string, body: any) => {
    const url = joinUrl(baseUrl, path);
    const doFetch = async (signal?: AbortSignal) => fetch(url, {
      method: "POST",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
    let res: Response;
    try {
      res = await withTimeout((signal: AbortSignal)=>doFetch(signal));
    } catch (e: any) {
      throw new Error(humanizeFetchError(e, baseUrl));
    }
    if (!res.ok) {
      let errText = `${res.status} ${res.statusText}`;
      try { const j = await res.json(); errText = j?.message || JSON.stringify(j); } catch {}
      throw new Error(errText);
    }
    return res.json();
  };
  return { get, post };
}

// ===== Pretty JSON component =====

const JsonBlock: React.FC<{ data: any }> = ({ data }) => (
  <pre className="whitespace-pre-wrap rounded-md bg-muted p-3 text-sm overflow-auto max-h-96">
    {JSON.stringify(data, null, 2)}
  </pre>
);

// ===== Banner for cross-origin tip =====

const CrossOriginBanner: React.FC<{ baseUrl: string }>=({ baseUrl })=>{
  if (!isCrossOrigin(baseUrl)) return null;

  return (
    <Alert className="border-amber-400 bg-amber-50">
      <AlertTitle className="flex items-center gap-2"><Info className="w-4 h-4"/> Cross-origin request</AlertTitle>
      <AlertDescription className="text-sm">
        Note: API base (<span className="font-mono">{baseUrl}</span>) differs from this page's origin (<span className="font-mono">{window.location.origin}</span>).
        If requests fail with <em>Failed to fetch</em>, enable CORS on the Flask API (e.g., <span className="font-mono">flask-cors</span>) or serve the UI from the same origin.
      </AlertDescription>
    </Alert>
  );
};

// ===== Main App =====

export default function App() {
  const defaultPort = import.meta.env.VITE_WHISPERTRACE_API_PORT || "5001";
  const [baseUrl, setBaseUrl] = useState<string>(`http://localhost:${defaultPort}`);
  const api = useMemo(() => useApi(baseUrl), [baseUrl]);

  // corpora
  const [corpora, setCorpora] = useState<Corpus[] | null>(null);
  const [loadingCorpora, setLoadingCorpora] = useState(false);
  const [corporaError, setCorporaError] = useState<string | null>(null);

  const refreshCorpora = async () => {
    setLoadingCorpora(true); setCorporaError(null);
    try {
      const data = await api.get("corpora");
      setCorpora(data as Corpus[]);
    } catch (e: any) {
      setCorpora([]);
      setCorporaError(e.message || String(e));
    } finally {
      setLoadingCorpora(false);
    }
  };

  // checkpoints
  const [checkpoints, setCheckpoints] = useState<Checkpoint[] | null>(null);
  const [loadingCheckpoints, setLoadingCheckpoints] = useState(false);
  const [checkpointsError, setCheckpointsError] = useState<string | null>(null);

  const refreshCheckpoints = async () => {
    setLoadingCheckpoints(true); setCheckpointsError(null);
    try {
      const data = await api.get("checkpoints");
      setCheckpoints(data as Checkpoint[]);
    } catch (e: any) {
      setCheckpoints([]);
      setCheckpointsError(e.message || String(e));
    } finally {
      setLoadingCheckpoints(false);
    }
  };

  // auto-load on mount & baseUrl change
  useEffect(() => {
    refreshCorpora();
    refreshCheckpoints();
  }, [baseUrl]);

  // form state — synthetic corpus
  const [synName, setSynName] = useState("");
  const [synN, setSynN] = useState<number>(2000);
  const [creatingSyn, setCreatingSyn] = useState(false);
  const createSynthetic = async () => {
    setCreatingSyn(true);
    try {
      const payload: SyntheticCorpusReq = { n: synN };
      if (synName) payload.name = synName;
      const res = await api.post("corpora/synthetic", payload);
      await refreshCorpora();
      showToast(`Synthetic corpus created: ${res?.name || "ok"}`, "success");
    } catch (e: any) {
      showToast(`Error: ${e.message}`, "error");
    } finally { setCreatingSyn(false); }
  };

  // form state — web corpus
  const [webName, setWebName] = useState("");
  const [webUrl, setWebUrl] = useState("");
  const [creatingWeb, setCreatingWeb] = useState(false);
  const createWeb = async () => {
    setCreatingWeb(true);
    try {
      const payload: WebScrapedCorpusReq = { url: webUrl };
      if (webName) payload.name = webName;
      const res = await api.post("corpora/web", payload);
      await refreshCorpora();
      showToast(`Web corpus created: ${res?.name || "ok"}`, "success");
    } catch (e: any) {
      showToast(`Error: ${e.message}`, "error");
    } finally { setCreatingWeb(false); }
  };

  // form state — create checkpoint
  const [ckName, setCkName] = useState("");
  const [ckCorpus, setCkCorpus] = useState("");
  const [ckEpochs, setCkEpochs] = useState<number>(100);
  const [ckBatch, setCkBatch] = useState<number>(64);
  const [ckLr, setCkLr] = useState<number>(0.002);
  const [creatingCk, setCreatingCk] = useState(false);
  const createCheckpoint = async () => {
    setCreatingCk(true);
    try {
      const payload: Checkpoint = { name: ckName || "", corpus: ckCorpus, epochs: ckEpochs, batch_size: ckBatch, learning_rate: ckLr };
      const res = await api.post("checkpoints", payload);
      await refreshCheckpoints();
      showToast(`Checkpoint created: ${res?.name || "ok"}`, "success");
    } catch (e: any) {
      showToast(`Error: ${e.message}`, "error");
    } finally { setCreatingCk(false); }
  };

  // form state — run MIA
  const [miaCorpus, setMiaCorpus] = useState("");
  const [miaCheckpoint, setMiaCheckpoint] = useState("");
  const [miaBatch, setMiaBatch] = useState<number>(64);
  const [miaInput, setMiaInput] = useState("");
  const [runningMia, setRunningMia] = useState(false);
  const [miaResult, setMiaResult] = useState<any>(null);
  const [miaError, setMiaError] = useState<string | null>(null);

  const runMia = async () => {
    setRunningMia(true);
    setMiaResult(null); setMiaError(null);
    try {
      // Join one-sentence-per-line input into pipe-separated string for backend
      const processedInput = miaInput
        ? miaInput.split(/\r?\n/)
            .map((s) => s.trim())
            .filter(Boolean)
            .join("|")
        : undefined;

      const payload: MiaReq = { checkpoint: miaCheckpoint, corpus: miaCorpus, batch_size: miaBatch, input: processedInput };
      const res = await api.post("mia", payload);
      setMiaResult(res);
    } catch (e: any) {
      setMiaError(e.message || String(e));
    } finally { setRunningMia(false); }
  };

  const corporaNames = (corpora || []).map(c => c.name);
  const checkpointNames = (checkpoints || []).map(c => c.name);

  // View/copy corpus content modal state + helpers
  const [viewingContent, setViewingContent] = useState<string | null>(null);
  const [viewingName, setViewingName] = useState<string | null>(null);
  const openContentView = (name: string, content?: string | undefined) => {
    setViewingName(name);
    setViewingContent(content ?? "(no content)");
  };
  const closeContentView = () => { setViewingContent(null); setViewingName(null); };
  const copyViewingContent = async () => {
    if (!viewingContent) return;
    try {
      await navigator.clipboard.writeText(viewingContent);
      showToast("Copied to clipboard", "success");
    } catch {
      showToast("Copy failed", "error");
    }
  };

  // ===== Diagnostics ("test cases") =====
  const [diagLog, setDiagLog] = useState<string[]>([]);
  const pushLog = (s: string) => setDiagLog(l => [new Date().toLocaleTimeString()+" · "+s, ...l].slice(0,100));
  const [diagBusy, setDiagBusy] = useState(false);

  const diagGetCorpora = async ()=>{
    setDiagBusy(true);
    try { await api.get("corpora"); pushLog("GET /corpora ✔"); }
    catch(e:any){ pushLog("GET /corpora ✖  " + (e.message||e)); }
    finally{ setDiagBusy(false); }
  };

  const diagPostSynthetic = async ()=>{
    setDiagBusy(true);
    try {
      const name = `ui_smoke_${Date.now()}`;
      await api.post("corpora/synthetic", { name, n: 1 } as SyntheticCorpusReq);
      pushLog("POST /corpora/synthetic (n=1) ✔");
    } catch(e:any){ pushLog("POST /corpora/synthetic ✖  " + (e.message||e)); }
    finally{ setDiagBusy(false); }
  };

  const diagPostMia = async ()=>{
    setDiagBusy(true);
    try {
      if (!miaCorpus || !miaCheckpoint) throw new Error("Select Corpus and Checkpoint first");
      await api.post("mia", { checkpoint: miaCheckpoint, corpus: miaCorpus, batch_size: 8, input: "Alice writes essays in watercolor at dawn." } as MiaReq);
      pushLog("POST /mia ✔");
    } catch(e:any){ pushLog("POST /mia ✖  " + (e.message||e)); }
    finally{ setDiagBusy(false); }
  };

  // short-lived toast (bottom-center)
  const [toast, setToast] = useState<{ message: string; kind?: "success" | "error" } | null>(null);
  const showToast = (message: string, kind: "success" | "error" = "success") => setToast({ message, kind });
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  return (
    <div className="mx-auto max-w-6xl p-4 space-y-6">
      {/* Toast (bottom-center) */}
      {toast && (
        <div className="fixed left-1/2 bottom-6 z-50 -translate-x-1/2">
          <div className={
            "px-4 py-2 rounded shadow-lg text-sm text-white " +
            (toast.kind === "error" ? "bg-red-600" : "bg-green-600")
          }>
            {toast.message}
          </div>
        </div>
      )}

      <header className="flex items-center gap-3">
        <ShieldCheck className="w-6 h-6" />
        <h1 className="text-2xl font-semibold">WhisperTrace</h1>
        <div className="ml-auto flex items-center gap-2">
          <Label className="text-sm">API Base</Label>
          <Input className="w-[360px]" value={baseUrl} onChange={e=>setBaseUrl(e.target.value)} placeholder="http://localhost:5001 or http://localhost:5001/api" />
          <Button variant="outline" onClick={()=>{refreshCorpora(); refreshCheckpoints();}}>
            <RefreshCcw className="w-4 h-4 mr-2"/> Refresh
          </Button>
        </div>
      </header>

      <Tabs defaultValue="corpora" className="w-full">
        <TabsList>
          <TabsTrigger value="corpora"><Database className="w-4 h-4 mr-1"/>Corpora</TabsTrigger>
          <TabsTrigger value="checkpoints"><BrainCircuit className="w-4 h-4 mr-1"/>Checkpoints</TabsTrigger>
          <TabsTrigger value="mia"><Play className="w-4 h-4 mr-1"/>MIA</TabsTrigger>
          <TabsTrigger value="diagnostics"><Bug className="w-4 h-4 mr-1"/>Diagnostics</TabsTrigger>
        </TabsList>

        {/* CORPORA TAB */}
        <TabsContent value="corpora" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><NotebookText className="w-4 h-4"/>Synthetic Corpus</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                 <Label>Name (optional)</Label>
                 <Input value={synName} onChange={e=>setSynName(e.target.value)} placeholder="e.g., synthetic"/>
                 <Label>Number of sentences</Label>
                 <Input type="number" value={synN} onChange={e=>setSynN(parseInt(e.target.value||"0"))} min={1} max={10000}/>
                <div className="flex justify-end">
                  <Button onClick={createSynthetic} disabled={creatingSyn}>
                    {creatingSyn && <Loader2 className="w-4 h-4 mr-2 animate-spin"/>}Create
                  </Button>
                </div>
               </CardContent>
             </Card>
 
             <Card className="shadow-sm">
               <CardHeader>
                 <CardTitle className="flex items-center gap-2"><Globe className="w-4 h-4"/>Web‑scraped Corpus</CardTitle>
               </CardHeader>
               <CardContent className="space-y-3">
                 <Label>Name (optional)</Label>
                 <Input value={webName} onChange={e=>setWebName(e.target.value)} placeholder="e.g., wiki_llg_equation"/>
                 <Label>URL</Label>
                 <Input value={webUrl} onChange={e=>setWebUrl(e.target.value)} placeholder="https://en.wikipedia.org/wiki/..."/>
                <div className="flex justify-end">
                  <Button onClick={createWeb} disabled={creatingWeb}>
                    {creatingWeb && <Loader2 className="w-4 h-4 mr-2 animate-spin"/>}Scrape & Create
                  </Button>
                </div>
               </CardContent>
             </Card>
           </div>

          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Available Corpora</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 mb-3 justify-between">
                <span className="text-sm text-muted-foreground">{loadingCorpora ? "Loading…" : `${corpora?.length ?? 0} corpora`}</span>
                <Button variant="outline" size="sm" onClick={refreshCorpora}><RefreshCcw className="w-4 h-4 mr-1"/>Refresh</Button>
              </div>
              {corporaError && (
                <Alert className="mb-3 border-red-300 bg-red-50">
                  <AlertTitle className="flex items-center gap-2"><WifiOff className="w-4 h-4"/> Failed to load corpora</AlertTitle>
                  <AlertDescription className="text-sm whitespace-pre-wrap">{corporaError}</AlertDescription>
                </Alert>
              )}
              {corpora && corpora.length > 0 ? (
                <div className="overflow-x-auto">
                  {(() => {
                    // Compute a deterministic column order:
                    // - Prefer this canonical order first
                    // - Then append any other keys found in the corpora (preserve encounter order)
                    const preferredOrder = ["name", "n", "url", "content"];
                    const allKeys = Array.from(new Set(corpora.flatMap((c) => Object.keys(c || {}))));
                    const cols = [
                      ...preferredOrder.filter((k) => allKeys.includes(k)),
                      ...allKeys.filter((k) => !preferredOrder.includes(k)),
                    ];
                     return (
                       <table className="min-w-full divide-y divide-muted">
                        <thead className="bg-muted">
                           <tr className="shadow-sm">
                             {cols.map((k) => {
                               const label = k === "content"
                                 ? "Preview"
                                 : k.replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase());
                               return (
                                 <th key={k} className="px-4 py-2 text-left text-sm font-medium">
                                   {label}
                                 </th>
                               );
                             })}
                          </tr>
                        </thead>
                        <tbody className="bg-background divide-y divide-muted">
                           {corpora.map((c, idx) => (
                             <tr key={idx} className="hover:bg-muted transition-colors">
                              {cols.map((k) => {
                                const v = (c as any)[k];

                                // CONTENT: remove very first line, then show truncated preview
                                if (k === "content") {
                                  const raw = v ? String(v) : "";
                                  const stripped = raw.replace(/^[^\n]*\n?/, ""); // remove first line and optional newline
                                  const preview = stripped.slice(0, 240);
                                  return (
                                    <td key={k} className="px-4 py-3 align-top">
                                      {raw ? (
                                        <div className="text-sm text-muted-foreground whitespace-pre-wrap max-h-36 overflow-auto">
                                          {preview}
                                          {stripped.length > 240 ? "…" : ""}
                                        </div>
                                      ) : <span className="text-sm text-muted-foreground">(no content)</span>}
                                    </td>
                                  );
                                }

                                // NAME: remove everything after the last "_"
                                if (k === "name") {
                                  const raw = v === null || v === undefined ? "" : String(v);
                                  const idx = raw.lastIndexOf("_");
                                  const display = idx >= 0 ? raw.slice(0, idx) : raw;
                                  const content = (c as any).content;
                                  const hasContent = Boolean(content);
                                  return (
                                    <td key={k} className="px-4 py-3 align-top">
                                      {hasContent ? (
                                        <button
                                          type="button"
                                          onClick={() => openContentView(raw, content)}
                                          className="text-sm font-medium text-left text-blue-600 underline hover:text-blue-700"
                                        >
                                          {display || <span className="text-muted-foreground">—</span>}
                                        </button>
                                      ) : (
                                        <div className="text-sm font-medium">{display || <span className="text-muted-foreground">—</span>}</div>
                                      )}
                                    </td>
                                  );
                                }

                                // Render URLs as clickable links for better UX
                                if (k === "url" && v) {
                                  return (
                                    <td key={k} className="px-4 py-3 align-top">
                                      <a
                                        href={String(v)}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-sm break-words min-w-[120px] max-w-[200px] inline-block text-blue-600 underline"
                                      >
                                        {String(v)}
                                      </a>
                                    </td>
                                  );
                                }

                                // Fallback: generic cell
                                return (
                                  <td key={k} className="px-4 py-3 align-top">
                                    <div className="text-sm whitespace-pre-wrap break-all min-w-[120px] max-w-[200px] overflow-auto">
                                      {v === null || v === undefined ? <span className="text-muted-foreground">—</span> : String(v)}
                                    </div>
                                  </td>
                                );
                              })}
                            </tr>
                         ))}

                        </tbody>
                      </table>
                    );
                  })()}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No corpora yet.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* CHECKPOINTS TAB */}
        <TabsContent value="checkpoints" className="space-y-4">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Create Checkpoint</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Row 1: Name + Corpus (span full width) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <Label>Name (Optional)</Label>
                  <Input value={ckName} onChange={e=>setCkName(e.target.value)} placeholder="e.g., my_checkpoint"/>
                </div>
                <div>
                  <Label>Corpus</Label>
                  <Select onValueChange={setCkCorpus} value={ckCorpus}>
                    <SelectTrigger><SelectValue placeholder="Select corpus" /></SelectTrigger>
                    <SelectContent>
                      {corporaNames.map(n => <SelectItem key={n} value={n}>{n}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Row 2: Epochs / Batch / LR (span full width) */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <Label>Epochs</Label>
                  <Input type="number" value={ckEpochs} onChange={e=>setCkEpochs(parseInt(e.target.value||"0"))}/>
                </div>
                <div>
                  <Label>Batch</Label>
                  <Input type="number" value={ckBatch} onChange={e=>setCkBatch(parseInt(e.target.value||"0"))}/>
                </div>
                <div>
                  <Label>LR</Label>
                  <Input type="number" step="0.0001" value={ckLr} onChange={e=>setCkLr(parseFloat(e.target.value||"0"))}/>
                </div>
              </div>

              {/* Row 3: Create button on its own row, right-aligned and narrower */}
              <div className="flex justify-end">
                <Button onClick={createCheckpoint} disabled={creatingCk} className="w-28">
                  {creatingCk && <Loader2 className="w-4 h-4 mr-2 animate-spin"/>}Create
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Available Checkpoints</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 mb-3 justify-between">
                <span className="text-sm text-muted-foreground">{loadingCheckpoints ? "Loading…" : `${checkpoints?.length ?? 0} checkpoints`}</span>
                <Button variant="outline" size="sm" onClick={refreshCheckpoints}><RefreshCcw className="w-4 h-4 mr-1"/>Refresh</Button>
              </div>
              {checkpointsError && (
                <Alert className="mb-3 border-red-300 bg-red-50">
                  <AlertTitle className="flex items-center gap-2"><WifiOff className="w-4 h-4"/> Failed to load checkpoints</AlertTitle>
                  <AlertDescription className="text-sm whitespace-pre-wrap">{checkpointsError}</AlertDescription>
                </Alert>
              )}
 
               {checkpoints && checkpoints.length > 0 ? (
                 <div className="overflow-x-auto">
                   {(() => {
                     const preferredOrder = ["name", "corpus", "epochs", "batch_size", "learning_rate"];
                     const allKeys = Array.from(new Set(checkpoints.flatMap((c) => Object.keys(c || {}))));
                     const cols = [
                       ...preferredOrder.filter((k) => allKeys.includes(k)),
                       ...allKeys.filter((k) => !preferredOrder.includes(k)),
                     ];
 
                     return (
                       <table className="min-w-full divide-y divide-muted">
                        <thead className="bg-muted">
                           <tr className="shadow-sm">
                             {cols.map((k) => (
                               <th key={k} className="px-4 py-2 text-left text-sm font-medium">
                                 {k.replace(/_/g, " ").replace(/\b\w/g, (ch) => ch.toUpperCase())}
                               </th>
                             ))}
                           </tr>
                         </thead>
                         <tbody className="bg-background divide-y divide-muted">
                           {checkpoints.map((ck, i) => (
                             <tr key={i} className="hover:bg-muted transition-colors">
                               {cols.map((k) => {
                                 const v = (ck as any)[k];
 
                                 if (k === "name") {
                                   const raw = v === null || v === undefined ? "" : String(v);
                                   const display = raw.split("__")[0] || "—";
                                   return (
                                     <td key={k} className="px-4 py-3 align-top">
                                       <div className="text-sm font-medium">{display}</div>
                                     </td>
                                   );
                                 }
 
                                 // numeric-ish fields: epochs, batch_size, learning_rate
                                 if (k === "learning_rate" && v !== null && v !== undefined) {
                                   return (
                                     <td key={k} className="px-4 py-3 align-top">
                                       <div className="text-sm">{Number(v).toPrecision ? Number(v).toString() : String(v)}</div>
                                     </td>
                                   );
                                 }
 
                                 return (
                                   <td key={k} className="px-4 py-3 align-top">
                                     <div className="text-sm whitespace-pre-wrap break-all min-w-[120px] max-w-[200px] overflow-auto">
                                       {v === null || v === undefined ? <span className="text-muted-foreground">—</span> : String(v)}
                                     </div>
                                   </td>
                                 );
                               })}
                             </tr>
                           ))}
                         </tbody>
                       </table>
                     );
                   })()}
                 </div>
               ) : (
                 <p className="text-sm text-muted-foreground">No checkpoints yet.</p>
               )}
             </CardContent>
          </Card>
        </TabsContent>

        {/* MIA TAB */}
        <TabsContent value="mia" className="space-y-4">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle>Run Membership Inference Attack</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <div className="md:col-span-2">
                <Label>Checkpoint</Label>
                <Select onValueChange={setMiaCheckpoint} value={miaCheckpoint}>
                  <SelectTrigger><SelectValue placeholder="Select checkpoint" /></SelectTrigger>
                  <SelectContent>
                    {checkpointNames.map(n => <SelectItem key={n} value={n}>{n}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Corpus</Label>
                <Select onValueChange={setMiaCorpus} value={miaCorpus}>
                  <SelectTrigger><SelectValue placeholder="Select corpus" /></SelectTrigger>
                  <SelectContent>
                    {corporaNames.map(n => <SelectItem key={n} value={n}>{n}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Batch size</Label>
                <Input type="number" value={miaBatch} onChange={e=>setMiaBatch(parseInt(e.target.value||"0"))}/>
              </div>
              <div className="md:col-span-4">
                <Label>Input text (optional—evaluate custom sentences, one per line)</Label>
                <Textarea rows={4} value={miaInput} onChange={e=>setMiaInput(e.target.value)} placeholder={'e.g.\nAlice writes essays in watercolor at dawn.\nNikola builds AI pipelines on GCP with privacy-first design.'} />
              </div>
              <div className="md:col-span-4 flex justify-end">
                <Button onClick={runMia} disabled={runningMia || !miaCorpus || !miaCheckpoint}>
                  {runningMia ? <Loader2 className="w-4 h-4 mr-2 animate-spin"/> : <Play className="w-4 h-4 mr-2"/>}
                  Run MIA
                </Button>
              </div>
              {miaError && (
                <div className="md:col-span-4">
                  <Alert className="border-red-300 bg-red-50">
                    <AlertTitle className="flex items-center gap-2"><WifiOff className="w-4 h-4"/> Request failed</AlertTitle>
                    <AlertDescription className="text-sm whitespace-pre-wrap">{miaError}</AlertDescription>
                  </Alert>
                </div>
              )}
            </CardContent>
          </Card>

          {miaResult && (
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle>Results</CardTitle>
              </CardHeader>
              <CardContent className="space-y-12">
                {/* Metadata (full-width) */}
                <div className="grid grid-cols-1 md:grid-cols-7 gap-3 items-start">
                  <div className="md:col-span-3">
                    <div className="text-xs text-muted-foreground">Checkpoint</div>
                    <div className="text-sm font-medium break-all">{miaResult.checkpoint}</div>
                  </div>
                  <div className="md:col-span-1">
                    <div className="text-xs text-muted-foreground">Corpus</div>
                    <div className="text-sm font-medium break-all">{miaResult.corpus}</div>
                  </div>
                  <div className="md:col-span-1">
                    <div className="text-xs text-muted-foreground">Batch size</div>
                    <div className="text-sm font-medium">{miaResult.batch_size ?? "—"}</div>
                  </div>
                  <div className="md:col-span-1">
                    <div className="text-xs text-muted-foreground">AUC</div>
                    <div className="text-sm font-medium">{typeof miaResult.auc === "number" ? miaResult.auc.toFixed(4) : "—"}</div>
                  </div>
                  <div className="md:col-span-1">
                    <div className="text-xs text-muted-foreground">Timestamp</div>
                    <div className="text-sm font-medium">{miaResult.timestamp || "—"}</div>
                  </div>
                </div>

                {/* Sentences table */}
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-muted">
                    <thead className="bg-muted">
                      <tr className="shadow-sm">
                        <th className="px-4 py-2 text-left text-sm font-medium">Content</th>
                        <th className="px-4 py-2 text-left text-sm font-medium">Score</th>
                        <th className="px-4 py-2 text-left text-sm font-medium">Normalized score [%]</th>
                        <th className="px-4 py-2 text-left text-sm font-medium">Is member</th>
                      </tr>
                    </thead>
                    <tbody className="bg-background divide-y divide-muted">
                      {(miaResult.sentences || []).map((s: any, i: number) => {
                        const content = s?.content ? String(s.content) : "";
                        const truncated = content.length > 100 ? content.slice(0, 100) + "…" : content;
                        const score = s?.score == null ? "—" : (Number(s.score).toFixed(3));
                        const normRaw = Number(s?.normalized_score || 0);
                        const normPct = Math.round(normRaw * 1000) / 10; // one decimal
                        const isHigh = normPct > 70.0;
                        const isMember = s?.is_member === true || String(s?.is_member).toLowerCase() === "true";

                        return (
                          <tr key={i} className="hover:bg-muted transition-colors">
                            <td className="px-4 py-3 align-top">
                              <div className="text-sm text-muted-foreground whitespace-pre-wrap break-all max-w-[48rem]">{truncated}</div>
                            </td>
                            <td className="px-4 py-3 align-top">
                              <div className="text-sm">{score}</div>
                            </td>
                            <td className="px-4 py-3 align-top">
                              <div className={"text-sm " + (isHigh ? "text-red-600 font-semibold" : "")}>
                                {isNaN(normPct) ? "—" : `${normPct.toFixed(1)}`}
                              </div>
                            </td>
                            <td className="px-4 py-3 align-top">
                              <div className={"inline-block px-2 py-0.5 text-sm rounded " + (isMember ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-700")}>
                                {isMember ? "True" : "False"}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
           )}
        </TabsContent>

        {/* DIAGNOSTICS TAB (acts like minimal test cases) */}
        <TabsContent value="diagnostics" className="space-y-4">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Bug className="w-4 h-4"/> Connectivity & CORS Diagnostics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">Use these to smoke-test API. POST tests will create tiny artifacts (n=1 synthetic corpus).</p>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" onClick={diagGetCorpora} disabled={diagBusy}><RefreshCcw className="w-4 h-4 mr-1"/>GET /corpora</Button>
                <Button variant="outline" onClick={diagPostSynthetic} disabled={diagBusy}><Plus className="w-4 h-4 mr-1"/>POST /corpora/synthetic</Button>
                <Button variant="outline" onClick={diagPostMia} disabled={diagBusy || !miaCorpus || !miaCheckpoint}><Play className="w-4 h-4 mr-1"/>POST /mia</Button>
              </div>
              <div className="text-xs text-muted-foreground">Tip: If these fail with <span className="font-mono">Failed to fetch</span>, confirm the Flask server is running and CORS is enabled.</div>
              <div className="border rounded-md p-3 bg-muted/50 max-h-60 overflow-auto">
                {diagLog.length ? diagLog.map((l, i)=>(<div key={i} className="font-mono text-xs">{l}</div>)) : <div className="text-sm text-muted-foreground">No logs yet.</div>}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <CrossOriginBanner baseUrl={baseUrl} />
 
      <footer className="text-xs text-muted-foreground py-4">WhisperTrace • Simple console for corpora, checkpoints, and membership inference</footer>

      {/* View Content Modal (for corpus content) */}
       {viewingContent !== null && (
         <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm" style={{ marginTop: 0 }}>
           <div className="bg-white dark:bg-slate-900 rounded-lg shadow-2xl w-full max-w-7xl max-h-[92vh] overflow-auto border border-slate-200">
             <div className="flex items-start justify-between p-4 border-b bg-white dark:bg-slate-900">
               <div className="pr-4">
                 <h3 className="text-lg font-semibold break-all">{viewingName}</h3>
               </div>
               <div className="flex items-center gap-2">
                 <Button variant="outline" size="sm" onClick={copyViewingContent}>Copy</Button>
                 <Button variant="ghost" onClick={closeContentView} aria-label="Close">
                   <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                   </svg>
                 </Button>
               </div>
             </div>
             <div className="p-4">
               <div className="whitespace-pre-wrap break-words text-sm max-h-[85vh] overflow-auto">
                 {viewingContent}
               </div>
             </div>
           </div>
         </div>
       )}
    </div>
  );
}
