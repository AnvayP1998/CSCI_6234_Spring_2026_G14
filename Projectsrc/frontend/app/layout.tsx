import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DataInsight AI",
  description: "Multimodal AI document analysis platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <nav className="border-b border-[#2e3250] bg-[#1a1d27] px-6 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
            AI
          </div>
          <span className="text-lg font-semibold text-white">DataInsight AI</span>
          <span className="ml-2 text-xs text-slate-500 font-mono">Multimodal Analysis Platform</span>
        </nav>
        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
