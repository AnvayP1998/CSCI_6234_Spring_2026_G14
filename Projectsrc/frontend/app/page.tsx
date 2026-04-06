"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api, Asset } from "@/lib/api";

const MODALITY_ICON: Record<string, string> = {
  document: "📄",
  image: "🖼️",
  audio: "🎵",
  video: "🎬",
};

const STATUS_COLOR: Record<string, string> = {
  UPLOADED: "bg-slate-700 text-slate-300",
  IN_PROGRESS: "bg-yellow-900 text-yellow-300",
  PROCESSED: "bg-blue-900 text-blue-300",
  FAILED: "bg-red-900 text-red-300",
  INDEXED: "bg-green-900 text-green-300",
};

export default function Dashboard() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAssets = useCallback(async () => {
    try {
      const data = await api.listAssets();
      setAssets(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load assets");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAssets(); }, [loadAssets]);

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        await api.uploadAsset(file);
      }
      await loadAssets();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="text-center py-6">
        <h1 className="text-3xl font-bold text-white mb-2">DataInsight AI</h1>
        <p className="text-slate-400 text-sm">
          Upload documents, images, audio, or video — extract, search, and analyze with AI
        </p>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files); }}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer
          ${dragOver ? "border-indigo-500 bg-indigo-950/30" : "border-[#2e3250] bg-[#1a1d27] hover:border-indigo-600"}`}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          multiple
          accept=".pdf,.txt,.png,.jpg,.jpeg,.mp3,.mp4,.wav"
          className="hidden"
          onChange={(e) => handleUpload(e.target.files)}
        />
        <div className="text-4xl mb-3">{uploading ? "⏳" : "☁️"}</div>
        <p className="text-white font-medium">
          {uploading ? "Uploading..." : "Drop files here or click to upload"}
        </p>
        <p className="text-slate-500 text-xs mt-1">PDF, TXT, PNG, JPG, MP3, MP4, WAV</p>
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Assets list */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Your Files ({assets.length})
        </h2>

        {loading ? (
          <div className="text-slate-500 text-sm">Loading...</div>
        ) : assets.length === 0 ? (
          <div className="text-slate-500 text-sm text-center py-12">
            No files yet — upload something to get started.
          </div>
        ) : (
          <div className="grid gap-3">
            {assets.map((a) => (
              <Link
                key={a.asset_id}
                href={`/assets/${a.asset_id}`}
                className="flex items-center gap-4 bg-[#1a1d27] border border-[#2e3250] rounded-xl px-5 py-4
                  hover:border-indigo-600 hover:bg-[#1e2235] transition-all group"
              >
                <span className="text-2xl">{MODALITY_ICON[a.modality] ?? "📁"}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium truncate">
                    {a.filename ?? a.asset_id.slice(0, 16) + "…"}
                  </p>
                  <p className="text-slate-500 text-xs mt-0.5">
                    {a.modality} · {new Date(a.created_at).toLocaleString()}
                  </p>
                </div>
                <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_COLOR[a.processing_status] ?? "bg-slate-700 text-slate-300"}`}>
                  {a.processing_status}
                </span>
                <span className="text-slate-600 group-hover:text-indigo-400 transition-colors">→</span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
