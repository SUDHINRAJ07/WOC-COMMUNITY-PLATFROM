import {modules,programs,extraPages} from '@/lib/data';
export default function sitemap(){const base=process.env.NEXT_PUBLIC_SITE_URL||'http://localhost:4317';return ['/',...modules.map(m=>`/${m.slug}/`),...programs.map(p=>`/${p.module}/${p.slug}/`),...extraPages.filter(x=>!['admin','dashboard','verify'].includes(x)).map(x=>`/${x}/`)].map(path=>({url:base+path,lastModified:new Date()}))}
export const dynamic='force-static';
