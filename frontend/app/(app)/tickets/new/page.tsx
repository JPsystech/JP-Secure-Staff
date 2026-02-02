'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { PageHeader } from '@/components/ui/PageHeader'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { apiRequest } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { ArrowLeft, Search } from 'lucide-react'

interface Department {
  id: number
  name: string
}

interface Person {
  id: string
  name: string
  mobile: string
  employee_code?: string
}

interface CreateTicketResponse {
  id: number
}

function CreateTicketSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-10 w-64 bg-muted animate-pulse rounded" />
      <Card>
        <CardContent className="p-6 space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

function CreateTicketContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [departments, setDepartments] = useState<Department[]>([])
  const [persons, setPersons] = useState<Person[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null)
  const [loading, setLoading] = useState(false)

  const personIdParam = searchParams.get('person_id') ?? ''
  const categoryParam = searchParams.get('category') ?? 'DOCUMENT_REQUEST'
  const toDeptParam = searchParams.get('to_dept') ?? ''

  const [formData, setFormData] = useState({
    to_dept_id: '',
    person_id: personIdParam,
    category: categoryParam,
    priority: 'NORMAL',
    subject: categoryParam === 'DOCUMENT_REQUEST'
      ? 'Request access to HR/Finance documents'
      : '',
    description: categoryParam === 'DOCUMENT_REQUEST'
      ? `I request temporary access to view and download Finance/HR documents for the person profile.`
      : '',
  })

  useEffect(() => {
    fetchDepartments()
    if (personIdParam) {
      fetchPerson(personIdParam)
    }
  }, [personIdParam])

  useEffect(() => {
    if (departments.length === 0 || !toDeptParam) return
    const dept = departments.find((d) =>
      d.name.toUpperCase().includes(toDeptParam.toUpperCase())
    )
    if (dept) {
      setFormData((prev) => ({ ...prev, to_dept_id: dept.id.toString() }))
    }
  }, [departments, toDeptParam])

  useEffect(() => {
    if (searchQuery.length > 2) {
      searchPersons()
    } else {
      setPersons([])
    }
  }, [searchQuery])

  const fetchDepartments = async () => {
    try {
      const response = await apiRequest<Department[]>('/departments')
      if (response.data) {
        setDepartments(response.data.filter(d => d.name !== 'OPERATIONS'))
      }
    } catch (err) {
      console.error('Failed to fetch departments')
    }
  }

  const fetchPerson = async (personId: string) => {
    try {
      const response = await apiRequest<Person>(`/persons/${personId}`)
      if (response.data) {
        setSelectedPerson(response.data)
        setFormData(prev => ({ ...prev, person_id: personId }))
      }
    } catch (err) {
      console.error('Failed to fetch person')
    }
  }

  const searchPersons = async () => {
    try {
      const response = await apiRequest<Person[]>('/cv-wallet')
      if (response.data) {
        const filtered = response.data.filter(p =>
          p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.mobile.includes(searchQuery) ||
          p.employee_code?.toLowerCase().includes(searchQuery.toLowerCase())
        ).slice(0, 10)
        setPersons(filtered)
      }
    } catch (err) {
      console.error('Failed to search persons')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const payload = {
        to_dept_id: parseInt(formData.to_dept_id),
        person_id: formData.person_id || null,
        category: formData.category,
        priority: formData.priority,
        subject: formData.subject,
        description: formData.description,
      }

      const response = await apiRequest<CreateTicketResponse>('/tickets', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      if (response.data) {
        toast({
          title: 'Success',
          description: 'Ticket created successfully',
        })
        router.push(`/tickets/${response.data.id}`)
      } else if (response.error) {
        toast({
          title: 'Error',
          description: response.error,
          variant: 'destructive',
        })
      }
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to create ticket',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Create Ticket"
        subtitle="Create a new ticket/query to another department"
        actions={
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <SectionHeader title="Ticket Details" description="Create a new ticket or query to another department" />
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="to_dept_id">To Department *</Label>
                <Select
                  value={formData.to_dept_id}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, to_dept_id: value }))}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select department" />
                  </SelectTrigger>
                  <SelectContent>
                    {departments.map((dept) => (
                      <SelectItem key={dept.id} value={dept.id.toString()}>
                        {dept.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="category">Category *</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
                  required
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DOCUMENT_REQUEST">Document Request</SelectItem>
                    <SelectItem value="DATA_CORRECTION">Data Correction</SelectItem>
                    <SelectItem value="CLARIFICATION">Clarification</SelectItem>
                    <SelectItem value="OTHER">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="priority">Priority *</Label>
                <Select
                  value={formData.priority}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, priority: value }))}
                  required
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOW">Low</SelectItem>
                    <SelectItem value="NORMAL">Normal</SelectItem>
                    <SelectItem value="HIGH">High</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="person">Person (Optional)</Label>
                <div className="space-y-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search by name, mobile, or employee code"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8"
                    />
                  </div>
                  {persons.length > 0 && (
                    <div className="border rounded-md max-h-40 overflow-y-auto">
                      {persons.map((person) => (
                        <div
                          key={person.id}
                          className="p-2 hover:bg-gray-50 cursor-pointer"
                          onClick={() => {
                            setSelectedPerson(person)
                            setFormData(prev => ({ ...prev, person_id: person.id }))
                            setSearchQuery('')
                            setPersons([])
                          }}
                        >
                          <div className="text-sm font-medium">{person.name}</div>
                          <div className="text-xs text-gray-500">
                            {person.mobile} {person.employee_code && `• ${person.employee_code}`}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {selectedPerson && (
                    <div className="p-2 bg-blue-50 border rounded-md">
                      <div className="text-sm font-medium">{selectedPerson.name}</div>
                      <div className="text-xs text-gray-500">
                        {selectedPerson.mobile} {selectedPerson.employee_code && `• ${selectedPerson.employee_code}`}
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="mt-1"
                        onClick={() => {
                          setSelectedPerson(null)
                          setFormData(prev => ({ ...prev, person_id: '' }))
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div>
              <Label htmlFor="subject">Subject *</Label>
              <Input
                id="subject"
                value={formData.subject}
                onChange={(e) => setFormData(prev => ({ ...prev, subject: e.target.value }))}
                required
              />
            </div>

            <div>
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows={6}
                required
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? 'Creating...' : 'Create Ticket'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  )
}

export default function CreateTicketPage() {
  return (
    <Suspense fallback={<CreateTicketSkeleton />}>
      <CreateTicketContent />
    </Suspense>
  )
}
