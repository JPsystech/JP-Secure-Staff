'use client'

import { useState, useEffect } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import AdminShell from '@/components/layouts/AdminShell'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { EmptyState } from '@/components/ui/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { audit, AuditLogItem, AuditLogFilters } from '@/lib/api'
import { Search, Download, ChevronLeft, ChevronRight, Eye, ScrollText } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'

export default function AuditDashboardPage() {
  const { toast } = useToast()
  const [logs, setLogs] = useState<AuditLogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [total, setTotal] = useState(0)
  const [exporting, setExporting] = useState(false)
  
  // Filters
  const [filters, setFilters] = useState<AuditLogFilters>({
    page: 1,
    page_size: 50,
    sort: '-created_at',
  })
  
  // Filter UI state
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [actionType, setActionType] = useState('')
  const [entityType, setEntityType] = useState('')
  const [actorUserId, setActorUserId] = useState('')
  const [deptId, setDeptId] = useState('')
  const [search, setSearch] = useState('')
  
  // Metadata viewer
  const [selectedMetadata, setSelectedMetadata] = useState<Record<string, any> | null>(null)
  const [metadataDialogOpen, setMetadataDialogOpen] = useState(false)
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null)
  
  // Distinct values for dropdowns (can be fetched or hardcoded)
  const actionTypes = [
    'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT',
    'TICKET_CREATED', 'TICKET_UPDATED', 'TICKET_RESOLVED',
    'DOC_DOWNLOADED', 'DOC_UPLOADED', 'DOC_DELETED',
    'PERSON_CREATED', 'PERSON_UPDATED', 'PERSON_STATUS_CHANGED',
    'FINANCE_KYC_UPDATED', 'FINANCE_KYC_VIEWED',
    'GRANT_CREATED', 'GRANT_REVOKED',
    'USER_CREATED', 'USER_UPDATED', 'USER_DEACTIVATED',
    'ROLE_PERMISSION_UPDATE',
  ]
  
  const entityTypes = [
    'Ticket', 'Person', 'Document', 'User', 'Role', 'Department',
    'FinanceKYC', 'AccessGrant', 'Template',
  ]
  
  const [departments, setDepartments] = useState<Array<{ id: number; name: string }>>([])
  const [users, setUsers] = useState<Array<{ id: number; full_name: string; email: string }>>([])

  const fetchLogs = async () => {
    setLoading(true)
    setError('')
    
    try {
      const params: AuditLogFilters = {
        ...filters,
        page,
        page_size: pageSize,
        sort: filters.sort || '-created_at',
      }
      
      if (dateFrom) params.date_from = new Date(dateFrom).toISOString()
      if (dateTo) params.date_to = new Date(dateTo).toISOString()
      if (actionType) params.action_type = actionType
      if (entityType) params.entity_type = entityType
      if (actorUserId) params.actor_user_id = parseInt(actorUserId)
      if (deptId) params.dept_id = parseInt(deptId)
      if (search) params.search = search
      
      const response = await audit.fetchLogs(params)
      if (response.data) {
        setLogs(response.data.items)
        setTotal(response.data.total)
        setPage(response.data.page)
        setPageSize(response.data.page_size)
      } else if (response.error) {
        setError(response.error)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch audit logs')
    } finally {
      setLoading(false)
    }
  }

  const fetchDepartments = async () => {
    try {
      const { apiRequest } = await import('@/lib/api')
      const response = await apiRequest<Array<{ id: number; name: string }>>('/departments')
      if (response.data) {
        setDepartments(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch departments', err)
    }
  }

  useEffect(() => {
    fetchDepartments()
    fetchLogs()
  }, [page, pageSize])

  const handleApplyFilters = () => {
    setPage(1)
    fetchLogs()
  }

  const handleResetFilters = () => {
    setDateFrom('')
    setDateTo('')
    setActionType('')
    setEntityType('')
    setActorUserId('')
    setDeptId('')
    setSearch('')
    setPage(1)
    setFilters({
      page: 1,
      page_size: pageSize,
      sort: '-created_at',
    })
    setTimeout(() => fetchLogs(), 100)
  }

  const handleExport = async (format: 'csv' | 'xlsx') => {
    setExporting(true)
    try {
      const params: AuditLogFilters = {}
      if (dateFrom) params.date_from = new Date(dateFrom).toISOString()
      if (dateTo) params.date_to = new Date(dateTo).toISOString()
      if (actionType) params.action_type = actionType
      if (entityType) params.entity_type = entityType
      if (actorUserId) params.actor_user_id = parseInt(actorUserId)
      if (deptId) params.dept_id = parseInt(deptId)
      if (search) params.search = search
      
      await audit.exportLogs(params, format)
      toast({
        title: 'Success',
        description: `Audit logs exported as ${format.toUpperCase()}`,
      })
    } catch (err) {
      toast({
        title: 'Export Failed',
        description: err instanceof Error ? err.message : 'Failed to export audit logs',
        variant: 'destructive',
      })
    } finally {
      setExporting(false)
    }
  }

  const formatDateTime = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateString
    }
  }

  const totalPages = Math.ceil(total / pageSize)

  return (
    <ProtectedRoute requireAdmin>
      <AdminShell>
        <div className="space-y-6">
          <PageHeader
            title="Audit Logs"
            subtitle="View and export system audit trail"
            actions={
              <div className="flex gap-2">
                <Button
                  onClick={() => handleExport('csv')}
                  disabled={exporting}
                  variant="outline"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export CSV
                </Button>
                <Button
                  onClick={() => handleExport('xlsx')}
                  disabled={exporting}
                  variant="outline"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Export Excel
                </Button>
              </div>
            }
          />

          {/* Filters */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Filters</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <Label>Date From</Label>
                  <Input
                    type="datetime-local"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Date To</Label>
                  <Input
                    type="datetime-local"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Action Type</Label>
                  <Select
                    value={actionType || '__all_actions'}
                    onValueChange={(value) =>
                      setActionType(value === '__all_actions' ? '' : value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All actions" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__all_actions">All actions</SelectItem>
                      {actionTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Entity Type</Label>
                  <Select
                    value={entityType || '__all_entities'}
                    onValueChange={(value) =>
                      setEntityType(value === '__all_entities' ? '' : value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All entities" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__all_entities">All entities</SelectItem>
                      {entityTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Department</Label>
                  <Select
                    value={deptId || '__all_departments'}
                    onValueChange={(value) =>
                      setDeptId(value === '__all_departments' ? '' : value)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All departments" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__all_departments">All departments</SelectItem>
                      {departments.map((dept) => (
                        <SelectItem key={dept.id} value={String(dept.id)}>
                          {dept.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Search (Entity ID or Metadata)</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <Input
                      type="text"
                      placeholder="Search..."
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <Button onClick={handleApplyFilters}>Apply Filters</Button>
                <Button onClick={handleResetFilters} variant="outline">
                  Reset
                </Button>
              </div>
            </CardContent>
          </Card>

          {error && (
            <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {loading ? (
            <Card>
              <CardContent className="p-6 space-y-4">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </CardContent>
            </Card>
          ) : logs.length === 0 ? (
            <Card>
              <CardContent className="p-6">
                <EmptyState
                  icon={<ScrollText className="h-6 w-6" />}
                  title="No audit logs found"
                  description="Try adjusting your filters."
                  className="py-8"
                />
              </CardContent>
            </Card>
          ) : (
            <>
              <Card>
<ResponsiveTableScroll minWidth={900}>
                <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date/Time</TableHead>
                        <TableHead>Action</TableHead>
                        <TableHead>Entity</TableHead>
                        <TableHead>Entity ID</TableHead>
                        <TableHead>Actor</TableHead>
                        <TableHead>Department</TableHead>
                        <TableHead>IP Address</TableHead>
                        <TableHead>Metadata</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {logs.map((log) => (
                        <TableRow key={log.id} className="hover:bg-muted/50">
                          <TableCell className="text-muted-foreground whitespace-nowrap text-sm">
                            {formatDateTime(log.created_at)}
                          </TableCell>
                          <TableCell className="font-medium">{log.action_type}</TableCell>
                          <TableCell>{log.entity_type}</TableCell>
                          <TableCell className="font-mono text-xs text-muted-foreground">
                            {log.entity_id ? `${log.entity_id.substring(0, 8)}...` : '—'}
                          </TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium">{log.actor_name || 'System'}</div>
                              {log.actor_email && (
                                <div className="text-xs text-muted-foreground">{log.actor_email}</div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-muted-foreground">{log.actor_dept_name || '—'}</TableCell>
                          <TableCell className="text-muted-foreground font-mono text-xs">{log.ip_address || '—'}</TableCell>
                          <TableCell>
                            {log.action_metadata ? (
                              <Dialog open={metadataDialogOpen && selectedLogId === log.id} onOpenChange={(open) => {
                                setMetadataDialogOpen(open)
                                if (!open) {
                                  setSelectedLogId(null)
                                  setSelectedMetadata(null)
                                }
                              }}>
                                <DialogTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      setSelectedMetadata(log.action_metadata || null)
                                      setSelectedLogId(log.id)
                                      setMetadataDialogOpen(true)
                                    }}
                                  >
                                    <Eye className="w-4 h-4 mr-1" />
                                    View
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                                  <DialogHeader>
                                    <DialogTitle>Metadata</DialogTitle>
                                  </DialogHeader>
                                  <pre className="bg-muted p-4 rounded-md text-xs overflow-auto">
                                    {JSON.stringify(selectedMetadata, null, 2)}
                                  </pre>
                                </DialogContent>
                              </Dialog>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ResponsiveTableScroll>
              </Card>

              {/* Pagination */}
              <div className="flex flex-wrap items-center justify-between gap-4 mt-4">
                <div className="text-sm text-muted-foreground">
                  Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} results
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1 || loading}
                    variant="outline"
                    size="sm"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages || loading}
                    variant="outline"
                    size="sm"
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                  <Select
                    value={String(pageSize)}
                    onValueChange={(value) => {
                      setPageSize(parseInt(value))
                      setPage(1)
                    }}
                  >
                    <SelectTrigger className="w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="25">25</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                      <SelectItem value="200">200</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </>
          )}
        </div>
      </AdminShell>
    </ProtectedRoute>
  )
}
