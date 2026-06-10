<template>
  <div>
    <div class="page-title">Company targets</div>
    <p class="page-sub">qwen3.6 suggests companies based on your profile. Visit their careers pages and paste JDs into the Matcher.</p>

    <div style="display:flex;gap:10px;margin-bottom:20px;align-items:center;">
      <select v-model="roleType" class="input" style="width:200px;">
        <option>Both</option><option>TPM</option><option>FDL</option>
      </select>
      <button class="btn btn-primary" :disabled="loading" @click="suggest">
        <i :class="['ti', loading ? 'ti-loader-2 spin' : 'ti-bulb']"/>
        {{ loading ? 'Thinking...' : 'Suggest targets' }}
      </button>
      <button class="btn" @click="showAdd = !showAdd">
        <i class="ti ti-plus"/>Add manually
      </button>
    </div>

    <ThinkingBar :visible="loading" message="qwen3.6 is reasoning through best company targets..."/>

    <div v-if="showAdd" class="card" style="margin-bottom:16px;">
      <div class="section-label" style="margin-bottom:12px;">Add manually</div>
      <div class="two-col" style="margin-bottom:10px;">
        <div class="field"><label class="label">Company</label><input v-model="manual.company" class="input" placeholder="e.g. Palantir"/></div>
        <div class="field"><label class="label">Role title</label><input v-model="manual.role" class="input" placeholder="e.g. Forward Deployed Engineer"/></div>
      </div>
      <div class="two-col" style="margin-bottom:12px;">
        <div class="field"><label class="label">Location</label><input v-model="manual.location" class="input" placeholder="Remote UK"/></div>
        <div class="field"><label class="label">JD URL</label><input v-model="manual.url" class="input" placeholder="https://..."/></div>
      </div>
      <div style="display:flex;gap:8px;">
        <button class="btn" @click="saveManual"><i class="ti ti-bookmark"/>Save to tracker</button>
        <button class="btn" style="color:var(--text3)" @click="showAdd=false">Cancel</button>
      </div>
    </div>

    <p v-if="error" style="color:var(--danger);font-size:13px;margin-bottom:12px;">{{ error }}</p>

    <div v-if="!suggestions.length && !loading" class="empty-state">
      <i class="ti ti-bulb"/>
      <p>Click "Suggest targets" — qwen3.6 will reason through the best companies for your profile.</p>
      <p style="margin-top:6px;font-size:12px;">Expect 20–30s. The thinking makes the suggestions significantly better.</p>
    </div>

    <div v-if="suggestions.length">
      <div class="section-label" style="margin-bottom:12px;">{{ suggestions.length }} targets identified</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        <div v-for="(s, i) in suggestions" :key="i" class="card">
          <div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:8px;">
            <div>
              <div style="font-size:14px;font-weight:600;margin-bottom:2px;">{{ s.company }}</div>
              <div style="font-size:12px;color:var(--text2);">{{ s.role_type }}</div>
            </div>
            <span class="chip" style="background:var(--bg2);color:var(--text2);flex-shrink:0;font-size:11px;">{{ s.location }}</span>
          </div>
          <p style="font-size:12px;color:var(--text2);line-height:1.6;margin-bottom:10px;">{{ s.why_fit }}</p>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <button class="btn" style="font-size:12px;padding:5px 10px;" @click="goMatch(s)">
              <i class="ti ti-git-compare" style="font-size:12px"/>Match JD
            </button>
            <button class="btn" style="font-size:12px;padding:5px 10px;" @click="save(s)">
              <i class="ti ti-bookmark" style="font-size:12px"/>Save
            </button>
            <a v-if="s.careers_url" :href="s.careers_url" target="_blank" class="btn" style="font-size:12px;padding:5px 10px;text-decoration:none;">
              <i class="ti ti-external-link" style="font-size:12px"/>Careers
            </a>
          </div>
        </div>
      </div>

      <div v-if="meta" class="meta-bar">
        <i class="ti ti-cpu" style="font-size:12px"/>
        <span class="chain">{{ meta.model_chain?.join(' → ') }}</span>
        <span>·</span><span>{{ meta.generation_ms }}ms</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useAppStore } from '../stores/app'
import ThinkingBar from '../components/ThinkingBar.vue'

const router = useRouter()
const store = useAppStore()
const roleType = ref('Both')
const suggestions = ref([])
const loading = ref(false)
const error = ref('')
const meta = ref(null)
const showAdd = ref(false)
const manual = ref({ company: '', role: '', location: '', url: '' })

async function suggest() {
  loading.value = true; error.value = ''
  try {
    const res = await api.discover.suggest(roleType.value)
    suggestions.value = res.suggestions || []
    meta.value = res.meta
  } catch (e) { error.value = e.message }
  loading.value = false
}

function goMatch(s) {
  sessionStorage.setItem('prefill_jd', `Company: ${s.company}\nRole: ${s.role_type}\n\nPaste the job description from their careers page here.`)
  router.push('/matcher')
}

async function save(s) {
  await store.createApplication({ company: s.company, role: s.role_type, location: s.location, url: s.careers_url || '' })
}

async function saveManual() {
  if (!manual.value.role) return
  await store.createApplication({ ...manual.value })
  manual.value = { company: '', role: '', location: '', url: '' }
  showAdd.value = false
}
</script>
