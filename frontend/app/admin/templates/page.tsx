'use client'

import { useState, useEffect } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import AdminShell from '@/components/layouts/AdminShell'
import { PageShell, DataCard, EmptyState, TableSkeleton } from '@/components/common'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useToast } from '@/components/ui/use-toast'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { apiRequest } from '@/lib/api'
import { Plus, FileText, Check } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface Template {
  id: number
  name: string | null
  type: string
  is_active: boolean
  active_revision_id: number | null
  revisions: TemplateRevision[]
}

interface TemplateRevision {
  id: number
  template_id: number
  version: string
  content: string
  status: string
  created_by: number
  created_at: string
}

export default function TemplatesPage() {
  const { toast } = useToast()
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(true)
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [showRevisionModal, setShowRevisionModal] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [templateFormData, setTemplateFormData] = useState({ type: 'DECLARATION', name: '' })
  const [revisionFormData, setRevisionFormData] = useState({ version: '', content: '' })
  const [formError, setFormError] = useState('')

  const fetchTemplates = async () => {
    setLoading(true)
    try {
      const response = await apiRequest<Template[]>('/templates')
      if (response.data) {
        setTemplates(response.data)
      }
    } catch {
      toast({ title: 'Error', description: 'Failed to fetch templates', variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTemplates()
  }, [])

  const handleTemplateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    try {
      const response = await apiRequest<Template>('/templates', {
        method: 'POST',
        body: JSON.stringify({ type: templateFormData.type, name: templateFormData.name || null }),
      })
      if (response.error) {
        setFormError(response.error)
        return
      }
      setShowTemplateModal(false)
      setTemplateFormData({ type: 'DECLARATION', name: '' })
      toast({ title: 'Template created' })
      fetchTemplates()
    } catch {
      setFormError('An error occurred')
    }
  }

  const handleActivate = async (templateId: number) => {
    try {
      const response = await apiRequest<Template>(`/templates/${templateId}/activate`, { method: 'POST' })
      if (response.data) {
        toast({ title: 'Template activated (others of same type deactivated)' })
        fetchTemplates()
      }
    } catch {
      toast({ title: 'Error', description: 'Failed to activate template', variant: 'destructive' })
    }
  }

  const handleRevisionSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    if (!selectedTemplate) return
    try {
      const response = await apiRequest<TemplateRevision>(`/templates/${selectedTemplate.id}/revisions`, {
        method: 'POST',
        body: JSON.stringify({
          version: revisionFormData.version,
          content: revisionFormData.content,
          status: 'DRAFT',
        }),
      })
      if (response.error) {
        setFormError(response.error)
        return
      }
      setShowRevisionModal(false)
      setRevisionFormData({ version: '', content: '' })
      setSelectedTemplate(null)
      toast({ title: 'Revision created' })
      fetchTemplates()
    } catch {
      setFormError('An error occurred')
    }
  }

  const handlePublish = async (templateId: number, revisionId: number) => {
    try {
      const response = await apiRequest<Template>(`/templates/${templateId}/publish/${revisionId}`, {
        method: 'POST',
      })
      if (response.error) {
        toast({ title: 'Error', description: response.error, variant: 'destructive' })
        return
      }
      toast({ title: 'Revision published' })
      fetchTemplates()
    } catch {
      toast({ title: 'Error', description: 'Failed to publish revision', variant: 'destructive' })
    }
  }

  return (
    <ProtectedRoute requireAdmin>
      <AdminShell>
        <PageShell
            title="Templates"
            subtitle="Manage document templates and revisions"
            actions={
              <Button onClick={() => setShowTemplateModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Template
              </Button>
            }
          >
            {loading ? (
              <TableSkeleton rows={4} cols={3} />
            ) : templates.length === 0 ? (
              <EmptyState
                icon={<FileText className="h-6 w-6" />}
                title="No templates"
                description="Create a template to get started."
                action={
                  <Button onClick={() => setShowTemplateModal(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Template
                  </Button>
                }
              />
            ) : (
              <div className="space-y-6">
                {templates.map((template) => (
                  <DataCard
                    key={template.id}
                    title={template.name ? `${template.name} ${template.is_active ? '(Active)' : ''}` : `${template.type}${template.is_active ? ' (Active)' : ''}`}
                    description={`${template.type} · Revision: ${template.active_revision_id ? `#${template.active_revision_id}` : 'None'}`}
                    icon={<FileText className="h-4 w-4" />}
                    actions={
                      <div className="flex gap-2">
                        {!template.is_active && (
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => handleActivate(template.id)}
                          >
                            <Check className="w-4 h-4 mr-1" />
                            Activate
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedTemplate(template)
                            setShowRevisionModal(true)
                          }}
                        >
                          <Plus className="w-4 h-4 mr-2" />
                          Add Revision
                        </Button>
                      </div>
                    }
                  >
                    <ResponsiveTableScroll minWidth={600}>
                      <Table className="min-w-[600px]">
                        <TableHeader>
                          <TableRow className="hover:bg-transparent border-b bg-muted/50 sticky top-0">
                            <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Version</TableHead>
                            <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Status</TableHead>
                            <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Created</TableHead>
                            <TableHead className="text-xs uppercase tracking-wide text-muted-foreground text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {template.revisions.map((revision) => (
                            <TableRow key={revision.id} className="hover:bg-muted/50">
                              <TableCell className="font-medium">{revision.version}</TableCell>
                              <TableCell>
                                {revision.id === template.active_revision_id ? (
                                  <Badge variant="default" className="text-xs">Active</Badge>
                                ) : (
                                  <Badge variant="secondary" className="text-xs">{revision.status}</Badge>
                                )}
                              </TableCell>
                              <TableCell className="text-sm text-muted-foreground">
                                {new Date(revision.created_at).toLocaleString()}
                              </TableCell>
                              <TableCell className="text-right">
                                {revision.status !== 'PUBLISHED' && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handlePublish(template.id, revision.id)}
                                  >
                                    <Check className="w-4 h-4 mr-1" />
                                    Publish
                                  </Button>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </ResponsiveTableScroll>
                  </DataCard>
                ))}
              </div>
            )}
          </PageShell>

          <Dialog open={showTemplateModal} onOpenChange={(open) => { setShowTemplateModal(open); if (!open) { setFormError(''); setTemplateFormData({ type: 'DECLARATION', name: '' }); } }}>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Add Template</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleTemplateSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name (optional)</Label>
                  <Input
                    id="name"
                    value={templateFormData.name}
                    onChange={(e) => setTemplateFormData({ ...templateFormData, name: e.target.value })}
                    placeholder="e.g. ACS Declaration 2024"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="type">Type</Label>
                  <select
                    id="type"
                    value={templateFormData.type}
                    onChange={(e) => setTemplateFormData({ ...templateFormData, type: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="DECLARATION">DECLARATION</option>
                    <option value="APPOINTMENT_PERMANENT">APPOINTMENT (Permanent)</option>
                    <option value="APPOINTMENT_FREELANCER">APPOINTMENT (Freelancer)</option>
                    <option value="APPOINTMENT_CONTRACTUAL">APPOINTMENT (Contractual)</option>
                  </select>
                </div>
                {formError && (
                  <p className="text-sm text-destructive">{formError}</p>
                )}
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setShowTemplateModal(false)}>Cancel</Button>
                  <Button type="submit">Create</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          <Dialog
            open={showRevisionModal && !!selectedTemplate}
            onOpenChange={(open) => {
              if (!open) {
                setShowRevisionModal(false)
                setSelectedTemplate(null)
                setRevisionFormData({ version: '', content: '' })
                setFormError('')
              }
            }}
          >
            <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Add Revision</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleRevisionSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="version">Version</Label>
                  <Input
                    id="version"
                    value={revisionFormData.version}
                    onChange={(e) => setRevisionFormData({ ...revisionFormData, version: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="content">Content</Label>
                  <textarea
                    id="content"
                    value={revisionFormData.content}
                    onChange={(e) => setRevisionFormData({ ...revisionFormData, content: e.target.value })}
                    required
                    rows={15}
                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>
                {formError && <p className="text-sm text-destructive">{formError}</p>}
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => { setShowRevisionModal(false); setSelectedTemplate(null); setRevisionFormData({ version: '', content: '' }); setFormError(''); }}>Cancel</Button>
                  <Button type="submit">Create</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
      </AdminShell>
    </ProtectedRoute>
  )
}
