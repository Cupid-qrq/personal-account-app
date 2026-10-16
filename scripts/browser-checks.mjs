import fs from 'node:fs/promises'
import path from 'node:path'
import { createRequire } from 'node:module'

export async function audit(call, root, base = 'http://127.0.0.1:8000') {
  const output = path.join(root, process.env.LEDGER_QA_OUTPUT || 'output/qa-v3.1')
  const records = []
  const text = r => r.content?.filter(c => c.type === 'text').map(c => c.text).join('\n') || ''
  const first = text(await call('new_page', { url: base }))
  const pageId = Number(first.match(/(\d+): .+\[selected\]/)?.[1])
  if (!pageId) throw new Error('No Chrome page opened: ' + first)
  async function tool(name, args = {}) {
    if(name === 'take_screenshot') await call('evaluate_script', {pageId, function:'async () => {await Promise.all(document.getAnimations().filter(a=>a.effect?.getComputedTiming().iterations!==Infinity).map(a=>a.finished.catch(()=>{})));return true}'})
    const r = await call(name, { pageId, ...args }); if (r.isError) throw new Error(text(r)); return r
  }
  async function evaluate(fn) { const r = text(await tool('evaluate_script', { function: fn })); const json = r.match(/```json\n([\s\S]*?)\n```/); if (!json) throw new Error(r); return JSON.parse(json[1]) }
  async function ready(selector) { await evaluate(`async () => { for (let i=0;i<100;i++) { if(document.querySelector(${JSON.stringify(selector)})) return true; await new Promise(r=>setTimeout(r,50)) } throw new Error('Missing ready selector') }`) }
  async function snapshot() { return text(await tool('take_snapshot')) }
  async function uid(role, name) {
    const snap = await snapshot()
    const line = snap.split('\n').find(line => line.includes(` ${role} "${name}"`))
    if (!line) throw new Error(`Missing ${role} "${name}"\n${snap}`)
    return line.match(/uid=(\S+)/)[1]
  }
  async function click(role, name) { await tool('click', { uid: await uid(role, name) }) }
  async function fill(name, value) { await tool('fill', { uid: await uid('textbox', name), value }) }
  async function check(name, fn) { try { const detail = await fn(); records.push({ name, pass: true, detail }); console.log('PASS ' + name) } catch (error) { records.push({ name, pass: false, error: error.message }); console.log('FAIL ' + name + ': ' + error.message.slice(0, 350)) } }
  async function go(query = '', selector = '.money-summary') { await tool('navigate_page', { type: 'url', url: `${base}/${query}` }); await ready(selector) }
  async function chartsReady() {
    return evaluate(`async () => {
      await document.fonts.ready;
      for(let i=0;i<100;i++) {
        const containers=[...document.querySelectorAll('.recharts-responsive-container')];
        const ok=containers.every(e=>{const svg=e.querySelector('svg.recharts-surface'); return svg && Math.abs(Number(svg.getAttribute('width'))-e.clientWidth)<2 && svg.querySelector('path[d]')});
        if(ok){await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return true}
        await new Promise(r=>setTimeout(r,50));
      }
      throw new Error('Chart geometry did not settle');
    }`)
  }
  const require = createRequire(path.join(root, 'frontend/package.json'))
  const axe = await fs.readFile(require.resolve('axe-core/axe.min.js'), 'utf8')
  for (const width of [1440, 1024, 768, 390, 375]) {
    await tool('emulate', { viewport: `${width}x${width < 768 ? 844 : 1000}x1${width < 768 ? ',mobile,touch' : ''}` })
    for (const [view, selector] of [['overview', '.money-summary'], ['analysis', '.calendar-grid'], ['ledger', '.ledger-table'], ['data', '.source-panel']]) {
      await check(`${width}px ${view} layout`, async () => {
        await go(`?view=${view}&month=2026-10`, selector)
        await chartsReady()
        const layout = await evaluate(`() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('main *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0 && r.right>innerWidth+1}).slice(0,12).map(e=>({tag:e.tagName,class:String(e.className),text:e.textContent.slice(0,60)}))})`)
        await tool('take_screenshot', { filePath: path.join(output, `${view}-${width}.png`), fullPage: true })
        if (layout.scrollWidth > width || layout.overflow.length) throw new Error(JSON.stringify(layout))
        const consoleLog = text(await tool('list_console_messages', { types: ['error', 'warn'] }))
        if (!consoleLog.includes('no console messages')) throw new Error(consoleLog)
        return layout
      })
    }
  }
  await tool('emulate', { viewport: '1440x1000x1' })
  for (const [view, selector] of [['overview', '.money-summary'], ['analysis', '.calendar-grid'], ['ledger', '.ledger-table'], ['data', '.source-panel']]) {
    await check(`${view} accessibility`, async () => {
      await go(`?view=${view}&month=2026-10`, selector)
      const result = await evaluate(`async () => { ${axe}; const r=await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}}); return r.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})) }`)
      await fs.writeFile(path.join(output, `axe-${view}.json`), JSON.stringify(result, null, 2))
      if (result.length) throw new Error(JSON.stringify(result).slice(0, 2000))
      return { violations: 0 }
    })
  }
  await go()
  await check('month select with keyboard', async () => {
    await click('combobox', '选择月份'); await tool('press_key', {key:'ArrowDown'}); await tool('press_key', {key:'Enter'})
    await ready('.money-summary')
    const ok = await evaluate(`async () => { for(let i=0;i<60;i++){if(document.querySelector('h1')?.textContent.includes('九月')) return true; await new Promise(r=>setTimeout(r,50))} return false }`)
    if (!ok) throw new Error('Month did not update')
    if (!(await evaluate('() => location.search')).includes('month=2026-09')) throw new Error('Month absent from URL')
  })
  await check('ledger search, empty and reset', async () => {
    await go('?view=ledger&month=2026-10', '.ledger-table')
    await fill('搜索账单', '队服')
    if (await evaluate('() => document.querySelectorAll(".ledger-table tbody tr").length') !== 1) throw new Error('Search mismatch')
    await fill('搜索账单', 'no-such-record')
    if (!(await snapshot()).includes('没有找到匹配的账单')) throw new Error('Missing empty state')
    await click('button', '清除筛选'); await ready('.ledger-table')
  })
  await check('pagination and amount sorting', async () => {
    await go('?view=ledger&month=2026-09', '.ledger-table')
    await click('button', '下一页')
    if (!(await evaluate('() => location.search')).includes('page=2')) throw new Error('Page did not advance')
    await click('button', '金额')
    const amounts = await evaluate('() => [...document.querySelectorAll("tbody .amount-cell")].map(e=>Number(e.textContent.replace(/[^0-9.]/g,"")))')
    if (!amounts.every((v, i) => !i || v <= amounts[i-1])) throw new Error('Not sorted descending')
  })
  await check('category drilldown and detail sheet', async () => {
    await go(); await click('button', '查看日常明细'); await ready('.ledger-table')
    if (!(await evaluate('() => decodeURIComponent(location.search)')).includes('category=日常')) throw new Error('Filter missing')
    await click('button', '查看队服账单详情')
    if (!(await snapshot()).includes('原始 ID')) throw new Error('Missing details')
    await tool('take_screenshot', { filePath: path.join(output, 'detail-desktop.png') })
    const bounds=await evaluate('()=>{const r=document.querySelector("[role=dialog]").getBoundingClientRect();return {left:r.left,right:r.right,width:innerWidth}}')
    if(bounds.left<0 || bounds.right>bounds.width+1)throw new Error('Detail drawer extends beyond viewport: '+JSON.stringify(bounds))
    await tool('press_key', { key: 'Escape' })
    const closed = await evaluate(`async () => {for(let i=0;i<30;i++){if(!document.querySelector('[role="dialog"][data-state="open"]'))return true; await new Promise(r=>setTimeout(r,50))}return false}`)
    if (!closed) throw new Error('Escape did not close')
  })
  await check('chart tabs and accessible data table', async () => {
    await go(); await click('tab', '年度')
    if (!(await snapshot()).includes('这一年的收与支')) throw new Error('Annual chart unavailable')
    await click('button', '查看数据表')
    if (await evaluate('() => document.querySelectorAll(".chart-data-table tbody tr").length') !== 10) throw new Error('Chart table mismatch')
  })
  await check('budget form and persistence', async () => {
    await go()
    const before = await evaluate('async () => (await (await fetch("/api/summary?month=2026-10")).json()).budget')
    try {
      await click('button', before ? '调整预算' : '设置预算')
      const snap = await snapshot(), id = snap.match(/uid=(\S+) spinbutton "月度支出预算（元）"/)?.[1]
      if (!id) throw new Error('Budget input missing')
      await tool('fill', { uid: id, value: '3200' }); await click('button', '保存预算')
      await ready('.budget-progress .progress-track')
      const after = await evaluate('async () => (await (await fetch("/api/summary?month=2026-10")).json()).budget')
      if (after !== 3200) throw new Error('Budget not persisted')
      await tool('take_screenshot', { filePath: path.join(output, 'budget-saved.png') })
    } finally {
      await evaluate(`async () => (await fetch('/api/budgets/2026-10',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount:${JSON.stringify(before)}})})).ok`)
    }
  })
  await check('import preview with real Excel, no writes', async () => {
    await go(); await click('button', '导入账单 +')
    const drop = await uid('button', '选择文件，或拖到这里 从记账软件导出的原始账单')
    await tool('upload_file', { uid: drop, filePaths: [path.join(root, 'data/origin/2026-10-11_100114.xlsx')] })
    await click('button', '预览并校验')
    await ready('.import-preview')
    const snap = await snapshot()
    if (!snap.includes('校验通过，可以导入')) throw new Error('Import did not pass')
    await tool('take_screenshot', { filePath: path.join(output, 'import-preview.png') })
    await tool('press_key', { key: 'Escape' })
  })
  await check('mobile dialog fits and Escape works', async () => {
    await tool('emulate', { viewport: '375x812x1,mobile,touch' }); await go('?view=data', '.source-panel')
    await click('button', '导入新账单')
    await tool('take_screenshot', { filePath: path.join(output, 'import-mobile.png') })
    const r = await evaluate('() => {const r=document.querySelector("[role=dialog]").getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:innerWidth,height:innerHeight}}')
    if(r.left<0 || r.right>r.width || r.top<0 || r.bottom>r.height) throw new Error(JSON.stringify(r))
    await tool('press_key', { key: 'Escape' })
  })
  await tool('emulate', {viewport:'1440x1000x1'})
  await check('subcategory drilldown preserves exact filter after reload', async () => {
    await go('?view=analysis&month=2026-10', '.subcategories button')
    const snap=await snapshot(), line=snap.split('\n').find(l=>l.includes(' button "01 ') && l.includes('学习'))
    if(!line) throw new Error('Subcategory button missing')
    await tool('click',{uid:line.match(/uid=(\S+)/)[1]}); await ready('.ledger-table')
    const url=await evaluate('()=>location.href')
    if(!decodeURIComponent(url).includes('subcategory=学习'))throw new Error('Subcategory absent from URL')
    await tool('navigate_page',{type:'reload'}); await ready('.ledger-table')
    const labels=await evaluate('()=>[...document.querySelectorAll(".category-cell small")].map(e=>e.textContent)')
    if(!labels.length || labels.some(s=>s!=='学习'))throw new Error('Subcategory filter lost')
  })
  await check('chart keyboard tooltip displays actual amount', async () => {
    await go(); await chartsReady()
    const snap=await snapshot(), line=snap.split('\n').find(l=>l.includes(' application'))
    if(!line)throw new Error('Accessible chart missing')
    await tool('click',{uid:line.match(/uid=(\S+)/)[1]}); await tool('press_key',{key:'ArrowRight'})
    await ready('.chart-tooltip')
    if(!(await snapshot()).includes('支出'))throw new Error('Missing tooltip amount')
    await tool('take_screenshot',{filePath:path.join(output,'chart-tooltip.png')})
  })
  await check('mobile accessibility including import dialog', async () => {
    await tool('emulate',{viewport:'375x812x1,mobile,touch'}); await go('?view=data','.source-panel');await click('button','导入新账单')
    const violations=await evaluate(`async () => {${axe};const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.failureSummary)}))}`)
    if(violations.length)throw new Error(JSON.stringify(violations))
    await tool('press_key',{key:'Escape'})
  })
  await check('browser back restores page and month', async () => {
    await tool('emulate',{viewport:'1440x1000x1'});await go('?view=overview&month=2026-09');await click('link','消费分析');await ready('.calendar-grid')
    await tool('navigate_page',{type:'back'});await ready('.money-summary')
    if(!(await evaluate('()=>document.querySelector("h1").textContent')).includes('九月'))throw new Error('Back lost month')
  })
  await check('filtered CSV export contains only matching rows', async () => {
    await go('?view=ledger&month=2026-10&q='+encodeURIComponent('队服'),'.ledger-table')
    await evaluate('() => {window.__createURL=URL.createObjectURL; URL.createObjectURL=blob=>{window.__exportBlob=blob; return window.__createURL(blob)}; return true}')
    await click('button','导出')
    const csv=await evaluate('async ()=>await window.__exportBlob.text()')
    if(csv.trim().split('\r\n').length!==2 || !csv.includes('队服') || !csv.includes('75'))throw new Error('Filtered CSV mismatch')
    await evaluate('()=>{URL.createObjectURL=window.__createURL;return true}')
  })
  await check('offline failure offers retry and recovers', async () => {
    await go()
    try {
      await tool('emulate',{networkConditions:'Offline',viewport:'1440x1000x1'})
      await click('button','刷新账本');await ready('.empty-state[role=alert]')
      if(!(await snapshot()).includes('无法连接账本服务'))throw new Error('Missing useful connection error')
    } finally { await tool('emulate',{viewport:'1440x1000x1'}) }
    await click('button','重新加载');await ready('.money-summary')
  })
  await check('dialog keyboard focus stays inside and returns', async () => {
    await go();await click('button','设置预算');await ready('[role=dialog]')
    for(let i=0;i<6;i++) {
      await tool('press_key',{key:'Tab'})
      if(!await evaluate('()=>Boolean(document.activeElement.closest("[role=dialog]"))'))throw new Error('Focus escaped dialog')
    }
    await tool('press_key',{key:'Escape'});await ready('.money-summary')
  })
  await check('mobile bottom navigation opens actual ledger', async () => {
    await tool('emulate',{viewport:'390x844x1,mobile,touch'});await go();await click('link','账单明细');await ready('.ledger-table')
    if(!await evaluate('()=>document.querySelector(".mobile-nav a[aria-current=page]").textContent.includes("账单明细")'))throw new Error('Wrong active destination')
  })
  await fs.writeFile(path.join(output, 'browser-results.json'), JSON.stringify({ at: new Date().toISOString(), base, driver: 'Chrome DevTools MCP', checks: records.length, failed: records.filter(r => !r.pass).length, records }, null, 2))
  console.log(JSON.stringify({ checks: records.length, failed: records.filter(r => !r.pass).length }))
  return records
}
