<template>
  <div>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;">
      <div>
        <div class="page-title">Application tracker</div>
        <p class="page-sub" style="margin-bottom:0;">{{ store.applications.length }} applications · backed by PostgreSQL</p>
      </div>
      <button class="btn" :disabled="!store.applications.length" @click="store.exportCsv()">
        <i class="ti ti-download"/>Export CSV
      </button>
    </div>

    <!-- Stats -->
    <div class="three-col" style="margin-bottom:20px;" v-if="store.applications.length">
      <div v-for="s in statusSummary" :key="s.label" :style="{background: s.bg, borderRadius: 'var(--radius)', padding: '12px', textAlign:'center'}">
        <div style="font-size:20px;font-weight:600;" :style="{color:s.color}">{{ s.count }}</div>
        <div style="font-size:11px;" :style="{color:s.color}">{{ s.label }}</div>
      </div>
    </div>

    <div v-if="!store.applications.length" class="empty-state">
      <i class="ti ti-table"/>
      <p>No applications yet. Save jobs from Discover or Matcher.</p>
    </div>

    <div v-else style="border:0.5px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;">
      <table style="width:100%;border-collapse:collapse;font-size:13px;table-layout:fixed;">
        <thead>
          <tr style="background:var(--bg2);">
            <th v-for="h in headers" :key="h.label" :style="h.style" style="padding:9px 12px;text-align:left;font-size:11px;font-weight:500;color:var(--text3);text-transform:uppercase;letter-spacing:0.06em;border-bottom:0.5px solid var(--border);">
              {{ h.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="app in store.applications" :key="app.id" style="border-bottom:0.5px solid var(--border);">
            <td style="padding:9px 12px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ app.company || '—' }}</td>
            <td style="padding:9px 12px;color:var(--text2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ app.role }}</td>
            <td style="padding:9px 12px;">
              <select :value="app.status" @change="updateStatus(app.id, $event.target.value)"
                :style="{ background: statusBg(app.status), color: statusColor(app.status), fontSize:'11px', fontWeight:'500', padding:'2px 6px', borderRadius:'6px', border:'none', cursor:'pointer' }">
                <option v-for="s in STATUSES" :key="s">{{ s }}</option>
              </select>
            </td>
            <td style="padding:9px 12px;color:var(--text2);font-size:12px;">{{ app.match_score != null ? app.match_score + '%' : '—' }}</td>
            <td style="padding:9px 12px;">
              <span class="chip" style="background:var(--info-bg);color:var(--info);">{{ (app.resume_variant || '').toUpperCase() }}</span>
            </td>
            <td style="padding:9px 12px;color:var(--text2);font-size:12px;">{{ app.rewritten_resume ? 'Yes' : 'No' }}</td>
            <td style="padding:9px 12px;color:var(--text3);font-size:12px;">{{ formatDate(app.created_at) }}</td>
            <td style="padding:9px 12px;text-align:center;">
              <div style="display:flex;gap:6px;justify-content:center;">
                <a v-if="app.url" :href="app.url" target="_blank" style="color:var(--text2);font-size:15px;"><i class="ti ti-external-link"/></a>
                <button @click="store.removeApplication(app.id)" style="background:transparent;border:none;cursor:pointer;color:var(--text3);font-size:15px;padding:0;"><i class="ti ti-trash"/></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()

const STATUSES = ['Saved', 'Applied', 'Screening', 'Interview', 'Offer', 'Rejected']
const headers = [
  { label: 'Company' }, { label: 'Role' },
  { label: 'Status', style: 'width:120px' }, { label: 'Score', style: 'width:65px' },
  { label: 'Resume', style: 'width:75px' }, { label: 'Updated', style: 'width:75px' }, { label: 'Date', style: 'width:90px' },
  { label: '', style: 'width:55px' }
]

const SBG = { Saved:'var(--bg2)', Applied:'var(--info-bg)', Screening:'var(--warn-bg)', Interview:'#E1F5EE', Offer:'var(--success-bg)', Rejected:'var(--danger-bg)' }
const STC = { Saved:'var(--text2)', Applied:'var(--info)', Screening:'var(--warn)', Interview:'#0F6E56', Offer:'var(--success)', Rejected:'var(--danger)' }
const statusBg = s => SBG[s] || SBG.Saved
const statusColor = s => STC[s] || STC.Saved

const statusSummary = computed(() => [
  { label: 'Applied', count: store.statusCounts['Applied'] || 0, bg: 'var(--info-bg)', color: 'var(--info)' },
  { label: 'Interview', count: store.statusCounts['Interview'] || 0, bg: '#E1F5EE', color: '#0F6E56' },
  { label: 'Offer', count: store.statusCounts['Offer'] || 0, bg: 'var(--success-bg)', color: 'var(--success)' },
])

function updateStatus(id, status) {
  store.updateApplication(id, { status })
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB')
}
</script>
