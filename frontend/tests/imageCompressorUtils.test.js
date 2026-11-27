import test from 'node:test'
import assert from 'node:assert/strict'
import {
  computeOutputDimensions,
  createImageZip,
  formatFileSize,
  getCompressionSavings,
  getInputImageType,
  readHeaderDimensions,
  validateCompressionSettings,
} from '../src/imageCompressorUtils.js'
import JSZip from 'jszip'

test('validates image extension and MIME type together', () => {
  assert.equal(getInputImageType({ name: 'photo.JPEG', type: 'image/jpeg' }).mime, 'image/jpeg')
  assert.throws(
    () => getInputImageType({ name: 'photo.png', type: 'image/jpeg' }),
    /does not match/,
  )
  assert.throws(() => getInputImageType({ name: 'notes.gif', type: 'image/gif' }), /Choose a JPG/)
})

test('validates compression controls and accepts blank maximum dimensions', () => {
  const settings = {
    quality: 75,
    resizePercentage: 100,
    maxWidth: '',
    maxHeight: '',
  }
  assert.equal(validateCompressionSettings(settings), '')
  assert.match(validateCompressionSettings({ ...settings, quality: 9 }), /10% to 100%/)
  assert.match(validateCompressionSettings({ ...settings, maxWidth: '0' }), /Maximum width/)
})

test('resizes proportionally to fit both maximum bounds', () => {
  assert.deepEqual(
    computeOutputDimensions(4000, 2000, {
      keepDimensions: false,
      maintainAspectRatio: true,
      resizePercentage: 100,
      maxWidth: '1600',
      maxHeight: '1000',
    }),
    { width: 1600, height: 800 },
  )
})

test('supports explicit dimensions and retains source dimensions when requested', () => {
  assert.deepEqual(
    computeOutputDimensions(1600, 900, {
      keepDimensions: false,
      maintainAspectRatio: false,
      resizePercentage: 50,
      maxWidth: '700',
      maxHeight: '600',
    }),
    { width: 700, height: 450 },
  )
  assert.deepEqual(
    computeOutputDimensions(1600, 900, { keepDimensions: true }),
    { width: 1600, height: 900 },
  )
})

test('reports real savings, including outputs that got larger', () => {
  assert.deepEqual(getCompressionSavings(200, 150), { percentage: 25, larger: false })
  assert.deepEqual(getCompressionSavings(100, 125), { percentage: -25, larger: true })
  assert.equal(formatFileSize(0), '0 B')
})

test('reads image dimensions from the PNG header before decoding', async () => {
  const header = new Uint8Array(24)
  header.set([137, 80, 78, 71, 13, 10, 26, 10], 0)
  header.set([73, 72, 68, 82], 12)
  header.set([0, 0, 3, 232], 16)
  header.set([0, 0, 1, 244], 20)
  const file = new Blob([header], { type: 'image/png' })
  Object.defineProperty(file, 'name', { value: 'dimensions.png' })
  assert.deepEqual(await readHeaderDimensions(file), { width: 1000, height: 500 })
})

test('reads large JPEG dimensions before image decoding', async () => {
  const bytes = new Uint8Array([
    0xff, 0xd8,
    0xff, 0xe0, 0x00, 0x04, 0x00, 0x00,
    0xff, 0xc0, 0x00, 0x07, 0x08, 0x17, 0x70, 0x1b, 0x58,
    0xff, 0xd9,
  ])
  const file = new Blob([bytes], { type: 'image/jpeg' })
  Object.defineProperty(file, 'name', { value: 'large.jpg' })
  assert.deepEqual(await readHeaderDimensions(file), { width: 7000, height: 6000 })
})

test('reads WebP extended-header dimensions', async () => {
  const bytes = new Uint8Array(30)
  bytes.set([0x52, 0x49, 0x46, 0x46, 22, 0, 0, 0, 0x57, 0x45, 0x42, 0x50], 0)
  bytes.set([0x56, 0x50, 0x38, 0x58, 10, 0, 0, 0], 12)
  bytes.set([0, 0, 0, 0, 0xff, 0x04, 0, 0xcf, 0x02, 0], 20)
  const file = new Blob([bytes], { type: 'image/webp' })
  Object.defineProperty(file, 'name', { value: 'large.webp' })
  assert.deepEqual(await readHeaderDimensions(file), { width: 1280, height: 720 })
})

test('creates a ZIP containing each successful image result', async () => {
  const zipBlob = await createImageZip([
    { outputName: 'one.jpg', resultBlob: new Blob(['jpeg data'], { type: 'image/jpeg' }) },
    { outputName: 'two.webp', resultBlob: new Blob(['webp data'], { type: 'image/webp' }) },
  ])
  const archive = await JSZip.loadAsync(zipBlob)
  assert.deepEqual(Object.keys(archive.files).sort(), ['one.jpg', 'two.webp'])
  assert.equal(await archive.file('one.jpg').async('string'), 'jpeg data')
})
