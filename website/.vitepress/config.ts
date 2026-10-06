import { defineConfig } from 'vitepress';

const repo = 'https://github.com/TypeFox/agent-skills';
// GitHub Pages serves the site under the repository's name.
const base = '/agent-skills/';

export default defineConfig({
    title: 'TypeFox Agent Skills',
    description: 'Agent skills for the open source technologies maintained at TypeFox',
    base,
    cleanUrls: true,
    themeConfig: {
        nav: [{ text: 'Skills', link: '/agent-experience' }],
        // One page per skill at the website root, so each guide lives at
        // typefox.dev/agent-skills/<skill-name>. Add new skills here.
        sidebar: [
            {
                text: 'Skills',
                items: [
                    { text: 'Agent Experience', link: '/agent-experience' },
                    { text: 'Eclipse License Check', link: '/eclipse-license-check' },
                    { text: 'Go Documentation', link: '/go-documentation' },
                    { text: 'Idiomatic Go', link: '/idiomatic-go' },
                    { text: 'Publish VS Code Extension', link: '/publish-vscode-extension' },
                    { text: 'Skill Evals', link: '/skill-evals' },
                    { text: 'TS Code Reviewer', link: '/ts-code-reviewer' },
                    { text: 'Write Like Me', link: '/write-like-me' }
                ]
            }
        ],
        search: { provider: 'local' },
        socialLinks: [{ icon: 'github', link: repo }],
        editLink: { pattern: `${repo}/edit/main/website/:path` },
        footer: {
            message: 'Released under the MIT License.',
            copyright: 'Made with ♥ by <a href="https://www.typefox.io/">TypeFox GmbH</a>'
        }
    }
});
