import JSZip from 'jszip'

export const IMAGE_TYPES = {
  jpg: { mime: 'image/jpeg', extension: 'jpg' },
  jpeg: { mime: 'image/jpeg', extension: 'jpg' },
  png: { mime: 'image/png', extension: 'png' },
  webp: { mime: 'image/webp', extension: 'webp' },
}

const MIME_EXTENSIONS = {
  'image/jpeg': ['jpg', 'jpeg'],
  'image/pjpeg': ['jpg', 'jpeg'],
  'image/png': ['png'],
  'image/webp': ['webp'],
}

export function getInputImageType(file) {
  const extension = file.name.split('.').pop()?.toLowerCase()
  const imageType = IMAGE_TYPES[extension]
  if (!imageType) {
    throw new Error('Choose a JPG, JPEG, PNG, or WebP image.')
  }

  if (file.type && !MIME_EXTENSIONS[file.type]?.includes(extension)) {
    throw new Error('The image file extension does not match its MIME type.')
  }

  return { ...imageType, extension }
}

export async function readHeaderDimensions(file) {
  const { extension } = getInputImageType(file)
  const bytes = new Uint8Array(await file.slice(0, Math.min(file.size, 4 * 1024 * 1024)).arrayBuffer())
  const readU16BE = (offset) => (bytes[offset] << 8) | bytes[offset + 1]
  const readU32BE = (offset) => (
    bytes[offset] * 0x1000000
    + (bytes[offset + 1] << 16)
    + (bytes[offset + 2] << 8)
    + bytes[offset + 3]
  )

  if (extension === 'png') {
    const signature = [137, 80, 78, 71, 13, 10, 26, 10]
    if (signature.some((value, index) => bytes[index] !== value) || bytes.length < 24) return null
    return { width: readU32BE(16), height: readU32BE(20) }
  }

  if (extension === 'jpg' || extension === 'jpeg') {
    if (bytes[0] !== 0xff || bytes[1] !== 0xd8) return null
    const startOfFrame = new Set([0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf])
    let offset = 2
    while (offset + 3 < bytes.length) {
      if (bytes[offset] !== 0xff) {
        offset += 1
        continue
      }
      while (bytes[offset] === 0xff) offset += 1
      const marker = bytes[offset]
      offset += 1
      if (marker === 0xda || marker === 0xd9) break
      if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) continue
      const segmentLength = readU16BE(offset)
      if (segmentLength < 2 || offset + segmentLength > bytes.length) break
      if (startOfFrame.has(marker) && segmentLength >= 7) {
        return { width: readU16BE(offset + 5), height: readU16BE(offset + 3) }
      }
      offset += segmentLength
    }
    return null
  }

  if (bytes.length < 30
    || bytes[0] !== 0x52 || bytes[1] !== 0x49 || bytes[2] !== 0x46 || bytes[3] !== 0x46
    || bytes[8] !== 0x57 || bytes[9] !== 0x45 || bytes[10] !== 0x42 || bytes[11] !== 0x50) {
    return null
  }
  let offset = 12
  while (offset + 8 <= bytes.length) {
    const chunkSize = bytes[offset + 4] | (bytes[offset + 5] << 8) | (bytes[offset + 6] << 16) | (bytes[offset + 7] << 24)
    const payload = offset + 8
    if (bytes[offset] === 0x56 && bytes[offset + 1] === 0x50 && bytes[offset + 2] === 0x38 && bytes[offset + 3] === 0x58) {
      return {
        width: 1 + bytes[payload + 4] + (bytes[payload + 5] << 8) + (bytes[payload + 6] << 16),
        height: 1 + bytes[payload + 7] + (bytes[payload + 8] << 8) + (bytes[payload + 9] << 16),
      }
    }
    if (bytes[offset] === 0x56 && bytes[offset + 1] === 0x50 && bytes[offset + 2] === 0x38 && bytes[offset + 3] === 0x4c
      && bytes[payload] === 0x2f) {
      return {
        width: 1 + bytes[payload + 1] + ((bytes[payload + 2] & 0x3f) << 8),
        height: 1 + ((bytes[payload + 2] & 0xc0) >> 6) + (bytes[payload + 3] << 2) + ((bytes[payload + 4] & 0x0f) << 10),
      }
    }
    if (bytes[offset] === 0x56 && bytes[offset + 1] === 0x50 && bytes[offset + 2] === 0x38 && bytes[offset + 3] === 0x20
      && bytes[payload + 3] === 0x9d && bytes[payload + 4] === 0x01 && bytes[payload + 5] === 0x2a) {
      return {
        width: (bytes[payload + 6] | (bytes[payload + 7] << 8)) & 0x3fff,
        height: (bytes[payload + 8] | (bytes[payload + 9] << 8)) & 0x3fff,
      }
    }
    if (chunkSize <= 0) break
    offset = payload + chunkSize + (chunkSize % 2)
  }
  return null
}

export function validateCompressionSettings(settings) {
  const quality = Number(settings.quality)
  if (!Number.isInteger(quality) || quality < 10 || quality > 100) {
    return 'Quality must be a whole number from 10% to 100%.'
  }

  const resizePercentage = Number(settings.resizePercentage)
  if (!Number.isFinite(resizePercentage) || resizePercentage <= 0 || resizePercentage > 500) {
    return 'Resize percentage must be greater than 0% and no more than 500%.'
  }

  for (const [label, value] of [['Maximum width', settings.maxWidth], ['Maximum height', settings.maxHeight]]) {
    if (value !== '' && (!Number.isInteger(Number(value)) || Number(value) < 1)) {
      return `${label} must be a positive whole number or left blank.`
    }
  }

  return ''
}

export function computeOutputDimensions(width, height, settings) {
  if (settings.keepDimensions) return { width, height }

  const percentScale = Number(settings.resizePercentage) / 100
  const maxWidth = settings.maxWidth === '' ? Infinity : Number(settings.maxWidth)
  const maxHeight = settings.maxHeight === '' ? Infinity : Number(settings.maxHeight)
  let outputWidth
  let outputHeight

  if (settings.maintainAspectRatio) {
    const scale = Math.min(percentScale, maxWidth / width, maxHeight / height)
    outputWidth = Math.round(width * scale)
    outputHeight = Math.round(height * scale)
  } else {
    outputWidth = Math.min(Math.round(width * percentScale), maxWidth)
    outputHeight = Math.min(Math.round(height * percentScale), maxHeight)
  }

  return {
    width: Math.max(1, outputWidth),
    height: Math.max(1, outputHeight),
  }
}

export function getCompressionSavings(originalSize, compressedSize) {
  const percentage = originalSize > 0
    ? ((originalSize - compressedSize) / originalSize) * 100
    : 0
  return {
    percentage,
    larger: compressedSize > originalSize,
  }
}

export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let size = bytes / 1024
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

export async function createImageZip(items, onProgress = () => {}) {
  const zip = new JSZip()
  items.forEach((item) => zip.file(item.outputName, item.resultBlob))
  return zip.generateAsync({ type: 'blob' }, (metadata) => onProgress(Math.round(metadata.percent)))
}

export function outputTypeDetails(requestedFormat, inputType) {
  if (requestedFormat === 'original') {
    const match = Object.values(IMAGE_TYPES).find((type) => type.mime === inputType)
    if (!match) throw new Error('The source image format is not supported.')
    return match
  }

  const match = Object.values(IMAGE_TYPES).find((type) => type.mime === requestedFormat)
  if (!match) throw new Error('Choose a supported output format.')
  return match
}
