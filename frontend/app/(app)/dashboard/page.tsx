'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PageShell } from '@/components/ui/PageShell'
import { DataCard } from '@/components/common/DataCard'
import { StatCard } from '@/components/ui/StatCard'
import { StatusPill } from '@/components/ui/StatusPill'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { apiRequest } from '@/lib/api'
import { UserPlus, FileText, Users, Wallet, Eye, ArrowRight, CheckCircle2 } from 'lucide-react'

interface Person {
  id: string
  name: string
  mobile: string
  email: string
  status: string
  employee_code?: string
  created_at: string
  stream?: string
  employment_type?: string
  rate_display?: string
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<any>(null)
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    draft: 0,
    submitted: 0,
    active: 0,
    total: 0,
  })

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      // Get all persons for stats
      const response = await apiRequest<Person[]>('/persons?limit=1000')
      if (response.data) {
        setPersons(response.data)
        
        // Calculate stats
        const draft = response.data.filter(p => p.status === 'DRAFT').length
        const submitted = response.data.filter(p => p.status === 'SUBMITTED_TO_FINANCE').length
        const active = response.data.filter(p => p.status === 'ACTIVE').length
        
        setStats({
          draft,
          submitted,
          active,
          total: response.data.length,
        })
      }
    } catch (err) {
      console.error('Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const isOperation = user?.role === 'OPS_USER'
  const isFinance = user?.role === 'FINANCE_USER'
  
  // Finance-specific stats
  const financeStats = {
    pending: persons.filter(p => p.status === 'SUBMITTED_TO_FINANCE').length,
    processedToday: persons.filter(p => {
      if (p.status === 'SENT_TO_HR' || p.status === 'ACTIVE') {
        const today = new Date()
        const updatedDate = new Date(p.created_at) // Using created_at as proxy
        return updatedDate.toDateString() === today.toDateString()
      }
      return false
    }).length,
    sentToHR: persons.filter(p => p.status === 'SENT_TO_HR').length,
    total: persons.length,
  }

  // Finance inbox preview (top 10 pending)
  const financeInboxPreview = persons
    .filter(p => p.status === 'SUBMITTED_TO_FINANCE')
    .slice(0, 10)

  // Recently processed (top 10 with employee code)
  const recentlyProcessed = persons
    .filter(p => (p.status === 'SENT_TO_HR' || p.status === 'ACTIVE') && p.employee_code)
    .slice(0, 10)

  const recentSubmissions = persons
    .filter(p => isOperation ? p.status !== 'DRAFT' : true)
    .slice(0, 10)


  return (
    <PageShell
      title="Dashboard"
      subtitle={
        isOperation
          ? 'Operations Dashboard — Track your submissions and workflow'
          : isFinance
            ? 'Finance Dashboard — Process profiles and manage workflow'
            : 'Welcome to JP Secure Staff'
      }
    >
      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isFinance ? (
          <>
            <StatCard title="Pending in Finance" value={financeStats.pending} icon={<FileText className="h-4 w-4" />} loading={loading} />
            <StatCard title="Processed Today" value={financeStats.processedToday} icon={<CheckCircle2 className="h-4 w-4" />} loading={loading} />
            <StatCard title="Sent to HR" value={financeStats.sentToHR} icon={<ArrowRight className="h-4 w-4" />} loading={loading} />
            <StatCard title="Total Profiles" value={financeStats.total} icon={<Wallet className="h-4 w-4" />} loading={loading} />
          </>
        ) : (
          <>
            <StatCard title="Draft Profiles" value={stats.draft} icon={<FileText className="h-4 w-4" />} loading={loading} />
            <StatCard title="Submitted to Finance" value={stats.submitted} icon={<ArrowRight className="h-4 w-4" />} loading={loading} />
            <StatCard title="Active" value={stats.active} icon={<Users className="h-4 w-4" />} loading={loading} />
            <StatCard title="Total Profiles" value={stats.total} icon={<Wallet className="h-4 w-4" />} loading={loading} />
          </>
        )}
      </div>

      {/* Quick Actions */}
      {isOperation && (
        <DataCard title="Quick Actions">
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={() => router.push('/operation/create')}
              className="gap-2"
            >
              <UserPlus className="h-4 w-4" />
              Create Stage-A Profile
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push('/operation/submissions')}
              className="gap-2"
            >
              <FileText className="h-4 w-4" />
              View My Submissions
            </Button>
          </div>
        </DataCard>
      )}

      {/* Finance Inbox Preview */}
      {isFinance && (
        <DataCard
          title="Finance Inbox Preview"
          actions={
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/finance/inbox')}
            >
              Open Full Inbox
            </Button>
          }
          noPadding
        >
          {loading ? (
            <div className="p-4 space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : financeInboxPreview.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No pending profiles"
                description="No profiles in Finance inbox."
                action={
                  <Button variant="outline" size="sm" onClick={() => router.push('/finance/inbox')}>
                    Open Inbox
                  </Button>
                }
              />
            </div>
          ) : (
            <ResponsiveTableScroll minWidth={700}>
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent bg-muted/50 border-b">
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Name</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Mobile</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Submitted</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Status</TableHead>
                    <TableHead className="text-right text-xs uppercase tracking-wide text-muted-foreground">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {financeInboxPreview.map((person, i) => (
                    <TableRow key={person.id} className={`hover:bg-muted/50 py-3 ${i % 2 === 1 ? 'bg-muted/20' : ''}`}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{person.name}</div>
                          {person.stream && (
                            <div className="text-xs text-muted-foreground">{person.stream}</div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{person.mobile}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(person.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <StatusPill status={person.status} />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => router.push(`/finance/inbox?person=${person.id}`)}
                        >
                          Complete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ResponsiveTableScroll>
          )}
        </DataCard>
      )}

      {/* Recently Processed (Finance) */}
      {isFinance && (
        <DataCard title="Recently Processed" noPadding>
          {loading ? (
            <div className="p-4 space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : recentlyProcessed.length === 0 ? (
            <div className="p-8">
              <EmptyState title="No processed profiles yet" description="Complete Finance processing to see them here." />
            </div>
          ) : (
            <ResponsiveTableScroll minWidth={700}>
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent bg-muted/50 border-b">
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Name</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Employee Code</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Type</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Rate/Salary</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Sent to HR</TableHead>
                    <TableHead className="text-right text-xs uppercase tracking-wide text-muted-foreground">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentlyProcessed.map((person, i) => (
                    <TableRow key={person.id} className={`hover:bg-muted/50 ${i % 2 === 1 ? 'bg-muted/20' : ''}`}>
                      <TableCell className="font-medium">{person.name}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">{person.employee_code}</Badge>
                      </TableCell>
                      <TableCell>
                        {person.employment_type ? (
                          <Badge variant="outline">
                            {person.employment_type === 'PERMANENT' ? 'Permanent' :
                             person.employment_type === 'FREELANCER' ? 'Freelancer' :
                             person.employment_type === 'CONTRACTUAL' ? 'Contractual' :
                             person.employment_type}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {person.rate_display ? (
                          <span className="font-medium">{person.rate_display}</span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(person.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/cv-wallet?person=${person.id}`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ResponsiveTableScroll>
          )}
        </DataCard>
      )}

      {/* Recent Submissions (Operations/Default) */}
      {!isFinance && (
        <DataCard title="Recent Submissions" noPadding>
          {loading ? (
            <div className="p-4 space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : recentSubmissions.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No submissions yet"
                description="Create your first profile to get started."
                action={
                  <Button size="sm" onClick={() => router.push('/operation/create')}>
                    <UserPlus className="h-4 w-4 mr-2" />
                    Create Profile
                  </Button>
                }
              />
            </div>
          ) : (
            <ResponsiveTableScroll minWidth={700}>
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent bg-muted/50 border-b">
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Name</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Status</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Employee Code</TableHead>
                    <TableHead className="text-xs uppercase tracking-wide text-muted-foreground">Created</TableHead>
                    <TableHead className="text-right text-xs uppercase tracking-wide text-muted-foreground">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentSubmissions.map((person, i) => (
                    <TableRow key={person.id} className={`hover:bg-muted/50 ${i % 2 === 1 ? 'bg-muted/20' : ''}`}>
                      <TableCell className="font-medium">{person.name}</TableCell>
                      <TableCell>
                        <StatusPill status={person.status} />
                      </TableCell>
                      <TableCell>
                        {person.employee_code ? (
                          <Badge variant="secondary">{person.employee_code}</Badge>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(person.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/cv-wallet?person=${person.id}`)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          Open
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ResponsiveTableScroll>
          )}
        </DataCard>
      )}
    </PageShell>
  )
}


