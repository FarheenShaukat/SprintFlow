const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { test } = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");

function loadApi(fetch) {
  const exports = {};
  const source = ts.transpileModule(readFileSync(`${__dirname}/api.ts`, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
  }).outputText;
  vm.runInNewContext(source, { exports, process: { env: {} }, fetch, Headers, FormData, URLSearchParams });
  return exports;
}

test("task lists gather every page, retain filters and ignore the server's next URL", async () => {
  const paths = [];
  const { taskApi } = loadApi(async (path) => {
    paths.push(path);
    const page = Number(new URL(path, "https://app.example").searchParams.get("page") || 1);
    return Response.json({
      count: 23, previous: null,
      next: page === 1 ? "https://untrusted.example/tasks/?page=2" : null,
      results: Array.from({ length: page === 1 ? 20 : 3 }, (_, index) => ({ id: (page - 1) * 20 + index + 1 }))
    });
  });
  const result = await taskApi.list(5, "?mine=true&priority=high");
  assert.equal(result.results.length, 23);
  assert.equal(result.results.at(-1).id, 23);
  assert.equal(result.next, null);
  assert.deepEqual(paths, [
    "/api/projects/5/tasks?mine=true&priority=high&page=1",
    "/api/projects/5/tasks?mine=true&priority=high&page=2"
  ]);
});

test("workspace, project and membership lists include subsequent pages", async () => {
  const { workspaceApi, projectApi } = loadApi(async (path) => {
    const page = Number(new URL(path, "https://app.example").searchParams.get("page") || 1);
    return Response.json({ count: 2, previous: null, next: page === 1 ? "?page=2" : null, results: [{ id: page }] });
  });
  for (const list of [workspaceApi.list, () => workspaceApi.members(1), () => projectApi.list(1), () => projectApi.members(1)]) {
    assert.equal((await list()).results.length, 2);
  }
});

test("a failed later page rejects instead of silently returning an incomplete list", async () => {
  let requests = 0;
  const { taskApi } = loadApi(async () => ++requests === 1
    ? Response.json({ count: 2, previous: null, next: "?page=2", results: [{ id: 1 }] })
    : Response.json({ detail: "Could not load page" }, { status: 500 }));
  await assert.rejects(taskApi.list(1), /Could not load page/);
});

test("pagination rejects a server that keeps returning the same page", async () => {
  let requests = 0;
  const { taskApi } = loadApi(async () => {
    requests++;
    return Response.json({ count: 2, previous: null, next: "?page=2", results: [{ id: 1 }] });
  });
  await assert.rejects(taskApi.list(1), /pagination/i);
  assert.equal(requests, 2);
});

test("empty lists complete, but an empty page with next rejects", async () => {
  for (const next of [null, "?page=2"]) {
    const { workspaceApi } = loadApi(async () => Response.json({ count: 0, previous: null, next, results: [] }));
    if (next) await assert.rejects(workspaceApi.list(), /pagination/i);
    else assert.equal((await workspaceApi.list()).results.length, 0);
  }
});
