import type {Program} from './data';

export const moduleImages:Record<string,string>={
 association:'home-reference',academy:'course-python',careers:'industry-partners',
 incubation:'innovation-lab',events:'campus-festival',partnerships:'global-partnerships',
 sports:'sports-cricket',culturals:'creative-arts',
};
const programImages:Record<string,string>={
 'python-full-stack':'course-python','artificial-intelligence':'course-ai',
 'data-analytics':'course-data','cybersecurity':'course-cyber',
 'ui-ux-design':'course-design','communication-skills':'course-communication',
 'frontend-internship':'course-python','data-internship':'course-data','design-internship':'course-design',
 'cricket-cup':'sports-cricket','football-cup':'sports-football','badminton-open':'sports-badminton',
 'arts-studio':'creative-arts','dance-stage':'campus-festival','music-stage':'campus-festival',
 'mentor-circle':'industry-partners','school-chapter':'course-communication',
 'access-partner':'course-communication','campus-skill-fest':'course-communication',
 'innovation-challenge':'innovation-lab','founders-meet':'industry-partners',
};
export function programImage(p:Program){return `/images/${programImages[p.slug]||moduleImages[p.module]||'campus-hero'}.webp`}
export function moduleImage(slug:string){return `/images/${moduleImages[slug]||'campus-hero'}.webp`}
