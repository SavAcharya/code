const BASE = '/api'

async function request(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  health: () => request('GET', '/../health'),
  status: () => request('GET', '/status'),

  discover: {
    suggest: (roleType = 'Both') =>
      request('POST', '/discover/suggest', { role_type: roleType })
  },
  matcher: {
    analyze: (jdText, resumeVariant = 'fdl') =>
      request('POST', '/matcher/analyze', { jd_text: jdText, resume_variant: resumeVariant })
  },
  tracker: {
    list: () => request('GET', '/tracker/'),
    create: (data) => request('POST', '/tracker/', data),
    update: (id, data) => request('PUT', `/tracker/${id}`, data),
    remove: (id) => request('DELETE', `/tracker/${id}`),
    exportCsv: () => fetch(BASE + '/tracker/export/csv')
  },
  cover: {
    generate: (company, role, jdText, resumeVariant = 'fdl') =>
      request('POST', '/cover/generate', { company, role, jd_text: jdText, resume_variant: resumeVariant })
  },
  profile: {
    get: () => request('GET', '/profile/'),
    save: (data) => request('POST', '/profile/', data),
    uploadResume: (data) => request('POST', '/profile/resume', data),
    uploadResumeFile: (formData) => fetch(BASE + '/profile/resume/file', {
      method: 'POST',
      body: formData
    }).then(async res => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      return res.json()
    })
  },
  resumes: {
    list: () => request('GET', '/resumes/'),
    getActive: (variant) => request('GET', `/resumes/${variant}/active`),
    create: (variant, label, content) =>
      request('POST', '/resumes/', { variant, label, content })
  }
}
