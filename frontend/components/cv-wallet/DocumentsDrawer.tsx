'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { apiRequest } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { Download, FileText, Key } from 'lucide-react'
// Simple tooltip using title attribute for now

interface StageADocument {
  id: number
  file_name: string
  doc_type?: string
  doc_type_name?: string
  doc_category?: string
  doc_name?: string
  issue_date?: string
  expiry_date?: string
  uploaded_at: string
  download_url: string
  file_key?: string
  can_download: boolean
  download_block_reason?: string
  // Step-7/8: Enhanced access information (shared shape used by all doc groups)
  reason?: string  // STAGE_A_PUBLIC, OWNER_DEPT, NEEDS_GRANT, GRANT_EXPIRED, NO_PERMISSION, etc.
  grant_expires_at?: string  // ISO datetime string
  visibility_label?: string  // "Available", "Locked", "Expires in Xh Ym", etc.
  owner_dept?: string  // OPERATIONS, FINANCE, HR
}

interface DocumentsDrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  person: {
    id: string
    name: string
    employee_code?: string
    status?: string
  } | null
}

export function DocumentsDrawer({ open, onOpenChange, person }: DocumentsDrawerProps) {
  const [stageADocuments, setStageADocuments] = useState<StageADocument[]>([])
  const [financeDocuments, setFinanceDocuments] = useState<Array<{
    id: number
    doc_name: string
    doc_category: string
    owner_dept?: string
    created_at: string
    can_download?: boolean
    reason?: string
    grant_expires_at?: string
    visibility_label?: string
  }>>([])
  const [hrDocuments, setHrDocuments] = useState<Array<{
    id: number
    doc_name: string
    doc_category: string
    owner_dept?: string
    created_at: string
    can_download?: boolean
    reason?: string
    grant_expires_at?: string
    visibility_label?: string
  }>>([])
  const [loading, setLoading] = useState(false)
  const [loadingFinanceHr, setLoadingFinanceHr] = useState(false)
  const { toast } = useToast()
  const router = useRouter()

  useEffect(() => {
    if (open && person) {
      fetchDocuments()
      fetchFinanceHrDocuments()
    }
  }, [open, person])
  
  const fetchFinanceHrDocuments = async () => {
    if (!person) return
    setLoadingFinanceHr(true)
    try {
      const response = await apiRequest<{categories: Record<string, Array<{
        id: number
        doc_name: string
        doc_category: string
        owner_dept: string
        created_at: string
        can_download?: boolean
        reason?: string
        grant_expires_at?: string
        visibility_label?: string
      }>>, total_count: number}>(`/cv-wallet/persons/${person.id}/finance-hr-docs`)
      if (response.data) {
        const allDocs = Object.values(response.data.categories || {}).flat()
        const finance = allDocs.filter((doc: any) => doc.owner_dept === 'FINANCE')
        const hr = allDocs.filter((doc: any) => doc.owner_dept === 'HR')
        setFinanceDocuments(finance)
        setHrDocuments(hr)
      }
    } catch (err) {
      console.error('Failed to fetch Finance/HR documents:', err)
      setFinanceDocuments([])
      setHrDocuments([])
    } finally {
      setLoadingFinanceHr(false)
    }
  }

  const fetchDocuments = async () => {
    if (!person) return
    setLoading(true)
    try {
      // CV Wallet spec: Fetch ONLY Stage-A documents
      const response = await apiRequest<{items: StageADocument[]} | StageADocument[]>(`/cv-wallet/persons/${person.id}/stage-a-docs`)
      if (response.data) {
        console.log('Fetched Stage-A documents:', response.data)
        // Handle both {items: [...]} and [...] formats
        const items = Array.isArray(response.data) 
          ? response.data 
          : (response.data as any).items || []
        setStageADocuments(items)
      } else {
        setStageADocuments([])
      }
    } catch (err: any) {
      console.error('Failed to fetch Stage-A documents:', err)
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to fetch documents'
      const statusCode = err?.response?.status
      
      if (statusCode === 401) {
        toast({
          title: 'Authentication Error',
          description: 'Please log in again',
          variant: 'destructive',
        })
      } else if (statusCode === 500) {
        toast({
          title: 'Server Error',
          description: 'Server error occurred. Please try again later.',
          variant: 'destructive',
        })
      } else {
        toast({
          title: 'Error',
          description: errorMessage,
          variant: 'destructive',
        })
      }
      setStageADocuments([])
    } finally {
      setLoading(false)
    }
  }

  // Unified download helper for ALL document types (Stage-A, Finance, HR)
  const handleDownload = async (doc: { id: number; file_name?: string; doc_name?: string; download_block_reason?: string }) => {
    try {
      const token = localStorage.getItem('token')
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      // All documents download via unified CV Wallet endpoint
      const downloadUrl = `/api/v1/cv-wallet/documents/${doc.id}/download`
      const fullUrl = `${apiBase}${downloadUrl}`
      
      const response = await fetch(fullUrl, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
      })
      
      if (response.ok) {
        // Get blob from response
        const blob = await response.blob()
        
        // Extract filename from Content-Disposition header or use fallback
        let filename = `${doc.file_name || doc.doc_name || 'document'}.pdf`
        const contentDisposition = response.headers.get('Content-Disposition')
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
          if (filenameMatch && filenameMatch[1]) {
            filename = filenameMatch[1].replace(/['"]/g, '')
          }
        }
        
        // Create object URL and trigger download
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        toast({
          title: 'Success',
          description: 'Document downloaded successfully',
        })
      } else {
        // Handle error responses
        let errorMessage = 'Failed to download document'
        
        try {
          const errorData = await response.json()
          const detail = typeof errorData.detail === 'string' ? errorData.detail : errorData.detail?.msg ?? errorData.detail
          errorMessage = detail || errorMessage
        } catch {
          if (response.status === 403) {
            errorMessage = doc.download_block_reason || 'You don\'t have permission to download this document.'
          } else if (response.status === 404) {
            errorMessage = 'Document not found.'
          }
        }
        const is403 = response.status === 403
        const permissionMsg = is403 && errorMessage ? `Missing permission: ${errorMessage}` : errorMessage
        toast({
          title: is403 ? 'Access Denied' : response.status === 404 ? 'Not Found' : 'Error',
          description: is403 ? permissionMsg : errorMessage,
          variant: 'destructive',
        })
      }
    } catch (err) {
      console.error('Failed to download document:', err)
      toast({
        title: 'Error',
        description: 'Failed to download document. Please try again.',
        variant: 'destructive',
      })
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  if (!person) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[100vw] max-w-[100vw] h-[100dvh] max-h-[100dvh] rounded-none overflow-y-auto sm:w-full sm:max-w-2xl sm:max-h-[90vh] sm:rounded-2xl">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-2xl">{person.name}</DialogTitle>
              <DialogDescription asChild>
                <div className="mt-2 flex gap-2 flex-wrap">
                  {person.employee_code && (
                    <Badge variant="secondary">
                      {person.employee_code}
                    </Badge>
                  )}
                  {person.status && (
                    <Badge variant={
                      person.status === 'ACTIVE' ? 'default' :
                      person.status === 'SENT_TO_HR' ? 'secondary' :
                      'outline'
                    }>
                      {person.status}
                    </Badge>
                  )}
                </div>
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6 px-4 pb-4 overflow-y-auto">
          {/* Stage-A Documents */}
          <Card className="shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <SectionHeader
                title="Stage-A Documents"
                description="CV, qualifications, certificates"
                actions={
                  person && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5"
                      onClick={() => {
                        router.push(`/tickets/new?person_id=${person.id}&category=DOCUMENT_REQUEST&to_dept=${person.status === 'SENT_TO_HR' ? 'HR' : 'FINANCE'}`)
                        onOpenChange(false)
                      }}
                    >
                      <Key className="h-4 w-4" />
                      Request Access to Finance/HR Docs
                    </Button>
                  )
                }
              />
            </CardHeader>
            <CardContent className="pt-0">
            {loading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-20 w-full rounded-md" />
                ))}
              </div>
            ) : stageADocuments.length === 0 ? (
              <EmptyState
                icon={<FileText className="h-6 w-6" />}
                title="No Stage-A documents"
                description="No documents in this section."
                className="border-0 bg-transparent py-6"
              />
            ) : (
              <div className="space-y-2">
                {stageADocuments.map((doc) => (
                  <div key={doc.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-4 transition-colors hover:bg-muted/30">
                    <div className="flex items-center gap-3 flex-1">
                      <FileText className="h-5 w-5 text-gray-400" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-medium">{doc.file_name}</p>
                          {/* Step-7: Badges for document type and owner dept */}
                          <Badge variant="outline" className="text-xs">
                            Stage-A
                          </Badge>
                          {doc.owner_dept && (
                            <Badge variant="secondary" className="text-xs">
                              {doc.owner_dept === 'OPERATIONS' ? 'OPS' : doc.owner_dept}
                            </Badge>
                          )}
                          {/* Step-7: Status chip using visibility_label */}
                          {doc.visibility_label && (
                            <Badge 
                              variant={
                                doc.can_download 
                                  ? (doc.reason === 'GRANTED' ? 'default' : 'secondary')
                                  : 'destructive'
                              }
                              className="text-xs"
                            >
                              {doc.visibility_label}
                            </Badge>
                          )}
                          {/* Step-7: Show expiry time when grant_expires_at is present */}
                          {doc.grant_expires_at && (
                            <Badge variant="outline" className="text-xs">
                              Expires: {new Date(doc.grant_expires_at).toLocaleString()}
                            </Badge>
                          )}
                        </div>
                        <div className="flex gap-4 mt-1">
                          {doc.doc_type_name && (
                            <p className="text-xs text-gray-500">Type: {doc.doc_type_name}</p>
                          )}
                          <p className="text-xs text-gray-500">
                            Uploaded: {formatDate(doc.uploaded_at)}
                          </p>
                          {doc.issue_date && (
                            <p className="text-xs text-gray-500">
                              Issue: {formatDate(doc.issue_date)}
                            </p>
                          )}
                          {doc.expiry_date && (
                            <p className="text-xs text-gray-500">
                              Expiry: {formatDate(doc.expiry_date)}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {/* Step-7: Show "Request Access" when reason=NEEDS_GRANT */}
                      {!doc.can_download && doc.reason === 'NEEDS_GRANT' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            router.push(`/tickets/new?person_id=${person.id}&category=DOCUMENT_REQUEST&to_dept=${doc.owner_dept}`)
                            onOpenChange(false)
                          }}
                        >
                          <Key className="w-4 h-4 mr-2" />
                          Request Access
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => doc.can_download && handleDownload(doc)}
                        disabled={!doc.can_download}
                        title={!doc.can_download ? (doc.download_block_reason || doc.visibility_label || 'Missing permission or access') : undefined}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            </CardContent>
          </Card>

          {/* Finance Documents */}
          {(financeDocuments.length > 0 || loadingFinanceHr) && (
            <Card className="shadow-sm">
              <CardHeader>
                <SectionHeader title="Finance Documents" description="KYC and finance-related documents" />
              </CardHeader>
              <CardContent className="pt-0">
              {loadingFinanceHr ? (
                <div className="space-y-2">
                  {[1, 2].map((i) => (
                    <Skeleton key={i} className="h-20 w-full rounded-md" />
                  ))}
                </div>
              ) : financeDocuments.length === 0 ? (
                <EmptyState
                  icon={<FileText className="h-6 w-6" />}
                  title="No finance documents"
                  description="No documents or no access."
                  className="border-0 bg-transparent py-6"
                />
              ) : (
                <div className="space-y-2">
                  {financeDocuments.map((doc) => (
                    <div key={doc.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-4 transition-colors hover:bg-muted/30">
                      <div className="flex items-center gap-3 flex-1">
                        <FileText className="h-5 w-5 text-gray-400" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="text-sm font-medium">{doc.doc_name}</p>
                            {/* Step-7: Badges for document type and owner dept */}
                            <Badge variant="outline" className="text-xs">
                              Finance
                            </Badge>
                            {doc.owner_dept && (
                              <Badge variant="secondary" className="text-xs">
                                {doc.owner_dept}
                              </Badge>
                            )}
                            {/* Step-7: Status chip using visibility_label */}
                            {doc.visibility_label && (
                              <Badge 
                                variant={
                                  doc.can_download 
                                    ? (doc.reason === 'GRANTED' ? 'default' : 'secondary')
                                    : 'destructive'
                                }
                                className="text-xs"
                              >
                                {doc.visibility_label}
                              </Badge>
                            )}
                            {/* Step-7: Show expiry time when grant_expires_at is present */}
                            {doc.grant_expires_at && (
                              <Badge variant="outline" className="text-xs">
                                Expires: {new Date(doc.grant_expires_at).toLocaleString()}
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-gray-500">
                            Uploaded: {formatDate(doc.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {/* Step-7: Show "Request Access" when reason=NEEDS_GRANT */}
                        {!doc.can_download && doc.reason === 'NEEDS_GRANT' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              router.push(`/tickets/new?person_id=${person.id}&category=DOCUMENT_REQUEST&to_dept=FINANCE`)
                              onOpenChange(false)
                            }}
                          >
                            <Key className="w-4 h-4 mr-2" />
                            Request Access
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => doc.can_download && handleDownload({ id: doc.id, doc_name: doc.doc_name, download_block_reason: doc.visibility_label })}
                          disabled={!doc.can_download}
                          title={!doc.can_download ? (doc.visibility_label || 'Missing permission or access') : undefined}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              </CardContent>
            </Card>
          )}

          {/* HR Documents */}
          {(hrDocuments.length > 0 || loadingFinanceHr) && (
            <Card className="shadow-sm">
              <CardHeader>
                <SectionHeader title="HR Documents" description="Appointment letters, declarations" />
              </CardHeader>
              <CardContent className="pt-0">
              {loadingFinanceHr ? (
                <div className="space-y-2">
                  {[1, 2].map((i) => (
                    <Skeleton key={i} className="h-20 w-full rounded-md" />
                  ))}
                </div>
              ) : hrDocuments.length === 0 ? (
                <EmptyState
                  icon={<FileText className="h-6 w-6" />}
                  title="No HR documents"
                  description="No documents or no access."
                  className="border-0 bg-transparent py-6"
                />
              ) : (
                <div className="space-y-2">
                  {hrDocuments.map((doc) => (
                    <div key={doc.id} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-card p-4 transition-colors hover:bg-muted/30">
                      <div className="flex items-center gap-3 flex-1">
                        <FileText className="h-5 w-5 text-gray-400" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="text-sm font-medium">{doc.doc_name}</p>
                            {/* Step-7: Badges for document type and owner dept */}
                            <Badge variant="outline" className="text-xs">
                              HR
                            </Badge>
                            {doc.owner_dept && (
                              <Badge variant="secondary" className="text-xs">
                                {doc.owner_dept}
                              </Badge>
                            )}
                            {/* Step-7: Status chip using visibility_label */}
                            {doc.visibility_label && (
                              <Badge 
                                variant={
                                  doc.can_download 
                                    ? (doc.reason === 'GRANTED' ? 'default' : 'secondary')
                                    : 'destructive'
                                }
                                className="text-xs"
                              >
                                {doc.visibility_label}
                              </Badge>
                            )}
                            {/* Step-7: Show expiry time when grant_expires_at is present */}
                            {doc.grant_expires_at && (
                              <Badge variant="outline" className="text-xs">
                                Expires: {new Date(doc.grant_expires_at).toLocaleString()}
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-gray-500">
                            Uploaded: {formatDate(doc.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {/* Step-7: Show "Request Access" when reason=NEEDS_GRANT */}
                        {!doc.can_download && doc.reason === 'NEEDS_GRANT' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              router.push(`/tickets/new?person_id=${person.id}&category=DOCUMENT_REQUEST&to_dept=HR`)
                              onOpenChange(false)
                            }}
                          >
                            <Key className="w-4 h-4 mr-2" />
                            Request Access
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => doc.can_download && handleDownload({ id: doc.id, doc_name: doc.doc_name, download_block_reason: doc.visibility_label })}
                          disabled={!doc.can_download}
                          title={!doc.can_download ? (doc.visibility_label || 'Missing permission or access') : undefined}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              </CardContent>
            </Card>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

