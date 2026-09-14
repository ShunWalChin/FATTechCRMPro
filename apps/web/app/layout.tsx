import type {Metadata} from 'next';
// suppressHydrationWarning marks a boundary the site's own script owns: it swaps no-js for js-ready
// on <html> before React hydrates, and that difference is intended, not a bug to be reported.
// Neutral on purpose: the public site brings its own fonts and stylesheets, and the workspace brings
// its own. A root that imported either would push one design onto the other.
export const metadata:Metadata={metadataBase:new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://fattech.com.br'),title:{default:'FAT Tech',template:'%s'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="pt-BR" suppressHydrationWarning><body>{children}</body></html>}
