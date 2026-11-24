import type {Program} from './data';

export const moduleImages:Record<string,string>={
 association:'home-reference',academy:'course-python',careers:'industry-partners',
 incubation:'innovation-lab',events:'events-workshop',partnerships:'global-partnerships',
 sports:'sports-cricket',culturals:'campus-festival',
};
const programImages:Record<string,string>={
 'python-full-stack':'python-full-stack-v2','artificial-intelligence':'artificial-intelligence-v2',
 'data-analytics':'course-data','cybersecurity':'course-cyber',
 'ui-ux-design':'course-design','communication-skills':'course-communication',
 'frontend-internship':'frontend-intern-v2','data-internship':'data-intern-v2','design-internship':'product-design-intern-v2',
 'cricket-cup':'sports-cricket','football-cup':'sports-football','badminton-open':'sports-badminton',
 'arts-studio':'creative-arts','dance-stage':'dance-performance','music-stage':'music-performance',
 'mentor-circle':'industry-partners','school-chapter':'school-discovery',
 'college-chapter':'college-chapter','campus-ambassador':'campus-ambassador',
 'founders-lab':'incubation-prototype','industry-projects':'global-partnerships',
 'access-partner':'learning-access','campus-skill-fest':'skill-fest-workshop',
 'innovation-challenge':'innovation-hackathon','founders-meet':'founders-networking',
};
export function programImage(p:Program){return `/images/${programImages[p.slug]||moduleImages[p.module]||'campus-hero'}.webp`}
const moduleCardImages:Record<string,string>={careers:'careers-conversation',incubation:'incubation-person'};
export function moduleImage(slug:string){return `/images/${moduleCardImages[slug]||moduleImages[slug]||'campus-hero'}.webp`}
