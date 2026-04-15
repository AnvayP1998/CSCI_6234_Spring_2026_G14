import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DataInsight AI",
  description: "Multimodal AI document analysis platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="h-screen flex flex-col antialiased overflow-hidden">
        <nav className="shrink-0 border-b border-[#2e3250] bg-[#1a1d27] px-6 py-3 flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-xs">
            AI
          </div>
          <span className="text-base font-semibold text-white">DataInsight AI</span>
          <span className="ml-1 text-xs text-slate-500 font-mono">Multimodal Analysis Platform</span>
        </nav>
        <main className="flex-1 overflow-auto">{children}</main>
      </body>
    </html>
  );
}
