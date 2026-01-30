'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import AdminShell from '@/components/layouts/AdminShell'
import { PageShell } from '@/components/ui/PageShell'
import { Button } from '@/components/ui/button'
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
import { EmptyState } from '@/components/ui/EmptyState'
import { SearchInput } from '@/components/ui/SearchInput'
import { IconButton } from '@/components/ui/IconButton'
import { StatusPill } from '@/components/ui/StatusPill'
import { ResponsiveTableScroll, TableCardRow } from '@/components/ui/ResponsiveTable'
import { Skeleton } from '@/components/ui/skeleton'
import { auth, admin, type AdminPersonListItem } from '@/lib/api'
import { Eye, MoreHorizontal, FileText } from 'lucide-react'

export default function AdminPersonsPage() {
  const router = useRouter()
  const [persons, setPersons] = useState<AdminPersonListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [error, setError] = useState('')
  const [forbidden, setForbidden] = useState(false)
  const [permissionChecked, setPermissionChecked] = useState(false)

  useEffect(() => {
    (async () => {
      const meRes = await auth.me()
      if (meRes.error || !meRes.data) {
        setPermissionChecked(true)
        return
      }
      const codes = (meRes.data as { permission_codes?: string[] }).permission_codes || []
      if (!codes.includes('ADMIN_PERSON_VIEW_ALL')) {
        setForbidden(true)
      }
      setPermissionChecked(true)
    })()
  }, [])

  useEffect(() => {
    if (!permissionChecked || forbidden) return
    const fetchList = async () => {
      setLoading(true)
      setError('')
      const response = await admin.listPersons({ search: searchTerm || undefined, limit: 200 })
      if (response.error) {
        if (response.error.includes('403') || response.error.includes('Missing required permission')) {
          setForbidden(true)
        } else {
          setError(response.error)
        }
        setPersons([])
      } else if (response.data) {
        setPersons(response.data)
      }
      setLoading(false)
    }
    fetchList()
  }, [permissionChecked, forbidden, searchTerm])

  if (!permissionChecked) {
    return (
      <ProtectedRoute requireAdmin>
        <AdminShell>
          <div className="flex justify-center py-12">
            <div className="space-y-3">
              {Array.from({ length: 6 }, (_, i) => i).map((i) => (
                <Skeleton key={i} className="h-12 w-full rounded" />
              ))}
            </div>
          </div>
        </AdminShell>
      </ProtectedRoute>
    )
  }

  if (forbidden) {
    return (
      <ProtectedRoute requireAdmin>
        <AdminShell>
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800 text-sm">
            You don&apos;t have permission to view all persons. Required: ADMIN_PERSON_VIEW_ALL.
          </div>
        </AdminShell>
      </ProtectedRoute>
    )
  }

  return (
    <ProtectedRoute requireAdmin>
      <AdminShell>
        <PageShell
          title="Persons"
          subtitle="View and manage all persons (Admin)"
        >
          <Card>
            <CardContent className="p-5 space-y-4">
              <div className="max-w-md">
                <SearchInput
                  placeholder="Search by name, email, or employee code..."
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
              ) : persons.length === 0 ? (
                <EmptyState
                  icon={<FileText className="h-6 w-6" />}
                  title="No records found"
                  description="Try adjusting your search or no persons match your filters."
                  className="py-10"
                />
              ) : (
                <>
                  <div className="md:hidden space-y-3">
                    {persons.map((p) => (
                      <TableCardRow key={p.id}>
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="min-w-0">
                            <p className="font-medium truncate">{p.name}</p>
                            <p className="text-xs text-muted-foreground">{p.employee_code || '—'} · {p.department_name || '—'}</p>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <StatusPill status={p.status || ''} />
                            <Button variant="outline" size="sm" onClick={() => router.push(`/admin/persons/${p.id}`)}>
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </div>
                        </div>
                      </TableCardRow>
                    ))}
                  </div>
                  <ResponsiveTableScroll minWidth={700} className="hidden md:block rounded-xl border border-border">
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-transparent border-b bg-muted/60 sticky top-0">
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Name</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Emp Code</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Department</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Status</TableHead>
                        <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Created</TableHead>
                        <TableHead className="text-right text-xs uppercase tracking-wider text-muted-foreground">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {persons.map((p, i) => (
                        <TableRow
                          key={p.id}
                          className={`hover:bg-muted/50 ${i % 2 === 1 ? 'bg-muted/20' : ''}`}
                        >
                          <TableCell className="font-medium py-3">{p.name}</TableCell>
                          <TableCell className="text-muted-foreground py-3">{p.employee_code || '—'}</TableCell>
                          <TableCell className="text-muted-foreground py-3">{p.department_name || '—'}</TableCell>
                          <TableCell className="py-3">
                            <StatusPill status={p.status || ''} />
                          </TableCell>
                          <TableCell className="text-muted-foreground py-3">
                            {p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}
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
                                <DropdownMenuItem onClick={() => router.push(`/admin/persons/${p.id}`)}>
                                  <Eye className="mr-2 h-4 w-4" />
                                  View
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ResponsiveTableScroll>
                </>
              )}
            </CardContent>
          </Card>
        </PageShell>
      </AdminShell>
    </ProtectedRoute>
  )
}
