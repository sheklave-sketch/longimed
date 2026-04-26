/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const backend = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return {
      beforeFiles: [
        {
          source: '/',
          has: [{ type: 'host', value: 'longimed.com' }],
          destination: '/landing',
        },
        {
          source: '/',
          has: [{ type: 'host', value: 'www.longimed.com' }],
          destination: '/landing',
        },
      ],
      afterFiles: [
        {
          source: '/api/:path*',
          destination: `${backend}/api/:path*`,
        },
        {
          source: '/uploads/:path*',
          destination: `${backend}/uploads/:path*`,
        },
      ],
      fallback: [],
    };
  },
};

module.exports = nextConfig;
