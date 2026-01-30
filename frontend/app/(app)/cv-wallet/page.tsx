'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { PageShell } from '@/components/ui/PageShell'
import { Toolbar } from '@/components/common/Toolbar'
import { DataCard } from '@/components/common/DataCard'
import { StatPills } from '@/components/ui/StatPills'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusPill } from '@/components/ui/StatusPill'
import { TableCardRow } from '@/components/ui/ResponsiveTable'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DocumentsDrawer } from '@/components/cv-wallet/DocumentsDrawer'
import { Skeleton } from '@/components/ui/skeleton'
import { apiRequest } from '@/lib/api'
import { FileText } from 'lucide-react'

interface Person {
  id: string
  name: string
  mobile: string
  email: string
  location?: string
  employee_code?: string
  company_name?: string
  status: string
  stream?: string
  rate_value?: number
  rate_label?: string
  rate_display?: string
}

export default function CVWalletPage() {
  const searchParams = useSearchParams()
  const [persons, setPersons] = useState<Person[]>([])
  const [filteredPersons, setFilteredPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [streamFilter, setStreamFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    fetchCVWallet()
  }, [])

  // Handle person_id query parameter to auto-open documents drawer
  useEffect(() => {
    const personId = searchParams.get('person_id')
    if (personId && persons.length > 0) {
      const person = persons.find(p => p.id === personId)
      if (person) {
        setSelectedPerson(person)
        setDrawerOpen(true)
      }
    }
  }, [searchParams, persons])

  useEffect(() => {
    filterPersons()
  }, [persons, searchQuery, streamFilter, statusFilter])

  const fetchCVWallet = async () => {
    setLoading(true)
    try {
      const response = await apiRequest<Person[]>('/cv-wallet')
      if (response.data) {
        setPersons(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch CV wallet')
    } finally {
      setLoading(false)
    }
  }

  const filterPersons = () => {
    let filtered = [...persons]

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(p =>
        p.name.toLowerCase().includes(query) ||
        p.mobile.includes(query) ||
        p.email?.toLowerCase().includes(query) ||
        p.employee_code?.toLowerCase().includes(query)
      )
    }

    // Stream filter
    if (streamFilter !== 'all') {
      filtered = filtered.filter(p => p.stream === streamFilter)
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(p => p.status === statusFilter)
    }

    setFilteredPersons(filtered)
  }

  const stats = {
    total: persons.length,
    active: persons.filter(p => p.status === 'ACTIVE').length,
    hrPending: persons.filter(p => p.status === 'SENT_TO_HR').length,
    withoutCode: persons.filter(p => !p.employee_code).length,
  }


  return (
    <PageShell
      title="CV Wallet"
      subtitle="All profiles visible after Finance submission"
    >
      <Toolbar
        searchValue={searchQuery}
        searchPlaceholder="Search by name, mobile, employee code..."
        onSearchChange={setSearchQuery}
        right={
          <>
            <Select value={streamFilter} onValueChange={setStreamFilter}>
              <SelectTrigger className="w-40 h-9">
                <SelectValue placeholder="Stream" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Streams</SelectItem>
                <SelectItem value="MECH">Mechanical</SelectItem>
                <SelectItem value="CIVIL">Civil</SelectItem>
                <SelectItem value="ELEC">Electrical</SelectItem>
                <SelectItem value="OTHER">Other</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48 h-9">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="SUBMITTED_TO_FINANCE">Submitted to Finance</SelectItem>
                <SelectItem value="SENT_TO_HR">Sent to HR</SelectItem>
                <SelectItem value="ACTIVE">Active</SelectItem>
              </SelectContent>
            </Select>
          </>
        }
      />

      <StatPills
        stats={[
          { label: 'Total Profiles', value: stats.total },
          { label: 'Active', value: stats.active },
          { label: 'HR Pending', value: stats.hrPending },
          { label: 'Without Code', value: stats.withoutCode },
        ]}
      />

      <DataCard title="Profiles" noPadding>
        {loading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 6 }, (_, i) => i).map((i) => (
              <Skeleton key={i} className="h-12 w-full rounded" />
            ))}
          </div>
        ) : filteredPersons.length === 0 ? (
          <div className="p-10">
            <EmptyState
              icon={<FileText className="h-6 w-6" />}
              title="No records found"
              description={
                persons.length === 0
                  ? 'Create a profile from Operations to begin.'
                  : 'Try adjusting your filters.'
              }
            />
          </div>
        ) : (
          <>
            <div className="md:hidden space-y-3">
              {filteredPersons.map((person) => (
                <TableCardRow key={person.id}>
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-medium truncate">{person.name}</p>
                        {person.stream && <p className="text-xs text-muted-foreground">{person.stream}</p>}
                        <p className="text-xs text-muted-foreground truncate">{person.email || person.mobile}</p>
                      </div>
                      <StatusPill status={person.status} />
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full sm:w-auto gap-1.5"
                      onClick={() => { setSelectedPerson(person); setDrawerOpen(true); }}
                    >
                      <FileText className="h-4 w-4" />
                      View Docs
                    </Button>
                  </div>
                </TableCardRow>
              ))}
            </div>
            <div className="hidden md:block w-full overflow-x-auto">
            <Table className="min-w-[800px]">
              <TableHeader>
                <TableRow className="hover:bg-transparent bg-muted/60 border-b sticky top-0">
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Employee Code</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Name</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Contact</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Location</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Rate</TableHead>
                  <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Status</TableHead>
                  <TableHead className="text-right text-xs uppercase tracking-wider text-muted-foreground">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPersons.map((person, i) => (
                  <TableRow key={person.id} className={`hover:bg-muted/50 ${i % 2 === 1 ? 'bg-muted/20' : ''}`}>
                    <TableCell className="py-3">
                      {person.employee_code ? (
                        <Badge variant="secondary">{person.employee_code}</Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="py-3">
                      <div>
                        <div className="font-medium">{person.name}</div>
                        {person.stream && (
                          <div className="text-xs text-muted-foreground">{person.stream}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="py-3">
                      <div className="text-sm">
                        <div>{person.email || '—'}</div>
                        <div className="text-muted-foreground">{person.mobile}</div>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground py-3">{person.location || '—'}</TableCell>
                    <TableCell className="py-3">
                      {person.rate_display ? (
                        <span className="font-medium">{person.rate_display}</span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="py-3">
                      <StatusPill status={person.status} />
                    </TableCell>
                    <TableCell className="text-right py-3">
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-1.5"
                        onClick={() => {
                          setSelectedPerson(person)
                          setDrawerOpen(true)
                        }}
                      >
                        <FileText className="h-4 w-4" />
                        View Docs
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          </>
        )}
      </DataCard>

      <DocumentsDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        person={selectedPerson}
      />
    </PageShell>
  )
}

