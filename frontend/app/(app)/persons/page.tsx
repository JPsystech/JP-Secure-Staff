'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { PageHeader } from '@/components/ui/PageHeader'
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
import { Skeleton } from '@/components/ui/skeleton'
import { apiRequest } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'
import { Plus, UserPlus } from 'lucide-react'

interface PersonSummary {
  id: string
  name: string
  mobile: string
  email?: string
  status: string
  employee_code?: string
  created_at: string
  stream?: string
}

export default function PersonsPage() {
  const [persons, setPersons] = useState<PersonSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    fetchPersons()
  }, [])

  const fetchPersons = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiRequest<PersonSummary[]>('/persons?limit=500')
      if (response.data) {
        setPersons(response.data)
      } else if (response.error) {
        setError(response.error)
      }
    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.debug('[Persons] fetch error', err)
      }
      setError('Failed to load persons')
      setPersons([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Persons"
        subtitle="All persons (submissions and records)"
        actions={
          <Button asChild>
            <Link href="/persons/new" prefetch={false}>
              <Plus className="w-4 h-4 mr-2" />
              Create Person
            </Link>
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : error ? (
            <div className="p-8 text-center text-muted-foreground">
              <p>{error}</p>
              <Button variant="outline" className="mt-4" onClick={fetchPersons}>
                Retry
              </Button>
            </div>
          ) : persons.length === 0 ? (
            <div className="p-12 text-center text-muted-foreground">
              <UserPlus className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium">No persons yet</p>
              <p className="text-sm mt-1">Create a person to get started.</p>
              <Button asChild className="mt-4">
                <Link href="/persons/new" prefetch={false}>
                  Create Person
                </Link>
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Mobile</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Employee code</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {persons.map((person) => (
                  <TableRow key={person.id}>
                    <TableCell className="font-medium">{person.name}</TableCell>
                    <TableCell>{person.mobile}</TableCell>
                    <TableCell>{person.email ?? '—'}</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center rounded-md px-2 py-1 text-xs font-medium bg-muted">
                        {person.status}
                      </span>
                    </TableCell>
                    <TableCell>{person.employee_code ?? '—'}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/persons/${person.id}`} prefetch={false}>
                          View
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
