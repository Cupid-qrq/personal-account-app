/** Interaction verification through actual Chrome MCP mouse movement, not synthetic pointer events. */
export async function interactionChecks({
  tool,
  evaluate,
  uid,
  click,
  go,
  shot,
  check,
  a11y,
}) {
  async function probes(selector, prefix) {
    await evaluate(
      `()=>{document.querySelectorAll('[data-motion-probe]').forEach(e=>e.remove());const zone=document.querySelector(${JSON.stringify(selector)});for(const [name,x,y] of [['nw',12,16],['se',82,76]]){const e=document.createElement('span');e.dataset.motionProbe='true';e.setAttribute('role','img');e.setAttribute('aria-label',${JSON.stringify(prefix)}+'-'+name);e.style.cssText='position:absolute;width:12px;height:12px;z-index:30;left:'+x+'%;top:'+y+'%;';zone.append(e)}return true}`,
    );
  }
  async function settle(selector = ".chapter-card") {
    return evaluate(
      `async()=>{await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));const e=document.querySelector(${JSON.stringify(selector)});for(let i=0;i<120;i++){if(e.dataset.pointerMotion==='idle')return {x:Number(e.style.getPropertyValue('--pointer-x')),y:Number(e.style.getPropertyValue('--pointer-y')),active:Number(e.style.getPropertyValue('--pointer-active')),matrix:getComputedStyle(e).transform};await new Promise(r=>setTimeout(r,16))}throw new Error('Spring did not settle')}`,
    );
  }
  async function round() {
    await tool("hover", { uid: await uid("image", "paper-nw") });
    const left = await settle();
    await tool("hover", { uid: await uid("image", "paper-se") });
    const right = await settle();
    if (left.x >= -0.4 || right.x <= 0.4 || left.matrix === right.matrix)
      throw new Error(JSON.stringify({ left, right }));
    await tool("hover", { uid: await uid("button", "刷新账本") });
    const rest = await settle();
    if (rest.x || rest.y || rest.active)
      throw new Error("Tilt did not return to rest " + JSON.stringify(rest));
    return { left: left.matrix, right: right.matrix, rest: rest.matrix };
  }
  async function removeProbes() {
    await evaluate(
      `()=>{document.querySelectorAll('[data-motion-probe]').forEach(e=>e.remove());return true}`,
    );
  }
  async function scrollAt(top) {
    return evaluate(
      `async()=>{scrollTo({top:${top},behavior:'instant'});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(r))));const e=document.querySelector('.chapter-scroll-layer');return {top:scrollY,front:getComputedStyle(e).transform,back:getComputedStyle(document.querySelector('.chapter-paper-back')).transform,timeline:e.getAnimations()[0]?.timeline?.constructor.name || null,overflow:document.documentElement.scrollWidth>innerWidth}}`,
    );
  }
  await check(
    "paper tilt changes actual matrices across five real mouse reentries",
    async () => {
      await go();
      await probes(".chapter-art", "paper");
      const rounds = [];
      for (let i = 0; i < 5; i++) rounds.push(await round());
      await tool("hover", { uid: await uid("image", "paper-se") });
      await settle();
      await shot("paper-hover-repeat");
      await removeProbes();
      await a11y();
      return { rounds };
    },
  );
  await check(
    "tilt survives dialog close, month change and route return",
    async () => {
      await click("button", "编辑月度手记与月结状态");
      await tool("press_key", { key: "Escape" });
      await probes(".chapter-art", "paper");
      await round();
      await click("combobox", "选择月份");
      await click("option", "2026 年 9 月");
      await evaluate(
        `async()=>{for(let i=0;i<80;i++){if(document.querySelector('h1').textContent.includes('九月'))return true;await new Promise(r=>setTimeout(r,30))}throw new Error('Month not changed')}`,
      );
      await probes(".chapter-art", "paper");
      await round();
      await click("link", "消费分析");
      await click("link", "月度总览");
      await probes(".chapter-art", "paper");
      await round();
      await removeProbes();
      await go();
    },
  );
  await check(
    "native scroll timeline scrubs both ways and holds when scrolling stops",
    async () => {
      const start = await scrollAt(0),
        middle = await scrollAt(100);
      await shot("scroll-paper-middle");
      const end = await scrollAt(240);
      await shot("scroll-paper-end");
      await evaluate(
        `async()=>{await new Promise(r=>setTimeout(r,350));return true}`,
      );
      const held = await scrollAt(240),
        back = await scrollAt(0);
      if (
        middle.timeline !== "ScrollTimeline" ||
        start.front === middle.front ||
        middle.back === end.back ||
        end.front !== held.front ||
        start.front !== back.front ||
        [start, middle, end, back].some((s) => s.overflow)
      )
        throw new Error(JSON.stringify({ start, middle, end, held, back }));
      return { start, middle, end, held, back };
    },
  );
  await check(
    "scroll fallback uses live progress when native animation is disabled",
    async () => {
      await evaluate(
        `()=>{document.querySelectorAll('.chapter-scroll-layer,.chapter-paper').forEach(e=>e.style.animation='none');return true}`,
      );
      const start = await scrollAt(0),
        end = await scrollAt(240),
        back = await scrollAt(0);
      if (start.front === end.front || start.front !== back.front)
        throw new Error(JSON.stringify({ start, end, back }));
      await go();
      return { start, end, back };
    },
  );
  await check(
    "magnetic action repeats, returns to rest and opens by keyboard",
    async () => {
      await probes(".magnetic-zone", "magnet");
      for (let i = 0; i < 3; i++) {
        await tool("hover", { uid: await uid("image", "magnet-se") });
        await settle(".magnetic-button");
        const translated = await evaluate(
          `()=>getComputedStyle(document.querySelector('.magnetic-content')).translate`,
        );
        if (translated === "none" || translated === "0px")
          throw new Error("Magnet did not move");
        if (i === 0) await shot("magnetic-action");
        await tool("hover", { uid: await uid("button", "刷新账本") });
        const rest = await settle(".magnetic-button");
        if (rest.x || rest.y || rest.active)
          throw new Error("Magnet did not reset");
      }
      await removeProbes();
      await click("button", "月度手记");
      await tool("press_key", { key: "Escape" });
      await tool("press_key", { key: "Enter" });
      if (!(await evaluate(`()=>!!document.querySelector('.review-dialog')`)))
        throw new Error("Keyboard action did not open review");
      await tool("press_key", { key: "Escape" });
    },
  );
  await check(
    "hover lift, animated underline and arrow feedback work repeatedly",
    async () => {
      await evaluate(
        `()=>{document.querySelector('.recent-transactions').scrollIntoView({block:'center'});return true}`,
      );
      await tool("hover", {
        uid: await uid("button", "队服 10月9日 · 日常 −¥75.00"),
      });
      const lift = await evaluate(
        `async()=>{await new Promise(r=>setTimeout(r,320));return getComputedStyle(document.querySelector('.transaction-preview')).transform}`,
      );
      if (lift === "none" || lift === "matrix(1, 0, 0, 1, 0, 0)")
        throw new Error("No lift");
      await tool("hover", { uid: await uid("button", "写下本月手记") });
      const line = await evaluate(
        `async()=>{await new Promise(r=>setTimeout(r,320));return getComputedStyle(document.querySelector('.month-note-panel .text-link'),'::after').transform}`,
      );
      if (!line.startsWith("matrix(1,"))
        throw new Error("Underline not expanded: " + line);
      await shot("microinteractions");
      await go();
      return { lift, line };
    },
  );
  await check(
    "list rows enter with ordered stagger without changing values",
    async () => {
      const delays = await evaluate(
        `async()=>{document.querySelector('.recent-transactions').scrollIntoView({block:'center'});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>requestAnimationFrame(r))));return [...document.querySelectorAll('.transaction-preview')].map(e=>({value:e.querySelector('.transaction-value').textContent,delay:e.getAnimations().find(a=>a.id==='atlas-reveal')?.effect.getTiming().delay}))}`,
      );
      const observed = delays.filter((d) => d.delay !== undefined);
      if (
        observed.length < 2 ||
        observed[0].value !== "−¥75.00" ||
        !observed.some((d, i) => i && d.delay > observed[i - 1].delay)
      )
        throw new Error(JSON.stringify(delays));
      await go();
      return { delays };
    },
  );
  await check("removed ornamental copy is absent from overview", async () => {
    const s = await evaluate(
      `()=>({bad:['生活记录中','每一笔，都有生活的注脚','记录是理解生活的起点','从容生活','MAKE ROOM FOR LIFE'].filter(s=>document.body.innerText.includes(s)),summary:document.querySelector('.hero-number').textContent})`,
    );
    if (s.bad.length || s.summary !== "¥744.00")
      throw new Error(JSON.stringify(s));
    return s;
  });
  await check(
    "reduced motion cancels an active spring and reenable restores reentry",
    async () => {
      await probes(".chapter-art", "paper");
      await tool("hover", { uid: await uid("image", "paper-se") });
      await click("button", "减少动态效果");
      const off = await evaluate(
        `()=>({matrix:getComputedStyle(document.querySelector('.chapter-card')).transform,active:document.querySelector('.chapter-card').dataset.pointerMotion,scroll:getComputedStyle(document.querySelector('.chapter-scroll-layer')).transform})`,
      );
      if (
        off.matrix !== "none" ||
        off.active !== "idle" ||
        off.scroll !== "none"
      )
        throw new Error(JSON.stringify(off));
      await click("button", "开启动效");
      await round();
      await removeProbes();
      return off;
    },
  );
  await check(
    "touch layout scrolls without mouse tilt, glow or horizontal overflow",
    async () => {
      await tool("emulate", { viewport: "375x812x1,mobile,touch" });
      await go();
      const start = await scrollAt(0),
        middle = await scrollAt(160);
      const s = await evaluate(
        `()=>({x:document.querySelector('.chapter-card').style.getPropertyValue('--pointer-x'),glow:getComputedStyle(document.querySelector('.chapter-spotlight')).opacity})`,
      );
      if (
        start.overflow ||
        middle.overflow ||
        Number(s.x) !== 0 ||
        Number(s.glow) !== 0
      )
        throw new Error(JSON.stringify({ start, middle, s }));
      await scrollAt(0);
      await shot("motion-mobile", true);
      await a11y();
      await tool("emulate", { viewport: "1440x1080x1" });
      await go();
      return { start, middle, s };
    },
  );
}
