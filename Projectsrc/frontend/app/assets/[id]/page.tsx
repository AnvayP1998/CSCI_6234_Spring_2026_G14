"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { api, Asset, SearchResult, Evidence } from "@/lib/api";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const STATUS_COLOR: Record<string, string> = {
  UPLOADED: "bg-slate-700 text-slate-300",
  IN_PROGRESS: "bg-yellow-900 text-yellow-300",
  PROCESSED: "bg-blue-900 text-blue-300",
  FAILED: "bg-red-900 text-red-300",
  INDEXED: "bg-green-900 text-green-300",
};

const SUGGESTED_PROMPTS: Record<string, { label: string; query: string; taskType: string }[]> = {
  document: [
    { label: "Summarize this document", query: "", taskType: "summarize" },
    { label: "What are the key points?", query: "What are the key points?", taskType: "qa" },
    { label: "What is this about?", query: "What is this document about?", taskType: "qa" },
    { label: "Classify document type", query: "", taskType: "classify" },
  ],
  image: [
    { label: "Describe the image", query: "Describe what you see in this image", taskType: "qa" },
    { label: "Extract text from image", query: "What text appears in this image?", taskType: "qa" },
    { label: "What is the main subject?", query: "What is the main subject of this image?", taskType: "qa" },
    { label: "Classify image", query: "", taskType: "classify" },
  ],
  audio: [
    { label: "Summarize transcript", query: "", taskType: "summarize" },
    { label: "Key topics discussed", query: "What are the key topics discussed?", taskType: "qa" },
    { label: "Who is speaking?", query: "Who is speaking in this audio?", taskType: "qa" },
    { label: "Classify content", query: "", taskType: "classify" },
  ],
  video: [
    { label: "Summarize content", query: "", taskType: "summarize" },
    { label: "Key points", query: "What are the key points in this video?", taskType: "qa" },
    { label: "What topics are covered?", query: "What topics are covered?", taskType: "qa" },
    { label: "Classify content", query: "", taskType: "classify" },
  ],
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  taskType?: string;
  confidence?: number;
  evidence?: Evidence[];
  loading?: boolean;
};

type Tab = "chat" | "search";

function FileViewer({ asset }: { asset: Asset }) {
  const [error, setError] = useState(false);
  const fileUrl = `${BASE}/api/assets/${asset.asset_id}/file`;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 text-center p-8">
        <div className="text-5xl opacity-30">
          {asset.modality === "document" ? "📄" : asset.modality === "image" ? "🖼️" : asset.modality === "audio" ? "🎵" : "🎬"}
        </div>
        <p className="text-slate-500 text-sm font-medium">{asset.filename}</p>
        <p className="text-slate-600 text-xs">Preview unavailable — restart the backend to enable file serving</p>
      </div>
    );
  }

  if (asset.modality === "document") {
    return <iframe src={fileUrl} className="w-full h-full border-0" title={asset.filename ?? "Document"} onError={() => setError(true)} />;
  }

  if (asset.modality === "image") {
    return (
      <img
        src={fileUrl}
        alt={asset.filename ?? "Image"}
        className="max-w-full max-h-full object-contain p-6"
        onError={() => setError(true)}
      />
    );
  }

  if (asset.modality === "audio") {
    return (
      <div className="flex flex-col items-center gap-5 p-8 text-center">
        <div className="w-20 h-20 rounded-2xl bg-indigo-900/40 border border-indigo-800 flex items-center justify-center text-4xl">
          🎵
        </div>
        <div>
          <p className="text-white font-medium text-sm">{asset.filename}</p>
          <p className="text-slate-500 text-xs mt-0.5">Audio file</p>
        </div>
        <audio controls src={fileUrl} className="w-72" onError={() => setError(true)} />
      </div>
    );
  }

  if (asset.modality === "video") {
    return (
      <video
        controls
        src={fileUrl}
        className="max-w-full max-h-full rounded-lg"
        onError={() => setError(true)}
      />
    );
  }

  return null;
}

export default function AssetDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [asset, setAsset] = useState<Asset | null>(null);
  const [tab, setTab] = useState<Tab>("chat");

  // pipeline
  const [processing, setProcessing] = useState(false);
  const [embedding, setEmbedding] = useState(false);
  const [pipelineError, setPipelineError] = useState<string | null>(null);

  // extracted text preview
  const [textPreview, setTextPreview] = useState<string | null>(null);
  const [textLength, setTextLength] = useState<number>(0);
  const [showText, setShowText] = useState(false);
  const [textLoading, setTextLoading] = useState(false);

  // chat
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [taskType, setTaskType] = useState("qa");
  const chatEndRef = useRef<HTMLDivElement>(null);

  // search
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const loadAsset = useCallback(async () => {
    try {
      const data = await api.listAssets();
      const found = data?.find((a) => a.asset_id === id);
      if (found) setAsset(found);
    } catch { /* ignore */ }
  }, [id]);

  useEffect(() => { loadAsset(); }, [loadAsset]);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const runProcess = async () => {
    setProcessing(true); setPipelineError(null);
    try {
      await api.processAsset(id);
      setTextPreview(null);
      await loadAsset();
    } catch (e: unknown) {
      setPipelineError(e instanceof Error ? e.message : "Processing failed");
    } finally { setProcessing(false); }
  };

  const runEmbed = async () => {
    setEmbedding(true); setPipelineError(null);
    try {
      await api.embedAsset(id);
      await loadAsset();
    } catch (e: unknown) {
      setPipelineError(e instanceof Error ? e.message : "Embedding failed");
    } finally { setEmbedding(false); }
  };

  const toggleTextPreview = async () => {
    if (showText) { setShowText(false); return; }
    if (textPreview !== null) { setShowText(true); return; }
    setTextLoading(true);
    try {
      const res = await api.getAssetText(id);
      if (res) { setTextPreview(res.content); setTextLength(res.text_length); }
      setShowText(true);
    } catch {
      setTextPreview("[No extracted text yet — run Extract Text first.]");
      setShowText(true);
    } finally { setTextLoading(false); }
  };

  const sendMessage = async (query: string, type: string) => {
    if (type === "qa" && !query.trim()) return;

    const displayContent =
      type === "summarize" ? "Summarize this document" :
      type === "classify"  ? "Classify this document" :
      query;

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: displayContent, taskType: type };
    const loadingMsg: ChatMessage = { id: crypto.randomUUID(), role: "assistant", content: "", loading: true };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setInput("");

    try {
      const res = await api.analyze(id, type, type === "qa" ? query : undefined);
      const result = await api.getTaskResult(res!.request_id);
      setMessages((prev) => prev.map((m) =>
        m.id === loadingMsg.id
          ? { ...m, loading: false, content: result!.answer, confidence: result!.confidence, evidence: result!.evidence }
          : m
      ));
    } catch (e: unknown) {
      setMessages((prev) => prev.map((m) =>
        m.id === loadingMsg.id
          ? { ...m, loading: false, content: e instanceof Error ? e.message : "Analysis failed" }
          : m
      ));
    }
  };

  const runSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true); setSearchError(null); setSearchResult(null);
    try {
      const res = await api.search(searchQuery, id);
      setSearchResult(res);
    } catch (e: unknown) {
      setSearchError(e instanceof Error ? e.message : "Search failed");
    } finally { setSearching(false); }
  };

  if (!asset) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-slate-600 text-sm">Loading…</div>
      </div>
    );
  }

  const canProcess = asset.processing_status === "UPLOADED" || asset.processing_status === "FAILED";
  const isIndexed = asset.chunks_indexed > 0;
  const canEmbed = asset.processing_status === "PROCESSED";
  const canAnalyze = !canProcess;
  const suggestions = SUGGESTED_PROMPTS[asset.modality] ?? SUGGESTED_PROMPTS.document;

  return (
    <div className="h-full flex flex-col">

      {/* ── Top bar ── */}
      <div className="shrink-0 flex items-center gap-3 px-5 py-2.5 bg-[#1a1d27] border-b border-[#2e3250]">
        <button
          onClick={() => router.push("/")}
          className="text-slate-500 hover:text-white text-sm transition-colors shrink-0 flex items-center gap-1"
        >
          ← Back
        </button>
        <div className="w-px h-4 bg-[#2e3250]" />
        <div className="flex-1 min-w-0 flex items-center gap-2">
          <span className="text-slate-400 text-sm">
            {asset.modality === "document" ? "📄" : asset.modality === "image" ? "🖼️" : asset.modality === "audio" ? "🎵" : "🎬"}
          </span>
          <p className="text-white text-sm font-medium truncate">{asset.filename ?? asset.asset_id}</p>
        </div>
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full shrink-0 ${STATUS_COLOR[asset.processing_status] ?? "bg-slate-700 text-slate-300"}`}>
          {asset.processing_status}
        </span>
      </div>

      {/* ── Pipeline bar ── */}
      <div className="shrink-0 flex items-center gap-2.5 px-5 py-2 bg-[#13151f] border-b border-[#2e3250] flex-wrap">
        <button
          onClick={runProcess}
          disabled={processing || !canProcess}
          className="px-3 py-1.5 rounded-md text-xs font-medium bg-blue-700 hover:bg-blue-600 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {processing ? "Extracting…" : "1 · Extract Text"}
        </button>
        <button
          onClick={runEmbed}
          disabled={embedding || !canEmbed}
          className={`px-3 py-1.5 rounded-md text-xs font-medium text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors
            ${isIndexed ? "bg-green-700 hover:bg-green-600" : "bg-indigo-700 hover:bg-indigo-600"}`}
        >
          {embedding ? "Indexing…" : isIndexed ? `2 · Re-index (${asset.chunks_indexed} chunks)` : "2 · Embed & Index"}
        </button>
        <div className="flex-1" />
        {asset.processing_status === "PROCESSED" && !isIndexed && (
          <span className="text-blue-400 text-xs">Text extracted — ready to embed</span>
        )}
        {isIndexed && <span className="text-green-400 text-xs">✓ {asset.chunks_indexed} chunks indexed</span>}
        {pipelineError && <span className="text-red-400 text-xs">{pipelineError}</span>}
      </div>

      {/* ── Two-column body ── */}
      <div className="flex flex-1 min-h-0">

        {/* LEFT — file viewer */}
        <div className="flex-1 bg-[#0d0f18] border-r border-[#2e3250] overflow-hidden flex items-center justify-center">
          <FileViewer asset={asset} />
        </div>

        {/* RIGHT — AI panel */}
        <div className="w-[440px] shrink-0 flex flex-col" style={{ background: "#161822" }}>

          {/* Tabs */}
          <div className="shrink-0 flex border-b border-[#2e3250]">
            {(["chat", "search"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 py-2.5 text-xs font-semibold uppercase tracking-widest transition-colors
                  ${tab === t ? "text-white border-b-2 border-indigo-500" : "text-slate-500 hover:text-slate-300 border-b-2 border-transparent"}`}
              >
                {t === "chat" ? "AI Assistant" : "Search"}
              </button>
            ))}
          </div>

          {/* ── CHAT TAB ── */}
          {tab === "chat" && (
            <>
              {/* Extracted text toggle */}
              <div className="shrink-0 border-b border-[#2e3250]">
                <button
                  onClick={toggleTextPreview}
                  className="w-full flex items-center justify-between px-4 py-2 text-xs text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <span className="flex items-center gap-1.5">
                    <span>Extracted Text</span>
                    {textLength > 0 && <span className="text-slate-700">{textLength.toLocaleString()} chars</span>}
                  </span>
                  <span className="text-slate-700">{textLoading ? "…" : showText ? "▲" : "▼"}</span>
                </button>
                {showText && textPreview && (
                  <pre className="mx-3 mb-2.5 text-xs text-slate-400 whitespace-pre-wrap leading-relaxed max-h-32 overflow-y-auto font-mono bg-[#0d0f18] rounded-lg p-3 border border-[#2e3250]">
                    {textPreview}
                  </pre>
                )}
              </div>

              {/* Suggested prompts */}
              {messages.length === 0 && canAnalyze && (
                <div className="shrink-0 px-4 pt-4 pb-3 border-b border-[#2e3250]">
                  <p className="text-xs text-slate-500 font-medium mb-2.5">Prompt ideas</p>
                  <div className="grid grid-cols-2 gap-1.5">
                    {suggestions.map((s) => (
                      <button
                        key={s.label}
                        onClick={() => sendMessage(s.query, s.taskType)}
                        className="text-left text-xs bg-[#1a1d27] hover:bg-[#1e2235] border border-[#2e3250] hover:border-indigo-500/60
                          rounded-xl px-3 py-2.5 text-slate-400 hover:text-slate-200 transition-all leading-snug"
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Not yet processed */}
              {!canAnalyze && messages.length === 0 && (
                <div className="flex-1 flex flex-col items-center justify-center gap-3 px-8 text-center">
                  <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-2xl">🤖</div>
                  <p className="text-slate-500 text-sm">Run <span className="text-blue-400 font-medium">Extract Text</span> then <span className="text-indigo-400 font-medium">Embed & Index</span> to enable the AI assistant.</p>
                </div>
              )}

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    {msg.role === "user" ? (
                      <div className="max-w-[85%] bg-indigo-600 text-white rounded-2xl rounded-br-sm px-4 py-2.5 text-sm leading-relaxed">
                        {msg.content}
                      </div>
                    ) : (
                      <div className="max-w-[98%] space-y-1 w-full">
                        {msg.loading ? (
                          <div className="bg-[#1a1d27] border border-[#2e3250] rounded-2xl rounded-bl-sm px-4 py-3.5">
                            <div className="flex gap-1.5 items-center">
                              {[0, 150, 300].map((d) => (
                                <span key={d} className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />
                              ))}
                            </div>
                          </div>
                        ) : (
                          <>
                            <div className="bg-[#1a1d27] border border-[#2e3250] rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-slate-200 leading-relaxed prose prose-sm prose-invert max-w-none">
                              <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>
                            <div className="flex items-center gap-3 px-1 flex-wrap">
                              {msg.confidence !== undefined && (
                                <span className="text-xs text-slate-600">
                                  confidence: {(msg.confidence * 100).toFixed(1)}%
                                </span>
                              )}
                              {msg.evidence && msg.evidence.length > 0 && (
                                <details>
                                  <summary className="text-xs text-slate-600 cursor-pointer hover:text-indigo-400 transition-colors">
                                    {msg.evidence.length} source chunks ▸
                                  </summary>
                                  <div className="mt-2 space-y-1.5">
                                    {msg.evidence.map((ev) => (
                                      <div key={ev.evidence_id} className="bg-[#0d0f18] border border-[#2e3250] rounded-lg px-3 py-2">
                                        <span className="text-xs font-mono text-indigo-400">{ev.location}</span>
                                        <p className="text-slate-500 text-xs mt-0.5 leading-relaxed line-clamp-2">{ev.snippet}</p>
                                      </div>
                                    ))}
                                  </div>
                                </details>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              {canAnalyze && (
                <div className="shrink-0 border-t border-[#2e3250] p-3">
                  <div className="flex gap-2 items-center bg-[#1a1d27] border border-[#2e3250] rounded-xl px-3 py-2 focus-within:border-indigo-500/60 transition-colors">
                    <select
                      value={taskType}
                      onChange={(e) => setTaskType(e.target.value)}
                      className="bg-transparent text-slate-400 text-xs focus:outline-none shrink-0 cursor-pointer"
                    >
                      <option value="qa">Q&A</option>
                      <option value="summarize">Summarize</option>
                      <option value="classify">Classify</option>
                    </select>
                    <div className="w-px h-4 bg-[#2e3250]" />
                    <input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) sendMessage(input, taskType); }}
                      placeholder={taskType === "qa" ? "Ask anything about this file…" : `Click ↑ to ${taskType}`}
                      disabled={taskType !== "qa"}
                      className="flex-1 bg-transparent text-white text-sm focus:outline-none placeholder-slate-600 disabled:opacity-40"
                    />
                    <button
                      onClick={() => sendMessage(input, taskType)}
                      disabled={taskType === "qa" && !input.trim()}
                      className="w-7 h-7 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm
                        disabled:opacity-30 disabled:cursor-not-allowed transition-colors shrink-0 flex items-center justify-center"
                    >
                      ↑
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {/* ── SEARCH TAB ── */}
          {tab === "search" && (
            <div className="flex flex-col flex-1 min-h-0 p-4 gap-3">
              <div className="flex gap-2 shrink-0 bg-[#1a1d27] border border-[#2e3250] rounded-xl px-3 py-2 focus-within:border-indigo-500/60 transition-colors">
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && runSearch()}
                  placeholder="Search this file semantically…"
                  className="flex-1 bg-transparent text-white text-sm focus:outline-none placeholder-slate-600"
                />
                <button
                  onClick={runSearch}
                  disabled={searching || !searchQuery.trim()}
                  className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-40 transition-colors font-medium"
                >
                  {searching ? "…" : "Search"}
                </button>
              </div>
              {searchError && <p className="text-red-400 text-xs shrink-0">{searchError}</p>}
              <div className="overflow-y-auto space-y-2 min-h-0">
                {searchResult && searchResult.hits.length === 0 && (
                  <p className="text-slate-600 text-sm text-center py-8">No results found.</p>
                )}
                {searchResult?.hits.map((hit, i) => (
                  <div key={i} className="bg-[#1a1d27] border border-[#2e3250] rounded-xl px-4 py-3">
                    <div className="flex justify-between mb-1.5">
                      <span className="text-xs font-mono text-indigo-400">chunk {hit.chunk_index}</span>
                      <span className="text-xs text-slate-600">{hit.score.toFixed(4)}</span>
                    </div>
                    <p className="text-slate-300 text-xs leading-relaxed">{hit.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
