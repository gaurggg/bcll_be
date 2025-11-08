import type { Metadata } from "next";
import "./globals.css";
import ConditionalNavbar from "@/components/ConditionalNavbar";

export const metadata: Metadata = {
  title: "Bhopal Bus POC - AI-Powered Bus System",
  description: "Intelligent bus routing and scheduling for Bhopal, MP",
  icons: {
    icon: "/bcll logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased" suppressHydrationWarning>
        <ConditionalNavbar />
        {children}
      </body>
    </html>
  );
}
