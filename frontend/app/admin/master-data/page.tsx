'use client'

import { useState, useEffect } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import AdminShell from '@/components/layouts/AdminShell'
import { PageShell, DataCard, EmptyState, TableSkeleton } from '@/components/common'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
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
import { Plus, Edit, Building2, FileText, MapPin, FolderKanban } from 'lucide-react'

interface Company {
  id: number
  name: string
  short_code: string
  is_akshar: boolean
}

interface Document {
  id: number
  name: string
  is_active: boolean
}

interface Location {
  id: number
  name: string
  is_active: boolean
}

interface Project {
  id: number
  name: string
  client: string | null
  location: string | null
  is_active: boolean
}

type ModalType = 'company' | 'document' | 'location' | 'project'

export default function MasterDataPage() {
  const { toast } = useToast()
  const [companies, setCompanies] = useState<Company[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [modalType, setModalType] = useState<ModalType>('company')
  const [editingItem, setEditingItem] = useState<Company | Document | Location | Project | null>(null)
  const [formData, setFormData] = useState<Record<string, unknown>>({})
  const [formError, setFormError] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const [companiesRes, documentsRes, locationsRes, projectsRes] = await Promise.all([
        apiRequest<Company[]>('/master-data/companies'),
        apiRequest<Document[]>('/master-data/documents'),
        apiRequest<Location[]>('/master-data/locations'),
        apiRequest<Project[]>('/master-data/projects'),
      ])
      if (companiesRes.data) setCompanies(companiesRes.data)
      if (documentsRes.data) setDocuments(documentsRes.data)
      if (locationsRes.data) setLocations(locationsRes.data)
      if (projectsRes.data) setProjects(projectsRes.data)
    } catch {
      toast({ title: 'Error', description: 'Failed to fetch data', variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    try {
      let endpoint = ''
      if (modalType === 'company') endpoint = '/master-data/companies'
      else if (modalType === 'document') endpoint = '/master-data/documents'
      else if (modalType === 'location') endpoint = '/master-data/locations'
      else if (modalType === 'project') endpoint = '/master-data/projects'

      const method = editingItem ? 'PATCH' : 'POST'
      const url = editingItem ? `${endpoint}/${(editingItem as { id: number }).id}` : endpoint

      const response = await apiRequest(url, {
        method,
        body: JSON.stringify(formData),
      })

      if (response.error) {
        setFormError(response.error)
        return
      }
      toast({ title: editingItem ? 'Updated' : 'Created' })
      setShowModal(false)
      setEditingItem(null)
      setFormData({})
      fetchData()
    } catch {
      setFormError('An error occurred')
    }
  }

  const openModal = (type: ModalType, item?: Company | Document | Location | Project) => {
    setModalType(type)
    setEditingItem(item ?? null)
    if (item) {
      setFormData(item as unknown as Record<string, unknown>)
    } else {
      setFormData(
        type === 'company'
          ? { name: '', short_code: '', is_akshar: false }
          : type === 'document' || type === 'location'
            ? { name: '', is_active: true }
            : { name: '', client: '', location: '', is_active: true }
      )
    }
    setShowModal(true)
  }

  const tableHeaderClass = 'text-xs uppercase tracking-wide text-muted-foreground'
  const emptyIcon = <Building2 className="h-6 w-6" />

  return (
    <ProtectedRoute requireAdmin>
      <AdminShell>
        <PageShell
          title="Master Data"
            subtitle="Companies, documents, locations, and projects"
          >
            <Tabs defaultValue="companies" className="w-full">
              <TabsList className="mb-4">
                <TabsTrigger value="companies">Companies</TabsTrigger>
                <TabsTrigger value="documents">Documents</TabsTrigger>
                <TabsTrigger value="locations">Locations</TabsTrigger>
                <TabsTrigger value="projects">Projects</TabsTrigger>
              </TabsList>

              <TabsContent value="companies">
                <DataCard
                  title="Companies"
                  description={`${companies.length} companies`}
                  icon={<Building2 className="h-4 w-4" />}
                  actions={
                    <Button variant="outline" size="sm" onClick={() => openModal('company')}>
                      <Plus className="w-4 h-4 mr-2" />
                      Add Company
                    </Button>
                  }
                  noPadding
                >
                  {loading ? (
                    <TableSkeleton rows={5} cols={4} />
                  ) : companies.length === 0 ? (
                    <EmptyState
                      icon={emptyIcon}
                      title="No companies"
                      description="Add a company to get started."
                      action={<Button size="sm" onClick={() => openModal('company')}><Plus className="w-4 h-4 mr-2" />Add Company</Button>}
                    />
                  ) : (
                    <ResponsiveTableScroll minWidth={600} className="inline-block w-full">
                      <Table>
                        <TableHeader>
                          <TableRow className="hover:bg-transparent border-b bg-muted/50 sticky top-0">
                            <TableHead className={tableHeaderClass}>Name</TableHead>
                            <TableHead className={tableHeaderClass}>Code</TableHead>
                            <TableHead className={tableHeaderClass}>Is Akshar</TableHead>
                            <TableHead className={`${tableHeaderClass} text-right`}>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {companies.map((item) => (
                            <TableRow key={item.id} className="hover:bg-muted/50">
                              <TableCell className="font-medium">{item.name}</TableCell>
                              <TableCell className="text-muted-foreground">{item.short_code}</TableCell>
                              <TableCell>{item.is_akshar ? <Badge variant="secondary">Yes</Badge> : 'No'}</TableCell>
                              <TableCell className="text-right">
                                <Button variant="outline" size="sm" onClick={() => openModal('company', item)}><Edit className="w-4 h-4" /></Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </ResponsiveTableScroll>
                  )}
                </DataCard>
              </TabsContent>

              <TabsContent value="documents">
                <DataCard
                  title="Documents"
                  description={`${documents.length} document types`}
                  icon={<FileText className="h-4 w-4" />}
                  actions={
                    <Button variant="outline" size="sm" onClick={() => openModal('document')}>
                      <Plus className="w-4 h-4 mr-2" />
                      Add Document
                    </Button>
                  }
                  noPadding
                >
                  {loading ? (
                    <TableSkeleton rows={5} cols={3} />
                  ) : documents.length === 0 ? (
                    <EmptyState icon={emptyIcon} title="No documents" description="Add a document type." action={<Button size="sm" onClick={() => openModal('document')}><Plus className="w-4 h-4 mr-2" />Add Document</Button>} />
                  ) : (
                    <ResponsiveTableScroll minWidth={600} className="inline-block w-full">
                      <Table>
                        <TableHeader>
                          <TableRow className="hover:bg-transparent border-b bg-muted/50 sticky top-0">
                            <TableHead className={tableHeaderClass}>Name</TableHead>
                            <TableHead className={tableHeaderClass}>Status</TableHead>
                            <TableHead className={`${tableHeaderClass} text-right`}>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {documents.map((item) => (
                            <TableRow key={item.id} className="hover:bg-muted/50">
                              <TableCell className="font-medium">{item.name}</TableCell>
                              <TableCell>{item.is_active ? <Badge variant="default">Active</Badge> : <Badge variant="secondary">Inactive</Badge>}</TableCell>
                              <TableCell className="text-right">
                                <Button variant="outline" size="sm" onClick={() => openModal('document', item)}><Edit className="w-4 h-4" /></Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </ResponsiveTableScroll>
                  )}
                </DataCard>
              </TabsContent>

              <TabsContent value="locations">
                <DataCard
                  title="Locations"
                  description={`${locations.length} locations`}
                  icon={<MapPin className="h-4 w-4" />}
                  actions={
                    <Button variant="outline" size="sm" onClick={() => openModal('location')}>
                      <Plus className="w-4 h-4 mr-2" />
                      Add Location
                    </Button>
                  }
                  noPadding
                >
                  {loading ? (
                    <TableSkeleton rows={5} cols={3} />
                  ) : locations.length === 0 ? (
                    <EmptyState icon={emptyIcon} title="No locations" description="Add a location." action={<Button size="sm" onClick={() => openModal('location')}><Plus className="w-4 h-4 mr-2" />Add Location</Button>} />
                  ) : (
                    <ResponsiveTableScroll minWidth={600} className="inline-block w-full">
                      <Table>
                        <TableHeader>
                          <TableRow className="hover:bg-transparent border-b bg-muted/50 sticky top-0">
                            <TableHead className={tableHeaderClass}>Name</TableHead>
                            <TableHead className={tableHeaderClass}>Status</TableHead>
                            <TableHead className={`${tableHeaderClass} text-right`}>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {locations.map((item) => (
                            <TableRow key={item.id} className="hover:bg-muted/50">
                              <TableCell className="font-medium">{item.name}</TableCell>
                              <TableCell>{item.is_active ? <Badge variant="default">Active</Badge> : <Badge variant="secondary">Inactive</Badge>}</TableCell>
                              <TableCell className="text-right">
                                <Button variant="outline" size="sm" onClick={() => openModal('location', item)}><Edit className="w-4 h-4" /></Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </ResponsiveTableScroll>
                  )}
                </DataCard>
              </TabsContent>

              <TabsContent value="projects">
                <DataCard
                  title="Projects"
                  description={`${projects.length} projects`}
                  icon={<FolderKanban className="h-4 w-4" />}
                  actions={
                    <Button variant="outline" size="sm" onClick={() => openModal('project')}>
                      <Plus className="w-4 h-4 mr-2" />
                      Add Project
                    </Button>
                  }
                  noPadding
                >
                  {loading ? (
                    <TableSkeleton rows={5} cols={5} />
                  ) : projects.length === 0 ? (
                    <EmptyState icon={emptyIcon} title="No projects" description="Add a project." action={<Button size="sm" onClick={() => openModal('project')}><Plus className="w-4 h-4 mr-2" />Add Project</Button>} />
                  ) : (
                    <ResponsiveTableScroll minWidth={600} className="inline-block w-full">
                      <Table>
                        <TableHeader>
                          <TableRow className="hover:bg-transparent border-b bg-muted/50 sticky top-0">
                            <TableHead className={tableHeaderClass}>Name</TableHead>
                            <TableHead className={tableHeaderClass}>Client</TableHead>
                            <TableHead className={tableHeaderClass}>Location</TableHead>
                            <TableHead className={tableHeaderClass}>Status</TableHead>
                            <TableHead className={`${tableHeaderClass} text-right`}>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {projects.map((item) => (
                            <TableRow key={item.id} className="hover:bg-muted/50">
                              <TableCell className="font-medium">{item.name}</TableCell>
                              <TableCell className="text-muted-foreground">{item.client || '—'}</TableCell>
                              <TableCell className="text-muted-foreground">{item.location || '—'}</TableCell>
                              <TableCell>{item.is_active ? <Badge variant="default">Active</Badge> : <Badge variant="secondary">Inactive</Badge>}</TableCell>
                              <TableCell className="text-right">
                                <Button variant="outline" size="sm" onClick={() => openModal('project', item)}><Edit className="w-4 h-4" /></Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </ResponsiveTableScroll>
                  )}
                </DataCard>
              </TabsContent>
            </Tabs>

            <Dialog
              open={showModal}
              onOpenChange={(open) => {
                if (!open) {
                  setShowModal(false)
                  setEditingItem(null)
                  setFormData({})
                  setFormError('')
                }
              }}
            >
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>{editingItem ? 'Edit' : 'Add'} {modalType.charAt(0).toUpperCase() + modalType.slice(1)}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  {modalType === 'company' && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="name">Name</Label>
                        <Input id="name" value={(formData.name as string) || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="short_code">Short Code</Label>
                        <Input id="short_code" value={(formData.short_code as string) || ''} onChange={(e) => setFormData({ ...formData, short_code: e.target.value })} required />
                      </div>
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="is_akshar" checked={!!formData.is_akshar} onChange={(e) => setFormData({ ...formData, is_akshar: e.target.checked })} className="rounded border-input" />
                        <Label htmlFor="is_akshar">Is Akshar</Label>
                      </div>
                    </>
                  )}
                  {(modalType === 'document' || modalType === 'location') && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="name">Name</Label>
                        <Input id="name" value={(formData.name as string) || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
                      </div>
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="is_active" checked={formData.is_active !== false} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} className="rounded border-input" />
                        <Label htmlFor="is_active">Active</Label>
                      </div>
                    </>
                  )}
                  {modalType === 'project' && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="name">Name</Label>
                        <Input id="name" value={(formData.name as string) || ''} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="client">Client</Label>
                        <Input id="client" value={(formData.client as string) || ''} onChange={(e) => setFormData({ ...formData, client: e.target.value })} />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="location">Location</Label>
                        <Input id="location" value={(formData.location as string) || ''} onChange={(e) => setFormData({ ...formData, location: e.target.value })} />
                      </div>
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="is_active" checked={formData.is_active !== false} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} className="rounded border-input" />
                        <Label htmlFor="is_active">Active</Label>
                      </div>
                    </>
                  )}
                  {formError && <p className="text-sm text-destructive">{formError}</p>}
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => { setShowModal(false); setEditingItem(null); setFormData({}); setFormError(''); }}>Cancel</Button>
                    <Button type="submit">{editingItem ? 'Update' : 'Create'}</Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </PageShell>
      </AdminShell>
    </ProtectedRoute>
  )
}
