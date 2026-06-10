<template>
  <div>
    <div class="page-title">JD Matcher</div>
    <p class="page-sub">qwen3.6 analyses your resume against the JD. Gemini judges and challenges the result.</p>

    <div class="two-col">
      <!-- Left: Input -->
      <div>
        <div class="section-label">Job description</div>
        <textarea v-model="jdText" class="input" rows="12" placeholder="Paste the full job description here..." style="margin-bottom:12px;"/>
        <div class="field">
          <label class="label">Resume variant</label>
          <div style="display:flex;gap:8px;">
            <button v-for="v in ['fdl','tpm']" :key="v" @click="variant = v"
              class="btn" :class="{ 'btn-primary': variant === v }" style="flex:1;justify-content:center;">
              {{ v === 'fdl' ? 'Forward Deployment Lead' : 'Technical Product Manager' }}
            </button>
          </div>
        </div>
        <p v-if="error" style="color:var(--danger);font-size:12px;margin-bottom:8px;">{{ error }}</p>
        <button class="btn btn-full" :disabled="loading" @click="analyze">
          <i :class="['ti', loading ? 'ti-loader-2 spin' : 'ti-chart-bar']"/>
          {{ loading ? 'Analyzing...' : 'Analyze match ↗' }}
        </button>
        <p style="font-size:11px;color:var(--text3);text-align:center;margin-top:6px;">
          qwen3.6 reasons through full match · Gemini judges the output · Allow 30–60s
        </p>
      </div>

      <!-- Right: Results -->
      <div>
        <div class="section-label">Match analysis</div>
        <ThinkingBar :visible="loading" message="qwen3.6 analyzing · Gemini judging..."/>

        <div v-if="!analysis && !loading" class="empty-state">
          <i class="ti ti-git-compare"/>
          <p>Paste a JD and click Analyze</p>
        </div>

        <template v-if="analysis">
          <!-- Score + verdict -->
          <div class="card" style="display:flex;align-items:center;gap:16px;margin-bottom:12px;">
            <ScoreGauge :score="analysis.match_score"/>
            <div style="flex:1">
              <div style="font-size:15px;font-weight:600;margin-bottom:3px;">{{ analysis.verdict }}</div>
              <div style="font-size:12px;color:var(--text2);margin-bottom:8px;">{{ analysis.role_detected }}</div>
              <button class="btn" style="font-size:12px;padding:5px 10px;" @click="saveToTracker">
                <i class="ti ti-bookmark" style="font-size:12px"/>Save to tracker
              </button>
            </div>
          </div>

          <!-- Keywords -->
          <div class="two-col" style="margin-bottom:12px;gap:8px;">
            <div style="background:var(--success-bg);border-radius:var(--radius);padding:10px 12px;">
              <div class="section-label" style="color:var(--success);margin-bottom:8px;">Matched ({{ analysis.matched_keywords?.length || 0 }})</div>
              <div style="display:flex;flex-wrap:wrap;gap:4px;">
                <span v-for="k in analysis.matched_keywords" :key="k" class="chip kw-matched">{{ k }}</span>
              </div>
            </div>
            <div style="background:var(--danger-bg);border-radius:var(--radius);padding:10px 12px;">
              <div class="section-label" style="color:var(--danger);margin-bottom:8px;">Missing ({{ analysis.missing_keywords?.length || 0 }})</div>
              <div style="display:flex;flex-wrap:wrap;gap:4px;">
                <span v-for="k in analysis.missing_keywords" :key="k" class="chip kw-missing">{{ k }}</span>
              </div>
            </div>
          </div>

          <!-- Rewritten bullets -->
          <div v-if="analysis.rewritten_bullets?.length" style="margin-bottom:12px;">
            <div class="section-label">Rewritten bullets</div>
            <div v-for="(b, i) in analysis.rewritten_bullets.slice(0,4)" :key="i" class="card" style="margin-bottom:8px;padding:12px;">
              <div style="font-size:12px;color:var(--text3);text-decoration:line-through;margin-bottom:4px;">{{ b.original }}</div>
              <div style="font-size:12px;margin-bottom:4px;">{{ b.rewritten }}</div>
              <div style="font-size:11px;color:var(--info);display:flex;align-items:flex-start;gap:4px;">
                <i class="ti ti-arrow-right" style="font-size:11px;margin-top:2px;flex-shrink:0"/>{{ b.reason }}
              </div>
            </div>
          </div>

          <!-- Tailored summary -->
          <div v-if="analysis.tailored_summary" class="card" style="margin-bottom:12px;padding:12px;">
            <div class="section-label">Tailored summary</div>
            <p style="font-size:12px;line-height:1.6;">{{ analysis.tailored_summary }}</p>
          </div>

          <!-- Recommendation -->
          <div v-if="analysis.overall_recommendation" style="font-size:12px;color:var(--text2);line-height:1.6;border-top:0.5px solid var(--border);padding-top:10px;margin-top:4px;">
            <strong style="color:var(--text);">Recommendation: </strong>{{ analysis.overall_recommendation }}
          </div>

          <!-- Judge panel -->
          <JudgePanel :judge="judgeResult" @use-improved="applyImproved"/>

          <!-- Meta -->
          <div v-if="meta" class="meta-bar">
            <i class="ti ti-cpu" style="font-size:12px"/>
            <span class="chain">{{ meta.model_chain?.join(' → ') }}</span>
            <span>·</span><span>{{ meta.generation_ms }}ms</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { useAppStore } from '../stores/app'
import ScoreGauge from '../components/ScoreGauge.vue'
import JudgePanel from '../components/JudgePanel.vue'
import ThinkingBar from '../components/ThinkingBar.vue'

const store = useAppStore()
const jdText = ref('')
const variant = ref('fdl')
const loading = ref(false)
const error = ref('')
const analysis = ref(null)
const judgeResult = ref(null)
const meta = ref(null)

onMounted(() => {
  const prefill = sessionStorage.getItem('prefill_jd')
  if (prefill) { jdText.value = prefill; sessionStorage.removeItem('prefill_jd') }
})

async function analyze() {
  if (!jdText.value.trim()) { error.value = 'Paste a job description first'; return }
  loading.value = true; error.value = ''; analysis.value = null; judgeResult.value = null
  try {
    const res = await api.matcher.analyze(jdText.value, variant.value)
    analysis.value = res.analysis
    judgeResult.value = res.judge
    meta.value = res.meta
  } catch (e) { error.value = e.message }
  loading.value = false
}

async function saveToTracker() {
  const rewritten = []
  if (analysis.value?.rewritten_bullets?.length) {
    rewritten.push(...analysis.value.rewritten_bullets.map(b => `- ${b.rewritten}`))
  }
  if (analysis.value?.tailored_summary) {
    rewritten.push(`\nTailored summary:\n${analysis.value.tailored_summary}`)
  }
  await store.createApplication({
    role: analysis.value?.role_detected || 'Unknown Role',
    match_score: analysis.value?.match_score || null,
    resume_variant: variant.value,
    jd_text: jdText.value.slice(0, 2000),
    rewritten_resume: rewritten.join('\n'),
  })
}

function applyImproved(content) {
  // Apply judge's improved summary to analysis
  if (analysis.value) analysis.value.tailored_summary = content
}
</script>
