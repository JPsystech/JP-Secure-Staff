/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // for Docker: copy .next/standalone + .next/static
}

module.exports = nextConfig

