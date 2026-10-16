import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";

export async function audit(call, root, base) {
  const output = path.join(
    root,
    process.env.LEDGER_QA_OUTPUT || "output/qa-v3.2",
  );
  const records = [],
    reducedSystem = !!process.env.LEDGER_REDUCED_MOTION;
  const text = (r) =>
    r.content
      ?.filter((c) => c.type === "text")
      .map((c) => c.text)
      .join("\n") || "";
  const created = text(
    await call("new_page", { url: base + "/?month=2026-10" }),
  );
  const pageId = Number(created.match(/(\d+): .+\[selected\]/)?.[1]);
  const require = createRequire(path.join(root, "frontend/package.json"));
  const axe = await fs.readFile(require.resolve("axe-core/axe.min.js"), "utf8");
  async function tool(name, args = {}) {
    const r = await call(name, { pageId, ...args });
    if (r.isError) throw new Error(text(r));
    return r;
  }
  async function evaluate(fn) {
    const result = text(
      await tool("evaluate_script", { function: fn, waitForStableDom: false }),
    );
    const json = result.match(/```json\n([\s\S]*?)\n```/);
    if (!json) throw new Error(result);
    return JSON.parse(json[1]);
  }
  async function ready(selector) {
    await evaluate(
      `async()=>{for(let i=0;i<100;i++){if(document.querySelector(${JSON.stringify(selector)}))return true;await new Promise(r=>setTimeout(r,50))}throw new Error('Missing '+${JSON.stringify(selector)})}`,
    );
  }
  async function uid(role, name) {
    const snapshot = text(await tool("take_snapshot"));
    const line = snapshot
      .split("\n")
      .find((l) => l.includes(` ${role} "${name}"`));
    if (!line)
      throw new Error("Missing " + role + " " + name + "\n" + snapshot);
    return line.match(/uid=(\S+)/)[1];
  }
  async function click(role, name) {
    await tool("click", { uid: await uid(role, name) });
  }
  async function go(query = "?month=2026-10") {
    await tool("navigate_page", { type: "url", url: base + "/" + query });
    await ready(".month-note-panel");
  }
  async function shot(name, fullPage = false) {
    await tool("take_screenshot", {
      filePath: path.join(output, name + ".png"),
      fullPage,
    });
  }
  async function check(name, fn) {
    try {
      const detail = await fn();
      const log = text(
        await tool("list_console_messages", { types: ["error", "warn"] }),
      );
      if (!log.includes("no console messages")) throw new Error(log);
      records.push({ name, pass: true, detail });
      console.log("PASS " + name);
    } catch (e) {
      records.push({ name, pass: false, error: e.message });
      console.log("FAIL " + name + ": " + e.message.slice(0, 500));
    }
  }
  async function a11y() {
    const result = await evaluate(
      `async()=>{${axe};const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))}`,
    );
    if (result.length) throw new Error(JSON.stringify(result));
    return { violations: 0 };
  }
  await ready(".month-note-panel");
  if (reducedSystem) {
    await check(
      "system reduced motion is respected at first render",
      async () => {
        const s = await evaluate(
          `()=>({system:matchMedia('(prefers-reduced-motion: reduce)').matches,mode:document.documentElement.dataset.motion,animations:document.getAnimations().filter(a=>a.playState==='running').length,amount:document.querySelector('.hero-number').textContent})`,
        );
        if (
          !s.system ||
          s.mode !== "reduce" ||
          s.animations ||
          !s.amount.includes("744.00")
        )
          throw new Error(JSON.stringify(s));
        await shot("system-reduced-desktop");
        return s;
      },
    );
    await check(
      "system reduced mode has no parallax or reveal on scroll",
      async () => {
        const s = await evaluate(
          `async()=>{window.scrollTo(0,600);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return {transform:getComputedStyle(document.querySelector('.chapter-scroll-layer')).transform,animations:document.getAnimations().filter(a=>a.playState==='running').length}}`,
        );
        if (s.transform !== "none" || s.animations)
          throw new Error(JSON.stringify(s));
        return s;
      },
    );
    await check("system reduced mode mobile layout and contrast", async () => {
      await tool("emulate", { viewport: "375x812x1,mobile,touch" });
      await go();
      await shot("system-reduced-mobile", true);
      if (await evaluate("()=>document.documentElement.scrollWidth>innerWidth"))
        throw new Error("Overflow");
      return a11y();
    });
  } else {
    await check(
      "actual hero animation intermediate and final states",
      async () => {
        await click("button", "减少动态效果");
        const initial = await evaluate(
          `async()=>{document.querySelector('button[aria-label="开启动效"]').click();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const a=document.getAnimations().filter(a=>a.animationName?.startsWith('chapter-'));a.forEach(a=>{a.pause();a.currentTime=80});return {animations:a.map(a=>a.animationName),opacity:getComputedStyle(document.querySelector('.chapter-card')).opacity,transform:getComputedStyle(document.querySelector('.chapter-enter')).transform}}`,
        );
        if (
          initial.animations.length < 3 ||
          initial.opacity !== "1" ||
          initial.transform === "none" ||
          initial.transform === "matrix(1, 0, 0, 1, 0, 0)"
        )
          throw new Error(JSON.stringify(initial));
        await shot("hero-frame-080");
        await a11y();
        await evaluate(
          `()=>{document.getAnimations().filter(a=>a.animationName?.startsWith('chapter-')).forEach(a=>{a.currentTime=360});return true}`,
        );
        await shot("hero-frame-360");
        await evaluate(
          `()=>{document.getAnimations().filter(a=>a.animationName?.startsWith('chapter-')).forEach(a=>a.finish());return true}`,
        );
        await shot("hero-frame-final");
        return initial;
      },
    );
    const { interactionChecks } = await import("./interaction-checks.mjs");
    await interactionChecks({
      tool,
      evaluate,
      uid,
      click,
      go,
      shot,
      check,
      a11y,
    });
    await check(
      "scroll changes reading progress and reveals lower content",
      async () => {
        const s = await evaluate(
          `async()=>{document.querySelector('.month-note-panel').scrollIntoView({block:'center'});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(r))));return {progress:getComputedStyle(document.documentElement).getPropertyValue('--reading-progress'),drift:getComputedStyle(document.documentElement).getPropertyValue('--hero-progress'),revealed:document.querySelector('.month-note-panel').dataset.revealed,animations:document.getAnimations().filter(a=>a.id==='atlas-reveal').length}}`,
        );
        if (
          Number(s.progress) <= 0 ||
          Number(s.drift) <= 0 ||
          s.revealed !== "true"
        )
          throw new Error(JSON.stringify(s));
        await shot("scroll-journal");
        return s;
      },
    );
    await check(
      "manual reduced motion persists and cancels motion",
      async () => {
        await click("button", "减少动态效果");
        const a = await evaluate(
          `()=>({mode:document.documentElement.dataset.motion,running:document.getAnimations().filter(a=>a.playState==='running').length})`,
        );
        if (a.mode !== "reduce" || a.running)
          throw new Error(JSON.stringify(a));
        await go();
        if (
          (await evaluate("()=>document.documentElement.dataset.motion")) !==
          "reduce"
        )
          throw new Error("Preference lost");
        await shot("manual-reduced");
        await click("button", "开启动效");
      },
    );
    await check(
      "monthly note saves, reloads and enters print report",
      async () => {
        const before = await evaluate(
          `async()=>(await(await fetch('/api/summary?month=2026-10')).json()).review || {note:'',status:'auto'}`,
        );
        try {
          await click("button", "编辑月度手记与月结状态");
          await tool("fill", {
            uid: await uid("textbox", "本月手记"),
            value: "本月添置了学习用品。\n周末和朋友一起运动。",
          });
          await click("button", "保存月度手记");
          await ready(".chapter-card");
          await go();
          const s = await evaluate(
            `()=>({note:document.querySelector('.month-note-panel>p').textContent,print:document.querySelector('.printed-note')?.textContent})`,
          );
          if (!s.note.includes("学习用品") || s.note !== s.print)
            throw new Error(JSON.stringify(s));
          await shot("note-saved", true);
        } finally {
          await evaluate(
            `async()=>{await fetch('/api/reviews/2026-10',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(${JSON.stringify({ note: before.note, status: before.status })})});return true}`,
          );
        }
      },
    );
    await check(
      "month close changes actual day count, and can be undone",
      async () => {
        await go();
        const before = await evaluate(
          `async()=>(await(await fetch('/api/summary?month=2026-10')).json()).review`,
        );
        try {
          await click("button", "编辑月度手记与月结状态");
          await click("combobox", "月结状态");
          await click("option", "已完成月结");
          await click("button", "保存月度手记");
          await go();
          const days = await evaluate(
            `async()=>(await(await fetch('/api/summary?month=2026-10')).json()).coverage.observed_days`,
          );
          if (
            days !== 31 ||
            !text(await tool("take_snapshot")).includes("已完成月结")
          )
            throw new Error("Close not applied");
        } finally {
          await evaluate(
            `async()=>{await fetch('/api/reviews/2026-10',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(${JSON.stringify({ note: before.note, status: before.status })})});return true}`,
          );
        }
      },
    );
    await check(
      "unsaved note offers continue editing and discard",
      async () => {
        await go();
        await click("button", "编辑月度手记与月结状态");
        await tool("fill", {
          uid: await uid("textbox", "本月手记"),
          value: "尚未保存的草稿",
        });
        await tool("press_key", { key: "Escape" });
        await click("button", "继续编辑");
        if (!text(await tool("take_snapshot")).includes("尚未保存的草稿"))
          throw new Error("Draft lost");
        if ((await evaluate(`()=>document.activeElement?.id`)) !== "month-note")
          throw new Error("Editing focus was not restored");
        await tool("press_key", { key: "Escape" });
        await click("button", "放弃修改");
        await ready(".chapter-card");
      },
    );
    await check(
      "mobile review fits with visible fields and accessible contrast",
      async () => {
        await tool("emulate", { viewport: "375x812x1,mobile,touch" });
        await go();
        await click("button", "编辑月度手记与月结状态");
        if ((await evaluate(`()=>document.activeElement?.tagName`)) !== "H2")
          throw new Error(
            "Mobile dialog should focus its title, not summon the keyboard",
          );
        await evaluate(
          `async()=>{await Promise.all(document.getAnimations().filter(a=>a.timeline instanceof DocumentTimeline).map(a=>a.finished.catch(()=>{})));return true}`,
        );
        const r = await evaluate(
          `()=>{const r=document.querySelector('[role=dialog]').getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}}`,
        );
        if (r.left < 0 || r.right > 376 || r.top < 0 || r.bottom > 813)
          throw new Error(JSON.stringify(r));
        await shot("review-mobile");
        await a11y();
        await tool("press_key", { key: "Escape" });
      },
    );
    await check(
      "same-file preview shows unchanged count without false differences",
      async () => {
        await tool("emulate", { viewport: "1440x1000x1" });
        await go();
        await click("button", "导入账单 +");
        await tool("upload_file", {
          uid: await uid(
            "button",
            "选择文件，或拖到这里 从记账软件导出的原始账单",
          ),
          filePaths: [path.join(root, "data/origin/2026-10-11_100114.xlsx")],
        });
        await click("button", "预览并校验");
        await ready(".import-preview");
        const counts = await evaluate(
          `()=>[...document.querySelectorAll('.preview-counts b')].map(e=>Number(e.textContent))`,
        );
        if (counts.join(",") !== "0,0,387")
          throw new Error(JSON.stringify(counts));
        await shot("import-unchanged");
        await tool("press_key", { key: "Escape" });
      },
    );
    await check(
      "changed-file preview shows before and after without writes",
      async () => {
        const fixture = path.join(output, "preview-changes.csv");
        const row = await evaluate(
          `async()=>(await(await fetch('/api/transactions?month=2026-10')).json()).rows.find(r=>r.note==='队服')`,
        );
        const csv =
          "ID,时间,分类,二级分类,类型,金额,备注,账本,币种\n" +
          [
            row.id,
            row.date,
            row.category,
            row.subcategory,
            row.type,
            80,
            "队服（核对）",
            row.book,
            "CNY",
          ].join(",");
        await fs.writeFile(fixture, csv, "utf8");
        await go();
        await click("button", "导入账单 +");
        await tool("upload_file", {
          uid: await uid(
            "button",
            "选择文件，或拖到这里 从记账软件导出的原始账单",
          ),
          filePaths: [fixture],
        });
        await click("button", "预览并校验");
        await ready(".import-diff");
        await evaluate(
          `()=>{document.querySelector('.import-diff').open=true;return true}`,
        );
        const content = await evaluate(
          `()=>document.querySelector('.import-diff').textContent`,
        );
        if (!content.includes("75.00") || !content.includes("80.00"))
          throw new Error("Missing amount difference");
        await shot("import-changes");
        await a11y();
        await tool("press_key", { key: "Escape" });
        if (
          (await evaluate(
            `async()=>(await(await fetch('/api/summary?month=2026-10')).json()).metrics.expense`,
          )) !== 744
        )
          throw new Error("Preview changed live data");
      },
    );
    await check(
      "200 percent browser-equivalent layout keeps core actions readable",
      async () => {
        await tool("emulate", { viewport: "720x500x2" });
        await go();
        if (
          await evaluate("()=>document.documentElement.scrollWidth>innerWidth")
        )
          throw new Error("Overflow at zoom equivalent");
        await shot("zoom-equivalent", true);
      },
    );
  }
  const filename = reducedSystem
    ? "system-reduced-results.json"
    : "motion-results.json";
  await fs.writeFile(
    path.join(output, filename),
    JSON.stringify(
      {
        at: new Date().toISOString(),
        driver: "Chrome DevTools MCP",
        checks: records.length,
        failed: records.filter((r) => !r.pass).length,
        records,
      },
      null,
      2,
    ),
  );
  console.log(
    JSON.stringify({
      checks: records.length,
      failed: records.filter((r) => !r.pass).length,
    }),
  );
  return records;
}
