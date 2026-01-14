/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Required for Docker deployment
  typescript: {
    ignoreBuildErrors: true, // Skip type checking during build
  },
  eslint: {
    ignoreDuringBuilds: true, // Skip ESLint during build
  },
};

module.exports = nextConfig;
