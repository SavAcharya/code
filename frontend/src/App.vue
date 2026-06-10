<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <h1><i class="ti ti-briefcase" style="margin-right:6px"/>Job Search OS</h1>
        <p>v2 · LLM-as-Judge</p>
      </div>
      <nav>
        <RouterLink to="/discover" class="nav-item"><i class="ti ti-bulb"/><span>Discover</span></RouterLink>
        <RouterLink to="/matcher" class="nav-item"><i class="ti ti-git-compare"/><span>JD Matcher</span></RouterLink>
        <RouterLink to="/profile" class="nav-item"><i class="ti ti-user"/><span>Profile</span></RouterLink>
        <RouterLink to="/tracker" class="nav-item">
          <i class="ti ti-table"/><span>Tracker</span>
          <span v-if="store.appCount" style="margin-left:auto;font-size:10px;background:var(--info-bg);color:var(--info);padding:1px 6px;border-radius:10px;font-weight:600;">{{ store.appCount }}</span>
        </RouterLink>
        <RouterLink to="/cover" class="nav-item"><i class="ti ti-file-text"/><span>Cover Letter</span></RouterLink>
      </nav>
      <div class="model-status">
        <div class="model-badge">
          <span :class="['dot', store.modelStatus.qwen?.healthy ? 'ok' : 'err']"/>
          <span style="font-family:var(--mono);">qwen3.6</span>
          <span style="opacity:0.6">:11434</span>
        </div>
        <div class="model-badge">
          <span :class="['dot', store.modelStatus.gemma?.healthy ? 'ok' : 'err']"/>
          <span style="font-family:var(--mono);">gemma4</span>
          <span style="opacity:0.6">:11435</span>
        </div>
        <div class="model-badge">
          <span :class="['dot', store.modelStatus.gemini?.enabled && store.modelStatus.gemini?.healthy ? 'ok' : 'err']"/>
          <span>Gemini judge</span>
          <span v-if="!store.modelStatus.gemini?.enabled" style="opacity:0.6">no key</span>
        </div>
      </div>
    </aside>
    <main class="main"><RouterView/></main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAppStore } from './stores/app'
const store = useAppStore()
onMounted(async () => {
  await store.loadStatus()
  await store.loadApplications()
})
</script>
