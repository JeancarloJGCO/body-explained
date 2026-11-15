import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Change SITE_URL in Netlify env vars when you connect your own domain.
const site = process.env.SITE_URL || 'https://the-body-explained.netlify.app';

export default defineConfig({
  site,
  trailingSlash: 'always',
  integrations: [sitemap()],
  build: { format: 'directory' },
});
