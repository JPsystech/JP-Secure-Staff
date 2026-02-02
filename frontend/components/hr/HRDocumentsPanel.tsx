'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiRequest, apiFetch } from '@/lib/api'
import { FileText, Download, Eye, Loader2, Upload, Package, Mail, Edit, Save } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/components/ui/use-toast'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

interface DocumentStatus {
  canGenerate: boolean
  templateKeyUsed: string | null
  lastGeneratedAt: string | null
  lastDocumentId?: number | null
  missingRatePlan?: boolean
  missingKyc?: boolean
  missingEmployment?: boolean
  missingTemplate?: boolean
  missingCompany?: boolean
}

interface DocumentsStatus {
  appointment: DocumentStatus
  declaration: DocumentStatus
}

interface HRDocumentsPanelProps {
  personId: string
}

interface HRDocument {
  id: number
  doc_name: string
  doc_category: string
  file_key: string
  created_at: string
}

export default function HRDocumentsPanel({ personId }: HRDocumentsPanelProps) {
  const { toast } = useToast()
  const [status, setStatus] = useState<DocumentsStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState<string | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [previewDocType, setPreviewDocType] = useState<string | null>(null)
  const [previewHtml, setPreviewHtml] = useState<string>('')
  const [hrDocuments, setHrDocuments] = useState<HRDocument[]>([])
  const [uploadingDoc, setUploadingDoc] = useState(false)
  const [savedDocIds, setSavedDocIds] = useState<{appointment?: number, declaration?: number}>({})
  const [publishing, setPublishing] = useState<string | null>(null)
  const [signedDocType, setSignedDocType] = useState<string>('')
  const [generatingPack, setGeneratingPack] = useState(false)
  const [sendingPack, setSendingPack] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [editDocType, setEditDocType] = useState<'APPOINTMENT' | 'DECLARATION' | null>(null)
  const [editContent, setEditContent] = useState('')
  const [savingDraft, setSavingDraft] = useState(false)
  const [loadingEditContent, setLoadingEditContent] = useState(false)

  useEffect(() => {
    fetchStatus()
    fetchHrDocuments()
  }, [personId])
  
  const fetchHrDocuments = async () => {
    try {
      const response = await apiRequest<{categories: Record<string, HRDocument[]>, total_count: number}>(`/cv-wallet/persons/${personId}/finance-hr-docs`)
      if (response.data) {
        // Filter only HR documents (APPOINTMENT, DECLARATION, HR_SIGNED, ID_CARD)
        const hrDocs = Object.values(response.data.categories || {}).flat().filter((doc: any) => 
          ['APPOINTMENT', 'DECLARATION', 'HR_SIGNED', 'ID_CARD'].includes(doc.doc_category)
        )
        setHrDocuments(hrDocs)
        
        // Track saved document IDs
        const appointmentDoc = hrDocs.find((doc: any) => doc.doc_category === 'APPOINTMENT')
        const declarationDoc = hrDocs.find((doc: any) => doc.doc_category === 'DECLARATION')
        setSavedDocIds({
          appointment: appointmentDoc?.id,
          declaration: declarationDoc?.id
        })
      }
    } catch (err) {
      console.error('Failed to fetch HR documents')
      setHrDocuments([])
    }
  }
  
  const handlePublish = async (docType: 'APPOINTMENT' | 'DECLARATION') => {
    setPublishing(docType)
    try {
      const response = await apiRequest<{id: number, doc_name: string, file_key: string}>(`/hr/persons/${personId}/publish/${docType.toLowerCase()}`, {
        method: 'POST',
      })
      
      if (response.data) {
        toast({
          title: 'Success',
          description: `${docType} published and saved successfully`,
        })
        fetchHrDocuments()
        setSavedDocIds(prev => ({
          ...prev,
          [docType.toLowerCase()]: response.data?.id
        }))
      }
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err.message || 'Failed to publish document',
        variant: 'destructive',
      })
    } finally {
      setPublishing(null)
    }
  }
  
  const handleDownload = async (docType: 'APPOINTMENT' | 'DECLARATION') => {
    if (docType === 'APPOINTMENT') {
      // For Appointment Letter: Use system-generated PDF endpoint (on-the-fly generation)
      try {
        const response = await apiFetch(`/hr/persons/${personId}/download/appointment`)
        
        if (response.ok) {
          const blob = await response.blob()
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          
          // Get filename from Content-Disposition header or use default
          const contentDisposition = response.headers.get('Content-Disposition')
          const filename = contentDisposition 
            ? contentDisposition.split('filename=')[1]?.replace(/"/g, '') 
            : `Appointment_Letter_${personId}.pdf`
          a.download = filename
          
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)
          toast({
            title: 'Success',
            description: 'Appointment letter downloaded successfully',
          })
        } else {
          const errorData = await response.json().catch(() => ({ detail: 'Download failed' }))
          throw new Error(errorData.detail || 'Download failed')
        }
      } catch (err: any) {
        toast({
          title: 'Error',
          description: err.message || 'Failed to download appointment letter',
          variant: 'destructive',
        })
      }
    } else {
      // For Declaration: Check if saved document exists, otherwise publish first
      const docId = savedDocIds.declaration
      
      if (docId) {
        // Download from saved HR document via HR endpoint
        try {
          const response = await apiFetch(`/hr/documents/${docId}/download`)
          
          if (response.ok) {
            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `Declaration_${personId}.pdf`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
            toast({
              title: 'Success',
              description: 'Document downloaded successfully',
            })
          } else {
            throw new Error('Download failed')
          }
        } catch (err: any) {
          toast({
            title: 'Error',
            description: 'Failed to download document',
            variant: 'destructive',
          })
        }
      } else {
        // Publish first, then download
        await handlePublish(docType)
        // After publish, download will be available
        setTimeout(() => {
          fetchHrDocuments().then(() => {
            const newDocId = savedDocIds.declaration
            if (newDocId) {
              handleDownload(docType)
            }
          })
        }, 500)
      }
    }
  }

  const fetchStatus = async () => {
    setLoading(true)
    try {
      const response = await apiRequest<DocumentsStatus>(`/hr/persons/${personId}/documents`)
      if (response.data) {
        setStatus(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch document status', err)
      toast({
        title: 'Error',
        description: 'Failed to load document status',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const hasAppointmentDoc = !!(savedDocIds.appointment ?? status?.appointment?.lastDocumentId)
  const hasDeclarationDoc = !!(savedDocIds.declaration ?? status?.declaration?.lastDocumentId)
  const canSendPack = hasAppointmentDoc && hasDeclarationDoc

  const handleGenerateHrPack = async () => {
    setGeneratingPack(true)
    try {
      const response = await apiRequest<{ documents: { id: number; doc_name: string; doc_category: string }[] }>(
        `/hr/persons/${personId}/generate-hr-pack`,
        { method: 'POST' }
      )
      if (response.data?.documents?.length) {
        toast({
          title: 'Success',
          description: `Generated ${response.data.documents.length} document(s): Appointment & Declaration`,
        })
        fetchStatus()
        fetchHrDocuments()
      }
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err?.message || 'Failed to generate HR pack',
        variant: 'destructive',
      })
    } finally {
      setGeneratingPack(false)
    }
  }

  const handleSendToPerson = async () => {
    if (!canSendPack) return
    setSendingPack(true)
    try {
      const response = await apiRequest<{ sent: boolean }>(`/hr/persons/${personId}/send-hr-pack`, {
        method: 'POST',
        body: JSON.stringify({}),
      })
      if (response.data?.sent) {
        toast({
          title: 'Success',
          description: 'Appointment & Declaration sent to person\'s email',
        })
      }
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err?.message || 'Failed to send HR pack',
        variant: 'destructive',
      })
    } finally {
      setSendingPack(false)
    }
  }

  const handleGenerate = async (docType: 'APPOINTMENT' | 'DECLARATION') => {
    setGenerating(docType)
    try {
      const response = await apiFetch(`/hr/persons/${personId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ docType }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to generate document')
      }

      // Download the PDF
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${docType === 'APPOINTMENT' ? 'AppointmentLetter' : 'Declaration'}_${personId}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast({
        title: 'Success',
        description: `${docType} generated and downloaded successfully`,
      })

      // Refresh status and documents
      fetchStatus()
      fetchHrDocuments()
    } catch (err: any) {
      console.error('Failed to generate document', err)
      toast({
        title: 'Error',
        description: err.message || 'Failed to generate document',
        variant: 'destructive',
      })
    } finally {
      setGenerating(null)
    }
  }

  const handlePreview = async (docType: 'APPOINTMENT' | 'DECLARATION') => {
    setPreviewDocType(docType)
    setPreviewOpen(true)
    setPreviewHtml('') // Clear previous preview
    try {
      const response = await apiFetch(`/hr/persons/${personId}/preview/${docType.toLowerCase()}`)
      if (response.ok) {
        const html = await response.text()
        setPreviewHtml(html)
      } else {
        // Get error message from backend
        let errorMessage = 'Failed to load preview'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorMessage
        } catch (jsonError) {
          // If response is not JSON, use status text
          errorMessage = response.statusText || errorMessage
        }
        throw new Error(errorMessage)
      }
    } catch (err: any) {
      console.error('Failed to load preview', err)
      toast({
        title: 'Error',
        description: err.message || 'Failed to load preview',
        variant: 'destructive',
      })
      setPreviewOpen(false) // Close dialog on error
    }
  }

  const handleOpenEdit = async (docType: 'APPOINTMENT' | 'DECLARATION') => {
    setEditDocType(docType)
    setEditOpen(true)
    setEditContent('')
    setLoadingEditContent(true)
    try {
      const draftRes = await apiFetch(`/hr/persons/${personId}/draft/${docType}`)
      if (draftRes.ok) {
        const data = await draftRes.json()
        setEditContent(data.content || '')
      } else {
        const previewRes = await apiFetch(`/hr/persons/${personId}/preview/${docType.toLowerCase()}`)
        if (previewRes.ok) {
          const html = await previewRes.text()
          setEditContent(html)
        }
      }
    } catch {
      toast({ title: 'Error', description: 'Failed to load content for editing', variant: 'destructive' })
    } finally {
      setLoadingEditContent(false)
    }
  }

  const handleSaveDraft = async () => {
    if (!editDocType) return
    setSavingDraft(true)
    try {
      const response = await apiRequest<{ saved: boolean }>(
        `/hr/persons/${personId}/draft/${editDocType}`,
        { method: 'PUT', body: JSON.stringify({ content: editContent }) }
      )
      if (response.data?.saved) {
        toast({ title: 'Draft saved', description: 'Generate & Save will use this content for the PDF.' })
      }
    } catch (err: any) {
      toast({ title: 'Error', description: err?.message || 'Failed to save draft', variant: 'destructive' })
    } finally {
      setSavingDraft(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>HR Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-20 bg-gray-100 animate-pulse rounded" />
            <div className="h-20 bg-gray-100 animate-pulse rounded" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!status) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>HR Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">Unable to load document status</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>HR Documents</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Generate HR Pack + Send to Person */}
          <div className="border rounded-lg p-4 space-y-3 bg-muted/30">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                onClick={handleGenerateHrPack}
                disabled={!status.appointment.canGenerate || !status.declaration.canGenerate || generatingPack}
              >
                {generatingPack ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Package className="w-4 h-4 mr-2" />
                    Generate HR Pack
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={handleSendToPerson}
                disabled={!canSendPack || sendingPack}
              >
                {sendingPack ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Mail className="w-4 h-4 mr-2" />
                    Send to Person
                  </>
                )}
              </Button>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
              <span>Appointment: {hasAppointmentDoc ? <Badge variant="default" className="text-xs">Ready</Badge> : <Badge variant="secondary">Missing</Badge>}</span>
              <span>Declaration: {hasDeclarationDoc ? <Badge variant="default" className="text-xs">Ready</Badge> : <Badge variant="secondary">Missing</Badge>}</span>
              {!canSendPack && (
                <span className="text-amber-600">Generate both documents before sending.</span>
              )}
            </div>
          </div>

          {/* Appointment Letter */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-gray-600" />
                <h3 className="font-semibold">Appointment Letter</h3>
              </div>
              {hasAppointmentDoc ? (
                <Badge variant="default">Ready</Badge>
              ) : status.appointment.canGenerate ? (
                <Badge variant="secondary">Not Generated</Badge>
              ) : (
                <Badge variant="secondary">Not Available</Badge>
              )}
            </div>
            {status.appointment.lastGeneratedAt && (
              <p className="text-xs text-gray-500">
                Last generated: {new Date(status.appointment.lastGeneratedAt).toLocaleString()}
              </p>
            )}
            {!status.appointment.canGenerate && (
              <div className="text-xs text-gray-500 space-y-1">
                {status.appointment.missingEmployment && <p>• Missing Employment record</p>}
                {status.appointment.missingKyc && <p>• Missing Finance KYC</p>}
                {status.appointment.missingRatePlan && <p>• Missing Rate Plan</p>}
                {status.appointment.missingCompany && <p>• Missing Company assignment</p>}
                {status.appointment.missingTemplate && (
                  <p className="flex items-center gap-1 flex-wrap">
                    <span>• Missing Appointment template.</span>
                    <Link href="/admin/templates" className="text-primary underline hover:no-underline font-medium">Add in Admin → Templates</Link>
                  </p>
                )}
                {!status.appointment.missingEmployment && !status.appointment.missingKyc && 
                 !status.appointment.missingRatePlan && !status.appointment.missingCompany && 
                 !status.appointment.missingTemplate && <p>Finance processing required</p>}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePreview('APPOINTMENT')}
                disabled={!status.appointment.canGenerate}
              >
                <Eye className="w-4 h-4 mr-2" />
                Preview
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleOpenEdit('APPOINTMENT')}
                disabled={!status.appointment.canGenerate}
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePublish('APPOINTMENT')}
                disabled={!status.appointment.canGenerate || publishing === 'APPOINTMENT'}
              >
                {publishing === 'APPOINTMENT' ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Publishing...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4 mr-2" />
                    Generate & Save
                  </>
                )}
              </Button>
              <Button
                size="sm"
                onClick={() => handleDownload('APPOINTMENT')}
                disabled={!status.appointment.canGenerate || (publishing === 'APPOINTMENT' || generating === 'APPOINTMENT')}
              >
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </Button>
            </div>
          </div>

          {/* Declaration */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-gray-600" />
                <h3 className="font-semibold">Declaration</h3>
              </div>
              {hasDeclarationDoc ? (
                <Badge variant="default">Ready</Badge>
              ) : status.declaration.canGenerate ? (
                <Badge variant="secondary">Not Generated</Badge>
              ) : (
                <Badge variant="secondary">Not Available</Badge>
              )}
            </div>
            {status.declaration.lastGeneratedAt && (
              <p className="text-xs text-gray-500">
                Last generated: {new Date(status.declaration.lastGeneratedAt).toLocaleString()}
              </p>
            )}
            {!status.declaration.canGenerate && (
              <div className="text-xs text-gray-500 space-y-1">
                {status.declaration.missingEmployment && <p>• Missing Employment record</p>}
                {status.declaration.missingKyc && <p>• Missing Finance KYC</p>}
                {status.declaration.missingCompany && <p>• Missing Company assignment</p>}
                {status.declaration.missingTemplate && (
                  <p className="flex items-center gap-1 flex-wrap">
                    <span>• Missing DECLARATION template.</span>
                    <Link
                      href="/admin/templates"
                      className="text-primary underline hover:no-underline font-medium"
                    >
                      Add DECLARATION in Admin → Templates
                    </Link>
                  </p>
                )}
                {!status.declaration.missingEmployment && !status.declaration.missingKyc && 
                 !status.declaration.missingCompany && !status.declaration.missingTemplate && 
                 <p>Finance processing required</p>}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePreview('DECLARATION')}
                disabled={!status.declaration.canGenerate}
              >
                <Eye className="w-4 h-4 mr-2" />
                Preview
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleOpenEdit('DECLARATION')}
                disabled={!status.declaration.canGenerate}
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePublish('DECLARATION')}
                disabled={!status.declaration.canGenerate || publishing === 'DECLARATION'}
              >
                {publishing === 'DECLARATION' ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Publishing...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4 mr-2" />
                    Generate & Save
                  </>
                )}
              </Button>
              <Button
                size="sm"
                onClick={() => handleDownload('DECLARATION')}
                disabled={!status.declaration.canGenerate || (publishing === 'DECLARATION' || generating === 'DECLARATION')}
              >
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </Button>
            </div>
          </div>
          
          {/* Upload Signed Documents */}
          <div className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold">Upload Signed Documents</h3>
            </div>
            <div className="space-y-2">
              <Label>Document Type</Label>
              <Select value={signedDocType} onValueChange={setSignedDocType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select document type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="HR_SIGNED">Signed Appointment Letter (HR_SIGNED)</SelectItem>
                  <SelectItem value="APPOINTMENT">Signed Appointment Letter (APPOINTMENT)</SelectItem>
                  <SelectItem value="DECLARATION">Signed Declaration (DECLARATION)</SelectItem>
                  <SelectItem value="ID_CARD">ID Card</SelectItem>
                  <SelectItem value="OTHER">Other HR Document</SelectItem>
                </SelectContent>
              </Select>
              <Label>Upload File</Label>
              <div className="flex gap-2">
                <Input
                  type="file"
                  id="hr-upload"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={async (e) => {
                    const file = e.target.files?.[0]
                    if (!file) return
                    
                    if (!signedDocType) {
                      toast({
                        title: 'Error',
                        description: 'Please select document type first',
                        variant: 'destructive',
                      })
                      return
                    }
                    
                    setUploadingDoc(true)
                    try {
                      const formDataObj = new FormData()
                      formDataObj.append('file', file)
                      formDataObj.append('stage', 'HR')
                      formDataObj.append('doc_category', signedDocType)  // Use doc_category enum value
                      formDataObj.append('doc_name', signedDocType === 'HR_SIGNED' ? 'Signed Appointment Letter' : 
                                                      signedDocType === 'APPOINTMENT' ? 'Signed Appointment Letter' :
                                                      signedDocType === 'DECLARATION' ? 'Signed Declaration' :
                                                      signedDocType === 'ID_CARD' ? 'ID Card' : 'Other HR Document')
                      
                      const response = await apiFetch(`/persons/${personId}/documents`, {
                        method: 'POST',
                        body: formDataObj,
                      })
                      
                      if (response.ok) {
                        toast({
                          title: 'Success',
                          description: 'Document uploaded successfully',
                        })
                        fetchHrDocuments()
                      } else {
                        const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
                        toast({
                          title: 'Error',
                          description: error.detail || 'Failed to upload document',
                          variant: 'destructive',
                        })
                      }
                    } catch (err: any) {
                      toast({
                        title: 'Error',
                        description: err.message || 'Failed to upload document',
                        variant: 'destructive',
                      })
                    } finally {
                      setUploadingDoc(false)
                      e.target.value = ''
                    }
                  }}
                  disabled={uploadingDoc}
                  className="hidden"
                />
                <label htmlFor="hr-upload">
                  <Button
                    type="button"
                    variant="outline"
                    disabled={uploadingDoc}
                    asChild
                  >
                    <span>
                      <Upload className="w-4 h-4 mr-2" />
                      {uploadingDoc ? 'Uploading...' : 'Upload Document'}
                    </span>
                  </Button>
                </label>
              </div>
            </div>
          </div>
          
          {/* Generated/Uploaded Documents List */}
          {hrDocuments.length > 0 && (
            <div className="border rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-gray-600" />
                <h3 className="font-semibold">HR Documents</h3>
              </div>
              <div className="space-y-2">
                {hrDocuments.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-2 border rounded">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="text-sm">{doc.doc_name}</span>
                      <Badge variant="outline" className="text-xs">
                        {doc.doc_category.replace(/_/g, ' ')}
                      </Badge>
                      <Badge variant="secondary" className="text-xs">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </Badge>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={async () => {
                        try {
                          const response = await apiFetch(`/hr/documents/${doc.id}/download`)
                          
                          if (response.ok) {
                            const blob = await response.blob()
                            const url = window.URL.createObjectURL(blob)
                            const a = document.createElement('a')
                            a.href = url
                            a.download = doc.doc_name
                            document.body.appendChild(a)
                            a.click()
                            window.URL.revokeObjectURL(url)
                            document.body.removeChild(a)
                          }
                        } catch (err) {
                          toast({
                            title: 'Error',
                            description: 'Failed to download document',
                            variant: 'destructive',
                          })
                        }
                      }}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Preview {previewDocType === 'APPOINTMENT' ? 'Appointment Letter' : 'Declaration'}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4">
            {previewHtml ? (
              <iframe
                srcDoc={previewHtml}
                className="w-full h-[75vh] border rounded"
                title="Document Preview"
                sandbox="allow-same-origin"
              />
            ) : (
              <div className="flex items-center justify-center h-[600px]">
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit content modal – save as draft; Generate & Save uses this for PDF */}
      <Dialog open={editOpen} onOpenChange={(open) => { setEditOpen(open); if (!open) { setEditDocType(null); setEditContent(''); } }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Edit {editDocType === 'APPOINTMENT' ? 'Appointment Letter' : 'Declaration'} (draft)
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Edit the HTML below. Save draft to use this content when you click Generate & Save. Base template is not changed.
          </p>
          {loadingEditContent ? (
            <div className="flex items-center justify-center h-[400px]">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={18}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono"
                placeholder="HTML content..."
              />
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditOpen(false)}>Cancel</Button>
                <Button onClick={handleSaveDraft} disabled={savingDraft}>
                  {savingDraft ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                  Save draft
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}

