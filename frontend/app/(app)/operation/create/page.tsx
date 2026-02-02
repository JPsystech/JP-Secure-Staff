'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { PageShell } from '@/components/common/PageShell'
import { DataCard } from '@/components/common/DataCard'
import { apiRequest, apiFetch } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { Upload, X, FileText, AlertCircle, CheckCircle2, Circle, Loader2 } from 'lucide-react'

interface DocumentFile {
  id: string
  file: File
  docName: string
  isMandatory: boolean
}

interface AdditionalDoc {
  id: string
  docName: string
  file: File | null
}

const formatError = (err: any): string => {
  if (!err) return 'Unknown error'
  if (typeof err === 'string') return err
  if (typeof err.message === 'string') return err.message
  if (typeof err.detail === 'string') return err.detail
  if (Array.isArray(err.detail)) {
    return err.detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
  }
  try {
    return JSON.stringify(err)
  } catch {
    return String(err)
  }
}

// Stage-A validation: name, mobile (exactly 10 digits), email (required + format)
const MOBILE_REGEX = /^[0-9]{10}$/
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function validateCreatePerson(data: { name: string; mobile: string; email: string }): { name?: string; mobile?: string; email?: string } {
  const errors: { name?: string; mobile?: string; email?: string } = {}
  if (!data.name?.trim()) errors.name = 'Name is required'
  const mobileClean = (data.mobile || '').replace(/\s/g, '')
  if (!mobileClean) errors.mobile = 'Mobile number is required'
  else if (!MOBILE_REGEX.test(mobileClean)) errors.mobile = 'Mobile must be exactly 10 digits (digits only)'
  if (!data.email?.trim()) errors.email = 'Email is required'
  else if (!EMAIL_REGEX.test(data.email.trim())) errors.email = 'Invalid email format'
  return errors
}

export default function CreatePersonPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [formData, setFormData] = useState({
    name: '',
    mobile: '',
    alt_mobile: '',
    email: '',
    dob: '',
    stream: '',
    stream_other: '',
    education: '',
    education_other: '',
    location: '',
  })
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [qualificationFile, setQualificationFile] = useState<File | null>(null)
  const [additionalDocs, setAdditionalDocs] = useState<AdditionalDoc[]>([])
  const [loading, setLoading] = useState(false)
  const [duplicateAlert, setDuplicateAlert] = useState<{show: boolean, data: any}>({show: false, data: null})
  const [fieldErrors, setFieldErrors] = useState<{ name?: string; mobile?: string; email?: string }>({})

  const validationErrors = validateCreatePerson({
    name: formData.name,
    mobile: formData.mobile,
    email: formData.email,
  })
  const isFormValid = !validationErrors.name && !validationErrors.mobile && !validationErrors.email

  const handleSubmit = async (submitToFinance: boolean = true) => {
    setDuplicateAlert({ show: false, data: null })
    const errors = validateCreatePerson({
      name: formData.name,
      mobile: formData.mobile,
      email: formData.email,
    })
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) {
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors below (Name, Mobile, Email are required; Mobile must be 10 digits; Email must be valid).',
        variant: 'destructive',
      })
      return
    }

    // Validate mandatory documents
    if (submitToFinance && (!cvFile || !qualificationFile)) {
      toast({
        title: "Missing Documents",
        description: "CV and Qualification Certificate are mandatory. Please upload both before submitting.",
        variant: "destructive",
      })
      return
    }
    
    setLoading(true)

    try {
      // Create person
      const personResponse = await apiRequest('/persons', {
        method: 'POST',
        body: JSON.stringify({
          ...formData,
          mobile: formData.mobile.replace(/\s/g, ''),
          email: formData.email.trim(),
          dob: formData.dob || null,
          stream: formData.stream || null,
          education: formData.education || null,
        }),
      })

      if (personResponse.error) {
        const errorStr = typeof personResponse.error === 'string'
          ? personResponse.error
          : formatError(personResponse.error)
        // Backend 422 validation: map field errors from detail array
        const raw = personResponse.error as any
        if (raw?.detail && Array.isArray(raw.detail)) {
          const errMap: { name?: string; mobile?: string; email?: string } = {}
          for (const e of raw.detail) {
            const loc = (e.loc && e.loc[e.loc.length - 1]) as string
            const msg = e.msg || e.message
            if (loc === 'name') errMap.name = msg
            else if (loc === 'mobile') errMap.mobile = msg
            else if (loc === 'email') errMap.email = msg
          }
          if (Object.keys(errMap).length > 0) {
            setFieldErrors(errMap)
            toast({ title: 'Validation Error', description: 'Please fix the errors below.', variant: 'destructive' })
            setLoading(false)
            return
          }
        }
        if (errorStr.includes('409') || errorStr.includes('Duplicate')) {
          try {
            const errorObj = typeof errorStr === 'string' ? JSON.parse(errorStr) : personResponse.error
            const detail = (errorObj as any)?.detail
            const duplicateData = Array.isArray(detail) ? undefined : (detail || errorObj)
            if (duplicateData?.existing_person_id ?? errorObj?.existing_person_id) {
              setDuplicateAlert({ show: true, data: duplicateData || errorObj })
              setLoading(false)
              return
            }
          } catch {}
        }
        toast({
          title: "Error",
          description: errorStr,
          variant: "destructive",
        })
        setLoading(false)
        return
      }

      if (!personResponse.data) {
        toast({
          title: "Error",
          description: "Failed to create person",
          variant: "destructive",
        })
        setLoading(false)
        return
      }

      const personId = (personResponse.data as { id: string }).id

      // Upload documents
      const allDocs: DocumentFile[] = []
      if (cvFile) {
        allDocs.push({ id: 'cv', file: cvFile, docName: 'CV', isMandatory: true })
      }
      if (qualificationFile) {
        allDocs.push({ id: 'qual', file: qualificationFile, docName: 'Qualification Certificate', isMandatory: true })
      }
      additionalDocs.forEach(doc => {
        if (doc.file) {
          allDocs.push({ id: doc.id, file: doc.file, docName: doc.docName, isMandatory: false })
        }
      })

      let uploadErrors = []
      for (const doc of allDocs) {
        const formDataObj = new FormData()
        formDataObj.append('file', doc.file)
        formDataObj.append('stage', 'OPERATION')
        formDataObj.append('doc_name', doc.docName)
        formDataObj.append('is_mandatory', doc.isMandatory.toString())

        try {
          const response = await apiFetch(`/persons/${personId}/documents`, {
            method: 'POST',
            body: formDataObj,
          })

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }))
            uploadErrors.push({ name: doc.docName, error: errorData.detail || 'Upload failed' })
            console.error(`Upload failed for ${doc.docName}:`, errorData)
          }
        } catch (err: any) {
          uploadErrors.push({ name: doc.docName, error: err.message || 'Network error' })
          console.error(`Upload error for ${doc.docName}:`, err)
        }
      }

      if (uploadErrors.length > 0) {
        const errorNames = uploadErrors.map(e => typeof e === 'string' ? e : e.name).join(', ')
        const errorMessages = uploadErrors.map(e => typeof e === 'string' ? '' : e.error).filter(Boolean).join('; ')
        toast({
          title: 'Upload Warning',
          description: `${uploadErrors.length} document(s) failed to upload: ${errorNames}${errorMessages ? `. Errors: ${errorMessages}` : ''}`,
          variant: 'destructive',
        })
        console.warn('Some documents failed to upload:', uploadErrors)
      } else {
        // All uploads succeeded
        toast({
          title: 'Success',
          description: 'All documents uploaded successfully',
        })
      }

      // Submit to finance if requested
      if (submitToFinance) {
        const submitResponse = await apiRequest(`/persons/${personId}/submit-to-finance`, {
          method: 'POST',
        })

        if (submitResponse.error) {
          const errMsg = formatError(submitResponse.error)
          toast({
            title: "Error",
            description: `Failed to submit to finance: ${errMsg}`,
            variant: "destructive",
          })
          setLoading(false)
          return
        }

        toast({
          title: "Success",
          description: uploadErrors.length > 0 
            ? `Person created and submitted to Finance. ${uploadErrors.length} document(s) failed to upload.`
            : "Person created and submitted to Finance successfully.",
        })

        // Reset form
        setFormData({
          name: '', mobile: '', alt_mobile: '', email: '', dob: '',
          stream: '', stream_other: '', education: '', education_other: '', location: '',
        })
        setCvFile(null)
        setQualificationFile(null)
        setAdditionalDocs([])
      } else {
        toast({
          title: "Draft Saved",
          description: "Person saved as draft. Submit to Finance when ready.",
        })
      }
    } catch (err: any) {
      toast({
        title: "Error",
        description: formatError(err),
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const addAdditionalDoc = () => {
    setAdditionalDocs([...additionalDocs, { id: Date.now().toString(), docName: '', file: null }])
  }

  const removeAdditionalDoc = (id: string) => {
    setAdditionalDocs(additionalDocs.filter(doc => doc.id !== id))
  }

  const updateAdditionalDoc = (id: string, field: 'docName' | 'file', value: string | File | null) => {
    setAdditionalDocs(additionalDocs.map(doc => 
      doc.id === id ? { ...doc, [field]: value } : doc
    ))
  }

  return (
    <PageShell
      title="Create New Person"
      subtitle="Stage-A (Operations) • Create profile and upload documents"
      actions={
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleSubmit(false)}
            disabled={true}
            title="Draft saving coming soon"
          >
            Save Draft
          </Button>
          <Button
            onClick={() => handleSubmit(true)}
            disabled={loading || !isFormValid}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit to Finance'
            )}
          </Button>
        </div>
      }
    >

      {/* Duplicate Alert */}
      {duplicateAlert.show && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Possible duplicate profile found</AlertTitle>
          <AlertDescription className="mt-2">
            <div className="space-y-2">
              <p>A person with similar details already exists in the system.</p>
              {duplicateAlert.data?.existing_employee_code && (
                <p className="font-medium">Employee Code: {duplicateAlert.data.existing_employee_code}</p>
              )}
              <div className="flex gap-2 mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setDuplicateAlert({show: false, data: null})}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    if (duplicateAlert.data?.existing_person_id) {
                      router.push(`/cv-wallet?person=${duplicateAlert.data.existing_person_id}`)
                    } else {
                      router.push('/cv-wallet')
                    }
                  }}
                >
                  Open Profile
                </Button>
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6">
        {/* Person Information */}
        <DataCard title="Person Information" description="Basic profile details for the new person">
            <form onSubmit={(e) => { e.preventDefault(); handleSubmit(true); }} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="name">
                    Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => {
                      setFormData({ ...formData, name: e.target.value })
                      if (fieldErrors.name) setFieldErrors((prev) => ({ ...prev, name: undefined }))
                    }}
                    className={`w-full ${fieldErrors.name ? 'border-destructive' : ''}`}
                    aria-invalid={!!fieldErrors.name}
                  />
                  {fieldErrors.name && (
                    <p className="text-sm text-destructive">{fieldErrors.name}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="mobile">
                    Mobile <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="mobile"
                    value={formData.mobile}
                    onChange={(e) => {
                      const v = e.target.value.replace(/\D/g, '').slice(0, 10)
                      setFormData({ ...formData, mobile: v })
                      if (fieldErrors.mobile) setFieldErrors((prev) => ({ ...prev, mobile: undefined }))
                    }}
                    placeholder="10 digits"
                    maxLength={10}
                    className={`w-full ${fieldErrors.mobile ? 'border-destructive' : ''}`}
                    aria-invalid={!!fieldErrors.mobile}
                  />
                  {fieldErrors.mobile && (
                    <p className="text-sm text-destructive">{fieldErrors.mobile}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="alt_mobile">Alternate Mobile</Label>
                  <Input
                    id="alt_mobile"
                    value={formData.alt_mobile}
                    onChange={(e) => setFormData({ ...formData, alt_mobile: e.target.value })}
                    className="w-full"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">
                    Email <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => {
                      setFormData({ ...formData, email: e.target.value })
                      if (fieldErrors.email) setFieldErrors((prev) => ({ ...prev, email: undefined }))
                    }}
                    className={`w-full ${fieldErrors.email ? 'border-destructive' : ''}`}
                    aria-invalid={!!fieldErrors.email}
                  />
                  {fieldErrors.email && (
                    <p className="text-sm text-destructive">{fieldErrors.email}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dob">Date of Birth</Label>
                  <Input
                    id="dob"
                    type="date"
                    value={formData.dob}
                    onChange={(e) => setFormData({...formData, dob: e.target.value})}
                    className="w-full"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    value={formData.location}
                    onChange={(e) => setFormData({...formData, location: e.target.value})}
                    className="w-full"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="stream">Stream</Label>
                  <Select value={formData.stream} onValueChange={(value) => setFormData({...formData, stream: value})}>
                    <SelectTrigger id="stream" className="w-full">
                      <SelectValue placeholder="Select Stream" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="MECH">MECH</SelectItem>
                      <SelectItem value="CIVIL">CIVIL</SelectItem>
                      <SelectItem value="ELEC">ELEC</SelectItem>
                      <SelectItem value="OTHER">OTHER</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {formData.stream === 'OTHER' && (
                  <div className="space-y-2">
                    <Label htmlFor="stream_other">Specify Stream</Label>
                    <Input
                      id="stream_other"
                      value={formData.stream_other}
                      onChange={(e) => setFormData({...formData, stream_other: e.target.value})}
                      className="w-full"
                    />
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="education">Education</Label>
                  <Select value={formData.education} onValueChange={(value) => setFormData({...formData, education: value})}>
                    <SelectTrigger id="education" className="w-full">
                      <SelectValue placeholder="Select Education" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DIPLOMA">DIPLOMA</SelectItem>
                      <SelectItem value="DEGREE">DEGREE</SelectItem>
                      <SelectItem value="ME">ME</SelectItem>
                      <SelectItem value="OTHER">OTHER</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {formData.education === 'OTHER' && (
                  <div className="space-y-2">
                    <Label htmlFor="education_other">Specify Education</Label>
                    <Input
                      id="education_other"
                      value={formData.education_other}
                      onChange={(e) => setFormData({...formData, education_other: e.target.value})}
                      className="w-full"
                    />
                  </div>
                )}
              </div>
            </form>
        </DataCard>

        {/* Documents */}
        <DataCard title="Documents" description="Upload mandatory and optional documents">
          <div className="space-y-6">
            {/* Mandatory Documents Checklist */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-4">
              <Label className="text-sm font-semibold mb-3 block">Mandatory Documents Checklist</Label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {cvFile ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <Circle className="h-4 w-4 text-gray-400" />
                  )}
                  <span className={cvFile ? "text-sm text-green-700" : "text-sm text-gray-600"}>
                    CV Document {cvFile ? "(Uploaded)" : "(Required)"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {qualificationFile ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <Circle className="h-4 w-4 text-gray-400" />
                  )}
                  <span className={qualificationFile ? "text-sm text-green-700" : "text-sm text-gray-600"}>
                    Qualification Certificate {qualificationFile ? "(Uploaded)" : "(Required)"}
                  </span>
                </div>
              </div>
              {(!cvFile || !qualificationFile) && (
                <p className="text-xs text-amber-600 mt-2">
                  ⚠️ Both mandatory documents must be uploaded before submitting to Finance
                </p>
              )}
            </div>

            {/* Mandatory Uploads */}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>
                  CV <span className="text-red-500">*</span> <span className="text-sm text-gray-500">(Mandatory)</span>
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="file"
                    accept=".pdf,.doc,.docx"
                    onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                    className="flex-1"
                  />
                  {cvFile && (
                    <Badge variant="secondary" className="gap-1">
                      <FileText className="h-3 w-3" />
                      {cvFile.name}
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-gray-500">Upload CV document (PDF, DOC, DOCX)</p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>
                  Qualification Certificate <span className="text-red-500">*</span> <span className="text-sm text-gray-500">(Mandatory)</span>
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="file"
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    onChange={(e) => setQualificationFile(e.target.files?.[0] || null)}
                    className="flex-1"
                  />
                  {qualificationFile && (
                    <Badge variant="secondary" className="gap-1">
                      <FileText className="h-3 w-3" />
                      {qualificationFile.name}
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-gray-500">Upload qualification certificate</p>
              </div>
            </div>

            <Separator />

            {/* Additional Documents */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Additional Technical Documents</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addAdditionalDoc}
                >
                  + Add Technical Document
                </Button>
              </div>

              {additionalDocs.map((doc) => (
                <div key={doc.id} className="flex gap-2 items-end p-4 border rounded-lg">
                  <div className="flex-1 space-y-2">
                    <Label>Document Name</Label>
                    <Input
                      placeholder="Enter document name"
                      value={doc.docName}
                      onChange={(e) => updateAdditionalDoc(doc.id, 'docName', e.target.value)}
                    />
                  </div>
                  <div className="flex-1 space-y-2">
                    <Label>File</Label>
                    <Input
                      type="file"
                      onChange={(e) => updateAdditionalDoc(doc.id, 'file', e.target.files?.[0] || null)}
                    />
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeAdditionalDoc(doc.id)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </DataCard>
      </div>
    </PageShell>
  )
}

