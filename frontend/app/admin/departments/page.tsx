'use client'

import { useState, useEffect } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import AdminShell from '@/components/layouts/AdminShell'
import { PageShell } from '@/components/ui/PageShell'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { SearchInput } from '@/components/ui/SearchInput'
import { IconButton } from '@/components/ui/IconButton'
import { StatusPill } from '@/components/ui/StatusPill'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { Skeleton } from '@/components/ui/skeleton'
import { apiRequest } from '@/lib/api'
import { Plus, Edit, Power, MoreHorizontal, Building2 } from 'lucide-react'

interface Department {
  id: number
  name: string
  code: string
  head: number | null
  is_active: boolean
  created_at: string
}

export default function DepartmentsPage() {
  const [departments, setDepartments] = useState<Department[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingDept, setEditingDept] = useState<Department | null>(null)
  const [formData, setFormData] = useState({ name: '', code: '', head: '' })
  const [error, setError] = useState('')

  const fetchDepartments = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchTerm) params.append('search', searchTerm)

      const response = await apiRequest<Department[]>(`/departments?${params.toString()}`)
      if (response.data) {
        setDepartments(response.data)
      } else {
        setError(response.error || 'Failed to fetch departments')
      }
    } catch (err) {
      setError('An error occurred')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDepartments()
  }, [searchTerm])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      if (editingDept) {
        const response = await apiRequest<Department>(`/departments/${editingDept.id}`, {
          method: 'PATCH',
          body: JSON.stringify({
            name: formData.name,
            code: formData.code,
            head: formData.head ? parseInt(formData.head) : null,
          }),
        })
        if (response.error) {
          setError(response.error)
          return
        }
      } else {
        const response = await apiRequest<Department>('/departments', {
          method: 'POST',
          body: JSON.stringify({
            name: formData.name,
            code: formData.code,
            head: formData.head ? parseInt(formData.head) : null,
          }),
        })
        if (response.error) {
          setError(response.error)
          return
        }
      }
      setShowModal(false)
      setEditingDept(null)
      setFormData({ name: '', code: '', head: '' })
      fetchDepartments()
    } catch (err) {
      setError('An error occurred')
    }
  }

  const handleEdit = (dept: Department) => {
    setEditingDept(dept)
    setFormData({
      name: dept.name,
      code: dept.code,
      head: dept.head?.toString() || '',
    })
    setShowModal(true)
  }

  const handleToggleActive = async (id: number) => {
    try {
      const response = await apiRequest<Department>(`/departments/${id}/toggle-active`, {
        method: 'PATCH',
      })
      if (response.data) {
        fetchDepartments()
      }
    } catch (err) {
      setError('Failed to toggle department status')
    }
  }

  return (
    <ProtectedRoute requireAdmin>
      <AdminShell>
        <PageShell
          title="Departments"
          subtitle="Manage departments and their heads"
          actions={
            <Button
              onClick={() => {
                setEditingDept(null)
                setFormData({ name: '', code: '', head: '' })
                setShowModal(true)
              }}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Department
            </Button>
          }
        >
          <Card>
            <CardContent className="p-5 space-y-4">
              <div className="max-w-sm">
                <SearchInput
                  placeholder="Search departments..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              {error && (
                <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              {loading ? (
                <div className="space-y-3">
                  {Array.from({ length: 6 }, (_, i) => i).map((i) => (
                    <Skeleton key={i} className="h-12 w-full rounded" />
                  ))}
                </div>
              ) : departments.length === 0 ? (
                <EmptyState
                  icon={<Building2 className="h-6 w-6" />}
                  title="No records found"
                  description="Try adjusting your search or add a department to get started."
                  className="py-10"
                  action={
                    <Button
                      size="sm"
                      onClick={() => {
                        setEditingDept(null)
                        setFormData({ name: '', code: '', head: '' })
                        setShowModal(true)
                      }}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Department
                    </Button>
                  }
                />
              ) : (
                <ResponsiveTableScroll minWidth={700} className="rounded-xl border border-border">
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-transparent border-b bg-muted/60 sticky top-0">
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Code</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Name</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Head</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Status</TableHead>
                        <TableHead className="w-[70px] text-right text-xs uppercase tracking-wider text-muted-foreground">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {departments.map((dept, i) => (
                        <TableRow
                          key={dept.id}
                          className={`hover:bg-muted/50 ${i % 2 === 1 ? 'bg-muted/20' : ''}`}
                        >
                          <TableCell className="font-medium py-3">{dept.code}</TableCell>
                          <TableCell className="text-muted-foreground py-3">{dept.name}</TableCell>
                          <TableCell className="text-muted-foreground py-3">{dept.head ?? '—'}</TableCell>
                          <TableCell className="py-3">
                            <StatusPill status={dept.is_active ? 'ACTIVE' : 'Inactive'} />
                          </TableCell>
                          <TableCell className="text-right py-3">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <IconButton
                                  icon={<MoreHorizontal className="h-4 w-4" />}
                                  aria-label="Actions"
                                />
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleEdit(dept)}>
                                  <Edit className="h-4 w-4 mr-2" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleToggleActive(dept.id)}>
                                  <Power className="h-4 w-4 mr-2" />
                                  {dept.is_active ? 'Deactivate' : 'Activate'}
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ResponsiveTableScroll>
              )}
            </CardContent>
          </Card>

          <Dialog open={showModal} onOpenChange={setShowModal}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>{editingDept ? 'Edit Department' : 'Add Department'}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="code">Code</Label>
                  <Input
                    id="code"
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="head">Head ID (Optional)</Label>
                  <Input
                    id="head"
                    type="number"
                    value={formData.head}
                    onChange={(e) => setFormData({ ...formData, head: e.target.value })}
                  />
                </div>
                {error && (
                  <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {error}
                  </div>
                )}
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowModal(false)
                      setEditingDept(null)
                      setFormData({ name: '', code: '', head: '' })
                      setError('')
                    }}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">{editingDept ? 'Update' : 'Create'}</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </PageShell>
      </AdminShell>
    </ProtectedRoute>
  )
}
