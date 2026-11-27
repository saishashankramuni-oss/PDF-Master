import React, { useEffect, useRef, useState } from 'react'
import { ArrowLeft, Download, FileImage, ImagePlus, Loader2, Trash2, Upload } from 'lucide-react'
import {
  computeOutputDimensions,
  createImageZip,
  formatFileSize,
  getCompressionSavings,
  getInputImageType,
  outputTypeDetails,
  readHeaderDimensions,
  validateCompressionSettings,
} from '../imageCompressorUtils'

const MAX_FILE_SIZE = 100 * 1024 * 1024
const MAX_IMAGE_PIXELS = 40_000_000
const INITIAL_SETTINGS = {
  quality: 75,
  maxWidth: '2000',
  maxHeight: '2000',
  resizePercentage: '100',
  maintainAspectRatio: true,
  keepDimensions: true,
  outputFormat: 'original',
}

function createId() {
  return globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`
}

async function decodeImage(file) {
  if (typeof globalThis.createImageBitmap === 'function') {
    const bitmap = await globalThis.createImageBitmap(file)
    return {
      width: bitmap.width,
      height: bitmap.height,
      draw: (context, width, height) => context.drawImage(bitmap, 0, 0, width, height),
      close: () => bitmap.close(),
    }
  }

  const url = URL.createObjectURL(file)
  const image = new window.Image()
  image.src = url
  try {
    await image.decode()
    return {
      width: image.naturalWidth,
      height: image.naturalHeight,
      draw: (context, width, height) => context.drawImage(image, 0, 0, width, height),
      close: () => URL.revokeObjectURL(url),
    }
  } catch (error) {
    URL.revokeObjectURL(url)
    throw error
  }
}

function encodeCanvas(canvas, mime, quality) {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('Your browser could not encode this image. Try a different output format.'))
      } else if (blob.type !== mime) {
        reject(new Error(`This browser cannot encode ${mime.replace('image/', '').toUpperCase()} images.`))
      } else {
        resolve(blob)
      }
    }, mime, quality)
  })
}

function makeOutputName(file, extension, usedNames) {
  const stem = file.name.replace(/\.[^.]+$/, '') || 'image'
  let name = `${stem}-compressed.${extension}`
  let suffix = 2
  while (usedNames.has(name.toLowerCase())) {
    name = `${stem}-compressed-${suffix}.${extension}`
    suffix += 1
  }
  usedNames.add(name.toLowerCase())
  return name
}

function triggerDownload(url, filename) {
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.rel = 'noopener'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
}

export default function ImageCompressor({ onBack }) {
  const [images, setImages] = useState([])
  const [settings, setSettings] = useState(INITIAL_SETTINGS)
  const [isDragging, setIsDragging] = useState(false)
  const [isAddingFiles, setIsAddingFiles] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState({ done: 0, total: 0 })
  const [zipProgress, setZipProgress] = useState(null)
  const [zipUrl, setZipUrl] = useState('')
  const [confirmFlattening, setConfirmFlattening] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)
  const imagesRef = useRef(images)
  const zipUrlRef = useRef(zipUrl)
  imagesRef.current = images
  zipUrlRef.current = zipUrl

  useEffect(() => () => {
    const urls = new Set()
    imagesRef.current.forEach((item) => {
      if (item.previewUrl) urls.add(item.previewUrl)
      if (item.resultUrl && item.resultUrl !== item.previewUrl) urls.add(item.resultUrl)
    })
    if (zipUrlRef.current) urls.add(zipUrlRef.current)
    urls.forEach((url) => URL.revokeObjectURL(url))
  }, [])

  const jpegWarningRequired = settings.outputFormat === 'image/jpeg'
    && images.some((item) => item.mime === 'image/png' || item.mime === 'image/webp')
  const canProcess = (item) => item.width && item.height
    && !['error', 'validating', 'processing'].includes(item.status)
  const readyCount = images.filter(canProcess).length
  const downloadCount = images.filter((item) => item.resultBlob).length
  const validatedSettingsError = validateCompressionSettings(settings)

  function updateImage(id, changes) {
    setImages((current) => current.map((item) => item.id === id ? { ...item, ...changes } : item))
  }

  async function addFiles(fileList) {
    const candidates = Array.from(fileList || [])
    if (!candidates.length) return

    setError('')
    setIsAddingFiles(true)
    const seen = new Set(images.map((item) => `${item.file.name}:${item.file.size}:${item.file.lastModified}`))

    for (const file of candidates) {
      const duplicateKey = `${file.name}:${file.size}:${file.lastModified}`
      if (seen.has(duplicateKey)) continue
      seen.add(duplicateKey)

      const id = createId()
      let fileType
      try {
        fileType = getInputImageType(file)
        if (file.size === 0) throw new Error('This image file is empty.')
        if (file.size > MAX_FILE_SIZE) {
          throw new Error(`Image is larger than the ${formatFileSize(MAX_FILE_SIZE)} browser limit.`)
        }
      } catch (validationError) {
        setImages((current) => [...current, {
          id,
          file,
          status: 'error',
          error: validationError.message,
        }])
        continue
      }

      const item = { id, file, ...fileType, status: 'validating' }
      setImages((current) => [...current, item])

      try {
        const headerDimensions = await readHeaderDimensions(file)
        if (headerDimensions && headerDimensions.width * headerDimensions.height > MAX_IMAGE_PIXELS) {
          throw new Error(`Image dimensions are too large to process safely (maximum ${MAX_IMAGE_PIXELS.toLocaleString()} pixels).`)
        }
        let decoded
        try {
          decoded = await decodeImage(file)
        } catch {
          throw new Error('This file could not be decoded as a supported image.')
        }
        const { width, height } = decoded
        decoded.close()
        if (!width || !height) throw new Error('The image has invalid dimensions.')
        if (width * height > MAX_IMAGE_PIXELS) {
          throw new Error(`Image dimensions are too large to process safely (maximum ${MAX_IMAGE_PIXELS.toLocaleString()} pixels).`)
        }

        updateImage(id, {
          width,
          height,
          previewUrl: URL.createObjectURL(file),
          status: 'ready',
        })
      } catch (validationError) {
        updateImage(id, {
          status: 'error',
          error: validationError.message || 'Image validation failed.',
        })
      }
    }

    setIsAddingFiles(false)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function removeImage(item) {
    if (isProcessing) return
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl)
    if (item.resultUrl && item.resultUrl !== item.previewUrl) URL.revokeObjectURL(item.resultUrl)
    setImages((current) => current.filter((entry) => entry.id !== item.id))
  }

  function updateSetting(name, value) {
    setSettings((current) => ({ ...current, [name]: value }))
    setError('')
  }

  async function compressImages() {
    if (isProcessing) return
    if (validatedSettingsError) {
      setError(validatedSettingsError)
      return
    }
    if (!images.some(canProcess)) {
      setError('Add at least one valid image before compressing.')
      return
    }
    if (jpegWarningRequired && !confirmFlattening) {
      setError('Confirm that transparent PNG/WebP areas may be flattened onto white before converting to JPEG.')
      return
    }

    const queue = images.filter(canProcess)
    const usedNames = new Set()
    queue.forEach((item) => {
      const details = outputTypeDetails(settings.outputFormat, item.mime)
      item.outputName = makeOutputName(item.file, details.extension, usedNames)
      if (item.resultUrl && item.resultUrl !== item.previewUrl) URL.revokeObjectURL(item.resultUrl)
    })
    setImages((current) => current.map((item) => queue.some((queued) => queued.id === item.id)
      ? { ...item, status: 'processing', error: '', resultBlob: null, resultUrl: null }
      : item))
    setError('')
    setIsProcessing(true)
    setProgress({ done: 0, total: queue.length })

    for (let index = 0; index < queue.length; index += 1) {
      const item = queue[index]
      try {
        const outputType = outputTypeDetails(settings.outputFormat, item.mime)
        const decoded = await decodeImage(item.file)
        let canvas
        let blob
        try {
          const dimensions = computeOutputDimensions(item.width, item.height, settings)
          if (dimensions.width * dimensions.height > MAX_IMAGE_PIXELS) {
            throw new Error(`Requested output dimensions exceed the ${MAX_IMAGE_PIXELS.toLocaleString()} pixel safety limit.`)
          }
          canvas = document.createElement('canvas')
          canvas.width = dimensions.width
          canvas.height = dimensions.height
          const context = canvas.getContext('2d', { alpha: outputType.mime !== 'image/jpeg' })
          if (!context) throw new Error('Your browser could not create an image processing canvas.')
          context.imageSmoothingEnabled = true
          context.imageSmoothingQuality = 'high'
          if (outputType.mime === 'image/jpeg') {
            context.fillStyle = '#ffffff'
            context.fillRect(0, 0, canvas.width, canvas.height)
          }
          decoded.draw(context, canvas.width, canvas.height)
          blob = await encodeCanvas(canvas, outputType.mime, Number(settings.quality) / 100)
        } finally {
          if (canvas) {
            canvas.width = 0
            canvas.height = 0
          }
          decoded.close()
        }

        const dimensions = computeOutputDimensions(item.width, item.height, settings)
        const resultUrl = URL.createObjectURL(blob)
        updateImage(item.id, {
          status: blob.size > item.file.size ? 'larger' : 'complete',
          resultBlob: blob,
          resultUrl,
          outputName: item.outputName,
          outputWidth: dimensions.width,
          outputHeight: dimensions.height,
          outputSize: blob.size,
          outputMime: outputType.mime,
          savings: getCompressionSavings(item.file.size, blob.size),
        })
      } catch (processingError) {
        updateImage(item.id, {
          status: 'error',
          error: processingError.message || 'Image compression failed.',
        })
      }
      setProgress({ done: index + 1, total: queue.length })
      await new Promise((resolve) => window.setTimeout(resolve, 0))
    }

    setIsProcessing(false)
  }

  function keepOriginal(item) {
    if (item.resultUrl && item.resultUrl !== item.previewUrl) URL.revokeObjectURL(item.resultUrl)
    updateImage(item.id, {
      status: 'kept-original',
      resultBlob: item.file,
      resultUrl: item.previewUrl,
      outputName: item.file.name.replace(/\.[^.]+$/, '') + `-original.${item.extension}`,
      outputWidth: item.width,
      outputHeight: item.height,
      outputSize: item.file.size,
      outputMime: item.mime,
      savings: getCompressionSavings(item.file.size, item.file.size),
    })
  }

  async function downloadAll() {
    if (zipProgress !== null) return
    const completed = images.filter((item) => item.resultBlob)
    if (!completed.length) return

    try {
      setZipProgress(0)
      const blob = await createImageZip(completed, setZipProgress)
      const url = URL.createObjectURL(blob)
      if (zipUrlRef.current) URL.revokeObjectURL(zipUrlRef.current)
      zipUrlRef.current = url
      setZipUrl(url)
      triggerDownload(url, 'compressed-images.zip')
    } catch (downloadError) {
      setError(`Could not create the ZIP download: ${downloadError.message}`)
    } finally {
      setZipProgress(null)
    }
  }

  function onDrop(event) {
    event.preventDefault()
    setIsDragging(false)
    addFiles(event.dataTransfer.files)
  }

  const progressPercent = progress.total ? Math.round((progress.done / progress.total) * 100) : 0

  return (
    <section className="mx-auto max-w-6xl">
      <button
        type="button"
        onClick={onBack}
        disabled={isProcessing}
        className="mb-5 inline-flex items-center gap-2 text-sm font-medium text-blue-700 hover:underline disabled:opacity-50 dark:text-blue-400"
      >
        <ArrowLeft className="h-4 w-4" />
        All tools
      </button>
      <div className="mb-7 flex items-start gap-3">
        <div className="rounded-xl bg-blue-100 p-3 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
          <FileImage className="h-7 w-7" />
        </div>
        <div>
          <h1 className="text-3xl font-bold md:text-4xl">Image Compressor</h1>
          <p className="mt-2 text-slate-600 dark:text-slate-300">
            Compress JPG, PNG, and WebP images privately in your browser.
          </p>
        </div>
      </div>

      <div
        onDragOver={(event) => { event.preventDefault(); setIsDragging(true) }}
        onDragLeave={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) setIsDragging(false)
        }}
        onDrop={onDrop}
        className={`rounded-2xl border-2 border-dashed p-7 text-center transition ${
          isDragging
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/40'
            : 'border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900'
        }`}
      >
        <ImagePlus className="mx-auto h-10 w-10 text-blue-600" />
        <h2 className="mt-3 text-lg font-semibold">Drop images here</h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">JPG, JPEG, PNG, and WebP · up to {formatFileSize(MAX_FILE_SIZE)} each</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
          multiple
          className="sr-only"
          onChange={(event) => addFiles(event.target.files)}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isAddingFiles || isProcessing}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isAddingFiles ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
          Browse Images
        </button>
        <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">Files are decoded and compressed locally; image contents are not uploaded.</p>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-4">
          {images.length === 0 ? (
            <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
              Your selected images will appear here.
            </div>
          ) : images.map((item) => (
            <ImageResult
              key={item.id}
              item={item}
              onRemove={() => removeImage(item)}
              onKeepOriginal={() => keepOriginal(item)}
              disabled={isProcessing}
            />
          ))}
        </div>

        <aside className="h-fit rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-lg font-semibold">Compression settings</h2>

          <label className="mt-5 block text-sm font-medium">
            Quality <span className="text-blue-700 dark:text-blue-300">{settings.quality}%</span>
            <input
              type="range"
              min="10"
              max="100"
              step="1"
              value={settings.quality}
              onChange={(event) => updateSetting('quality', Number(event.target.value))}
              className="mt-2 w-full accent-blue-600"
            />
          </label>

          <label className="mt-5 block text-sm font-medium">
            Output format
            <select
              value={settings.outputFormat}
              onChange={(event) => { updateSetting('outputFormat', event.target.value); setConfirmFlattening(false) }}
              className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-800"
            >
              <option value="original">Keep each original format</option>
              <option value="image/jpeg">JPEG</option>
              <option value="image/webp">WebP</option>
              <option value="image/png">PNG</option>
            </select>
          </label>

          <fieldset disabled={settings.keepDimensions} className="mt-5 space-y-3 disabled:opacity-50">
            <legend className="mb-2 text-sm font-medium">Resize</legend>
            <label className="block text-xs text-slate-600 dark:text-slate-300">
              Resize percentage
              <input
                type="number"
                min="1"
                max="500"
                step="1"
                value={settings.resizePercentage}
                onChange={(event) => updateSetting('resizePercentage', event.target.value)}
                className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800"
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block text-xs text-slate-600 dark:text-slate-300">
                Maximum width
                <input
                  type="number"
                  min="1"
                  value={settings.maxWidth}
                  onChange={(event) => updateSetting('maxWidth', event.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800"
                />
              </label>
              <label className="block text-xs text-slate-600 dark:text-slate-300">
                Maximum height
                <input
                  type="number"
                  min="1"
                  value={settings.maxHeight}
                  onChange={(event) => updateSetting('maxHeight', event.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800"
                />
              </label>
            </div>
          </fieldset>

          <label className="mt-5 flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={settings.maintainAspectRatio}
              disabled={settings.keepDimensions}
              onChange={(event) => updateSetting('maintainAspectRatio', event.target.checked)}
              className="mt-1 accent-blue-600"
            />
            Maintain aspect ratio
          </label>
          <label className="mt-3 flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              checked={settings.keepDimensions}
              onChange={(event) => updateSetting('keepDimensions', event.target.checked)}
              className="mt-1 accent-blue-600"
            />
            Retain original dimensions
          </label>

          {settings.outputFormat === 'image/png' && (
            <p className="mt-3 rounded-lg bg-amber-50 p-3 text-xs text-amber-900 dark:bg-amber-950 dark:text-amber-200">
              PNG is re-encoded losslessly; the quality slider does not apply, and the result may be larger.
            </p>
          )}
          {jpegWarningRequired && (
            <label className="mt-3 block rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs text-amber-950 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-100">
              PNG/WebP images can contain transparency. JPEG does not support it, so transparent areas will become white.
              <span className="mt-2 flex items-start gap-2 font-medium">
                <input
                  type="checkbox"
                  checked={confirmFlattening}
                  onChange={(event) => setConfirmFlattening(event.target.checked)}
                  className="mt-0.5 accent-amber-700"
                />
                I understand; flatten transparent areas to white.
              </span>
            </label>
          )}

          {validatedSettingsError && <p className="mt-3 text-xs text-red-700">{validatedSettingsError}</p>}
          {error && <p role="alert" className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-200">{error}</p>}

          {isProcessing && (
            <div className="mt-5" aria-live="polite">
              <div className="mb-1 flex justify-between text-xs text-slate-600 dark:text-slate-300">
                <span>Processing images</span><span>{progress.done}/{progress.total}</span>
              </div>
              <progress className="h-2 w-full accent-blue-600" max="100" value={progressPercent} />
            </div>
          )}
          <button
            type="button"
            onClick={compressImages}
            disabled={isProcessing || isAddingFiles || readyCount === 0 || Boolean(validatedSettingsError) || (jpegWarningRequired && !confirmFlattening)}
            className="mt-5 w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isProcessing ? 'Compressing…' : `Compress ${readyCount ? `${readyCount} image${readyCount === 1 ? '' : 's'}` : 'Images'}`}
          </button>

          {downloadCount > 0 && (
            <button
              type="button"
              onClick={downloadAll}
              disabled={zipProgress !== null}
              className="mt-3 w-full rounded-lg border border-blue-600 px-4 py-2.5 font-semibold text-blue-700 hover:bg-blue-50 disabled:opacity-50 dark:text-blue-300 dark:hover:bg-slate-800"
            >
              {zipProgress === null ? `Download All as ZIP (${downloadCount})` : `Creating ZIP… ${zipProgress}%`}
            </button>
          )}
          <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
            Images over {MAX_IMAGE_PIXELS.toLocaleString()} pixels are rejected before full decode to protect browser memory.
          </p>
          {zipUrl && (
            <a
              href={zipUrl}
              download="compressed-images.zip"
              className="mt-2 block text-center text-sm font-medium text-blue-700 underline dark:text-blue-300"
            >
              If the ZIP did not start, download it here
            </a>
          )}
        </aside>
      </div>
    </section>
  )
}

function ImageResult({ item, onRemove, onKeepOriginal, disabled }) {
  const saving = item.savings
  const outputComplete = Boolean(item.resultBlob)
  const statusText = {
    validating: 'Validating image…',
    ready: 'Ready to compress',
    processing: 'Compressing…',
    complete: 'Compressed',
    larger: 'Result is larger than the original',
    'kept-original': 'Original kept',
    error: 'Could not process',
  }[item.status] || item.status

  return (
    <article className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-4 py-3 dark:border-slate-800">
        <div className="min-w-0">
          <h3 className="truncate font-semibold" title={item.file.name}>{item.file.name}</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">{statusText}</p>
        </div>
        <button
          type="button"
          onClick={onRemove}
          disabled={disabled}
          aria-label={`Remove ${item.file.name}`}
          className="rounded p-1 text-slate-500 hover:bg-slate-100 hover:text-red-600 disabled:opacity-40 dark:hover:bg-slate-800"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      {item.previewUrl && (
        <div className={`grid gap-3 p-4 ${outputComplete ? 'sm:grid-cols-2' : 'grid-cols-1'}`}>
          <figure className="min-w-0">
            <figcaption className="mb-2 text-xs font-medium text-slate-500">Original</figcaption>
            <div className="flex h-40 items-center justify-center overflow-hidden rounded-lg bg-[linear-gradient(45deg,#e2e8f0_25%,transparent_25%,transparent_75%,#e2e8f0_75%),linear-gradient(45deg,#e2e8f0_25%,transparent_25%,transparent_75%,#e2e8f0_75%)] bg-[length:16px_16px] bg-[position:0_0,8px_8px] dark:bg-slate-800">
              <img src={item.previewUrl} alt={`Original ${item.file.name}`} className="max-h-full max-w-full object-contain" />
            </div>
          </figure>
          {outputComplete && (
            <figure className="min-w-0">
              <figcaption className="mb-2 text-xs font-medium text-slate-500">Compressed result</figcaption>
              <div className="flex h-40 items-center justify-center overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-800">
                <img src={item.resultUrl} alt={`Compressed ${item.file.name}`} className="max-h-full max-w-full object-contain" />
              </div>
            </figure>
          )}
        </div>
      )}

      <div className="grid gap-3 px-4 pb-4 text-sm sm:grid-cols-2">
        <p className="text-slate-600 dark:text-slate-300">
          Original: {item.width && item.height ? `${item.width} × ${item.height} · ` : ''}{formatFileSize(item.file.size)}
        </p>
        {outputComplete && (
          <p className="text-slate-600 dark:text-slate-300">
            Result: {item.outputWidth} × {item.outputHeight} · {formatFileSize(item.outputSize)}
          </p>
        )}
        {saving && (
          <p className={`font-medium ${saving.larger ? 'text-amber-700 dark:text-amber-300' : 'text-green-700 dark:text-green-300'}`}>
            {saving.larger
              ? `${Math.abs(saving.percentage).toFixed(1)}% larger than original`
              : `${saving.percentage.toFixed(1)}% saved`}
          </p>
        )}
        {item.error && <p role="alert" className="text-sm text-red-700 dark:text-red-300">{item.error}</p>}
      </div>

      {item.status === 'larger' && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900 dark:bg-amber-950/50">
          <p className="text-sm text-amber-900 dark:text-amber-200">The encoded image is larger. You can use the original instead.</p>
          <button type="button" onClick={onKeepOriginal} disabled={disabled} className="rounded-md border border-amber-700 px-3 py-1.5 text-sm font-medium text-amber-900 dark:text-amber-200">
            Keep original
          </button>
        </div>
      )}
      {outputComplete && (
        <div className="border-t border-slate-100 px-4 py-3 dark:border-slate-800">
          <a
            href={item.resultUrl}
            download={item.outputName}
            className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700"
          >
            <Download className="h-4 w-4" />
            Download {item.status === 'kept-original' ? 'image' : 'compressed'}
          </a>
        </div>
      )}
    </article>
  )
}
