import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const component = name => readFile(new URL(`../src/components/${name}.jsx`, import.meta.url), 'utf8')

for (const [name, marker] of [
  ['StatePanel', 'Account state'], ['TradeJournal', 'Trade journal'],
  ['SpecialistPanel', 'Specialists'], ['EvidenceViewer', 'Evidence'],
  ['SetupWizard', 'Setup wizard'], ['Alerts', 'Alerts'],
]) test(`${name} exposes its accessible panel heading`, async () => assert.match(await component(name), new RegExp(marker)))

for (const name of ['PositionTable', 'ConsensusCard', 'LoadingState', 'EmptyState', 'ErrorState']) {
  test(`${name} component exists and exports a view`, async () => assert.match(await component(name), /export default function/))
}

test('specialist panel remains display-only', async () => assert.match(await component('SpecialistPanel'), /does not approve or execute/))
test('setup wizard warns that broker credentials are not stored', async () => assert.match(await component('SetupWizard'), /never displayed or stored/))
test('application renders all six dashboard foundations', async () => {
  const source = await readFile(new URL('../src/App.jsx', import.meta.url), 'utf8')
  for (const name of ['StatePanel', 'TradeJournal', 'SpecialistPanel', 'EvidenceViewer', 'SetupWizard', 'Alerts']) assert.match(source, new RegExp(`<${name}`))
  assert.match(source, /<LoadingState/); assert.match(source, /<ErrorState/)
})
test('position table is wired into account state', async () => assert.match(await component('StatePanel'), /<PositionTable/))
test('consensus card is wired into specialist view', async () => assert.match(await component('SpecialistPanel'), /<ConsensusCard/))
test('responsive styling includes tablet and mobile boundaries', async () => {
  const css = await readFile(new URL('../src/App.css', import.meta.url), 'utf8')
  assert.match(css, /max-width:900px/); assert.match(css, /max-width:600px/)
})
