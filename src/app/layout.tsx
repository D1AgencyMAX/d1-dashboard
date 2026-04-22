import type { Metadata } from "next";
import "./globals.css";
import { ComedianNav } from "@/components/comedian/Navigation";

export const metadata: Metadata = {
  title: "Digital One Agency — Command Center",
  description: "AI Agency Operations Dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased min-h-screen bg-slate-950 text-slate-100">
        <ComedianNav />
        {children}
      </body>
    </html>
  );
}
