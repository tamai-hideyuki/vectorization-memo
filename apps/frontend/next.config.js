/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
        return [
            {

                source: '/api/:path*',

                destination: 'http://vectorization-backend:8000/api/:path*'
            },
        ]
    },
}

module.exports = nextConfig
