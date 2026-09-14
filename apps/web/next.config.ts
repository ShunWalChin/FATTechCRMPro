import type { NextConfig } from 'next';
import path from 'node:path';
import transcribed from './app/(site)/redirects.json';
const nextConfig: NextConfig = {
  allowedDevOrigins: ['127.0.0.1'],
  output: 'standalone',
  outputFileTracingRoot: path.join(process.cwd(), '../..'),
  poweredByHeader: false,
  // The original site was served as .html files and those URLs may be linked or indexed, so every one
  // of them still resolves. /crm.html keeps its own URL: /crm is the private workspace.
  async redirects() {
    return [
      {source:'/index.html',destination:'/',permanent:true},
      {source:'/blog/index.html',destination:'/blog',permanent:true},
      {source:'/blog/artigos/:slug.html',destination:'/blog/artigos/:slug',permanent:true},
      {source:'/lp/:slug.html',destination:'/lp/:slug',permanent:true},
      {source:'/lp/impulse-crm/index.html',destination:'/lp/impulse-crm',permanent:true},
      {source:'/privacidade.html',destination:'/privacidade',permanent:true},
      {source:'/integracoes.html',destination:'/integracoes',permanent:true},
      ...transcribed,
    ];
  },
  async rewrites() { return [{ source: '/api/v1/:path*', destination: `${process.env.API_INTERNAL_URL || 'http://127.0.0.1:8000'}/api/v1/:path*` }]; },
  async headers() { return [{ source: '/:path*', headers: [{key:'X-Content-Type-Options',value:'nosniff'},{key:'Referrer-Policy',value:'strict-origin-when-cross-origin'},{key:'X-Frame-Options',value:'DENY'},{key:'Permissions-Policy',value:'camera=(), microphone=(), geolocation=()'}] }]; }
};
export default nextConfig;
