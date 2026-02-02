'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { apiRequest, apiFetch } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { ArrowLeft, MessageSquare, Paperclip, Clock, User, Key, X, FileText, ExternalLink } from 'lucide-react'

interface Ticket {
  id: string
  ticket_no: string
  from_dept_name: string
  to_dept_name: string
  creator_name: string
  created_by_user_id: number
  assigned_to_name?: string
  person_name?: string
  person_id?: string
  category: string
  priority: string
  status: string
  subject: string
  description: string
  created_at: string
  updated_at: string
  comments: Comment[]
  attachments: Attachment[]
}

interface Comment {
  id: string
  author_name: string
  message: string
  created_at: string
}

interface Attachment {
  id: string
  file_name: string
  mime_type: string
  size_bytes: number
  created_at: string
}

interface AccessGrant {
  id: string
  scope_type: string
  scope_value: string
  expires_at: string
  granted_by_name: string
}

export default function TicketDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { toast } = useToast()
  const ticketId = params.id as string

  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)
  const [commentText, setCommentText] = useState('')
  const [submittingComment, setSubmittingComment] = useState(false)
  const [uploadingFile, setUploadingFile] = useState(false)
  const [showGrantDialog, setShowGrantDialog] = useState(false)
  const [grants, setGrants] = useState<AccessGrant[]>([])
  const [grantsLoading, setGrantsLoading] = useState(false)
  const [availableDocs, setAvailableDocs] = useState<any>(null)
  const [loadingDocs, setLoadingDocs] = useState(false)
  const [grantForm, setGrantForm] = useState({
    scope_type: 'CATEGORY',
    scope_value: '',
    expires_in_hours: 8,
  })

  const [user, setUser] = useState<any>({})
  const [userDeptName, setUserDeptName] = useState<string>('')

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userData = localStorage.getItem('user')
      if (userData) {
        const parsed = JSON.parse(userData)
        setUser(parsed)
        setUserDeptName(parsed.department?.name || parsed.dept_name || '')
      }
    }
  }, [])

  useEffect(() => {
    fetchTicket()
  }, [ticketId])

  useEffect(() => {
    if (ticket?.person_id) {
      fetchGrants()
    } else {
      setGrants([])
      setGrantsLoading(false)
    }
  }, [ticket?.person_id])

  const fetchTicket = async () => {
    setLoading(true)
    try {
      const response = await apiRequest<Ticket>(`/tickets/${ticketId}`)
      if (response.data) {
        setTicket(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch ticket')
    } finally {
      setLoading(false)
    }
  }

  const fetchGrants = async () => {
    if (!ticket?.person_id) {
      setGrants([])
      return
    }
    setGrantsLoading(true)
    try {
      const response = await apiRequest<AccessGrant[]>(`/access-grants/active?person_id=${ticket.person_id}`)
      if (response.data) {
        setGrants(response.data.filter(g => g.scope_value))
      }
    } catch (err) {
      console.error('Failed to fetch grants')
      setGrants([])
    } finally {
      setGrantsLoading(false)
    }
  }

  const handleAddComment = async () => {
    if (!commentText.trim()) return
    setSubmittingComment(true)
    try {
      const response = await apiRequest(`/tickets/${ticketId}/comments`, {
        method: 'POST',
        body: JSON.stringify({ message: commentText }),
      })
      if (response.data) {
        setCommentText('')
        fetchTicket()
        toast({
          title: 'Success',
          description: 'Comment added',
        })
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to add comment',
        variant: 'destructive',
      })
    } finally {
      setSubmittingComment(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    try {
      const response = await apiRequest(`/tickets/${ticketId}`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      })
      if (response.data) {
        fetchTicket()
        toast({
          title: 'Success',
          description: 'Status updated',
        })
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to update status',
        variant: 'destructive',
      })
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploadingFile(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await apiFetch(`/tickets/${ticketId}/attachments`, {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        fetchTicket()
        toast({
          title: 'Success',
          description: 'File uploaded',
        })
      } else {
        throw new Error('Upload failed')
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to upload file',
        variant: 'destructive',
      })
    } finally {
      setUploadingFile(false)
    }
  }

  const handleCreateGrant = async () => {
    if (!ticket?.person_id) return

    try {
      const response = await apiRequest('/access-grants', {
        method: 'POST',
        body: JSON.stringify({
          ticket_id: ticketId,
          person_id: ticket.person_id,
          granted_to_user_id: ticket.created_by_user_id,
          scope_type: grantForm.scope_type,
          scope_value: grantForm.scope_value,
          expires_in_hours: grantForm.expires_in_hours,
        }),
      })

      if (response.data) {
        setShowGrantDialog(false)
        setGrantForm({
          scope_type: 'CATEGORY',
          scope_value: '',
          expires_in_hours: 8,
        })
        fetchGrants()
        fetchTicket()
        toast({
          title: 'Success',
          description: 'Access granted successfully. The requester can now view the documents.',
        })
      } else if (response.error) {
        toast({
          title: 'Error',
          description: response.error,
          variant: 'destructive',
        })
      }
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err.message || 'Failed to create grant',
        variant: 'destructive',
      })
    }
  }

  const canGrantAccess = ticket && 
    ticket.to_dept_name &&
    userDeptName &&
    ticket.to_dept_name.toUpperCase() === userDeptName.toUpperCase() &&
    ticket.category === 'DOCUMENT_REQUEST' &&
    ticket.person_id

  const fetchAvailableDocuments = async () => {
    if (!ticket?.person_id) return
    setLoadingDocs(true)
    try {
      const response = await apiRequest<{categories: Record<string, any[]>, total_count: number}>(`/cv-wallet/persons/${ticket.person_id}/finance-hr-docs`)
      if (response.data) {
        setAvailableDocs(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch available documents:', err)
      setAvailableDocs(null)
    } finally {
      setLoadingDocs(false)
    }
  }

  const handleOpenGrantDialog = () => {
    setShowGrantDialog(true)
    if (ticket?.person_id) {
      fetchAvailableDocuments()
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 rounded-md bg-muted animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="h-64 rounded-lg border bg-muted/50 animate-pulse" />
            <div className="h-48 rounded-lg border bg-muted/50 animate-pulse" />
          </div>
          <div className="space-y-6">
            <div className="h-40 rounded-lg border bg-muted/50 animate-pulse" />
          </div>
        </div>
      </div>
    )
  }

  if (!ticket) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-lg font-medium">Ticket not found</p>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Ticket ${ticket.ticket_no}`}
        subtitle={ticket.subject}
        actions={
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-6 min-w-0">
          {/* Ticket Info */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Ticket Details</CardTitle>
                <div className="flex gap-2">
                  <Badge variant={ticket.status === 'OPEN' ? 'default' : 'secondary'}>
                    {ticket.status}
                  </Badge>
                  <Badge className={
                    ticket.priority === 'HIGH' ? 'bg-red-100 text-red-800' :
                    ticket.priority === 'NORMAL' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }>
                    {ticket.priority}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">From:</span> {ticket.from_dept_name}
                </div>
                <div>
                  <span className="text-gray-500">To:</span> {ticket.to_dept_name}
                </div>
                <div>
                  <span className="text-gray-500">Created by:</span> {ticket.creator_name}
                </div>
                {ticket.assigned_to_name && (
                  <div>
                    <span className="text-gray-500">Assigned to:</span> {ticket.assigned_to_name}
                  </div>
                )}
                {ticket.person_name && (
                  <div className="col-span-2">
                    <span className="text-gray-500">Person:</span> {ticket.person_name}
                    {ticket.person_id && (
                      <Button
                        variant="link"
                        size="sm"
                        className="ml-2 h-auto p-0"
                        onClick={() => {
                          // Open CV Wallet for this person
                          window.open(`/cv-wallet?person_id=${ticket.person_id}`, '_blank')
                        }}
                      >
                        View Person Profile
                      </Button>
                    )}
                  </div>
                )}
              </div>
              <Separator />
              <div>
                <h4 className="font-semibold mb-2">Description</h4>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{ticket.description}</p>
              </div>
              {ticket.person_id && canGrantAccess && (
                <>
                  <Separator />
                  <div>
                    <h4 className="font-semibold mb-2">Grant Access to Documents</h4>
                    <p className="text-xs text-gray-500 mb-2">
                      Click "Grant Access" button in the Actions panel to grant temporary access to Finance/HR documents for the requester.
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          // Open CV Wallet in new tab to view documents
                          window.open(`/cv-wallet?person_id=${ticket.person_id}`, '_blank')
                        }}
                      >
                        <FileText className="w-4 h-4 mr-2" />
                        View All Documents
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleOpenGrantDialog}
                      >
                        <Key className="w-4 h-4 mr-2" />
                        Grant Access Now
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Comments */}
          <Card>
            <CardHeader>
              <CardTitle>Comments</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {ticket.comments.map((comment) => (
                  <div key={comment.id} className="border-l-2 pl-4">
                    <div className="flex items-center gap-2 mb-1">
                      <User className="w-4 h-4 text-gray-400" />
                      <span className="text-sm font-medium">{comment.author_name}</span>
                      <span className="text-xs text-gray-500">
                        {new Date(comment.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700">{comment.message}</p>
                  </div>
                ))}
              </div>
              <Separator />
              <div className="space-y-2">
                <Textarea
                  placeholder="Add a comment..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  rows={3}
                />
                <Button onClick={handleAddComment} disabled={submittingComment || !commentText.trim()}>
                  <MessageSquare className="w-4 h-4 mr-2" />
                  {submittingComment ? 'Adding...' : 'Add Comment'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Attachments */}
          <Card>
            <CardHeader>
              <CardTitle>Attachments</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 mb-4">
                {ticket.attachments.map((attachment) => (
                  <div key={attachment.id} className="flex items-center justify-between p-2 border rounded">
                    <div className="flex items-center gap-2">
                      <Paperclip className="w-4 h-4 text-gray-400" />
                      <span className="text-sm">{attachment.file_name}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {(attachment.size_bytes / 1024).toFixed(2)} KB
                    </span>
                  </div>
                ))}
              </div>
              <Label htmlFor="file-upload" className="cursor-pointer">
                <Input
                  id="file-upload"
                  type="file"
                  onChange={handleFileUpload}
                  disabled={uploadingFile}
                  className="hidden"
                />
                <Button variant="outline" asChild disabled={uploadingFile}>
                  <span>
                    <Paperclip className="w-4 h-4 mr-2" />
                    {uploadingFile ? 'Uploading...' : 'Upload Attachment'}
                  </span>
                </Button>
              </Label>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-4 space-y-6 min-w-0">
          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <Label className="text-xs text-gray-500 mb-1 block">Change Status</Label>
                <Select value={ticket.status} onValueChange={handleStatusChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="OPEN">Open</SelectItem>
                    <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                    <SelectItem value="WAITING">Waiting</SelectItem>
                    <SelectItem value="RESOLVED">Resolved</SelectItem>
                    <SelectItem value="CLOSED">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {canGrantAccess && (
                <Button
                  className="w-full"
                  onClick={handleOpenGrantDialog}
                  disabled={!ticket.person_id}
                >
                  <Key className="w-4 h-4 mr-2" />
                  Grant Access
                </Button>
              )}
              {!canGrantAccess && ticket.category === 'DOCUMENT_REQUEST' && (
                <div className="text-xs text-gray-500 p-2 bg-gray-50 rounded">
                  {!ticket.person_id 
                    ? 'Person must be linked to grant access'
                    : 'Only target department users can grant access'
                  }
                </div>
              )}
            </CardContent>
          </Card>

          {/* Active Grants */}
          {ticket.person_id && (
            <Card>
              <CardHeader>
                <CardTitle>Active Grants</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {grantsLoading ? (
                  <div className="text-center py-2 text-xs text-gray-500">Loading grants...</div>
                ) : grants.length > 0 ? (
                  grants.map((grant) => (
                    <div key={grant.id} className="p-2 border rounded text-sm bg-green-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium">{grant.scope_value}</div>
                          <div className="text-xs text-gray-500">
                            Granted by: {grant.granted_by_name}
                          </div>
                          <div className="text-xs text-gray-500">
                            Expires: {new Date(grant.expires_at).toLocaleString()}
                          </div>
                        </div>
                        <Clock className="w-4 h-4 text-green-500 flex-shrink-0 ml-2" />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-2 text-xs text-gray-500">
                    No active grants
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Grant Access Dialog */}
      <Dialog open={showGrantDialog} onOpenChange={setShowGrantDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Grant Temporary Access</DialogTitle>
            <DialogDescription>
              Grant temporary access to Finance/HR documents for {ticket?.person_name || 'this person'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {/* Show Available Documents */}
            {ticket?.person_id && (
              <div className="border rounded-lg p-4 bg-gray-50">
                <Label className="text-sm font-semibold mb-2 block">Available Documents</Label>
                {loadingDocs ? (
                  <div className="text-sm text-gray-500">Loading available documents...</div>
                ) : availableDocs && availableDocs.total_count > 0 ? (
                  <div className="space-y-2">
                    {Object.entries(availableDocs.categories).map(([category, docs]: [string, any]) => (
                      <div key={category} className="text-sm">
                        <div className="font-medium text-gray-700">
                          {category.replace('_', ' ')} ({docs.length} document{docs.length !== 1 ? 's' : ''})
                        </div>
                        <div className="text-xs text-gray-500 ml-2">
                          {docs.slice(0, 3).map((doc: any) => doc.doc_name).join(', ')}
                          {docs.length > 3 && ` +${docs.length - 3} more`}
                        </div>
                      </div>
                    ))}
                    <div className="text-xs text-gray-500 mt-2">
                      Total: {availableDocs.total_count} document{availableDocs.total_count !== 1 ? 's' : ''}
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">
                    No Finance/HR documents found for this person.
                  </div>
                )}
              </div>
            )}

            <div>
              <Label>Scope Type</Label>
              <Select
                value={grantForm.scope_type}
                onValueChange={(value) => setGrantForm(prev => ({ ...prev, scope_type: value, scope_value: '' }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CATEGORY">Category (All documents in category)</SelectItem>
                  <SelectItem value="DOCUMENTS">Specific Document (by ID)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Scope Value {grantForm.scope_type === 'CATEGORY' && '(Select Category)'}</Label>
              {grantForm.scope_type === 'CATEGORY' ? (
                <Select
                  value={grantForm.scope_value}
                  onValueChange={(value) => setGrantForm(prev => ({ ...prev, scope_value: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category to grant access" />
                  </SelectTrigger>
                  <SelectContent>
                    {/* Show categories based on available documents */}
                    {availableDocs && Object.keys(availableDocs.categories).length > 0 ? (
                      Object.keys(availableDocs.categories).map((category) => (
                        <SelectItem key={category} value={category}>
                          {category.replace('_', ' ')} ({availableDocs.categories[category].length} docs)
                        </SelectItem>
                      ))
                    ) : (
                      <>
                        {/* Fallback: Show all possible categories based on department */}
                        {userDeptName.toUpperCase().includes('HR') && (
                          <>
                            <SelectItem value="HR_SIGNED">HR Signed Documents</SelectItem>
                            <SelectItem value="APPOINTMENT">Appointment Letters</SelectItem>
                            <SelectItem value="ID_CARD">ID Cards</SelectItem>
                          </>
                        )}
                        {userDeptName.toUpperCase().includes('FINANCE') && (
                          <SelectItem value="FINANCE_KYC">Finance KYC Documents</SelectItem>
                        )}
                        {!userDeptName.toUpperCase().includes('HR') && !userDeptName.toUpperCase().includes('FINANCE') && (
                          <>
                            <SelectItem value="HR_SIGNED">HR Signed Documents</SelectItem>
                            <SelectItem value="FINANCE_KYC">Finance KYC Documents</SelectItem>
                            <SelectItem value="APPOINTMENT">Appointment Letters</SelectItem>
                            <SelectItem value="ID_CARD">ID Cards</SelectItem>
                            <SelectItem value="OTHER">Other Documents</SelectItem>
                          </>
                        )}
                      </>
                    )}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  placeholder="Document ID (UUID)"
                  value={grantForm.scope_value}
                  onChange={(e) => setGrantForm(prev => ({ ...prev, scope_value: e.target.value }))}
                />
              )}
            </div>
            <div>
              <Label>Access Duration (hours)</Label>
              <Input
                type="number"
                min="1"
                max="8"
                value={grantForm.expires_in_hours}
                onChange={(e) => setGrantForm(prev => ({ ...prev, expires_in_hours: parseInt(e.target.value) || 8 }))}
              />
              <p className="text-xs text-gray-500 mt-1">
                Access will expire after {grantForm.expires_in_hours} hour{grantForm.expires_in_hours !== 1 ? 's' : ''}
              </p>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <Button variant="outline" onClick={() => {
                setShowGrantDialog(false)
                setAvailableDocs(null)
                setGrantForm({ scope_type: 'CATEGORY', scope_value: '', expires_in_hours: 8 })
              }}>
                Cancel
              </Button>
              <Button onClick={handleCreateGrant} disabled={!grantForm.scope_value}>
                <Key className="w-4 h-4 mr-2" />
                Grant Access
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

