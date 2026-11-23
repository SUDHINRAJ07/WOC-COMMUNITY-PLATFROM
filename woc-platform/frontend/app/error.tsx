'use client';
export default function ErrorPage({reset}:{reset:()=>void}){return <main className="container section"><h1>Something interrupted this page.</h1><p>Please try loading it again.</p><button onClick={reset} className="button">Try again</button></main>}
