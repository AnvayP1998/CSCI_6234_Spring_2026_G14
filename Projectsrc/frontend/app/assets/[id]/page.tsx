"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { api, Asset, TaskResult, SearchResult } from "@/lib/api";

const STATUS_COLOR: Record<string, string> = {
  UPLOADED: "bg-slate-700 text-slate-300",
  IN_PROGRESS: "bg-yellow-900 text-yellow-300",
  PROCESSED: "bg-blue-900 text-blue-300",
  FAILED: "bg-red-900 text-red-300",
  INDEXED: "bg-green-900 text-green-300",
};

type Tab = "analyze" | "search";

export default function AssetDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [asset, setAsset] = useState<Asset | null>(null);
  const [tab, setTab] = useState<Tab>("analyze");

  // pipeline state
  const [processing, setProcessing] = useState(false);
  const [embedding, setEmbedding] = useState(false);
  const [pipelineMsg, setPipelineMsg] = useState<string | null>(null);
  const [pipelineError, setPipelineError] = useState<string | null>(null);

  // analyze state
  const [taskType, setTaskType] = useState("summarize");
  const [qaQuery, setQaQuery] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  // search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  const loadAsset = useCallback(async () => {
    try {
      const data = await api.listAssets();
      const found = data.find((a) => a.asset_id === id);
      if (found) setAsset(found);
    } catch {
      // ignore
    }
  }, [id]);

  useEffect(() => { loadAsset(); }, [loadAsset]);

  const runProcess = async () => {
    setProcessing(true); setPipelineError(null); setPipelineMsg(null);
    try {
      await api.processAsset(id);
      setPipelineMsg("Text extracted successfully.");
      await loadAsset();
    } catch (e: unknown) {
      setPipelineError(e instanceof Error ? e.message : "Processing failed");
    } finally {
      setProcessing(false);
    }
  };

  const runEmbed = async () => {
    setEmbedding(true); setPipelineError(null); setPipelineMsg(null);
    try {
      const res = await api.embedAsset(id) as { chunks_indexed: number };
      setPipelineMsg(`Indexed ${res.chunks_indexed} chunks into vector DB.`);
      await loadAsset();
    } catch (e: unknown) {
      setPipelineError(e instanceof Error ? e.message : "Embedding failed");
    } finally {
      setEmbedding(false);
    }
  };

  const runAnalyze = async () => {
    setAnalyzing(true); setAnalyzeError(null); setTaskResult(null);
    try {
      const res = await api.analyze(id, taskType, taskType === "qa" ? qaQuery : undefined);
      const result = await api.getTaskResult(res.request_id);
      setTaskResult(result);
    } catch (e: unknown) {
      setAnalyzeError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
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
    } finally {
      setSearching(false);
    }
  };

  if (!asset) {
    return <div className="text-slate-500 text-sm">Loading asset…</div>;
  }

  const canProcess = asset.processing_status === "UPLOADED" || asset.processing_status === "FAILED";
  const isIndexed = asset.chunks_indexed > 0;
  const canEmbed = asset.processing_status === "PROCESSED";
  const canAnalyze = !canProcess;

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <button
        onClick={() => router.push("/")}
        className="text-slate-400 hover:text-white text-sm flex items-center gap-1 transition-colors"
      >
        ← Back to files
      </button>

      <div className="bg-[#1a1d27] border border-[#2e3250] rounded-xl px-6 py-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-white">
              {asset.filename ?? asset.asset_id}
            </h1>
            <p className="text-slate-500 text-xs mt-1 font-mono">{asset.asset_id}</p>
            <p className="text-slate-400 text-sm mt-1 capitalize">{asset.modality}</p>
          </div>
          <span className={`text-xs font-medium px-3 py-1.5 rounded-full shrink-0 ${STATUS_COLOR[asset.processing_status] ?? "bg-slate-700 text-slate-300"}`}>
            {asset.processing_status}
          </span>
        </div>
      </div>

      {/* Pipeline actions */}
      <div className="bg-[#1a1d27] border border-[#2e3250] rounded-xl px-6 py-5 space-y-4">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Pipeline</h2>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={runProcess}
            disabled={processing || !canProcess}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-colors
              bg-blue-700 hover:bg-blue-600 text-white disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {processing ? "Extracting…" : "1 · Extract Text"}
          </button>
          <button
            onClick={runEmbed}
            disabled={embedding || !canEmbed}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors text-white
              disabled:opacity-40 disabled:cursor-not-allowed
              ${isIndexed ? "bg-green-700 hover:bg-green-600" : "bg-indigo-700 hover:bg-indigo-600"}`}
          >
            {embedding ? "Indexing…" : isIndexed ? `2 · Re-index (${asset.chunks_indexed} chunks)` : "2 · Embed & Index"}
          </button>
        </div>
        {isIndexed && (
          <p className="text-green-400 text-sm">Indexed {asset.chunks_indexed} chunks into vector DB.</p>
        )}
        {pipelineError && (
          <p className="text-red-400 text-sm">{pipelineError}</p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#2e3250] gap-1">
        {(["analyze", "search"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors border-b-2 -mb-px
              ${tab === t ? "border-indigo-500 text-white" : "border-transparent text-slate-400 hover:text-white"}`}
          >
            {t === "analyze" ? "AI Analysis" : "Semantic Search"}
          </button>
        ))}
      </div>

      {/* Analyze tab */}
      {tab === "analyze" && (
        <div className="space-y-4">
          <div className="flex gap-3 flex-wrap items-end">
            <div className="space-y-1">
              <label className="text-xs text-slate-400">Task</label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                className="bg-[#1a1d27] border border-[#2e3250] text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="summarize">Summarize</option>
                <option value="classify">Classify</option>
                <option value="qa">Question & Answer</option>
              </select>
            </div>
            {taskType === "qa" && (
              <div className="flex-1 space-y-1">
                <label className="text-xs text-slate-400">Your question</label>
                <input
                  value={qaQuery}
                  onChange={(e) => setQaQuery(e.target.value)}
                  placeholder="e.g. What is the main finding?"
                  className="w-full bg-[#1a1d27] border border-[#2e3250] text-white rounded-lg px-3 py-2 text-sm
                    focus:outline-none focus:border-indigo-500 placeholder-slate-600"
                />
              </div>
            )}
            <button
              onClick={runAnalyze}
              disabled={analyzing || !canAnalyze || (taskType === "qa" && !qaQuery.trim())}
              className="px-5 py-2 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-500
                text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {analyzing ? "Analyzing…" : "Run"}
            </button>
          </div>

          {!canAnalyze && (
            <p className="text-slate-500 text-sm">Run Extract Text first to enable analysis.</p>
          )}

          {analyzeError && (
            <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
              {analyzeError}
            </div>
          )}

          {taskResult && (
            <div className="space-y-4">
              {/* Answer card */}
              <div className="bg-[#1a1d27] border border-indigo-900 rounded-xl px-6 py-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-indigo-400 uppercase tracking-wider">
                    {taskResult.task_type}
                  </h3>
                  <span className="text-xs text-slate-500 font-mono">
                    confidence: {(taskResult.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="text-slate-200 text-sm leading-relaxed prose prose-sm prose-invert max-w-none">
                  <ReactMarkdown>{taskResult.answer}</ReactMarkdown>
                </div>
              </div>

              {/* Evidence */}
              {taskResult.evidence.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Source Evidence ({taskResult.evidence.length} chunks)
                  </h3>
                  <div className="grid gap-2">
                    {taskResult.evidence.map((ev) => (
                      <div
                        key={ev.evidence_id}
                        className="bg-[#1a1d27] border border-[#2e3250] rounded-lg px-4 py-3"
                      >
                        <span className="text-xs font-mono text-indigo-400">{ev.location}</span>
                        <p className="text-slate-400 text-xs mt-1 leading-relaxed line-clamp-3">
                          {ev.snippet}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Search tab */}
      {tab === "search" && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch()}
              placeholder="Search this document semantically…"
              className="flex-1 bg-[#1a1d27] border border-[#2e3250] text-white rounded-lg px-4 py-2.5 text-sm
                focus:outline-none focus:border-indigo-500 placeholder-slate-600"
            />
            <button
              onClick={runSearch}
              disabled={searching || !searchQuery.trim()}
              className="px-5 py-2 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-500
                text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {searching ? "Searching…" : "Search"}
            </button>
          </div>

          {searchError && (
            <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
              {searchError}
            </div>
          )}

          {searchResult && (
            <div className="space-y-2">
              <p className="text-xs text-slate-500">{searchResult.hits.length} results for &quot;{searchResult.query}&quot;</p>
              {searchResult.hits.length === 0 ? (
                <p className="text-slate-500 text-sm">No results found. Make sure the file is indexed first.</p>
              ) : (
                searchResult.hits.map((hit, i) => (
                  <div key={i} className="bg-[#1a1d27] border border-[#2e3250] rounded-xl px-5 py-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono text-indigo-400">chunk {hit.chunk_index}</span>
                      <span className="text-xs text-slate-500">score: {hit.score.toFixed(4)}</span>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed">{hit.text}</p>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
