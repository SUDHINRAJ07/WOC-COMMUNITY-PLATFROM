import {modules,programs,extraPages} from '@/lib/data';
import {PageView} from '@/components/Pages';
export const dynamicParams=false;
export function generateStaticParams(){return [...modules.map(m=>({section:m.slug,slug:[]})),...programs.map(p=>({section:p.module,slug:[p.slug]})),{section:'careers',slug:['opportunity']},...extraPages.map(section=>({section,slug:[]}))]}
export async function generateMetadata({params}:{params:Promise<{section:string;slug?:string[]}>}){const {section,slug}=await params;return {title:programs.find(p=>p.slug===slug?.[0])?.title||modules.find(m=>m.slug===section)?.name||section[0].toUpperCase()+section.slice(1)}}
export default async function Page({params}:{params:Promise<{section:string;slug?:string[]}>}){const p=await params;return <PageView section={p.section} slug={p.slug?.[0]}/>}
