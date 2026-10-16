/** Real Chrome DevTools MCP client. --serve exposes a loopback-only QA session. */
import { createRequire } from 'node:module'
import { pathToFileURL, fileURLToPath } from 'node:url'
import path from 'node:path'
import fs from 'node:fs/promises'
import http from 'node:http'
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const require = createRequire(path.join(root, 'frontend/package.json'))
const { Client } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/index.js')))
const { StdioClientTransport } = await import(pathToFileURL(require.resolve('@modelcontextprotocol/sdk/client/stdio.js')))
const chromeBin = path.join(root, 'frontend/node_modules/chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js')
const output = path.join(root, process.env.LEDGER_QA_OUTPUT || 'output/qa-v3.2')
if (process.argv.includes('--reduced')) process.env.LEDGER_REDUCED_MOTION = '1'
await fs.mkdir(output, { recursive: true })
const client = new Client({ name: 'ledger-atlas-qa', version: '1.0.0' })
await client.connect(new StdioClientTransport({ command: process.execPath, args: [chromeBin, '--headless', '--isolated', '--no-usage-statistics', '--no-performance-crux', '--viewport=1440x1080', `--workspace=${root}`, ...(process.env.LEDGER_REDUCED_MOTION ? ['--chromeArg=--force-prefers-reduced-motion'] : [])], stderr: 'pipe' }))
const tools = await client.listTools()
await fs.writeFile(path.join(output, 'mcp-tools.json'), JSON.stringify(tools, null, 2))
async function call(name, args = {}) {
  const result = await client.callTool({ name, arguments: args })
  await fs.appendFile(path.join(output, 'devtools-transcript.jsonl'), JSON.stringify({ at: new Date().toISOString(), tool: name, args, result }) + '\n')
  return result
}
if (process.argv.includes('--serve')) {
  http.createServer(async (req, res) => {
    res.setHeader('Content-Type', 'application/json')
    try {
      if (req.url === '/tools') { res.end(JSON.stringify(tools)); return }
      let input = ''; for await (const chunk of req) input += chunk
      const { name, args } = JSON.parse(input)
      res.end(JSON.stringify(await call(name, args)))
    } catch (err) { res.statusCode = 500; res.end(JSON.stringify({ error: err.message })) }
  }).listen(9321, '127.0.0.1', () => console.log('Chrome DevTools MCP QA session: http://127.0.0.1:9321'))
} else {
  try {
    const { audit } = await import(process.argv.includes('--motion-only') ? './motion-checks.mjs' : './browser-checks.mjs')
    const records = await audit(call, root, process.env.LEDGER_QA_URL || 'http://127.0.0.1:8000')
    if(records.some(r => !r.pass)) process.exitCode = 1
  } finally { await client.close() }
}
