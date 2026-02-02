'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { apiRequest } from '@/lib/api'
import { UserPlus, Users } from 'lucide-react'

interface Person {
  id: string
  name: string
  mobile: string
  email?: string
  status: string
  employee_code?: string
  created_at: string
  stream?: string
  location?: string
}

export default function PersonsPage() {
  const router = useRouter()
  const [persons, setPersons] = useState<Person[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function fetchPersons() {
      setLoading(true)
      setError(null)
      try {
        const response = await apiRequest<Person[]>('/persons?limit=500')
        if (cancelled) return
        if (response.data) {
          setPersons(response.data)
        } else if (response.error) {
          setError(response.error)
        }
      } catch (err) {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load persons')
        if (process.env.NODE_ENV === 'development') {
          console.debug('[Persons] fetch error:', err)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    fetchPersons()
    return () => { cancelled = true }
  }, [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Persons"
        subtitle="List of persons (My Submissions)"
        actions={
          <Button onClick={() => router.push('/operation/create')}>
            <UserPlus className="h-4 w-4 mr-2" />
            Create Person
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
              <p className="text-sm mt-2">Check backend is running and you are logged in.</p>
            </div>
          ) : persons.length === 0 ? (
            <div className="p-12 text-center">
              <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">No persons yet</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Create a person to get started.
              </p>
              <Button onClick={() => router.push('/operation/create')}>
                <UserPlus className="h-4 w-4 mr-2" />
                Create Person
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
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {persons.map((person) => (
                  <TableRow key={person.id}>
                    <TableCell className="font-medium">{person.name}</TableCell>
                    <TableCell>{person.mobile}</TableCell>
                    <TableCell>{person.email ?? '—'}</TableCell>
                    <TableCell>{person.status}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => router.push(`/persons/${person.id}`)}
                      >
                        View
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
