<template>
  <div>
    <div class="page-title">Profile</div>
    <p class="page-sub">Upload your resume text, save it as an active profile resume, and store your LinkedIn URL.</p>

    <div class="card" style="margin-bottom:18px;">
      <div class="section-label">LinkedIn profile</div>
      <div class="field">
        <label class="label">LinkedIn URL</label>
        <input v-model="linkedinUrl" class="input" placeholder="https://www.linkedin.com/in/your-profile" />
      </div>
      <div class="field" style="margin-top:12px;">
        <label class="label">Primary resume variant</label>
        <div style="display:flex;gap:8px;">
          <button class="btn" :class="{ 'btn-primary': variant === 'fdl' }" @click="variant = 'fdl'">Forward Deployment Lead</button>
          <button class="btn" :class="{ 'btn-primary': variant === 'tpm' }" @click="variant = 'tpm'">Technical Product Manager</button>
        </div>
      </div>
      <div class="field" style="margin-top:12px;">
        <label class="label">Resume text</label>
        <textarea v-model="resumeText" class="input" rows="12" placeholder="Paste your resume text here or upload a .txt/.pdf/.doc/.docx file"></textarea>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:12px;">
        <label class="btn" style="padding:8px 12px;border-radius:8px;cursor:pointer;">
          <i class="ti ti-upload" style="margin-right:6px"></i>Upload .txt, .pdf, .doc, .docx
          <input type="file" accept=".txt,.pdf,.doc,.docx" @change="loadFile" style="display:none" />
        </label>
        <button class="btn btn-primary" :disabled="saving" @click="saveProfile">
          <i :class="['ti', saving ? 'ti-loader-2 spin' : 'ti-check']"></i>
          {{ saving ? 'Saving...' : 'Save profile' }}
        </button>
        <button class="btn" :disabled="saving || (!resumeText.trim() && !selectedFile)" @click="uploadResume">
          <i class="ti ti-database" style="margin-right:6px"></i>Upload resume
        </button>
      </div>
      <div v-if="selectedFile" style="margin-top:12px;font-size:13px;color:var(--text2);">
        Selected file: {{ selectedFile.name }}
      </div>
      </div>
      <p v-if="message" style="margin-top:12px;color:var(--info);font-size:13px;">{{ message }}</p>
      <p v-if="error" style="margin-top:12px;color:var(--danger);font-size:13px;">{{ error }}</p>
    </div>

    <div v-if="activeResumeLabel || activeResumeContent" class="card">
      <div class="section-label">Active resume</div>
      <p style="font-size:12px;color:var(--text2);margin-bottom:10px;">Current active resume for variant {{ activeResumeVariant.toUpperCase() }}.</p>
      <div v-if="activeResumeLabel" style="font-size:13px;font-weight:600;margin-bottom:6px;">{{ activeResumeLabel }}</div>
      <pre style="white-space:pre-wrap;font-size:12px;line-height:1.5;color:var(--text2);">{{ activeResumeContent || 'No active resume uploaded yet.' }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const linkedinUrl = ref('')
const variant = ref('fdl')
const resumeText = ref('')
const selectedFile = ref(null)
const activeResumeLabel = ref('')
const activeResumeContent = ref('')
const activeResumeVariant = ref('fdl')
const saving = ref(false)
const message = ref('')
const error = ref('')

async function loadProfile() {
  try {
    const res = await api.profile.get()
    linkedinUrl.value = res.linkedin_url || ''
    variant.value = res.active_resume_variant || 'fdl'
    activeResumeVariant.value = res.active_resume_variant || 'fdl'
    activeResumeLabel.value = res.active_resume_label || ''
    activeResumeContent.value = res.active_resume_content || ''
  } catch (e) {
    error.value = e.message
  }
}

function loadFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  selectedFile.value = file

  if (file.name.toLowerCase().endsWith('.txt')) {
    const reader = new FileReader()
    reader.onload = () => {
      resumeText.value = String(reader.result || '')
    }
    reader.readAsText(file)
  } else {
    resumeText.value = ''
    message.value = `Selected ${file.name}. Click Upload resume to send it.`
  }
}

async function saveProfile() {
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    await api.profile.save({ linkedin_url: linkedinUrl.value, active_resume_variant: variant.value })
    activeResumeVariant.value = variant.value
    message.value = 'Profile saved successfully.'
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function uploadResume() {
  if (!resumeText.value.trim() && !selectedFile.value) {
    error.value = 'Paste or upload resume text first.'
    return
  }
  saving.value = true
  message.value = ''
  error.value = ''
  try {
    let res
    if (selectedFile.value) {
      const formData = new FormData()
      formData.append('variant', variant.value)
      formData.append('label', `${variant.value.toUpperCase()} profile upload`)
      formData.append('file', selectedFile.value)
      res = await api.profile.uploadResumeFile(formData)
    } else {
      res = await api.profile.uploadResume({ variant: variant.value, label: `${variant.value.toUpperCase()} profile upload`, content: resumeText.value })
    }
    activeResumeVariant.value = res.variant
    activeResumeLabel.value = res.label
    activeResumeContent.value = res.content
    message.value = 'Resume uploaded and set active.'
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
    selectedFile.value = null
  }
}

onMounted(loadProfile)
</script>
