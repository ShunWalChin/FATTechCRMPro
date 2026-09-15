import '@fontsource-variable/inter';
import '../globals.css';
// Sign-in belongs to the workspace, not to the public site, so it loads the workspace design system.
export default function LoginLayout({children}:{children:React.ReactNode}){return <><link rel="preconnect" href="https://fonts.googleapis.com"/><link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous"/><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700;900&display=swap"/>{children}</>}
