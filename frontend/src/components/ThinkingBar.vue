<template>
  <Transition name="fade">
    <div v-if="visible" class="thinking">
      <i class="ti ti-brain spin" style="font-size:15px;color:var(--info)"/>
      <span>{{ message }}</span>
      <span class="thinking-timer">{{ elapsed }}s</span>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
const props = defineProps({
  visible: Boolean,
  message: { type: String, default: 'Thinking...' }
})
const elapsed = ref(0)
let timer = null

watch(() => props.visible, (v) => {
  if (v) { elapsed.value = 0; timer = setInterval(() => elapsed.value++, 1000) }
  else { clearInterval(timer) }
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
