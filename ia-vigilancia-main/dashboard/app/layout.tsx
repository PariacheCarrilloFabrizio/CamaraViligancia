import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IA Vigilancia Dashboard",
  description: "Panel de monitoreo para el prototipo de videovigilancia inteligente.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
