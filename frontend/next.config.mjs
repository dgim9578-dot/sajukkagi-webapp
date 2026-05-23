/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["three", "@react-three/fiber", "@react-three/drei"],
  async rewrites() {
    const api = process.env.SAJU_API_URL || "http://127.0.0.1:8000";
    return {
      afterFiles: [
        { source: "/api/briefing/generate", destination: `${api}/api/briefing/generate` },
        { source: "/api/briefing/generate/:path*", destination: `${api}/api/briefing/generate/:path*` },
        { source: "/api/briefing/sample", destination: `${api}/api/briefing/sample` },
        {
          source: "/api/briefing/get/:fingerprint",
          destination: `${api}/api/briefing/get/:fingerprint`,
        },
        {
          source: "/api/briefing/get/match/:fingerprint",
          destination: `${api}/api/briefing/get/match/:fingerprint`,
        },
      ],
    };
  },
};

export default nextConfig;
