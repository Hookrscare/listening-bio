import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the listening.bio marketing page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /listening/i);
  assert.match(html, /Auditable acoustic biodiversity monitoring/i);
  assert.match(html, /Nature leaves/i);
  assert.match(html, /Automated detections are evidence candidates/i);
  assert.match(html, /\$10,000 pilot/i);
  assert.match(html, /rodrigo@listening\.bio/i);
});

test("verifies marketing page source structure", async () => {
  const [page, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(page, /SignalField/);
  assert.match(page, /Auditable acoustic biodiversity monitoring/);
  assert.match(page, /Automated detections are evidence candidates/);
  assert.match(layout, /listening\.bio/i);
  assert.match(packageJson, /"vinext"/);
});

