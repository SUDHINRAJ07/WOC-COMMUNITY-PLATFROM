import type {Metadata} from 'next';
import './globals.css';
import './visual-update.css';
import './auth-update.css';
import Platform from '@/components/Platform';
export const metadata:Metadata={title:{default:'THE WOC — Wind of Change',template:'%s | THE WOC'},description:'Learn practical skills, build your community and explore student-to-industry opportunities with Wind of Change.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><Platform>{children}</Platform></body></html>}
