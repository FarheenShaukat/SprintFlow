import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SprintFlow AI",
  description: "Intelligent project management for software teams"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
