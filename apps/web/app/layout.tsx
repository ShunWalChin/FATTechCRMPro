import type {Metadata} from 'next';
// Neutral on purpose: the public site brings its own fonts and stylesheets, and the workspace brings
// its own. A root that imported either would push one design onto the other.
export const metadata:Metadata={metadataBase:new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://fattech.com.br'),title:{default:'FAT Tech',template:'%s'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="pt-BR"><body>{children}</body></html>}
