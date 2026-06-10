<template>
  <div class="gauge-wrap">
    <div class="gauge" :style="{ background: colors.bg }">
      <svg width="96" height="96" style="position:absolute;top:0;left:0;transform:rotate(-90deg)">
        <circle cx="48" cy="48" r="38" fill="none" stroke="rgba(0,0,0,0.07)" stroke-width="8"/>
        <circle cx="48" cy="48" r="38" fill="none" :stroke="colors.text" stroke-width="8"
          :stroke-dasharray="`${fill} ${circ}`" stroke-linecap="round"/>
      </svg>
      <div class="gauge-inner">
        <div class="gauge-num" :style="{ color: colors.text }">{{ score }}</div>
        <div class="gauge-denom" :style="{ color: colors.text }">/100</div>
      </div>
    </div>
    <div class="gauge-label" :style="{ color: colors.text }">{{ label }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ score: { type: Number, default: 0 } })
const R = 38, circ = 2 * Math.PI * R
const fill = computed(() => (props.score / 100) * circ)
const colors = computed(() => {
  if (props.score >= 75) return { bg: 'var(--success-bg)', text: 'var(--success)' }
  if (props.score >= 50) return { bg: 'var(--warn-bg)', text: 'var(--warn)' }
  return { bg: 'var(--danger-bg)', text: 'var(--danger)' }
})
const label = computed(() => {
  if (props.score >= 75) return 'Strong match'
  if (props.score >= 50) return 'Partial match'
  return 'Weak match'
})
</script>

<style scoped>
.gauge-wrap { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.gauge { position: relative; width: 96px; height: 96px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.gauge-inner { text-align: center; }
.gauge-num { font-size: 22px; font-weight: 600; line-height: 1; }
.gauge-denom { font-size: 10px; opacity: 0.75; }
.gauge-label { font-size: 12px; font-weight: 500; }
</style>
