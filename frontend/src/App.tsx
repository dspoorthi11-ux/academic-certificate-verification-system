import { motion } from 'framer-motion'
import {
  BadgeCheck,
  ChevronRight,
  FileCheck,
  Globe,
  Lock,
  LogOut,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  UserRound,
  Workflow,
} from 'lucide-react'
import { type FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, Navigate, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import api, { apiOrigin, getApiError, tokenKey, type ApiUser, type ApiVerification } from './lib/api'

type Role = ApiUser['role']

type User = {
  id: string
  name: string
  email: string
  role: Role
}

type Certificate = {
  id: string
  studentName: string
  studentEmail: string
  course: string
  certificateType: string
  institution: string
  issueDate: string
  status: 'ACTIVE' | 'PENDING' | 'REVOKED'
  hash: string
  blockchainHash: string
  risk: number
  issuer: string
}

type VerificationState = {
  certificate_id: string
  result: string
  message: string
  institution: string | null
  issuer_authentication: string
  document_integrity: string
  blockchain_status: string
  blockchain_reference: string | null
  ai_analysis: ApiVerification['ai_analysis']
  attestation: ApiVerification['attestation']
}

const stats = [
  { label: 'Issuer review', value: 'Independent' },
  { label: 'Document integrity', value: 'SHA-256' },
  { label: 'Attestation seal', value: 'Ed25519' },
]

const features = [
  { title: 'Trusted issuer review', description: 'Institutions enter the public registry only after administrator review of supporting evidence.', icon: Shield },
  { title: 'AI-assisted risk cues', description: 'Heuristic risk analysis supports reviewers; it never decides authenticity.', icon: Sparkles },
  { title: 'Evidence integrity', description: 'SHA-256 hashes compare submitted documents with issuer records.', icon: Globe },
  { title: 'Signed attestations', description: 'Successful checks produce a verifiable Ed25519 attestation and public QR link.', icon: FileCheck },
]

const steps = [
  'Institution applies for review',
  'Administrator checks evidence',
  'Issuer record is matched',
  'Uploaded file hash is compared',
  'Signed attestation is published',
]

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [certificates, setCertificates] = useState<Certificate[]>([])
  const [authLoading, setAuthLoading] = useState(true)

  useEffect(() => {
    const token = window.localStorage.getItem(tokenKey)
    if (!token) {
      setAuthLoading(false)
      return
    }

    api.get<ApiUser>('/auth/me')
      .then(({ data }) => setUser({ id: data.id, name: data.full_name, email: data.email, role: data.role }))
      .catch(() => window.localStorage.removeItem(tokenKey))
      .finally(() => setAuthLoading(false))
  }, [])

  const handleLogin = (nextUser: User) => {
    setUser(nextUser)
  }

  const handleLogout = () => {
    window.localStorage.removeItem(tokenKey)
    setUser(null)
  }

  const handleRegister = (nextUser: User) => {
    setUser(nextUser)
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route path="/verify" element={<VerificationPage />} />
      <Route path="/public/verify/:publicId" element={<PublicAttestationPage />} />
      <Route
        path="/login"
        element={
          authLoading ? <div className="auth-shell"><p>Checking session...</p></div> : user ? (
            <Navigate to={`/dashboard/${user.role}`} replace />
          ) : (
            <LoginPage onLogin={handleLogin} />
          )
        }
      />
      <Route
        path="/register"
        element={
          authLoading ? <div className="auth-shell"><p>Checking session...</p></div> : user ? (
            <Navigate to={`/dashboard/${user.role}`} replace />
          ) : (
            <RegisterPage onRegister={handleRegister} />
          )
        }
      />
      <Route
        path="/dashboard"
        element={
          authLoading ? <div className="auth-shell"><p>Checking session...</p></div> : user ? (
            <DashboardGate
              user={user}
              certificates={certificates}
              setCertificates={setCertificates}
              onLogout={handleLogout}
            />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/dashboard/:role"
        element={
          authLoading ? <div className="auth-shell"><p>Checking session...</p></div> : user ? (
            <DashboardGate
              user={user}
              certificates={certificates}
              setCertificates={setCertificates}
              onLogout={handleLogout}
            />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function LandingPage() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">C</div>
          <div>
            <div className="brand-name">CertiChain</div>
            <div className="brand-sub">Academic trust infrastructure</div>
          </div>
        </div>
        <nav className="nav">
          <a href="#how-it-works">How it works</a>
          <Link to="/register">For universities</Link>
          <Link to="/register">For employers</Link>
          <Link to="/about">About us</Link>
          <Link to="/verify">Verify</Link>
          <Link to="/login">Login</Link>
        </nav>
        <Link to="/login" className="primary-button small">Access platform</Link>
      </header>

      <main>
        <section className="hero-section">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="hero-copy"
          >
            <span className="eyebrow">Independent academic credential verification network</span>
            <h1>Trust Every Academic Credential</h1>
            <p>
              An independent verification service that helps universities, employers, and individuals establish confidence in academic documents.
            </p>
            <div className="cta-row">
              <Link to="/verify" className="primary-button">Verify a certificate</Link>
              <Link to="/register" className="secondary-button">Register your institution</Link>
            </div>
            <div className="hero-metrics">
              {stats.slice(0, 3).map((item) => (
                <div key={item.label} className="metric-box">
                  <strong>{item.value}</strong>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7 }}
            className="hero-visual"
          >
            <div className="visual-panel glass-card">
              <div className="mini-header"><span className="status-pill neutral">Verification workflow</span><span className="status-pill success"><BadgeCheck size={14} /> Evidence-led</span></div>
              <div className="workflow-list">
                <div><span>01</span><div><strong>Issuer identity</strong><small>Approved registry entry required</small></div><ShieldCheck size={18} /></div>
                <div><span>02</span><div><strong>Document integrity</strong><small>Uploaded SHA-256 compared with issuer record</small></div><Lock size={18} /></div>
                <div><span>03</span><div><strong>Risk assessment</strong><small>AI findings are supporting evidence only</small></div><Sparkles size={18} /></div>
                <div><span>04</span><div><strong>Independent attestation</strong><small>Signed only after successful checks</small></div><Workflow size={18} /></div>
              </div>
            </div>
          </motion.div>
        </section>

        <section className="content-section" style={{ paddingTop: '56px' }}>
          <div className="section-header">
            <span className="eyebrow">The problem</span>
            <h2>Fraud, delays, and trust gaps in academic records</h2>
          </div>
          <div className="info-cards">
            <div className="glass-card info-card">
              <TrendingUp size={30} />
              <h3>Manual verification</h3>
              <p>Universities and employers still rely on fragile document checks and slow confirmations.</p>
            </div>
            <div className="glass-card info-card">
              <Shield size={30} />
              <h3>Forged credentials</h3>
              <p>Certificates can be copied, edited, or reissued without traceable evidence.</p>
            </div>
            <div className="glass-card info-card">
              <UserRound size={30} />
              <h3>Low transparency</h3>
              <p>Students and employers need confidence in authenticity, issuer identity, and integrity.</p>
            </div>
          </div>
        </section>

        <section className="content-section">
          <div className="section-header center">
            <span className="eyebrow">How it works</span>
            <h2 id="how-it-works">From issuer evidence to a checkable attestation</h2>
          </div>
          <div className="steps-grid">
            {steps.map((step, index) => (
              <div key={step} className="step-item glass-card">
                <div className="step-number">0{index + 1}</div>
                <p>{step}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="content-section">
          <div className="section-header center">
            <span className="eyebrow">Platform features</span>
            <h2>Clear evidence, explicit limits, verifiable results</h2>
          </div>
          <div className="features-grid">
            {features.map(({ title, description, icon: Icon }) => (
              <div key={title} className="glass-card feature-card">
                <Icon size={28} />
                <h3>{title}</h3>
                <p>{description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="content-section audience-grid">
          <div className="panel"><span className="eyebrow">For universities</span><h2>Establish trusted issuer status</h2><p>Submit accreditation and authorization evidence. A platform administrator reviews every application before issuer records can be used for independent verification.</p><Link to="/register" className="secondary-button">Apply to the issuer network</Link></div>
          <div className="panel"><span className="eyebrow">For employers</span><h2>Check academic documents</h2><p>Compare a candidate’s document against an approved issuer record, inspect integrity and risk findings, and share a public attestation when checks succeed.</p><Link to="/verify" className="secondary-button">Verify a certificate</Link></div>
        </section>

        <section className="content-section">
          <div className="section-header"><span className="eyebrow">Verification seal</span><h2>Three identities, clearly separated</h2></div>
          <div className="features-grid">
            <div className="panel feature-card"><ShieldCheck size={28} /><h3>University credential</h3><p>The academic qualification remains issued and governed by the university.</p></div>
            <div className="panel feature-card"><Lock size={28} /><h3>Platform attestation</h3><p>Our Ed25519 signature seals the verification evidence; it does not replace a legally recognized electronic signature.</p></div>
            <div className="panel feature-card"><Globe size={28} /><h3>External trust services</h3><p>CCA-licensed signing and trusted timestamp services require an authorized provider integration.</p></div>
            <div className="panel feature-card"><Sparkles size={28} /><h3>Risk assessment</h3><p>AI cues prioritize review and never independently establish whether a credential is genuine.</p></div>
          </div>
        </section>

        <section className="content-section faq-section">
          <div className="section-header"><span className="eyebrow">Frequently asked questions</span><h2>What a verification result means</h2></div>
          <details><summary>Does this platform issue academic qualifications?</summary><p>No. Universities remain the original issuers. This platform records independent verification outcomes.</p></details>
          <details><summary>Does an AI score prove a certificate is authentic?</summary><p>No. Authenticity requires an approved issuer record and matching document hash. AI provides supporting risk cues only.</p></details>
          <details><summary>Does the platform seal count as a legally recognized DSC?</summary><p>No. The platform Ed25519 signature makes its attestation independently checkable. A legally recognized electronic signature requires an authorized signing-provider integration.</p></details>
          <details><summary>Is blockchain confirmation always available?</summary><p>No. Blockchain results are reported as unconfirmed until a deployed contract and transaction verification integration are configured.</p></details>
        </section>

        <section className="content-section cta-section glass-card">
          <div>
            <span className="eyebrow">Independent verification network</span>
            <h2>Verify once. Preserve trust for the future.</h2>
          </div>
          <Link to="/register" className="primary-button">
            Register an institution <ChevronRight size={18} />
          </Link>
        </section>
      </main>
      <footer className="site-footer"><span>Independent Academic Credential Verification Network</span><span>Platform attestations do not replace university-issued credentials or legally recognized signatures.</span><Link to="/about">About the service</Link></footer>
    </div>
  )
}

function AboutPage() {
  return (
    <div className="app-shell page-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">C</div>
          <div>
            <div className="brand-name">CertiChain</div>
            <div className="brand-sub">Academic trust infrastructure</div>
          </div>
        </div>
        <nav className="nav">
          <Link to="/">Home</Link>
          <Link to="/verify">Verify</Link>
          <Link to="/login">Login</Link>
        </nav>
      </header>

      <main className="page-content">
        <div className="panel">
          <span className="eyebrow">About the platform</span>
          <h1>Designed for trusted academic records</h1>
          <p>
            CertiChain gives universities, students, and verifiers a unified process for creating,
            storing, and validating academic credentials with the confidence of blockchain immutability,
            AI-assisted fraud checks, and fast public verification.
          </p>
        </div>

        <div className="three-col-grid">
          <div className="panel mini-panel">
            <ShieldCheck size={28} />
            <h3>Issuer trust</h3>
            <p>Institution records are anchored to a verifiable hash and made visible to authorized parties.</p>
          </div>
          <div className="panel mini-panel">
            <Sparkles size={28} />
            <h3>AI review</h3>
            <p>Each credential is evaluated with risk cues such as document mismatch, missing metadata, and anomalies.</p>
          </div>
          <div className="panel mini-panel">
            <Workflow size={28} />
            <h3>Public access</h3>
            <p>Anyone can verify a certificate with an ID, QR reference, or uploaded document without ambiguity.</p>
          </div>
        </div>
      </main>
    </div>
  )
}

function VerificationPage() {
  const [searchParams] = useSearchParams()
  const [candidate, setCandidate] = useState(() => searchParams.get('certificateId') ?? '')
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<VerificationState | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleCheck = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setResult(null)
    setProgress(0)
    if (!candidate.trim()) {
      setError('Enter the certificate ID provided by its institution.')
      return
    }

    setBusy(true)
    try {
      if (file) {
        const body = new FormData()
        body.append('certificate_id', candidate.trim())
        body.append('file', file)
        const { data } = await api.post<VerificationState>('/verification/verify-upload', body, {
          onUploadProgress: (event) => {
            if (event.total) setProgress(Math.round((event.loaded * 100) / event.total))
          },
        })
        setResult(data)
      } else {
        const { data } = await api.post<VerificationState>('/verification/verify', { certificate_id: candidate.trim() })
        setResult(data)
      }
    } catch (requestError) {
      setError(getApiError(requestError))
    } finally {
      setBusy(false)
    }
  }

  const selectFile = (selected: File | undefined) => {
    setError('')
    if (!selected) return
    if (!['application/pdf', 'image/jpeg', 'image/png'].includes(selected.type)) {
      setError('Choose a PDF, JPG, or PNG file.')
      return
    }
    if (selected.size > 10 * 1024 * 1024) {
      setError('The file must be 10 MB or smaller.')
      return
    }
    setFile(selected)
  }

  const statusTone = result?.result === 'AUTHENTIC' ? 'success' : result?.result === 'REVOKED' || result?.result === 'TAMPERED' ? 'danger' : 'neutral'

  return (
    <div className="app-shell page-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">C</div>
          <div>
            <div className="brand-name">CertiChain</div>
            <div className="brand-sub">Certificate verification</div>
          </div>
        </div>
        <nav className="nav">
          <Link to="/">Home</Link>
          <Link to="/about">About</Link>
          <Link to="/login">Login</Link>
        </nav>
      </header>

      <main className="page-content verify-layout">
        <div className="panel verification-panel">
          <span className="eyebrow">Public verification</span>
          <h1>Independently verify a certificate</h1>
          <form onSubmit={handleCheck} className="stacked-form">
            <label>
              Certificate ID
              <input
                value={candidate}
                onChange={(event) => setCandidate(event.target.value)}
                placeholder="Certificate ID from the issuer"
              />
            </label>
            <label className="upload-field">
              Certificate document (PDF, JPG, PNG; up to 10 MB)
              <input type="file" accept="application/pdf,image/jpeg,image/png" onChange={(event) => selectFile(event.target.files?.[0])} />
            </label>
            {file && <div className="file-chip"><span>{file.name} · {(file.size / 1024 / 1024).toFixed(2)} MB</span><button type="button" className="ghost-button" onClick={() => setFile(null)}>Remove</button></div>}
            {busy && file && <div className="progress"><div className="progress-bar" style={{ width: `${progress}%` }} /></div>}
            {error && <div className="alert error">{error}</div>}
            <button type="submit" disabled={busy} className="primary-button full-width">{busy ? 'Checking evidence...' : 'Verify certificate'}</button>
          </form>
          <p className="trust-note">AI analysis is a supporting risk assessment. Authenticity requires an approved issuer record and a matching document hash.</p>
        </div>

        <div className="panel result-panel">
          {result ? (
            <>
              <div className="result-header">
                <span className={`status-pill ${statusTone}`}>{result.result.replaceAll('_', ' ')}</span>
                <small>{result.certificate_id}</small>
              </div>
              <h3>{result.message}</h3>
              <div className="result-stats">
                <div>
                  <span>Issuer authentication</span>
                  <strong>{result.issuer_authentication}</strong>
                </div>
                <div>
                  <span>Document integrity</span>
                  <strong>{result.document_integrity}</strong>
                </div>
              </div>
              <dl className="evidence-list">
                <div><dt>Institution</dt><dd>{result.institution ?? 'Not confirmed'}</dd></div>
                <div><dt>Blockchain</dt><dd>{result.blockchain_status.replaceAll('_', ' ')}</dd></div>
                <div><dt>AI risk assessment</dt><dd>{result.ai_analysis.analysis_status === 'NOT_ASSESSED' ? 'Not assessed' : `${result.ai_analysis.risk_category} · ${result.ai_analysis.risk_score ?? 'N/A'}/100`}</dd></div>
                <div><dt>AI role</dt><dd>Supporting evidence only</dd></div>
              </dl>
              {result.ai_analysis.detected_anomalies.length > 0 && <p className="muted-copy">{result.ai_analysis.detected_anomalies.join('; ')}</p>}
              {result.attestation && <div className="attestation-actions"><img src={`${apiOrigin}/public/verify/${result.attestation.verification_id}/qr.png`} alt="Attestation QR code" /><div><strong>{result.attestation.verification_id}</strong><a href={result.attestation.public_url} target="_blank" rel="noreferrer">Independently check attestation</a><a href={`${apiOrigin}/api/attestations/${result.attestation.verification_id}/report.pdf`}>Download verification report</a></div></div>}
            </>
          ) : (
            <div className="empty-state">
              <ShieldAlert size={34} />
              <p>Verification results will show the issuer, document integrity, blockchain evidence, AI risk cues, and signature status.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function PublicAttestationPage() {
  const { publicId = '' } = useParams()
  const [attestation, setAttestation] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get(`/attestations/${encodeURIComponent(publicId)}`)
      .then(({ data }) => setAttestation(data as Record<string, unknown>))
      .catch((requestError: unknown) => setError(getApiError(requestError)))
  }, [publicId])

  const signature = attestation?.signature as { algorithm?: string; key_id?: string; valid?: boolean } | undefined

  return (
    <div className="app-shell page-shell">
      <header className="topbar"><Link className="brand-wrap" to="/"><div className="brand-mark">C</div><div><div className="brand-name">Independent Verification Network</div><div className="brand-sub">Public attestation check</div></div></Link><Link to="/verify" className="secondary-button">Verify another</Link></header>
      <main className="page-content">
        {error ? <div className="panel"><h1>Attestation unavailable</h1><p>{error}</p></div> : !attestation ? <div className="panel"><h1>Checking attestation...</h1></div> : (
          <div className="panel attestation-view">
            <span className={`status-pill ${signature?.valid ? 'success' : 'danger'}`}>{signature?.valid ? 'Signature valid' : 'Signature invalid'}</span>
            <h1>{String(attestation.result ?? 'Verification result')}</h1>
            <p>This is an independent platform verification attestation, not a university-issued credential or a legally recognized electronic signature.</p>
            <dl className="evidence-list">
              <div><dt>Verification ID</dt><dd>{String(attestation.verification_id ?? publicId)}</dd></div>
              <div><dt>Certificate ID</dt><dd>{String(attestation.certificate_id ?? '')}</dd></div>
              <div><dt>Original document SHA-256</dt><dd>{String(attestation.document_sha256 ?? '')}</dd></div>
              <div><dt>Institution</dt><dd>{String(attestation.institution ?? '')}</dd></div>
              <div><dt>Verified at</dt><dd>{String(attestation.verified_at ?? '')}</dd></div>
              <div><dt>Document integrity</dt><dd>{String(attestation.document_integrity ?? '')}</dd></div>
              <div><dt>Issuer confirmation</dt><dd>{String(attestation.issuer_authentication ?? '')}</dd></div>
              <div><dt>Blockchain</dt><dd>{String(attestation.blockchain_status ?? '')}</dd></div>
              <div><dt>Signature</dt><dd>{signature?.algorithm} · key {signature?.key_id}</dd></div>
            </dl>
            <img className="public-attestation-qr" src={`${apiOrigin}/public/verify/${encodeURIComponent(publicId)}/qr.png`} alt="QR code for this public attestation" />
            <p>{String(attestation.methodology ?? '')}</p>
            <a className="primary-button" href={`${apiOrigin}/api/attestations/${encodeURIComponent(publicId)}/report.pdf`}>Download verification report</a>
          </div>
        )}
      </main>
    </div>
  )
}

function LoginPage({ onLogin }: { onLogin: (user: User) => void }) {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const { data: token } = await api.post<{ access_token: string }>('/auth/login', form)
      window.localStorage.setItem(tokenKey, token.access_token)
      const { data: profile } = await api.get<ApiUser>('/auth/me')
      onLogin({ id: profile.id, name: profile.full_name, email: profile.email, role: profile.role })
      navigate(`/dashboard/${profile.role}`)
    } catch (requestError) {
      window.localStorage.removeItem(tokenKey)
      setError(getApiError(requestError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-panel panel">
        <span className="eyebrow">Secure access</span>
        <h1>Welcome back</h1>
        <p>Sign in to your institution, student, employer, or administrator workspace.</p>

        <form onSubmit={handleSubmit} className="stacked-form">
          <label>
            Email
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
            />
          </label>

          {error && <div className="alert error">{error}</div>}

          <button type="submit" disabled={busy} className="primary-button full-width">{busy ? 'Signing in...' : 'Sign in'}</button>
        </form>

        <div className="auth-footer">
          <span>Need an account?</span>
          <Link to="/register">Create one</Link>
        </div>
      </div>
    </div>
  )
}

function RegisterPage({ onRegister }: { onRegister: (user: User) => void }) {
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'university' as Role })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const { data: token } = await api.post<{ access_token: string }>('/auth/register', {
        email: form.email,
        full_name: form.name,
        password: form.password,
        role: form.role,
      })
      window.localStorage.setItem(tokenKey, token.access_token)
      const { data: profile } = await api.get<ApiUser>('/auth/me')
      onRegister({ id: profile.id, name: profile.full_name, email: profile.email, role: profile.role })
      navigate(`/dashboard/${profile.role}`)
    } catch (requestError) {
      setError(getApiError(requestError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-panel panel">
        <span className="eyebrow">Create account</span>
        <h1>Register your organization</h1>
        <p>Create a university, student, or employer account. Institution approval is a separate review process.</p>

        <form onSubmit={handleSubmit} className="stacked-form">
          <label>
            Full name
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          </label>

          <label>
            Work email
            <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          </label>

          <label>
            Password
            <input type="password" minLength={8} required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
          </label>

          <label>
            Role
            <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value as Role })}>
              <option value="university">University</option>
              <option value="student">Student</option>
              <option value="verifier">Employer / verifier</option>
            </select>
          </label>

          {error && <div className="alert error">{error}</div>}
          <button type="submit" disabled={busy} className="primary-button full-width">{busy ? 'Creating account...' : 'Create account'}</button>
        </form>

        <div className="auth-footer">
          <span>Already have access?</span>
          <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  )
}

function DashboardGate({
  user,
  certificates,
  setCertificates,
  onLogout,
}: {
  user: User
  certificates: Certificate[]
  setCertificates: React.Dispatch<React.SetStateAction<Certificate[]>>
  onLogout: () => void
}) {
  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role === 'university') {
    return <UniversityDashboard user={user} certificates={certificates} setCertificates={setCertificates} onLogout={onLogout} />
  }

  if (user.role === 'student') {
    return <StudentDashboard user={user} onLogout={onLogout} />
  }

  if (user.role === 'admin') {
    return <AdminDashboard user={user} onLogout={onLogout} />
  }

  return <VerifierDashboard user={user} onLogout={onLogout} />
}

type InstitutionApplication = {
  id: string
  institution_name: string
  institution_type: string
  official_email: string
  website: string
  country: string
  status: string
  domain_candidate: string
  accreditation: string
  supporting_documents: { id: string; name: string; sha256: string; mime_type: string }[]
  created_at: string
}

function InstitutionApplicationPanel() {
  const [application, setApplication] = useState<InstitutionApplication | null>(null)
  const [files, setFiles] = useState<File[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState({
    institution_name: '', institution_type: 'University', official_email: '', website: '', country: '', state: '', address: '', accreditation: '', representative_name: '', representative_designation: '', contact_number: '',
  })

  useEffect(() => {
    api.get<InstitutionApplication>('/institutions/mine')
      .then(({ data }) => setApplication(data))
      .catch(() => setApplication(null))
  }, [])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setNotice('')
    if (files.length === 0) {
      setError('Attach at least one official supporting document before submitting.')
      return
    }
    setBusy(true)
    try {
      const { data } = await api.post<InstitutionApplication>('/institutions/register', form)
      setApplication(data)
      for (const file of files) {
        const body = new FormData()
        body.append('file', file)
        await api.post(`/institutions/${data.id}/documents`, body)
      }
      const { data: refreshed } = await api.get<InstitutionApplication>('/institutions/mine')
      setApplication(refreshed)
      setFiles([])
      setNotice('Application submitted for independent review. This account is not a trusted issuer until approved.')
    } catch (requestError) {
      setError(getApiError(requestError))
    } finally {
      setBusy(false)
    }
  }

  const uploadPendingEvidence = async () => {
    if (!application || files.length === 0) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      for (const file of files) {
        const body = new FormData()
        body.append('file', file)
        await api.post(`/institutions/${application.id}/documents`, body)
      }
      const { data } = await api.get<InstitutionApplication>('/institutions/mine')
      setApplication(data)
      setFiles([])
      setNotice('Supporting evidence uploaded for administrator review.')
    } catch (requestError) {
      setError(getApiError(requestError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel institution-application">
      <div className="section-heading-row"><div><span className="eyebrow">Trusted issuer network</span><h2>Institution verification</h2></div>{application && <span className={`pill ${application.status === 'APPROVED' ? 'positive' : application.status === 'REJECTED' || application.status === 'SUSPENDED' ? 'negative' : 'warning'}`}>{application.status.replaceAll('_', ' ')}</span>}</div>
      {application ? (
        <div className="application-summary">
          <strong>{application.institution_name}</strong>
          <p>{application.website} · {application.official_email}</p>
          <p>{application.status === 'APPROVED' ? 'This institution is listed as an approved issuer.' : 'The application is under human review. Certificate records cannot be independently authenticated until approval.'}</p>
          <small>{application.supporting_documents.length} evidence document(s) submitted · Applied {new Date(application.created_at).toLocaleDateString()}</small>
          {['PENDING', 'UNDER_REVIEW'].includes(application.status) && <div className="pending-evidence"><label>Add supporting evidence (PDF/JPG/PNG, max 20 MB each)<input type="file" multiple accept="application/pdf,image/jpeg,image/png" onChange={(event) => setFiles(Array.from(event.target.files ?? []))} /></label>{files.length > 0 && <p className="muted-copy">{files.map((file) => file.name).join(', ')}</p>}<button type="button" disabled={busy || files.length === 0} className="secondary-button" onClick={() => void uploadPendingEvidence()}>{busy ? 'Uploading evidence...' : 'Upload evidence'}</button></div>}
        </div>
      ) : (
        <form className="institution-form" onSubmit={handleSubmit}>
          <label>Official institution name<input required value={form.institution_name} onChange={(event) => setForm({ ...form, institution_name: event.target.value })} /></label>
          <label>Institution type<select value={form.institution_type} onChange={(event) => setForm({ ...form, institution_type: event.target.value })}><option>University</option><option>College</option><option>Technical institute</option><option>Other accredited institution</option></select></label>
          <label>Official email<input required type="email" value={form.official_email} onChange={(event) => setForm({ ...form, official_email: event.target.value })} /></label>
          <label>Website<input required type="url" placeholder="https://institution.edu" value={form.website} onChange={(event) => setForm({ ...form, website: event.target.value })} /></label>
          <label>Country<input required value={form.country} onChange={(event) => setForm({ ...form, country: event.target.value })} /></label>
          <label>State / region<input value={form.state} onChange={(event) => setForm({ ...form, state: event.target.value })} /></label>
          <label>Official address<textarea required value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} /></label>
          <label>Accreditation body and reference<textarea required value={form.accreditation} onChange={(event) => setForm({ ...form, accreditation: event.target.value })} /></label>
          <label>Authorized representative<input required value={form.representative_name} onChange={(event) => setForm({ ...form, representative_name: event.target.value })} /></label>
          <label>Representative designation<input required value={form.representative_designation} onChange={(event) => setForm({ ...form, representative_designation: event.target.value })} /></label>
          <label>Contact number<input required value={form.contact_number} onChange={(event) => setForm({ ...form, contact_number: event.target.value })} /></label>
          <label className="wide-field">Supporting evidence (PDF/JPG/PNG, max 20 MB each)<input required type="file" multiple accept="application/pdf,image/jpeg,image/png" onChange={(event) => setFiles(Array.from(event.target.files ?? []))} /></label>
          {files.length > 0 && <p className="wide-field muted-copy">{files.map((file) => file.name).join(', ')}</p>}
          {error && <div className="alert error wide-field">{error}</div>}
          {notice && <div className="alert success wide-field">{notice}</div>}
          <button type="submit" disabled={busy} className="primary-button wide-field">{busy ? 'Submitting application...' : 'Submit for independent review'}</button>
        </form>
      )}
      {notice && application && <div className="alert success">{notice}</div>}
    </section>
  )
}

function AdminDashboard({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [applications, setApplications] = useState<InstitutionApplication[]>([])
  const [auditEvents, setAuditEvents] = useState<{ id: string; action: string; resource: string | null; result: string; created_at: string; details: string | null }[]>([])
  const [busyId, setBusyId] = useState('')
  const [error, setError] = useState('')

  const reload = () => api.get<InstitutionApplication[]>('/institutions/applications').then(({ data }) => setApplications(data)).catch((requestError: unknown) => setError(getApiError(requestError)))
  const reloadAudit = () => api.get<typeof auditEvents>('/audit?limit=100').then(({ data }) => setAuditEvents(data)).catch((requestError: unknown) => setError(getApiError(requestError)))
  useEffect(() => { void reload(); void reloadAudit() }, [])

  const review = async (application: InstitutionApplication, status: 'APPROVED' | 'REJECTED' | 'SUSPENDED') => {
    setBusyId(application.id)
    setError('')
    try {
      await api.post(`/institutions/${application.id}/review`, {
        status,
        evidence_reviewed: application.supporting_documents.map((document) => document.id),
        notes: `Status changed to ${status} by ${user.name}`,
      })
      await reload()
    } catch (requestError) {
      setError(getApiError(requestError))
    } finally {
      setBusyId('')
    }
  }

  const downloadEvidence = async (application: InstitutionApplication, evidence: InstitutionApplication['supporting_documents'][number]) => {
    try {
      const { data } = await api.get(`/institutions/${application.id}/documents/${evidence.id}`, { responseType: 'blob' })
      const url = URL.createObjectURL(data as Blob)
      const link = document.createElement('a')
      link.href = url
      link.download = evidence.name
      link.click()
      URL.revokeObjectURL(url)
    } catch (requestError) {
      setError(getApiError(requestError))
    }
  }

  return (
    <DashboardShell user={user} onLogout={onLogout}>
      <div className="dashboard-header"><div><span className="eyebrow">Platform administration</span><h1>Issuer review queue</h1></div><button type="button" className="secondary-button" onClick={() => void reload()}>Refresh</button></div>
      {error && <div className="alert error">{error}</div>}
      <section className="panel"><div className="section-heading-row"><h2>Institution applications</h2><span className="status-pill neutral">{applications.filter((item) => item.status === 'PENDING' || item.status === 'UNDER_REVIEW').length} awaiting review</span></div>
        {applications.length === 0 ? <div className="empty-state"><p>No institution applications have been submitted.</p></div> : <div className="admin-application-list">{applications.map((application) => (
          <article className="admin-application" key={application.id}>
            <div className="section-heading-row"><div><h3>{application.institution_name}</h3><p>{application.institution_type} · {application.country}</p></div><span className={`pill ${application.status === 'APPROVED' ? 'positive' : application.status === 'REJECTED' || application.status === 'SUSPENDED' ? 'negative' : 'warning'}`}>{application.status}</span></div>
            <dl className="evidence-list"><div><dt>Official email</dt><dd>{application.official_email}</dd></div><div><dt>Website / domain</dt><dd>{application.website} · {application.domain_candidate}</dd></div><div><dt>Accreditation</dt><dd>{application.accreditation}</dd></div><div><dt>Supporting evidence</dt><dd>{application.supporting_documents.length} file(s)</dd></div></dl>
            <div className="evidence-downloads">{application.supporting_documents.map((document) => <button type="button" className="ghost-button" key={document.id} onClick={() => void downloadEvidence(application, document)}>{document.name}</button>)}</div>
            <div className="row-actions"><button type="button" disabled={busyId === application.id} className="primary-button" onClick={() => void review(application, 'APPROVED')}>Approve</button><button type="button" disabled={busyId === application.id} className="ghost-button" onClick={() => void review(application, 'REJECTED')}>Reject</button>{application.status === 'APPROVED' && <button type="button" disabled={busyId === application.id} className="ghost-button danger" onClick={() => void review(application, 'SUSPENDED')}>Suspend</button>}</div>
          </article>
        ))}</div>}
      </section>
      <section className="panel"><div className="section-heading-row"><h2>Audit activity</h2><button type="button" className="ghost-button" onClick={() => void reloadAudit()}>Refresh</button></div>{auditEvents.length === 0 ? <p className="muted-copy">No audit events have been recorded.</p> : <div className="list-stack">{auditEvents.map((event) => <div className="list-item" key={event.id}><div><strong>{event.action.replaceAll('_', ' ')}</strong><small>{event.resource ?? 'Platform'} · {new Date(event.created_at).toLocaleString()}</small></div><span className="pill neutral">{event.result}</span></div>)}</div>}</section>
    </DashboardShell>
  )
}

function UniversityDashboard({
  user,
  certificates,
  setCertificates,
  onLogout,
}: {
  user: User
  certificates: Certificate[]
  setCertificates: React.Dispatch<React.SetStateAction<Certificate[]>>
  onLogout: () => void
}) {
  const [form, setForm] = useState({
    studentName: '',
    studentEmail: '',
    course: '',
    certificateType: 'Degree Certificate',
    institution: '',
  })
  const [document, setDocument] = useState<File | null>(null)
  const [issuerStatus, setIssuerStatus] = useState('LOADING')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const reloadCertificates = async () => {
    const { data } = await api.get<Record<string, unknown>[]>('/certificates')
    setCertificates(data.map((record) => ({
      id: String(record.certificate_id),
      studentName: String(record.student_id),
      studentEmail: '',
      course: String(record.course_name),
      certificateType: String(record.certificate_type),
      institution: String(record.institution_name),
      issueDate: String(record.issue_date).slice(0, 10),
      status: String(record.status) as Certificate['status'],
      hash: String(record.document_hash),
      blockchainHash: String(record.blockchain_transaction_hash ?? ''),
      risk: 0,
      issuer: user.name,
    })))
  }

  useEffect(() => {
    void reloadCertificates().catch((requestError: unknown) => setError(getApiError(requestError)))
    api.get<InstitutionApplication>('/institutions/mine')
      .then(({ data }) => setIssuerStatus(data.status))
      .catch(() => setIssuerStatus('NOT_REGISTERED'))
  }, [])

  const activeCount = useMemo(
    () => certificates.filter((item) => item.status === 'ACTIVE').length,
    [certificates],
  )
  const pendingCount = useMemo(
    () => certificates.filter((item) => item.status === 'PENDING').length,
    [certificates],
  )

  const handleIssueCertificate = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      if (!document) throw new Error('Upload the source certificate file before creating its issuer record.')
      if (!['application/pdf', 'image/jpeg', 'image/png'].includes(document.type)) throw new Error('Use a PDF, JPG, or PNG certificate file.')
      const upload = new FormData()
      upload.append('file', document)
      const { data: uploaded } = await api.post<{ hash: string }>('/certificates/upload', upload)
      await api.post('/certificates', {
        student_name: form.studentName,
        student_email: form.studentEmail,
        course_name: form.course,
        certificate_type: form.certificateType,
        institution_name: form.institution,
        document_hash: uploaded.hash,
        status: 'ACTIVE',
      })
      await reloadCertificates()
      setDocument(null)
      setNotice('Issuer record saved. No blockchain confirmation is claimed until an actual network transaction is configured.')
      setForm({ studentName: '', studentEmail: '', course: '', certificateType: 'Degree Certificate', institution: form.institution })
    } catch (requestError) {
      setError(getApiError(requestError))
    } finally {
      setBusy(false)
    }
  }

  const handleRevoke = async (certificateId: string) => {
    setError('')
    try {
      await api.post(`/certificates/${certificateId}/revoke`)
      await reloadCertificates()
    } catch (requestError) {
      setError(getApiError(requestError))
    }
  }

  const handleCopyId = async (certificateId: string) => {
    await navigator.clipboard.writeText(certificateId)
    setNotice(`Certificate ID ${certificateId} copied.`)
  }

  return (
    <DashboardShell user={user} onLogout={onLogout}>
      <div className="dashboard-header">
        <div>
          <span className="eyebrow">University workspace</span>
          <h1>Issuer dashboard</h1>
        </div>
        <Link to="/verify" className="secondary-button">Public verification</Link>
      </div>

      {issuerStatus !== 'APPROVED' && <div className="alert warning">Issuer status: {issuerStatus.replaceAll('_', ' ')}. Certificate records can only be added after independent administrator approval.</div>}
      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}

      <InstitutionApplicationPanel />

      <div className="summary-grid">
        <div className="panel summary-card">
          <span>Active certificates</span>
          <strong>{activeCount}</strong>
        </div>
        <div className="panel summary-card">
          <span>Pending review</span>
          <strong>{pendingCount}</strong>
        </div>
        <div className="panel summary-card">
          <span>Revoked</span>
          <strong>{certificates.filter((item) => item.status === 'REVOKED').length}</strong>
        </div>
      </div>

      <div className="dashboard-grid two-columns">
        <div className="panel">
          <h3>Issue certificate</h3>
          <form onSubmit={handleIssueCertificate} className="stacked-form compact">
            <label>
              Student name
              <input value={form.studentName} onChange={(event) => setForm({ ...form, studentName: event.target.value })} />
            </label>
            <label>
              Student email
              <input value={form.studentEmail} onChange={(event) => setForm({ ...form, studentEmail: event.target.value })} />
            </label>
            <label>
              Course
              <input value={form.course} onChange={(event) => setForm({ ...form, course: event.target.value })} />
            </label>
            <label>
              Certificate type
              <input value={form.certificateType} onChange={(event) => setForm({ ...form, certificateType: event.target.value })} />
            </label>
            <label>
              Institution name
              <input required value={form.institution} onChange={(event) => setForm({ ...form, institution: event.target.value })} />
            </label>
            <label>
              Original certificate PDF or image
              <input required type="file" accept="application/pdf,image/jpeg,image/png" onChange={(event) => setDocument(event.target.files?.[0] ?? null)} />
            </label>
            <button type="submit" disabled={busy || issuerStatus !== 'APPROVED'} className="primary-button">{busy ? 'Saving issuer record...' : 'Add verified issuer record'}</button>
          </form>
        </div>

        <div className="panel">
          <h3>Verification overview</h3>
          <div className="list-stack">
            {certificates.slice(0, 4).map((certificate) => (
              <div key={certificate.id} className="list-item">
                <div>
                  <strong>{certificate.id}</strong>
                  <small>{certificate.studentName}</small>
                </div>
                <span className={`pill ${certificate.status === 'ACTIVE' ? 'positive' : certificate.status === 'REVOKED' ? 'negative' : 'warning'}`}>
                  {certificate.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel">
        <h3>Recent certificates</h3>
        {certificates.length === 0 ? <p className="muted-copy">No issuer records are available for this institution.</p> : null}
        <div className="certificate-table">
          {certificates.map((certificate) => (
            <div className="table-row" key={certificate.id}>
              <div>
                <strong>{certificate.studentName}</strong>
                <small>{certificate.course}</small>
              </div>
              <span>#{certificate.id}</span>
              <span>{certificate.issueDate}</span>
              <span className={`pill ${certificate.status === 'ACTIVE' ? 'positive' : certificate.status === 'REVOKED' ? 'negative' : 'warning'}`}>
                {certificate.status}
              </span>
              <div className="row-actions">
                <button type="button" className="ghost-button" onClick={() => void handleCopyId(certificate.id)}>
                  Copy ID
                </button>
                <button type="button" disabled={certificate.status === 'REVOKED'} className="ghost-button danger" onClick={() => void handleRevoke(certificate.id)}>
                  Revoke
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </DashboardShell>
  )
}

function StudentDashboard({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [studentCertificates, setStudentCertificates] = useState<Certificate[]>([])
  const [selectedId, setSelectedId] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api.get<Record<string, unknown>[]>('/certificates')
      .then(({ data }) => {
        const records = data.map((record) => ({
          id: String(record.certificate_id),
          studentName: user.name,
          studentEmail: user.email,
          course: String(record.course_name),
          certificateType: String(record.certificate_type),
          institution: String(record.institution_name),
          issueDate: String(record.issue_date).slice(0, 10),
          status: String(record.status) as Certificate['status'],
          hash: String(record.document_hash),
          blockchainHash: String(record.blockchain_transaction_hash ?? ''),
          risk: 0,
          issuer: '',
        }))
        setStudentCertificates(records)
        setSelectedId(records[0]?.id ?? '')
      })
      .catch((requestError: unknown) => setError(getApiError(requestError)))
  }, [user.email, user.name])

  const selected = studentCertificates.find((item) => item.id === selectedId)

  return (
    <DashboardShell user={user} onLogout={onLogout}>
      <div className="dashboard-header">
        <div>
          <span className="eyebrow">Student workspace</span>
          <h1>Hello, {user.name}</h1>
        </div>
        <Link to="/verify" className="secondary-button">Verify credential</Link>
      </div>

      <div className="dashboard-grid two-columns">
        <div className="panel">
          <h3>Your certificates</h3>
          {error && <div className="alert error">{error}</div>}
          <div className="list-stack">
            {studentCertificates.map((certificate) => (
              <button type="button" key={certificate.id} className="list-item button-like" onClick={() => setSelectedId(certificate.id)}>
                <div>
                  <strong>{certificate.course}</strong>
                  <small>{certificate.id}</small>
                </div>
                <span className={`pill ${certificate.status === 'ACTIVE' ? 'positive' : certificate.status === 'REVOKED' ? 'negative' : 'warning'}`}>
                  {certificate.status}
                </span>
              </button>
            ))}
            {studentCertificates.length === 0 && !error && <div className="empty-state"><p>No certificates are linked to your student account yet.</p></div>}
          </div>
        </div>

        {selected && (
          <div className="panel credential-detail">
            <div className="detail-header">
              <span className="eyebrow">Issuer record</span>
              <span className={`pill ${selected.status === 'ACTIVE' ? 'positive' : selected.status === 'REVOKED' ? 'negative' : 'warning'}`}>{selected.status}</span>
            </div>
            <h3>{selected.course}</h3>
            <ul>
              <li>Institution: {selected.institution}</li>
              <li>Issue date: {selected.issueDate}</li>
              <li>Certificate ID: {selected.id}</li>
              <li>Document SHA-256: {selected.hash}</li>
              <li>Blockchain reference: {selected.blockchainHash || 'Not confirmed'}</li>
            </ul>
            <Link to={`/verify?certificateId=${encodeURIComponent(selected.id)}`} className="primary-button">Independently verify</Link>
          </div>
        )}
      </div>
    </DashboardShell>
  )
}

function VerifierDashboard({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [candidate, setCandidate] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<VerificationState | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [history, setHistory] = useState<{ verification_id: string; certificate_id: string; result: string; checked_at: string }[]>([])

  const reloadHistory = async () => {
    const { data } = await api.get<typeof history>('/verification/history')
    setHistory(data)
  }

  useEffect(() => {
    void reloadHistory().catch((requestError: unknown) => setError(getApiError(requestError)))
  }, [])

  const handleVerify = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setResult(null)
    if (!candidate.trim()) {
      setError('Enter the certificate ID supplied by the issuer.')
      return
    }

    setBusy(true)
    try {
      if (file) {
        const body = new FormData()
        body.append('certificate_id', candidate.trim())
        body.append('file', file)
        const { data } = await api.post<VerificationState>('/verification/verify-upload', body)
        setResult(data)
        void reloadHistory()
      } else {
        const { data } = await api.post<VerificationState>('/verification/verify', { certificate_id: candidate.trim() })
        setResult(data)
        void reloadHistory()
      }
    } catch (requestError) {
      setError(getApiError(requestError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <DashboardShell user={user} onLogout={onLogout}>
      <div className="dashboard-header">
        <div>
          <span className="eyebrow">Verifier workspace</span>
          <h1>Review queue</h1>
        </div>
        <Link to="/verify" className="secondary-button">Open public verification</Link>
      </div>

      <div className="dashboard-grid two-columns">
        <form className="panel stacked-form compact" onSubmit={handleVerify}>
          <h3>Review a credential</h3>
          <label>Certificate ID<input required value={candidate} onChange={(event) => setCandidate(event.target.value)} /></label>
          <label>Document for SHA-256 comparison<input type="file" accept="application/pdf,image/jpeg,image/png" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
          {file && <div className="file-chip"><span>{file.name}</span><button type="button" className="ghost-button" onClick={() => setFile(null)}>Remove</button></div>}
          {error && <div className="alert error">{error}</div>}
          <button type="submit" disabled={busy} className="primary-button">{busy ? 'Reviewing...' : 'Run independent check'}</button>
        </form>

        <div className="panel result-panel">
          {result ? <>
            <div className="result-header"><span className={`status-pill ${result.result === 'AUTHENTIC' ? 'success' : result.result === 'REVOKED' || result.result === 'TAMPERED' ? 'danger' : 'neutral'}`}>{result.result.replaceAll('_', ' ')}</span><small>{result.certificate_id}</small></div>
            <h3>{result.message}</h3>
            <dl className="evidence-list"><div><dt>Issuer</dt><dd>{result.institution ?? 'Not confirmed'}</dd></div><div><dt>Document hash</dt><dd>{result.document_integrity}</dd></div><div><dt>Blockchain evidence</dt><dd>{result.blockchain_status.replaceAll('_', ' ')}</dd></div><div><dt>AI risk</dt><dd>{result.ai_analysis.analysis_status === 'NOT_ASSESSED' ? 'Not assessed' : `${result.ai_analysis.risk_category} · ${result.ai_analysis.risk_score ?? 'N/A'}/100`}</dd></div></dl>
            {result.attestation && <div className="attestation-actions"><img src={`${apiOrigin}/public/verify/${result.attestation.verification_id}/qr.png`} alt="Attestation QR code" /><div><strong>{result.attestation.verification_id}</strong><a href={result.attestation.public_url} target="_blank" rel="noreferrer">Open public attestation</a><a href={`${apiOrigin}/api/attestations/${result.attestation.verification_id}/report.pdf`}>Download report</a></div></div>}
          </> : <div className="empty-state"><ShieldAlert size={32} /><p>A certificate ID alone can locate issuer records. Upload the document to compare its hash and issue a signed attestation.</p></div>}
        </div>
      </div>
      <section className="panel"><div className="section-heading-row"><h2>Verification history</h2><span className="status-pill neutral">{history.length} checks</span></div>{history.length === 0 ? <p className="muted-copy">Checks performed while signed in will appear here.</p> : <div className="list-stack">{history.map((item) => <div className="list-item" key={item.verification_id}><div><strong>{item.certificate_id}</strong><small>{new Date(item.checked_at).toLocaleString()}</small></div><span className={`pill ${item.result === 'AUTHENTIC' ? 'positive' : item.result === 'TAMPERED' || item.result === 'REVOKED' ? 'negative' : 'warning'}`}>{item.result.replaceAll('_', ' ')}</span></div>)}</div>}</section>
    </DashboardShell>
  )
}

function DashboardShell({
  user,
  onLogout,
  children,
}: {
  user: User
  onLogout: () => void
  children: React.ReactNode
}) {
  return (
    <div className="dashboard-shell">
      <aside className="sidebar panel">
        <div className="brand-wrap">
          <div className="brand-mark">C</div>
          <div>
            <div className="brand-name">CertiChain</div>
            <div className="brand-sub">{user.role}</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <Link to="/dashboard">Overview</Link>
          <Link to="/verify">Verification</Link>
          <Link to="/about">About</Link>
        </nav>

        <div className="user-card">
          <div className="user-dot" />
          <div>
            <strong>{user.name}</strong>
            <small>{user.email}</small>
          </div>
        </div>

        <button type="button" className="secondary-button sidebar-action" onClick={onLogout}>
          <LogOut size={16} /> Logout
        </button>
      </aside>

      <main className="dashboard-main">{children}</main>
    </div>
  )
}

export default App
