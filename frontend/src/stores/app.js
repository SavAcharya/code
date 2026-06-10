import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api'

export const useAppStore = defineStore('app', () => {
  const applications = ref([])
  const modelStatus = ref({ qwen: { healthy: false }, gemma: { healthy: false }, gemini: { healthy: false, enabled: false } })
  const loading = ref(false)

  const appCount = computed(() => applications.value.length)
  const statusCounts = computed(() => {
    const c = {}
    applications.value.forEach(a => { c[a.status] = (c[a.status] || 0) + 1 })
    return c
  })

  async function loadStatus() {
    try { modelStatus.value = await api.status() } catch {}
  }

  async function loadApplications() {
    applications.value = await api.tracker.list()
  }

  async function createApplication(data) {
    const app = await api.tracker.create(data)
    applications.value.unshift(app)
    return app
  }

  async function updateApplication(id, data) {
    const updated = await api.tracker.update(id, data)
    const idx = applications.value.findIndex(a => a.id === id)
    if (idx !== -1) applications.value[idx] = updated
  }

  async function removeApplication(id) {
    await api.tracker.remove(id)
    applications.value = applications.value.filter(a => a.id !== id)
  }

  async function exportCsv() {
    const res = await api.tracker.exportCsv()
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'job_tracker.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return { applications, modelStatus, loading, appCount, statusCounts,
    loadStatus, loadApplications, createApplication, updateApplication, removeApplication, exportCsv }
})
