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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { EmptyState } from '@/components/ui/EmptyState'
import { SearchInput } from '@/components/ui/SearchInput'
import { IconButton } from '@/components/ui/IconButton'
import { StatusPill } from '@/components/ui/StatusPill'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/ui/use-toast'
import { apiRequest } from '@/lib/api'
import { Plus, Edit, Power, Key, MoreHorizontal, Users } from 'lucide-react'

interface User {
  id: number
  full_name: string
  email: string
  dept_id: number | null
  role_id: number | null
  role_name?: string | null
  department_name?: string | null
  is_active: boolean
}

interface Department {
  id: number
  name: string
  code: string
}

interface Role {
  id: number
  name: string
  code: string
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    dept_id: '',
    role_id: '',
    is_active: true,
  })
  const [error, setError] = useState('')

  const fetchUsers = async () => {
    try {
      const params = new URLSearchParams()
      if (searchTerm) params.append('search', searchTerm)
      
      const response = await apiRequest<User[]>(`/users?${params.toString()}`)
      if (response.data) {
        setUsers(response.data)
      }
    } catch (err) {
      setError('Failed to fetch users')
    }
  }

  const fetchDepartments = async () => {
    const response = await apiRequest<Department[]>('/departments')
    if (response.data) {
      setDepartments(response.data)
    }
  }

  const fetchRoles = async () => {
    const response = await apiRequest<Role[]>('/roles')
    if (response.data) {
      setRoles(response.data)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([fetchUsers(), fetchDepartments(), fetchRoles()])
      setLoading(false)
    }
    loadData()
  }, [searchTerm])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    try {
      const payload: any = {
        full_name: formData.full_name,
        email: formData.email,
        dept_id: formData.dept_id ? parseInt(formData.dept_id) : null,
        role_id: formData.role_id ? parseInt(formData.role_id) : null,
        is_active: formData.is_active,
      }

      if (!editingUser) {
        payload.password = formData.password
      }

      if (editingUser) {
        const response = await apiRequest<User>(`/users/${editingUser.id}`, {
          method: 'PATCH',
          body: JSON.stringify(payload),
        })
        if (response.error) {
          setError(response.error)
          return
        }
      } else {
        const response = await apiRequest<User>('/users', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        if (response.error) {
          setError(response.error)
          return
        }
      }
      setShowModal(false)
      setEditingUser(null)
      setFormData({
        full_name: '',
        email: '',
        password: '',
        dept_id: '',
        role_id: '',
        is_active: true,
      })
      fetchUsers()
    } catch (err) {
      setError('An error occurred')
    }
  }

  const handleEdit = (user: User) => {
    setEditingUser(user)
    setFormData({
      full_name: user.full_name,
      email: user.email,
      password: '',
      dept_id: user.dept_id?.toString() || '',
      role_id: user.role_id?.toString() || '',
      is_active: user.is_active,
    })
    setShowModal(true)
  }

  const handleToggleActive = async (id: number) => {
    try {
      const response = await apiRequest<User>(`/users/${id}/toggle-active`, {
        method: 'PATCH',
      })
      if (response.data) {
        fetchUsers()
      }
    } catch (err) {
      setError('Failed to toggle user status')
    }
  }

  const { toast } = useToast()

  const handleResetPassword = async (id: number) => {
    const newPassword = prompt('Enter new password:')
    if (!newPassword) return

    try {
      const response = await apiRequest(`/users/${id}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ new_password: newPassword }),
      })
      if (response.data) {
        toast({ title: 'Success', description: 'Password reset successfully' })
      } else {
        toast({
          title: 'Error',
          description: response.error || 'Failed to reset password',
          variant: 'destructive',
        })
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to reset password',
        variant: 'destructive',
      })
    }
  }

  return (
    <ProtectedRoute requireAdmin>
      <AdminShell>
        <PageShell
          title="Users"
          subtitle="Manage system users, roles, and departments"
          actions={
            <Button
              onClick={() => {
                setEditingUser(null)
                setFormData({
                  full_name: '',
                  email: '',
                  password: '',
                  dept_id: '',
                  role_id: '',
                  is_active: true,
                })
                setShowModal(true)
              }}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add User
            </Button>
          }
        >
          <Card>
            <CardContent className="p-5 space-y-4">
              <div className="max-w-sm">
                <SearchInput
                  placeholder="Search users..."
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
              ) : users.length === 0 ? (
                <EmptyState
                  icon={<Users className="h-6 w-6" />}
                  title="No records found"
                  description="Try adjusting your search or add a user to get started."
                  className="py-10"
                  action={
                    <Button
                      size="sm"
                      onClick={() => {
                        setEditingUser(null)
                        setFormData({
                          full_name: '',
                          email: '',
                          password: '',
                          dept_id: '',
                          role_id: '',
                          is_active: true,
                        })
                        setShowModal(true)
                      }}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add User
                    </Button>
                  }
                />
              ) : (
                <ResponsiveTableScroll minWidth={800} className="rounded-xl border border-border">
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-transparent border-b bg-muted/60 sticky top-0">
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Name</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Email</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Department</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Role</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Status</TableHead>
                        <TableHead className="w-[70px] text-right text-xs uppercase tracking-wider text-muted-foreground">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {users.map((user, i) => {
                        const roleName = user.role_name || roles.find(r => r.id === user.role_id)?.name || '—'
                        const deptName = user.department_name || departments.find(d => d.id === user.dept_id)?.name || '—'
                        return (
                          <TableRow
                            key={user.id}
                            className={`hover:bg-muted/50 ${i % 2 === 1 ? 'bg-muted/20' : ''}`}
                          >
                            <TableCell className="font-medium py-3">{user.full_name}</TableCell>
                            <TableCell className="text-muted-foreground py-3">{user.email}</TableCell>
                            <TableCell className="text-muted-foreground py-3">{deptName}</TableCell>
                            <TableCell className="text-muted-foreground py-3">{roleName}</TableCell>
                            <TableCell className="py-3">
                              <StatusPill status={user.is_active ? 'ACTIVE' : 'Inactive'} />
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
                                  <DropdownMenuItem onClick={() => handleEdit(user)}>
                                    <Edit className="h-4 w-4 mr-2" />
                                    Edit
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleToggleActive(user.id)}>
                                    <Power className="h-4 w-4 mr-2" />
                                    {user.is_active ? 'Deactivate' : 'Activate'}
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleResetPassword(user.id)}>
                                    <Key className="h-4 w-4 mr-2" />
                                    Reset Password
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </ResponsiveTableScroll>
              )}
            </CardContent>
          </Card>

          <Dialog open={showModal} onOpenChange={setShowModal}>
            <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingUser ? 'Edit User' : 'Add User'}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>
                {!editingUser && (
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required={!editingUser}
                    />
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="dept_id">Department</Label>
                  <Select value={formData.dept_id || '__none__'} onValueChange={(v) => setFormData({ ...formData, dept_id: v === '__none__' ? '' : v })}>
                    <SelectTrigger id="dept_id">
                      <SelectValue placeholder="Select Department" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">None</SelectItem>
                      {departments.map((dept) => (
                        <SelectItem key={dept.id} value={String(dept.id)}>{dept.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role_id">Role</Label>
                  <Select value={formData.role_id || '__none__'} onValueChange={(v) => setFormData({ ...formData, role_id: v === '__none__' ? '' : v })}>
                    <SelectTrigger id="role_id">
                      <SelectValue placeholder="Select Role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">None</SelectItem>
                      {roles.map((role) => (
                        <SelectItem key={role.id} value={String(role.id)}>{role.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4 rounded border-input"
                  />
                  <Label htmlFor="is_active" className="cursor-pointer">Active</Label>
                </div>
                {error && (
                  <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {error}
                  </div>
                )}
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setShowModal(false)
                      setEditingUser(null)
                      setFormData({
                        full_name: '',
                        email: '',
                        password: '',
                        dept_id: '',
                        role_id: '',
                        is_active: true,
                      })
                      setError('')
                    }}
                  >
                    Cancel
                  </Button>
                  <Button type="submit">{editingUser ? 'Update' : 'Create'}</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </PageShell>
      </AdminShell>
    </ProtectedRoute>
  )
}

