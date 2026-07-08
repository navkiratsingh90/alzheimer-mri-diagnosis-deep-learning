import type { NextConfig } from "next";

/** @type {import('next').NextConfig} */
const nextConfig : NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/static/uploads/**',
      },
    ],
  },
};
module.exports = nextConfig;

export default nextConfig;
