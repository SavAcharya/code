<template>
  <div v-if="judge" class="judge-panel">
    <div class="judge-header">
      <i class="ti ti-gavel" style="font-size:15px"/>
      <span class="judge-title">Gemini Judge</span>
      <span :class="['verdict-badge', verdictClass]">
        <i :class="['ti', verdictIcon]" style="font-size:12px"/>
        {{ judge.verdict }}
      </span>
      <span class="judge-score">{{ judge.score.toFixed(1) }}/10</span>
      <span class="judge-model">{{ judge.model }}</span>
    </div>

    <p class="judge-feedback">{{ judge.feedback }}</p>

    <div v-if="judge.specific_issues?.length" class="judge-section">
      <div class="section-label">Issues found</div>
      <div v-for="(issue, i) in judge.specific_issues" :key="i" class="issue-row">
        <i class="ti ti-alert-circle" style="font-size:13px;color:var(--warn);flex-shrink:0;margin-top:2px"/>
        <span>{{ issue }}</span>
      </div>
    </div>

    <div v-if="judge.improvement_suggestions?.length" class="judge-section">
      <div class="section-label">Suggestions</div>
      <div v-for="(s, i) in judge.improvement_suggestions" :key="i" class="sugg-row">
        <i class="ti ti-arrow-right" style="font-size:13px;color:var(--info);flex-shrink:0;margin-top:2px"/>
        <span>{{ s }}</span>
      </div>
    </div>

    <div v-if="judge.improved_content" class="judge-improved">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <div class="section-label" style="margin:0">Improved version</div>
        <button class="btn" style="font-size:11px;padding:4px 10px;" @click="$emit('use-improved', judge.improved_content)">
          <i class="ti ti-check" style="font-size:12px"/>Use this
        </button>
      </div>
      <div class="improved-text">{{ judge.improved_content }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ judge: Object })
defineEmits(['use-improved'])

const verdictClass = computed(() => ({
  'verdict-pass': props.judge?.verdict === 'PASS',
  'verdict-challenge': props.judge?.verdict === 'CHALLENGE',
  'verdict-fail': props.judge?.verdict === 'FAIL',
}))
const verdictIcon = computed(() => ({
  PASS: 'ti-circle-check',
  CHALLENGE: 'ti-alert-triangle',
  FAIL: 'ti-circle-x',
})[props.judge?.verdict] || 'ti-question-mark')
</script>

<style scoped>
.judge-panel { background: var(--bg2); border: 0.5px solid var(--border); border-radius: var(--radius-lg); padding: 14px; margin-top: 14px; }
.judge-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.judge-title { font-size: 13px; font-weight: 600; }
.judge-score { font-size: 13px; color: var(--text2); margin-left: 2px; }
.judge-model { font-size: 11px; color: var(--text3); margin-left: auto; font-family: var(--mono); }
.judge-feedback { font-size: 13px; color: var(--text2); line-height: 1.6; margin-bottom: 12px; }
.judge-section { margin-bottom: 10px; }
.issue-row, .sugg-row { display: flex; gap: 8px; font-size: 12px; color: var(--text2); margin-bottom: 5px; line-height: 1.5; }
.verdict-badge { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 6px; }
.verdict-pass { background: var(--success-bg); color: var(--success); }
.verdict-challenge { background: var(--warn-bg); color: var(--warn); }
.verdict-fail { background: var(--danger-bg); color: var(--danger); }
.judge-improved { border-top: 0.5px solid var(--border); padding-top: 12px; margin-top: 10px; }
.improved-text { font-size: 12px; color: var(--text); line-height: 1.7; white-space: pre-wrap; background: var(--bg); padding: 10px; border-radius: var(--radius); border: 0.5px solid var(--border); max-height: 300px; overflow-y: auto; }
</style>
