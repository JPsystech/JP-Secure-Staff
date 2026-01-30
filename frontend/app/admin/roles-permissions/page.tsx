'use client'

import { useState, useEffect } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import AdminShell from '@/components/layouts/AdminShell'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { apiRequest } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { Search, Shield, Save } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

interface Permission {
  code: string
  label: string
  description: string
  module: string
  action: string
}

interface Role {
  id: number
  name: string
  code: string
  description: string | null
  is_active: boolean
}

interface RolePermissions {
  role_id: number
  role_name: string
  role_code: string
  permission_codes: string[]
}

export default function RolesPermissionsPage() {
  const { toast } = useToast()
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [rolePermissions, setRolePermissions] = useState<RolePermissions | null>(null)
  const [selectedPermissionCodes, setSelectedPermissionCodes] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [accessDenied, setAccessDenied] = useState(false)

  useEffect(() => {
    checkAccessAndLoad()
  }, [])

  const checkAccessAndLoad = async () => {
    setLoading(true)
    try {
      // Check if user has access (will fail if no permission)
      await Promise.all([
        fetchRoles(),
        fetchPermissions()
      ])
      setAccessDenied(false)
    } catch (err: any) {
      if (err?.response?.status === 403) {
        setAccessDenied(true)
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load data',
          variant: 'destructive',
        })
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchRoles = async () => {
    try {
      const params = new URLSearchParams()
      if (searchTerm) params.append('search', searchTerm)
      
      const response = await apiRequest<Role[]>(`/roles?${params.toString()}`)
      if (response.data) {
        setRoles(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch roles:', err)
      throw err
    }
  }

  const fetchPermissions = async () => {
    try {
      const response = await apiRequest<Permission[]>('/admin/permissions')
      if (response.data) {
        setPermissions(response.data.sort((a, b) => a.code.localeCompare(b.code)))
      }
    } catch (err) {
      console.error('Failed to fetch permissions:', err)
      throw err
    }
  }

  const fetchRolePermissions = async (roleId: number) => {
    try {
      const response = await apiRequest<RolePermissions>(`/admin/roles/${roleId}/permissions`)
      if (response.data) {
        setRolePermissions(response.data)
        setSelectedPermissionCodes(new Set(response.data.permission_codes))
      }
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err?.response?.data?.detail || 'Failed to fetch role permissions',
        variant: 'destructive',
      })
    }
  }

  const handleSelectRole = (role: Role) => {
    setSelectedRole(role)
    fetchRolePermissions(role.id)
  }

  const handleTogglePermission = (code: string) => {
    const newSet = new Set(selectedPermissionCodes)
    if (newSet.has(code)) {
      newSet.delete(code)
    } else {
      newSet.add(code)
    }
    setSelectedPermissionCodes(newSet)
  }

  const handleSave = async () => {
    if (!selectedRole) return
    
    setSaving(true)
    try {
      const response = await apiRequest<RolePermissions>(`/admin/roles/${selectedRole.id}/permissions`, {
        method: 'PUT',
        body: JSON.stringify({
          codes: Array.from(selectedPermissionCodes)
        }),
      })
      
      if (response.data) {
        setRolePermissions(response.data)
        toast({
          title: 'Success',
          description: 'Role permissions updated successfully',
        })
        // Refresh roles list
        fetchRoles()
      }
    } catch (err: any) {
      toast({
        title: 'Error',
        description: err?.response?.data?.detail || 'Failed to update permissions',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const filteredRoles = roles.filter(role =>
    role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    role.code.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Group permissions by module for better UI
  const permissionsByModule = permissions.reduce((acc, perm) => {
    if (!acc[perm.module]) {
      acc[perm.module] = []
    }
    acc[perm.module].push(perm)
    return acc
  }, {} as Record<string, Permission[]>)

  if (loading) {
    return (
      <ProtectedRoute requireAdmin>
        <AdminShell>
          <div className="space-y-6">
            <Skeleton className="h-10 w-80" />
            <Skeleton className="h-96 w-full" />
          </div>
        </AdminShell>
      </ProtectedRoute>
    )
  }

  if (accessDenied) {
    return (
      <ProtectedRoute requireAdmin>
        <AdminShell>
          <Card>
            <CardContent className="p-8">
              <EmptyState
                icon={<Shield className="h-6 w-6" />}
                title="Access Denied"
                description="You don't have permission to manage roles and permissions. This page requires ROLE_MANAGE permission or Master Admin access."
                className="border-destructive/30"
              />
            </CardContent>
          </Card>
        </AdminShell>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute requireAdmin>
      <AdminShell>
        <div className="space-y-6">
          <PageHeader
            title="Roles & Permissions"
            subtitle="Manage role permissions. Permissions are defined in code and cannot be created/deleted via UI."
          />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Roles List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Roles</CardTitle>
            <div className="relative mt-2">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                placeholder="Search roles..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  fetchRoles()
                }}
                className="pl-10"
              />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {filteredRoles.map((role) => (
                <div
                  key={role.id}
                  onClick={() => handleSelectRole(role)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedRole?.id === role.id
                      ? 'bg-blue-50 border-blue-500'
                      : 'hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="font-semibold">{role.name}</div>
                  <div className="text-sm text-gray-500">{role.code}</div>
                  {role.description && (
                    <div className="text-xs text-gray-400 mt-1">{role.description}</div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Permissions Matrix */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>
                  {selectedRole ? `Permissions: ${selectedRole.name}` : 'Select a Role'}
                </CardTitle>
                {selectedRole && rolePermissions && (
                  <p className="text-sm text-gray-500 mt-1">
                    {rolePermissions.permission_codes.length} permission(s) assigned
                  </p>
                )}
              </div>
              {selectedRole && (
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  className="ml-4"
                >
                  {saving ? (
                    <>Saving...</>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!selectedRole ? (
              <EmptyState
                icon={<Shield className="h-6 w-6" />}
                title="Select a role"
                description="Select a role from the list to manage its permissions."
                className="py-12"
              />
            ) : (
              <div className="space-y-6 max-h-[600px] overflow-y-auto">
                {Object.entries(permissionsByModule).map(([module, modulePermissions]) => (
                  <div key={module} className="border-b pb-4 last:border-b-0">
                    <h3 className="font-semibold text-lg mb-3 capitalize">{module}</h3>
                    <div className="space-y-2">
                      {modulePermissions.map((perm) => {
                        const isSelected = selectedPermissionCodes.has(perm.code)
                        return (
                          <label
                            key={perm.code}
                            className={`flex items-start p-3 rounded-lg border cursor-pointer transition-colors ${
                              isSelected
                                ? 'bg-blue-50 border-blue-300'
                                : 'hover:bg-gray-50 border-gray-200'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => handleTogglePermission(perm.code)}
                              className="mt-1 mr-3"
                            />
                            <div className="flex-1">
                              <div className="font-medium">{perm.label || perm.code}</div>
                              <div className="text-xs text-gray-500 mt-1">{perm.description || perm.code}</div>
                              <Badge variant="outline" className="mt-1 text-xs">
                                {perm.code}
                              </Badge>
                            </div>
                          </label>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
          </div>
        </div>
      </AdminShell>
    </ProtectedRoute>
  )
}
