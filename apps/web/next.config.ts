import type { NextConfig } from 'next';
import path from 'node:path';
const nextConfig: NextConfig = {
  allowedDevOrigins: ['127.0.0.1'],
  output: 'standalone',
  outputFileTracingRoot: path.join(process.cwd(), '../..'),
  poweredByHeader: false,
  // O site institucional volta a ser o HTML puro do repositório oficial, servido de public/ byte a
  // byte. Ele sempre publicou endereços terminados em .html e agora os publica de novo, então os
  // redirecionamentos que apontavam para URLs limpas deixam de existir: eles só faziam sentido
  // enquanto o site era uma transcrição em React, e essa transcrição quebrava as animações que os
  // scripts do original fazem no DOM.
  async rewrites() {
    const api = process.env.API_INTERNAL_URL || 'http://127.0.0.1:8000';
    return {
      beforeFiles: [
        // A raiz é o único endereço que o original não publica como arquivo.
        { source: '/', destination: '/index.html' },
        { source: '/blog', destination: '/blog/index.html' },
        { source: '/lp/impulse-crm', destination: '/lp/impulse-crm/index.html' },
      ],
      afterFiles: [
        { source: '/api/v1/:path*', destination: `${api}/api/v1/:path*` },
        { source: '/api/public/:path*', destination: `${api}/api/public/:path*` },
      ],
      fallback: [],
    };
  },
  async headers() { return [{ source: '/:path*', headers: [{key:'X-Content-Type-Options',value:'nosniff'},{key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},{key:'X-Frame-Options',value:'DENY'},{key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'}] }]; }
};
export default nextConfig;
