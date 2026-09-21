import type { Metadata } from "next";
import { AuthProvider } from "@/context/AuthContext";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProofPath | Placement Cell Dashboard",
  description: "Enterprise candidate verification and deterministic placement matching portal",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <body className="min-h-full flex flex-col bg-[#0B0F17] text-slate-100 selection:bg-indigo-500/30 selection:text-white">
        <AuthProvider>
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
