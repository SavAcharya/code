<template>
  <div>
    <div class="page-title">Cover letter</div>
    <p class="page-sub">qwen3.6 drafts · Gemini judges and challenges · you choose which version to send</p>

    <div class="two-col">
      <!-- Left: Config -->
      <div>
        <div class="section-label">Application</div>
        <div class="field">
          <label class="label">Select from tracker</label>
          <select v-model="selectedId" class="input">
            <option value="">— choose application —</option>
            <option v-for="a in store.applications" :key="a.id" :value="a.id">
              {{ a.company ? a.company + ' — ' : '' }}{{ a.role }}
            </option>
          </select>
        </div>
        <template v-if="selectedId">
          <div class="field">
            <label class="label">Override company name</label>
            <input v-model="company" class="input" placeholder="Company name"/>
          </div>
          <div class="field">
            <label class="label">Resume variant</label>
            <div style="display:flex;gap:8px;">
              <button v-for="v in ['fdl','tpm']" :key="v" @click="variant = v"
                class="btn" :class="{ 'btn-primary': variant === v }" style="flex:1;justify-content:center;font-size:12px;">
                {{ v.toUpperCase() }}
              </button>
            </div>
          </div>
          <div class="field">
            <label class="label">Job description <span style="font-weight:400;color:var(--text3)">(optional but recommended)</span></label>
            <textarea v-model="jdText" class="input" rows="8" placeholder="Paste JD for a more tailored letter..."/>
          </div>
          <p v-if="error" style="color:var(--danger);font-size:12px;margin-bottom:8px;">{{ error }}</p>
          <button class="btn btn-full btn-primary" :disabled="loading" @click="generate">
            <i :class="['ti', loading ? 'ti-loader-2 spin' : 'ti-file-text']"/>
            {{ loading ? 'Writing & judging...' : 'Generate cover letter ↗' }}
          </button>
          <p style="font-size:11px;color:var(--text3);text-align:center;margin-top:6px;">
            qwen3.6 drafts · Gemini scores and improves · Critical complexity
          </p>
        </template>
        <div v-else class="empty-state" style="margin-top:16px;">
          <i class="ti ti-arrow-up"/>
          <p>Select an application from the tracker above</p>
        </div>
      </div>

      <!-- Right: Output -->
      <div>
        <div class="section-label">Output</div>
        <ThinkingBar :visible="loading" message="qwen3.6 drafting · Gemini reviewing..."/>

        <div v-if="!coverLetter && !loading" class="empty-state">
          <i class="ti ti-file-text"/>
          <p>Select an application and generate</p>
        </div>

        <template v-if="coverLetter">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <span style="font-size:12px;font-weight:500;">Draft</span>
            <button class="btn" style="font-size:12px;padding:4px 10px;" @click="copy(coverLetter)">
              <i class="ti ti-copy" style="font-size:12px"/>Copy
            </button>
          </div>
          <textarea v-model="coverLetter" class="input" rows="14" style="line-height:1.7;margin-bottom:4px;"/>

          <!-- Judge panel with use-improved -->
          <JudgePanel :judge="judgeResult" @use-improved="coverLetter = $event"/>

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
import { ref, watch, computed } from 'vue'
import { api } from '../api'
import { useAppStore } from '../stores/app'
import JudgePanel from '../components/JudgePanel.vue'
import ThinkingBar from '../components/ThinkingBar.vue'

const store = useAppStore()
const selectedId = ref('')
const company = ref('')
const variant = ref('fdl')
const jdText = ref('')
const coverLetter = ref('')
const judgeResult = ref(null)
const meta = ref(null)
const loading = ref(false)
const error = ref('')

watch(selectedId, (id) => {
  const app = store.applications.find(a => a.id === Number(id))
  if (app) {
    company.value = app.company || ''
    variant.value = app.resume_variant || 'fdl'
    jdText.value = app.jd_text || ''
  }
})

async function generate() {
  const app = store.applications.find(a => a.id === Number(selectedId.value))
  if (!app) return
  loading.value = true; error.value = ''; coverLetter.value = ''; judgeResult.value = null
  try {
    const res = await api.cover.generate(company.value || app.company, app.role, jdText.value, variant.value)
    coverLetter.value = res.cover_letter
    judgeResult.value = res.judge
    meta.value = res.meta
  } catch (e) { error.value = e.message }
  loading.value = false
}

function copy(text) {
  navigator.clipboard.writeText(text)
}
</script>
