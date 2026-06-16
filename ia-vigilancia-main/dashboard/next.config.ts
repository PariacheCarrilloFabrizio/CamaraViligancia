import type { NextConfig } from "next";

const nextConfig: NextConfig = {
    // Permitimos la IP de tu red virtual/local para que Next.js no bloquee el video
    allowedDevOrigins: ['192.168.56.1', 'localhost'],
};

export default nextConfig;