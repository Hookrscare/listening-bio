import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://listening.bio"),
  title: "Listening.bio | Biodiversity, heard",
  description: "Transparent, reviewable acoustic biodiversity monitoring for conservation partners.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
  openGraph: { title: "Listening.bio | Nature leaves a signal", description: "Turn environmental sound into transparent, reviewable biodiversity evidence.", type: "website", images: [{ url: "/og.png", width: 1200, height: 630, alt: "Listening.bio acoustic signal field" }] },
  twitter: { card: "summary_large_image", title: "Listening.bio | Nature leaves a signal", description: "Auditable acoustic biodiversity monitoring.", images: ["/og.png"] },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
