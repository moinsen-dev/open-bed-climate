import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import type { APIContext } from "astro";
import { SITE_NAME } from "../site.ts";

export async function GET(context: APIContext) {
  const posts = (await getCollection("log")).sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
  return rss({
    title: `${SITE_NAME} build log`,
    description: "Milestone updates from an open-source, local-first bed climate system.",
    site: context.site!,
    trailingSlash: true,
    items: posts.map((p) => ({ title: p.data.title, pubDate: p.data.date, description: p.data.summary, link: `/log/${p.id}/` })),
  });
}
