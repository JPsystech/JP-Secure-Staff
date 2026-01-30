'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/ui/PageHeader'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { FinanceCompletionDrawer } from '@/components/finance/FinanceCompletionDrawer'
import { getStatusBadgeVariant, getStatusColorClass, formatStatus } from '@/lib/status-badge'
import { ResponsiveTableScroll } from '@/components/ui/ResponsiveTable'
import { apiRequest } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { FileText, Search, CheckCircle2 } from 'lucide-react'

interface Person {
  id: string
  name: string
  mobile: string
  email?: string
  status: string
  employee_code?: string
  company_name?: string
  location?: string
  stream?: string
  created_at: string
}

export default function FinanceInboxPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [persons, setPersons] = useState<Person[]>([])
  const [filteredPersons, setFilteredPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    fetchInbox()
  }, [])

  // Check for person ID in URL after data loads
  useEffect(() => {
    const personId = searchParams.get('person')
    if (personId) {
      if (persons.length > 0) {
        // Find person in inbox list
        const person = persons.find(p => p.id === personId)
        if (person) {
          setSelectedPerson(person)
          setDrawerOpen(true)
        } else {
          // If person not in inbox, fetch it directly
          fetchPersonById(personId)
        }
      } else if (!loading) {
        // If inbox is loaded but empty, or person not found, fetch directly
        fetchPersonById(personId)
      }
    }
  }, [persons, searchParams, loading])

  useEffect(() => {
    filterPersons()
  }, [persons, searchQuery, statusFilter, typeFilter])

  const fetchInbox = async () => {
    setLoading(true)
    try {
      const response = await apiRequest<Person[]>('/finance/inbox')
      if (response.data) {
        setPersons(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch inbox')
    } finally {
      setLoading(false)
    }
  }

  const fetchPersonById = async (personId: string) => {
    try {
      const response = await apiRequest<Person>(`/persons/${personId}`)
      if (response.data) {
        setSelectedPerson(response.data)
        setDrawerOpen(true)
      }
    } catch (err) {
      console.error('Failed to fetch person')
      toast({
        title: 'Error',
        description: 'Failed to load person details',
        variant: 'destructive',
      })
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

    // Status filter
    if (statusFilter !== 'all') {
      if (statusFilter === 'pending') {
        filtered = filtered.filter(p => p.status === 'SUBMITTED_TO_FINANCE')
      } else if (statusFilter === 'completed') {
        filtered = filtered.filter(p => p.status === 'SENT_TO_HR' || p.status === 'ACTIVE')
      }
    }

    // Type filter (employment type - would need to fetch from employment, for now show all)
    // This would require additional API call or include in response

    setFilteredPersons(filtered)
  }

  const handleCompleteFinance = (person: Person) => {
    setSelectedPerson(person)
    setDrawerOpen(true)
  }

  const handleDrawerComplete = () => {
    fetchInbox()
    setDrawerOpen(false)
    setSelectedPerson(null)
    toast({
      title: 'Success',
      description: 'Profile processed and submitted to HR',
    })
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Finance Inbox"
        subtitle="Process profiles and complete finance requirements"
        actions={
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search by name, mobile, employee code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 w-64"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="PERMANENT">Permanent</SelectItem>
                <SelectItem value="FREELANCER">Freelancer</SelectItem>
                <SelectItem value="CONTRACTUAL">Contractual</SelectItem>
              </SelectContent>
            </Select>
          </div>
        }
      />

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : filteredPersons.length === 0 ? (
            <div className="p-12 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {persons.length === 0
                  ? 'No persons in finance inbox'
                  : 'No profiles match your filters'}
              </h3>
              <p className="text-sm text-gray-500">
                {persons.length === 0
                  ? 'Persons will appear here after Operations submits them'
                  : 'Try adjusting your search or filters'}
              </p>
            </div>
          ) : (
            <ResponsiveTableScroll minWidth={800}>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Person ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Mobile</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPersons.map((person) => (
                    <TableRow key={person.id}>
                      <TableCell>
                        <span className="text-xs text-gray-500 font-mono">
                          {person.id.substring(0, 8)}...
                        </span>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{person.name}</div>
                          {person.stream && (
                            <div className="text-xs text-gray-500">{person.stream}</div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{person.mobile}</TableCell>
                      <TableCell>{person.location || '—'}</TableCell>
                      <TableCell>
                        <Badge
                          variant={getStatusBadgeVariant(person.status)}
                          className={getStatusColorClass(person.status)}
                        >
                          {formatStatus(person.status)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleCompleteFinance(person)}
                        >
                          <CheckCircle2 className="w-4 h-4 mr-2" />
                          Complete Finance
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ResponsiveTableScroll>
          )}
        </CardContent>
      </Card>

      {/* Finance Completion Drawer */}
      <FinanceCompletionDrawer
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
        person={selectedPerson}
        onComplete={handleDrawerComplete}
      />
    </div>
  )
}
