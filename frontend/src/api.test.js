import test from 'node:test'
import assert from 'node:assert/strict'
import { createApiUrl } from './api.js'

test('createApiUrl keeps relative routes for development proxying', () => {
  assert.equal(createApiUrl('/api/tools'), '/api/tools')
})

test('createApiUrl joins a configured production API origin and route', () => {
  assert.equal(
    createApiUrl('/api/jobs/123', 'https://api.example.test/'),
    'https://api.example.test/api/jobs/123',
  )
})

test('createApiUrl normalizes routes without a leading slash', () => {
  assert.equal(createApiUrl('health', 'https://api.example.test'), 'https://api.example.test/health')
})
